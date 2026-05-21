"""Inert local simulation boundary skeleton (P5-01) and simulated order intent model (P5-02).

This subpackage provides the smallest possible local simulation
boundary that the project can use to *represent* a simulated trading
progression without touching real trading systems. The boundary is
**inert**: it never submits, never routes, never executes, never
persists, never schedules, and never connects to any broker (real or
paper), market-data feed, or external service. Its responsibilities
are to declare typed shapes for a simulation lane, a placeholder
:class:`SimulatedIntent`, a richer :class:`SimulatedOrderIntent`
(P5-02), the two closed enumerations of authorized simulated-order
side and order type (P5-02), and to gate any proposed simulated
progression on an existing already-clear
:class:`gmc_rebuild.runtime.SafetyVerdict`.

Authorizations:

- ``governance/authorizations/2026-05-17_p5-01.md`` — the original
  inert local simulation boundary skeleton (``SimulationLane``,
  ``SimulatedIntent``, ``SimulationBoundary.propose``).
- ``governance/authorizations/2026-05-17_p5-02.md`` — the simulated
  order intent model added on top of the P5-01 skeleton
  (``SimulatedOrderSide``, ``SimulatedOrderType``,
  ``SimulatedOrderIntent``, ``SimulationBoundary.propose_order``).
- ``governance/authorizations/2026-05-21_p6-04.md`` — the P6-04
  Direction A simulated order intent extension added in place
  (``SimulatedOrderTimeInForce`` closed enum carried as a ninth
  ``SimulatedOrderIntent`` field defaulting to ``DAY``, and the
  deterministic ``derive_simulated_order_intent_id`` identity helper).

Design constraints — these are governance constraints, not stylistic
preferences:

- **Inert by construction.** No ``__main__`` entry point, no daemon,
  no scheduler, no background thread, no long-running service, no
  broker integration (real or paper), no market-data ingestion, no
  order placement, no order routing, no execution adapter, no
  strategy / scanner / model / portfolio / backtest content, no
  env-var loading, no secrets, no network, no persistence, no
  ``time.sleep``, no ``asyncio.sleep``.
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
  invariant end-to-end through the simulation gate. This invariant
  applies to **both** :meth:`SimulationBoundary.propose` (for
  :class:`SimulatedIntent`) and
  :meth:`SimulationBoundary.propose_order` (for
  :class:`SimulatedOrderIntent`).
- **Closed lane enumeration.** Only :attr:`SimulationLane.LOCAL_ONLY`
  is authorized by P5-01 and P5-02. No paper-broker lane, no
  backtest lane, no live lane is declared here; each future lane
  requires its own separate written authorization from Kevin.
- **Closed order-side enumeration (P5-02).** Only
  :attr:`SimulatedOrderSide.BUY` and :attr:`SimulatedOrderSide.SELL`
  are authorized. ``SELL_SHORT`` / ``BUY_TO_COVER`` / etc. are
  explicitly **not** declared; each requires its own separate
  written authorization from Kevin.
- **Closed order-type enumeration (P5-02).** Only
  :attr:`SimulatedOrderType.MARKET` and
  :attr:`SimulatedOrderType.LIMIT` are authorized. ``STOP``,
  ``STOP_LIMIT``, ``MARKET_ON_CLOSE``, ``LIMIT_ON_OPEN``,
  ``TRAILING_STOP``, etc. are explicitly **not** declared; each
  requires its own separate written authorization from Kevin.
- **Closed time-in-force enumeration (P6-04 Direction A).** Only
  :attr:`SimulatedOrderTimeInForce.DAY`,
  :attr:`SimulatedOrderTimeInForce.GOOD_TILL_CANCEL`,
  :attr:`SimulatedOrderTimeInForce.IMMEDIATE_OR_CANCEL`, and
  :attr:`SimulatedOrderTimeInForce.FILL_OR_KILL` are authorized.
  ``GOOD_TILL_DATE``, ``AT_THE_OPEN``, ``AT_THE_CLOSE``, etc. are
  explicitly **not** declared; each requires its own separate written
  authorization from Kevin. The time-in-force tag is a pure
  order-duration label, not an execution instruction.
- **Deterministic order-intent identity (P6-04 Direction A).**
  :func:`derive_simulated_order_intent_id` derives a deterministic
  content-fingerprint identifier from a closed subset of the
  order-intent content with no randomness, no clock read, no counter,
  and no hidden state; its output is a valid ``intent_id`` value.
- **Placeholder intent and order intent only.**
  :class:`SimulatedIntent` (P5-01) carries a lane, an opaque
  identifier, and an ADR-004 ``Z``-suffixed UTC creation timestamp.
  :class:`SimulatedOrderIntent` (P5-02, extended in place by P6-04)
  adds symbol (opaque string, no symbol-universe lookup), side,
  quantity (positive ``int``; ``bool`` rejected; fractional /
  ``float`` quantities not authorized), order type, an optional limit
  price (``None`` for ``MARKET``; positive finite ``float`` for
  ``LIMIT``), and a P6-04 ``time_in_force`` order-duration tag
  (defaulting to ``DAY``). **Neither** record carries a venue,
  broker, account, routing instruction, post-only / IOC / FOK
  execution modifier, route-allow / route-deny list, broker
  credential, API key, or persistence handle. Adding any further
  field requires its own separate written authorization from Kevin
  per the §16.5 Risk Register entry on order-intent semantics in
  ``RECOVERY.md``.
- **ADR-004 UTC discipline.** Timestamps surfaced on
  :class:`SimulatedIntent` and :class:`SimulatedOrderIntent` are
  ADR-004 ``Z``-suffixed UTC strings sourced via
  :func:`gmc_rebuild.risk.to_utc_string`.
"""

from __future__ import annotations

from gmc_rebuild.simulation._boundary import (
    SimulatedIntent,
    SimulatedOrderIntent,
    SimulatedOrderSide,
    SimulatedOrderTimeInForce,
    SimulatedOrderType,
    SimulationBoundary,
    SimulationBoundaryError,
    SimulationLane,
    derive_simulated_order_intent_id,
)

__all__ = [
    "SimulatedIntent",
    "SimulatedOrderIntent",
    "SimulatedOrderSide",
    "SimulatedOrderTimeInForce",
    "SimulatedOrderType",
    "SimulationBoundary",
    "SimulationBoundaryError",
    "SimulationLane",
    "derive_simulated_order_intent_id",
]
