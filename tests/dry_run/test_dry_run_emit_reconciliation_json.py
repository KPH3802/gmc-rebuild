"""Tests for the ``--emit-reconciliation-json`` opt-in flag (P6-11).

Tripwires:

1. **Back-compat**: the no-flag stdout of ``python -m gmc_rebuild.dry_run
   --source insider_cluster`` is byte-for-byte identical to the locked
   ``_EXPECTED_NO_FLAG_STDOUT`` literal — proving the new flag changes
   nothing unless it is explicitly passed.
2. **--emit-reconciliation-json <path> writes the documented MATCH shape**
   for the NKE fixture (self-comparison of the simulated portfolio).
3. **--emit-reconciliation-json - streams the same payload to stdout** and
   creates no file; the human summary is unchanged ahead of it.
4. **stdout and file payloads are byte-for-byte equal** for the same run.
5. **absent flag ⇒ no filesystem write** anywhere in the run.
6. **--emit-reconciliation-json is rejected on ``--source synthetic``.**
7. **both flags combine**: ``--emit-json`` and
   ``--emit-reconciliation-json`` may be passed in one run; each writes its
   own documented payload and the two are independent.

Mirrors the no-``pytest.raises`` convention used by the sibling
``tests/dry_run/test_dry_run_emit_json.py`` suite.

Authorization: ``governance/authorizations/2026-06-20_p6-11.md``.
"""

from __future__ import annotations

import io
import json
import shutil
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from gmc_rebuild.dry_run.__main__ import main as cli_main

_FIXTURE: Path = (
    Path(__file__).resolve().parents[1] / "insider_cluster_intake" / "fixtures" / "sample.db"
)


# Committed back-compat tripwire: the human summary that precedes any JSON.
# Identical to the locked literal in test_dry_run_emit_json.py.
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


# The reconciliation payload for the NKE fixture: a self-comparison of the
# simulated portfolio against ExpectedPositions.from_simulated_portfolio,
# which is MATCH by construction (every simulated position matches).
_EXPECTED_NKE_RECONCILIATION_PAYLOAD: dict[str, object] = {
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


def _copy_fixture(temp_dir: Path) -> Path:
    dst = temp_dir / "sample.db"
    shutil.copy(_FIXTURE, dst)
    return dst


def _capture_main_stdout(argv: list[str]) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        cli_main(argv)
    return buf.getvalue()


def _split_summary_and_json(stdout: str) -> tuple[str, dict[str, object]]:
    """Split combined stdout into the human summary and the trailing JSON.

    The CLI prints the human summary first, then the JSON object; the JSON
    object always begins at the first ``{`` on its own line.
    """
    brace_idx = stdout.index("\n{") + 1
    summary = stdout[:brace_idx]
    payload = json.loads(stdout[brace_idx:])
    assert isinstance(payload, dict)
    return summary, payload


# ---------------------------------------------------------------------------
# 1. Back-compat: no-flag stdout is byte-for-byte unchanged
# ---------------------------------------------------------------------------


def test_no_flag_stdout_is_byte_for_byte_unchanged() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        db_copy = _copy_fixture(Path(raw_temp))
        stdout = _capture_main_stdout(["--source", "insider_cluster", "--db", str(db_copy)])
    assert stdout == _EXPECTED_NO_FLAG_STDOUT


# ---------------------------------------------------------------------------
# 2. --emit-reconciliation-json <path> writes the documented MATCH shape
# ---------------------------------------------------------------------------


def test_emit_reconciliation_json_writes_documented_shape_for_nke_fixture() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db_copy = _copy_fixture(temp)
        out_path = temp / "reconciliation.json"
        stdout = _capture_main_stdout(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db_copy),
                "--emit-reconciliation-json",
                str(out_path),
            ]
        )
        # Human summary still printed (no stdout regression).
        assert stdout == _EXPECTED_NO_FLAG_STDOUT
        assert out_path.is_file(), "--emit-reconciliation-json did not write the file"
        payload = json.loads(out_path.read_text())
    assert payload == _EXPECTED_NKE_RECONCILIATION_PAYLOAD


def test_emit_reconciliation_json_output_is_pretty_printed_and_sorted() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db_copy = _copy_fixture(temp)
        out_path = temp / "reconciliation.json"
        _capture_main_stdout(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db_copy),
                "--emit-reconciliation-json",
                str(out_path),
            ]
        )
        text = out_path.read_text()
    # Pretty-printed = multi-line.
    assert "\n" in text
    # Sorted keys: 'matches' (m) precedes 'outcome' (o) precedes 'summary' (s).
    matches_idx = text.index('"matches"')
    outcome_idx = text.index('"outcome"')
    summary_idx = text.index('"summary"')
    assert matches_idx < outcome_idx < summary_idx


# ---------------------------------------------------------------------------
# 3 & 4. --emit-reconciliation-json - streams to stdout; equals file payload
# ---------------------------------------------------------------------------


def test_emit_reconciliation_json_dash_streams_to_stdout_and_creates_no_file() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db_copy = _copy_fixture(temp)
        before = sorted(p.name for p in temp.iterdir())
        stdout = _capture_main_stdout(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db_copy),
                "--emit-reconciliation-json",
                "-",
            ]
        )
        after = sorted(p.name for p in temp.iterdir())
    assert before == after == ["sample.db"]
    summary, payload = _split_summary_and_json(stdout)
    assert summary == _EXPECTED_NO_FLAG_STDOUT
    assert payload == _EXPECTED_NKE_RECONCILIATION_PAYLOAD


def test_emit_reconciliation_json_dash_matches_file_payload_byte_for_byte() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db_copy = _copy_fixture(temp)
        out_path = temp / "reconciliation.json"
        file_run_stdout = _capture_main_stdout(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db_copy),
                "--emit-reconciliation-json",
                str(out_path),
            ]
        )
        file_json = out_path.read_text()
        dash_stdout = _capture_main_stdout(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db_copy),
                "--emit-reconciliation-json",
                "-",
            ]
        )
    # The dash run's stdout is the human summary followed by the file JSON.
    assert dash_stdout == file_run_stdout + file_json


# ---------------------------------------------------------------------------
# 5. absent flag ⇒ no filesystem write
# ---------------------------------------------------------------------------


def test_no_flag_creates_no_files_in_the_run_directory() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db_copy = _copy_fixture(temp)
        before = sorted(p.name for p in temp.iterdir())
        _capture_main_stdout(["--source", "insider_cluster", "--db", str(db_copy)])
        after = sorted(p.name for p in temp.iterdir())
    assert before == after == ["sample.db"]


# ---------------------------------------------------------------------------
# 6. --emit-reconciliation-json rejected on --source synthetic
# ---------------------------------------------------------------------------


def test_emit_reconciliation_json_rejected_on_synthetic_source() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        out_path = Path(raw_temp) / "reconciliation.json"
        stderr_buf = io.StringIO()
        raised: BaseException | None = None
        try:
            with redirect_stderr(stderr_buf), redirect_stdout(io.StringIO()):
                cli_main(["--source", "synthetic", "--emit-reconciliation-json", str(out_path)])
        except SystemExit as exc:
            raised = exc
        assert isinstance(raised, SystemExit), "argparse should have exited"
        assert raised.code != 0
        assert "insider_cluster" in stderr_buf.getvalue()
        assert not out_path.exists()


def test_emit_reconciliation_json_dash_rejected_on_synthetic_source() -> None:
    stderr_buf = io.StringIO()
    raised: BaseException | None = None
    try:
        with redirect_stderr(stderr_buf), redirect_stdout(io.StringIO()):
            cli_main(["--source", "synthetic", "--emit-reconciliation-json", "-"])
    except SystemExit as exc:
        raised = exc
    assert isinstance(raised, SystemExit)
    assert raised.code != 0
    assert "insider_cluster" in stderr_buf.getvalue()


# ---------------------------------------------------------------------------
# 7. both flags combine independently in one run
# ---------------------------------------------------------------------------


def test_both_emit_flags_combine_in_one_run() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db_copy = _copy_fixture(temp)
        decisions_path = temp / "decisions.json"
        reconciliation_path = temp / "reconciliation.json"
        stdout = _capture_main_stdout(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db_copy),
                "--emit-json",
                str(decisions_path),
                "--emit-reconciliation-json",
                str(reconciliation_path),
            ]
        )
        # Human summary unchanged; both files written.
        assert stdout == _EXPECTED_NO_FLAG_STDOUT
        assert decisions_path.is_file()
        assert reconciliation_path.is_file()
        reconciliation_payload = json.loads(reconciliation_path.read_text())
        decisions_payload = json.loads(decisions_path.read_text())
    assert reconciliation_payload == _EXPECTED_NKE_RECONCILIATION_PAYLOAD
    # The decisions payload is the P6 decision shape, not the reconciliation
    # shape — proving the two flags are independent.
    assert decisions_payload["decisions"][0]["symbol"] == "NKE"
    assert "outcome" not in decisions_payload
