"""Deterministic in-memory read-only dry-run position reconciliation (P6-09).

This subpackage provides the ninth Phase 6 dry-run engine capability: a
pure, deterministic, **read-only** comparison of the merged P6-05
:class:`~gmc_rebuild.portfolio_state.SimulatedPortfolio` snapshot against
a caller-supplied, value-typed :class:`ExpectedPositions` input, producing
a frozen, typed :class:`DryRunReconciliationResult`. It is downstream of
the P6-05 simulated portfolio state and references the merged P2-05
:class:`~gmc_rebuild.risk.ReconciliationStatus` enum only to echo the
caller's status verbatim.

Authorization: ``governance/authorizations/2026-06-19_p6-09.md``.

Design constraints — these are governance constraints, not stylistic
preferences:

- **Pure / deterministic / read-only.** The comparison mutates none of
  its inputs, holds no hidden state, reads no clock, and returns the
  byte-for-byte identical result for identical inputs.
- **Closed, value-typed surface.** Exactly five public symbols, exposed
  only via ``from gmc_rebuild.dry_run_reconciliation import ...`` (this
  subpackage is **not** re-exported from
  :mod:`gmc_rebuild`). No ``render()`` method, no human-readable string
  surface.
- **Reconciliation status echoed verbatim.** The caller-supplied
  :class:`~gmc_rebuild.risk.ReconciliationStatus` is carried onto the
  result unchanged, preserving the ADR-003 ``UNAVAILABLE`` vs ``FAILED``
  distinction end-to-end.
- **Distinct from the P3-05 fixture.** The ``dry_run_`` prefix keeps the
  import statement visibly distinct from the merged P3-05
  ``gmc_rebuild.reconciliation`` ``InMemoryReconciliation`` fake, which
  this subpackage neither imports, re-exports, nor runtime-activates. No
  abstract :class:`gmc_rebuild.risk.ReconciliationProtocol` is
  implemented.
- **No runtime, no broker, no real account.** No ``__main__``, no daemon,
  no scheduler, no network, no persistence, no filesystem snapshot, no
  env-var read, no secrets, no ``audit_event`` emission, no broker, no
  real account, no balances, no P&L, no market data, no order routing.
"""

from __future__ import annotations

from gmc_rebuild.dry_run_reconciliation._reconcile import (
    DryRunReconciliationOutcome,
    DryRunReconciliationResult,
    ExpectedPositions,
    ReconciliationQuantityMismatch,
    reconcile_dry_run_positions,
)

__all__ = [
    "DryRunReconciliationOutcome",
    "DryRunReconciliationResult",
    "ExpectedPositions",
    "ReconciliationQuantityMismatch",
    "reconcile_dry_run_positions",
]
