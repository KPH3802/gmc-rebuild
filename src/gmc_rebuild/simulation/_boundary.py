"""Inert local simulation boundary skeleton (P5-01) and simulated order intent model (P5-02).

See :mod:`gmc_rebuild.simulation` for the design constraints and
authorization references. This module deliberately performs only:

- declaration of a closed string-enum identifying the authorized
  local simulation lane(s) (P5-01);
- declaration of an immutable :class:`SimulatedIntent` record that
  represents a *placeholder* for a future simulated progression,
  carrying only a lane, an identifier, and an ADR-004 ``Z``-suffixed
  UTC creation timestamp (P5-01);
- declaration of closed string-enums for simulated order side and
  simulated order type, and an immutable :class:`SimulatedOrderIntent`
  record adding the order-shaped fields the operator may attach to a
  simulated progression (symbol, side, quantity, order type, optional
  limit price) (P5-02);
- declaration of a :class:`SimulationBoundary` that exposes two
  read-only gate methods, :meth:`SimulationBoundary.propose` for
  :class:`SimulatedIntent` (P5-01) and
  :meth:`SimulationBoundary.propose_order` for
  :class:`SimulatedOrderIntent` (P5-02). Each returns the supplied
  intent unchanged if and only if (a) the boundary's lane matches the
  intent's lane and (b) the supplied :class:`SafetyVerdict` is
  ``clear``. The boundary does not submit, route, execute, persist,
  schedule, or connect anything; it owns no state beyond its own
  lane; it raises :class:`SimulationBoundaryError` with the verdict's
  blocker tuple when the verdict is not clear.

The boundary is a *gate*. It does not start a simulation, does not
hold a queue of pending intents, does not run, does not sleep, does
not talk to any broker (real or paper), does not read market data,
does not read secrets, does not reach the network, does not persist,
and does not schedule. The new :class:`SimulatedOrderIntent` type
adds order-shaped data fields but **no execution capability**: no
venue / account / broker credential fields exist on the record, no
routing instruction is carried, and the only operation that can
"do" anything with the intent is :meth:`SimulationBoundary.propose_order`,
which returns the intent unchanged on a clear safety verdict and
raises on any other condition.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from gmc_rebuild.risk import to_utc_string
from gmc_rebuild.runtime import SafetyVerdict


class SimulationBoundaryError(ValueError):
    """Raised when the simulation boundary rejects construction or input.

    Subclass of ``ValueError`` so callers can catch it alongside other
    bad-input cases while still distinguishing simulation-boundary
    shape and gate violations by type.
    """


class SimulationLane(StrEnum):
    """Closed enumeration of authorized local simulation lanes.

    Only :attr:`LOCAL_ONLY` is authorized by the P5-01 packet. The
    lane identifies that an intent (or boundary) is scoped to a
    purely-local, in-process simulation that does not connect to any
    broker (real or paper), does not place orders, and does not
    ingest market data. Future lanes (for example a paper-broker lane
    or a backtest lane) are explicitly **not** authorized by this
    enum or this module; each requires its own separate written
    authorization from Kevin per ``AI_WORKFLOW.md`` §7.
    """

    LOCAL_ONLY = "local_only"


@dataclass(frozen=True, slots=True)
class SimulatedIntent:
    """Immutable placeholder for a future simulated progression.

    Fields:

    - ``lane``: the :class:`SimulationLane` the intent is scoped to.
    - ``intent_id``: short non-empty identifier for the intent; must
      contain no whitespace. The identifier is opaque to this module
      (no parsing, no broker mapping).
    - ``created_at``: ADR-004 ``Z``-suffixed UTC string recording
      when the intent record was constructed by the operator.

    The intent carries no symbol, no side, no quantity, no price, no
    venue, no broker account, no routing instruction, and no
    persistence handle. It is a typed placeholder; future authorized
    packets may extend the schema, but **this** packet only defines
    the placeholder shape.
    """

    lane: SimulationLane
    intent_id: str
    created_at: str

    def __post_init__(self) -> None:
        if not isinstance(self.lane, SimulationLane):
            raise SimulationBoundaryError(
                f"SimulatedIntent.lane must be a SimulationLane, got {type(self.lane).__name__}"
            )
        if not isinstance(self.intent_id, str) or not self.intent_id:
            raise SimulationBoundaryError("SimulatedIntent.intent_id must be a non-empty str")
        if any(ch.isspace() for ch in self.intent_id):
            raise SimulationBoundaryError("SimulatedIntent.intent_id must not contain whitespace")
        if not isinstance(self.created_at, str) or not self.created_at:
            raise SimulationBoundaryError("SimulatedIntent.created_at must be a non-empty str")
        if not self.created_at.endswith("Z"):
            raise SimulationBoundaryError(
                "SimulatedIntent.created_at must be an ADR-004 Z-suffixed UTC string"
            )

    @classmethod
    def build(
        cls,
        *,
        lane: SimulationLane,
        intent_id: str,
        created_at: datetime,
    ) -> SimulatedIntent:
        """Construct a :class:`SimulatedIntent` from a UTC ``datetime``.

        Convenience constructor that converts ``created_at`` into the
        ADR-004 ``Z``-suffixed UTC string via
        :func:`gmc_rebuild.risk.to_utc_string`. Naive datetimes raise
        :class:`gmc_rebuild.time.NaiveDatetimeError` from
        :func:`gmc_rebuild.time.ensure_utc`, consistent with the
        existing P2-05 risk-control boundary.
        """
        return cls(lane=lane, intent_id=intent_id, created_at=to_utc_string(created_at))


class SimulatedOrderSide(StrEnum):
    """Closed enumeration of authorized simulated-order sides (P5-02).

    Only :attr:`BUY` and :attr:`SELL` are authorized by the P5-02
    packet. The side identifies the direction the operator would
    intend if this were a real progression; in this packet it is a
    pure data tag and triggers no broker action. Future sides
    (for example ``SELL_SHORT`` or ``BUY_TO_COVER``) are explicitly
    **not** authorized by this enum and would each require their own
    separate written authorization from Kevin per ``AI_WORKFLOW.md``
    §7 (see also the §16.5 Risk Register entry on order-intent
    semantics in ``RECOVERY.md``).
    """

    BUY = "buy"
    SELL = "sell"


class SimulatedOrderType(StrEnum):
    """Closed enumeration of authorized simulated-order types (P5-02).

    Only :attr:`MARKET` and :attr:`LIMIT` are authorized by the P5-02
    packet. The order type identifies the price discipline the
    operator would intend if this were a real progression; in this
    packet it is a pure data tag and triggers no broker action. A
    :attr:`MARKET` intent must have ``limit_price`` set to ``None``;
    a :attr:`LIMIT` intent must have a positive ``limit_price``.
    Future order types (for example ``STOP``, ``STOP_LIMIT``,
    ``MARKET_ON_CLOSE``, ``LIMIT_ON_OPEN``, ``TRAILING_STOP``, etc.)
    are explicitly **not** authorized by this enum and would each
    require their own separate written authorization from Kevin per
    ``AI_WORKFLOW.md`` §7.
    """

    MARKET = "market"
    LIMIT = "limit"


@dataclass(frozen=True, slots=True)
class SimulatedOrderIntent:
    """Immutable simulated-order-intent record (P5-02).

    Adds the order-shaped data fields the operator may attach to a
    simulated progression. Carries no broker, no venue, no account,
    no routing instruction, no execution capability, no persistence
    handle, and no market-data binding. The only operation that can
    "do" anything with this record is
    :meth:`SimulationBoundary.propose_order`, which returns the
    record unchanged on a clear safety verdict and raises on any
    other condition.

    Fields:

    - ``lane``: the :class:`SimulationLane` the intent is scoped to.
      Currently restricted to :attr:`SimulationLane.LOCAL_ONLY` by
      the P5-01 enum.
    - ``intent_id``: short non-empty identifier for the intent; must
      contain no whitespace. The identifier is opaque to this module
      (no parsing, no broker mapping, no exchange order-ID format
      assumed).
    - ``created_at``: ADR-004 ``Z``-suffixed UTC string recording
      when the intent record was constructed by the operator.
    - ``symbol``: short non-empty identifier for the instrument; must
      contain no whitespace. The symbol is opaque to this module (no
      symbol-universe lookup, no exchange resolution, no normalization
      to any vendor format, no validation against any market-data
      source). Future authorized packets may add symbol-universe
      validation; this packet treats the field as a free-form tag.
    - ``side``: :class:`SimulatedOrderSide` — currently ``BUY`` or
      ``SELL`` only.
    - ``quantity``: positive ``int`` representing the size of the
      simulated intent. ``bool`` values (which are a subclass of
      ``int``) are explicitly rejected to avoid the ``True == 1`` /
      ``False == 0`` trap. Fractional quantities are not authorized
      by this packet; ``float`` quantities are rejected.
    - ``order_type``: :class:`SimulatedOrderType` — currently
      ``MARKET`` or ``LIMIT`` only.
    - ``limit_price``: ``None`` when ``order_type`` is ``MARKET``;
      positive ``float`` when ``order_type`` is ``LIMIT``. ``bool``
      values are explicitly rejected. Negative, zero, or non-finite
      (``nan``, ``inf``) prices are explicitly rejected when
      ``order_type`` is ``LIMIT``.

    The record carries **no** venue, broker, account, routing
    instruction, time-in-force qualifier, post-only / IOC / FOK
    modifier, route-allow / route-deny list, broker credential, API
    key, or persistence handle. Adding any of those fields requires
    its own separate written authorization from Kevin per the §16.5
    Risk Register entry on order-intent semantics in ``RECOVERY.md``.
    """

    lane: SimulationLane
    intent_id: str
    created_at: str
    symbol: str
    side: SimulatedOrderSide
    quantity: int
    order_type: SimulatedOrderType
    limit_price: float | None

    def __post_init__(self) -> None:
        if not isinstance(self.lane, SimulationLane):
            raise SimulationBoundaryError(
                f"SimulatedOrderIntent.lane must be a SimulationLane, "
                f"got {type(self.lane).__name__}"
            )
        if not isinstance(self.intent_id, str) or not self.intent_id:
            raise SimulationBoundaryError("SimulatedOrderIntent.intent_id must be a non-empty str")
        if any(ch.isspace() for ch in self.intent_id):
            raise SimulationBoundaryError(
                "SimulatedOrderIntent.intent_id must not contain whitespace"
            )
        if not isinstance(self.created_at, str) or not self.created_at:
            raise SimulationBoundaryError("SimulatedOrderIntent.created_at must be a non-empty str")
        if not self.created_at.endswith("Z"):
            raise SimulationBoundaryError(
                "SimulatedOrderIntent.created_at must be an ADR-004 Z-suffixed UTC string"
            )
        if not isinstance(self.symbol, str) or not self.symbol:
            raise SimulationBoundaryError("SimulatedOrderIntent.symbol must be a non-empty str")
        if any(ch.isspace() for ch in self.symbol):
            raise SimulationBoundaryError("SimulatedOrderIntent.symbol must not contain whitespace")
        if not isinstance(self.side, SimulatedOrderSide):
            raise SimulationBoundaryError(
                f"SimulatedOrderIntent.side must be a SimulatedOrderSide, "
                f"got {type(self.side).__name__}"
            )
        if isinstance(self.quantity, bool) or not isinstance(self.quantity, int):
            raise SimulationBoundaryError(
                "SimulatedOrderIntent.quantity must be an int (not bool, not float)"
            )
        if self.quantity <= 0:
            raise SimulationBoundaryError("SimulatedOrderIntent.quantity must be positive")
        if not isinstance(self.order_type, SimulatedOrderType):
            raise SimulationBoundaryError(
                f"SimulatedOrderIntent.order_type must be a SimulatedOrderType, "
                f"got {type(self.order_type).__name__}"
            )
        if self.order_type is SimulatedOrderType.MARKET:
            if self.limit_price is not None:
                raise SimulationBoundaryError(
                    "SimulatedOrderIntent.limit_price must be None when order_type is MARKET"
                )
        else:
            if isinstance(self.limit_price, bool) or not isinstance(self.limit_price, float):
                raise SimulationBoundaryError(
                    "SimulatedOrderIntent.limit_price must be a float when order_type is LIMIT"
                )
            if not (self.limit_price == self.limit_price):
                raise SimulationBoundaryError(
                    "SimulatedOrderIntent.limit_price must be a finite number "
                    "when order_type is LIMIT"
                )
            if self.limit_price in (float("inf"), float("-inf")):
                raise SimulationBoundaryError(
                    "SimulatedOrderIntent.limit_price must be a finite number "
                    "when order_type is LIMIT"
                )
            if self.limit_price <= 0:
                raise SimulationBoundaryError(
                    "SimulatedOrderIntent.limit_price must be positive when order_type is LIMIT"
                )

    @classmethod
    def build(
        cls,
        *,
        lane: SimulationLane,
        intent_id: str,
        created_at: datetime,
        symbol: str,
        side: SimulatedOrderSide,
        quantity: int,
        order_type: SimulatedOrderType,
        limit_price: float | None = None,
    ) -> SimulatedOrderIntent:
        """Construct a :class:`SimulatedOrderIntent` from a UTC ``datetime``.

        Convenience constructor that converts ``created_at`` into the
        ADR-004 ``Z``-suffixed UTC string via
        :func:`gmc_rebuild.risk.to_utc_string`. Naive datetimes raise
        :class:`gmc_rebuild.time.NaiveDatetimeError` from
        :func:`gmc_rebuild.time.ensure_utc`, consistent with the
        existing P2-05 risk-control boundary and the existing
        :meth:`SimulatedIntent.build` classmethod.
        """
        return cls(
            lane=lane,
            intent_id=intent_id,
            created_at=to_utc_string(created_at),
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
        )


class SimulationBoundary:
    """Inert local simulation boundary.

    Owns a single :class:`SimulationLane` and exposes one operation,
    :meth:`propose`, which returns the supplied
    :class:`SimulatedIntent` unchanged if and only if:

    1. ``intent.lane`` equals the boundary's lane (no cross-lane
       progression is permitted; the only authorized lane today is
       :attr:`SimulationLane.LOCAL_ONLY`); and
    2. the supplied :class:`SafetyVerdict` has ``clear`` set to
       ``True`` (the P4-06 / P4-07 / P4-08 safety foundation gate
       must already be clear).

    If either condition fails, :meth:`propose` raises
    :class:`SimulationBoundaryError`. The boundary never mutates the
    intent, never stores it, never submits it, never routes it,
    never executes it, never persists it, never schedules anything,
    and never talks to any broker or network.

    The boundary holds no per-call state and is safe to share across
    operator calls. Constructing the boundary requires no
    authentication, no secrets, and no I/O.
    """

    __slots__ = ("_lane",)

    def __init__(self, *, lane: SimulationLane) -> None:
        if not isinstance(lane, SimulationLane):
            raise SimulationBoundaryError(
                f"SimulationBoundary.lane must be a SimulationLane, got {type(lane).__name__}"
            )
        self._lane: SimulationLane = lane

    @property
    def lane(self) -> SimulationLane:
        """The :class:`SimulationLane` this boundary is scoped to."""
        return self._lane

    def propose(
        self,
        *,
        intent: SimulatedIntent,
        verdict: SafetyVerdict,
    ) -> SimulatedIntent:
        """Return ``intent`` unchanged if and only if the gate is clear.

        Read-only: does not mutate ``intent``, ``verdict``, the
        boundary, or any external state. Does not record the call,
        does not enqueue, does not schedule, does not submit, does
        not route, does not execute, does not persist, does not
        sleep, and does not reach the network.

        Raises :class:`SimulationBoundaryError` when:

        - ``intent`` is not a :class:`SimulatedIntent`;
        - ``verdict`` is not a :class:`SafetyVerdict`;
        - ``intent.lane`` does not equal this boundary's
          :attr:`lane`;
        - ``verdict.clear`` is ``False`` (the error message includes
          the tuple of blocker codes from
          :attr:`SafetyVerdict.blockers` so the caller can surface
          which safety control rejected the progression).
        """
        if not isinstance(intent, SimulatedIntent):
            raise SimulationBoundaryError(
                f"SimulationBoundary.propose intent must be a SimulatedIntent, "
                f"got {type(intent).__name__}"
            )
        if not isinstance(verdict, SafetyVerdict):
            raise SimulationBoundaryError(
                f"SimulationBoundary.propose verdict must be a SafetyVerdict, "
                f"got {type(verdict).__name__}"
            )
        if intent.lane is not self._lane:
            raise SimulationBoundaryError(
                f"SimulationBoundary.propose lane mismatch: boundary lane is "
                f"{str(self._lane)!r}, intent lane is {str(intent.lane)!r}"
            )
        if not verdict.clear:
            raise SimulationBoundaryError(
                f"SimulationBoundary.propose blocked by safety verdict; "
                f"blockers={verdict.blockers!r}"
            )
        return intent

    def propose_order(
        self,
        *,
        order_intent: SimulatedOrderIntent,
        verdict: SafetyVerdict,
    ) -> SimulatedOrderIntent:
        """Return ``order_intent`` unchanged if and only if the gate is clear.

        Sibling of :meth:`propose` for the richer
        :class:`SimulatedOrderIntent` shape introduced by P5-02.
        Read-only: does not mutate ``order_intent``, ``verdict``, the
        boundary, or any external state. Does not record the call,
        does not enqueue, does not schedule, does not submit, does
        not route, does not execute, does not persist, does not
        sleep, does not reach the network, does not talk to any
        broker (real or paper), and does not consult any market-data
        source. The boundary's contract is identical to :meth:`propose`:
        the supplied intent is returned **by identity** on a clear
        verdict, and any other condition raises
        :class:`SimulationBoundaryError`.

        Raises :class:`SimulationBoundaryError` when:

        - ``order_intent`` is not a :class:`SimulatedOrderIntent`;
        - ``verdict`` is not a :class:`SafetyVerdict`;
        - ``order_intent.lane`` does not equal this boundary's
          :attr:`lane`;
        - ``verdict.clear`` is ``False`` (the error message includes
          the tuple of blocker codes from
          :attr:`SafetyVerdict.blockers` so the caller can surface
          which safety control rejected the progression).
        """
        if not isinstance(order_intent, SimulatedOrderIntent):
            raise SimulationBoundaryError(
                f"SimulationBoundary.propose_order order_intent must be a "
                f"SimulatedOrderIntent, got {type(order_intent).__name__}"
            )
        if not isinstance(verdict, SafetyVerdict):
            raise SimulationBoundaryError(
                f"SimulationBoundary.propose_order verdict must be a SafetyVerdict, "
                f"got {type(verdict).__name__}"
            )
        if order_intent.lane is not self._lane:
            raise SimulationBoundaryError(
                f"SimulationBoundary.propose_order lane mismatch: boundary lane is "
                f"{str(self._lane)!r}, order_intent lane is {str(order_intent.lane)!r}"
            )
        if not verdict.clear:
            raise SimulationBoundaryError(
                f"SimulationBoundary.propose_order blocked by safety verdict; "
                f"blockers={verdict.blockers!r}"
            )
        return order_intent


__all__ = [
    "SimulatedIntent",
    "SimulatedOrderIntent",
    "SimulatedOrderSide",
    "SimulatedOrderType",
    "SimulationBoundary",
    "SimulationBoundaryError",
    "SimulationLane",
]
