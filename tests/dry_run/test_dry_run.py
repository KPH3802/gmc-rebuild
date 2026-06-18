"""Dry-run entrypoint end-to-end tests (P6-DRYRUN-ENTRYPOINT).

Composes the merged P6-01..P6-07 surface into a single runnable loop and
asserts that the loop produces a deterministic :class:`DailyReport` with
the expected per-outcome counts. Mirrors the try/except convention used
by ``tests/reporting/test_reporting.py`` and the other P6-NN tests
(no ``pytest.raises``, no fixture-typed parameters).
"""

from __future__ import annotations

from gmc_rebuild.dry_run import format_report, run_dry_run
from gmc_rebuild.reporting import DailyReport
from gmc_rebuild.risk import ReconciliationStatus


def test_run_dry_run_returns_a_daily_report() -> None:
    report = run_dry_run()
    assert isinstance(report, DailyReport)


def test_run_dry_run_counts_match_expected_sample() -> None:
    """Three hardcoded sample signals: two clear-through (would_trade),
    one ineligible (would_skip). Counts must reconcile with
    ``decisions_total``."""
    report = run_dry_run()
    assert report.decisions_total == 3
    assert report.would_trade == 2
    assert report.would_skip == 1
    assert report.would_trade + report.would_skip == report.decisions_total


def test_run_dry_run_applies_traded_intents_to_portfolio() -> None:
    """Each ``WOULD_TRADE`` decision lands a simulated order intent ID
    in the end-of-cycle portfolio's ``applied_intent_ids`` tuple."""
    report = run_dry_run()
    assert len(report.applied_intent_ids) == report.would_trade
    # Canonical (sorted, unique) tuple per ``SimulatedPortfolio``.
    assert list(report.applied_intent_ids) == sorted(report.applied_intent_ids)
    assert len(set(report.applied_intent_ids)) == len(report.applied_intent_ids)


def test_run_dry_run_reports_clean_reconciliation_status() -> None:
    report = run_dry_run()
    assert report.reconciliation_status is ReconciliationStatus.CLEAN


def test_run_dry_run_is_deterministic() -> None:
    """Two calls with no arguments return byte-for-byte identical reports."""
    assert run_dry_run() == run_dry_run()


def test_format_report_includes_human_readable_summary() -> None:
    report = run_dry_run()
    text = format_report(report)
    assert isinstance(text, str)
    assert text  # non-empty
    assert report.report_date in text
    # Decision counts must surface as readable lines.
    assert "would_trade" in text or "would-trade" in text
    assert "would_skip" in text or "would-skip" in text
    assert "reconciliation" in text
