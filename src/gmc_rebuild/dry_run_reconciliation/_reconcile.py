"""P6-09 deterministic in-memory read-only dry-run position reconciliation — internal module.

Defines the frozen, slotted value types and the pure
:func:`reconcile_dry_run_positions` comparison function authorized by
PR P6-09 (see ``governance/authorizations/2026-06-19_p6-09.md``).

This module performs a pure, deterministic, **read-only** comparison of
the merged P6-05 :class:`~gmc_rebuild.portfolio_state.SimulatedPortfolio`
snapshot against a caller-supplied, value-typed :class:`ExpectedPositions`
input, producing a frozen, typed :class:`DryRunReconciliationResult`. It
is the ninth Phase 6 dry-run capability.

Design constraints — these are governance constraints, not stylistic
preferences (``governance/authorizations/2026-06-19_p6-09.md``):

- **Pure / deterministic / read-only.** The comparison takes its inputs
  by value, mutates none of them, holds no hidden state, reads no clock,
  and returns the byte-for-byte identical result for identical inputs.
  Any internal ordering is canonicalized by symbol ascending.
- **Closed, value-typed surface.** Exactly five public symbols. The
  result is a frozen, slotted value object over tuples of frozen value
  types and ``StrEnum`` members — no open-ended mutable containers, no
  ``render()`` method, no human-readable string surface.
- **Reconciliation status echoed verbatim.** The caller supplies a
  :class:`~gmc_rebuild.risk.ReconciliationStatus`; it is carried onto the
  result unchanged so the ADR-003 ``UNAVAILABLE`` (no upstream data) vs
  ``FAILED`` (confirmed material mismatch) distinction is preserved
  end-to-end. This module never itself selects between those values.
- **Future-aware abstract input.** :class:`ExpectedPositions` is a plain
  frozen value object that does not know where its data came from. A
  later, separately-authorized phase could add a new constructor (e.g. a
  read-only real-account snapshot) **elsewhere** without changing this
  module. No such constructor is authorized here: the only convenience
  constructor is :meth:`ExpectedPositions.from_simulated_portfolio`,
  which derives expected positions from a merged P6-05 snapshot for
  self-comparison sanity checks.
- **No runtime activation.** No ``__main__`` entry point, no daemon, no
  scheduler, no background thread, no long-running service.
- **No external I/O.** No filesystem, no network, no broker SDK, no
  persistence, no ``time.sleep``, no ``os.environ`` / ``os.getenv``
  reads, no secrets, no ``audit_event`` emission.
- **No broker / real account.** No real account, no account identifier,
  no balances, no P&L, no cash ledger, no valuation, no broker
  reconciliation, no account sync, no market data, no order routing.
- **No ReconciliationProtocol implementation.** This module declares no
  class conforming to the abstract
  :class:`gmc_rebuild.risk.ReconciliationProtocol`, and does not import,
  re-export, or runtime-activate the merged P3-05
  ``gmc_rebuild.reconciliation`` ``InMemoryReconciliation`` fake.
- **No re-export from package root.** :mod:`gmc_rebuild` is unchanged by
  this packet; this subpackage exposes its public surface only through
  ``from gmc_rebuild.dry_run_reconciliation import ...``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from gmc_rebuild.portfolio_state import SimulatedPortfolio
from gmc_rebuild.risk import ReconciliationStatus


def _check_symbol(field_label: str, symbol: object) -> None:
    """Validate a position symbol: non-empty ``str`` with no whitespace."""
    if not isinstance(symbol, str) or not symbol:
        raise ValueError(f"{field_label} symbol must be a non-empty str")
    if any(ch.isspace() for ch in symbol):
        raise ValueError(f"{field_label} symbol must not contain whitespace")


def _check_quantity(field_label: str, quantity: object) -> None:
    """Validate a signed net quantity: ``int`` rejecting ``bool``."""
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise TypeError(f"{field_label} quantity must be an int (not bool, not float)")


def _validate_canonical_pairs(field_label: str, pairs: object) -> None:
    """Validate a canonical ``tuple[tuple[str, int], ...]``.

    Each entry is a ``(symbol, signed non-zero int quantity)`` pair; the
    tuple is sorted by symbol ascending, with unique symbols and no
    zero-quantity entries.
    """
    if not isinstance(pairs, tuple):
        raise TypeError(f"{field_label} must be a tuple, got {type(pairs).__name__}")
    seen: set[str] = set()
    for pair in pairs:
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise TypeError(f"{field_label} members must be (symbol, quantity) 2-tuples")
        symbol, quantity = pair
        _check_symbol(field_label, symbol)
        _check_quantity(field_label, quantity)
        if quantity == 0:
            raise ValueError(
                f"{field_label} quantity must be non-zero; a flat symbol is represented by absence"
            )
        if symbol in seen:
            raise ValueError(f"{field_label} must have unique symbols; {symbol!r} repeats")
        seen.add(symbol)
    if list(pairs) != sorted(pairs, key=lambda p: p[0]):
        raise ValueError(f"{field_label} must be sorted by symbol ascending")


class DryRunReconciliationOutcome(StrEnum):
    """Closed aggregate outcome of a dry-run reconciliation.

    Exactly two members:

    - ``MATCH`` — every symbol present in both snapshots agrees on signed
      net quantity, and neither snapshot carries a symbol the other lacks.
    - ``MISMATCH`` — at least one quantity mismatch or one extra symbol on
      either side.
    """

    MATCH = "MATCH"
    MISMATCH = "MISMATCH"


@dataclass(frozen=True, slots=True)
class ReconciliationQuantityMismatch:
    """Immutable per-symbol quantity-mismatch detail.

    A symbol present in both the simulated snapshot and the expected
    positions but with differing signed net quantities. Equal quantities
    are a *match*, not a mismatch, and are rejected here.

    Three fields:

    - ``symbol``: non-empty identifier with no whitespace.
    - ``simulated_quantity``: signed ``int`` from the simulated snapshot.
    - ``expected_quantity``: signed ``int`` from the expected positions.
    """

    symbol: str
    simulated_quantity: int
    expected_quantity: int

    def __post_init__(self) -> None:
        _check_symbol("ReconciliationQuantityMismatch.symbol", self.symbol)
        _check_quantity(
            "ReconciliationQuantityMismatch.simulated_quantity", self.simulated_quantity
        )
        _check_quantity("ReconciliationQuantityMismatch.expected_quantity", self.expected_quantity)
        if self.simulated_quantity == self.expected_quantity:
            raise ValueError(
                "ReconciliationQuantityMismatch requires differing quantities; "
                "equal quantities are a match, not a mismatch"
            )


@dataclass(frozen=True, slots=True)
class ExpectedPositions:
    """Immutable, value-typed expected-positions input.

    A plain frozen value object holding a single canonical
    ``positions`` tuple of ``(symbol, signed_net_quantity)`` pairs:
    sorted by symbol ascending, with unique symbols and no zero-quantity
    entries. The value object does not know whether its data came from a
    simulated portfolio, a test fixture, or (in a separately-authorized
    future phase) a read-only real-account snapshot — it is the abstract
    value-typed comparison source.
    """

    positions: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        _validate_canonical_pairs("ExpectedPositions.positions", self.positions)

    @classmethod
    def from_simulated_portfolio(cls, snapshot: SimulatedPortfolio) -> ExpectedPositions:
        """Derive :class:`ExpectedPositions` from a P6-05 snapshot.

        Convenience constructor for tests and self-comparison sanity
        checks only. Implemented in terms of the merged P6-05
        :class:`~gmc_rebuild.portfolio_state.SimulatedPortfolio` value
        object; opens no real-account / broker / live-feed path. The
        snapshot's ``positions`` are already canonical, so the derived
        tuple is canonical.
        """
        if not isinstance(snapshot, SimulatedPortfolio):
            raise TypeError(f"snapshot must be a SimulatedPortfolio, got {type(snapshot).__name__}")
        return cls(positions=tuple((p.symbol, p.net_quantity) for p in snapshot.positions))


@dataclass(frozen=True, slots=True)
class DryRunReconciliationResult:
    """Immutable, deterministic result of a dry-run reconciliation.

    Six fields, all value-typed:

    - ``outcome``: :class:`DryRunReconciliationOutcome`. Enforced
      biconditional: ``MATCH`` iff there are no quantity mismatches and no
      extra symbols on either side.
    - ``matches``: canonical ``(symbol, net_quantity)`` pairs present in
      both snapshots with equal signed net quantities.
    - ``quantity_mismatches``: canonical tuple of
      :class:`ReconciliationQuantityMismatch` records (sorted by symbol,
      unique) for symbols present in both snapshots with differing
      quantities.
    - ``only_in_simulated``: canonical ``(symbol, net_quantity)`` pairs
      present in the simulated snapshot but absent from the expected
      positions.
    - ``only_in_expected``: canonical ``(symbol, net_quantity)`` pairs
      present in the expected positions but absent from the simulated
      snapshot.
    - ``reconciliation_status``: the caller-supplied
      :class:`~gmc_rebuild.risk.ReconciliationStatus`, echoed verbatim.

    The result is frozen and slotted; it is hashable because every field
    is a tuple of hashable values or a ``StrEnum`` member.
    """

    outcome: DryRunReconciliationOutcome
    matches: tuple[tuple[str, int], ...]
    quantity_mismatches: tuple[ReconciliationQuantityMismatch, ...]
    only_in_simulated: tuple[tuple[str, int], ...]
    only_in_expected: tuple[tuple[str, int], ...]
    reconciliation_status: ReconciliationStatus

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, DryRunReconciliationOutcome):
            raise TypeError(
                f"DryRunReconciliationResult.outcome must be a DryRunReconciliationOutcome, "
                f"got {type(self.outcome).__name__}"
            )
        _validate_canonical_pairs("DryRunReconciliationResult.matches", self.matches)
        _validate_canonical_pairs(
            "DryRunReconciliationResult.only_in_simulated", self.only_in_simulated
        )
        _validate_canonical_pairs(
            "DryRunReconciliationResult.only_in_expected", self.only_in_expected
        )

        if not isinstance(self.quantity_mismatches, tuple):
            raise TypeError(
                f"DryRunReconciliationResult.quantity_mismatches must be a tuple, "
                f"got {type(self.quantity_mismatches).__name__}"
            )
        seen: set[str] = set()
        for mismatch in self.quantity_mismatches:
            if not isinstance(mismatch, ReconciliationQuantityMismatch):
                raise TypeError(
                    "DryRunReconciliationResult.quantity_mismatches members must be "
                    f"ReconciliationQuantityMismatch, got {type(mismatch).__name__}"
                )
            if mismatch.symbol in seen:
                raise ValueError(
                    "DryRunReconciliationResult.quantity_mismatches must have unique symbols; "
                    f"{mismatch.symbol!r} repeats"
                )
            seen.add(mismatch.symbol)
        if list(self.quantity_mismatches) != sorted(
            self.quantity_mismatches, key=lambda m: m.symbol
        ):
            raise ValueError(
                "DryRunReconciliationResult.quantity_mismatches must be sorted by symbol ascending"
            )

        if not isinstance(self.reconciliation_status, ReconciliationStatus):
            raise TypeError(
                "DryRunReconciliationResult.reconciliation_status must be a ReconciliationStatus, "
                f"got {type(self.reconciliation_status).__name__}"
            )

        no_differences = (
            self.quantity_mismatches == ()
            and self.only_in_simulated == ()
            and self.only_in_expected == ()
        )
        if no_differences and self.outcome is not DryRunReconciliationOutcome.MATCH:
            raise ValueError(
                "DryRunReconciliationResult.outcome must be MATCH when there are no quantity "
                "mismatches and no extra symbols on either side"
            )
        if not no_differences and self.outcome is not DryRunReconciliationOutcome.MISMATCH:
            raise ValueError(
                "DryRunReconciliationResult.outcome must be MISMATCH when there is any quantity "
                "mismatch or extra symbol on either side"
            )


def reconcile_dry_run_positions(
    *,
    simulated: SimulatedPortfolio,
    expected: ExpectedPositions,
    reconciliation_status: ReconciliationStatus,
) -> DryRunReconciliationResult:
    """Compare a simulated snapshot against expected positions.

    Pure, deterministic, read-only. Returns a
    :class:`DryRunReconciliationResult` classifying every symbol present
    in either input into ``matches``, ``quantity_mismatches``,
    ``only_in_simulated``, or ``only_in_expected``, with the aggregate
    ``outcome`` set to ``MATCH`` exactly when there are no differences.
    The supplied ``reconciliation_status`` is echoed verbatim onto the
    result. Mutates none of the inputs and has no side effects.

    :raises TypeError: if ``simulated`` is not a
        :class:`~gmc_rebuild.portfolio_state.SimulatedPortfolio`,
        ``expected`` is not an :class:`ExpectedPositions`, or
        ``reconciliation_status`` is not a
        :class:`~gmc_rebuild.risk.ReconciliationStatus`.
    """
    if not isinstance(simulated, SimulatedPortfolio):
        raise TypeError(f"simulated must be a SimulatedPortfolio, got {type(simulated).__name__}")
    if not isinstance(expected, ExpectedPositions):
        raise TypeError(f"expected must be an ExpectedPositions, got {type(expected).__name__}")
    if not isinstance(reconciliation_status, ReconciliationStatus):
        raise TypeError(
            "reconciliation_status must be a ReconciliationStatus, "
            f"got {type(reconciliation_status).__name__}"
        )

    simulated_quantities = {
        position.symbol: position.net_quantity for position in simulated.positions
    }
    expected_quantities = {symbol: quantity for symbol, quantity in expected.positions}

    matches: list[tuple[str, int]] = []
    quantity_mismatches: list[ReconciliationQuantityMismatch] = []
    only_in_simulated: list[tuple[str, int]] = []
    only_in_expected: list[tuple[str, int]] = []

    for symbol in sorted(simulated_quantities.keys() | expected_quantities.keys()):
        in_simulated = symbol in simulated_quantities
        in_expected = symbol in expected_quantities
        if in_simulated and in_expected:
            simulated_quantity = simulated_quantities[symbol]
            expected_quantity = expected_quantities[symbol]
            if simulated_quantity == expected_quantity:
                matches.append((symbol, simulated_quantity))
            else:
                quantity_mismatches.append(
                    ReconciliationQuantityMismatch(
                        symbol=symbol,
                        simulated_quantity=simulated_quantity,
                        expected_quantity=expected_quantity,
                    )
                )
        elif in_simulated:
            only_in_simulated.append((symbol, simulated_quantities[symbol]))
        else:
            only_in_expected.append((symbol, expected_quantities[symbol]))

    no_differences = not quantity_mismatches and not only_in_simulated and not only_in_expected
    outcome = (
        DryRunReconciliationOutcome.MATCH
        if no_differences
        else DryRunReconciliationOutcome.MISMATCH
    )

    return DryRunReconciliationResult(
        outcome=outcome,
        matches=tuple(matches),
        quantity_mismatches=tuple(quantity_mismatches),
        only_in_simulated=tuple(only_in_simulated),
        only_in_expected=tuple(only_in_expected),
        reconciliation_status=reconciliation_status,
    )


__all__ = [
    "DryRunReconciliationOutcome",
    "DryRunReconciliationResult",
    "ExpectedPositions",
    "ReconciliationQuantityMismatch",
    "reconcile_dry_run_positions",
]
