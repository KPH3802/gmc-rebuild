"""P6-04 Direction A simulated order intent extension tests.

Deterministic, pytest-only tests for the P6-04 Direction A additions to
the merged P5-01 / P5-02 simulation surface
(``governance/authorizations/2026-05-21_p6-04.md``):

- a closed :class:`SimulatedOrderTimeInForce` ``StrEnum`` carried as a
  ninth :class:`SimulatedOrderIntent` field defaulting to
  :attr:`SimulatedOrderTimeInForce.DAY`; and
- a deterministic, pure :func:`derive_simulated_order_intent_id`
  identity helper.

The tests prove:

- the time-in-force enum is closed (exactly four members), is a
  ``StrEnum`` (values equal member-name-derived strings), and is a
  ``str`` subclass;
- the deterministic identity helper is deterministic / idempotent
  (identical inputs return the byte-for-byte identical id across
  repeated calls), is sensitive to every content field (distinct inputs
  return distinct ids), produces a non-empty whitespace-free id usable
  as a :attr:`SimulatedOrderIntent.intent_id`, and validates its inputs
  with the same per-field discipline as :class:`SimulatedOrderIntent`;
- :class:`SimulatedOrderIntent` remains frozen / slotted / immutable
  with the new ninth field, defaults ``time_in_force`` to ``DAY`` when
  omitted, and rejects a non-:class:`SimulatedOrderTimeInForce`
  ``time_in_force``;
- the simulation boundary remains local-only: ``propose_order``
  identity-returns a time-in-force-bearing intent on a clear verdict,
  rejects a lane mismatch, and rejects a blocked verdict with the
  blocker tuple, exactly as for the merged P5-02 shape.

Tests avoid ``pytest.raises`` and fixture-typed parameters so the mypy
strict pre-commit hook does not need a pytest-stub dependency, matching
the convention of the existing ``tests/simulation/`` modules. Source
inertness for the underlying file is already covered by the existing
``tests/simulation/test_simulation_boundary.py`` checks, which glob
every ``*.py`` under ``src/gmc_rebuild/simulation/`` and therefore
automatically cover the P6-04 additions in ``_boundary.py``.
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from types import MappingProxyType

from gmc_rebuild.risk import (
    HeartbeatStatus,
    KillSwitchState,
    ReconciliationStatus,
)
from gmc_rebuild.runtime import (
    BLOCKER_HEARTBEAT_STALE,
    BLOCKER_KILL_SWITCH_TRIPPED,
    SafetyVerdict,
)
from gmc_rebuild.simulation import (
    SimulatedOrderIntent,
    SimulatedOrderSide,
    SimulatedOrderTimeInForce,
    SimulatedOrderType,
    SimulationBoundary,
    SimulationBoundaryError,
    SimulationLane,
    derive_simulated_order_intent_id,
)

_FIXED_CLOCK = datetime(2026, 5, 21, 14, 0, 0, tzinfo=UTC)
_FIXED_CLOCK_Z = "2026-05-21T14:00:00Z"


def _expect_boundary_error(call: object, match: str) -> None:
    raised: Exception | None = None
    try:
        call()  # type: ignore[operator]
    except SimulationBoundaryError as exc:
        raised = exc
    assert isinstance(raised, SimulationBoundaryError), (
        f"expected SimulationBoundaryError matching {match!r}, got {raised!r}"
    )
    assert match in str(raised), f"error {str(raised)!r} did not contain {match!r}"


def _clear_verdict() -> SafetyVerdict:
    return SafetyVerdict(
        clear=True,
        blockers=(),
        heartbeat_statuses=MappingProxyType({"operator": HeartbeatStatus.FRESH}),
        kill_switch_state=KillSwitchState.ARMED,
        reconciliation_status=ReconciliationStatus.CLEAN,
        observed_at=_FIXED_CLOCK_Z,
    )


def _blocked_verdict() -> SafetyVerdict:
    return SafetyVerdict(
        clear=False,
        blockers=(BLOCKER_HEARTBEAT_STALE, BLOCKER_KILL_SWITCH_TRIPPED),
        heartbeat_statuses=MappingProxyType({"operator": HeartbeatStatus.STALE}),
        kill_switch_state=KillSwitchState.TRIPPED,
        reconciliation_status=ReconciliationStatus.CLEAN,
        observed_at=_FIXED_CLOCK_Z,
    )


def _derive(
    *,
    lane: SimulationLane = SimulationLane.LOCAL_ONLY,
    symbol: str = "SIM-P6-04",
    side: SimulatedOrderSide = SimulatedOrderSide.BUY,
    quantity: int = 10,
    order_type: SimulatedOrderType = SimulatedOrderType.MARKET,
    limit_price: float | None = None,
    time_in_force: SimulatedOrderTimeInForce = SimulatedOrderTimeInForce.DAY,
    created_at: str = _FIXED_CLOCK_Z,
) -> str:
    """Typed wrapper over :func:`derive_simulated_order_intent_id`.

    Keeps the per-test call sites mypy-strict-clean (concrete argument
    types) while letting each test override exactly one content field.
    """
    return derive_simulated_order_intent_id(
        lane=lane,
        symbol=symbol,
        side=side,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit_price,
        time_in_force=time_in_force,
        created_at=created_at,
    )


def _order(**overrides: object) -> SimulatedOrderIntent:
    kwargs: dict[str, object] = {
        "lane": SimulationLane.LOCAL_ONLY,
        "intent_id": "order-p6-04-A",
        "created_at": _FIXED_CLOCK_Z,
        "symbol": "SIM-P6-04",
        "side": SimulatedOrderSide.BUY,
        "quantity": 10,
        "order_type": SimulatedOrderType.MARKET,
        "limit_price": None,
    }
    kwargs.update(overrides)
    return SimulatedOrderIntent(**kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# SimulatedOrderTimeInForce closed enumeration
# ---------------------------------------------------------------------------


def test_time_in_force_is_closed_four_member_strenum() -> None:
    assert set(SimulatedOrderTimeInForce) == {
        SimulatedOrderTimeInForce.DAY,
        SimulatedOrderTimeInForce.GOOD_TILL_CANCEL,
        SimulatedOrderTimeInForce.IMMEDIATE_OR_CANCEL,
        SimulatedOrderTimeInForce.FILL_OR_KILL,
    }


def test_time_in_force_member_values_are_stable() -> None:
    assert SimulatedOrderTimeInForce.DAY.value == "day"
    assert SimulatedOrderTimeInForce.GOOD_TILL_CANCEL.value == "good_till_cancel"
    assert SimulatedOrderTimeInForce.IMMEDIATE_OR_CANCEL.value == "immediate_or_cancel"
    assert SimulatedOrderTimeInForce.FILL_OR_KILL.value == "fill_or_kill"


def test_time_in_force_is_a_str_subclass() -> None:
    assert isinstance(SimulatedOrderTimeInForce.DAY, str)


def test_time_in_force_has_exactly_four_members() -> None:
    assert len(tuple(SimulatedOrderTimeInForce)) == 4


# ---------------------------------------------------------------------------
# Deterministic identity helper
# ---------------------------------------------------------------------------


def test_identity_is_deterministic_across_repeated_calls() -> None:
    ids = [_derive() for _ in range(5)]
    for value in ids[1:]:
        assert value == ids[0]


def test_identity_is_non_empty_whitespace_free_and_prefixed() -> None:
    value = _derive()
    assert value
    assert not any(ch.isspace() for ch in value)
    assert value.startswith("simoi-")


def test_identity_is_usable_as_simulated_order_intent_id() -> None:
    value = _derive()
    order = _order(intent_id=value)
    assert order.intent_id == value


def test_identity_differs_when_any_content_field_differs() -> None:
    base = _derive()
    variants = (
        _derive(symbol="SIM-OTHER"),
        _derive(side=SimulatedOrderSide.SELL),
        _derive(quantity=11),
        _derive(time_in_force=SimulatedOrderTimeInForce.GOOD_TILL_CANCEL),
        _derive(created_at="2026-05-21T14:00:01Z"),
        _derive(order_type=SimulatedOrderType.LIMIT, limit_price=42.5),
    )
    for variant in variants:
        assert variant != base


def test_identity_distinguishes_limit_price_values() -> None:
    a = _derive(order_type=SimulatedOrderType.LIMIT, limit_price=42.5)
    b = _derive(order_type=SimulatedOrderType.LIMIT, limit_price=42.6)
    assert a != b


def test_identity_rejects_non_lane() -> None:
    _expect_boundary_error(
        lambda: derive_simulated_order_intent_id(
            lane="local_only",  # type: ignore[arg-type]
            symbol="SIM-P6-04",
            side=SimulatedOrderSide.BUY,
            quantity=10,
            order_type=SimulatedOrderType.MARKET,
            limit_price=None,
            time_in_force=SimulatedOrderTimeInForce.DAY,
            created_at=_FIXED_CLOCK_Z,
        ),
        "lane",
    )


def test_identity_rejects_bool_quantity() -> None:
    _expect_boundary_error(
        lambda: derive_simulated_order_intent_id(
            lane=SimulationLane.LOCAL_ONLY,
            symbol="SIM-P6-04",
            side=SimulatedOrderSide.BUY,
            quantity=True,
            order_type=SimulatedOrderType.MARKET,
            limit_price=None,
            time_in_force=SimulatedOrderTimeInForce.DAY,
            created_at=_FIXED_CLOCK_Z,
        ),
        "quantity",
    )


def test_identity_rejects_non_time_in_force() -> None:
    _expect_boundary_error(
        lambda: derive_simulated_order_intent_id(
            lane=SimulationLane.LOCAL_ONLY,
            symbol="SIM-P6-04",
            side=SimulatedOrderSide.BUY,
            quantity=10,
            order_type=SimulatedOrderType.MARKET,
            limit_price=None,
            time_in_force="day",  # type: ignore[arg-type]
            created_at=_FIXED_CLOCK_Z,
        ),
        "time_in_force",
    )


def test_identity_rejects_limit_price_on_market_order() -> None:
    _expect_boundary_error(
        lambda: _derive(order_type=SimulatedOrderType.MARKET, limit_price=10.0),
        "limit_price",
    )


def test_identity_rejects_naive_created_at_without_z_suffix() -> None:
    _expect_boundary_error(
        lambda: _derive(created_at="2026-05-21T14:00:00"),
        "created_at",
    )


# ---------------------------------------------------------------------------
# Nine-field shape, default, immutability, validation
# ---------------------------------------------------------------------------


def test_order_intent_has_nine_fields_in_canonical_order() -> None:
    field_names = tuple(f.name for f in dataclasses.fields(SimulatedOrderIntent))
    assert field_names == (
        "lane",
        "intent_id",
        "created_at",
        "symbol",
        "side",
        "quantity",
        "order_type",
        "limit_price",
        "time_in_force",
    )


def test_time_in_force_defaults_to_day_when_omitted() -> None:
    order = _order()
    assert order.time_in_force is SimulatedOrderTimeInForce.DAY


def test_time_in_force_round_trips_each_member() -> None:
    for member in SimulatedOrderTimeInForce:
        order = _order(time_in_force=member)
        assert order.time_in_force is member


def test_order_intent_is_frozen_against_time_in_force_assignment() -> None:
    order = _order()
    raised: Exception | None = None
    try:
        order.time_in_force = SimulatedOrderTimeInForce.FILL_OR_KILL  # type: ignore[misc]
    except dataclasses.FrozenInstanceError as exc:
        raised = exc
    assert isinstance(raised, dataclasses.FrozenInstanceError)


def test_order_intent_uses_slots_and_has_no_dict_with_new_field() -> None:
    order = _order(time_in_force=SimulatedOrderTimeInForce.IMMEDIATE_OR_CANCEL)
    assert hasattr(SimulatedOrderIntent, "__slots__")
    assert "time_in_force" in tuple(SimulatedOrderIntent.__slots__)
    assert not hasattr(order, "__dict__")


def test_order_intent_rejects_non_time_in_force() -> None:
    _expect_boundary_error(
        lambda: _order(time_in_force="day"),
        "time_in_force",
    )


def test_build_classmethod_accepts_time_in_force() -> None:
    order = SimulatedOrderIntent.build(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="order-build",
        created_at=_FIXED_CLOCK,
        symbol="SIM-P6-04",
        side=SimulatedOrderSide.SELL,
        quantity=5,
        order_type=SimulatedOrderType.LIMIT,
        limit_price=12.5,
        time_in_force=SimulatedOrderTimeInForce.FILL_OR_KILL,
    )
    assert order.time_in_force is SimulatedOrderTimeInForce.FILL_OR_KILL
    assert order.created_at == _FIXED_CLOCK_Z


def test_build_classmethod_defaults_time_in_force_to_day() -> None:
    order = SimulatedOrderIntent.build(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="order-build-default",
        created_at=_FIXED_CLOCK,
        symbol="SIM-P6-04",
        side=SimulatedOrderSide.BUY,
        quantity=5,
        order_type=SimulatedOrderType.MARKET,
    )
    assert order.time_in_force is SimulatedOrderTimeInForce.DAY


def test_two_orders_with_same_fields_including_tif_are_equal_and_hash_equal() -> None:
    a = _order(time_in_force=SimulatedOrderTimeInForce.GOOD_TILL_CANCEL)
    b = _order(time_in_force=SimulatedOrderTimeInForce.GOOD_TILL_CANCEL)
    assert a == b
    assert hash(a) == hash(b)


# ---------------------------------------------------------------------------
# Boundary remains local-only with the time-in-force-bearing intent
# ---------------------------------------------------------------------------


def test_propose_order_identity_returns_tif_bearing_intent_on_clear_verdict() -> None:
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    order = _order(time_in_force=SimulatedOrderTimeInForce.GOOD_TILL_CANCEL)
    result = boundary.propose_order(order_intent=order, verdict=_clear_verdict())
    assert result is order


def test_propose_order_rejects_blocked_verdict_for_tif_bearing_intent() -> None:
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    order = _order(time_in_force=SimulatedOrderTimeInForce.IMMEDIATE_OR_CANCEL)
    _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=order, verdict=_blocked_verdict()),
        "blocked by safety verdict",
    )


def test_boundary_lane_is_closed_at_local_only() -> None:
    assert set(SimulationLane) == {SimulationLane.LOCAL_ONLY}


def test_propose_order_does_not_mutate_tif_bearing_intent() -> None:
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    order = _order(time_in_force=SimulatedOrderTimeInForce.FILL_OR_KILL)
    before = (
        order.lane,
        order.intent_id,
        order.created_at,
        order.symbol,
        order.side,
        order.quantity,
        order.order_type,
        order.limit_price,
        order.time_in_force,
    )
    for _ in range(3):
        boundary.propose_order(order_intent=order, verdict=_clear_verdict())
    after = (
        order.lane,
        order.intent_id,
        order.created_at,
        order.symbol,
        order.side,
        order.quantity,
        order.order_type,
        order.limit_price,
        order.time_in_force,
    )
    assert before == after


# ---------------------------------------------------------------------------
# Root package does not re-export the new surface
# ---------------------------------------------------------------------------


def test_root_package_does_not_re_export_p6_04_surface() -> None:
    import gmc_rebuild

    for name in ("SimulatedOrderTimeInForce", "derive_simulated_order_intent_id"):
        assert not hasattr(gmc_rebuild, name), (
            f"gmc_rebuild unexpectedly re-exports {name!r}; the P6-04 surface "
            f"must be reachable only via gmc_rebuild.simulation."
        )
