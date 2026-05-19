"""P6-01 typed signal-intake boundary — internal module.

Defines the closed :class:`SignalSide` enumeration, the frozen, slotted
:class:`SignalIntent` dataclass, and the pure :func:`accept_signal_intent`
acceptance function authorized by PR P6-01 (see
``governance/authorizations/2026-05-19_p6-01.md``).

Design constraints — these are governance constraints, not stylistic
preferences:

- **No runtime activation.** No ``__main__`` entry point, no daemon, no
  scheduler, no background thread, no long-running service.
- **No external I/O.** No filesystem, no network, no broker SDK, no
  ``time.sleep``, no ``os.environ`` / ``os.getenv`` reads.
- **No strategy logic.** A signal intent is a structured record of a
  *candidate* trade idea supplied by an external caller. This module
  does not decide what to trade, does not generate signals, does not
  scan markets, does not fetch data, and does not validate symbols
  against any external universe.
- **No order placement.** A :class:`SignalIntent` is upstream of any
  order; it carries no venue, account, broker, fill, position, or
  execution information.
- **No persistence.** Nothing on this module writes to disk, opens a
  database, or maintains any cache.
- **No re-export from package root.** :mod:`gmc_rebuild` is unchanged
  by this packet; this subpackage exposes its public surface only
  through ``from gmc_rebuild.signal_intake import ...``.
- **ADR-004 UTC discipline applies to any future timestamp field.**
  This packet introduces no timestamp field; the dataclass shape is
  the closed five-field set documented below.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SignalSide(StrEnum):
    """Closed set of candidate-trade-idea sides accepted by the boundary.

    The set is deliberately minimal — ``BUY`` and ``SELL`` only. Extending
    this enumeration requires a separate written authorization from Kevin
    per ``AI_WORKFLOW.md`` §7. Short-sale, cover, exit, and other venue-
    or strategy-specific sides are out of scope for the P6-01 boundary.
    """

    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True, slots=True)
class SignalIntent:
    """Structured record of a candidate trade idea.

    A :class:`SignalIntent` describes *what* a caller proposes to consider
    trading. It does not authorize, route, or place any order; it does not
    fetch market data; it does not commit to any execution decision. The
    boundary that accepts it (:func:`accept_signal_intent`) returns the
    intent unchanged on success and raises on validation failure.

    The five-field shape is closed. Adding, removing, or renaming a field
    requires a separate written authorization.

    Validation (enforced at construction via :meth:`__post_init__`):

    - ``intent_id`` must be a non-empty :class:`str`.
    - ``symbol`` must be a non-empty :class:`str`.
    - ``side`` must be a :class:`SignalSide` member.
    - ``quantity`` must be a positive :class:`int`. :class:`bool` is
      rejected (Python treats ``bool`` as a subclass of ``int``; the
      boundary rejects it explicitly so that ``True`` / ``False`` are not
      silently accepted as quantities).
    - ``rationale`` must be a non-empty :class:`str`.
    """

    intent_id: str
    symbol: str
    side: SignalSide
    quantity: int
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.intent_id, str):
            raise TypeError(f"intent_id must be a str, got {type(self.intent_id).__name__}")
        if not self.intent_id:
            raise ValueError("intent_id must be a non-empty string")
        if not isinstance(self.symbol, str):
            raise TypeError(f"symbol must be a str, got {type(self.symbol).__name__}")
        if not self.symbol:
            raise ValueError("symbol must be a non-empty string")
        if not isinstance(self.side, SignalSide):
            raise TypeError(f"side must be a SignalSide member, got {type(self.side).__name__}")
        # Reject bool explicitly: bool is a subclass of int in Python, so a
        # naive isinstance(quantity, int) check would accept True / False.
        if isinstance(self.quantity, bool) or not isinstance(self.quantity, int):
            raise TypeError(f"quantity must be an int, got {type(self.quantity).__name__}")
        if self.quantity <= 0:
            raise ValueError(f"quantity must be a positive integer, got {self.quantity}")
        if not isinstance(self.rationale, str):
            raise TypeError(f"rationale must be a str, got {type(self.rationale).__name__}")
        if not self.rationale:
            raise ValueError("rationale must be a non-empty string")


def accept_signal_intent(intent: SignalIntent) -> SignalIntent:
    """Accept a candidate :class:`SignalIntent` and return it unchanged.

    This is the typed entry point of the P6-01 signal-intake boundary.
    It performs one check — that ``intent`` is a :class:`SignalIntent`
    instance — and returns the supplied object by identity on success.
    Field-level validation is enforced by :class:`SignalIntent` itself
    at construction time and is not re-run here; an invalid
    :class:`SignalIntent` cannot exist as a constructed object.

    The function has no side effects: no logging, no audit-event emit,
    no filesystem write, no network call, no env-var read, no scheduler,
    no broker call. Callers needing to record the acceptance of a signal
    intent must do so explicitly via the merged
    ``gmc_rebuild.logging.audit_event`` helper.

    :raises TypeError: if ``intent`` is not a :class:`SignalIntent`.
    """
    if not isinstance(intent, SignalIntent):
        raise TypeError(f"intent must be a SignalIntent, got {type(intent).__name__}")
    return intent
