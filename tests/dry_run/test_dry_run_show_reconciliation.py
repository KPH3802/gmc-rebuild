"""Tests for the ``--show-reconciliation`` opt-in flag (P6-12).

Tripwires:

1. **Back-compat**: the no-flag stdout of ``python -m gmc_rebuild.dry_run
   --source insider_cluster`` is byte-for-byte identical to the locked
   ``_EXPECTED_NO_FLAG_STDOUT`` literal — proving the new flag changes
   nothing unless it is explicitly passed.
2. **``--show-reconciliation`` appends the documented MATCH block** for
   the NKE fixture (self-comparison of the simulated portfolio).
3. **``--show-reconciliation`` is rejected on ``--source synthetic``**.
4. **``--show-reconciliation`` creates no files** in the run directory.
5. **The three opt-in flags combine independently** in one run: each
   surface (text block on stdout, decisions JSON file, reconciliation
   JSON file) is produced; the human summary is unchanged ahead of them.
6. **Pure formatter** ``format_dry_run_reconciliation_block`` renders the
   documented shape for MATCH and MISMATCH P6-09 results, with ``(none)``
   placeholders for empty lists.

Mirrors the no-``pytest.raises`` convention used by the sibling
``test_dry_run_emit_json.py`` and ``test_dry_run_emit_reconciliation_json.py``
suites.

Authorization: ``governance/authorizations/2026-06-20_p6-12.md``.
"""

from __future__ import annotations

import io
import json
import shutil
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from gmc_rebuild.dry_run.__main__ import main as cli_main
from gmc_rebuild.dry_run._loop import format_dry_run_reconciliation_block
from gmc_rebuild.dry_run_reconciliation import (
    DryRunReconciliationOutcome,
    DryRunReconciliationResult,
    ReconciliationQuantityMismatch,
)
from gmc_rebuild.risk import ReconciliationStatus

_FIXTURE: Path = (
    Path(__file__).resolve().parents[1] / "insider_cluster_intake" / "fixtures" / "sample.db"
)


# Committed back-compat tripwire: the human summary that precedes any block.
# Identical to the locked literal in test_dry_run_emit_reconciliation_json.py.
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


# The reconciliation text block for the NKE fixture: a self-comparison of
# the simulated portfolio against ExpectedPositions.from_simulated_portfolio,
# which is MATCH by construction (every simulated position matches).
_EXPECTED_NKE_RECONCILIATION_BLOCK: str = (
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


def _copy_fixture(temp_dir: Path) -> Path:
    dst = temp_dir / "sample.db"
    shutil.copy(_FIXTURE, dst)
    return dst


def _capture_main_stdout(argv: list[str]) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        cli_main(argv)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. Back-compat: no-flag stdout is byte-for-byte unchanged
# ---------------------------------------------------------------------------


def test_no_flag_stdout_is_byte_for_byte_unchanged() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        db_copy = _copy_fixture(Path(raw_temp))
        stdout = _capture_main_stdout(["--source", "insider_cluster", "--db", str(db_copy)])
    assert stdout == _EXPECTED_NO_FLAG_STDOUT


# ---------------------------------------------------------------------------
# 2. --show-reconciliation appends the documented MATCH block
# ---------------------------------------------------------------------------


def test_show_reconciliation_appends_documented_block_for_nke_fixture() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        db_copy = _copy_fixture(Path(raw_temp))
        stdout = _capture_main_stdout(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db_copy),
                "--show-reconciliation",
            ]
        )
    assert stdout == _EXPECTED_NO_FLAG_STDOUT + _EXPECTED_NKE_RECONCILIATION_BLOCK


def test_show_reconciliation_block_is_appended_after_existing_summary() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        db_copy = _copy_fixture(Path(raw_temp))
        stdout = _capture_main_stdout(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db_copy),
                "--show-reconciliation",
            ]
        )
    summary_end = stdout.index("dry_run_reconciliation:")
    summary = stdout[:summary_end]
    # The existing summary, with a trailing blank-line separator, must be
    # byte-for-byte unchanged ahead of the new block.
    assert summary == _EXPECTED_NO_FLAG_STDOUT + "\n"


# ---------------------------------------------------------------------------
# 3. --show-reconciliation rejected on --source synthetic
# ---------------------------------------------------------------------------


def test_show_reconciliation_rejected_on_synthetic_source() -> None:
    stderr_buf = io.StringIO()
    raised: BaseException | None = None
    try:
        with redirect_stderr(stderr_buf), redirect_stdout(io.StringIO()):
            cli_main(["--source", "synthetic", "--show-reconciliation"])
    except SystemExit as exc:
        raised = exc
    assert isinstance(raised, SystemExit), "argparse should have exited"
    assert raised.code != 0
    assert "insider_cluster" in stderr_buf.getvalue()


# ---------------------------------------------------------------------------
# 4. --show-reconciliation creates no files
# ---------------------------------------------------------------------------


def test_show_reconciliation_creates_no_files_in_the_run_directory() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db_copy = _copy_fixture(temp)
        before = sorted(p.name for p in temp.iterdir())
        _capture_main_stdout(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db_copy),
                "--show-reconciliation",
            ]
        )
        after = sorted(p.name for p in temp.iterdir())
    assert before == after == ["sample.db"]


# ---------------------------------------------------------------------------
# 5. Three opt-in flags combine independently in one run
# ---------------------------------------------------------------------------


def test_all_three_flags_combine_in_one_run() -> None:
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
                "--show-reconciliation",
            ]
        )
        # Human summary + text block on stdout; both files written.
        assert decisions_path.is_file()
        assert reconciliation_path.is_file()
        reconciliation_payload = json.loads(reconciliation_path.read_text())
        decisions_payload = json.loads(decisions_path.read_text())
    assert stdout == _EXPECTED_NO_FLAG_STDOUT + _EXPECTED_NKE_RECONCILIATION_BLOCK
    # The JSON payloads are still the P6-10 / P6-11 shapes, proving the
    # text flag does not change them.
    assert reconciliation_payload["outcome"] == "MATCH"
    assert reconciliation_payload["matches"] == [{"symbol": "NKE", "quantity": 163}]
    assert decisions_payload["decisions"][0]["symbol"] == "NKE"


def test_show_reconciliation_alone_writes_no_json_files() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db_copy = _copy_fixture(temp)
        before = sorted(p.name for p in temp.iterdir())
        _capture_main_stdout(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db_copy),
                "--show-reconciliation",
            ]
        )
        after = sorted(p.name for p in temp.iterdir())
    assert before == after == ["sample.db"]


# ---------------------------------------------------------------------------
# 6. Pure formatter: MATCH / MISMATCH / empty-list rendering
# ---------------------------------------------------------------------------


def _build_match_result() -> DryRunReconciliationResult:
    return DryRunReconciliationResult(
        outcome=DryRunReconciliationOutcome.MATCH,
        matches=(("AAPL", 10), ("MSFT", -5)),
        quantity_mismatches=(),
        only_in_simulated=(),
        only_in_expected=(),
        reconciliation_status=ReconciliationStatus.CLEAN,
    )


def _build_mismatch_result() -> DryRunReconciliationResult:
    return DryRunReconciliationResult(
        outcome=DryRunReconciliationOutcome.MISMATCH,
        matches=(("AAPL", 10),),
        quantity_mismatches=(
            ReconciliationQuantityMismatch(
                symbol="MSFT", simulated_quantity=7, expected_quantity=5
            ),
        ),
        only_in_simulated=(("NVDA", 3),),
        only_in_expected=(("TSLA", -2),),
        reconciliation_status=ReconciliationStatus.FAILED,
    )


def test_format_block_renders_match_with_empty_sections_as_none() -> None:
    rendered = format_dry_run_reconciliation_block(_build_match_result())
    assert rendered == (
        "\n"
        "dry_run_reconciliation:\n"
        "  outcome: MATCH\n"
        "  status: clean\n"
        "  summary: 2 matches, 0 quantity_mismatches, 0 only_in_simulated, "
        "0 only_in_expected\n"
        "  matches:\n"
        "    - AAPL: 10\n"
        "    - MSFT: -5\n"
        "  quantity_mismatches:\n"
        "    (none)\n"
        "  only_in_simulated:\n"
        "    (none)\n"
        "  only_in_expected:\n"
        "    (none)"
    )


def test_format_block_renders_mismatch_with_all_four_sections_populated() -> None:
    rendered = format_dry_run_reconciliation_block(_build_mismatch_result())
    assert rendered == (
        "\n"
        "dry_run_reconciliation:\n"
        "  outcome: MISMATCH\n"
        "  status: failed\n"
        "  summary: 1 matches, 1 quantity_mismatches, 1 only_in_simulated, "
        "1 only_in_expected\n"
        "  matches:\n"
        "    - AAPL: 10\n"
        "  quantity_mismatches:\n"
        "    - MSFT: simulated=7 expected=5\n"
        "  only_in_simulated:\n"
        "    - NVDA: 3\n"
        "  only_in_expected:\n"
        "    - TSLA: -2"
    )


def test_format_block_is_deterministic_for_identical_input() -> None:
    result = _build_match_result()
    assert format_dry_run_reconciliation_block(result) == format_dry_run_reconciliation_block(
        result
    )


def test_format_block_rejects_non_reconciliation_result() -> None:
    raised: BaseException | None = None
    try:
        format_dry_run_reconciliation_block("not a result")  # type: ignore[arg-type]
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "DryRunReconciliationResult" in str(raised)
