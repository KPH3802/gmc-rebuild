"""P5-03 simulated-order-intent invariants — tripwire-only tests.

This module is a **tripwire-only** test suite for the merged P5-01
local simulation boundary skeleton
(``governance/authorizations/2026-05-17_p5-01.md``) and the merged
P5-02 simulated order intent model
(``governance/authorizations/2026-05-17_p5-02.md``). It introduces
**no new production behaviour**: every test in this module exercises
the existing merged surface (``SimulationLane``, ``SimulatedIntent``,
``SimulatedOrderSide``, ``SimulatedOrderType``, ``SimulatedOrderIntent``,
``SimulationBoundary.propose``, ``SimulationBoundary.propose_order``,
``SimulationBoundaryError``) and asserts invariants that, if ever
violated by a future change, would fail before the change reached
``main``.

Authorization: ``governance/authorizations/2026-05-17_p5-03.md``.

Invariants tripwired here:

- **Equality / hashability of** :class:`SimulatedOrderIntent` —
  records constructed with the same logical inputs compare equal and
  hash equal; differing in any single field breaks both equality and
  hash equality.
- **build() ↔ direct-construct equivalence** — a record built via
  :meth:`SimulatedOrderIntent.build` with a UTC ``datetime`` equals a
  record constructed directly with the equivalent ADR-004 Z-suffixed
  string. Future timestamp-format drift would break this invariant.
- **Frozen / __slots__ / exact eight-field shape** — assignment to any
  field raises :class:`dataclasses.FrozenInstanceError`; the
  ``__slots__`` tuple matches the ``dataclasses.fields()`` order
  exactly; adding a ninth field would fail the shape assertion. (The
  shape assertion is the same closed-tuple tripwire used by the P5-02
  test ``test_simulated_order_intent_dataclass_fields_are_exactly_the_authorized_set``;
  this module re-asserts it under a different lens to make scope-creep
  visible from both directions.)
- :meth:`SimulationBoundary.propose_order` **determinism** — calling
  it twice with the same inputs returns the same object by identity
  both times, and the returned object is the supplied ``order_intent``
  itself (not a copy, not a derived value).
- :meth:`SimulationBoundary.propose_order` **non-mutation** — after a
  successful call, every observable field of the input
  ``order_intent`` and ``verdict`` is unchanged, and ``id()`` of both
  is preserved. Future "act on intent" drift (e.g., quietly clearing
  ``limit_price`` or mutating ``blockers``) would fail this invariant
  immediately. This directly tripwires the
  ``RECOVERY.md`` §16.5 "Paper and live execution remain blocked"
  rule.
- **Blocker-surface coverage** — for every non-clear
  :class:`SafetyVerdict` shape exercised here, every blocker code
  present in ``verdict.blockers`` appears in the raised
  :class:`SimulationBoundaryError`'s message. Future "swallow blocker"
  drift would fail.
- :class:`SimulatedIntent` **vs** :class:`SimulatedOrderIntent`
  **separation** — :meth:`SimulationBoundary.propose_order` rejects a
  :class:`SimulatedIntent`, and :meth:`SimulationBoundary.propose`
  rejects a :class:`SimulatedOrderIntent`. Future "merge propose
  paths" drift would fail this invariant.

Design constraints (governance, not stylistic):

- **Tripwire only.** This module adds no module under ``src/**``, no
  new public symbol, no new field, no new method, and no
  ``SimulationLane`` / ``SimulatedOrderSide`` / ``SimulatedOrderType``
  member.
- **Pytest-stub-free.** Tests avoid ``pytest.raises`` and
  fixture-typed parameters so the mypy strict pre-commit hook does
  not need a pytest-stub dependency, mirroring the existing
  ``tests/simulation/test_simulation_boundary.py`` and
  ``tests/simulation/test_simulated_order_intent.py`` patterns.
- **Local-only.** No I/O, no network, no ``time.sleep``, no
  ``os.environ`` / ``os.getenv``, no broker SDK, no scheduler /
  daemon / background thread, no ``__main__`` entry point, no
  persistence.
"""

from __future__ import annotations

import contextlib
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
    BLOCKER_RECONCILIATION_FAILED,
    BLOCKER_RECONCILIATION_UNAVAILABLE,
    BLOCKER_RECONCILIATION_WARNING,
    SafetyVerdict,
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

_FIXED_CLOCK = datetime(2026, 5, 17, 14, 0, 0, tzinfo=UTC)
_FIXED_CLOCK_Z = "2026-05-17T14:00:00Z"


# ---------------------------------------------------------------------------
# Tripwire helpers (mirror the existing test_simulated_order_intent.py shape)
# ---------------------------------------------------------------------------


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


def _market_order(*, intent_id: str = "order-A1") -> SimulatedOrderIntent:
    return SimulatedOrderIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_FIXED_CLOCK_Z,
        symbol="SIM-INV-A",
        side=SimulatedOrderSide.BUY,
        quantity=100,
        order_type=SimulatedOrderType.MARKET,
        limit_price=None,
    )


def _limit_order(*, intent_id: str = "order-B2") -> SimulatedOrderIntent:
    return SimulatedOrderIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_FIXED_CLOCK_Z,
        symbol="SIM-INV-B",
        side=SimulatedOrderSide.SELL,
        quantity=50,
        order_type=SimulatedOrderType.LIMIT,
        limit_price=42.5,
    )


def _placeholder_intent(*, intent_id: str = "intent-X9") -> SimulatedIntent:
    return SimulatedIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_FIXED_CLOCK_Z,
    )


# ---------------------------------------------------------------------------
# Invariant 1 — Equality / hashability of SimulatedOrderIntent
# ---------------------------------------------------------------------------


def test_invariant_equal_orders_are_eq_and_hash_eq_for_market_shape() -> None:
    """Two MARKET records with the same logical inputs are ``==`` and hash equal."""
    a = _market_order()
    b = _market_order()
    assert a is not b
    assert a == b
    assert hash(a) == hash(b)


def test_invariant_equal_orders_are_eq_and_hash_eq_for_limit_shape() -> None:
    """Two LIMIT records with the same logical inputs are ``==`` and hash equal."""
    a = _limit_order()
    b = _limit_order()
    assert a is not b
    assert a == b
    assert hash(a) == hash(b)


def test_invariant_differing_field_breaks_equality_and_hash() -> None:
    """Differing in any single field breaks both equality and hash equality.

    The tripwire shape: for each of the eight fields, construct a
    sibling record that differs only in that field, and assert
    ``a != b and hash(a) != hash(b)``. If a future change makes any
    field collapse to a "do not care" status (e.g., quietly clearing
    ``limit_price`` for ``MARKET`` orders, or coercing ``symbol`` to
    upper-case), this test fails because two previously-distinct
    records would now collide.
    """
    base = _limit_order()

    differs_by_lane_only: list[SimulatedOrderIntent] = []
    differs_by_intent_id = SimulatedOrderIntent(
        lane=base.lane,
        intent_id=base.intent_id + "-alt",
        created_at=base.created_at,
        symbol=base.symbol,
        side=base.side,
        quantity=base.quantity,
        order_type=base.order_type,
        limit_price=base.limit_price,
    )
    differs_by_created_at = SimulatedOrderIntent(
        lane=base.lane,
        intent_id=base.intent_id,
        created_at="2026-05-17T14:00:01Z",
        symbol=base.symbol,
        side=base.side,
        quantity=base.quantity,
        order_type=base.order_type,
        limit_price=base.limit_price,
    )
    differs_by_symbol = SimulatedOrderIntent(
        lane=base.lane,
        intent_id=base.intent_id,
        created_at=base.created_at,
        symbol=base.symbol + "X",
        side=base.side,
        quantity=base.quantity,
        order_type=base.order_type,
        limit_price=base.limit_price,
    )
    differs_by_side = SimulatedOrderIntent(
        lane=base.lane,
        intent_id=base.intent_id,
        created_at=base.created_at,
        symbol=base.symbol,
        side=SimulatedOrderSide.BUY,
        quantity=base.quantity,
        order_type=base.order_type,
        limit_price=base.limit_price,
    )
    differs_by_quantity = SimulatedOrderIntent(
        lane=base.lane,
        intent_id=base.intent_id,
        created_at=base.created_at,
        symbol=base.symbol,
        side=base.side,
        quantity=base.quantity + 1,
        order_type=base.order_type,
        limit_price=base.limit_price,
    )
    # order_type change forces a corresponding limit_price change to keep
    # the new record validly-constructed (MARKET requires None).
    differs_by_order_type = SimulatedOrderIntent(
        lane=base.lane,
        intent_id=base.intent_id,
        created_at=base.created_at,
        symbol=base.symbol,
        side=base.side,
        quantity=base.quantity,
        order_type=SimulatedOrderType.MARKET,
        limit_price=None,
    )
    differs_by_limit_price = SimulatedOrderIntent(
        lane=base.lane,
        intent_id=base.intent_id,
        created_at=base.created_at,
        symbol=base.symbol,
        side=base.side,
        quantity=base.quantity,
        order_type=base.order_type,
        limit_price=99.0,
    )

    # `lane` cannot vary today because SimulationLane is closed at LOCAL_ONLY;
    # the closed-enum tripwire elsewhere covers the lane invariant, so this
    # field is intentionally omitted from the "differs-by-field" matrix.
    assert differs_by_lane_only == []

    differs = [
        differs_by_intent_id,
        differs_by_created_at,
        differs_by_symbol,
        differs_by_side,
        differs_by_quantity,
        differs_by_order_type,
        differs_by_limit_price,
    ]
    for sibling in differs:
        assert sibling != base, f"sibling collided with base: {sibling}"
        assert hash(sibling) != hash(base), f"sibling hash collided with base: {sibling}"


def test_invariant_orders_can_live_in_a_set_and_a_dict_key_position() -> None:
    """Records are hashable in practice, not just in the dunder.

    Adding two equal records to a ``set`` collapses to one entry;
    using them as ``dict`` keys retrieves the same value. If a future
    change accidentally removes ``frozen=True`` or adds a mutable
    field, ``__hash__`` would be set to ``None`` and this invariant
    would fail.
    """
    a = _market_order()
    b = _market_order()
    seen = {a, b}
    assert len(seen) == 1
    table = {a: "first", b: "second"}
    assert table[a] == "second"


# ---------------------------------------------------------------------------
# Invariant 2 — build() ↔ direct-construct equivalence (UTC discipline)
# ---------------------------------------------------------------------------


def test_invariant_market_build_equals_direct_construct() -> None:
    """A MARKET record built via ``.build()`` equals the directly-constructed equivalent."""
    direct = SimulatedOrderIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="build-eq-A",
        created_at=_FIXED_CLOCK_Z,
        symbol="SIM-BUILD-A",
        side=SimulatedOrderSide.BUY,
        quantity=10,
        order_type=SimulatedOrderType.MARKET,
        limit_price=None,
    )
    built = SimulatedOrderIntent.build(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="build-eq-A",
        created_at=_FIXED_CLOCK,
        symbol="SIM-BUILD-A",
        side=SimulatedOrderSide.BUY,
        quantity=10,
        order_type=SimulatedOrderType.MARKET,
        limit_price=None,
    )
    assert direct == built
    assert hash(direct) == hash(built)
    assert built.created_at == _FIXED_CLOCK_Z


def test_invariant_limit_build_equals_direct_construct() -> None:
    """A LIMIT record built via ``.build()`` equals the directly-constructed equivalent."""
    direct = SimulatedOrderIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="build-eq-B",
        created_at=_FIXED_CLOCK_Z,
        symbol="SIM-BUILD-B",
        side=SimulatedOrderSide.SELL,
        quantity=25,
        order_type=SimulatedOrderType.LIMIT,
        limit_price=12.5,
    )
    built = SimulatedOrderIntent.build(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="build-eq-B",
        created_at=_FIXED_CLOCK,
        symbol="SIM-BUILD-B",
        side=SimulatedOrderSide.SELL,
        quantity=25,
        order_type=SimulatedOrderType.LIMIT,
        limit_price=12.5,
    )
    assert direct == built
    assert hash(direct) == hash(built)
    assert built.created_at == _FIXED_CLOCK_Z


def test_invariant_build_default_limit_price_is_none() -> None:
    """``.build()`` defaults ``limit_price`` to ``None`` (MARKET-compatible)."""
    built = SimulatedOrderIntent.build(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="build-default-C",
        created_at=_FIXED_CLOCK,
        symbol="SIM-BUILD-C",
        side=SimulatedOrderSide.BUY,
        quantity=1,
        order_type=SimulatedOrderType.MARKET,
    )
    assert built.limit_price is None


# ---------------------------------------------------------------------------
# Invariant 3 — Frozen / __slots__ / exact eight-field shape
# ---------------------------------------------------------------------------


def test_invariant_simulated_order_intent_is_frozen_against_field_assignment() -> None:
    """Direct attribute assignment on any field raises ``FrozenInstanceError``.

    Tripwires against future ``frozen=False`` drift.
    """
    order = _market_order()
    raised: list[Exception] = []
    field_names = tuple(field.name for field in dataclasses.fields(order))
    for name in field_names:
        try:
            object.__setattr__(order, name, getattr(order, name))
        except Exception as exc:
            raised.append(exc)
            continue
        # Using object.__setattr__ deliberately bypasses __setattr__ guard;
        # plain attribute assignment should still raise.
        try:
            setattr(order, name, getattr(order, name))
        except dataclasses.FrozenInstanceError:
            continue
        raised.append(AssertionError(f"field {name!r} accepted assignment"))
    assert raised == [], f"frozen dataclass invariant broke: {raised!r}"


def test_invariant_simulated_order_intent_uses_slots() -> None:
    """``__slots__`` is declared and matches the field order; no ``__dict__``."""
    order = _market_order()
    assert hasattr(order, "__slots__")
    field_names = tuple(field.name for field in dataclasses.fields(order))
    # __slots__ on a slotted frozen dataclass is the tuple of field names.
    assert tuple(SimulatedOrderIntent.__slots__) == field_names
    # No __dict__ — a slotted dataclass should not have one.
    assert not hasattr(order, "__dict__"), f"slotted dataclass leaked __dict__: {order.__dict__!r}"


def test_invariant_simulated_order_intent_has_exactly_eight_fields_in_order() -> None:
    """``dataclasses.fields()`` returns the exact eight authorized fields in order.

    This is the same closed-tuple tripwire enforced by
    ``test_simulated_order_intent_dataclass_fields_are_exactly_the_authorized_set``;
    repeating it here under the invariants lens makes the rule
    discoverable from both test modules. A future ninth field — for
    example a venue, account, broker_credential, time_in_force, or
    persistence_handle — fails this assertion before it lands.
    """
    fields = tuple(field.name for field in dataclasses.fields(SimulatedOrderIntent))
    assert fields == (
        "lane",
        "intent_id",
        "created_at",
        "symbol",
        "side",
        "quantity",
        "order_type",
        "limit_price",
    ), f"SimulatedOrderIntent fields drift: {fields}"


# ---------------------------------------------------------------------------
# Invariant 4 — propose_order determinism and identity-return
# ---------------------------------------------------------------------------


def test_invariant_propose_order_returns_input_by_identity_market() -> None:
    """``propose_order`` returns the same object by identity on clear verdict (MARKET)."""
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    order = _market_order()
    verdict = _clear_verdict()
    returned = boundary.propose_order(order_intent=order, verdict=verdict)
    assert returned is order


def test_invariant_propose_order_returns_input_by_identity_limit() -> None:
    """``propose_order`` returns the same object by identity on clear verdict (LIMIT)."""
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    order = _limit_order()
    verdict = _clear_verdict()
    returned = boundary.propose_order(order_intent=order, verdict=verdict)
    assert returned is order


def test_invariant_propose_order_is_deterministic_across_repeated_calls() -> None:
    """Calling ``propose_order`` twice with the same inputs returns identical results.

    Tripwires against future "first call returns X, second call
    returns Y" drift — for example a hidden retry, queue, or stateful
    accumulator inside the boundary.
    """
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    order = _limit_order()
    verdict = _clear_verdict()
    first = boundary.propose_order(order_intent=order, verdict=verdict)
    second = boundary.propose_order(order_intent=order, verdict=verdict)
    third = boundary.propose_order(order_intent=order, verdict=verdict)
    assert first is order
    assert second is order
    assert third is order
    assert first is second
    assert second is third


def test_invariant_propose_order_is_deterministic_across_equal_inputs() -> None:
    """Two equal-but-distinct inputs each return their own input by identity.

    The boundary does not collapse equal-but-distinct objects to a
    single canonical instance; each call returns the exact object it
    was given.
    """
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    order_a = _market_order()
    order_b = _market_order()
    verdict = _clear_verdict()
    assert order_a is not order_b
    assert order_a == order_b
    returned_a = boundary.propose_order(order_intent=order_a, verdict=verdict)
    returned_b = boundary.propose_order(order_intent=order_b, verdict=verdict)
    assert returned_a is order_a
    assert returned_b is order_b
    assert returned_a is not returned_b


# ---------------------------------------------------------------------------
# Invariant 5 — propose_order non-mutation of order_intent and verdict
# ---------------------------------------------------------------------------


def test_invariant_propose_order_does_not_mutate_order_intent_market() -> None:
    """After a successful ``propose_order``, every field of the input is unchanged."""
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    order = _market_order()
    verdict = _clear_verdict()
    snapshot = (
        order.lane,
        order.intent_id,
        order.created_at,
        order.symbol,
        order.side,
        order.quantity,
        order.order_type,
        order.limit_price,
    )
    snapshot_id = id(order)
    boundary.propose_order(order_intent=order, verdict=verdict)
    assert id(order) == snapshot_id
    assert (
        order.lane,
        order.intent_id,
        order.created_at,
        order.symbol,
        order.side,
        order.quantity,
        order.order_type,
        order.limit_price,
    ) == snapshot


def test_invariant_propose_order_does_not_mutate_order_intent_limit() -> None:
    """After a successful ``propose_order``, LIMIT-shaped input is unchanged.

    Specifically tripwires against future "quietly clear ``limit_price``
    on a successful proposal" drift, which would silently weaken the
    inertness contract.
    """
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    order = _limit_order()
    verdict = _clear_verdict()
    snapshot = (
        order.lane,
        order.intent_id,
        order.created_at,
        order.symbol,
        order.side,
        order.quantity,
        order.order_type,
        order.limit_price,
    )
    snapshot_id = id(order)
    boundary.propose_order(order_intent=order, verdict=verdict)
    assert id(order) == snapshot_id
    assert (
        order.lane,
        order.intent_id,
        order.created_at,
        order.symbol,
        order.side,
        order.quantity,
        order.order_type,
        order.limit_price,
    ) == snapshot
    assert order.limit_price == 42.5


def test_invariant_propose_order_does_not_mutate_verdict() -> None:
    """After a successful ``propose_order``, the supplied verdict is unchanged."""
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    order = _market_order()
    verdict = _clear_verdict()
    snapshot = (
        verdict.clear,
        verdict.blockers,
        verdict.kill_switch_state,
        verdict.reconciliation_status,
        verdict.observed_at,
    )
    statuses_snapshot = dict(verdict.heartbeat_statuses)
    snapshot_id = id(verdict)
    boundary.propose_order(order_intent=order, verdict=verdict)
    assert id(verdict) == snapshot_id
    assert (
        verdict.clear,
        verdict.blockers,
        verdict.kill_switch_state,
        verdict.reconciliation_status,
        verdict.observed_at,
    ) == snapshot
    assert dict(verdict.heartbeat_statuses) == statuses_snapshot


# ---------------------------------------------------------------------------
# Invariant 6 — Blocker codes are surfaced in SimulationBoundaryError
# ---------------------------------------------------------------------------


def _blocked_verdict(blockers: tuple[str, ...]) -> SafetyVerdict:
    """Construct a non-clear verdict carrying the supplied blockers.

    The heartbeat / kill-switch / reconciliation enums are chosen to
    produce a self-consistent verdict shape for each blocker code;
    they are not meant to model every possible state, only to make
    the verdict constructable.
    """
    return SafetyVerdict(
        clear=False,
        blockers=blockers,
        heartbeat_statuses=MappingProxyType({"operator": HeartbeatStatus.STALE}),
        kill_switch_state=(
            KillSwitchState.TRIPPED
            if BLOCKER_KILL_SWITCH_TRIPPED in blockers
            else KillSwitchState.ARMED
        ),
        reconciliation_status=(
            ReconciliationStatus.FAILED
            if BLOCKER_RECONCILIATION_FAILED in blockers
            else ReconciliationStatus.UNAVAILABLE
            if BLOCKER_RECONCILIATION_UNAVAILABLE in blockers
            else ReconciliationStatus.WARNING
            if BLOCKER_RECONCILIATION_WARNING in blockers
            else ReconciliationStatus.CLEAN
        ),
        observed_at=_FIXED_CLOCK_Z,
    )


def test_invariant_propose_order_surfaces_single_blocker_in_error() -> None:
    """Each blocker code in a single-blocker verdict appears in the error message."""
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    order = _market_order()
    for blocker in (
        BLOCKER_HEARTBEAT_STALE,
        BLOCKER_KILL_SWITCH_TRIPPED,
        BLOCKER_RECONCILIATION_FAILED,
        BLOCKER_RECONCILIATION_UNAVAILABLE,
        BLOCKER_RECONCILIATION_WARNING,
    ):
        verdict = _blocked_verdict((blocker,))
        _expect_boundary_error(
            lambda v=verdict, o=order: boundary.propose_order(order_intent=o, verdict=v),
            match=blocker,
        )


def test_invariant_propose_order_surfaces_every_blocker_in_multi_blocker_error() -> None:
    """In a multi-blocker verdict, every blocker code appears in the error message.

    Tripwires against future "summarize blockers" drift that would
    drop blocker codes for terseness.
    """
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    order = _market_order()
    blockers = (
        BLOCKER_HEARTBEAT_STALE,
        BLOCKER_KILL_SWITCH_TRIPPED,
        BLOCKER_RECONCILIATION_FAILED,
    )
    verdict = _blocked_verdict(blockers)
    raised: SimulationBoundaryError | None = None
    try:
        boundary.propose_order(order_intent=order, verdict=verdict)
    except SimulationBoundaryError as exc:
        raised = exc
    assert raised is not None
    message = str(raised)
    for blocker in blockers:
        assert blocker in message, f"blocker {blocker!r} missing from message {message!r}"


def test_invariant_propose_order_blocked_error_does_not_mutate_inputs() -> None:
    """A blocked ``propose_order`` does not mutate the input order or verdict."""
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    order = _limit_order()
    verdict = _blocked_verdict((BLOCKER_HEARTBEAT_STALE,))
    order_snapshot = (
        order.lane,
        order.intent_id,
        order.created_at,
        order.symbol,
        order.side,
        order.quantity,
        order.order_type,
        order.limit_price,
    )
    verdict_snapshot = (
        verdict.clear,
        verdict.blockers,
        verdict.kill_switch_state,
        verdict.reconciliation_status,
        verdict.observed_at,
    )
    statuses_snapshot = dict(verdict.heartbeat_statuses)
    with contextlib.suppress(SimulationBoundaryError):
        boundary.propose_order(order_intent=order, verdict=verdict)
    assert (
        order.lane,
        order.intent_id,
        order.created_at,
        order.symbol,
        order.side,
        order.quantity,
        order.order_type,
        order.limit_price,
    ) == order_snapshot
    assert (
        verdict.clear,
        verdict.blockers,
        verdict.kill_switch_state,
        verdict.reconciliation_status,
        verdict.observed_at,
    ) == verdict_snapshot
    assert dict(verdict.heartbeat_statuses) == statuses_snapshot


# ---------------------------------------------------------------------------
# Invariant 7 — P5-01 SimulatedIntent ↔ P5-02 SimulatedOrderIntent separation
# ---------------------------------------------------------------------------


def test_invariant_propose_order_rejects_simulated_intent() -> None:
    """Passing a :class:`SimulatedIntent` to ``propose_order`` raises with a type complaint.

    Tripwires against future "merge propose paths" drift in which
    :meth:`SimulationBoundary.propose_order` quietly accepts the
    P5-01 placeholder shape.
    """
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    verdict = _clear_verdict()
    _expect_boundary_error(
        lambda: boundary.propose_order(
            order_intent=placeholder,  # type: ignore[arg-type]
            verdict=verdict,
        ),
        match="SimulatedOrderIntent",
    )


def test_invariant_propose_rejects_simulated_order_intent() -> None:
    """Passing a :class:`SimulatedOrderIntent` to ``propose`` raises with a type complaint.

    Tripwires the mirror-image drift: :meth:`SimulationBoundary.propose`
    must continue to reject the P5-02 richer shape so the two paths
    stay distinct.
    """
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    order = _market_order()
    verdict = _clear_verdict()
    _expect_boundary_error(
        lambda: boundary.propose(
            intent=order,  # type: ignore[arg-type]
            verdict=verdict,
        ),
        match="SimulatedIntent",
    )


def test_invariant_propose_and_propose_order_remain_independent_methods() -> None:
    """``propose`` and ``propose_order`` are distinct, non-aliased methods.

    A future refactor that points one method at the other (e.g.,
    ``propose_order = propose`` for "convenience") would change the
    qualname relationship asserted here.
    """
    assert SimulationBoundary.propose.__qualname__ != SimulationBoundary.propose_order.__qualname__
    # If a future change aliases one to the other, both attributes would
    # resolve to the same callable; we read the underlying ``__func__``
    # via the class dict so the comparison stays meaningful even if the
    # method-resolution order changes.
    propose_in_dict = SimulationBoundary.__dict__["propose"]
    propose_order_in_dict = SimulationBoundary.__dict__["propose_order"]
    assert propose_in_dict.__qualname__ == "SimulationBoundary.propose"
    assert propose_order_in_dict.__qualname__ == "SimulationBoundary.propose_order"


def test_invariant_simulated_intent_and_simulated_order_intent_are_distinct_classes() -> None:
    """:class:`SimulatedIntent` and :class:`SimulatedOrderIntent` are distinct types.

    Neither is a subclass of the other; their ``dataclasses.fields()``
    tuples differ. This prevents accidental polymorphism between the
    P5-01 placeholder and the P5-02 record from creeping in.
    """
    assert not issubclass(SimulatedIntent, SimulatedOrderIntent)
    assert not issubclass(SimulatedOrderIntent, SimulatedIntent)
    placeholder_fields = tuple(f.name for f in dataclasses.fields(SimulatedIntent))
    order_fields = tuple(f.name for f in dataclasses.fields(SimulatedOrderIntent))
    assert placeholder_fields == ("lane", "intent_id", "created_at")
    assert order_fields == (
        "lane",
        "intent_id",
        "created_at",
        "symbol",
        "side",
        "quantity",
        "order_type",
        "limit_price",
    )
    # Sanity: the placeholder field tuple is a strict prefix of the order tuple,
    # which makes the future "extend by adding a new field at position N"
    # tripwire above (in test_invariant_simulated_order_intent_has_exactly_eight_fields_in_order)
    # particularly meaningful.
    assert order_fields[: len(placeholder_fields)] == placeholder_fields
