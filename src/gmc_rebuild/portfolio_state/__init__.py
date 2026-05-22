"""Deterministic in-memory simulated portfolio state (P6-05).

This subpackage provides the fifth Phase 6 dry-run engine capability: a
deterministic, in-memory, value-typed simulated portfolio state that
applies an **accepted** P6-03
:class:`~gmc_rebuild.decision.PositionDecision` together with a P6-04
:class:`~gmc_rebuild.simulation.SimulatedOrderIntent` to a position book
keyed by symbol, under a fixed, deterministic, fixture-only full-fill
assumption. It is downstream of the P6-01 signal-intake boundary, the
P6-02 eligibility check, the P6-03 decision composer, and the P5-02 /
P6-04 simulated order intent surface.

Authorization: ``governance/authorizations/2026-05-22_p6-05.md``.

Design constraints — these are governance constraints, not stylistic
preferences:

- **Frozen / value-typed replaceable snapshot.** :class:`SimulatedPortfolio`
  is a frozen, slotted value object; applying an intent returns a new
  snapshot and never mutates the prior one. There is no event-sourced /
  append-only event log.
- **Idempotent application keyed by simulated order intent ID.**
  Re-applying the same accepted P6-04 simulated order intent ID does not
  double-apply the position change; the snapshot carries a value-typed,
  canonical (sorted, unique) tuple of applied intent IDs.
- **Deterministic, fixture-only full-fill assumption.** The applied
  quantity is exactly the intent's positive ``quantity`` (``+`` for
  ``BUY``, ``-`` for ``SELL``); there is no fill price, no partial fill,
  and no fill engine — only deterministic signed-integer bookkeeping.
- **No runtime activation.** No ``__main__`` entry point, no daemon, no
  scheduler, no background thread, no long-running service.
- **No external I/O.** No filesystem, no network, no broker SDK, no
  persistence, no ``time.sleep``, no ``os.environ`` / ``os.getenv``
  reads, no secrets.
- **No real position book.** No real account, no account identifier, no
  balances, no P&L, no cash ledger, no valuation, no broker
  reconciliation, no account sync, no market data. The snapshot is a
  pure value object over the supplied inputs and connects to nothing.
- **No mutation of inputs.** :func:`apply_simulated_order_intent` does
  not modify the supplied snapshot, decision, or order intent.
- **No re-export from package root.** :mod:`gmc_rebuild` is unchanged by
  this packet; the public surface is reachable only via
  ``from gmc_rebuild.portfolio_state import ...``.
"""

from __future__ import annotations

from gmc_rebuild.portfolio_state._state import (
    SimulatedPortfolio,
    SimulatedPosition,
    apply_simulated_order_intent,
)

__all__ = [
    "SimulatedPortfolio",
    "SimulatedPosition",
    "apply_simulated_order_intent",
]
