"""P6-02 eligibility-check pure functions — internal module.

Defines the closed :class:`EligibilityOutcome` and :class:`EligibilityReason`
enumerations, the frozen, slotted :class:`EligibilityConfig` configuration
slice, the frozen, slotted :class:`EligibilityDecision` result, and the
pure :func:`check_eligibility` function authorized by PR P6-02 (see
``governance/authorizations/2026-05-19_p6-02.md``).

Design constraints — these are governance constraints, not stylistic
preferences:

- **No runtime activation.** No ``__main__`` entry point, no daemon, no
  scheduler, no background thread, no long-running service.
- **No external I/O.** No filesystem, no network, no broker SDK, no
  ``time.sleep``, no ``os.environ`` / ``os.getenv`` reads, no real
  external symbol allow/deny list — the entire allowed-symbols set is
  supplied by the caller via :class:`EligibilityConfig`.
- **No external config loading.** This module does not import
  :mod:`gmc_rebuild.config` or any other configuration source; the
  caller is responsible for constructing the :class:`EligibilityConfig`
  slice and passing it in.
- **No strategy logic.** Eligibility is a structural pre-filter
  operating only on the supplied :class:`SignalIntent` plus the
  supplied :class:`EligibilityConfig`. It does not decide what to
  trade; it decides whether the upstream caller's signal is
  structurally permitted by the caller's own config slice.
- **No mutation of inputs.** :func:`check_eligibility` does not
  modify the supplied :class:`SignalIntent` or
  :class:`EligibilityConfig`. Both are frozen / immutable.
- **No re-export from package root.** :mod:`gmc_rebuild` is unchanged
  by this packet; this subpackage exposes its public surface only
  through ``from gmc_rebuild.eligibility import ...``.
- **Closed enumerations.** :class:`EligibilityOutcome` has exactly two
  members (``ELIGIBLE``, ``INELIGIBLE``). :class:`EligibilityReason`
  has exactly five members enumerating the structural checks the
  function performs. Extending either requires a separate written
  authorization per ``AI_WORKFLOW.md`` §7.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from gmc_rebuild.signal_intake import SignalIntent, SignalSide


class EligibilityOutcome(StrEnum):
    """Closed set of decision outcomes returned by the eligibility check.

    Two members only. ``ELIGIBLE`` means the supplied
    :class:`~gmc_rebuild.signal_intake.SignalIntent` passed every check
    against the supplied :class:`EligibilityConfig`; the returned
    :class:`EligibilityDecision` carries an empty ``reasons`` tuple.
    ``INELIGIBLE`` means at least one check failed; the ``reasons``
    tuple is non-empty and lists every failing reason in the canonical
    declaration order of :class:`EligibilityReason`.
    """

    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"


class EligibilityReason(StrEnum):
    """Closed set of ineligibility reason codes returned by the check.

    Exactly five members. The order below is the canonical declaration
    order used to sort the ``reasons`` tuple on an ineligible decision.
    Extending this enumeration requires a separate written authorization
    per ``AI_WORKFLOW.md`` §7.
    """

    SYMBOL_NOT_ALLOWED = "SYMBOL_NOT_ALLOWED"
    SIDE_NOT_PERMITTED = "SIDE_NOT_PERMITTED"
    QUANTITY_BELOW_MINIMUM = "QUANTITY_BELOW_MINIMUM"
    QUANTITY_ABOVE_MAXIMUM = "QUANTITY_ABOVE_MAXIMUM"
    RATIONALE_TOO_SHORT = "RATIONALE_TOO_SHORT"


# Canonical ordering used to sort the reasons tuple on an INELIGIBLE
# decision. Keeping this as a module-level tuple — rather than relying
# on dict / set iteration — makes the determinism invariant explicit.
_REASON_ORDER: tuple[EligibilityReason, ...] = (
    EligibilityReason.SYMBOL_NOT_ALLOWED,
    EligibilityReason.SIDE_NOT_PERMITTED,
    EligibilityReason.QUANTITY_BELOW_MINIMUM,
    EligibilityReason.QUANTITY_ABOVE_MAXIMUM,
    EligibilityReason.RATIONALE_TOO_SHORT,
)


@dataclass(frozen=True, slots=True)
class EligibilityConfig:
    """Caller-supplied configuration slice for the eligibility check.

    All five fields are required and supplied explicitly by the caller.
    No field is loaded from an environment variable, a file, or any
    other external source by this module; this is a structural slice,
    not a configuration loader.

    Fields:

    - ``allowed_symbols``: frozenset of allowed symbol strings. An
      empty set is permitted and means no symbol is allowed; every
      :class:`~gmc_rebuild.signal_intake.SignalIntent` will then be
      rejected with :attr:`EligibilityReason.SYMBOL_NOT_ALLOWED`.
    - ``allowed_sides``: frozenset of allowed
      :class:`~gmc_rebuild.signal_intake.SignalSide` members. An empty
      set is permitted and means no side is allowed.
    - ``min_quantity``: minimum allowed positive integer quantity.
      Must be a positive :class:`int`; ``bool`` is rejected.
    - ``max_quantity``: maximum allowed positive integer quantity.
      Must be a positive :class:`int` and at least ``min_quantity``;
      ``bool`` is rejected.
    - ``min_rationale_length``: minimum allowed length of the
      ``rationale`` string. Must be a non-negative :class:`int`;
      ``bool`` is rejected. ``0`` means any non-empty rationale passes
      (a non-empty rationale is already required by the upstream
      :class:`SignalIntent` boundary).
    """

    allowed_symbols: frozenset[str]
    allowed_sides: frozenset[SignalSide]
    min_quantity: int
    max_quantity: int
    min_rationale_length: int

    def __post_init__(self) -> None:
        if not isinstance(self.allowed_symbols, frozenset):
            raise TypeError(
                f"allowed_symbols must be a frozenset, got {type(self.allowed_symbols).__name__}"
            )
        for symbol in self.allowed_symbols:
            if not isinstance(symbol, str):
                raise TypeError(f"allowed_symbols members must be str, got {type(symbol).__name__}")
            if not symbol:
                raise ValueError("allowed_symbols must not contain empty strings")
        if not isinstance(self.allowed_sides, frozenset):
            raise TypeError(
                f"allowed_sides must be a frozenset, got {type(self.allowed_sides).__name__}"
            )
        for side in self.allowed_sides:
            if not isinstance(side, SignalSide):
                raise TypeError(
                    f"allowed_sides members must be SignalSide, got {type(side).__name__}"
                )
        if isinstance(self.min_quantity, bool) or not isinstance(self.min_quantity, int):
            raise TypeError(f"min_quantity must be an int, got {type(self.min_quantity).__name__}")
        if self.min_quantity <= 0:
            raise ValueError(f"min_quantity must be a positive integer, got {self.min_quantity}")
        if isinstance(self.max_quantity, bool) or not isinstance(self.max_quantity, int):
            raise TypeError(f"max_quantity must be an int, got {type(self.max_quantity).__name__}")
        if self.max_quantity <= 0:
            raise ValueError(f"max_quantity must be a positive integer, got {self.max_quantity}")
        if self.max_quantity < self.min_quantity:
            raise ValueError(
                f"max_quantity ({self.max_quantity}) must be at least "
                f"min_quantity ({self.min_quantity})"
            )
        if isinstance(self.min_rationale_length, bool) or not isinstance(
            self.min_rationale_length, int
        ):
            raise TypeError(
                f"min_rationale_length must be an int, "
                f"got {type(self.min_rationale_length).__name__}"
            )
        if self.min_rationale_length < 0:
            raise ValueError(
                f"min_rationale_length must be non-negative, got {self.min_rationale_length}"
            )


@dataclass(frozen=True, slots=True)
class EligibilityDecision:
    """Result of an eligibility check.

    Two fields:

    - ``outcome``: :class:`EligibilityOutcome` member.
    - ``reasons``: tuple of :class:`EligibilityReason` members. Empty
      when ``outcome`` is :attr:`EligibilityOutcome.ELIGIBLE`;
      non-empty and sorted in the canonical declaration order of
      :class:`EligibilityReason` when ``outcome`` is
      :attr:`EligibilityOutcome.INELIGIBLE`.

    The biconditional ``outcome == EligibilityOutcome.ELIGIBLE iff
    reasons == ()`` is enforced at construction.
    """

    outcome: EligibilityOutcome
    reasons: tuple[EligibilityReason, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, EligibilityOutcome):
            raise TypeError(
                f"outcome must be an EligibilityOutcome, got {type(self.outcome).__name__}"
            )
        if not isinstance(self.reasons, tuple):
            raise TypeError(f"reasons must be a tuple, got {type(self.reasons).__name__}")
        for reason in self.reasons:
            if not isinstance(reason, EligibilityReason):
                raise TypeError(
                    f"reasons members must be EligibilityReason, got {type(reason).__name__}"
                )
        # Biconditional: ELIGIBLE iff reasons is empty.
        if self.outcome is EligibilityOutcome.ELIGIBLE and self.reasons:
            raise ValueError("EligibilityDecision with outcome=ELIGIBLE must have empty reasons")
        if self.outcome is EligibilityOutcome.INELIGIBLE and not self.reasons:
            raise ValueError(
                "EligibilityDecision with outcome=INELIGIBLE must have non-empty reasons"
            )


def check_eligibility(intent: SignalIntent, config: EligibilityConfig) -> EligibilityDecision:
    """Decide whether ``intent`` is structurally eligible under ``config``.

    Pure function. Runs every check unconditionally and returns an
    :class:`EligibilityDecision` carrying every failing reason in the
    canonical declaration order of :class:`EligibilityReason`. Does not
    mutate ``intent`` or ``config``. Has no side effects.

    :raises TypeError: if ``intent`` is not a
        :class:`~gmc_rebuild.signal_intake.SignalIntent` or ``config``
        is not an :class:`EligibilityConfig`.
    """
    if not isinstance(intent, SignalIntent):
        raise TypeError(f"intent must be a SignalIntent, got {type(intent).__name__}")
    if not isinstance(config, EligibilityConfig):
        raise TypeError(f"config must be an EligibilityConfig, got {type(config).__name__}")

    failing: set[EligibilityReason] = set()
    if intent.symbol not in config.allowed_symbols:
        failing.add(EligibilityReason.SYMBOL_NOT_ALLOWED)
    if intent.side not in config.allowed_sides:
        failing.add(EligibilityReason.SIDE_NOT_PERMITTED)
    if intent.quantity < config.min_quantity:
        failing.add(EligibilityReason.QUANTITY_BELOW_MINIMUM)
    if intent.quantity > config.max_quantity:
        failing.add(EligibilityReason.QUANTITY_ABOVE_MAXIMUM)
    if len(intent.rationale) < config.min_rationale_length:
        failing.add(EligibilityReason.RATIONALE_TOO_SHORT)

    if not failing:
        return EligibilityDecision(
            outcome=EligibilityOutcome.ELIGIBLE,
            reasons=(),
        )
    ordered = tuple(reason for reason in _REASON_ORDER if reason in failing)
    return EligibilityDecision(
        outcome=EligibilityOutcome.INELIGIBLE,
        reasons=ordered,
    )
