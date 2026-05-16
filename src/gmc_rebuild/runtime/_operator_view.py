"""Read-only operator view for the inert local runtime safety verdict (P4-07).

See :mod:`gmc_rebuild.runtime` for the P4-06 design constraints and
authorization. This module adds the smallest possible read-only operator
view that formats an existing :class:`SafetyVerdict` produced by
:class:`RuntimeShell` for human / operator inspection. The view is:

- **read-only** — it accepts an already-built :class:`SafetyVerdict`
  by value and never reaches back into the protocol instances; it does
  not call :meth:`RuntimeShell.evaluate` itself;
- **deterministic** — for a given verdict, the same lines are produced
  every time;
- **local** — pure Python; no broker, no market data, no order, no
  scheduler, no daemon, no network, no persistence, no env-var, no
  secrets, no ``time.sleep``, no ``__main__``;
- **safety-preserving** — the view cannot widen the verdict; a blocked
  verdict is always rendered as ``BLOCKED`` with the blocker codes
  listed, and a ``clear`` verdict is rendered as ``CLEAR`` only when
  ``SafetyVerdict.clear`` is :data:`True`.

The view is intended for operator-facing surfaces (CLI log line,
docstring, future read-only status surface) and is deliberately scoped
to formatting only. It does not authorize trading, does not place
orders, does not trip or arm the kill switch, does not stage
reconciliation, and does not beat the heartbeat.

Authorization: ``governance/authorizations/2026-05-16_p4-07.md``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from gmc_rebuild.runtime._shell import (
    BLOCKER_HEARTBEAT_STALE,
    BLOCKER_KILL_SWITCH_TRIPPED,
    BLOCKER_RECONCILIATION_FAILED,
    BLOCKER_RECONCILIATION_UNAVAILABLE,
    BLOCKER_RECONCILIATION_WARNING,
    SafetyVerdict,
)

VERDICT_CLEAR: str = "CLEAR"
"""Operator-facing label for a ``clear`` :class:`SafetyVerdict`."""

VERDICT_BLOCKED: str = "BLOCKED"
"""Operator-facing label for a non-``clear`` :class:`SafetyVerdict`."""

_BLOCKER_DESCRIPTIONS: Mapping[str, str] = MappingProxyType(
    {
        BLOCKER_HEARTBEAT_STALE: (
            "heartbeat stale — at least one required component is STALE (ADR-005)"
        ),
        BLOCKER_KILL_SWITCH_TRIPPED: "kill switch tripped (ADR-002)",
        BLOCKER_RECONCILIATION_FAILED: (
            "reconciliation failed — confirmed material mismatch (ADR-003)"
        ),
        BLOCKER_RECONCILIATION_UNAVAILABLE: (
            "reconciliation unavailable — no upstream data (ADR-003)"
        ),
        BLOCKER_RECONCILIATION_WARNING: ("reconciliation warning — advisory band (ADR-003)"),
    }
)


@dataclass(frozen=True, slots=True)
class OperatorSafetyView:
    """Immutable read-only operator view of a :class:`SafetyVerdict`.

    Fields:

    - ``status``: :data:`VERDICT_CLEAR` when the verdict is ``clear``,
      :data:`VERDICT_BLOCKED` otherwise.
    - ``blocker_lines``: tuple of human-readable blocker descriptions,
      in the same order as :attr:`SafetyVerdict.blockers`. Empty when
      ``status`` is :data:`VERDICT_CLEAR`.
    - ``heartbeat_lines``: tuple of ``"component: STATUS"`` strings,
      one per required heartbeat component, in deterministic
      component-name-sorted order so the view is stable across calls.
    - ``kill_switch_line``: ``"kill_switch: STATE"`` string.
    - ``reconciliation_line``: ``"reconciliation: STATUS"`` string.
    - ``observed_at``: ADR-004 ``Z``-suffixed UTC string carried over
      verbatim from the underlying :attr:`SafetyVerdict.observed_at`.
    """

    status: str
    blocker_lines: tuple[str, ...]
    heartbeat_lines: tuple[str, ...]
    kill_switch_line: str
    reconciliation_line: str
    observed_at: str

    def render(self) -> str:
        """Return a deterministic multi-line text rendering of the view.

        The rendering is intended for operator-facing surfaces and is
        purely textual. It does not call any side-effecting API.
        """
        lines: list[str] = [
            f"safety: {self.status}",
            f"observed_at: {self.observed_at}",
            self.kill_switch_line,
            self.reconciliation_line,
        ]
        lines.extend(self.heartbeat_lines)
        if self.blocker_lines:
            lines.append("blockers:")
            for blocker in self.blocker_lines:
                lines.append(f"  - {blocker}")
        return "\n".join(lines)


def format_safety_verdict(verdict: SafetyVerdict) -> OperatorSafetyView:
    """Return an :class:`OperatorSafetyView` for the given verdict.

    Pure read-only formatter: takes an already-built
    :class:`SafetyVerdict` by value, inspects only its public fields,
    and produces an immutable :class:`OperatorSafetyView`. Does not call
    any protocol method, does not mutate the verdict, does not perform
    any I/O, and does not authorize any action.
    """
    if not isinstance(verdict, SafetyVerdict):
        raise TypeError("format_safety_verdict expects a SafetyVerdict")

    status = VERDICT_CLEAR if verdict.clear else VERDICT_BLOCKED

    blocker_lines = tuple(_BLOCKER_DESCRIPTIONS.get(code, code) for code in verdict.blockers)

    heartbeat_lines = tuple(
        f"heartbeat[{component}]: {verdict.heartbeat_statuses[component].value}"
        for component in sorted(verdict.heartbeat_statuses)
    )

    kill_switch_line = f"kill_switch: {verdict.kill_switch_state.value}"
    reconciliation_line = f"reconciliation: {verdict.reconciliation_status.value}"

    return OperatorSafetyView(
        status=status,
        blocker_lines=blocker_lines,
        heartbeat_lines=heartbeat_lines,
        kill_switch_line=kill_switch_line,
        reconciliation_line=reconciliation_line,
        observed_at=verdict.observed_at,
    )


__all__ = [
    "VERDICT_BLOCKED",
    "VERDICT_CLEAR",
    "OperatorSafetyView",
    "format_safety_verdict",
]
