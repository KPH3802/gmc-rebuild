"""Inert local runtime shell boundary (P4-06).

This subpackage provides the smallest possible local runtime shell
boundary that composes the three already-merged risk-control Protocol
boundaries declared in :mod:`gmc_rebuild.risk` (P2-05) — ``HeartbeatProtocol``
(ADR-005), ``KillSwitchProtocol`` (ADR-002), ``ReconciliationProtocol``
(ADR-003) — into a single read-only "would safety controls block
progression" verdict. The boundary is **inert**: it never trades, never
talks to a broker, never reads market data, never schedules anything,
never reads secrets, never reaches the network, never persists, and
never sleeps. Its sole responsibility is to ask the three injected
protocol-typed instances for their current status and report a composed
verdict.

Authorization: ``governance/authorizations/2026-05-16_p4-06.md``.

Design constraints — these are governance constraints, not stylistic
preferences:

- **Inert by construction.** No ``__main__`` entry point, no daemon,
  no scheduler, no background thread, no long-running service, no
  broker integration, no market-data ingestion, no order placement, no
  strategy / scanner / model / portfolio / backtest / live / paper
  trading logic, no env-var loading, no secrets, no network, no
  persistence, no ``time.sleep``, no ``asyncio.sleep``.
- **Composed, not concrete.** This module composes the abstract
  Protocol boundaries declared in :mod:`gmc_rebuild.risk`. It does not
  introduce a new concrete implementation of ``HeartbeatProtocol``,
  ``KillSwitchProtocol``, or ``ReconciliationProtocol``.
- **Safety-gated.** A verdict is ``clear`` only when the heartbeat for
  every required component is ``FRESH``, the kill switch is ``ARMED``,
  and reconciliation is ``CLEAN``. Any other observed state produces a
  blocking verdict with a structured list of blockers — preserving the
  ADR-002 / ADR-003 / ADR-005 "safe default is no trading" invariant
  end-to-end.
- **Read-only.** The shell does not mutate the injected protocol
  instances. It calls only the read methods declared on the abstract
  Protocols (``HeartbeatProtocol.status``, ``KillSwitchProtocol.current``,
  ``ReconciliationProtocol.reconcile``).
- **ADR-004 UTC discipline.** Timestamps surfaced on the verdict are
  ADR-004 ``Z``-suffixed UTC strings sourced from the injected
  protocol instances.
"""

from __future__ import annotations

from gmc_rebuild.runtime._operator_view import (
    VERDICT_BLOCKED,
    VERDICT_CLEAR,
    OperatorSafetyView,
    format_safety_verdict,
)
from gmc_rebuild.runtime._shell import (
    BLOCKER_HEARTBEAT_STALE,
    BLOCKER_KILL_SWITCH_TRIPPED,
    BLOCKER_RECONCILIATION_FAILED,
    BLOCKER_RECONCILIATION_UNAVAILABLE,
    BLOCKER_RECONCILIATION_WARNING,
    RuntimeShell,
    RuntimeShellError,
    SafetyVerdict,
)

__all__ = [
    "BLOCKER_HEARTBEAT_STALE",
    "BLOCKER_KILL_SWITCH_TRIPPED",
    "BLOCKER_RECONCILIATION_FAILED",
    "BLOCKER_RECONCILIATION_UNAVAILABLE",
    "BLOCKER_RECONCILIATION_WARNING",
    "VERDICT_BLOCKED",
    "VERDICT_CLEAR",
    "OperatorSafetyView",
    "RuntimeShell",
    "RuntimeShellError",
    "SafetyVerdict",
    "format_safety_verdict",
]
