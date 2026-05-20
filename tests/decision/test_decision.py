"""P6-03 position/risk decision composer tests.

Deterministic, pytest-only tests for the merged P6-03 position/risk
decision composer at :mod:`gmc_rebuild.decision`. The tests cover:

- The would-trade happy path (eligible eligibility plus clear safety
  verdict; ``outcome`` is :attr:`PositionDecisionOutcome.WOULD_TRADE`;
  ``reasons`` is empty; ``intent_id`` / ``eligibility`` / ``verdict``
  carried forward).
- The would-skip path on ineligibility alone.
- The would-skip path on each of the merged P4-08 ``BLOCKER_*``
  constants in turn, propagated through the composer's closed
  :class:`PositionDecisionReason` taxonomy.
- The would-skip path on composed failure (ineligibility plus a
  non-clear safety verdict), with reasons emitted in canonical
  declaration order.
- The ``WOULD_TRADE iff reasons == ()`` biconditional on
  :class:`PositionDecision` construction.
- Closed-set invariants on :class:`PositionDecisionOutcome` and
  :class:`PositionDecisionReason`.
- Frozen / slotted / closed-shape invariants on
  :class:`PositionDecision`.
- Deterministic repeat calls.
- Non-mutation of inputs.
- Identity preservation of carried-forward upstream context
  (``eligibility``, ``verdict``).
- Type-validation rejections on invalid input types.
- Equality and hashability of :class:`PositionDecision`.
- Composed integration with the merged P3-03 / P3-04 / P3-05
  in-memory fakes via the P4-06 :class:`RuntimeShell` end-to-end.
- :mod:`ast` import-graph inertness self-check confirming that the
  subpackage's source imports are drawn only from the authorized
  prefix set and are disjoint from the forbidden runtime roots.
- Substring-scan inertness self-check for ``__main__`` blocks,
  ``time.sleep(``, ``socket.``, ``urllib``, ``requests.``, and the
  ``open(`` builtin.
- Root-package non-re-export of the new P6-03 surface.

Authorization: ``governance/authorizations/2026-05-20_p6-03.md``.
"""

from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType

from gmc_rebuild.decision import (
    PositionDecision,
    PositionDecisionOutcome,
    PositionDecisionReason,
    compose_position_decision,
)
from gmc_rebuild.eligibility import (
    EligibilityConfig,
    EligibilityDecision,
    EligibilityReason,
    check_eligibility,
)
from gmc_rebuild.heartbeat import InMemoryHeartbeat
from gmc_rebuild.kill_switch import InMemoryKillSwitch
from gmc_rebuild.reconciliation import InMemoryReconciliation
from gmc_rebuild.risk import (
    HeartbeatStatus,
    KillSwitchState,
    ReconciliationStatus,
)
from gmc_rebuild.runtime import (
    BLOCKER_HEARTBEAT_STALE,
    BLOCKER_KILL_SWITCH_TRIPPED,
    BLOCKER_RECONCILIATION_FAILED,
    BLOCKER_RECONCILIATION_UNAVAILABLE,
    BLOCKER_RECONCILIATION_WARNING,
    RuntimeShell,
    SafetyVerdict,
)
from gmc_rebuild.signal_intake import SignalIntent, SignalSide

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _intent(**overrides: object) -> SignalIntent:
    kwargs: dict[str, object] = {
        "intent_id": "intent-p6-03-A",
        "symbol": "SIM-P6-03",
        "side": SignalSide.BUY,
        "quantity": 10,
        "rationale": "p6-03 composer tripwire fixture rationale",
    }
    kwargs.update(overrides)
    return SignalIntent(**kwargs)  # type: ignore[arg-type]


def _config(**overrides: object) -> EligibilityConfig:
    kwargs: dict[str, object] = {
        "allowed_symbols": frozenset({"SIM-P6-03", "SIM-OTHER"}),
        "allowed_sides": frozenset({SignalSide.BUY, SignalSide.SELL}),
        "min_quantity": 1,
        "max_quantity": 100,
        "min_rationale_length": 5,
    }
    kwargs.update(overrides)
    return EligibilityConfig(**kwargs)  # type: ignore[arg-type]


def _eligible_decision() -> EligibilityDecision:
    return check_eligibility(_intent(), _config())


def _ineligible_decision() -> EligibilityDecision:
    return check_eligibility(_intent(symbol="UNAUTHORIZED"), _config())


def _clear_verdict() -> SafetyVerdict:
    return SafetyVerdict(
        clear=True,
        blockers=(),
        heartbeat_statuses=MappingProxyType({"operator": HeartbeatStatus.FRESH}),
        kill_switch_state=KillSwitchState.ARMED,
        reconciliation_status=ReconciliationStatus.CLEAN,
        observed_at="2026-05-20T00:00:00Z",
    )


def _blocked_verdict(
    *,
    blockers: tuple[str, ...],
    heartbeat_statuses: MappingProxyType[str, HeartbeatStatus] | None = None,
    kill_switch_state: KillSwitchState = KillSwitchState.ARMED,
    reconciliation_status: ReconciliationStatus = ReconciliationStatus.CLEAN,
) -> SafetyVerdict:
    if heartbeat_statuses is None:
        heartbeat_statuses = MappingProxyType({"operator": HeartbeatStatus.FRESH})
    return SafetyVerdict(
        clear=False,
        blockers=blockers,
        heartbeat_statuses=heartbeat_statuses,
        kill_switch_state=kill_switch_state,
        reconciliation_status=reconciliation_status,
        observed_at="2026-05-20T00:00:00Z",
    )


def _snapshot_intent(intent: SignalIntent) -> tuple[object, ...]:
    return (
        intent.intent_id,
        intent.symbol,
        intent.side,
        intent.quantity,
        intent.rationale,
    )


def _snapshot_eligibility(decision: EligibilityDecision) -> tuple[object, ...]:
    return (decision.outcome, tuple(decision.reasons))


def _snapshot_verdict(verdict: SafetyVerdict) -> tuple[object, ...]:
    return (
        verdict.clear,
        tuple(verdict.blockers),
        dict(verdict.heartbeat_statuses),
        verdict.kill_switch_state,
        verdict.reconciliation_status,
        verdict.observed_at,
    )


# ---------------------------------------------------------------------------
# Would-trade happy path
# ---------------------------------------------------------------------------


def test_would_trade_happy_path_returns_trade_with_empty_reasons() -> None:
    intent = _intent()
    eligibility = _eligible_decision()
    verdict = _clear_verdict()
    decision = compose_position_decision(intent, eligibility, verdict)
    assert decision.outcome is PositionDecisionOutcome.WOULD_TRADE
    assert decision.reasons == ()
    assert decision.intent_id == intent.intent_id
    assert decision.eligibility is eligibility
    assert decision.verdict is verdict


# ---------------------------------------------------------------------------
# Would-skip on ineligibility
# ---------------------------------------------------------------------------


def test_would_skip_on_ineligibility_only() -> None:
    eligibility = _ineligible_decision()
    verdict = _clear_verdict()
    decision = compose_position_decision(_intent(), eligibility, verdict)
    assert decision.outcome is PositionDecisionOutcome.WOULD_SKIP
    assert decision.reasons == (PositionDecisionReason.ELIGIBILITY_INELIGIBLE,)
    # Upstream P6-02 reason taxonomy preserved by value on carried-forward
    # eligibility — the composer does not re-encode the P6-02 reasons.
    assert decision.eligibility.reasons == (EligibilityReason.SYMBOL_NOT_ALLOWED,)


# ---------------------------------------------------------------------------
# Would-skip on each authorized safety blocker reason
# ---------------------------------------------------------------------------


def test_would_skip_on_safety_heartbeat_stale() -> None:
    verdict = _blocked_verdict(
        blockers=(BLOCKER_HEARTBEAT_STALE,),
        heartbeat_statuses=MappingProxyType({"operator": HeartbeatStatus.STALE}),
    )
    decision = compose_position_decision(_intent(), _eligible_decision(), verdict)
    assert decision.outcome is PositionDecisionOutcome.WOULD_SKIP
    assert decision.reasons == (PositionDecisionReason.SAFETY_HEARTBEAT_STALE,)


def test_would_skip_on_safety_kill_switch_not_armed() -> None:
    verdict = _blocked_verdict(
        blockers=(BLOCKER_KILL_SWITCH_TRIPPED,),
        kill_switch_state=KillSwitchState.TRIPPED,
    )
    decision = compose_position_decision(_intent(), _eligible_decision(), verdict)
    assert decision.outcome is PositionDecisionOutcome.WOULD_SKIP
    assert decision.reasons == (PositionDecisionReason.SAFETY_KILL_SWITCH_NOT_ARMED,)


def test_would_skip_on_safety_reconciliation_failed() -> None:
    verdict = _blocked_verdict(
        blockers=(BLOCKER_RECONCILIATION_FAILED,),
        reconciliation_status=ReconciliationStatus.FAILED,
    )
    decision = compose_position_decision(_intent(), _eligible_decision(), verdict)
    assert decision.outcome is PositionDecisionOutcome.WOULD_SKIP
    assert decision.reasons == (PositionDecisionReason.SAFETY_RECONCILIATION_NOT_CLEAN,)


def test_would_skip_on_safety_reconciliation_unavailable() -> None:
    verdict = _blocked_verdict(
        blockers=(BLOCKER_RECONCILIATION_UNAVAILABLE,),
        reconciliation_status=ReconciliationStatus.UNAVAILABLE,
    )
    decision = compose_position_decision(_intent(), _eligible_decision(), verdict)
    assert decision.outcome is PositionDecisionOutcome.WOULD_SKIP
    assert decision.reasons == (PositionDecisionReason.SAFETY_RECONCILIATION_NOT_CLEAN,)


def test_would_skip_on_safety_reconciliation_warning() -> None:
    verdict = _blocked_verdict(
        blockers=(BLOCKER_RECONCILIATION_WARNING,),
        reconciliation_status=ReconciliationStatus.WARNING,
    )
    decision = compose_position_decision(_intent(), _eligible_decision(), verdict)
    assert decision.outcome is PositionDecisionOutcome.WOULD_SKIP
    assert decision.reasons == (PositionDecisionReason.SAFETY_RECONCILIATION_NOT_CLEAN,)


def test_would_skip_on_safety_verdict_not_clear_catchall_for_unknown_blocker() -> None:
    """If a safety verdict is not clear but carries only blocker codes the
    composer does not recognize, the catch-all
    :attr:`PositionDecisionReason.SAFETY_VERDICT_NOT_CLEAR` member is
    emitted. This is the load-bearing defense-in-depth invariant
    against silent breakage if a future ``BLOCKER_*`` constant is
    added to the merged P4-08 set without a matching composer update.
    """
    verdict = SafetyVerdict(
        clear=False,
        blockers=("some_future_blocker_not_known_to_p6_03",),
        heartbeat_statuses=MappingProxyType({"operator": HeartbeatStatus.FRESH}),
        kill_switch_state=KillSwitchState.ARMED,
        reconciliation_status=ReconciliationStatus.CLEAN,
        observed_at="2026-05-20T00:00:00Z",
    )
    decision = compose_position_decision(_intent(), _eligible_decision(), verdict)
    assert decision.outcome is PositionDecisionOutcome.WOULD_SKIP
    assert decision.reasons == (PositionDecisionReason.SAFETY_VERDICT_NOT_CLEAR,)


def test_would_skip_on_multiple_safety_blockers_canonical_order() -> None:
    """Multiple safety blockers surface in the canonical declaration order
    of :class:`PositionDecisionReason`, regardless of the order they
    appear in :attr:`SafetyVerdict.blockers`.
    """
    verdict = SafetyVerdict(
        clear=False,
        blockers=(
            BLOCKER_RECONCILIATION_FAILED,
            BLOCKER_KILL_SWITCH_TRIPPED,
            BLOCKER_HEARTBEAT_STALE,
        ),
        heartbeat_statuses=MappingProxyType({"operator": HeartbeatStatus.STALE}),
        kill_switch_state=KillSwitchState.TRIPPED,
        reconciliation_status=ReconciliationStatus.FAILED,
        observed_at="2026-05-20T00:00:00Z",
    )
    decision = compose_position_decision(_intent(), _eligible_decision(), verdict)
    assert decision.outcome is PositionDecisionOutcome.WOULD_SKIP
    assert decision.reasons == (
        PositionDecisionReason.SAFETY_HEARTBEAT_STALE,
        PositionDecisionReason.SAFETY_KILL_SWITCH_NOT_ARMED,
        PositionDecisionReason.SAFETY_RECONCILIATION_NOT_CLEAN,
    )


# ---------------------------------------------------------------------------
# Composed failure paths
# ---------------------------------------------------------------------------


def test_would_skip_on_composed_ineligibility_and_safety_blocker() -> None:
    verdict = _blocked_verdict(
        blockers=(BLOCKER_HEARTBEAT_STALE,),
        heartbeat_statuses=MappingProxyType({"operator": HeartbeatStatus.STALE}),
    )
    decision = compose_position_decision(_intent(), _ineligible_decision(), verdict)
    assert decision.outcome is PositionDecisionOutcome.WOULD_SKIP
    assert decision.reasons == (
        PositionDecisionReason.ELIGIBILITY_INELIGIBLE,
        PositionDecisionReason.SAFETY_HEARTBEAT_STALE,
    )


def test_would_skip_on_composed_ineligibility_and_multiple_safety_blockers() -> None:
    verdict = SafetyVerdict(
        clear=False,
        blockers=(
            BLOCKER_HEARTBEAT_STALE,
            BLOCKER_KILL_SWITCH_TRIPPED,
            BLOCKER_RECONCILIATION_FAILED,
        ),
        heartbeat_statuses=MappingProxyType({"operator": HeartbeatStatus.STALE}),
        kill_switch_state=KillSwitchState.TRIPPED,
        reconciliation_status=ReconciliationStatus.FAILED,
        observed_at="2026-05-20T00:00:00Z",
    )
    decision = compose_position_decision(_intent(), _ineligible_decision(), verdict)
    assert decision.outcome is PositionDecisionOutcome.WOULD_SKIP
    assert decision.reasons == (
        PositionDecisionReason.ELIGIBILITY_INELIGIBLE,
        PositionDecisionReason.SAFETY_HEARTBEAT_STALE,
        PositionDecisionReason.SAFETY_KILL_SWITCH_NOT_ARMED,
        PositionDecisionReason.SAFETY_RECONCILIATION_NOT_CLEAN,
    )


# ---------------------------------------------------------------------------
# Dataclass biconditional invariant
# ---------------------------------------------------------------------------


def test_biconditional_would_trade_requires_empty_reasons() -> None:
    raised: Exception | None = None
    try:
        PositionDecision(
            outcome=PositionDecisionOutcome.WOULD_TRADE,
            reasons=(PositionDecisionReason.ELIGIBILITY_INELIGIBLE,),
            intent_id="intent-p6-03-A",
            eligibility=_eligible_decision(),
            verdict=_clear_verdict(),
        )
    except ValueError as exc:
        raised = exc
    assert isinstance(raised, ValueError)
    assert "WOULD_TRADE" in str(raised)


def test_biconditional_would_skip_requires_non_empty_reasons() -> None:
    raised: Exception | None = None
    try:
        PositionDecision(
            outcome=PositionDecisionOutcome.WOULD_SKIP,
            reasons=(),
            intent_id="intent-p6-03-A",
            eligibility=_eligible_decision(),
            verdict=_clear_verdict(),
        )
    except ValueError as exc:
        raised = exc
    assert isinstance(raised, ValueError)
    assert "WOULD_SKIP" in str(raised)


# ---------------------------------------------------------------------------
# Closed-set StrEnum invariants
# ---------------------------------------------------------------------------


def test_position_decision_outcome_is_closed_two_member_strenum() -> None:
    assert set(PositionDecisionOutcome) == {
        PositionDecisionOutcome.WOULD_TRADE,
        PositionDecisionOutcome.WOULD_SKIP,
    }
    assert PositionDecisionOutcome.WOULD_TRADE.value == "WOULD_TRADE"
    assert PositionDecisionOutcome.WOULD_SKIP.value == "WOULD_SKIP"


def test_position_decision_outcome_is_a_str_subclass() -> None:
    assert isinstance(PositionDecisionOutcome.WOULD_TRADE, str)


def test_position_decision_reason_is_closed_five_member_strenum() -> None:
    assert set(PositionDecisionReason) == {
        PositionDecisionReason.ELIGIBILITY_INELIGIBLE,
        PositionDecisionReason.SAFETY_HEARTBEAT_STALE,
        PositionDecisionReason.SAFETY_KILL_SWITCH_NOT_ARMED,
        PositionDecisionReason.SAFETY_RECONCILIATION_NOT_CLEAN,
        PositionDecisionReason.SAFETY_VERDICT_NOT_CLEAR,
    }


def test_position_decision_reason_values_match_member_names() -> None:
    for reason in PositionDecisionReason:
        assert reason.value == reason.name


def test_position_decision_reason_is_a_str_subclass() -> None:
    assert isinstance(PositionDecisionReason.ELIGIBILITY_INELIGIBLE, str)


# ---------------------------------------------------------------------------
# Frozen / slotted / closed-shape invariants
# ---------------------------------------------------------------------------


def test_decision_is_frozen() -> None:
    decision = compose_position_decision(_intent(), _eligible_decision(), _clear_verdict())
    raised: Exception | None = None
    try:
        decision.outcome = PositionDecisionOutcome.WOULD_SKIP  # type: ignore[misc]
    except FrozenInstanceError as exc:
        raised = exc
    assert isinstance(raised, FrozenInstanceError)


def test_decision_uses_slots_and_has_no_dict() -> None:
    decision = compose_position_decision(_intent(), _eligible_decision(), _clear_verdict())
    assert hasattr(PositionDecision, "__slots__")
    assert not hasattr(decision, "__dict__")


def test_decision_field_set_is_closed_five_fields_in_canonical_order() -> None:
    expected = (
        "outcome",
        "reasons",
        "intent_id",
        "eligibility",
        "verdict",
    )
    assert tuple(PositionDecision.__dataclass_fields__) == expected


# ---------------------------------------------------------------------------
# Deterministic repeat calls
# ---------------------------------------------------------------------------


def test_repeat_calls_return_equal_decisions_would_trade_path() -> None:
    intent = _intent()
    eligibility = _eligible_decision()
    verdict = _clear_verdict()
    decisions = [compose_position_decision(intent, eligibility, verdict) for _ in range(5)]
    for d in decisions[1:]:
        assert d == decisions[0]


def test_repeat_calls_return_equal_decisions_would_skip_path() -> None:
    intent = _intent()
    eligibility = _ineligible_decision()
    verdict = _blocked_verdict(
        blockers=(BLOCKER_HEARTBEAT_STALE,),
        heartbeat_statuses=MappingProxyType({"operator": HeartbeatStatus.STALE}),
    )
    decisions = [compose_position_decision(intent, eligibility, verdict) for _ in range(5)]
    for d in decisions[1:]:
        assert d == decisions[0]


# ---------------------------------------------------------------------------
# Non-mutation of inputs
# ---------------------------------------------------------------------------


def test_compose_does_not_mutate_intent() -> None:
    intent = _intent()
    eligibility = _ineligible_decision()
    verdict = _blocked_verdict(blockers=(BLOCKER_HEARTBEAT_STALE,))
    snapshot = _snapshot_intent(intent)
    for _ in range(3):
        compose_position_decision(intent, eligibility, verdict)
    assert _snapshot_intent(intent) == snapshot


def test_compose_does_not_mutate_eligibility_decision() -> None:
    intent = _intent()
    eligibility = _ineligible_decision()
    verdict = _clear_verdict()
    snapshot = _snapshot_eligibility(eligibility)
    for _ in range(3):
        compose_position_decision(intent, eligibility, verdict)
    assert _snapshot_eligibility(eligibility) == snapshot


def test_compose_does_not_mutate_safety_verdict() -> None:
    intent = _intent()
    eligibility = _eligible_decision()
    verdict = _blocked_verdict(blockers=(BLOCKER_HEARTBEAT_STALE,))
    snapshot = _snapshot_verdict(verdict)
    for _ in range(3):
        compose_position_decision(intent, eligibility, verdict)
    assert _snapshot_verdict(verdict) == snapshot


# ---------------------------------------------------------------------------
# Preservation of carried-forward context
# ---------------------------------------------------------------------------


def test_intent_id_carried_forward_by_value() -> None:
    intent = _intent(intent_id="intent-p6-03-carry")
    decision = compose_position_decision(intent, _eligible_decision(), _clear_verdict())
    assert decision.intent_id == "intent-p6-03-carry"


def test_eligibility_carried_forward_by_identity() -> None:
    intent = _intent()
    eligibility = _ineligible_decision()
    decision = compose_position_decision(intent, eligibility, _clear_verdict())
    assert decision.eligibility is eligibility


def test_verdict_carried_forward_by_identity() -> None:
    intent = _intent()
    verdict = _blocked_verdict(blockers=(BLOCKER_HEARTBEAT_STALE,))
    decision = compose_position_decision(intent, _eligible_decision(), verdict)
    assert decision.verdict is verdict


# ---------------------------------------------------------------------------
# Type validation
# ---------------------------------------------------------------------------


def test_compose_rejects_non_signal_intent() -> None:
    raised: Exception | None = None
    try:
        compose_position_decision(
            "not-an-intent",  # type: ignore[arg-type]
            _eligible_decision(),
            _clear_verdict(),
        )
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "SignalIntent" in str(raised)


def test_compose_rejects_non_eligibility_decision() -> None:
    raised: Exception | None = None
    try:
        compose_position_decision(
            _intent(),
            "not-an-eligibility-decision",  # type: ignore[arg-type]
            _clear_verdict(),
        )
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "EligibilityDecision" in str(raised)


def test_compose_rejects_non_safety_verdict() -> None:
    raised: Exception | None = None
    try:
        compose_position_decision(
            _intent(),
            _eligible_decision(),
            "not-a-safety-verdict",  # type: ignore[arg-type]
        )
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "SafetyVerdict" in str(raised)


def test_decision_rejects_non_outcome_outcome() -> None:
    raised: Exception | None = None
    try:
        PositionDecision(
            outcome="WOULD_TRADE",  # type: ignore[arg-type]
            reasons=(),
            intent_id="intent-p6-03-A",
            eligibility=_eligible_decision(),
            verdict=_clear_verdict(),
        )
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "outcome" in str(raised)


def test_decision_rejects_non_tuple_reasons() -> None:
    raised: Exception | None = None
    try:
        PositionDecision(
            outcome=PositionDecisionOutcome.WOULD_SKIP,
            reasons=[PositionDecisionReason.ELIGIBILITY_INELIGIBLE],  # type: ignore[arg-type]
            intent_id="intent-p6-03-A",
            eligibility=_eligible_decision(),
            verdict=_clear_verdict(),
        )
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "reasons" in str(raised)


def test_decision_rejects_non_reason_reason_member() -> None:
    raised: Exception | None = None
    try:
        PositionDecision(
            outcome=PositionDecisionOutcome.WOULD_SKIP,
            reasons=("ELIGIBILITY_INELIGIBLE",),  # type: ignore[arg-type]
            intent_id="intent-p6-03-A",
            eligibility=_eligible_decision(),
            verdict=_clear_verdict(),
        )
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "reasons" in str(raised)


def test_decision_rejects_non_string_intent_id() -> None:
    raised: Exception | None = None
    try:
        PositionDecision(
            outcome=PositionDecisionOutcome.WOULD_TRADE,
            reasons=(),
            intent_id=42,  # type: ignore[arg-type]
            eligibility=_eligible_decision(),
            verdict=_clear_verdict(),
        )
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "intent_id" in str(raised)


def test_decision_rejects_empty_intent_id() -> None:
    raised: Exception | None = None
    try:
        PositionDecision(
            outcome=PositionDecisionOutcome.WOULD_TRADE,
            reasons=(),
            intent_id="",
            eligibility=_eligible_decision(),
            verdict=_clear_verdict(),
        )
    except ValueError as exc:
        raised = exc
    assert isinstance(raised, ValueError)
    assert "intent_id" in str(raised)


def test_decision_rejects_non_eligibility_decision_eligibility() -> None:
    raised: Exception | None = None
    try:
        PositionDecision(
            outcome=PositionDecisionOutcome.WOULD_TRADE,
            reasons=(),
            intent_id="intent-p6-03-A",
            eligibility="not-an-eligibility-decision",  # type: ignore[arg-type]
            verdict=_clear_verdict(),
        )
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "eligibility" in str(raised)


def test_decision_rejects_non_safety_verdict_verdict() -> None:
    raised: Exception | None = None
    try:
        PositionDecision(
            outcome=PositionDecisionOutcome.WOULD_TRADE,
            reasons=(),
            intent_id="intent-p6-03-A",
            eligibility=_eligible_decision(),
            verdict="not-a-safety-verdict",  # type: ignore[arg-type]
        )
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "verdict" in str(raised)


# ---------------------------------------------------------------------------
# Equality and hashability
# ---------------------------------------------------------------------------


def test_two_decisions_with_same_fields_compare_equal() -> None:
    intent = _intent()
    eligibility = _eligible_decision()
    verdict = _clear_verdict()
    a = compose_position_decision(intent, eligibility, verdict)
    b = compose_position_decision(intent, eligibility, verdict)
    assert a == b


def test_decision_hashability_tracks_carried_safety_verdict() -> None:
    """Hashability of :class:`PositionDecision` is structurally inherited
    from the carried :class:`SafetyVerdict`. The merged P4-06
    ``SafetyVerdict`` carries a ``Mapping[str, HeartbeatStatus]``
    field, which is unhashable; therefore a ``PositionDecision``
    that carries that verdict is also unhashable. The composer must
    not paper over this — the upstream P4-06 closed shape is
    preserved as-is, and the dataclass-generated ``__hash__`` raises
    ``TypeError`` consistent with the carried field's
    unhashability.
    """
    decision = compose_position_decision(_intent(), _eligible_decision(), _clear_verdict())
    raised: Exception | None = None
    try:
        hash(decision)
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)


def test_decisions_differing_in_outcome_are_not_equal() -> None:
    intent = _intent()
    eligibility = _eligible_decision()
    trade = compose_position_decision(intent, eligibility, _clear_verdict())
    skip = compose_position_decision(
        intent,
        eligibility,
        _blocked_verdict(blockers=(BLOCKER_HEARTBEAT_STALE,)),
    )
    assert trade != skip


def test_decisions_differing_in_reasons_are_not_equal() -> None:
    intent = _intent()
    eligibility = _eligible_decision()
    heartbeat_skip = compose_position_decision(
        intent,
        eligibility,
        _blocked_verdict(blockers=(BLOCKER_HEARTBEAT_STALE,)),
    )
    kill_switch_skip = compose_position_decision(
        intent,
        eligibility,
        _blocked_verdict(
            blockers=(BLOCKER_KILL_SWITCH_TRIPPED,),
            kill_switch_state=KillSwitchState.TRIPPED,
        ),
    )
    assert heartbeat_skip != kill_switch_skip


# ---------------------------------------------------------------------------
# Composed integration with P3 / P4-06 in-memory fakes
# ---------------------------------------------------------------------------


def _build_runtime_shell(
    *,
    base_time: datetime,
    heartbeat_components: tuple[str, ...] = ("operator",),
) -> tuple[RuntimeShell, InMemoryHeartbeat, InMemoryKillSwitch, InMemoryReconciliation]:
    heartbeat = InMemoryHeartbeat(observed_at=base_time)
    for component in heartbeat_components:
        heartbeat.beat(component, base_time)
    kill_switch = InMemoryKillSwitch(observed_at=base_time)
    reconciliation = InMemoryReconciliation(checked_at=base_time)
    reconciliation.set_next(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
    )
    shell = RuntimeShell(
        heartbeat=heartbeat,
        kill_switch=kill_switch,
        reconciliation=reconciliation,
        required_components=heartbeat_components,
    )
    return shell, heartbeat, kill_switch, reconciliation


def test_composed_pipeline_would_trade_via_real_runtime_shell() -> None:
    base_time = datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC)
    shell, _, _, _ = _build_runtime_shell(base_time=base_time)
    verdict = shell.evaluate()
    assert verdict.clear is True
    decision = compose_position_decision(_intent(), _eligible_decision(), verdict)
    assert decision.outcome is PositionDecisionOutcome.WOULD_TRADE
    assert decision.reasons == ()


def test_composed_pipeline_would_skip_heartbeat_stale_via_runtime_shell() -> None:
    base_time = datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC)
    shell, heartbeat, _, _ = _build_runtime_shell(base_time=base_time)
    # Push the operator heartbeat past the default 8h staleness window.
    heartbeat.advance(9 * 3600.0)
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert BLOCKER_HEARTBEAT_STALE in verdict.blockers
    decision = compose_position_decision(_intent(), _eligible_decision(), verdict)
    assert decision.outcome is PositionDecisionOutcome.WOULD_SKIP
    assert PositionDecisionReason.SAFETY_HEARTBEAT_STALE in decision.reasons


def test_composed_pipeline_would_skip_kill_switch_via_runtime_shell() -> None:
    base_time = datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC)
    shell, _, kill_switch, _ = _build_runtime_shell(base_time=base_time)
    kill_switch.trip(reason="composed-pipeline-test", triggered_by="p6-03-test")
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert BLOCKER_KILL_SWITCH_TRIPPED in verdict.blockers
    decision = compose_position_decision(_intent(), _eligible_decision(), verdict)
    assert decision.outcome is PositionDecisionOutcome.WOULD_SKIP
    assert PositionDecisionReason.SAFETY_KILL_SWITCH_NOT_ARMED in decision.reasons


def test_composed_pipeline_would_skip_reconciliation_failed_via_runtime_shell() -> None:
    base_time = datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC)
    shell, _, _, reconciliation = _build_runtime_shell(base_time=base_time)
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=42.0,
    )
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert BLOCKER_RECONCILIATION_FAILED in verdict.blockers
    decision = compose_position_decision(_intent(), _eligible_decision(), verdict)
    assert decision.outcome is PositionDecisionOutcome.WOULD_SKIP
    assert PositionDecisionReason.SAFETY_RECONCILIATION_NOT_CLEAN in decision.reasons


def test_composed_pipeline_would_skip_on_ineligibility_with_clear_safety() -> None:
    base_time = datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC)
    shell, _, _, _ = _build_runtime_shell(base_time=base_time)
    verdict = shell.evaluate()
    decision = compose_position_decision(_intent(), _ineligible_decision(), verdict)
    assert decision.outcome is PositionDecisionOutcome.WOULD_SKIP
    assert decision.reasons == (PositionDecisionReason.ELIGIBILITY_INELIGIBLE,)


# ---------------------------------------------------------------------------
# Inertness self-check: no forbidden runtime imports
# ---------------------------------------------------------------------------


_AUTHORIZED_IMPORT_PREFIXES: tuple[str, ...] = (
    "__future__",
    "dataclasses",
    "enum",
    "gmc_rebuild.decision",
    "gmc_rebuild.eligibility",
    "gmc_rebuild.runtime",
    "gmc_rebuild.signal_intake",
)


_FORBIDDEN_IMPORT_ROOTS: frozenset[str] = frozenset(
    {
        "os",
        "socket",
        "requests",
        "urllib",
        "http",
        "threading",
        "asyncio",
        "subprocess",
        "sqlite3",
        "pickle",
        "shelve",
        "ssl",
        "smtplib",
        "ftplib",
        "time",
    }
)


def _collect_imported_modules_from_subpackage_source() -> set[str]:
    subpackage_root = (
        Path(__file__).resolve().parents[1].parent / "src" / "gmc_rebuild" / "decision"
    )
    imported: set[str] = set()
    for path in sorted(subpackage_root.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
                imported.add(node.module)
    return imported


def test_decision_source_has_no_forbidden_runtime_imports() -> None:
    imported = _collect_imported_modules_from_subpackage_source()
    roots = {name.split(".", 1)[0] for name in imported}
    overlap = roots & _FORBIDDEN_IMPORT_ROOTS
    assert overlap == set(), (
        f"forbidden import roots present in decision source: {sorted(overlap)!r}"
    )


def test_decision_source_only_imports_from_authorized_prefixes() -> None:
    imported = _collect_imported_modules_from_subpackage_source()
    unauthorized: list[str] = []
    for name in sorted(imported):
        if not any(
            name == prefix or name.startswith(prefix + ".")
            for prefix in _AUTHORIZED_IMPORT_PREFIXES
        ):
            unauthorized.append(name)
    assert unauthorized == [], f"unauthorized imports in decision source: {unauthorized!r}"


def test_decision_source_has_no_main_block_or_sleep_or_builtin_io() -> None:
    """Belt-and-suspenders substring scan for patterns the import-graph
    test above cannot catch: ``__main__`` statements, ``time.sleep(`` /
    ``urllib`` / ``requests.`` / ``socket.`` call sites, and the
    ``open(`` builtin. ``os.environ`` and ``os.getenv`` are not
    substring-checked because docstrings legitimately use those tokens
    in backticked reassurance prose; the AST import scan above already
    proves :mod:`os` is not imported.
    """
    subpackage_root = (
        Path(__file__).resolve().parents[1].parent / "src" / "gmc_rebuild" / "decision"
    )
    for path in sorted(subpackage_root.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert 'if __name__ == "__main__"' not in source, path
        assert "time.sleep(" not in source, path
        assert "socket." not in source, path
        assert "urllib" not in source, path
        assert "requests." not in source, path
        assert "open(" not in source, path


# ---------------------------------------------------------------------------
# Root package does not re-export the new surface
# ---------------------------------------------------------------------------


def test_gmc_rebuild_root_does_not_re_export_decision_surface() -> None:
    root = importlib.import_module("gmc_rebuild")
    for name in (
        "PositionDecision",
        "PositionDecisionOutcome",
        "PositionDecisionReason",
        "compose_position_decision",
    ):
        assert not hasattr(root, name), (
            f"gmc_rebuild unexpectedly re-exports {name!r}; per P6-03 the new "
            f"surface must be reachable only via gmc_rebuild.decision."
        )


def test_gmc_rebuild_root_all_does_not_include_decision_surface() -> None:
    root = importlib.import_module("gmc_rebuild")
    root_all = list(getattr(root, "__all__", ()))
    for name in (
        "PositionDecision",
        "PositionDecisionOutcome",
        "PositionDecisionReason",
        "compose_position_decision",
    ):
        assert name not in root_all, (
            f"gmc_rebuild.__all__ unexpectedly includes {name!r}; "
            f"per P6-03 the new surface must not be re-exported."
        )
