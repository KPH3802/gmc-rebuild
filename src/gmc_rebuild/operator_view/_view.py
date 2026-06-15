"""P6-07 deterministic read-only operator view — internal module.

Defines the frozen, slotted :class:`DryRunOperatorView` value object and the
pure :func:`build_dry_run_operator_view` builder authorized by PR P6-07
(see ``governance/authorizations/2026-06-15_p6-07.md`` and the merged
planning packet ``governance/authorizations/2026-06-15_p6-07-planning.md``).

This module projects the current dry-run engine state — the cycle's P6-03
decisions, the cycle's P6-04 simulated order intents, the end-of-cycle
P6-05 simulated portfolio snapshot, and the P6-06 daily-report summary —
into an operator-facing value object plus a deterministic string render.
It is the seventh Phase 6 dry-run capability, a pure read-only consumer of
P6-03 / P6-04 / P6-05 / P6-06.

Design constraints — these are governance constraints, not stylistic
preferences (``governance/authorizations/2026-06-15_p6-07.md``):

- **Pure consumer of merged upstream values.** Imports only the merged
  ``gmc_rebuild.decision`` / ``gmc_rebuild.simulation`` /
  ``gmc_rebuild.portfolio_state`` / ``gmc_rebuild.reporting`` /
  ``gmc_rebuild.risk`` surfaces, and only by value. Does **not** import
  :mod:`gmc_rebuild.runtime` or compose with the merged P4-07
  ``OperatorSafetyView`` (planning §3.4 default; reserved for the future
  P6-07 successor authorization).
- **No safety-verdict input.** Per the merged planning packet §3.4 default
  and Kevin's implementation directive, the :class:`SafetyVerdict` is
  excluded from the closed input set. Each :class:`PositionDecision`
  carries a ``verdict`` field by value, but this module summarizes only
  the decision ``outcome`` and ``reasons``; it does **not** re-render the
  carried verdict.
- **Deterministic and side-effect free.** Identical inputs yield byte-for-
  byte identical output every call. No global / module-level / class-level
  mutable state, no cache, no counter, no randomness.
- **No clock read.** Any date shown is echoed from the caller-supplied
  :attr:`~gmc_rebuild.reporting.DailyReport.report_date` label; this module
  never calls ``now_utc()`` / ``time.*`` / ``datetime.now()``.
- **No mutation of inputs.** The supplied decisions, order intents,
  portfolio snapshot, and daily report are not modified. All produced
  values are frozen / value-typed.
- **No runtime activation / external I/O.** No ``__main__``, no daemon,
  no scheduler, no network, no filesystem write, no persistence, no
  broker, no account, no market data, no secrets, no env-var read, no
  ``audit_event`` emission.
- **No re-export from package root.** :mod:`gmc_rebuild` is unchanged by
  this packet; the public surface is reachable only via
  ``from gmc_rebuild.operator_view import ...``.
"""

from __future__ import annotations

from dataclasses import dataclass

from gmc_rebuild.decision import PositionDecision, PositionDecisionOutcome
from gmc_rebuild.portfolio_state import SimulatedPortfolio
from gmc_rebuild.reporting import DailyReport
from gmc_rebuild.risk import ReconciliationStatus
from gmc_rebuild.simulation import SimulatedOrderIntent


@dataclass(frozen=True, slots=True)
class DryRunOperatorView:
    """Immutable read-only operator view of one dry-run cycle's engine state.

    Ten closed, value-typed fields. All string content is derived
    deterministically from the upstream inputs only; this view reads no
    clock and depends on no module-level state.

    Fields:

    - ``report_date``: the cycle/date label echoed verbatim from
      :attr:`~gmc_rebuild.reporting.DailyReport.report_date`. Opaque to
      this module.
    - ``decisions_total``: total number of P6-03 decisions in the cycle,
      echoed from :attr:`~gmc_rebuild.reporting.DailyReport.decisions_total`.
    - ``would_trade``: count of ``WOULD_TRADE`` decisions, echoed.
    - ``would_skip``: count of ``WOULD_SKIP`` decisions, echoed.
    - ``decision_lines``: per-decision summary tuple in input order. Each
      line is ``"<intent_id>: WOULD_TRADE"`` for an accepted decision, or
      ``"<intent_id>: WOULD_SKIP [<reason>, <reason>, ...]"`` for a
      skipped decision (reasons in the canonical declaration order
      established by :class:`PositionDecisionReason`, preserved from
      :attr:`PositionDecision.reasons`).
    - ``order_intent_lines``: per-order-intent summary tuple in input
      order. Each line is ``"<symbol> <side> <quantity>"`` where
      ``side`` is the :attr:`SimulatedOrderIntent.side` enum value.
    - ``net_position_lines``: per-position summary tuple. Each line is
      ``"<symbol>: <signed-net-quantity>"`` in
      :attr:`SimulatedPortfolio.positions` canonical order (sorted by
      symbol ascending; non-zero quantities only — mirrored from the
      end-of-cycle snapshot).
    - ``applied_intent_ids``: canonical tuple of simulated order intent
      IDs already applied, echoed from
      :attr:`SimulatedPortfolio.applied_intent_ids` (sorted, unique).
    - ``reconciliation_status``: the cycle's
      :class:`~gmc_rebuild.risk.ReconciliationStatus` value (the enum
      member's ``value`` string), echoed from the daily report. Preserves
      the ADR-003 ``UNAVAILABLE`` vs ``FAILED`` distinction end-to-end.
    - ``tripped_invariant_lines``: caller-supplied tripped-invariant codes
      echoed in input order from
      :attr:`~gmc_rebuild.reporting.DailyReport.tripped_invariants`. Each
      line is the raw code string.

    The view carries no price, no P&L, no balances, no account identifier,
    no broker handle, no external state, no safety verdict, and no
    audit-event payload. It is a pure summary of in-memory engine state.
    """

    report_date: str
    decisions_total: int
    would_trade: int
    would_skip: int
    decision_lines: tuple[str, ...]
    order_intent_lines: tuple[str, ...]
    net_position_lines: tuple[str, ...]
    applied_intent_ids: tuple[str, ...]
    reconciliation_status: str
    tripped_invariant_lines: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.report_date, str) or not self.report_date:
            raise ValueError("DryRunOperatorView.report_date must be a non-empty str")

        for name in ("decisions_total", "would_trade", "would_skip"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"DryRunOperatorView.{name} must be an int (not bool, not float)")
            if value < 0:
                raise ValueError(f"DryRunOperatorView.{name} must be non-negative")
        if self.would_trade + self.would_skip != self.decisions_total:
            raise ValueError(
                "DryRunOperatorView invariant violated: would_trade + would_skip must "
                "equal decisions_total"
            )

        for field_name in (
            "decision_lines",
            "order_intent_lines",
            "net_position_lines",
            "applied_intent_ids",
            "tripped_invariant_lines",
        ):
            field_value = getattr(self, field_name)
            if not isinstance(field_value, tuple):
                raise TypeError(
                    f"DryRunOperatorView.{field_name} must be a tuple, "
                    f"got {type(field_value).__name__}"
                )
            for entry in field_value:
                if not isinstance(entry, str) or not entry:
                    raise ValueError(
                        f"DryRunOperatorView.{field_name} members must be non-empty str"
                    )

        if len(self.decision_lines) != self.decisions_total:
            raise ValueError("DryRunOperatorView.decision_lines length must equal decisions_total")

        if not isinstance(self.reconciliation_status, str) or not self.reconciliation_status:
            raise ValueError("DryRunOperatorView.reconciliation_status must be a non-empty str")

    def render(self) -> str:
        """Return a deterministic multi-line text rendering of the view.

        The rendering is intended for operator-facing surfaces (CLI log
        line, docstring, future read-only status surface). It is purely
        textual and does not call any side-effecting API. Identical inputs
        produce a byte-for-byte identical string every call.
        """
        lines: list[str] = [
            f"dry_run: {self.report_date}",
            (
                f"decisions: {self.decisions_total} total, "
                f"{self.would_trade} would-trade, {self.would_skip} would-skip"
            ),
            f"reconciliation: {self.reconciliation_status}",
        ]
        lines.append("order_intents:")
        if self.order_intent_lines:
            for entry in self.order_intent_lines:
                lines.append(f"  - {entry}")
        else:
            lines.append("  (none)")
        lines.append("net_positions:")
        if self.net_position_lines:
            for entry in self.net_position_lines:
                lines.append(f"  - {entry}")
        else:
            lines.append("  (none)")
        lines.append("applied_intent_ids:")
        if self.applied_intent_ids:
            for entry in self.applied_intent_ids:
                lines.append(f"  - {entry}")
        else:
            lines.append("  (none)")
        lines.append("decisions_detail:")
        if self.decision_lines:
            for entry in self.decision_lines:
                lines.append(f"  - {entry}")
        else:
            lines.append("  (none)")
        if self.tripped_invariant_lines:
            lines.append("tripped_invariants:")
            for entry in self.tripped_invariant_lines:
                lines.append(f"  - {entry}")
        return "\n".join(lines)


def _format_decision_line(decision: PositionDecision) -> str:
    if decision.outcome is PositionDecisionOutcome.WOULD_TRADE:
        return f"{decision.intent_id}: {decision.outcome.value}"
    reasons = ", ".join(reason.value for reason in decision.reasons)
    return f"{decision.intent_id}: {decision.outcome.value} [{reasons}]"


def _format_order_intent_line(order_intent: SimulatedOrderIntent) -> str:
    return f"{order_intent.symbol} {order_intent.side.value} {order_intent.quantity}"


def build_dry_run_operator_view(
    *,
    decisions: tuple[PositionDecision, ...],
    order_intents: tuple[SimulatedOrderIntent, ...],
    portfolio: SimulatedPortfolio,
    report: DailyReport,
) -> DryRunOperatorView:
    """Build a :class:`DryRunOperatorView` from one simulated dry-run cycle.

    Pure, deterministic, side-effect free. Does not mutate any input and
    does not read the clock. Counts are echoed from ``report`` (which is
    itself a pure summary of ``decisions`` + ``portfolio``); the per-line
    summaries are derived from ``decisions``, ``order_intents``, and
    ``portfolio`` in their canonical / input order.

    The :class:`~gmc_rebuild.runtime.SafetyVerdict` is intentionally not an
    input. Each :class:`PositionDecision` carries a ``verdict`` field by
    value, but this builder summarizes only the decision ``outcome`` and
    ``reasons``; it does not import ``gmc_rebuild.runtime`` and does not
    compose with the merged P4-07 ``OperatorSafetyView``.

    :raises TypeError: if ``decisions`` is not a tuple of
        :class:`~gmc_rebuild.decision.PositionDecision`, ``order_intents``
        is not a tuple of
        :class:`~gmc_rebuild.simulation.SimulatedOrderIntent`, ``portfolio``
        is not a :class:`~gmc_rebuild.portfolio_state.SimulatedPortfolio`,
        or ``report`` is not a :class:`~gmc_rebuild.reporting.DailyReport`.
    """
    if not isinstance(decisions, tuple):
        raise TypeError(f"decisions must be a tuple, got {type(decisions).__name__}")
    for decision in decisions:
        if not isinstance(decision, PositionDecision):
            raise TypeError(
                f"decisions members must be PositionDecision, got {type(decision).__name__}"
            )
    if not isinstance(order_intents, tuple):
        raise TypeError(f"order_intents must be a tuple, got {type(order_intents).__name__}")
    for order_intent in order_intents:
        if not isinstance(order_intent, SimulatedOrderIntent):
            raise TypeError(
                f"order_intents members must be SimulatedOrderIntent, "
                f"got {type(order_intent).__name__}"
            )
    if not isinstance(portfolio, SimulatedPortfolio):
        raise TypeError(f"portfolio must be a SimulatedPortfolio, got {type(portfolio).__name__}")
    if not isinstance(report, DailyReport):
        raise TypeError(f"report must be a DailyReport, got {type(report).__name__}")

    decision_lines = tuple(_format_decision_line(d) for d in decisions)
    order_intent_lines = tuple(_format_order_intent_line(o) for o in order_intents)
    net_position_lines = tuple(
        f"{position.symbol}: {position.net_quantity}" for position in portfolio.positions
    )
    reconciliation_value = report.reconciliation_status.value
    if not isinstance(report.reconciliation_status, ReconciliationStatus):
        raise TypeError(
            "report.reconciliation_status must be a ReconciliationStatus, "
            f"got {type(report.reconciliation_status).__name__}"
        )

    return DryRunOperatorView(
        report_date=report.report_date,
        decisions_total=report.decisions_total,
        would_trade=report.would_trade,
        would_skip=report.would_skip,
        decision_lines=decision_lines,
        order_intent_lines=order_intent_lines,
        net_position_lines=net_position_lines,
        applied_intent_ids=report.applied_intent_ids,
        reconciliation_status=reconciliation_value,
        tripped_invariant_lines=report.tripped_invariants,
    )


__all__ = [
    "DryRunOperatorView",
    "build_dry_run_operator_view",
]
