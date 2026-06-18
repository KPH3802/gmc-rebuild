"""Internal dry-run composition module.

See :mod:`gmc_rebuild.dry_run` for the package-level docstring and the
authorization reference.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any

from gmc_rebuild.decision import (
    PositionDecision,
    PositionDecisionOutcome,
    compose_position_decision,
)
from gmc_rebuild.eligibility import EligibilityConfig, check_eligibility
from gmc_rebuild.insider_cluster_intake import load_insider_cluster_signal
from gmc_rebuild.portfolio_state import SimulatedPortfolio, apply_simulated_order_intent
from gmc_rebuild.reporting import DailyReport, build_daily_report
from gmc_rebuild.risk import HeartbeatStatus, KillSwitchState, ReconciliationStatus
from gmc_rebuild.runtime import SafetyVerdict
from gmc_rebuild.signal_intake import SignalIntent, SignalSide, accept_signal_intent
from gmc_rebuild.simulation import (
    SimulatedOrderIntent,
    SimulatedOrderSide,
    SimulatedOrderTimeInForce,
    SimulatedOrderType,
    SimulationBoundary,
    SimulationLane,
    derive_simulated_order_intent_id,
)

_REPORT_DATE: str = "2026-06-18"
_OBSERVED_AT: str = "2026-06-18T00:00:00Z"
_FIXED_TIMESTAMP: datetime = datetime(2026, 6, 18, 12, 0, 0, tzinfo=UTC)


def _clear_safety_verdict() -> SafetyVerdict:
    """A real ``clear`` :class:`SafetyVerdict` constructed the same way
    the merged ``tests/reporting/test_reporting.py`` and
    ``tests/operator_view/test_operator_view.py`` helpers build one."""
    return SafetyVerdict(
        clear=True,
        blockers=(),
        heartbeat_statuses=MappingProxyType({"operator": HeartbeatStatus.FRESH}),
        kill_switch_state=KillSwitchState.ARMED,
        reconciliation_status=ReconciliationStatus.CLEAN,
        observed_at=_OBSERVED_AT,
    )


def _eligibility_config() -> EligibilityConfig:
    return EligibilityConfig(
        allowed_symbols=frozenset({"SIM-ALPHA", "SIM-BETA"}),
        allowed_sides=frozenset({SignalSide.BUY, SignalSide.SELL}),
        min_quantity=1,
        max_quantity=1_000,
        min_rationale_length=5,
    )


# Three hardcoded sample signals. Two land in the eligibility config and
# should clear the pipeline to ``WOULD_TRADE``; the third uses a symbol
# outside ``allowed_symbols`` and is therefore ``INELIGIBLE`` →
# ``WOULD_SKIP``.
_SAMPLE_SIGNALS: tuple[SignalIntent, ...] = (
    SignalIntent(
        intent_id="sig-alpha-buy",
        symbol="SIM-ALPHA",
        side=SignalSide.BUY,
        quantity=10,
        rationale="dry-run fixture: alpha long entry",
    ),
    SignalIntent(
        intent_id="sig-beta-sell",
        symbol="SIM-BETA",
        side=SignalSide.SELL,
        quantity=5,
        rationale="dry-run fixture: beta short entry",
    ),
    SignalIntent(
        intent_id="sig-gamma-buy",
        symbol="SIM-GAMMA",  # not in allowed_symbols → INELIGIBLE
        side=SignalSide.BUY,
        quantity=7,
        rationale="dry-run fixture: gamma rejected entry",
    ),
)


def _order_intent_for(signal: SignalIntent) -> SimulatedOrderIntent:
    """Map a :class:`SignalIntent` onto a deterministic LOCAL_ONLY
    :class:`SimulatedOrderIntent` (market order, day-tif)."""
    side = SimulatedOrderSide.BUY if signal.side is SignalSide.BUY else SimulatedOrderSide.SELL
    intent_id = derive_simulated_order_intent_id(
        lane=SimulationLane.LOCAL_ONLY,
        symbol=signal.symbol,
        side=side,
        quantity=signal.quantity,
        order_type=SimulatedOrderType.MARKET,
        limit_price=None,
        time_in_force=SimulatedOrderTimeInForce.DAY,
        created_at=_OBSERVED_AT,
    )
    return SimulatedOrderIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_OBSERVED_AT,
        symbol=signal.symbol,
        side=side,
        quantity=signal.quantity,
        order_type=SimulatedOrderType.MARKET,
        limit_price=None,
        time_in_force=SimulatedOrderTimeInForce.DAY,
    )


def run_dry_run() -> DailyReport:
    """Run the dry-run loop over the hardcoded sample signals.

    Pure, deterministic, side-effect free. Returns the resulting
    :class:`~gmc_rebuild.reporting.DailyReport` value object. Threads
    each signal through:

      :func:`accept_signal_intent` (P6-01) →
      :func:`check_eligibility` (P6-02) →
      :func:`compose_position_decision` against a clear
      :class:`SafetyVerdict` (P6-03 / P4-06) →
      :meth:`SimulationBoundary.propose_order` on the
      ``LOCAL_ONLY`` lane (P5-01 / P5-02 / P6-04) →
      :func:`apply_simulated_order_intent` into the running
      :class:`SimulatedPortfolio` (P6-05) →
      :func:`build_daily_report` at end-of-cycle (P6-06).
    """
    config = _eligibility_config()
    verdict = _clear_safety_verdict()
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)

    decisions: list[PositionDecision] = []
    portfolio = SimulatedPortfolio.empty()

    for raw_signal in _SAMPLE_SIGNALS:
        intent = accept_signal_intent(raw_signal)
        eligibility = check_eligibility(intent, config)
        decision = compose_position_decision(intent, eligibility, verdict)
        decisions.append(decision)

        if decision.outcome is PositionDecisionOutcome.WOULD_TRADE:
            order_intent = _order_intent_for(intent)
            # Gate the order intent through the local simulation boundary;
            # returns the same intent by identity on the clear path.
            boundary.propose_order(order_intent=order_intent, verdict=verdict)
            portfolio = apply_simulated_order_intent(
                portfolio, decision=decision, order_intent=order_intent
            )

    return build_daily_report(
        report_date=_REPORT_DATE,
        decisions=tuple(decisions),
        portfolio=portfolio,
        reconciliation_status=ReconciliationStatus.CLEAN,
    )


def format_report(report: DailyReport) -> str:
    """Return a deterministic multi-line human-readable rendering of
    ``report``. No I/O. The :mod:`gmc_rebuild.dry_run.__main__` module
    is the only caller that prints the result to stdout."""
    if not isinstance(report, DailyReport):
        raise TypeError(f"report must be a DailyReport, got {type(report).__name__}")

    lines: list[str] = [
        f"daily_report: {report.report_date}",
        (
            f"decisions: {report.decisions_total} total, "
            f"{report.would_trade} would_trade, {report.would_skip} would_skip"
        ),
        f"reconciliation: {report.reconciliation_status.value}",
        "net_positions:",
    ]
    if report.net_positions:
        for symbol, quantity in report.net_positions:
            lines.append(f"  - {symbol}: {quantity}")
    else:
        lines.append("  (none)")

    lines.append("applied_intent_ids:")
    if report.applied_intent_ids:
        for intent_id in report.applied_intent_ids:
            lines.append(f"  - {intent_id}")
    else:
        lines.append("  (none)")

    if report.tripped_invariants:
        lines.append("tripped_invariants:")
        for code in report.tripped_invariants:
            lines.append(f"  - {code}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Insider-cluster path (real-signal source)
# ---------------------------------------------------------------------------


def _eligibility_config_for(signal: SignalIntent) -> EligibilityConfig:
    """Build a permissive but typed eligibility config for ONE caller-
    chosen symbol.

    The operator has already decided to act on this signal (by passing
    its DB), so ``allowed_symbols`` is the singleton ``{signal.symbol}``.
    This is intentionally *not* a maintained universe — the eligibility
    gate's job in this dry-run path is to exercise the type discipline
    end-to-end, not to validate the symbol against a research universe.
    """
    return EligibilityConfig(
        allowed_symbols=frozenset({signal.symbol}),
        allowed_sides=frozenset({SignalSide.BUY, SignalSide.SELL}),
        min_quantity=1,
        max_quantity=100_000,
        min_rationale_length=5,
    )


@dataclass(frozen=True, slots=True)
class InsiderClusterCycle:
    """Rich, frozen bundle of the artifacts produced by one
    insider-cluster dry-run cycle.

    The signal is included here (alongside the report / verdict /
    decision) so JSON-export callers can render the human-readable
    fields (``symbol``, ``side``, ``quantity``, ``rationale``) without
    re-opening the source database. ``signal`` is the same value that
    was threaded through ``accept_signal_intent`` → ... → the resulting
    ``decision``.
    """

    report: DailyReport
    verdict: SafetyVerdict
    decision: PositionDecision
    signal: SignalIntent


def _run_insider_cluster_cycle(db_path: Path) -> InsiderClusterCycle:
    """Private rich-bundle variant of the insider-cluster dry-run.

    Same pipeline as :func:`run_dry_run_insider_cluster`; the only
    difference is the return type carries the originating
    :class:`SignalIntent` alongside the report/verdict/decision triple
    so JSON-export callers do not need to re-read the source DB.
    """
    signal = load_insider_cluster_signal(db_path)
    config = _eligibility_config_for(signal)
    verdict = _clear_safety_verdict()
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)

    intent = accept_signal_intent(signal)
    eligibility = check_eligibility(intent, config)
    decision = compose_position_decision(intent, eligibility, verdict)

    portfolio = SimulatedPortfolio.empty()
    if decision.outcome is PositionDecisionOutcome.WOULD_TRADE:
        order_intent = _order_intent_for(intent)
        boundary.propose_order(order_intent=order_intent, verdict=verdict)
        portfolio = apply_simulated_order_intent(
            portfolio, decision=decision, order_intent=order_intent
        )

    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(decision,),
        portfolio=portfolio,
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    return InsiderClusterCycle(report=report, verdict=verdict, decision=decision, signal=signal)


def run_dry_run_insider_cluster(
    db_path: Path,
) -> tuple[DailyReport, SafetyVerdict, PositionDecision]:
    """Run the dry-run loop on ONE real insider-cluster signal.

    Returns the merged-precedent ``(report, verdict, decision)`` triple
    that PR #189 introduced. The public contract is unchanged; callers
    that also need the originating :class:`SignalIntent` should use the
    private :func:`_run_insider_cluster_cycle` instead.

    Pure / deterministic for identical inputs. No network, no broker,
    no order placement.
    """
    cycle = _run_insider_cluster_cycle(db_path)
    return cycle.report, cycle.verdict, cycle.decision


def format_insider_cluster_summary(
    report: DailyReport,
    verdict: SafetyVerdict,
    decision: PositionDecision,
) -> str:
    """Render the daily report, the safety verdict, and a one-line
    decision summary as deterministic plain text."""
    if not isinstance(report, DailyReport):
        raise TypeError(f"report must be a DailyReport, got {type(report).__name__}")
    if not isinstance(verdict, SafetyVerdict):
        raise TypeError(f"verdict must be a SafetyVerdict, got {type(verdict).__name__}")
    if not isinstance(decision, PositionDecision):
        raise TypeError(f"decision must be a PositionDecision, got {type(decision).__name__}")

    blockers_repr = list(verdict.blockers) if verdict.blockers else "none"
    reasons_repr = [reason.value for reason in decision.reasons] if decision.reasons else "none"
    return "\n".join(
        [
            format_report(report),
            "",
            f"safety_verdict: clear={verdict.clear}, blockers={blockers_repr}",
            (f"decision: {decision.outcome.value} {decision.intent_id} reasons={reasons_repr}"),
        ]
    )


def build_decisions_json_payload(
    *,
    report: DailyReport,
    verdict: SafetyVerdict,
    decisions: Sequence[PositionDecision],
    signals: Sequence[SignalIntent],
) -> dict[str, Any]:
    """Build the deterministic JSON-serializable decision payload.

    Pure function. Schema:

    .. code-block:: json

        {
          "as_of": "<DailyReport.report_date>",
          "decisions": [
            {
              "symbol": "<signal.symbol>",
              "side": "<signal.side.value>",
              "quantity": <signal.quantity>,
              "outcome": "<decision.outcome.value>",
              "rationale": "<signal.rationale>",
              "verdict_clear": <bool>
            },
            ...
          ],
          "summary": {
            "total": <DailyReport.decisions_total>,
            "would_trade": <DailyReport.would_trade>,
            "would_skip": <DailyReport.would_skip>
          }
        }

    ``decisions`` and ``signals`` must be the same length and aligned —
    ``signals[i]`` is the :class:`SignalIntent` that produced
    ``decisions[i]``. ``verdict_clear`` is shared across all entries
    because the dry-run loop currently uses a single safety verdict per
    cycle.
    """
    if not isinstance(report, DailyReport):
        raise TypeError(f"report must be a DailyReport, got {type(report).__name__}")
    if not isinstance(verdict, SafetyVerdict):
        raise TypeError(f"verdict must be a SafetyVerdict, got {type(verdict).__name__}")
    if len(decisions) != len(signals):
        raise ValueError(
            "decisions and signals must be the same length "
            f"(got decisions={len(decisions)}, signals={len(signals)})"
        )

    decision_records: list[dict[str, Any]] = []
    for decision, signal in zip(decisions, signals, strict=True):
        if not isinstance(decision, PositionDecision):
            raise TypeError(
                f"decisions members must be PositionDecision, got {type(decision).__name__}"
            )
        if not isinstance(signal, SignalIntent):
            raise TypeError(f"signals members must be SignalIntent, got {type(signal).__name__}")
        decision_records.append(
            {
                "symbol": signal.symbol,
                "side": signal.side.value,
                "quantity": signal.quantity,
                "outcome": decision.outcome.value,
                "rationale": signal.rationale,
                "verdict_clear": verdict.clear,
            }
        )

    return {
        "as_of": report.report_date,
        "decisions": decision_records,
        "summary": {
            "total": report.decisions_total,
            "would_trade": report.would_trade,
            "would_skip": report.would_skip,
        },
    }


__all__ = [
    "FIXED_TIMESTAMP",
    "InsiderClusterCycle",
    "build_decisions_json_payload",
    "format_insider_cluster_summary",
    "format_report",
    "run_dry_run",
    "run_dry_run_insider_cluster",
]


# Re-export the fixed timestamp as a module-level constant so callers
# (e.g. ``__main__``, downstream renderers) that need to pair the report
# with an audit-event timestamp can use the same deterministic value the
# loop itself uses.
FIXED_TIMESTAMP: datetime = _FIXED_TIMESTAMP
