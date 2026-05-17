"""Inert local simulation boundary skeleton (P5-01).

See :mod:`gmc_rebuild.simulation` for the design constraints and
authorization reference. This module deliberately performs only:

- declaration of a closed string-enum identifying the authorized
  local simulation lane(s);
- declaration of an immutable :class:`SimulatedIntent` record that
  represents a *placeholder* for a future simulated progression
  (no symbol, no side, no quantity, no price — the intent carries
  only a lane, an identifier, and an ADR-004 ``Z``-suffixed UTC
  creation timestamp);
- declaration of a :class:`SimulationBoundary` whose only public
  operation, :meth:`SimulationBoundary.propose`, returns the supplied
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
and does not schedule.
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


__all__ = [
    "SimulatedIntent",
    "SimulationBoundary",
    "SimulationBoundaryError",
    "SimulationLane",
]
