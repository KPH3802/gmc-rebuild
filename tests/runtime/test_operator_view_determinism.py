"""P5-07 operator-view determinism / idempotence tripwires.

This module is a **tripwire-only** integration test suite that pins
the byte-identical determinism and idempotence of
:func:`gmc_rebuild.runtime.format_safety_verdict` under the real
composed P3-03 / P3-04 / P3-05 / P4-06 / P4-07 / P5-01 / P5-02
pipeline.

The tests verify that repeated calls to ``format_safety_verdict``
for the same :class:`SafetyVerdict` produce
:class:`OperatorSafetyView` instances that compare equal and whose
``render()`` strings compare byte-for-byte equal, and that repeated
rendering does **not** observably perturb the P3 in-memory fakes
(:class:`InMemoryHeartbeat`, :class:`InMemoryKillSwitch`,
:class:`InMemoryReconciliation`), the safety surface
(:class:`SafetyVerdict`, :class:`RuntimeShell`), or the simulation
surface (:class:`SimulationBoundary`, :class:`SimulatedIntent`,
:class:`SimulatedOrderIntent`).

This is **direction (b)** of the four planning-level candidate
sketches recorded in
``governance/authorizations/2026-05-18_p5-07-planning.md``; the
other three candidate directions (closed-enum / closed-field
defense-in-depth; ADR-005 / ADR-002 / ADR-003 composed-policy
alignment; simulation surface inertness self-check) remain
planning-level candidates only.

Authorization: ``governance/authorizations/2026-05-18_p5-07.md``.

This module introduces **no new production behaviour**: every test
composes already-merged public surfaces from
``gmc_rebuild.heartbeat``, ``gmc_rebuild.kill_switch``,
``gmc_rebuild.reconciliation``, ``gmc_rebuild.risk``,
``gmc_rebuild.runtime``, and ``gmc_rebuild.simulation``. It adds no
module under ``src/**``, no new public symbol, no new field, no new
method, and no ``SimulationLane`` / ``SimulatedOrderSide`` /
``SimulatedOrderType`` member. Tests avoid ``pytest.raises`` and
fixture-typed parameters so the mypy-strict pre-commit hook does not
need a pytest-stub dependency, mirroring the existing
``tests/runtime/test_operator_view.py``,
``tests/runtime/test_operator_view_composed_safety_foundation.py``,
``tests/simulation/test_composed_safety_foundation.py``,
``tests/simulation/test_propose_symmetry.py``, and the other
``tests/simulation/`` modules.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from gmc_rebuild.heartbeat import InMemoryHeartbeat
from gmc_rebuild.kill_switch import InMemoryKillSwitch
from gmc_rebuild.reconciliation import InMemoryReconciliation
from gmc_rebuild.risk import (
    ReconciliationStatus,
)
from gmc_rebuild.runtime import (
    BLOCKER_HEARTBEAT_STALE,
    BLOCKER_KILL_SWITCH_TRIPPED,
    BLOCKER_RECONCILIATION_FAILED,
    BLOCKER_RECONCILIATION_UNAVAILABLE,
    BLOCKER_RECONCILIATION_WARNING,
    VERDICT_BLOCKED,
    VERDICT_CLEAR,
    OperatorSafetyView,
    RuntimeShell,
    SafetyVerdict,
    format_safety_verdict,
)
from gmc_rebuild.simulation import (
    SimulatedIntent,
    SimulatedOrderIntent,
    SimulatedOrderSide,
    SimulatedOrderType,
    SimulationBoundary,
    SimulationBoundaryError,
    SimulationLane,
)

_FIXED_CLOCK = datetime(2026, 5, 18, 14, 0, 0, tzinfo=UTC)
_FIXED_CLOCK_Z = "2026-05-18T14:00:00Z"
_REPEAT_COUNT = 12


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_clear_pipeline() -> tuple[
    InMemoryHeartbeat,
    InMemoryKillSwitch,
    InMemoryReconciliation,
    RuntimeShell,
]:
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    reconciliation.enqueue(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"p5-07-scenario": "clear"},
    )
    shell = RuntimeShell(
        heartbeat=heartbeat,
        kill_switch=kill_switch,
        reconciliation=reconciliation,
        required_components=("operator",),
    )
    return heartbeat, kill_switch, reconciliation, shell


def _placeholder_intent(*, intent_id: str = "intent-p5-07-X") -> SimulatedIntent:
    return SimulatedIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_FIXED_CLOCK_Z,
    )


def _market_order(*, intent_id: str = "order-p5-07-A") -> SimulatedOrderIntent:
    return SimulatedOrderIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_FIXED_CLOCK_Z,
        symbol="SIM-P5-07-A",
        side=SimulatedOrderSide.BUY,
        quantity=10,
        order_type=SimulatedOrderType.MARKET,
        limit_price=None,
    )


def _limit_order(*, intent_id: str = "order-p5-07-B") -> SimulatedOrderIntent:
    return SimulatedOrderIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_FIXED_CLOCK_Z,
        symbol="SIM-P5-07-B",
        side=SimulatedOrderSide.SELL,
        quantity=25,
        order_type=SimulatedOrderType.LIMIT,
        limit_price=7.5,
    )


def _verdict_snapshot(verdict: SafetyVerdict) -> tuple[object, ...]:
    return (
        verdict.clear,
        verdict.blockers,
        verdict.kill_switch_state,
        verdict.reconciliation_status,
        verdict.observed_at,
        dict(verdict.heartbeat_statuses),
    )


def _placeholder_snapshot(intent: SimulatedIntent) -> tuple[object, ...]:
    return (intent.lane, intent.intent_id, intent.created_at)


def _order_snapshot(order: SimulatedOrderIntent) -> tuple[object, ...]:
    return (
        order.lane,
        order.intent_id,
        order.created_at,
        order.symbol,
        order.side,
        order.quantity,
        order.order_type,
        order.limit_price,
    )


def _kill_switch_snapshot(kill_switch: InMemoryKillSwitch) -> tuple[object, ...]:
    decision = kill_switch.current()
    return (decision.state, decision.observed_at, decision.reason, decision.triggered_by)


def _expect_boundary_error(call: object, match: str) -> SimulationBoundaryError:
    raised: Exception | None = None
    try:
        call()  # type: ignore[operator]
    except SimulationBoundaryError as exc:
        raised = exc
    assert isinstance(raised, SimulationBoundaryError), (
        f"expected SimulationBoundaryError matching {match!r}, got {raised!r}"
    )
    assert match in str(raised), (
        f"SimulationBoundaryError message {str(raised)!r} missing {match!r}"
    )
    return raised


def _make_blocked_pipeline_heartbeat_stale() -> tuple[
    InMemoryHeartbeat,
    InMemoryKillSwitch,
    InMemoryReconciliation,
    RuntimeShell,
]:
    heartbeat, kill_switch, reconciliation, shell = _build_clear_pipeline()
    heartbeat.advance(9 * 3600.0)
    return heartbeat, kill_switch, reconciliation, shell


def _make_blocked_pipeline_kill_switch_tripped() -> tuple[
    InMemoryHeartbeat,
    InMemoryKillSwitch,
    InMemoryReconciliation,
    RuntimeShell,
]:
    heartbeat, kill_switch, reconciliation, shell = _build_clear_pipeline()
    kill_switch.trip(reason="p5-07 determinism trip", triggered_by="operator")
    return heartbeat, kill_switch, reconciliation, shell


def _make_blocked_pipeline_reconciliation_failed() -> tuple[
    InMemoryHeartbeat,
    InMemoryKillSwitch,
    InMemoryReconciliation,
    RuntimeShell,
]:
    heartbeat, kill_switch, reconciliation, shell = _build_clear_pipeline()
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=42.5,
        details={"p5-07-scenario": "failed"},
    )
    return heartbeat, kill_switch, reconciliation, shell


def _make_blocked_pipeline_reconciliation_unavailable() -> tuple[
    InMemoryHeartbeat,
    InMemoryKillSwitch,
    InMemoryReconciliation,
    RuntimeShell,
]:
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    shell = RuntimeShell(
        heartbeat=heartbeat,
        kill_switch=kill_switch,
        reconciliation=reconciliation,
        required_components=("operator",),
    )
    return heartbeat, kill_switch, reconciliation, shell


def _make_blocked_pipeline_reconciliation_warning() -> tuple[
    InMemoryHeartbeat,
    InMemoryKillSwitch,
    InMemoryReconciliation,
    RuntimeShell,
]:
    heartbeat, kill_switch, reconciliation, shell = _build_clear_pipeline()
    reconciliation.set_next(
        status=ReconciliationStatus.WARNING,
        tolerance=10.0,
        observed_delta=3.0,
        details={"p5-07-scenario": "warning"},
    )
    return heartbeat, kill_switch, reconciliation, shell


def _make_blocked_pipeline_multi() -> tuple[
    InMemoryHeartbeat,
    InMemoryKillSwitch,
    InMemoryReconciliation,
    RuntimeShell,
]:
    heartbeat, kill_switch, reconciliation, shell = _build_clear_pipeline()
    heartbeat.advance(9 * 3600.0)
    kill_switch.trip(reason="p5-07 multi-blocker trip", triggered_by="operator")
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=99.0,
        details={"p5-07-scenario": "multi-blocker"},
    )
    return heartbeat, kill_switch, reconciliation, shell


def _render_n(verdict: SafetyVerdict, n: int = _REPEAT_COUNT) -> list[OperatorSafetyView]:
    return [format_safety_verdict(verdict) for _ in range(n)]


# ---------------------------------------------------------------------------
# Invariant 1 — Clear verdict: byte-identical determinism across repeated calls
# ---------------------------------------------------------------------------


def test_clear_verdict_format_is_byte_identical_across_repeated_calls() -> None:
    _heartbeat, _kill_switch, _reconciliation, shell = _build_clear_pipeline()
    verdict = shell.evaluate()
    assert verdict.clear is True
    views = _render_n(verdict)
    first = views[0]
    assert first.status == VERDICT_CLEAR
    first_render = first.render()
    for view in views[1:]:
        assert view == first
        assert view.render() == first_render
    # SHA-style identity check: collapse every render into a single string set.
    rendered_set = {view.render() for view in views}
    assert len(rendered_set) == 1
    assert next(iter(rendered_set)) == first_render


# ---------------------------------------------------------------------------
# Invariant 2 — Blocked verdict (each BLOCKER_* code): byte-identical determinism
# ---------------------------------------------------------------------------


def test_each_blocker_code_format_is_byte_identical_across_repeated_calls() -> None:
    builders = (
        (_make_blocked_pipeline_heartbeat_stale, BLOCKER_HEARTBEAT_STALE),
        (_make_blocked_pipeline_kill_switch_tripped, BLOCKER_KILL_SWITCH_TRIPPED),
        (_make_blocked_pipeline_reconciliation_failed, BLOCKER_RECONCILIATION_FAILED),
        (
            _make_blocked_pipeline_reconciliation_unavailable,
            BLOCKER_RECONCILIATION_UNAVAILABLE,
        ),
        (_make_blocked_pipeline_reconciliation_warning, BLOCKER_RECONCILIATION_WARNING),
    )
    for builder, blocker_code in builders:
        _heartbeat, _kill_switch, _reconciliation, shell = builder()
        verdict = shell.evaluate()
        assert verdict.clear is False, (
            f"builder {builder.__name__} produced a clear verdict; expected blocked"
        )
        assert blocker_code in verdict.blockers, (
            f"builder {builder.__name__} produced blockers {verdict.blockers!r} "
            f"missing expected code {blocker_code!r}"
        )
        views = _render_n(verdict)
        first = views[0]
        assert first.status == VERDICT_BLOCKED
        first_render = first.render()
        rendered_set = {view.render() for view in views}
        assert len(rendered_set) == 1, (
            f"builder {builder.__name__} produced non-identical renders: {rendered_set!r}"
        )
        assert next(iter(rendered_set)) == first_render
        for view in views[1:]:
            assert view == first
            assert view.render() == first_render


# ---------------------------------------------------------------------------
# Invariant 3 — Multi-blocker: byte-identical determinism across repeated calls
# ---------------------------------------------------------------------------


def test_multi_blocker_format_is_byte_identical_across_repeated_calls() -> None:
    _heartbeat, _kill_switch, _reconciliation, shell = _make_blocked_pipeline_multi()
    verdict = shell.evaluate()
    assert verdict.clear is False
    for code in (
        BLOCKER_HEARTBEAT_STALE,
        BLOCKER_KILL_SWITCH_TRIPPED,
        BLOCKER_RECONCILIATION_FAILED,
    ):
        assert code in verdict.blockers, (
            f"multi-blocker verdict missing expected code {code!r}: {verdict.blockers!r}"
        )
    views = _render_n(verdict)
    first = views[0]
    first_render = first.render()
    rendered_set = {view.render() for view in views}
    assert len(rendered_set) == 1
    assert next(iter(rendered_set)) == first_render
    for view in views[1:]:
        assert view == first
        assert view.render() == first_render


# ---------------------------------------------------------------------------
# Invariant 4 — Field-level idempotence: every public field stable across calls
# ---------------------------------------------------------------------------


def test_every_public_field_is_identical_across_repeated_calls_for_each_scenario() -> None:
    builders = (
        _build_clear_pipeline,
        _make_blocked_pipeline_heartbeat_stale,
        _make_blocked_pipeline_kill_switch_tripped,
        _make_blocked_pipeline_reconciliation_failed,
        _make_blocked_pipeline_reconciliation_unavailable,
        _make_blocked_pipeline_reconciliation_warning,
        _make_blocked_pipeline_multi,
    )
    for builder in builders:
        _heartbeat, _kill_switch, _reconciliation, shell = builder()
        verdict = shell.evaluate()
        views = _render_n(verdict)
        first = views[0]
        for view in views[1:]:
            assert view.status == first.status, (
                f"builder {builder.__name__} status drift: {view.status!r} vs {first.status!r}"
            )
            assert view.blocker_lines == first.blocker_lines, (
                f"builder {builder.__name__} blocker_lines drift"
            )
            assert view.heartbeat_lines == first.heartbeat_lines, (
                f"builder {builder.__name__} heartbeat_lines drift"
            )
            assert view.kill_switch_line == first.kill_switch_line, (
                f"builder {builder.__name__} kill_switch_line drift"
            )
            assert view.reconciliation_line == first.reconciliation_line, (
                f"builder {builder.__name__} reconciliation_line drift"
            )
            assert view.observed_at == first.observed_at, (
                f"builder {builder.__name__} observed_at drift"
            )


# ---------------------------------------------------------------------------
# Invariant 5 — Distinct-but-equal verdict idempotence
# ---------------------------------------------------------------------------


def test_dataclasses_replace_produces_byte_identical_view() -> None:
    _heartbeat, _kill_switch, _reconciliation, shell = _build_clear_pipeline()
    original = shell.evaluate()
    twin = replace(original)
    assert twin is not original
    assert twin == original
    original_render = format_safety_verdict(original).render()
    twin_render = format_safety_verdict(twin).render()
    assert twin_render == original_render

    _hb2, _ks2, _rc2, shell_b = _make_blocked_pipeline_multi()
    blocked_original = shell_b.evaluate()
    blocked_twin = replace(blocked_original)
    assert blocked_twin is not blocked_original
    assert blocked_twin == blocked_original
    blocked_original_render = format_safety_verdict(blocked_original).render()
    blocked_twin_render = format_safety_verdict(blocked_twin).render()
    assert blocked_twin_render == blocked_original_render


# ---------------------------------------------------------------------------
# Invariant 6 — P3 fakes non-perturbation under repeated rendering
# ---------------------------------------------------------------------------


def test_repeated_rendering_does_not_perturb_p3_fakes_on_clear_path() -> None:
    heartbeat, kill_switch, _reconciliation, shell = _build_clear_pipeline()
    verdict = shell.evaluate()
    operator_status_before = heartbeat.status("operator")
    kill_switch_before = _kill_switch_snapshot(kill_switch)
    for _ in range(_REPEAT_COUNT):
        format_safety_verdict(verdict)
    operator_status_after = heartbeat.status("operator")
    kill_switch_after = _kill_switch_snapshot(kill_switch)
    assert operator_status_before == operator_status_after
    assert kill_switch_before == kill_switch_after


def test_repeated_rendering_does_not_perturb_p3_fakes_on_blocked_paths() -> None:
    builders = (
        _make_blocked_pipeline_heartbeat_stale,
        _make_blocked_pipeline_kill_switch_tripped,
        _make_blocked_pipeline_reconciliation_failed,
        _make_blocked_pipeline_reconciliation_unavailable,
        _make_blocked_pipeline_reconciliation_warning,
        _make_blocked_pipeline_multi,
    )
    for builder in builders:
        heartbeat, kill_switch, _reconciliation, shell = builder()
        verdict = shell.evaluate()
        assert verdict.clear is False, (
            f"builder {builder.__name__} produced a clear verdict; expected blocked"
        )
        operator_status_before = heartbeat.status("operator")
        kill_switch_before = _kill_switch_snapshot(kill_switch)
        for _ in range(_REPEAT_COUNT):
            format_safety_verdict(verdict)
        operator_status_after = heartbeat.status("operator")
        kill_switch_after = _kill_switch_snapshot(kill_switch)
        assert operator_status_before == operator_status_after, (
            f"builder {builder.__name__} mutated heartbeat status during rendering"
        )
        assert kill_switch_before == kill_switch_after, (
            f"builder {builder.__name__} mutated kill switch during rendering"
        )


def test_repeated_rendering_preserves_staged_reconciliation_outcome() -> None:
    """Second staged outcome must come back unchanged on the next evaluate after rendering.

    Reconciliation outcomes are popped from the fake's queue by
    ``shell.evaluate()``; this test stages a second CLEAN outcome
    after the initial evaluate, renders the verdict N times, then
    calls ``evaluate()`` again and asserts the second outcome is the
    one returned — proving that ``format_safety_verdict`` does not
    secretly pop, peek-and-skip, or otherwise perturb the
    reconciliation queue.
    """
    _heartbeat, _kill_switch, reconciliation, shell = _build_clear_pipeline()
    verdict = shell.evaluate()
    assert verdict.reconciliation_status is ReconciliationStatus.CLEAN
    reconciliation.enqueue(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"p5-07-scenario": "second-staged"},
    )
    for _ in range(_REPEAT_COUNT):
        format_safety_verdict(verdict)
    verdict_second = shell.evaluate()
    assert verdict_second.reconciliation_status is ReconciliationStatus.CLEAN
    assert verdict_second.clear is True


# ---------------------------------------------------------------------------
# Invariant 7 — Safety surface non-perturbation under repeated rendering
# ---------------------------------------------------------------------------


def test_repeated_rendering_does_not_mutate_verdict_or_shell() -> None:
    _heartbeat, _kill_switch, reconciliation, shell = _build_clear_pipeline()
    # Stage a second CLEAN outcome so the post-rendering shell.evaluate()
    # has a queued outcome to consume (the first was consumed by the
    # initial evaluate below).
    reconciliation.enqueue(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"p5-07-scenario": "verdict-snapshot-second"},
    )
    verdict = shell.evaluate()
    snapshot_before = _verdict_snapshot(verdict)
    for _ in range(_REPEAT_COUNT):
        format_safety_verdict(verdict)
    snapshot_after = _verdict_snapshot(verdict)
    assert snapshot_before == snapshot_after
    # The shell remains usable and produces an equal verdict on re-evaluation.
    verdict_again = shell.evaluate()
    assert verdict_again == verdict
    assert verdict_again.clear is True


def test_repeated_rendering_does_not_mutate_simulation_boundary_lane() -> None:
    _heartbeat, _kill_switch, _reconciliation, shell = _build_clear_pipeline()
    verdict = shell.evaluate()
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    lane_before = boundary.lane
    for _ in range(_REPEAT_COUNT):
        format_safety_verdict(verdict)
    assert boundary.lane is lane_before
    assert boundary.lane is SimulationLane.LOCAL_ONLY


# ---------------------------------------------------------------------------
# Invariant 8 — Simulation surface non-perturbation under repeated rendering
# ---------------------------------------------------------------------------


def test_repeated_rendering_does_not_mutate_intents_and_preserves_propose_behavior_clear() -> None:
    _heartbeat, _kill_switch, _reconciliation, shell = _build_clear_pipeline()
    verdict = shell.evaluate()
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    order = _market_order()
    placeholder_before = _placeholder_snapshot(placeholder)
    order_before = _order_snapshot(order)
    for _ in range(_REPEAT_COUNT):
        format_safety_verdict(verdict)
    placeholder_after = _placeholder_snapshot(placeholder)
    order_after = _order_snapshot(order)
    assert placeholder_before == placeholder_after
    assert order_before == order_after
    # Boundary still accepts by identity on the clear path after rendering.
    assert boundary.propose(intent=placeholder, verdict=verdict) is placeholder
    assert boundary.propose_order(order_intent=order, verdict=verdict) is order


def test_repeated_rendering_preserves_propose_blocked_behavior_across_codes() -> None:
    builders = (
        (_make_blocked_pipeline_heartbeat_stale, BLOCKER_HEARTBEAT_STALE),
        (_make_blocked_pipeline_kill_switch_tripped, BLOCKER_KILL_SWITCH_TRIPPED),
        (_make_blocked_pipeline_reconciliation_failed, BLOCKER_RECONCILIATION_FAILED),
        (
            _make_blocked_pipeline_reconciliation_unavailable,
            BLOCKER_RECONCILIATION_UNAVAILABLE,
        ),
        (_make_blocked_pipeline_reconciliation_warning, BLOCKER_RECONCILIATION_WARNING),
    )
    for builder, blocker_code in builders:
        _heartbeat, _kill_switch, _reconciliation, shell = builder()
        verdict = shell.evaluate()
        boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
        placeholder = _placeholder_intent()
        order = _limit_order()
        for _ in range(_REPEAT_COUNT):
            format_safety_verdict(verdict)
        _expect_boundary_error(
            lambda b=boundary, p=placeholder, v=verdict: b.propose(intent=p, verdict=v),
            match=blocker_code,
        )
        _expect_boundary_error(
            lambda b=boundary, o=order, v=verdict: b.propose_order(order_intent=o, verdict=v),
            match=blocker_code,
        )


# ---------------------------------------------------------------------------
# Invariant 9 — Render-then-propose / propose-then-render order independence
# ---------------------------------------------------------------------------


def test_render_then_propose_and_propose_then_render_produce_same_view() -> None:
    _heartbeat, _kill_switch, _reconciliation, shell = _build_clear_pipeline()
    verdict = shell.evaluate()
    boundary_a = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder_a = _placeholder_intent(intent_id="intent-order-a")
    order_a = _market_order(intent_id="order-order-a")
    boundary_b = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder_b = _placeholder_intent(intent_id="intent-order-b")
    order_b = _market_order(intent_id="order-order-b")
    # Order A: render, then propose, then render.
    view_a_first = format_safety_verdict(verdict)
    assert boundary_a.propose(intent=placeholder_a, verdict=verdict) is placeholder_a
    assert boundary_a.propose_order(order_intent=order_a, verdict=verdict) is order_a
    view_a_second = format_safety_verdict(verdict)
    # Order B: propose, then render, then propose.
    assert boundary_b.propose(intent=placeholder_b, verdict=verdict) is placeholder_b
    view_b_first = format_safety_verdict(verdict)
    assert boundary_b.propose_order(order_intent=order_b, verdict=verdict) is order_b
    view_b_second = format_safety_verdict(verdict)
    # All four views byte-identical.
    rendered = {
        view_a_first.render(),
        view_a_second.render(),
        view_b_first.render(),
        view_b_second.render(),
    }
    assert len(rendered) == 1


# ---------------------------------------------------------------------------
# Invariant 10 — Interleaved render / propose idempotence
# ---------------------------------------------------------------------------


def test_interleaved_render_and_propose_preserves_view_and_behavior() -> None:
    _heartbeat, _kill_switch, _reconciliation, shell = _build_clear_pipeline()
    verdict = shell.evaluate()
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    order = _market_order()
    baseline_render = format_safety_verdict(verdict).render()
    for _ in range(_REPEAT_COUNT):
        assert format_safety_verdict(verdict).render() == baseline_render
        assert boundary.propose(intent=placeholder, verdict=verdict) is placeholder
        assert format_safety_verdict(verdict).render() == baseline_render
        assert boundary.propose_order(order_intent=order, verdict=verdict) is order
        assert format_safety_verdict(verdict).render() == baseline_render
    # Verdict and intents still intact at the end.
    assert verdict.clear is True
    assert _placeholder_snapshot(placeholder) == (
        SimulationLane.LOCAL_ONLY,
        "intent-p5-07-X",
        _FIXED_CLOCK_Z,
    )
    assert _order_snapshot(order) == (
        SimulationLane.LOCAL_ONLY,
        "order-p5-07-A",
        _FIXED_CLOCK_Z,
        "SIM-P5-07-A",
        SimulatedOrderSide.BUY,
        10,
        SimulatedOrderType.MARKET,
        None,
    )


def test_interleaved_render_and_propose_preserves_blocker_message_on_blocked_path() -> None:
    _heartbeat, _kill_switch, _reconciliation, shell = _make_blocked_pipeline_multi()
    verdict = shell.evaluate()
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    order = _limit_order()
    baseline_render = format_safety_verdict(verdict).render()
    baseline_propose_err = _expect_boundary_error(
        lambda: boundary.propose(intent=placeholder, verdict=verdict),
        match=BLOCKER_HEARTBEAT_STALE,
    )
    baseline_propose_msg = str(baseline_propose_err)
    baseline_propose_order_err = _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=order, verdict=verdict),
        match=BLOCKER_HEARTBEAT_STALE,
    )
    baseline_propose_order_msg = str(baseline_propose_order_err)
    for _ in range(_REPEAT_COUNT):
        assert format_safety_verdict(verdict).render() == baseline_render
        propose_err = _expect_boundary_error(
            lambda: boundary.propose(intent=placeholder, verdict=verdict),
            match=BLOCKER_HEARTBEAT_STALE,
        )
        assert str(propose_err) == baseline_propose_msg
        propose_order_err = _expect_boundary_error(
            lambda: boundary.propose_order(order_intent=order, verdict=verdict),
            match=BLOCKER_HEARTBEAT_STALE,
        )
        assert str(propose_order_err) == baseline_propose_order_msg
        assert format_safety_verdict(verdict).render() == baseline_render


# ---------------------------------------------------------------------------
# Invariant 11 — Type validation determinism
# ---------------------------------------------------------------------------


def test_format_safety_verdict_type_error_is_deterministic_across_repeated_calls() -> None:
    bad_inputs: tuple[object, ...] = (
        "not-a-verdict",
        42,
        None,
        ("clear", ()),
        {"clear": True},
    )
    for bad in bad_inputs:
        messages: list[str] = []
        for _ in range(_REPEAT_COUNT):
            raised: Exception | None = None
            try:
                format_safety_verdict(bad)  # type: ignore[arg-type]
            except TypeError as exc:
                raised = exc
            assert isinstance(raised, TypeError), (
                f"format_safety_verdict({bad!r}) did not raise TypeError; got {raised!r}"
            )
            messages.append(str(raised))
        assert len(set(messages)) == 1, (
            f"format_safety_verdict({bad!r}) produced non-deterministic TypeError messages: "
            f"{set(messages)!r}"
        )


# ---------------------------------------------------------------------------
# Invariant 12 — Inertness self-check: imports are bounded
# ---------------------------------------------------------------------------


_AUTHORIZED_IMPORT_PREFIXES: tuple[str, ...] = (
    "__future__",
    "ast",
    "dataclasses",
    "datetime",
    "pathlib",
    "gmc_rebuild.heartbeat",
    "gmc_rebuild.kill_switch",
    "gmc_rebuild.reconciliation",
    "gmc_rebuild.risk",
    "gmc_rebuild.runtime",
    "gmc_rebuild.simulation",
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
    }
)


def _collect_imported_modules() -> set[str]:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
            imported.add(node.module)
    return imported


def test_operator_view_determinism_module_has_no_forbidden_runtime_imports() -> None:
    imported = _collect_imported_modules()
    roots = {name.split(".", 1)[0] for name in imported}
    overlap = roots & _FORBIDDEN_IMPORT_ROOTS
    assert overlap == set(), f"forbidden import roots present in test module: {sorted(overlap)!r}"


def test_operator_view_determinism_module_only_imports_from_authorized_prefixes() -> None:
    imported = _collect_imported_modules()
    unauthorized: list[str] = []
    for name in sorted(imported):
        if not any(
            name == prefix or name.startswith(prefix + ".")
            for prefix in _AUTHORIZED_IMPORT_PREFIXES
        ):
            unauthorized.append(name)
    assert unauthorized == [], f"unauthorized imports in test module: {unauthorized!r}"
