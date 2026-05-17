"""Inert local simulation boundary skeleton (P5-01).

This subpackage provides the smallest possible local simulation
boundary that the project can use to *represent* a simulated trading
progression without touching real trading systems. The boundary is
**inert**: it never submits, never routes, never executes, never
persists, never schedules, and never connects to any broker (real or
paper), market-data feed, or external service. Its sole responsibility
is to declare typed shapes for a simulation lane and a placeholder
simulated intent, and to gate any proposed simulated progression on
an existing already-clear :class:`gmc_rebuild.runtime.SafetyVerdict`.

Authorization: ``governance/authorizations/2026-05-17_p5-01.md``.

Design constraints — these are governance constraints, not stylistic
preferences:

- **Inert by construction.** No ``__main__`` entry point, no daemon,
  no scheduler, no background thread, no long-running service, no
  broker integration (real or paper), no market-data ingestion, no
  order placement, no strategy / scanner / model / portfolio /
  backtest content, no env-var loading, no secrets, no network, no
  persistence, no ``time.sleep``, no ``asyncio.sleep``.
- **Composed, not concrete.** The boundary composes the merged
  P4-06 :class:`gmc_rebuild.runtime.SafetyVerdict` boundary; it does
  not introduce a new concrete implementation of
  :class:`gmc_rebuild.risk.HeartbeatProtocol`,
  :class:`gmc_rebuild.risk.KillSwitchProtocol`, or
  :class:`gmc_rebuild.risk.ReconciliationProtocol`, and it does not
  reach inside the P4-06 / P4-07 / P4-08 safety surfaces.
- **Safety-gated.** A simulated progression is permitted only when
  :attr:`gmc_rebuild.runtime.SafetyVerdict.clear` is ``True``. Any
  other observed state causes :class:`SimulationBoundaryError` to be
  raised with the verdict's blocker tuple — preserving the
  ADR-002 / ADR-003 / ADR-005 "safe default is no trading"
  invariant end-to-end through the simulation gate.
- **Closed lane enumeration.** Only :attr:`SimulationLane.LOCAL_ONLY`
  is authorized by this packet. No paper-broker lane, no backtest
  lane, no live lane is declared here; each future lane requires
  its own separate written authorization from Kevin.
- **Placeholder intent only.** :class:`SimulatedIntent` carries a
  lane, an opaque identifier, and an ADR-004 ``Z``-suffixed UTC
  creation timestamp. It carries no symbol, no side, no quantity,
  no price, no venue, no broker account, no routing instruction, and
  no persistence handle. Future authorized packets may extend the
  schema; this packet only defines the placeholder shape.
- **ADR-004 UTC discipline.** Timestamps surfaced on
  :class:`SimulatedIntent` are ADR-004 ``Z``-suffixed UTC strings
  sourced via :func:`gmc_rebuild.risk.to_utc_string`.
"""

from __future__ import annotations

from gmc_rebuild.simulation._boundary import (
    SimulatedIntent,
    SimulationBoundary,
    SimulationBoundaryError,
    SimulationLane,
)

__all__ = [
    "SimulatedIntent",
    "SimulationBoundary",
    "SimulationBoundaryError",
    "SimulationLane",
]
