"""Deterministic daily dry-run report (P6-06).

This subpackage provides the sixth Phase 6 dry-run engine capability: a
deterministic, in-memory daily-report record that summarizes a single
simulated dry-run cycle and is emitted **only** via the merged P2-04
:func:`gmc_rebuild.logging.audit_event` helper to the standard logger. It
consumes already-rendered upstream values by value — the P6-03
:class:`~gmc_rebuild.decision.PositionDecision` results, the P6-05
:class:`~gmc_rebuild.portfolio_state.SimulatedPortfolio` snapshot, the
P2-05 / P3-05 :class:`~gmc_rebuild.risk.ReconciliationStatus`, and
caller-supplied tripped-invariant codes — and produces a frozen
:class:`DailyReport` value object plus a deterministic
:class:`~gmc_rebuild.logging.AuditEvent`.

Authorization: ``governance/authorizations/2026-05-23_p6-06.md``.

Design constraints — these are governance constraints, not stylistic
preferences:

- **Pure consumer of the merged P2-04 contract.** Emitted only via
  ``audit_event`` under the **closed** ``lifecycle`` audit category
  (event name ``lifecycle.daily_report``). This packet does not modify
  ``AUDIT_CATEGORIES`` or any other part of the P2-04 surface, install a
  logging handler, call ``logging.basicConfig``, or write to any external
  sink.
- **Caller-supplied timestamp only — no clock read.**
  :func:`render_daily_report_event` requires an explicit timezone-aware
  ``datetime`` and forbids the implicit ``now_utc()`` fallback; this
  packet never reads the wall clock.
- **Deterministic and side-effect free.** Identical inputs (and the same
  explicit timestamp) yield byte-for-byte identical output every call. No
  global / module-level mutable state, no cache, no randomness.
- **No mutation of inputs.** The supplied decisions, portfolio snapshot,
  reconciliation status, and invariant codes are not modified.
- **No runtime activation / external I/O.** No ``__main__``, no daemon,
  no scheduler, no network, no filesystem write, no persistence, no
  broker, no account, no market data, no secrets, no env-var read.
- **No re-export from package root.** :mod:`gmc_rebuild` is unchanged by
  this packet; the public surface is reachable only via
  ``from gmc_rebuild.reporting import ...``.
"""

from __future__ import annotations

from gmc_rebuild.reporting._report import (
    DailyReport,
    build_daily_report,
    render_daily_report_event,
)

__all__ = [
    "DailyReport",
    "build_daily_report",
    "render_daily_report_event",
]
