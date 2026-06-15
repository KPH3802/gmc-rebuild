"""Deterministic read-only operator view of dry-run engine state (P6-07).

This subpackage provides the seventh Phase 6 dry-run engine capability: a
deterministic, in-memory, **read-only** projection of the current dry-run
engine state — the cycle's P6-03
:class:`~gmc_rebuild.decision.PositionDecision` results, the cycle's P6-04
:class:`~gmc_rebuild.simulation.SimulatedOrderIntent` values, the end-of-cycle
P6-05 :class:`~gmc_rebuild.portfolio_state.SimulatedPortfolio` snapshot, and
the P6-06 :class:`~gmc_rebuild.reporting.DailyReport` summary — into an
operator-facing :class:`DryRunOperatorView` value object plus a deterministic
string render. The view summarizes the in-memory state of one dry-run cycle;
it places no orders, beats no heartbeat, stages no reconciliation, and
performs no I/O.

Authorization: ``governance/authorizations/2026-06-15_p6-07.md`` (and the
merged planning packet ``governance/authorizations/2026-06-15_p6-07-planning.md``).

Design constraints — these are governance constraints, not stylistic
preferences:

- **Pure read-only consumer.** The view consumes already-rendered upstream
  values by value and modifies none of them. It does **not** re-execute the
  decision composer, the simulation boundary, the portfolio applier, or the
  report builder. The :class:`~gmc_rebuild.runtime.SafetyVerdict` is
  intentionally **not** an input, and this packet does **not** import
  :mod:`gmc_rebuild.runtime` or compose with the merged P4-07
  ``OperatorSafetyView`` — that decision is reserved for the future P6-07
  successor authorization per the merged planning packet §3.4.
- **Pure / deterministic / no clock read.** Identical inputs return the
  byte-for-byte identical :class:`DryRunOperatorView` and the byte-for-byte
  identical :meth:`DryRunOperatorView.render` string on every call. Any date
  shown is **echoed** from the caller-supplied
  :attr:`~gmc_rebuild.reporting.DailyReport.report_date` string; this module
  never calls ``now_utc()`` / ``time.*`` / ``datetime.now()``.
- **No side effects.** No I/O, no network, no filesystem write, no
  persistence, no broker, no account, no market data, no orders, no secrets,
  no env-var read. The view does **not** emit any ``audit_event`` and does
  **not** import :mod:`gmc_rebuild.logging`.
- **No runtime activation.** No ``__main__`` entry point, no daemon, no
  scheduler, no background thread, no long-running service, no
  ``time.sleep``, no ``asyncio.sleep``, no handler installation, no
  ``logging.basicConfig``.
- **No mutation of inputs.** The supplied decisions, order intents,
  portfolio snapshot, and daily report are not modified.
- **No re-export from package root.** :mod:`gmc_rebuild` is unchanged by
  this packet; the public surface is reachable only via
  ``from gmc_rebuild.operator_view import ...``.
"""

from __future__ import annotations

from gmc_rebuild.operator_view._view import (
    DryRunOperatorView,
    build_dry_run_operator_view,
)

__all__ = [
    "DryRunOperatorView",
    "build_dry_run_operator_view",
]
