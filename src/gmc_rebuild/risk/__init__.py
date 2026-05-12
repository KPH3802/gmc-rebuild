"""gmc_rebuild.risk — risk-control interfaces (P2-05).

This subpackage is authorized by PR P2-05 (see
``governance/authorizations/2026-05-12_p2-05.md`` and
``plan/phase2_entry_plan.md`` §4). It defines abstract :class:`typing.Protocol`
boundaries and supporting frozen dataclasses for the kill-switch (ADR-002),
reconciliation (ADR-003), and heartbeat (ADR-005) risk-control surfaces.

P2-05 deliberately does **not** introduce:

- broker, account, or execution logic (no broker SDK, no order objects,
  no order placement, no fills, no position management),
- strategy, signal, scanner, model, portfolio, or backtest code,
- market-data ingestion,
- persistence, database writes, or on-disk reconciliation/heartbeat state,
- schedulers, background jobs, daemons, runtime entry points,
- env-var or secrets loading inside this submodule,
- external sinks (network, syslog/journald, cloud logging, HTTP),
- any concrete runtime implementation of the protocols; test-only fakes
  live under ``tests/`` and are not exported from the runtime package,
- expansion into Phase 2 work beyond P2-05 or any Phase 3+ item.

See ``MASTER_STATUS.md`` §6, §7, and §8 for the phase-boundary controls
that continue to apply.
"""

from __future__ import annotations

from gmc_rebuild.risk.interfaces import (
    HeartbeatProtocol,
    HeartbeatRecord,
    HeartbeatStatus,
    KillSwitchDecision,
    KillSwitchProtocol,
    KillSwitchState,
    ReconciliationProtocol,
    ReconciliationReport,
    ReconciliationStatus,
    RiskControlError,
    to_utc_string,
)

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
