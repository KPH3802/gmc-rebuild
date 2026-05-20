"""P6-03 position/risk decision composer — internal module.

Defines the closed :class:`PositionDecisionOutcome` and
:class:`PositionDecisionReason` enumerations, the frozen, slotted
:class:`PositionDecision` result, and the pure
:func:`compose_position_decision` function authorized by PR P6-03
(see ``governance/authorizations/2026-05-20_p6-03.md``).

Design constraints — these are governance constraints, not stylistic
preferences:

- **No runtime activation.** No ``__main__`` entry point, no daemon,
  no scheduler, no background thread, no long-running service.
- **No external I/O.** No filesystem, no network, no broker SDK, no
  ``time.sleep``, no ``os.environ`` / ``os.getenv`` reads.
- **No strategy logic.** The composer is a structural composition
  of already-rendered upstream decisions; it does not generate
  signals, scan markets, fetch data, score candidates, or rank
  alternatives.
- **No mutation of inputs.** :func:`compose_position_decision` does
  not modify the supplied :class:`SignalIntent`,
  :class:`EligibilityDecision`, or :class:`SafetyVerdict`.
- **No re-export from package root.** :mod:`gmc_rebuild` is
  unchanged by this packet; this subpackage exposes its public
  surface only through ``from gmc_rebuild.decision import ...``.
- **Closed enumerations.** :class:`PositionDecisionOutcome` has
  exactly two members. :class:`PositionDecisionReason` has exactly
  five members. Extending either requires a separate written
  authorization per ``AI_WORKFLOW.md`` §7.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from gmc_rebuild.eligibility import EligibilityDecision, EligibilityOutcome
from gmc_rebuild.runtime import (
    BLOCKER_HEARTBEAT_STALE,
    BLOCKER_KILL_SWITCH_TRIPPED,
    BLOCKER_RECONCILIATION_FAILED,
    BLOCKER_RECONCILIATION_UNAVAILABLE,
    BLOCKER_RECONCILIATION_WARNING,
    SafetyVerdict,
)
from gmc_rebuild.signal_intake import SignalIntent


class PositionDecisionOutcome(StrEnum):
    """Closed set of outcomes returned by the position-decision composer.

    Two members only. ``WOULD_TRADE`` means every upstream gate
    passed: the supplied :class:`EligibilityDecision` is
    :attr:`~gmc_rebuild.eligibility.EligibilityOutcome.ELIGIBLE` and
    the supplied :class:`SafetyVerdict` is ``clear``; the returned
    :class:`PositionDecision` carries an empty ``reasons`` tuple.
    ``WOULD_SKIP`` means at least one upstream gate failed; the
    ``reasons`` tuple is non-empty and lists every failing reason in
    the canonical declaration order of
    :class:`PositionDecisionReason`.
    """

    WOULD_TRADE = "WOULD_TRADE"
    WOULD_SKIP = "WOULD_SKIP"


class PositionDecisionReason(StrEnum):
    """Closed set of skip reasons returned by the composer.

    Exactly five members. The order below is the canonical
    declaration order used to sort the ``reasons`` tuple on a
    :attr:`PositionDecisionOutcome.WOULD_SKIP` decision. Extending
    this enumeration requires a separate written authorization per
    ``AI_WORKFLOW.md`` §7.

    Each member maps to a specific upstream failure mode:

    - ``ELIGIBILITY_INELIGIBLE`` — propagated when the supplied
      :class:`EligibilityDecision` outcome is
      :attr:`~gmc_rebuild.eligibility.EligibilityOutcome.INELIGIBLE`.
      The individual upstream
      :class:`~gmc_rebuild.eligibility.EligibilityReason` codes are
      preserved by value on the carried-forward
      :attr:`PositionDecision.eligibility` field; the composer does
      not re-encode them.
    - ``SAFETY_HEARTBEAT_STALE`` — propagated when the
      :class:`SafetyVerdict` carries the merged P4-08
      :data:`~gmc_rebuild.runtime.BLOCKER_HEARTBEAT_STALE`.
    - ``SAFETY_KILL_SWITCH_NOT_ARMED`` — propagated when the
      :class:`SafetyVerdict` carries the merged P4-08
      :data:`~gmc_rebuild.runtime.BLOCKER_KILL_SWITCH_TRIPPED`.
    - ``SAFETY_RECONCILIATION_NOT_CLEAN`` — propagated when the
      :class:`SafetyVerdict` carries any of the merged P4-08
      reconciliation blockers
      (:data:`~gmc_rebuild.runtime.BLOCKER_RECONCILIATION_FAILED`,
      :data:`~gmc_rebuild.runtime.BLOCKER_RECONCILIATION_UNAVAILABLE`,
      :data:`~gmc_rebuild.runtime.BLOCKER_RECONCILIATION_WARNING`).
      The distinguishing ``FAILED`` / ``UNAVAILABLE`` / ``WARNING``
      state is preserved by value on the carried-forward
      :attr:`PositionDecision.verdict` for operator-view inspection.
    - ``SAFETY_VERDICT_NOT_CLEAR`` — defense-in-depth catch-all
      propagated when :attr:`SafetyVerdict.clear` is ``False`` for
      any reason not enumerated above. Exists so that a future
      ``BLOCKER_*`` addition does not silently produce a
      :attr:`PositionDecisionOutcome.WOULD_TRADE` decision when
      safety is in fact blocked.
    """

    ELIGIBILITY_INELIGIBLE = "ELIGIBILITY_INELIGIBLE"
    SAFETY_HEARTBEAT_STALE = "SAFETY_HEARTBEAT_STALE"
    SAFETY_KILL_SWITCH_NOT_ARMED = "SAFETY_KILL_SWITCH_NOT_ARMED"
    SAFETY_RECONCILIATION_NOT_CLEAN = "SAFETY_RECONCILIATION_NOT_CLEAN"
    SAFETY_VERDICT_NOT_CLEAR = "SAFETY_VERDICT_NOT_CLEAR"


_REASON_ORDER: tuple[PositionDecisionReason, ...] = (
    PositionDecisionReason.ELIGIBILITY_INELIGIBLE,
    PositionDecisionReason.SAFETY_HEARTBEAT_STALE,
    PositionDecisionReason.SAFETY_KILL_SWITCH_NOT_ARMED,
    PositionDecisionReason.SAFETY_RECONCILIATION_NOT_CLEAN,
    PositionDecisionReason.SAFETY_VERDICT_NOT_CLEAR,
)


# Closed mapping from merged P4-08 blocker codes to the
# PositionDecisionReason member that carries them. New BLOCKER_*
# constants that are not named here fall through to the
# SAFETY_VERDICT_NOT_CLEAR catch-all, preserving the safety
# defense-in-depth invariant.
_BLOCKER_TO_REASON: dict[str, PositionDecisionReason] = {
    BLOCKER_HEARTBEAT_STALE: PositionDecisionReason.SAFETY_HEARTBEAT_STALE,
    BLOCKER_KILL_SWITCH_TRIPPED: PositionDecisionReason.SAFETY_KILL_SWITCH_NOT_ARMED,
    BLOCKER_RECONCILIATION_FAILED: PositionDecisionReason.SAFETY_RECONCILIATION_NOT_CLEAN,
    BLOCKER_RECONCILIATION_UNAVAILABLE: PositionDecisionReason.SAFETY_RECONCILIATION_NOT_CLEAN,
    BLOCKER_RECONCILIATION_WARNING: PositionDecisionReason.SAFETY_RECONCILIATION_NOT_CLEAN,
}


@dataclass(frozen=True, slots=True)
class PositionDecision:
    """Result of a position/risk decision composition.

    Five fields:

    - ``outcome``: :class:`PositionDecisionOutcome` member.
    - ``reasons``: tuple of :class:`PositionDecisionReason` members.
      Empty when ``outcome`` is
      :attr:`PositionDecisionOutcome.WOULD_TRADE`; non-empty and
      sorted in the canonical declaration order of
      :class:`PositionDecisionReason` when ``outcome`` is
      :attr:`PositionDecisionOutcome.WOULD_SKIP`.
    - ``intent_id``: the
      :attr:`~gmc_rebuild.signal_intake.SignalIntent.intent_id`
      carried forward by value for trace correlation.
    - ``eligibility``: the upstream
      :class:`~gmc_rebuild.eligibility.EligibilityDecision`
      preserved by value (and by identity) so callers can inspect
      the upstream P6-02 reason taxonomy that drove the outcome.
    - ``verdict``: the upstream
      :class:`~gmc_rebuild.runtime.SafetyVerdict` preserved by
      value (and by identity) so callers can inspect the safety
      state that drove the outcome.

    The biconditional ``outcome == WOULD_TRADE iff reasons == ()``
    is enforced at construction.
    """

    outcome: PositionDecisionOutcome
    reasons: tuple[PositionDecisionReason, ...]
    intent_id: str
    eligibility: EligibilityDecision
    verdict: SafetyVerdict

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, PositionDecisionOutcome):
            raise TypeError(
                f"outcome must be a PositionDecisionOutcome, got {type(self.outcome).__name__}"
            )
        if not isinstance(self.reasons, tuple):
            raise TypeError(f"reasons must be a tuple, got {type(self.reasons).__name__}")
        for reason in self.reasons:
            if not isinstance(reason, PositionDecisionReason):
                raise TypeError(
                    f"reasons members must be PositionDecisionReason, got {type(reason).__name__}"
                )
        if not isinstance(self.intent_id, str):
            raise TypeError(f"intent_id must be a str, got {type(self.intent_id).__name__}")
        if not self.intent_id:
            raise ValueError("intent_id must be a non-empty string")
        if not isinstance(self.eligibility, EligibilityDecision):
            raise TypeError(
                f"eligibility must be an EligibilityDecision, got {type(self.eligibility).__name__}"
            )
        if not isinstance(self.verdict, SafetyVerdict):
            raise TypeError(f"verdict must be a SafetyVerdict, got {type(self.verdict).__name__}")
        # Biconditional: WOULD_TRADE iff reasons is empty.
        if self.outcome is PositionDecisionOutcome.WOULD_TRADE and self.reasons:
            raise ValueError("PositionDecision with outcome=WOULD_TRADE must have empty reasons")
        if self.outcome is PositionDecisionOutcome.WOULD_SKIP and not self.reasons:
            raise ValueError("PositionDecision with outcome=WOULD_SKIP must have non-empty reasons")


def compose_position_decision(
    intent: SignalIntent,
    eligibility: EligibilityDecision,
    verdict: SafetyVerdict,
) -> PositionDecision:
    """Compose a :class:`PositionDecision` from the three upstream inputs.

    Pure function. Inspects the supplied
    :class:`~gmc_rebuild.eligibility.EligibilityDecision` and
    :class:`~gmc_rebuild.runtime.SafetyVerdict`, accumulates every
    applicable :class:`PositionDecisionReason`, and returns a
    :class:`PositionDecision` whose ``outcome`` is
    :attr:`PositionDecisionOutcome.WOULD_TRADE` exactly when both
    upstream gates pass and ``reasons`` is empty. Does not mutate
    any input. Has no side effects. Carries the supplied
    ``eligibility`` and ``verdict`` forward by identity into the
    returned :class:`PositionDecision`.

    :raises TypeError: if ``intent`` is not a
        :class:`~gmc_rebuild.signal_intake.SignalIntent`,
        ``eligibility`` is not an
        :class:`~gmc_rebuild.eligibility.EligibilityDecision`, or
        ``verdict`` is not a
        :class:`~gmc_rebuild.runtime.SafetyVerdict`.
    """
    if not isinstance(intent, SignalIntent):
        raise TypeError(f"intent must be a SignalIntent, got {type(intent).__name__}")
    if not isinstance(eligibility, EligibilityDecision):
        raise TypeError(
            f"eligibility must be an EligibilityDecision, got {type(eligibility).__name__}"
        )
    if not isinstance(verdict, SafetyVerdict):
        raise TypeError(f"verdict must be a SafetyVerdict, got {type(verdict).__name__}")

    failing: set[PositionDecisionReason] = set()
    if eligibility.outcome is EligibilityOutcome.INELIGIBLE:
        failing.add(PositionDecisionReason.ELIGIBILITY_INELIGIBLE)
    if not verdict.clear:
        named_safety_reason = False
        for blocker in verdict.blockers:
            mapped = _BLOCKER_TO_REASON.get(blocker)
            if mapped is not None:
                failing.add(mapped)
                named_safety_reason = True
        if not named_safety_reason:
            failing.add(PositionDecisionReason.SAFETY_VERDICT_NOT_CLEAR)

    if not failing:
        return PositionDecision(
            outcome=PositionDecisionOutcome.WOULD_TRADE,
            reasons=(),
            intent_id=intent.intent_id,
            eligibility=eligibility,
            verdict=verdict,
        )
    ordered = tuple(reason for reason in _REASON_ORDER if reason in failing)
    return PositionDecision(
        outcome=PositionDecisionOutcome.WOULD_SKIP,
        reasons=ordered,
        intent_id=intent.intent_id,
        eligibility=eligibility,
        verdict=verdict,
    )


__all__ = [
    "PositionDecision",
    "PositionDecisionOutcome",
    "PositionDecisionReason",
    "compose_position_decision",
]
