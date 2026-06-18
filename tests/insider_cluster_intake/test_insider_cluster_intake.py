"""End-to-end test for the insider-cluster intake adapter and dry-run path.

Copies the committed fixture ``sample.db`` to a temp path, loads ONE row
via :func:`load_insider_cluster_signal`, asserts the resulting
:class:`SignalIntent` is valid, runs the full insider-cluster dry-run
loop, and asserts the safety verdict is clear and the decision is
``WOULD_TRADE``. Mirrors the no-``pytest.raises`` / no-fixture-parameter
convention used by the other ``tests/<layer>/`` tests.

Authorization: ``governance/authorizations/2026-06-18_insider-cluster-intake.md``.
"""

from __future__ import annotations

import shutil
import sqlite3
import tempfile
from pathlib import Path

from gmc_rebuild.decision import PositionDecisionOutcome
from gmc_rebuild.dry_run._loop import (
    format_insider_cluster_summary,
    run_dry_run_insider_cluster,
)
from gmc_rebuild.insider_cluster_intake import (
    TARGET_NOTIONAL_USD,
    load_insider_cluster_signal,
)
from gmc_rebuild.signal_intake import SignalIntent, SignalSide

_FIXTURE: Path = Path(__file__).resolve().parent / "fixtures" / "sample.db"


def _copy_fixture_to_temp(temp_dir: Path) -> Path:
    """Copy the committed read-only fixture to ``temp_dir/sample.db``.

    The adapter opens the DB in SQLite read-only URI mode, but per the
    operator directive every test path also reads from a *copy* of the
    fixture rather than the committed file itself.
    """
    dst = temp_dir / "sample.db"
    shutil.copy(_FIXTURE, dst)
    return dst


def test_committed_fixture_has_expected_nke_row() -> None:
    """Sanity check on the committed fixture before the adapter touches it."""
    with tempfile.TemporaryDirectory() as raw_temp:
        db_copy = _copy_fixture_to_temp(Path(raw_temp))
        with sqlite3.connect(db_copy) as conn:
            row = conn.execute(
                "SELECT ticker, entry_price, num_insiders, total_dollars, "
                "roles FROM backtest_results"
            ).fetchone()
    assert row is not None
    ticker, entry_price, num_insiders, total_dollars, roles = row
    assert ticker == "NKE"
    assert abs(entry_price - 61.19) < 0.01
    assert num_insiders == 3
    assert abs(total_dollars - 4_449_886.94) < 0.01
    assert roles == "CEO,Director"


def test_adapter_returns_a_valid_signal_intent() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        db_copy = _copy_fixture_to_temp(Path(raw_temp))
        signal = load_insider_cluster_signal(db_copy)
    assert isinstance(signal, SignalIntent)
    assert signal.symbol == "NKE"
    assert signal.side is SignalSide.BUY
    # Deterministic quantity derived from TARGET_NOTIONAL ÷ entry_price,
    # floored to whole shares. With $10k notional and $61.19 entry price
    # → 163 shares.
    expected_quantity = int(TARGET_NOTIONAL_USD / 61.19)
    assert signal.quantity == expected_quantity
    assert signal.quantity > 0
    assert "3 insiders" in signal.rationale
    assert "CEO" in signal.rationale
    # The composed rationale must include the cluster dollars in millions
    # rounded to 2 decimals.
    assert "$4.45M" in signal.rationale or "$4.44M" in signal.rationale


def test_adapter_signal_intent_id_is_deterministic() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        db_copy = _copy_fixture_to_temp(Path(raw_temp))
        first = load_insider_cluster_signal(db_copy)
        second = load_insider_cluster_signal(db_copy)
    assert first.intent_id == second.intent_id
    assert first == second


def test_insider_cluster_dry_run_emits_clear_verdict_and_would_trade() -> None:
    """Full end-to-end: insider-cluster signal → adapter → dry-run loop →
    clear ``SafetyVerdict`` and ``WOULD_TRADE`` decision."""
    with tempfile.TemporaryDirectory() as raw_temp:
        db_copy = _copy_fixture_to_temp(Path(raw_temp))
        report, verdict, decision = run_dry_run_insider_cluster(db_copy)

    # SafetyVerdict must be clear (no blockers).
    assert verdict.clear is True
    assert verdict.blockers == ()

    # Decision must be WOULD_TRADE with no skip reasons.
    assert decision.outcome is PositionDecisionOutcome.WOULD_TRADE
    assert decision.reasons == ()

    # DailyReport must show exactly one would-trade decision and one
    # applied simulated order intent in the end-of-cycle portfolio.
    assert report.decisions_total == 1
    assert report.would_trade == 1
    assert report.would_skip == 0
    assert len(report.applied_intent_ids) == 1
    assert len(report.net_positions) == 1
    assert report.net_positions[0][0] == "NKE"


def test_format_insider_cluster_summary_includes_verdict_and_decision() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        db_copy = _copy_fixture_to_temp(Path(raw_temp))
        report, verdict, decision = run_dry_run_insider_cluster(db_copy)
        summary = format_insider_cluster_summary(report, verdict, decision)
    assert isinstance(summary, str)
    assert "NKE" in summary
    assert "safety_verdict" in summary
    assert "clear=True" in summary
    assert "WOULD_TRADE" in summary
    assert decision.intent_id in summary
