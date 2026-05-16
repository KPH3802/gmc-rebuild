"""Inert local runtime shell boundary implementation (P4-06).

See :mod:`gmc_rebuild.runtime` for the design constraints and
authorization reference. This module deliberately performs only:

- dependency injection of three protocol-typed instances at
  construction;
- read-only calls to the three abstract Protocol methods
  (``HeartbeatProtocol.status``, ``KillSwitchProtocol.current``,
  ``ReconciliationProtocol.reconcile``);
- assembly of an immutable :class:`SafetyVerdict` describing whether
  the composed safety controls would block progression.

It does not import any concrete fixture from
:mod:`gmc_rebuild.heartbeat`, :mod:`gmc_rebuild.kill_switch`, or
:mod:`gmc_rebuild.reconciliation`; callers pass already-constructed
protocol-typed instances in.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

from gmc_rebuild.risk import (
    HeartbeatProtocol,
    HeartbeatStatus,
    KillSwitchProtocol,
    KillSwitchState,
    ReconciliationProtocol,
    ReconciliationStatus,
)

BLOCKER_HEARTBEAT_STALE: str = "heartbeat_stale"
"""Blocker code emitted when any required heartbeat component is ``STALE``."""

BLOCKER_KILL_SWITCH_TRIPPED: str = "kill_switch_tripped"
"""Blocker code emitted when the kill switch reports ``TRIPPED``."""

BLOCKER_RECONCILIATION_FAILED: str = "reconciliation_failed"
"""Blocker code emitted when reconciliation reports ``FAILED``."""

BLOCKER_RECONCILIATION_UNAVAILABLE: str = "reconciliation_unavailable"
"""Blocker code emitted when reconciliation reports ``UNAVAILABLE``."""

BLOCKER_RECONCILIATION_WARNING: str = "reconciliation_warning"
"""Blocker code emitted when reconciliation reports ``WARNING``.

ADR-003 documents ``WARNING`` as advisory (no automatic kill-switch
trip). The inert shell still treats ``WARNING`` as a blocker because
its only output is a composed "would safety controls block
progression" verdict, and the only state that is unambiguously clear
is ``CLEAN``. ``WARNING`` is reported as a distinct, advisory-grade
blocker so consumers can distinguish it from ``FAILED`` and
``UNAVAILABLE`` without the shell making a trading decision.
"""


class RuntimeShellError(ValueError):
    """Raised when the runtime shell is constructed with invalid input."""


@dataclass(frozen=True, slots=True)
class SafetyVerdict:
    """Immutable composed safety verdict produced by :class:`RuntimeShell`.

    Fields:

    - ``clear``: ``True`` only when every required heartbeat component
      is ``FRESH``, the kill switch is ``ARMED``, and reconciliation
      is ``CLEAN``. ``False`` in any other observed state.
    - ``blockers``: tuple of blocker codes ordered as
      ``(heartbeat_*, kill_switch_*, reconciliation_*)``. Empty when
      ``clear`` is ``True``.
    - ``heartbeat_statuses``: read-only mapping from required-component
      name to its observed :class:`HeartbeatStatus`.
    - ``kill_switch_state``: the observed :class:`KillSwitchState`.
    - ``reconciliation_status``: the observed
      :class:`ReconciliationStatus`.
    - ``observed_at``: ADR-004 ``Z``-suffixed UTC string sourced from
      the kill switch's ``current()`` decision; the shell uses the
      kill-switch clock as the verdict's reference timestamp because
      it is the only one of the three protocols that always returns a
      timestamp without first being staged.
    """

    clear: bool
    blockers: tuple[str, ...]
    heartbeat_statuses: Mapping[str, HeartbeatStatus]
    kill_switch_state: KillSwitchState
    reconciliation_status: ReconciliationStatus
    observed_at: str

    def __post_init__(self) -> None:
        if not isinstance(self.clear, bool):
            raise RuntimeShellError("SafetyVerdict.clear must be a bool")
        if not isinstance(self.blockers, tuple) or not all(
            isinstance(b, str) and b for b in self.blockers
        ):
            raise RuntimeShellError("SafetyVerdict.blockers must be a tuple of non-empty str")
        if self.clear and self.blockers:
            raise RuntimeShellError(
                "SafetyVerdict.blockers must be empty when SafetyVerdict.clear is True"
            )
        if not self.clear and not self.blockers:
            raise RuntimeShellError(
                "SafetyVerdict.blockers must be non-empty when SafetyVerdict.clear is False"
            )
        if not isinstance(self.heartbeat_statuses, Mapping):
            raise RuntimeShellError("SafetyVerdict.heartbeat_statuses must be a Mapping")
        if not isinstance(self.heartbeat_statuses, MappingProxyType):
            statuses: dict[str, HeartbeatStatus] = {}
            for component, status in self.heartbeat_statuses.items():
                if not isinstance(component, str) or not component:
                    raise RuntimeShellError(
                        "SafetyVerdict.heartbeat_statuses keys must be non-empty str"
                    )
                if not isinstance(status, HeartbeatStatus):
                    raise RuntimeShellError(
                        "SafetyVerdict.heartbeat_statuses values must be HeartbeatStatus"
                    )
                statuses[component] = status
            object.__setattr__(self, "heartbeat_statuses", MappingProxyType(statuses))
        if not isinstance(self.kill_switch_state, KillSwitchState):
            raise RuntimeShellError("SafetyVerdict.kill_switch_state must be a KillSwitchState")
        if not isinstance(self.reconciliation_status, ReconciliationStatus):
            raise RuntimeShellError(
                "SafetyVerdict.reconciliation_status must be a ReconciliationStatus"
            )
        if not isinstance(self.observed_at, str) or not self.observed_at:
            raise RuntimeShellError("SafetyVerdict.observed_at must be a non-empty str")


class RuntimeShell:
    """Inert local runtime shell boundary.

    Composes a :class:`gmc_rebuild.risk.HeartbeatProtocol`, a
    :class:`gmc_rebuild.risk.KillSwitchProtocol`, and a
    :class:`gmc_rebuild.risk.ReconciliationProtocol` via dependency
    injection and exposes a single read-only :meth:`evaluate` method
    that returns a :class:`SafetyVerdict` describing whether progression
    would be blocked by the composed safety controls.

    The shell does not trade, does not place orders, does not talk to a
    broker, does not read market data, does not schedule anything, does
    not read secrets, does not reach the network, does not persist, and
    does not sleep. It is the smallest local boundary that can answer
    the question "would the safety controls block progression?" without
    crossing into any of those categories.
    """

    __slots__ = (
        "_heartbeat",
        "_kill_switch",
        "_reconciliation",
        "_required_components",
    )

    def __init__(
        self,
        *,
        heartbeat: HeartbeatProtocol,
        kill_switch: KillSwitchProtocol,
        reconciliation: ReconciliationProtocol,
        required_components: Iterable[str],
    ) -> None:
        if not isinstance(heartbeat, HeartbeatProtocol):
            raise RuntimeShellError("RuntimeShell.heartbeat must conform to HeartbeatProtocol")
        if not isinstance(kill_switch, KillSwitchProtocol):
            raise RuntimeShellError("RuntimeShell.kill_switch must conform to KillSwitchProtocol")
        if not isinstance(reconciliation, ReconciliationProtocol):
            raise RuntimeShellError(
                "RuntimeShell.reconciliation must conform to ReconciliationProtocol"
            )
        components = tuple(required_components)
        if not components:
            raise RuntimeShellError("RuntimeShell.required_components must be non-empty")
        seen: set[str] = set()
        for component in components:
            if not isinstance(component, str) or not component:
                raise RuntimeShellError(
                    "RuntimeShell.required_components entries must be non-empty str"
                )
            if any(ch.isspace() for ch in component):
                raise RuntimeShellError(
                    "RuntimeShell.required_components entries must not contain whitespace"
                )
            if component in seen:
                raise RuntimeShellError("RuntimeShell.required_components entries must be unique")
            seen.add(component)
        self._heartbeat: HeartbeatProtocol = heartbeat
        self._kill_switch: KillSwitchProtocol = kill_switch
        self._reconciliation: ReconciliationProtocol = reconciliation
        self._required_components: tuple[str, ...] = components

    @property
    def required_components(self) -> Sequence[str]:
        """The tuple of required heartbeat component names (read-only)."""
        return self._required_components

    def evaluate(self) -> SafetyVerdict:
        """Return the composed :class:`SafetyVerdict` at call time.

        Read-only: calls only the abstract Protocol read methods on the
        injected instances. Does not mutate the instances, the shell,
        or any external state.
        """
        heartbeat_statuses: dict[str, HeartbeatStatus] = {}
        any_heartbeat_stale = False
        for component in self._required_components:
            record = self._heartbeat.status(component)
            heartbeat_statuses[component] = record.status
            if record.status is HeartbeatStatus.STALE:
                any_heartbeat_stale = True

        kill_switch_decision = self._kill_switch.current()
        reconciliation_report = self._reconciliation.reconcile()

        blockers: list[str] = []
        if any_heartbeat_stale:
            blockers.append(BLOCKER_HEARTBEAT_STALE)
        if kill_switch_decision.state is KillSwitchState.TRIPPED:
            blockers.append(BLOCKER_KILL_SWITCH_TRIPPED)
        if reconciliation_report.status is ReconciliationStatus.FAILED:
            blockers.append(BLOCKER_RECONCILIATION_FAILED)
        elif reconciliation_report.status is ReconciliationStatus.UNAVAILABLE:
            blockers.append(BLOCKER_RECONCILIATION_UNAVAILABLE)
        elif reconciliation_report.status is ReconciliationStatus.WARNING:
            blockers.append(BLOCKER_RECONCILIATION_WARNING)

        return SafetyVerdict(
            clear=not blockers,
            blockers=tuple(blockers),
            heartbeat_statuses=heartbeat_statuses,
            kill_switch_state=kill_switch_decision.state,
            reconciliation_status=reconciliation_report.status,
            observed_at=kill_switch_decision.observed_at,
        )


__all__ = [
    "BLOCKER_HEARTBEAT_STALE",
    "BLOCKER_KILL_SWITCH_TRIPPED",
    "BLOCKER_RECONCILIATION_FAILED",
    "BLOCKER_RECONCILIATION_UNAVAILABLE",
    "BLOCKER_RECONCILIATION_WARNING",
    "RuntimeShell",
    "RuntimeShellError",
    "SafetyVerdict",
]
