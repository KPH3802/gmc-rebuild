"""P6-06 deterministic daily dry-run report — internal module.

Defines the frozen, slotted :class:`DailyReport` value object, the pure
:func:`build_daily_report` builder, and the pure
:func:`render_daily_report_event` renderer authorized by PR P6-06 (see
``governance/authorizations/2026-05-23_p6-06.md``).

This module summarizes a single simulated dry-run cycle — the decisions
made (P6-03), the end-of-cycle simulated position book (P6-05), the
reconciliation status (P2-05 / P3-05), and any caller-supplied tripped
invariants — into a value object, and renders that value object to a
structured :class:`~gmc_rebuild.logging.AuditEvent` via the merged P2-04
``audit_event`` helper. It is the sixth Phase 6 dry-run capability,
downstream of P6-01..P6-05.

Design constraints — these are governance constraints, not stylistic
preferences (``governance/authorizations/2026-05-23_p6-06.md``):

- **Pure consumer of the merged P2-04 contract.** The report is emitted
  only via ``audit_event`` to the standard logger, reusing the **closed**
  ``lifecycle`` audit category (event name ``lifecycle.daily_report``).
  This module does **not** modify ``AUDIT_CATEGORIES`` or any other part
  of the P2-04 surface, install logging handlers, call
  ``logging.basicConfig``, or write to any external sink.
- **Caller-supplied timestamp only — no clock read.**
  :func:`render_daily_report_event` requires an explicit, timezone-aware
  ``datetime`` and forbids the implicit ``now_utc()`` fallback that
  ``audit_event`` would otherwise apply for a ``None`` timestamp. This
  module never calls ``now_utc()`` / ``time.*`` / ``datetime.now()``.
- **Deterministic and side-effect free.** Identical inputs (and, for the
  rendered event, the same explicit timestamp) yield byte-for-byte
  identical output every call. No global / module-level / class-level
  mutable state, no cache, no counter, no randomness.
- **No mutation of inputs.** The supplied decisions tuple, portfolio
  snapshot, reconciliation status, and tripped-invariant codes are not
  modified. All produced values are frozen / value-typed.
- **No runtime activation / external I/O.** No ``__main__``, no daemon,
  no scheduler, no network, no filesystem write, no persistence, no
  broker, no account, no market data, no secrets, no env-var read.
- **No re-export from package root.** :mod:`gmc_rebuild` is unchanged by
  this packet; the public surface is reachable only via
  ``from gmc_rebuild.reporting import ...``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from gmc_rebuild.decision import PositionDecision, PositionDecisionOutcome
from gmc_rebuild.logging import AuditEvent, audit_event
from gmc_rebuild.portfolio_state import SimulatedPortfolio
from gmc_rebuild.risk import ReconciliationStatus

_AUDIT_CATEGORY = "lifecycle"
_AUDIT_NAME = "lifecycle.daily_report"


@dataclass(frozen=True, slots=True)
class DailyReport:
    """Immutable deterministic summary of one simulated dry-run cycle.

    Eight closed, value-typed fields:

    - ``report_date``: caller-supplied non-empty cycle/date label (an
      opaque string, e.g. an ISO date). It is a label only; the
      :class:`~gmc_rebuild.logging.AuditEvent` timestamp is supplied
      separately at render time.
    - ``decisions_total``: total number of P6-03 decisions in the cycle.
    - ``would_trade``: count of ``WOULD_TRADE`` decisions.
    - ``would_skip``: count of ``WOULD_SKIP`` decisions. The invariant
      ``would_trade + would_skip == decisions_total`` is enforced.
    - ``applied_intent_ids``: canonical (sorted, unique) tuple of the
      simulated order intent IDs applied in the end-of-cycle portfolio.
    - ``net_positions``: canonical tuple of ``(symbol, net_quantity)``
      pairs from the end-of-cycle portfolio, sorted by symbol ascending,
      unique symbols, no zero quantities — mirroring the
      :class:`~gmc_rebuild.portfolio_state.SimulatedPortfolio` canonical
      form.
    - ``reconciliation_status``: the cycle's
      :class:`~gmc_rebuild.risk.ReconciliationStatus`, preserving the
      ``UNAVAILABLE`` vs ``FAILED`` distinction end-to-end (ADR-003).
    - ``tripped_invariants``: caller-supplied tuple of non-empty
      invariant-code strings (order preserved as supplied).

    The report carries no price, no P&L, no balances, no account, no
    broker handle, and no external state.
    """

    report_date: str
    decisions_total: int
    would_trade: int
    would_skip: int
    applied_intent_ids: tuple[str, ...]
    net_positions: tuple[tuple[str, int], ...]
    reconciliation_status: ReconciliationStatus
    tripped_invariants: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.report_date, str) or not self.report_date:
            raise ValueError("DailyReport.report_date must be a non-empty str")

        for name in ("decisions_total", "would_trade", "would_skip"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"DailyReport.{name} must be an int (not bool, not float)")
            if value < 0:
                raise ValueError(f"DailyReport.{name} must be non-negative")
        if self.would_trade + self.would_skip != self.decisions_total:
            raise ValueError(
                "DailyReport invariant violated: would_trade + would_skip must equal "
                "decisions_total"
            )

        if not isinstance(self.applied_intent_ids, tuple):
            raise TypeError(
                f"DailyReport.applied_intent_ids must be a tuple, "
                f"got {type(self.applied_intent_ids).__name__}"
            )
        seen_ids: set[str] = set()
        for intent_id in self.applied_intent_ids:
            if not isinstance(intent_id, str) or not intent_id:
                raise ValueError("DailyReport.applied_intent_ids members must be non-empty str")
            if intent_id in seen_ids:
                raise ValueError(
                    f"DailyReport.applied_intent_ids must be unique; {intent_id!r} repeats"
                )
            seen_ids.add(intent_id)
        if list(self.applied_intent_ids) != sorted(self.applied_intent_ids):
            raise ValueError("DailyReport.applied_intent_ids must be sorted ascending")

        if not isinstance(self.net_positions, tuple):
            raise TypeError(
                f"DailyReport.net_positions must be a tuple, "
                f"got {type(self.net_positions).__name__}"
            )
        seen_symbols: set[str] = set()
        for pair in self.net_positions:
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise TypeError("DailyReport.net_positions members must be (symbol, qty) pairs")
            symbol, quantity = pair
            if not isinstance(symbol, str) or not symbol:
                raise ValueError("DailyReport.net_positions symbol must be a non-empty str")
            if any(ch.isspace() for ch in symbol):
                raise ValueError("DailyReport.net_positions symbol must not contain whitespace")
            if isinstance(quantity, bool) or not isinstance(quantity, int):
                raise TypeError("DailyReport.net_positions quantity must be an int")
            if quantity == 0:
                raise ValueError("DailyReport.net_positions quantity must be non-zero")
            if symbol in seen_symbols:
                raise ValueError(
                    f"DailyReport.net_positions must have unique symbols; {symbol!r} repeats"
                )
            seen_symbols.add(symbol)
        if list(self.net_positions) != sorted(self.net_positions, key=lambda p: p[0]):
            raise ValueError("DailyReport.net_positions must be sorted by symbol ascending")

        if not isinstance(self.reconciliation_status, ReconciliationStatus):
            raise TypeError(
                f"DailyReport.reconciliation_status must be a ReconciliationStatus, "
                f"got {type(self.reconciliation_status).__name__}"
            )

        if not isinstance(self.tripped_invariants, tuple):
            raise TypeError(
                f"DailyReport.tripped_invariants must be a tuple, "
                f"got {type(self.tripped_invariants).__name__}"
            )
        for code in self.tripped_invariants:
            if not isinstance(code, str) or not code:
                raise ValueError("DailyReport.tripped_invariants members must be non-empty str")


def build_daily_report(
    *,
    report_date: str,
    decisions: tuple[PositionDecision, ...],
    portfolio: SimulatedPortfolio,
    reconciliation_status: ReconciliationStatus,
    tripped_invariants: tuple[str, ...] = (),
) -> DailyReport:
    """Build a :class:`DailyReport` from one simulated dry-run cycle.

    Pure, deterministic, side-effect free. Does not mutate any input and
    does not read the clock. Counts the P6-03 ``decisions`` by outcome,
    snapshots the end-of-cycle ``portfolio`` position book and applied
    intent IDs, and carries the ``reconciliation_status`` and any
    caller-supplied ``tripped_invariants`` forward by value.

    :raises TypeError: if ``decisions`` is not a tuple of
        :class:`~gmc_rebuild.decision.PositionDecision`, ``portfolio`` is
        not a :class:`~gmc_rebuild.portfolio_state.SimulatedPortfolio`,
        ``reconciliation_status`` is not a
        :class:`~gmc_rebuild.risk.ReconciliationStatus`, or
        ``tripped_invariants`` is not a tuple.
    """
    if not isinstance(decisions, tuple):
        raise TypeError(f"decisions must be a tuple, got {type(decisions).__name__}")
    for decision in decisions:
        if not isinstance(decision, PositionDecision):
            raise TypeError(
                f"decisions members must be PositionDecision, got {type(decision).__name__}"
            )
    if not isinstance(portfolio, SimulatedPortfolio):
        raise TypeError(f"portfolio must be a SimulatedPortfolio, got {type(portfolio).__name__}")
    if not isinstance(reconciliation_status, ReconciliationStatus):
        raise TypeError(
            f"reconciliation_status must be a ReconciliationStatus, "
            f"got {type(reconciliation_status).__name__}"
        )
    if not isinstance(tripped_invariants, tuple):
        raise TypeError(
            f"tripped_invariants must be a tuple, got {type(tripped_invariants).__name__}"
        )

    would_trade = sum(1 for d in decisions if d.outcome is PositionDecisionOutcome.WOULD_TRADE)
    would_skip = sum(1 for d in decisions if d.outcome is PositionDecisionOutcome.WOULD_SKIP)
    net_positions = tuple((p.symbol, p.net_quantity) for p in portfolio.positions)

    return DailyReport(
        report_date=report_date,
        decisions_total=len(decisions),
        would_trade=would_trade,
        would_skip=would_skip,
        applied_intent_ids=portfolio.applied_intent_ids,
        net_positions=net_positions,
        reconciliation_status=reconciliation_status,
        tripped_invariants=tripped_invariants,
    )


def render_daily_report_event(report: DailyReport, *, timestamp: datetime) -> AuditEvent:
    """Render a :class:`DailyReport` to a deterministic ``AuditEvent``.

    Pure, deterministic, side-effect free. Emits the report through the
    merged P2-04 :func:`~gmc_rebuild.logging.audit_event` helper under the
    closed ``lifecycle`` category and the ``lifecycle.daily_report`` event
    name. The ``timestamp`` is **caller-supplied** and required: a
    ``None`` timestamp is rejected so the deterministic contract is never
    silently replaced by ``audit_event``'s ``now_utc()`` clock fallback.

    :raises TypeError: if ``report`` is not a :class:`DailyReport` or
        ``timestamp`` is not a :class:`datetime.datetime`.
    :raises ValueError: if ``timestamp`` is ``None``.
    """
    if not isinstance(report, DailyReport):
        raise TypeError(f"report must be a DailyReport, got {type(report).__name__}")
    if timestamp is None:
        raise ValueError(
            "render_daily_report_event requires an explicit caller-supplied timestamp; "
            "the implicit clock fallback is forbidden for determinism"
        )
    if not isinstance(timestamp, datetime):
        raise TypeError(f"timestamp must be a datetime, got {type(timestamp).__name__}")

    message = (
        f"Daily dry-run report for {report.report_date}: "
        f"{report.would_trade} would-trade, {report.would_skip} would-skip, "
        f"{len(report.net_positions)} open position(s), "
        f"reconciliation {report.reconciliation_status.value}"
    )
    fields = {
        "report_date": report.report_date,
        "decisions_total": report.decisions_total,
        "would_trade": report.would_trade,
        "would_skip": report.would_skip,
        "applied_intent_ids": list(report.applied_intent_ids),
        "net_positions": {symbol: quantity for symbol, quantity in report.net_positions},
        "reconciliation_status": report.reconciliation_status.value,
        "tripped_invariants": list(report.tripped_invariants),
    }
    return audit_event(_AUDIT_CATEGORY, _AUDIT_NAME, message, fields=fields, timestamp=timestamp)


__all__ = [
    "DailyReport",
    "build_daily_report",
    "render_daily_report_event",
]
