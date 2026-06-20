"""Tests for the dry-run ``--expected-positions`` opt-in input (DRYRUN-EXPECTED-POSITIONS).

The reconciliation surfaces (``--emit-reconciliation-json`` /
``--show-reconciliation``) previously only ran a self-comparison of the
simulated portfolio against itself, so they could only ever produce
``outcome=MATCH``. This packet adds an opt-in
``--expected-positions PATH`` flag that lets the operator point at a
small local JSON file describing the independent expected positions; the
reconciliation surfaces then compare the simulated portfolio against
that input, so both MATCH and MISMATCH outcomes are reachable.

Tripwires:

1. **Default behavior unchanged** — without ``--expected-positions``,
   the no-flag stdout is byte-for-byte identical to the locked literal,
   and the existing ``--show-reconciliation`` / ``--emit-reconciliation-json``
   self-comparison payloads remain MATCH by construction.
2. **MATCH path** — a fixture whose positions equal the simulated NKE
   portfolio produces the documented MATCH block / JSON payload.
3. **MISMATCH path** — a fixture differing from the simulated NKE
   portfolio produces a MISMATCH outcome with the expected
   quantity_mismatches / only_in_expected entries; both the text block
   and the JSON payload reflect the independent input (not the
   self-comparison).
4. **JSON ↔ text surface agreement** — for the same expected-positions
   input, the JSON payload and the text block describe the same outcome.
5. **Operator-readable errors** — missing file → exit 1 + ``error: ...``
   on stderr + empty stdout + no traceback. Malformed JSON / wrong schema
   / wrong types / duplicate symbol / zero quantity → exit 1 + ``error:
   ...`` on stderr + empty stdout + no traceback.
6. **Synthetic source rejection** — ``--expected-positions`` is rejected
   on ``--source synthetic`` with exit code 2 (argparse usage error).

Authorization: ``governance/authorizations/2026-06-20_dryrun-expected-positions.md``.
"""

from __future__ import annotations

import io
import json
import shutil
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from gmc_rebuild.dry_run.__main__ import main as cli_main
from gmc_rebuild.dry_run._expected_positions import (
    ExpectedPositionsSchemaError,
    load_expected_positions,
)

_DB_FIXTURE: Path = (
    Path(__file__).resolve().parents[1] / "insider_cluster_intake" / "fixtures" / "sample.db"
)
_FIXTURES_DIR: Path = Path(__file__).resolve().parent / "fixtures"
_MATCH_FIXTURE: Path = _FIXTURES_DIR / "expected_positions_match_nke.json"
_MISMATCH_FIXTURE: Path = _FIXTURES_DIR / "expected_positions_mismatch_nke.json"


_EXPECTED_NO_FLAG_STDOUT: str = (
    "daily_report: 2026-06-18\n"
    "decisions: 1 total, 1 would_trade, 0 would_skip\n"
    "reconciliation: clean\n"
    "net_positions:\n"
    "  - NKE: 163\n"
    "applied_intent_ids:\n"
    "  - simoi-34836e27172d51b4d97d5f99a0f8cdca2ef84d855c18ab14e86dafe3db288e11\n"
    "\n"
    "safety_verdict: clear=True, blockers=none\n"
    "decision: WOULD_TRADE insider-NKE-2025-12-29 reasons=none\n"
)


_EXPECTED_MATCH_BLOCK: str = (
    "\n"
    "dry_run_reconciliation:\n"
    "  outcome: MATCH\n"
    "  status: clean\n"
    "  summary: 1 matches, 0 quantity_mismatches, 0 only_in_simulated, "
    "0 only_in_expected\n"
    "  matches:\n"
    "    - NKE: 163\n"
    "  quantity_mismatches:\n"
    "    (none)\n"
    "  only_in_simulated:\n"
    "    (none)\n"
    "  only_in_expected:\n"
    "    (none)\n"
)


_EXPECTED_MISMATCH_BLOCK: str = (
    "\n"
    "dry_run_reconciliation:\n"
    "  outcome: MISMATCH\n"
    "  status: clean\n"
    "  summary: 0 matches, 1 quantity_mismatches, 0 only_in_simulated, "
    "1 only_in_expected\n"
    "  matches:\n"
    "    (none)\n"
    "  quantity_mismatches:\n"
    "    - NKE: simulated=163 expected=100\n"
    "  only_in_simulated:\n"
    "    (none)\n"
    "  only_in_expected:\n"
    "    - AAPL: 5\n"
)


def _copy_db(temp_dir: Path) -> Path:
    dst = temp_dir / "sample.db"
    shutil.copy(_DB_FIXTURE, dst)
    return dst


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
# 1. Default behavior unchanged (no --expected-positions)
# ---------------------------------------------------------------------------


def test_no_flag_no_expected_positions_stdout_unchanged() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        db = _copy_db(Path(raw_temp))
        stdout, stderr, code = _run_cli(["--source", "insider_cluster", "--db", str(db)])
    assert code is None
    assert stderr == ""
    assert stdout == _EXPECTED_NO_FLAG_STDOUT


def test_show_reconciliation_without_expected_positions_is_still_self_match() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        db = _copy_db(Path(raw_temp))
        stdout, _, _ = _run_cli(
            ["--source", "insider_cluster", "--db", str(db), "--show-reconciliation"]
        )
    assert stdout == _EXPECTED_NO_FLAG_STDOUT + _EXPECTED_MATCH_BLOCK


# ---------------------------------------------------------------------------
# 2. MATCH path — independent fixture equal to simulated NKE portfolio
# ---------------------------------------------------------------------------


def test_show_reconciliation_with_match_fixture_renders_match_block() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        db = _copy_db(Path(raw_temp))
        stdout, _, _ = _run_cli(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db),
                "--expected-positions",
                str(_MATCH_FIXTURE),
                "--show-reconciliation",
            ]
        )
    assert stdout == _EXPECTED_NO_FLAG_STDOUT + _EXPECTED_MATCH_BLOCK


def test_emit_reconciliation_json_with_match_fixture_emits_match_payload() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db = _copy_db(temp)
        out = temp / "recon.json"
        stdout, _, _ = _run_cli(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db),
                "--expected-positions",
                str(_MATCH_FIXTURE),
                "--emit-reconciliation-json",
                str(out),
            ]
        )
        payload = json.loads(out.read_text())
    assert stdout == _EXPECTED_NO_FLAG_STDOUT
    assert payload == {
        "outcome": "MATCH",
        "reconciliation_status": "clean",
        "matches": [{"symbol": "NKE", "quantity": 163}],
        "quantity_mismatches": [],
        "only_in_simulated": [],
        "only_in_expected": [],
        "summary": {
            "matches": 1,
            "quantity_mismatches": 0,
            "only_in_simulated": 0,
            "only_in_expected": 0,
        },
    }


# ---------------------------------------------------------------------------
# 3. MISMATCH path — independent fixture differing from the NKE portfolio
# ---------------------------------------------------------------------------


def test_show_reconciliation_with_mismatch_fixture_renders_mismatch_block() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        db = _copy_db(Path(raw_temp))
        stdout, _, _ = _run_cli(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db),
                "--expected-positions",
                str(_MISMATCH_FIXTURE),
                "--show-reconciliation",
            ]
        )
    assert stdout == _EXPECTED_NO_FLAG_STDOUT + _EXPECTED_MISMATCH_BLOCK


def test_emit_reconciliation_json_with_mismatch_fixture_emits_mismatch_payload() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db = _copy_db(temp)
        out = temp / "recon.json"
        _run_cli(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db),
                "--expected-positions",
                str(_MISMATCH_FIXTURE),
                "--emit-reconciliation-json",
                str(out),
            ]
        )
        payload = json.loads(out.read_text())
    assert payload == {
        "outcome": "MISMATCH",
        "reconciliation_status": "clean",
        "matches": [],
        "quantity_mismatches": [
            {"symbol": "NKE", "simulated_quantity": 163, "expected_quantity": 100}
        ],
        "only_in_simulated": [],
        "only_in_expected": [{"symbol": "AAPL", "quantity": 5}],
        "summary": {
            "matches": 0,
            "quantity_mismatches": 1,
            "only_in_simulated": 0,
            "only_in_expected": 1,
        },
    }


# ---------------------------------------------------------------------------
# 4. JSON ↔ text surface agreement (same expected-positions input)
# ---------------------------------------------------------------------------


def test_json_and_text_surfaces_agree_for_mismatch_fixture() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db = _copy_db(temp)
        out = temp / "recon.json"
        stdout, _, _ = _run_cli(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db),
                "--expected-positions",
                str(_MISMATCH_FIXTURE),
                "--emit-reconciliation-json",
                str(out),
                "--show-reconciliation",
            ]
        )
        payload = json.loads(out.read_text())
    # Text block ends in MISMATCH; JSON payload outcome is MISMATCH.
    assert stdout == _EXPECTED_NO_FLAG_STDOUT + _EXPECTED_MISMATCH_BLOCK
    assert payload["outcome"] == "MISMATCH"
    assert payload["quantity_mismatches"] == [
        {"symbol": "NKE", "simulated_quantity": 163, "expected_quantity": 100}
    ]
    assert payload["only_in_expected"] == [{"symbol": "AAPL", "quantity": 5}]


# ---------------------------------------------------------------------------
# 5. Operator-readable errors
# ---------------------------------------------------------------------------


def test_missing_expected_positions_file_produces_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db = _copy_db(temp)
        missing = temp / "nope.json"
        stdout, stderr, code = _run_cli(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db),
                "--expected-positions",
                str(missing),
                "--show-reconciliation",
            ]
        )
    assert code == 1
    assert stdout == ""
    assert stderr == f"error: expected-positions file not found: {missing}\n"
    assert "Traceback" not in stderr


def test_malformed_json_produces_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db = _copy_db(temp)
        bad = temp / "bad.json"
        bad.write_text("{ not json", encoding="utf-8")
        stdout, stderr, code = _run_cli(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db),
                "--expected-positions",
                str(bad),
                "--show-reconciliation",
            ]
        )
    assert code == 1
    assert stdout == ""
    assert stderr.startswith(f"error: invalid expected-positions file {bad}: ")
    assert "not valid JSON" in stderr
    assert "Traceback" not in stderr


def test_missing_positions_key_produces_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db = _copy_db(temp)
        bad = temp / "no_key.json"
        bad.write_text('{"other": []}', encoding="utf-8")
        _, stderr, code = _run_cli(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db),
                "--expected-positions",
                str(bad),
                "--show-reconciliation",
            ]
        )
    assert code == 1
    assert "missing required 'positions' key" in stderr
    assert "Traceback" not in stderr


def test_duplicate_symbol_produces_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db = _copy_db(temp)
        bad = temp / "dup.json"
        bad.write_text(
            '{"positions": [{"symbol": "NKE", "quantity": 10}, {"symbol": "NKE", "quantity": 20}]}',
            encoding="utf-8",
        )
        _, stderr, code = _run_cli(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db),
                "--expected-positions",
                str(bad),
                "--show-reconciliation",
            ]
        )
    assert code == 1
    assert "duplicate" in stderr
    assert "Traceback" not in stderr


def test_zero_quantity_produces_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db = _copy_db(temp)
        bad = temp / "zero.json"
        bad.write_text('{"positions": [{"symbol": "NKE", "quantity": 0}]}', encoding="utf-8")
        _, stderr, code = _run_cli(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db),
                "--expected-positions",
                str(bad),
                "--show-reconciliation",
            ]
        )
    assert code == 1
    assert "non-zero" in stderr
    assert "Traceback" not in stderr


def test_float_quantity_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db = _copy_db(temp)
        bad = temp / "float.json"
        bad.write_text('{"positions": [{"symbol": "NKE", "quantity": 1.5}]}', encoding="utf-8")
        _, stderr, code = _run_cli(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db),
                "--expected-positions",
                str(bad),
                "--show-reconciliation",
            ]
        )
    assert code == 1
    assert "must be an integer" in stderr


def test_eager_validation_skips_db_open_on_missing_expected_positions_file() -> None:
    # The DB path is intentionally also bogus; the missing-expected-positions
    # error must fire first so the operator sees that error rather than the
    # DB error. This locks in the eager-validation ordering.
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        missing_db = temp / "no_db.db"
        missing_exp = temp / "no_exp.json"
        stdout, stderr, code = _run_cli(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(missing_db),
                "--expected-positions",
                str(missing_exp),
                "--show-reconciliation",
            ]
        )
    assert code == 1
    assert stdout == ""
    assert "expected-positions file not found" in stderr
    assert "insider-cluster DB" not in stderr


# ---------------------------------------------------------------------------
# 6. --expected-positions rejected on --source synthetic
# ---------------------------------------------------------------------------


def test_expected_positions_rejected_on_synthetic_source() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        bad = Path(raw_temp) / "match.json"
        bad.write_text('{"positions": []}', encoding="utf-8")
        # Empty positions is allowed by the loader; the rejection is the
        # argparse-level synthetic-source guard.
        _, stderr, code = _run_cli(["--source", "synthetic", "--expected-positions", str(bad)])
    assert code == 2
    assert "insider_cluster" in stderr


# ---------------------------------------------------------------------------
# Pure loader unit tests (no CLI)
# ---------------------------------------------------------------------------


def test_load_expected_positions_sorts_by_symbol_ascending() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        unsorted_path = temp / "unsorted.json"
        unsorted_path.write_text(
            '{"positions": ['
            '{"symbol": "MSFT", "quantity": 5}, '
            '{"symbol": "AAPL", "quantity": 10}'
            "]}",
            encoding="utf-8",
        )
        loaded = load_expected_positions(unsorted_path)
    assert loaded.positions == (("AAPL", 10), ("MSFT", 5))


def test_load_expected_positions_accepts_empty_positions_array() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        path = Path(raw_temp) / "empty.json"
        path.write_text('{"positions": []}', encoding="utf-8")
        loaded = load_expected_positions(path)
    assert loaded.positions == ()


def test_load_expected_positions_raises_schema_error_on_top_level_list() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        path = Path(raw_temp) / "list.json"
        path.write_text("[]", encoding="utf-8")
        raised: BaseException | None = None
        try:
            load_expected_positions(path)
        except ExpectedPositionsSchemaError as exc:
            raised = exc
    assert isinstance(raised, ExpectedPositionsSchemaError)
    assert "top-level value" in str(raised)


def test_load_expected_positions_rejects_bool_quantity() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        path = Path(raw_temp) / "bool.json"
        path.write_text('{"positions": [{"symbol": "NKE", "quantity": true}]}', encoding="utf-8")
        raised: BaseException | None = None
        try:
            load_expected_positions(path)
        except ExpectedPositionsSchemaError as exc:
            raised = exc
    assert isinstance(raised, ExpectedPositionsSchemaError)
    assert "must be an integer" in str(raised)
