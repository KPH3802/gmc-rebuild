"""Risk-control interfaces (P2-05).

Defines the abstract :class:`typing.Protocol` boundaries and supporting
frozen dataclasses that future Phase 2 / Phase 3 risk-control code will
implement. The implementation here is intentionally interface-only —
protocols, immutable record types, and string-enum status types — with
no runtime side effects.

Design constraints, mirrored from
``governance/authorizations/2026-05-12_p2-05.md``:

- No broker, account, or execution logic; no broker SDK, no order
  objects, no order placement.
- No env-var reads, no filesystem I/O, no network calls, no external
  sinks, no schedulers, no background jobs, no ``__main__`` entry point.
- Timestamps come from :mod:`gmc_rebuild.time` so ADR-004's UTC discipline
  is enforced at the risk-control boundary.
- The runtime package exports **types and abstract boundaries only**.
  Concrete implementations (including the SQLite-backed kill switch from
  ADR-002 and the operator heartbeat from ADR-005) require separate
  authorization and live elsewhere; test-only fakes live under
  ``tests/``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable

from gmc_rebuild.time import ensure_utc, format_utc


class RiskControlError(ValueError):
    """Raised when a risk-control record is constructed with invalid input.

    Subclass of ``ValueError`` so callers can catch it alongside other
    bad-input cases while still distinguishing risk-control shape
    violations by type.
    """


class KillSwitchState(str, Enum):
    """Allowed kill-switch states.

    ``ARMED`` — no active trip; future runtime is permitted to trade
    subject to the other risk controls.
    ``TRIPPED`` — at least one active trip record is present; future
    runtime must enter the safe state per ADR-002.
    """

    ARMED = "armed"
    TRIPPED = "tripped"


class ReconciliationStatus(str, Enum):
    """Allowed reconciliation outcomes.

    ``CLEAN`` — expected and observed values agree within tolerance.
    ``WARNING`` — values disagree but inside an advisory band; no
    automatic kill-switch trip.
    ``FAILED`` — material mismatch confirmed per ADR-003; future runtime
    must trip the kill switch.
    ``UNAVAILABLE`` — observed values could not be obtained (e.g.
    upstream outage); explicitly distinct from a confirmed disagreement.
    """

    CLEAN = "clean"
    WARNING = "warning"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


class HeartbeatStatus(str, Enum):
    """Allowed heartbeat statuses.

    ``FRESH`` — last update is within the configured staleness window.
    ``STALE`` — last update is older than the window; ADR-005 requires
    the future runtime to enter the safe state.
    """

    FRESH = "fresh"
    STALE = "stale"


@dataclass(frozen=True, slots=True)
class KillSwitchDecision:
    """Immutable description of a kill-switch decision at a point in time.

    Fields:

    - ``state``: :class:`KillSwitchState` — armed or tripped.
    - ``observed_at``: ISO-8601 UTC string with ``Z`` suffix (ADR-004).
    - ``reason``: short human-readable explanation; empty string when
      ``state`` is :attr:`KillSwitchState.ARMED`.
    - ``triggered_by``: identifier of the actor that tripped the switch,
      or empty string when armed.
    """

    state: KillSwitchState
    observed_at: str
    reason: str
    triggered_by: str

    def __post_init__(self) -> None:
        if not isinstance(self.state, KillSwitchState):
            raise RiskControlError(
                f"KillSwitchDecision.state must be a KillSwitchState, "
                f"got {type(self.state).__name__}"
            )
        if not isinstance(self.observed_at, str) or not self.observed_at:
            raise RiskControlError("KillSwitchDecision.observed_at must be a non-empty str")
        if not isinstance(self.reason, str):
            raise RiskControlError("KillSwitchDecision.reason must be a str")
        if not isinstance(self.triggered_by, str):
            raise RiskControlError("KillSwitchDecision.triggered_by must be a str")
        if self.state is KillSwitchState.ARMED:
            if self.reason or self.triggered_by:
                raise RiskControlError(
                    "KillSwitchDecision.reason and .triggered_by must be empty when armed"
                )
        else:
            if not self.reason:
                raise RiskControlError(
                    "KillSwitchDecision.reason must be non-empty when state is tripped"
                )
            if not self.triggered_by:
                raise RiskControlError(
                    "KillSwitchDecision.triggered_by must be non-empty when state is tripped"
                )


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    """Immutable summary of a reconciliation pass.

    Fields:

    - ``status``: :class:`ReconciliationStatus`.
    - ``checked_at``: ISO-8601 UTC string with ``Z`` suffix (ADR-004).
    - ``tolerance``: non-negative float (USD or matching unit) used for
      the check; ADR-003 prescribes ``max(10, 0.001 * net_liquidation)``.
    - ``observed_delta``: non-negative float observed mismatch
      magnitude; ``0.0`` when status is :attr:`ReconciliationStatus.CLEAN`
      or :attr:`ReconciliationStatus.UNAVAILABLE`.
    - ``details``: read-only mapping of structured detail (e.g.
      per-symbol deltas, source descriptors). No secrets, no credentials.
    """

    status: ReconciliationStatus
    checked_at: str
    tolerance: float
    observed_delta: float
    details: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.status, ReconciliationStatus):
            raise RiskControlError(
                f"ReconciliationReport.status must be a ReconciliationStatus, "
                f"got {type(self.status).__name__}"
            )
        if not isinstance(self.checked_at, str) or not self.checked_at:
            raise RiskControlError("ReconciliationReport.checked_at must be a non-empty str")
        if isinstance(self.tolerance, bool) or not isinstance(self.tolerance, (int, float)):
            raise RiskControlError("ReconciliationReport.tolerance must be a number")
        if self.tolerance < 0:
            raise RiskControlError("ReconciliationReport.tolerance must be non-negative")
        if isinstance(self.observed_delta, bool) or not isinstance(
            self.observed_delta, (int, float)
        ):
            raise RiskControlError("ReconciliationReport.observed_delta must be a number")
        if self.observed_delta < 0:
            raise RiskControlError("ReconciliationReport.observed_delta must be non-negative")
        if not isinstance(self.details, Mapping):
            raise RiskControlError("ReconciliationReport.details must be a Mapping")
        if not isinstance(self.details, MappingProxyType):
            object.__setattr__(self, "details", MappingProxyType(dict(self.details)))


@dataclass(frozen=True, slots=True)
class HeartbeatRecord:
    """Immutable description of a heartbeat sample.

    Fields:

    - ``component``: short identifier for the heartbeat source (e.g.
      ``"operator"``, ``"local_machine"``). Non-empty string with no
      whitespace.
    - ``status``: :class:`HeartbeatStatus`.
    - ``last_update``: ISO-8601 UTC string with ``Z`` suffix (ADR-004).
    - ``observed_at``: ISO-8601 UTC string with ``Z`` suffix; the moment
      the staleness check was evaluated.
    - ``age_seconds``: non-negative float; ``observed_at - last_update``
      expressed in seconds.
    """

    component: str
    status: HeartbeatStatus
    last_update: str
    observed_at: str
    age_seconds: float

    def __post_init__(self) -> None:
        if not isinstance(self.component, str) or not self.component:
            raise RiskControlError("HeartbeatRecord.component must be a non-empty str")
        if any(ch.isspace() for ch in self.component):
            raise RiskControlError("HeartbeatRecord.component must not contain whitespace")
        if not isinstance(self.status, HeartbeatStatus):
            raise RiskControlError(
                f"HeartbeatRecord.status must be a HeartbeatStatus, "
                f"got {type(self.status).__name__}"
            )
        if not isinstance(self.last_update, str) or not self.last_update:
            raise RiskControlError("HeartbeatRecord.last_update must be a non-empty str")
        if not isinstance(self.observed_at, str) or not self.observed_at:
            raise RiskControlError("HeartbeatRecord.observed_at must be a non-empty str")
        if isinstance(self.age_seconds, bool) or not isinstance(self.age_seconds, (int, float)):
            raise RiskControlError("HeartbeatRecord.age_seconds must be a number")
        if self.age_seconds < 0:
            raise RiskControlError("HeartbeatRecord.age_seconds must be non-negative")


@runtime_checkable
class KillSwitchProtocol(Protocol):
    """Abstract kill-switch boundary (ADR-002).

    A conforming implementation reports the current kill-switch decision
    and accepts a trip request. The runtime contract is:

    - :meth:`current` returns a fresh :class:`KillSwitchDecision`
      reflecting the kill switch's state at the moment of the call.
      Implementations must not raise for the steady-state case; transient
      backend failures should surface as ``state=TRIPPED`` to satisfy the
      ADR-002 "safe default is no trading" invariant.
    - :meth:`trip` records an active trip with the supplied ``reason``
      and ``triggered_by`` actor. Subsequent calls to :meth:`current`
      must return ``state=TRIPPED`` until a future reset workflow clears
      it. ``reason`` and ``triggered_by`` must be non-empty strings.
    """

    def current(self) -> KillSwitchDecision: ...

    def trip(self, *, reason: str, triggered_by: str) -> KillSwitchDecision: ...


@runtime_checkable
class ReconciliationProtocol(Protocol):
    """Abstract reconciliation boundary (ADR-003).

    A conforming implementation performs one reconciliation pass and
    returns an immutable :class:`ReconciliationReport`. Implementations
    must distinguish :attr:`ReconciliationStatus.UNAVAILABLE` (no
    upstream data) from :attr:`ReconciliationStatus.FAILED` (confirmed
    material mismatch); ADR-003 requires that distinction to avoid
    treating upstream outages as automatic kill-switch trips.
    """

    def reconcile(self) -> ReconciliationReport: ...


@runtime_checkable
class HeartbeatProtocol(Protocol):
    """Abstract heartbeat boundary (ADR-005).

    A conforming implementation reports the current heartbeat record for
    a named component. :meth:`status` evaluates staleness against the
    implementation's configured threshold (ADR-005 documents 8 hours for
    the operator heartbeat) and returns an immutable
    :class:`HeartbeatRecord`. A component the implementation has never
    seen must report :attr:`HeartbeatStatus.STALE` rather than raising,
    to preserve ADR-005's "safe default is paused" property.
    """

    def status(self, component: str) -> HeartbeatRecord: ...


def to_utc_string(value: datetime) -> str:
    """Normalize a timezone-aware ``datetime`` to the ADR-004 ``Z``-suffixed string.

    Thin wrapper over :func:`gmc_rebuild.time.format_utc` /
    :func:`gmc_rebuild.time.ensure_utc` provided so callers constructing
    risk-control records from ``datetime`` values do not need to import
    the :mod:`gmc_rebuild.time` module directly. Naive datetimes raise
    :class:`gmc_rebuild.time.NaiveDatetimeError` from ``ensure_utc``.
    """
    if not isinstance(value, datetime):
        raise RiskControlError(
            f"to_utc_string expects a datetime, got {type(value).__name__}"
        )
    return format_utc(ensure_utc(value))


__all__ = [
    "HeartbeatProtocol",
    "HeartbeatRecord",
    "HeartbeatStatus",
    "KillSwitchDecision",
    "KillSwitchProtocol",
    "KillSwitchState",
    "ReconciliationProtocol",
    "ReconciliationReport",
    "ReconciliationStatus",
    "RiskControlError",
    "to_utc_string",
]
