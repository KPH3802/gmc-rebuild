"""Tests for the dry-run ``--append-run-history`` + ``--run-id`` flags
(DRYRUN-RUN-HISTORY).

This is the structured local run-history surface. Each invocation
appends one JSONL line to a small caller-supplied local file so
repeated experiments accrete into a comparable record the operator can
diff and rank. The record schema (``schema_version`` = 1) is documented
in ``src/gmc_rebuild/dry_run/_run_history.py``.

Tripwires:

1. **Default behavior unchanged** — without ``--append-run-history``,
   the no-flag stdout / file behavior is byte-for-byte identical.
2. **One run appends one record** — with the flag, the file gains one
   JSONL line carrying the documented shape.
3. **Two runs append two comparable records** — repeated invocations on
   the same path accrete to one line per run, in insertion order.
4. **Cross-experiment comparison** — two different signals files against
   the same expected-positions produce two records with different
   reconciliation outcomes (MATCH vs MISMATCH) — the learning loop made
   explicit in the history file.
5. **--run-id required when appending** — argparse rejects
   ``--append-run-history`` without ``--run-id``.
6. **--run-id without --append-run-history** is rejected.
7. **Empty / whitespace run_id rejected** by argparse.
8. **Missing parent directory** → ``error: ...`` + exit 1 + no
   traceback (and no partial file is created).
9. **Target path that is a directory** → ``error: ...`` + exit 1.
10. **Reconciliation block** is included when ``--show-reconciliation``
    or ``--emit-reconciliation-json`` was passed, and is ``null``
    otherwise.
11. **Works with --emit-json** — the run-history record and the
    ``--emit-json`` payload are emitted in the same run independently.
12. **Source gating** — rejected on ``--source synthetic``.

Authorization: ``governance/authorizations/2026-06-20_dryrun-run-history.md``.
"""

from __future__ import annotations

import io
import json
import shutil
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from gmc_rebuild.dry_run.__main__ import main as cli_main

_FIXTURES_DIR: Path = Path(__file__).resolve().parent / "fixtures"
_TWO_IDEAS: Path = _FIXTURES_DIR / "signals_two_ideas.json"
_THREE_IDEAS: Path = _FIXTURES_DIR / "signals_three_ideas.json"
_EXPECTED_TWO_MATCH: Path = _FIXTURES_DIR / "expected_positions_match_two_ideas.json"
_DB_FIXTURE: Path = (
    Path(__file__).resolve().parents[1] / "insider_cluster_intake" / "fixtures" / "sample.db"
)


def _run_cli(argv: list[str]) -> tuple[str, str, int | str | None]:
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exit_code: int | str | None = None
    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            cli_main(argv)
    except SystemExit as exc:
        exit_code = exc.code
    return stdout_buf.getvalue(), stderr_buf.getvalue(), exit_code


# ---------------------------------------------------------------------------
# 1. Default behavior unchanged
# ---------------------------------------------------------------------------


def test_no_run_history_flag_leaves_filesystem_alone() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        before = sorted(p.name for p in temp.iterdir())
        _run_cli(["--source", "signals_json", "--signals-file", str(_TWO_IDEAS)])
        after = sorted(p.name for p in temp.iterdir())
    assert before == after == []


# ---------------------------------------------------------------------------
# 2. One run appends one JSONL record with the documented shape
# ---------------------------------------------------------------------------


def test_one_run_appends_one_record_with_documented_shape() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "history.jsonl"
        _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_TWO_IDEAS),
                "--run-id",
                "exp-a-001",
                "--append-run-history",
                str(history),
            ]
        )
        lines = history.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["schema_version"] == 1
    assert record["run_id"] == "exp-a-001"
    assert record["source"] == "signals_json"
    assert record["report_date"] == "2026-06-18"
    assert record["inputs"] == {
        "signals_file": str(_TWO_IDEAS),
        "db": None,
        "expected_positions_file": None,
        "signal_count": 2,
        "symbols": ["AAPL", "TSLA"],
    }
    assert record["decisions"]["total"] == 2
    assert record["decisions"]["would_trade"] == 2
    assert record["decisions"]["would_skip"] == 0
    assert record["decisions"]["by_signal"] == [
        {
            "intent_id": "exp-1-aapl-long",
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 10,
            "outcome": "WOULD_TRADE",
        },
        {
            "intent_id": "exp-2-tsla-short",
            "symbol": "TSLA",
            "side": "SELL",
            "quantity": 5,
            "outcome": "WOULD_TRADE",
        },
    ]
    assert record["net_positions"] == [
        {"symbol": "AAPL", "quantity": 10},
        {"symbol": "TSLA", "quantity": -5},
    ]
    assert record["reconciliation"] is None


def test_record_line_is_compact_and_sort_keys_ordered() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "history.jsonl"
        _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_TWO_IDEAS),
                "--run-id",
                "exp-a-001",
                "--append-run-history",
                str(history),
            ]
        )
        text = history.read_text(encoding="utf-8")
    # Single line, ends in newline, no pretty-print indents.
    assert text.endswith("\n")
    assert text.count("\n") == 1
    assert "  " not in text  # no two-space indent from pretty-printing
    # sort_keys=True implies "decisions" < "inputs" < "net_positions" < ...
    line = text.rstrip("\n")
    decisions_idx = line.index('"decisions"')
    inputs_idx = line.index('"inputs"')
    schema_idx = line.index('"schema_version"')
    assert decisions_idx < inputs_idx < schema_idx


# ---------------------------------------------------------------------------
# 3 & 4. Two runs accrete; cross-experiment comparison is visible
# ---------------------------------------------------------------------------


def test_two_runs_append_two_records_in_order() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "history.jsonl"
        _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_TWO_IDEAS),
                "--run-id",
                "exp-a-001",
                "--append-run-history",
                str(history),
            ]
        )
        _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_THREE_IDEAS),
                "--run-id",
                "exp-b-002",
                "--append-run-history",
                str(history),
            ]
        )
        lines = history.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    record_a = json.loads(lines[0])
    record_b = json.loads(lines[1])
    assert record_a["run_id"] == "exp-a-001"
    assert record_b["run_id"] == "exp-b-002"
    assert record_a["inputs"]["signal_count"] == 2
    assert record_b["inputs"]["signal_count"] == 3
    assert record_a["inputs"]["symbols"] == ["AAPL", "TSLA"]
    assert record_b["inputs"]["symbols"] == ["AAPL", "MSFT", "TSLA"]


def test_two_experiments_against_same_expected_yield_comparable_records() -> None:
    """The MVP scoring/learning loop in one history file: two runs, two
    different signals files, same expected portfolio — one record says
    MATCH, the other says MISMATCH. This is the structural delta a
    scoring function will rank on."""
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "history.jsonl"
        _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_TWO_IDEAS),
                "--expected-positions",
                str(_EXPECTED_TWO_MATCH),
                "--show-reconciliation",
                "--run-id",
                "exp-a-001",
                "--append-run-history",
                str(history),
            ]
        )
        _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_THREE_IDEAS),
                "--expected-positions",
                str(_EXPECTED_TWO_MATCH),
                "--show-reconciliation",
                "--run-id",
                "exp-b-002",
                "--append-run-history",
                str(history),
            ]
        )
        records = [json.loads(line) for line in history.read_text().splitlines()]
    assert records[0]["reconciliation"]["outcome"] == "MATCH"
    assert records[1]["reconciliation"]["outcome"] == "MISMATCH"
    # Both records carry comparable counts the scorer can rank on.
    assert records[0]["reconciliation"]["quantity_mismatches"] == 0
    assert records[1]["reconciliation"]["quantity_mismatches"] == 1
    assert records[0]["reconciliation"]["only_in_simulated"] == 0
    assert records[1]["reconciliation"]["only_in_simulated"] == 1


# ---------------------------------------------------------------------------
# 5 & 6 & 7. --run-id / --append-run-history pairing
# ---------------------------------------------------------------------------


def test_append_without_run_id_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "history.jsonl"
        _, stderr, code = _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_TWO_IDEAS),
                "--append-run-history",
                str(history),
            ]
        )
    assert code == 2
    assert "--run-id is required" in stderr
    # File never created.
    assert not history.exists()


def test_run_id_without_append_is_rejected() -> None:
    _, stderr, code = _run_cli(
        [
            "--source",
            "signals_json",
            "--signals-file",
            str(_TWO_IDEAS),
            "--run-id",
            "exp-orphan",
        ]
    )
    assert code == 2
    assert "--run-id requires --append-run-history" in stderr


def test_empty_run_id_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "history.jsonl"
        _, stderr, code = _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_TWO_IDEAS),
                "--run-id",
                "",
                "--append-run-history",
                str(history),
            ]
        )
    assert code == 2
    assert "run-id" in stderr


def test_whitespace_run_id_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "history.jsonl"
        _, stderr, code = _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_TWO_IDEAS),
                "--run-id",
                "has space",
                "--append-run-history",
                str(history),
            ]
        )
    assert code == 2
    assert "whitespace-free" in stderr


# ---------------------------------------------------------------------------
# 8 & 9. Operator-readable filesystem errors
# ---------------------------------------------------------------------------


def test_missing_parent_directory_produces_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        nonexistent = Path(raw_temp) / "does_not_exist" / "history.jsonl"
        _, stderr, code = _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_TWO_IDEAS),
                "--run-id",
                "exp-001",
                "--append-run-history",
                str(nonexistent),
            ]
        )
    assert code == 1
    assert stderr.startswith("error: cannot append run history:")
    assert "parent directory does not exist" in stderr
    assert "Traceback" not in stderr
    assert not nonexistent.exists()


def test_target_path_is_a_directory_produces_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        dir_target = Path(raw_temp) / "history_dir"
        dir_target.mkdir()
        _, stderr, code = _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_TWO_IDEAS),
                "--run-id",
                "exp-001",
                "--append-run-history",
                str(dir_target),
            ]
        )
    assert code == 1
    assert "is a directory" in stderr
    assert "Traceback" not in stderr


# ---------------------------------------------------------------------------
# 10. Reconciliation block inclusion
# ---------------------------------------------------------------------------


def test_reconciliation_block_is_null_when_no_recon_requested() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "history.jsonl"
        _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_TWO_IDEAS),
                "--run-id",
                "exp-no-recon",
                "--append-run-history",
                str(history),
            ]
        )
        record = json.loads(history.read_text())
    assert record["reconciliation"] is None


def test_reconciliation_block_populated_when_show_reconciliation_passed() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "history.jsonl"
        _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_TWO_IDEAS),
                "--show-reconciliation",
                "--run-id",
                "exp-recon",
                "--append-run-history",
                str(history),
            ]
        )
        record = json.loads(history.read_text())
    assert record["reconciliation"]["outcome"] == "MATCH"
    assert record["reconciliation"]["matches"] == 2
    assert record["reconciliation"]["reconciliation_status"] == "clean"


# ---------------------------------------------------------------------------
# 11. --emit-json and --append-run-history are independent in one run
# ---------------------------------------------------------------------------


def test_emit_json_and_append_run_history_compose_in_one_run() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        history = temp / "history.jsonl"
        decisions_out = temp / "decisions.json"
        _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_TWO_IDEAS),
                "--emit-json",
                str(decisions_out),
                "--run-id",
                "exp-compose",
                "--append-run-history",
                str(history),
            ]
        )
        history_record = json.loads(history.read_text())
        decisions_payload = json.loads(decisions_out.read_text())
    # The two surfaces are independent and carry the same underlying
    # signal/decision data, but in their own documented shapes.
    assert history_record["decisions"]["total"] == 2
    assert decisions_payload["summary"]["total"] == 2
    assert history_record["run_id"] == "exp-compose"
    assert "run_id" not in decisions_payload  # decisions JSON has no run_id


# ---------------------------------------------------------------------------
# 12. Source gating
# ---------------------------------------------------------------------------


def test_append_run_history_rejected_on_synthetic_source() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "history.jsonl"
        _, stderr, code = _run_cli(
            [
                "--source",
                "synthetic",
                "--run-id",
                "exp-001",
                "--append-run-history",
                str(history),
            ]
        )
    assert code == 2
    assert "insider_cluster" in stderr
    assert "signals_json" in stderr


def test_append_run_history_works_over_insider_cluster_source() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db_copy = temp / "sample.db"
        shutil.copy(_DB_FIXTURE, db_copy)
        history = temp / "history.jsonl"
        _run_cli(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db_copy),
                "--run-id",
                "ins-001",
                "--append-run-history",
                str(history),
            ]
        )
        record = json.loads(history.read_text())
    assert record["source"] == "insider_cluster"
    assert record["inputs"]["db"] == str(db_copy)
    assert record["inputs"]["signals_file"] is None
    assert record["inputs"]["signal_count"] == 1
    assert record["inputs"]["symbols"] == ["NKE"]
    assert record["decisions"]["by_signal"][0]["symbol"] == "NKE"
