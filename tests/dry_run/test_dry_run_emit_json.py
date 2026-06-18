"""Tests for the ``--emit-json`` opt-in flag on the dry-run entry point.

Five tripwires:

1. **Back-compat**: the no-flag stdout of ``python -m gmc_rebuild.dry_run
   --source insider_cluster`` is byte-for-byte identical to the locked
   ``_EXPECTED_NO_FLAG_STDOUT`` literal — any output drift breaks this
   test immediately. The literal is captured from ``main`` at commit
   ``a808ed7`` (PR #189).
2. **--emit-json writes the documented shape** for the NKE fixture.
3. **--emit-json absent ⇒ no filesystem write** anywhere in the run.
4. **--emit-json is rejected on ``--source synthetic``** (scope of this
   PR is the insider-cluster path only).
5. **Helper unit test**: ``build_decisions_json_payload`` produces the
   same shape directly, without going through the CLI.

Mirrors the no-``pytest.raises`` convention used by the other
``tests/<layer>/`` tests.

Authorization: ``governance/authorizations/2026-06-18_dry-run-emit-json.md``.
"""

from __future__ import annotations

import io
import json
import shutil
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from gmc_rebuild.dry_run import build_decisions_json_payload
from gmc_rebuild.dry_run.__main__ import main as cli_main
from gmc_rebuild.dry_run._loop import _run_insider_cluster_cycle

_FIXTURE: Path = (
    Path(__file__).resolve().parents[1] / "insider_cluster_intake" / "fixtures" / "sample.db"
)


# Committed back-compat tripwire: captured from `main` at commit a808ed7
# (PR #189). Any change to the no-flag stdout breaks this test on purpose.
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


_EXPECTED_NKE_PAYLOAD: dict[str, object] = {
    "as_of": "2026-06-18",
    "decisions": [
        {
            "symbol": "NKE",
            "side": "BUY",
            "quantity": 163,
            "outcome": "WOULD_TRADE",
            "rationale": "3 insiders; $4.45M cluster; roles: CEO,Director",
            "verdict_clear": True,
        }
    ],
    "summary": {
        "total": 1,
        "would_trade": 1,
        "would_skip": 0,
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


# ---------------------------------------------------------------------------
# 1. Back-compat: no-flag stdout is byte-for-byte unchanged from current main
# ---------------------------------------------------------------------------


def test_no_flag_stdout_is_byte_for_byte_unchanged_from_main() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        db_copy = _copy_fixture(Path(raw_temp))
        stdout = _capture_main_stdout(["--source", "insider_cluster", "--db", str(db_copy)])
    assert stdout == _EXPECTED_NO_FLAG_STDOUT


# ---------------------------------------------------------------------------
# 2. --emit-json writes the documented shape for the NKE fixture
# ---------------------------------------------------------------------------


def test_emit_json_writes_documented_shape_for_nke_fixture() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db_copy = _copy_fixture(temp)
        out_path = temp / "decisions.json"
        stdout = _capture_main_stdout(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db_copy),
                "--emit-json",
                str(out_path),
            ]
        )
        # Human summary still printed (no stdout regression).
        assert "WOULD_TRADE" in stdout
        assert "safety_verdict" in stdout
        # JSON file written with the documented shape.
        assert out_path.is_file(), "--emit-json did not write the file"
        payload = json.loads(out_path.read_text())

    assert payload == _EXPECTED_NKE_PAYLOAD


def test_emit_json_output_is_pretty_printed_and_sorted_deterministically() -> None:
    """The on-disk file is JSON-pretty-printed with ``sort_keys=True`` so
    text diffs across runs are stable."""
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        db_copy = _copy_fixture(temp)
        out_path = temp / "decisions.json"
        _capture_main_stdout(
            [
                "--source",
                "insider_cluster",
                "--db",
                str(db_copy),
                "--emit-json",
                str(out_path),
            ]
        )
        text = out_path.read_text()
    # Pretty-printed = multi-line.
    assert "\n" in text
    # Sorted keys: 'as_of' (a) precedes 'decisions' (d) precedes 'summary' (s).
    as_of_idx = text.index('"as_of"')
    decisions_idx = text.index('"decisions"')
    summary_idx = text.index('"summary"')
    assert as_of_idx < decisions_idx < summary_idx


# ---------------------------------------------------------------------------
# 3. --emit-json absent ⇒ no filesystem write anywhere in the run
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
# 4. --emit-json rejected on --source synthetic
# ---------------------------------------------------------------------------


def test_emit_json_rejected_on_synthetic_source() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        out_path = Path(raw_temp) / "decisions.json"
        stderr_buf = io.StringIO()
        raised: BaseException | None = None
        try:
            with redirect_stderr(stderr_buf), redirect_stdout(io.StringIO()):
                cli_main(
                    [
                        "--source",
                        "synthetic",
                        "--emit-json",
                        str(out_path),
                    ]
                )
        except SystemExit as exc:
            raised = exc
        assert isinstance(raised, SystemExit), "argparse should have exited"
        assert raised.code != 0
        assert "insider_cluster" in stderr_buf.getvalue()
        assert not out_path.exists()


# ---------------------------------------------------------------------------
# 5. build_decisions_json_payload helper unit test
# ---------------------------------------------------------------------------


def test_build_decisions_json_payload_produces_documented_shape() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        db_copy = _copy_fixture(Path(raw_temp))
        cycle = _run_insider_cluster_cycle(db_copy)
    payload = build_decisions_json_payload(
        report=cycle.report,
        verdict=cycle.verdict,
        decisions=(cycle.decision,),
        signals=(cycle.signal,),
    )
    assert payload == _EXPECTED_NKE_PAYLOAD


def test_build_decisions_json_payload_rejects_length_mismatch() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        db_copy = _copy_fixture(Path(raw_temp))
        cycle = _run_insider_cluster_cycle(db_copy)
    raised: BaseException | None = None
    try:
        build_decisions_json_payload(
            report=cycle.report,
            verdict=cycle.verdict,
            decisions=(cycle.decision,),
            signals=(),  # mismatch
        )
    except ValueError as exc:
        raised = exc
    assert isinstance(raised, ValueError)
    assert "same length" in str(raised) or "length" in str(raised).lower()
