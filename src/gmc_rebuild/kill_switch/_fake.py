"""In-memory ``KillSwitchProtocol`` fake (P3-04 test-fixture support).

Pure-Python, deterministic, in-memory fake implementation of
:class:`gmc_rebuild.risk.KillSwitchProtocol` (ADR-002). The sole
intended consumer is the test suite under ``tests/kill_switch/``.

See :mod:`gmc_rebuild.kill_switch` for the full design constraints.
In particular: no I/O, no network, no ``time.sleep``, no
``os.environ`` / ``os.getenv``, no broker SDK, no scheduler / daemon /
background thread, no ``__main__`` entry point, no runtime consumer,
no order placement, no broker activity.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from gmc_rebuild.risk import (
    KillSwitchDecision,
    KillSwitchState,
    RiskControlError,
    to_utc_string,
)
from gmc_rebuild.time import ensure_utc


class InMemoryKillSwitch:
    """Deterministic in-memory fake conforming to ``KillSwitchProtocol``.

    The fake stores at most one active trip and a fixed in-memory
    ``observed_at`` clock. It conforms structurally to
    :class:`gmc_rebuild.risk.KillSwitchProtocol`, so
    ``isinstance(fake, KillSwitchProtocol)`` is ``True``.

    A freshly constructed fake is :attr:`KillSwitchState.ARMED`. Once
    :meth:`trip` is called with a non-empty ``reason`` and
    ``triggered_by``, the fake records that trip and subsequent calls to
    :meth:`current` return :attr:`KillSwitchState.TRIPPED` with the same
    ``reason`` / ``triggered_by`` until the test suite tears the fake
    down. There is no auto-reset, no clear API, no broker-side effect,
    and no order-placement consequence. The clock is fixed at
    construction and advances only via the explicit :meth:`advance`
    helper; there is no wall-clock read, no ``time.sleep``, no
    scheduler, no background activity.
    """

    __slots__ = ("_observed_at", "_trip")

    def __init__(self, observed_at: datetime) -> None:
        self._observed_at: datetime = ensure_utc(observed_at)
        self._trip: KillSwitchDecision | None = None

    def advance(self, seconds: float) -> None:
        """Advance the in-memory clock by ``seconds`` (must be non-negative)."""
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
            raise RiskControlError("InMemoryKillSwitch.advance seconds must be a number")
        if seconds < 0:
            raise RiskControlError("InMemoryKillSwitch.advance seconds must be non-negative")
        self._observed_at = self._observed_at + timedelta(seconds=float(seconds))

    def current(self) -> KillSwitchDecision:
        """Return the current :class:`KillSwitchDecision`.

        Conforms to :class:`gmc_rebuild.risk.KillSwitchProtocol.current`:
        steady-state callers do not see exceptions. When no trip has
        been recorded, the decision is ``ARMED`` with empty
        ``reason`` / ``triggered_by``; when a trip is active, the
        decision restates the recorded ``reason`` / ``triggered_by``
        with the current ``observed_at`` clock value.
        """
        if self._trip is None:
            return KillSwitchDecision(
                state=KillSwitchState.ARMED,
                observed_at=to_utc_string(self._observed_at),
                reason="",
                triggered_by="",
            )
        return KillSwitchDecision(
            state=KillSwitchState.TRIPPED,
            observed_at=to_utc_string(self._observed_at),
            reason=self._trip.reason,
            triggered_by=self._trip.triggered_by,
        )

    def trip(self, *, reason: str, triggered_by: str) -> KillSwitchDecision:
        """Record an active trip with ``reason`` / ``triggered_by``.

        Conforms to :class:`gmc_rebuild.risk.KillSwitchProtocol.trip`:
        ``reason`` and ``triggered_by`` must be non-empty strings.
        Subsequent calls to :meth:`current` return
        :attr:`KillSwitchState.TRIPPED` with the recorded values until
        the fake is discarded. There is no clear / reset API on the
        fake: ADR-002's reset workflow is out of scope for this
        test-fixture artifact.
        """
        if not isinstance(reason, str) or not reason:
            raise RiskControlError("InMemoryKillSwitch.trip reason must be a non-empty str")
        if not isinstance(triggered_by, str) or not triggered_by:
            raise RiskControlError("InMemoryKillSwitch.trip triggered_by must be a non-empty str")
        decision = KillSwitchDecision(
            state=KillSwitchState.TRIPPED,
            observed_at=to_utc_string(self._observed_at),
            reason=reason,
            triggered_by=triggered_by,
        )
        self._trip = decision
        return decision


__all__ = ["InMemoryKillSwitch"]
