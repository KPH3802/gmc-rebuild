"""P5-02 simulated order intent model tests.

Verifies that the order-shaped data fields added to
``gmc_rebuild.simulation`` by P5-02
(``governance/authorizations/2026-05-17_p5-02.md``):

- declare exactly the authorized closed enumerations
  (``SimulatedOrderSide`` is ``BUY`` / ``SELL`` only;
  ``SimulatedOrderType`` is ``MARKET`` / ``LIMIT`` only);
- treat :class:`SimulatedOrderIntent` as a frozen, slotted, immutable
  record with strict per-field validation;
- enforce ADR-004 ``Z``-suffixed UTC timestamps via the
  ``build()`` classmethod and reject naive datetimes;
- reject all forbidden order shapes (``bool`` quantity, fractional
  quantity, non-positive quantity, missing limit for ``LIMIT``,
  non-``None`` limit for ``MARKET``, non-positive / non-finite limit,
  empty / whitespace ``symbol`` and ``intent_id``);
- carry **no** venue / broker / account / routing / time-in-force /
  post-only / IOC / FOK / credential / persistence-handle field
  (structural assertion: the dataclass fields are exactly the eight
  authorized ones);
- compose the safety-gate of :class:`SimulationBoundary`
  unchanged: :meth:`SimulationBoundary.propose_order` returns the
  intent by identity on a clear verdict, raises with the verdict's
  blockers on a blocked verdict, rejects a lane mismatch, and does
  not mutate the intent or the verdict.

Tests avoid ``pytest.raises`` and fixture-typed parameters so the
mypy strict pre-commit hook does not need a pytest-stub dependency.
Inertness for the underlying source file is already covered by the
existing ``tests/simulation/test_simulation_boundary.py`` checks
(``test_simulation_package_has_no_main_entry_point``,
``test_simulation_package_has_no_forbidden_runtime_imports``,
``test_simulation_package_has_no_sleep_or_env_or_io``,
``test_simulation_package_does_not_modify_runtime_or_risk_subpackages``),
which glob every ``*.py`` file under ``src/gmc_rebuild/simulation/``
and therefore automatically cover the P5-02 additions in
``_boundary.py``.
"""

from __future__ import annotations

import dataclasses
import math
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any

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
    SimulatedOrderType,
    SimulationBoundary,
    SimulationBoundaryError,
    SimulationLane,
)

_FIXED_CLOCK = datetime(2026, 5, 17, 14, 0, 0, tzinfo=UTC)
_FIXED_CLOCK_Z = "2026-05-17T14:00:00Z"


def _expect_boundary_error(call: object, match: str) -> None:
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


def _market_order(*, intent_id: str = "order-001") -> SimulatedOrderIntent:
    return SimulatedOrderIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_FIXED_CLOCK_Z,
        symbol="SIM-AAA",
        side=SimulatedOrderSide.BUY,
        quantity=100,
        order_type=SimulatedOrderType.MARKET,
        limit_price=None,
    )


def _limit_order(*, intent_id: str = "order-002") -> SimulatedOrderIntent:
    return SimulatedOrderIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_FIXED_CLOCK_Z,
        symbol="SIM-BBB",
        side=SimulatedOrderSide.SELL,
        quantity=50,
        order_type=SimulatedOrderType.LIMIT,
        limit_price=42.5,
    )


# ---------------------------------------------------------------------------
# Closed authorized enumerations (P5-02 tripwires)
# ---------------------------------------------------------------------------


def test_simulated_order_side_has_only_authorized_values() -> None:
    """Only ``BUY`` and ``SELL`` are authorized by P5-02.

    Adding ``SELL_SHORT``, ``BUY_TO_COVER``, or any other side
    without separate written authorization is a phase-expanding
    change and must be rejected at review. This test fails on any
    unauthorized addition.
    """
    members = {side.value for side in SimulatedOrderSide}
    assert members == {"buy", "sell"}, f"unexpected SimulatedOrderSide members: {members}"


def test_simulated_order_side_is_strenum() -> None:
    assert SimulatedOrderSide.BUY.value == "buy"
    assert SimulatedOrderSide.SELL.value == "sell"
    assert isinstance(SimulatedOrderSide.BUY, str)
    assert str(SimulatedOrderSide.BUY) == "buy"


def test_simulated_order_type_has_only_authorized_values() -> None:
    """Only ``MARKET`` and ``LIMIT`` are authorized by P5-02.

    Adding ``STOP``, ``STOP_LIMIT``, ``MARKET_ON_CLOSE``,
    ``LIMIT_ON_OPEN``, ``TRAILING_STOP``, or any other order type
    without separate written authorization is a phase-expanding
    change and must be rejected at review. This test fails on any
    unauthorized addition.
    """
    members = {kind.value for kind in SimulatedOrderType}
    assert members == {"market", "limit"}, f"unexpected SimulatedOrderType members: {members}"


def test_simulated_order_type_is_strenum() -> None:
    assert SimulatedOrderType.MARKET.value == "market"
    assert SimulatedOrderType.LIMIT.value == "limit"
    assert isinstance(SimulatedOrderType.MARKET, str)
    assert str(SimulatedOrderType.LIMIT) == "limit"


# ---------------------------------------------------------------------------
# SimulatedOrderIntent: shape, immutability, and no forbidden fields
# ---------------------------------------------------------------------------


def test_simulated_order_intent_dataclass_fields_are_exactly_the_authorized_set() -> None:
    """The dataclass must declare exactly the eight authorized fields.

    This is a structural tripwire: any addition of a venue, broker,
    account, routing instruction, time-in-force qualifier, post-only
    / IOC / FOK modifier, route-allow / route-deny list, broker
    credential, API key, persistence handle, or any other field
    without separate written authorization will fail this test.
    """
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
    ), f"unexpected SimulatedOrderIntent fields: {field_names}"


def test_simulated_order_intent_uses_slots() -> None:
    intent = _market_order()
    assert not hasattr(intent, "__dict__")


def test_simulated_order_intent_is_frozen() -> None:
    intent = _market_order()
    raised: Exception | None = None
    try:
        intent.quantity = 200  # type: ignore[misc]
    except Exception as exc:
        raised = exc
    assert raised is not None, "frozen SimulatedOrderIntent must reject attribute mutation"


def test_simulated_order_intent_equality_is_structural() -> None:
    a = _market_order(intent_id="dup")
    b = _market_order(intent_id="dup")
    assert a == b
    assert a is not b


# ---------------------------------------------------------------------------
# build() classmethod (datetime → ADR-004 Z-suffixed string)
# ---------------------------------------------------------------------------


def test_build_converts_datetime_to_z_string_for_market_order() -> None:
    intent = SimulatedOrderIntent.build(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="order-build-market",
        created_at=_FIXED_CLOCK,
        symbol="SIM-CCC",
        side=SimulatedOrderSide.BUY,
        quantity=10,
        order_type=SimulatedOrderType.MARKET,
    )
    assert intent.created_at == _FIXED_CLOCK_Z
    assert intent.limit_price is None  # default when omitted for MARKET


def test_build_converts_datetime_to_z_string_for_limit_order() -> None:
    intent = SimulatedOrderIntent.build(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="order-build-limit",
        created_at=_FIXED_CLOCK,
        symbol="SIM-DDD",
        side=SimulatedOrderSide.SELL,
        quantity=25,
        order_type=SimulatedOrderType.LIMIT,
        limit_price=12.34,
    )
    assert intent.created_at == _FIXED_CLOCK_Z
    assert intent.limit_price == 12.34


# ---------------------------------------------------------------------------
# Per-field validation
# ---------------------------------------------------------------------------


def test_rejects_non_lane() -> None:
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane="local_only",  # type: ignore[arg-type]
            intent_id="bad-lane",
            created_at=_FIXED_CLOCK_Z,
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=1,
            order_type=SimulatedOrderType.MARKET,
            limit_price=None,
        ),
        "lane must be a SimulationLane",
    )


def test_rejects_empty_or_whitespace_intent_id() -> None:
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="",
            created_at=_FIXED_CLOCK_Z,
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=1,
            order_type=SimulatedOrderType.MARKET,
            limit_price=None,
        ),
        "intent_id must be a non-empty str",
    )
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="bad id",
            created_at=_FIXED_CLOCK_Z,
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=1,
            order_type=SimulatedOrderType.MARKET,
            limit_price=None,
        ),
        "intent_id must not contain whitespace",
    )


def test_rejects_non_z_suffixed_created_at() -> None:
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="bad-created-at",
            created_at="2026-05-17T14:00:00+00:00",
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=1,
            order_type=SimulatedOrderType.MARKET,
            limit_price=None,
        ),
        "ADR-004 Z-suffixed UTC string",
    )
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="empty-created-at",
            created_at="",
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=1,
            order_type=SimulatedOrderType.MARKET,
            limit_price=None,
        ),
        "created_at must be a non-empty str",
    )


def test_rejects_empty_or_whitespace_symbol() -> None:
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="empty-symbol",
            created_at=_FIXED_CLOCK_Z,
            symbol="",
            side=SimulatedOrderSide.BUY,
            quantity=1,
            order_type=SimulatedOrderType.MARKET,
            limit_price=None,
        ),
        "symbol must be a non-empty str",
    )
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="ws-symbol",
            created_at=_FIXED_CLOCK_Z,
            symbol="BAD SYM",
            side=SimulatedOrderSide.BUY,
            quantity=1,
            order_type=SimulatedOrderType.MARKET,
            limit_price=None,
        ),
        "symbol must not contain whitespace",
    )


def test_rejects_non_side_enum() -> None:
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="bad-side",
            created_at=_FIXED_CLOCK_Z,
            symbol="SIM-AAA",
            side="buy",  # type: ignore[arg-type]
            quantity=1,
            order_type=SimulatedOrderType.MARKET,
            limit_price=None,
        ),
        "side must be a SimulatedOrderSide",
    )


def test_rejects_bool_quantity() -> None:
    """``bool`` is a subclass of ``int``; reject explicitly to avoid the True == 1 trap."""
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="bool-qty",
            created_at=_FIXED_CLOCK_Z,
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=True,
            order_type=SimulatedOrderType.MARKET,
            limit_price=None,
        ),
        "quantity must be an int (not bool, not float)",
    )


def test_rejects_float_quantity() -> None:
    """Fractional quantities are not authorized by P5-02."""
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="float-qty",
            created_at=_FIXED_CLOCK_Z,
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=1.5,  # type: ignore[arg-type]
            order_type=SimulatedOrderType.MARKET,
            limit_price=None,
        ),
        "quantity must be an int (not bool, not float)",
    )


def test_rejects_non_positive_quantity() -> None:
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="zero-qty",
            created_at=_FIXED_CLOCK_Z,
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=0,
            order_type=SimulatedOrderType.MARKET,
            limit_price=None,
        ),
        "quantity must be positive",
    )
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="neg-qty",
            created_at=_FIXED_CLOCK_Z,
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=-1,
            order_type=SimulatedOrderType.MARKET,
            limit_price=None,
        ),
        "quantity must be positive",
    )


def test_rejects_non_order_type_enum() -> None:
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="bad-type",
            created_at=_FIXED_CLOCK_Z,
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=1,
            order_type="market",  # type: ignore[arg-type]
            limit_price=None,
        ),
        "order_type must be a SimulatedOrderType",
    )


def test_market_order_rejects_non_none_limit_price() -> None:
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="market-with-price",
            created_at=_FIXED_CLOCK_Z,
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=1,
            order_type=SimulatedOrderType.MARKET,
            limit_price=10.0,
        ),
        "limit_price must be None when order_type is MARKET",
    )


def test_limit_order_rejects_none_limit_price() -> None:
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="limit-none-price",
            created_at=_FIXED_CLOCK_Z,
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=1,
            order_type=SimulatedOrderType.LIMIT,
            limit_price=None,
        ),
        "limit_price must be a float when order_type is LIMIT",
    )


def test_limit_order_rejects_bool_limit_price() -> None:
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="limit-bool-price",
            created_at=_FIXED_CLOCK_Z,
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=1,
            order_type=SimulatedOrderType.LIMIT,
            limit_price=True,
        ),
        "limit_price must be a float when order_type is LIMIT",
    )


def test_limit_order_rejects_int_limit_price() -> None:
    """Limit prices must be ``float``; ``int`` is rejected for type clarity."""
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="limit-int-price",
            created_at=_FIXED_CLOCK_Z,
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=1,
            order_type=SimulatedOrderType.LIMIT,
            limit_price=10,
        ),
        "limit_price must be a float when order_type is LIMIT",
    )


def test_limit_order_rejects_non_positive_price() -> None:
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="limit-zero-price",
            created_at=_FIXED_CLOCK_Z,
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=1,
            order_type=SimulatedOrderType.LIMIT,
            limit_price=0.0,
        ),
        "limit_price must be positive when order_type is LIMIT",
    )
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="limit-neg-price",
            created_at=_FIXED_CLOCK_Z,
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=1,
            order_type=SimulatedOrderType.LIMIT,
            limit_price=-1.0,
        ),
        "limit_price must be positive when order_type is LIMIT",
    )


def test_limit_order_rejects_nan_and_inf_price() -> None:
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="limit-nan-price",
            created_at=_FIXED_CLOCK_Z,
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=1,
            order_type=SimulatedOrderType.LIMIT,
            limit_price=math.nan,
        ),
        "must be a finite number",
    )
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="limit-inf-price",
            created_at=_FIXED_CLOCK_Z,
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=1,
            order_type=SimulatedOrderType.LIMIT,
            limit_price=math.inf,
        ),
        "must be a finite number",
    )
    _expect_boundary_error(
        lambda: SimulatedOrderIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="limit-neg-inf-price",
            created_at=_FIXED_CLOCK_Z,
            symbol="SIM-AAA",
            side=SimulatedOrderSide.BUY,
            quantity=1,
            order_type=SimulatedOrderType.LIMIT,
            limit_price=-math.inf,
        ),
        "must be a finite number",
    )


def test_market_order_constructs_with_valid_inputs() -> None:
    intent = _market_order()
    assert intent.lane is SimulationLane.LOCAL_ONLY
    assert intent.symbol == "SIM-AAA"
    assert intent.side is SimulatedOrderSide.BUY
    assert intent.quantity == 100
    assert intent.order_type is SimulatedOrderType.MARKET
    assert intent.limit_price is None


def test_limit_order_constructs_with_valid_inputs() -> None:
    intent = _limit_order()
    assert intent.order_type is SimulatedOrderType.LIMIT
    assert intent.limit_price == 42.5


# ---------------------------------------------------------------------------
# SimulationBoundary.propose_order: safety gate
# ---------------------------------------------------------------------------


def test_propose_order_returns_intent_by_identity_when_verdict_is_clear() -> None:
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    intent = _market_order()
    result = boundary.propose_order(order_intent=intent, verdict=_clear_verdict())
    assert result is intent  # identity, not copy or wrap


def test_propose_order_is_deterministic_for_equivalent_inputs() -> None:
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    a = _limit_order(intent_id="det-order")
    b = _limit_order(intent_id="det-order")
    assert a == b
    res_a = boundary.propose_order(order_intent=a, verdict=_clear_verdict())
    res_b = boundary.propose_order(order_intent=b, verdict=_clear_verdict())
    assert res_a == res_b
    assert boundary.propose_order(order_intent=a, verdict=_clear_verdict()) is a


def test_propose_order_rejects_non_order_intent() -> None:
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    bogus: Any = object()
    _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=bogus, verdict=_clear_verdict()),
        "order_intent must be a SimulatedOrderIntent",
    )


def test_propose_order_rejects_non_verdict() -> None:
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    intent = _market_order()
    bogus: Any = object()
    _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=intent, verdict=bogus),
        "verdict must be a SafetyVerdict",
    )


def test_propose_order_blocks_when_verdict_is_not_clear() -> None:
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    intent = _market_order()
    _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=intent, verdict=_blocked_verdict()),
        "blocked by safety verdict",
    )


def test_propose_order_surfaces_blocker_codes_in_error_message() -> None:
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    intent = _limit_order()
    raised: SimulationBoundaryError | None = None
    try:
        boundary.propose_order(order_intent=intent, verdict=_blocked_verdict())
    except SimulationBoundaryError as exc:
        raised = exc
    assert raised is not None
    message = str(raised)
    assert BLOCKER_HEARTBEAT_STALE in message
    assert BLOCKER_KILL_SWITCH_TRIPPED in message


def test_propose_order_does_not_mutate_intent_or_verdict() -> None:
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    intent = _limit_order(intent_id="immut-order")
    verdict = _clear_verdict()
    intent_snapshot = (
        intent.lane,
        intent.intent_id,
        intent.created_at,
        intent.symbol,
        intent.side,
        intent.quantity,
        intent.order_type,
        intent.limit_price,
    )
    verdict_snapshot = (
        verdict.clear,
        verdict.blockers,
        verdict.kill_switch_state,
        verdict.reconciliation_status,
        verdict.observed_at,
    )
    boundary.propose_order(order_intent=intent, verdict=verdict)
    assert (
        intent.lane,
        intent.intent_id,
        intent.created_at,
        intent.symbol,
        intent.side,
        intent.quantity,
        intent.order_type,
        intent.limit_price,
    ) == intent_snapshot
    assert (
        verdict.clear,
        verdict.blockers,
        verdict.kill_switch_state,
        verdict.reconciliation_status,
        verdict.observed_at,
    ) == verdict_snapshot


def test_propose_order_rejects_intent_with_mismatched_lane() -> None:
    """Lane mismatch raises with both lanes' string values in the message.

    :class:`SimulationLane` has only one authorized value
    (``LOCAL_ONLY``); to exercise the mismatch branch this test
    injects a stand-in :class:`StrEnum` value via
    ``object.__setattr__`` on the frozen intent (the same technique
    used by the P5-01 boundary tests for the identical branch).
    """
    from enum import StrEnum

    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    intent = _market_order(intent_id="lane-mismatch")

    class _StandInLane(StrEnum):
        OTHER = "other_lane_test_only"

    object.__setattr__(intent, "lane", _StandInLane.OTHER)
    _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=intent, verdict=_clear_verdict()),
        "lane mismatch",
    )


def test_propose_order_lane_check_uses_identity() -> None:
    """Boundary lane comparison is by identity (``is``) because
    :class:`SimulationLane` is a :class:`StrEnum` and enum members
    are singletons. This test documents the contract for the
    P5-02 surface (mirroring the P5-01 contract on ``propose``)."""
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    intent = _limit_order()
    assert intent.lane is boundary.lane
    boundary.propose_order(order_intent=intent, verdict=_clear_verdict())


# ---------------------------------------------------------------------------
# Boundary continues to gate the original P5-01 SimulatedIntent unchanged
# ---------------------------------------------------------------------------


def test_propose_order_does_not_accept_p5_01_simulated_intent() -> None:
    """``propose_order`` is strict about its input type.

    Passing a P5-01 :class:`SimulatedIntent` to ``propose_order``
    must raise rather than silently widen to accept the simpler
    placeholder shape. The original :meth:`SimulationBoundary.propose`
    remains the gate for :class:`SimulatedIntent`.
    """
    from gmc_rebuild.simulation import SimulatedIntent

    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    p5_01_intent = SimulatedIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="p5-01-shape",
        created_at=_FIXED_CLOCK_Z,
    )
    bogus: Any = p5_01_intent
    _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=bogus, verdict=_clear_verdict()),
        "order_intent must be a SimulatedOrderIntent",
    )
