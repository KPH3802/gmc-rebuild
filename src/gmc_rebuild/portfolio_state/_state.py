"""P6-05 deterministic in-memory simulated portfolio state — internal module.

Defines the frozen, slotted :class:`SimulatedPosition` and
:class:`SimulatedPortfolio` value types and the pure
:func:`apply_simulated_order_intent` application function authorized by
PR P6-05 (see ``governance/authorizations/2026-05-22_p6-05.md``).

This module applies an **accepted** P6-03
:class:`~gmc_rebuild.decision.PositionDecision` together with a P6-04
:class:`~gmc_rebuild.simulation.SimulatedOrderIntent` to a value-typed
position book under a fixed, deterministic, fixture-only fill
assumption. It is the fifth Phase 6 dry-run capability; it is downstream
of the P6-01 signal-intake boundary, the P6-02 eligibility check, the
P6-03 decision composer, and the P5-02 / P6-04 simulated order intent
surface.

Design constraints — these are governance constraints, not stylistic
preferences (``governance/authorizations/2026-05-22_p6-05.md``):

- **State model — frozen / value-typed replaceable snapshot.** The
  portfolio is a frozen, slotted value object. "Applying" an accepted
  intent is a pure transformation that **returns a new snapshot**; the
  prior snapshot is never mutated. State evolution is expressed by
  replacing one immutable snapshot with the next. There is no
  event-sourced / append-only event log.
- **Idempotent application keyed by simulated order intent ID.** Each
  snapshot carries a value-typed, canonical (sorted, unique) tuple of
  the P6-04 simulated order intent IDs already applied. Re-applying the
  same accepted intent ID returns the prior snapshot unchanged (by
  identity); the position change is never double-applied.
- **Deterministic, fixture-only full-fill assumption.** The applied
  quantity is exactly the intent's ``quantity`` (a positive ``int``); a
  ``BUY`` adds it to the symbol's signed net quantity and a ``SELL``
  subtracts it. There is **no fill price, no partial fill, no fill
  engine, no market data, no broker confirmation** — only deterministic
  integer bookkeeping. A symbol whose net quantity reaches zero is
  dropped from the snapshot (canonical form).
- **No runtime activation.** No ``__main__`` entry point, no daemon, no
  scheduler, no background thread, no long-running service.
- **No external I/O.** No filesystem, no network, no broker SDK, no
  persistence, no ``time.sleep``, no ``os.environ`` / ``os.getenv``
  reads, no secrets.
- **No real position book.** No real account, no account identifier, no
  balances, no P&L, no cash ledger, no valuation, no broker
  reconciliation, no account sync. The snapshot is a pure value object
  over the supplied inputs and connects to nothing.
- **No mutation of inputs.** :func:`apply_simulated_order_intent` does
  not modify the supplied :class:`SimulatedPortfolio`,
  :class:`~gmc_rebuild.decision.PositionDecision`, or
  :class:`~gmc_rebuild.simulation.SimulatedOrderIntent`.
- **No re-export from package root.** :mod:`gmc_rebuild` is unchanged by
  this packet; this subpackage exposes its public surface only through
  ``from gmc_rebuild.portfolio_state import ...``.
"""

from __future__ import annotations

from dataclasses import dataclass

from gmc_rebuild.decision import PositionDecision, PositionDecisionOutcome
from gmc_rebuild.simulation import SimulatedOrderIntent, SimulatedOrderSide


@dataclass(frozen=True, slots=True)
class SimulatedPosition:
    """Immutable signed net position in a single symbol.

    Two fields:

    - ``symbol``: short non-empty identifier for the instrument; must
      contain no whitespace. Opaque to this module (no symbol-universe
      lookup, no market-data binding) exactly as on the upstream
      :class:`~gmc_rebuild.simulation.SimulatedOrderIntent`.
    - ``net_quantity``: signed ``int`` net position. Positive is a net
      long simulated position, negative is a net short simulated
      position. Zero is **not** a valid stored position — a symbol with
      no net position is represented by absence from the
      :class:`SimulatedPortfolio` (canonical form). ``bool`` values
      (a subclass of ``int``) are rejected.

    The position carries no price, no cost basis, no P&L, no currency,
    no venue, no account, and no broker handle. It is pure signed-integer
    bookkeeping.
    """

    symbol: str
    net_quantity: int

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not self.symbol:
            raise ValueError("SimulatedPosition.symbol must be a non-empty str")
        if any(ch.isspace() for ch in self.symbol):
            raise ValueError("SimulatedPosition.symbol must not contain whitespace")
        if isinstance(self.net_quantity, bool) or not isinstance(self.net_quantity, int):
            raise TypeError("SimulatedPosition.net_quantity must be an int (not bool, not float)")
        if self.net_quantity == 0:
            raise ValueError(
                "SimulatedPosition.net_quantity must be non-zero; a flat symbol is "
                "represented by absence from the SimulatedPortfolio"
            )


@dataclass(frozen=True, slots=True)
class SimulatedPortfolio:
    """Immutable deterministic in-memory simulated portfolio snapshot.

    Two fields, both stored in canonical form so that two snapshots are
    equal exactly when they hold the same positions and have applied the
    same intent IDs:

    - ``positions``: tuple of :class:`SimulatedPosition`, sorted by
      ``symbol`` ascending, with unique symbols and no zero-quantity
      entries. Represents the position book keyed by symbol.
    - ``applied_intent_ids``: tuple of the P6-04 simulated order intent
      IDs already applied, sorted ascending and unique. This is the
      value-typed dedup structure that makes
      :func:`apply_simulated_order_intent` idempotent.

    The snapshot is frozen and slotted; it is replaced, never mutated.
    It is hashable because both fields are tuples of hashable values.
    """

    positions: tuple[SimulatedPosition, ...]
    applied_intent_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.positions, tuple):
            raise TypeError(
                f"SimulatedPortfolio.positions must be a tuple, got {type(self.positions).__name__}"
            )
        seen_symbols: set[str] = set()
        for position in self.positions:
            if not isinstance(position, SimulatedPosition):
                raise TypeError(
                    f"SimulatedPortfolio.positions members must be SimulatedPosition, "
                    f"got {type(position).__name__}"
                )
            if position.symbol in seen_symbols:
                raise ValueError(
                    f"SimulatedPortfolio.positions must have unique symbols; "
                    f"{position.symbol!r} appears more than once"
                )
            seen_symbols.add(position.symbol)
        if list(self.positions) != sorted(self.positions, key=lambda p: p.symbol):
            raise ValueError("SimulatedPortfolio.positions must be sorted by symbol ascending")

        if not isinstance(self.applied_intent_ids, tuple):
            raise TypeError(
                f"SimulatedPortfolio.applied_intent_ids must be a tuple, "
                f"got {type(self.applied_intent_ids).__name__}"
            )
        seen_ids: set[str] = set()
        for intent_id in self.applied_intent_ids:
            if not isinstance(intent_id, str) or not intent_id:
                raise ValueError(
                    "SimulatedPortfolio.applied_intent_ids members must be non-empty str"
                )
            if intent_id in seen_ids:
                raise ValueError(
                    f"SimulatedPortfolio.applied_intent_ids must be unique; "
                    f"{intent_id!r} appears more than once"
                )
            seen_ids.add(intent_id)
        if list(self.applied_intent_ids) != sorted(self.applied_intent_ids):
            raise ValueError("SimulatedPortfolio.applied_intent_ids must be sorted ascending")

    @classmethod
    def empty(cls) -> SimulatedPortfolio:
        """Return the canonical empty snapshot (no positions, no applied IDs)."""
        return cls(positions=(), applied_intent_ids=())

    def net_quantity(self, symbol: str) -> int:
        """Return the signed net quantity held in ``symbol`` (0 if absent)."""
        if not isinstance(symbol, str) or not symbol:
            raise ValueError("symbol must be a non-empty str")
        for position in self.positions:
            if position.symbol == symbol:
                return position.net_quantity
        return 0

    def has_applied(self, intent_id: str) -> bool:
        """Return ``True`` if ``intent_id`` has already been applied to this snapshot."""
        if not isinstance(intent_id, str) or not intent_id:
            raise ValueError("intent_id must be a non-empty str")
        return intent_id in self.applied_intent_ids


def _signed_delta(order_intent: SimulatedOrderIntent) -> int:
    """Return the deterministic signed position delta for a full fill.

    ``BUY`` adds the full intent quantity; ``SELL`` subtracts it. This is
    the fixed, fixture-only full-fill assumption — no fill price, no
    partial fill, no fill engine.
    """
    if order_intent.side is SimulatedOrderSide.BUY:
        return order_intent.quantity
    return -order_intent.quantity


def _positions_with_delta(
    positions: tuple[SimulatedPosition, ...],
    symbol: str,
    delta: int,
) -> tuple[SimulatedPosition, ...]:
    """Return a new canonical positions tuple with ``delta`` applied to ``symbol``.

    A symbol whose net quantity reaches zero is dropped. The result is
    sorted by symbol ascending. The input tuple is not mutated.
    """
    updated: list[SimulatedPosition] = []
    found = False
    for position in positions:
        if position.symbol == symbol:
            found = True
            new_quantity = position.net_quantity + delta
            if new_quantity != 0:
                updated.append(SimulatedPosition(symbol=symbol, net_quantity=new_quantity))
        else:
            updated.append(position)
    if not found and delta != 0:
        updated.append(SimulatedPosition(symbol=symbol, net_quantity=delta))
    updated.sort(key=lambda p: p.symbol)
    return tuple(updated)


def apply_simulated_order_intent(
    portfolio: SimulatedPortfolio,
    *,
    decision: PositionDecision,
    order_intent: SimulatedOrderIntent,
) -> SimulatedPortfolio:
    """Apply an accepted simulated order intent to ``portfolio``.

    Pure, deterministic transformation. Returns a new
    :class:`SimulatedPortfolio` reflecting the applied position change, or
    the supplied ``portfolio`` unchanged (by identity) when the intent is
    not applied. Does not mutate any input. Has no side effects.

    The intent is applied **only** when both:

    1. ``decision.outcome`` is
       :attr:`~gmc_rebuild.decision.PositionDecisionOutcome.WOULD_TRADE`
       (an accepted decision); and
    2. ``order_intent.intent_id`` has not already been applied to
       ``portfolio`` (idempotent dedup keyed on the deterministic P6-04
       simulated order intent ID).

    When applied, the symbol's signed net quantity changes by the full
    intent quantity (``+quantity`` for ``BUY``, ``-quantity`` for
    ``SELL``) under the fixed fixture-only full-fill assumption, and the
    intent ID is recorded. A non-accepted decision (any
    ``WOULD_SKIP`` outcome) or an already-applied intent ID is a no-op:
    the supplied ``portfolio`` is returned by identity.

    :raises TypeError: if ``portfolio`` is not a
        :class:`SimulatedPortfolio`, ``decision`` is not a
        :class:`~gmc_rebuild.decision.PositionDecision`, or
        ``order_intent`` is not a
        :class:`~gmc_rebuild.simulation.SimulatedOrderIntent`.
    """
    if not isinstance(portfolio, SimulatedPortfolio):
        raise TypeError(f"portfolio must be a SimulatedPortfolio, got {type(portfolio).__name__}")
    if not isinstance(decision, PositionDecision):
        raise TypeError(f"decision must be a PositionDecision, got {type(decision).__name__}")
    if not isinstance(order_intent, SimulatedOrderIntent):
        raise TypeError(
            f"order_intent must be a SimulatedOrderIntent, got {type(order_intent).__name__}"
        )

    # Non-accepted decision: no position change. Return unchanged by identity.
    if decision.outcome is not PositionDecisionOutcome.WOULD_TRADE:
        return portfolio

    # Idempotent dedup keyed on the deterministic P6-04 intent ID.
    if order_intent.intent_id in portfolio.applied_intent_ids:
        return portfolio

    delta = _signed_delta(order_intent)
    new_positions = _positions_with_delta(portfolio.positions, order_intent.symbol, delta)
    new_applied = (*portfolio.applied_intent_ids, order_intent.intent_id)
    return SimulatedPortfolio(
        positions=new_positions,
        applied_intent_ids=tuple(sorted(new_applied)),
    )


__all__ = [
    "SimulatedPortfolio",
    "SimulatedPosition",
    "apply_simulated_order_intent",
]
