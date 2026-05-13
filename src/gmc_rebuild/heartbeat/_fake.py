"""In-memory ``HeartbeatProtocol`` fake (P3-03 test-fixture support).

Pure-Python, deterministic, in-memory fake implementation of
:class:`gmc_rebuild.risk.HeartbeatProtocol` (ADR-005). The sole intended
consumer is the test suite under ``tests/heartbeat/``.

See :mod:`gmc_rebuild.heartbeat` for the full design constraints. In
particular: no I/O, no network, no ``time.sleep``, no ``os.environ`` /
``os.getenv``, no broker SDK, no scheduler / daemon / background
thread, no ``__main__`` entry point, no runtime consumer.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from gmc_rebuild.risk import (
    HeartbeatRecord,
    HeartbeatStatus,
    RiskControlError,
    to_utc_string,
)
from gmc_rebuild.time import ensure_utc

DEFAULT_STALENESS_SECONDS: float = 8 * 3600.0
"""ADR-005 default operator-heartbeat staleness threshold (8 hours)."""


class InMemoryHeartbeat:
    """Deterministic in-memory fake conforming to ``HeartbeatProtocol``.

    The fake stores last-update timestamps per component and computes
    staleness against a fixed in-memory ``observed_at`` clock and a
    configurable threshold (default: ADR-005's 8 hours). It conforms
    structurally to :class:`gmc_rebuild.risk.HeartbeatProtocol`, so
    ``isinstance(fake, HeartbeatProtocol)`` is ``True``.

    Unknown components report :attr:`HeartbeatStatus.STALE`, preserving
    ADR-005's "safe default is paused" property.

    The clock is fixed at construction and only advances via the
    explicit :meth:`advance` helper; there is no wall-clock read, no
    ``time.sleep``, no scheduler, no background activity.
    """

    __slots__ = ("_last_updates", "_observed_at", "_threshold")

    def __init__(
        self,
        observed_at: datetime,
        threshold_seconds: float = DEFAULT_STALENESS_SECONDS,
    ) -> None:
        observed = ensure_utc(observed_at)
        if isinstance(threshold_seconds, bool) or not isinstance(threshold_seconds, (int, float)):
            raise RiskControlError("InMemoryHeartbeat.threshold_seconds must be a number")
        if threshold_seconds <= 0:
            raise RiskControlError("InMemoryHeartbeat.threshold_seconds must be positive")
        self._observed_at: datetime = observed
        self._threshold: float = float(threshold_seconds)
        self._last_updates: dict[str, datetime] = {}

    def advance(self, seconds: float) -> None:
        """Advance the in-memory clock by ``seconds`` (must be non-negative)."""
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
            raise RiskControlError("InMemoryHeartbeat.advance seconds must be a number")
        if seconds < 0:
            raise RiskControlError("InMemoryHeartbeat.advance seconds must be non-negative")
        self._observed_at = self._observed_at + timedelta(seconds=float(seconds))

    def beat(self, component: str, when: datetime) -> None:
        """Record a heartbeat for ``component`` at ``when`` (UTC datetime)."""
        if not isinstance(component, str) or not component:
            raise RiskControlError("InMemoryHeartbeat.beat component must be a non-empty str")
        if any(ch.isspace() for ch in component):
            raise RiskControlError("InMemoryHeartbeat.beat component must not contain whitespace")
        self._last_updates[component] = ensure_utc(when)

    def status(self, component: str) -> HeartbeatRecord:
        """Return the current :class:`HeartbeatRecord` for ``component``.

        Conforms to :class:`gmc_rebuild.risk.HeartbeatProtocol.status`:
        unknown components return ``status=STALE`` rather than raising.
        """
        if not isinstance(component, str) or not component:
            raise RiskControlError("InMemoryHeartbeat.status component must be a non-empty str")
        if any(ch.isspace() for ch in component):
            raise RiskControlError("InMemoryHeartbeat.status component must not contain whitespace")

        last = self._last_updates.get(component)
        if last is None:
            synthetic_last = self._observed_at - timedelta(seconds=self._threshold + 1.0)
            return HeartbeatRecord(
                component=component,
                status=HeartbeatStatus.STALE,
                last_update=to_utc_string(synthetic_last),
                observed_at=to_utc_string(self._observed_at),
                age_seconds=self._threshold + 1.0,
            )

        age = (self._observed_at - last).total_seconds()
        is_stale = age > self._threshold
        return HeartbeatRecord(
            component=component,
            status=HeartbeatStatus.STALE if is_stale else HeartbeatStatus.FRESH,
            last_update=to_utc_string(last),
            observed_at=to_utc_string(self._observed_at),
            age_seconds=max(0.0, age),
        )


__all__ = ["DEFAULT_STALENESS_SECONDS", "InMemoryHeartbeat"]
