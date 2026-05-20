"""Position/risk decision composer (P6-03).

This subpackage provides the third Phase 6 dry-run engine capability:
a pure-function position/risk decision composer that consumes the
merged P6-01 :class:`~gmc_rebuild.signal_intake.SignalIntent`
boundary, the merged P6-02
:class:`~gmc_rebuild.eligibility.EligibilityDecision` result, and the
merged P4-06 :class:`~gmc_rebuild.runtime.SafetyVerdict` safety
surface, and returns a deterministic
:class:`PositionDecision` describing whether the system would trade
or would skip. It is downstream of the P6-01 signal-intake boundary
and the P6-02 eligibility check, and downstream of the P4-06 /
P4-07 / P4-08 safety verdict surface; it is upstream of any later
order-intent capability.

Authorization: ``governance/authorizations/2026-05-20_p6-03.md``.

Design constraints — these are governance constraints, not stylistic
preferences:

- **No runtime activation.** The package has no ``__main__`` entry
  point, no daemon, no scheduler, no background thread, no
  long-running service.
- **No external I/O.** No filesystem, no network, no broker SDK, no
  ``time.sleep``, no ``os.environ`` / ``os.getenv`` reads.
- **No external config loading.** This subpackage does not import
  :mod:`gmc_rebuild.config` or any other configuration source; every
  input is supplied by the caller.
- **No real-runtime consumer.** This subpackage is not re-exported
  by :mod:`gmc_rebuild` as part of any runtime API. Its public
  surface is reachable only via ``from gmc_rebuild.decision import
  ...``.
- **No strategy / scanner / model / portfolio / backtest logic.**
  The composer is a structural composition of already-rendered
  upstream decisions; it does not generate signals, scan markets,
  fetch data, score candidates, rank alternatives, decide position
  size, or pick a venue / order type / time-in-force.
- **No order placement / broker integration / market data.** A
  position decision returned here is informational; downstream
  packets decide what to do with it. This packet emits no order,
  contacts no broker, and reads no market data.
- **No mutation of inputs.** :func:`compose_position_decision` does
  not modify the supplied :class:`SignalIntent`,
  :class:`EligibilityDecision`, or :class:`SafetyVerdict`. All
  upstream dataclasses are already frozen / slotted; the composer
  preserves them by value (and by identity for the carried-forward
  ``verdict`` and ``eligibility`` fields).
- **Closed enumerations.** :class:`PositionDecisionOutcome` has
  exactly two members (``WOULD_TRADE``, ``WOULD_SKIP``).
  :class:`PositionDecisionReason` has exactly five members
  enumerating the disjoint failure modes propagated from the
  upstream P6-02 eligibility and P4-06 safety layers
  (``ELIGIBILITY_INELIGIBLE``, ``SAFETY_HEARTBEAT_STALE``,
  ``SAFETY_KILL_SWITCH_NOT_ARMED``,
  ``SAFETY_RECONCILIATION_NOT_CLEAN``,
  ``SAFETY_VERDICT_NOT_CLEAR``). Any expansion of either requires a
  separate written authorization per ``AI_WORKFLOW.md`` §7.
- **Closed dataclass shape.** :class:`PositionDecision` has exactly
  five fields. The biconditional ``outcome == WOULD_TRADE iff
  reasons == ()`` is enforced at construction, mirroring the merged
  P6-02 :class:`EligibilityDecision` precedent.
"""

from __future__ import annotations

from gmc_rebuild.decision._compose import (
    PositionDecision,
    PositionDecisionOutcome,
    PositionDecisionReason,
    compose_position_decision,
)

__all__ = [
    "PositionDecision",
    "PositionDecisionOutcome",
    "PositionDecisionReason",
    "compose_position_decision",
]
