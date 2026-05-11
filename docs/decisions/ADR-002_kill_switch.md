# ADR-002: Runtime Kill Switch Architecture

## Status

Accepted

## Date

2026-05-10 UTC

## Context / Problem

Before any trading logic is rebuilt, the project needs a documented safe-state mechanism. The kill switch must be durable, auditable, inspectable by a solo operator, and available to future monitoring code without requiring a web service or broker integration during Phase 1.

## Decision

Use a SQLite-backed runtime kill switch stored outside the repository under `gmc_data/monitor.db` when Phase 2 implementation begins. A future runtime component must treat any active kill-switch record as a hard stop.

## Alternatives Considered

- In-memory flag: fast, but lost on restart and not auditable.
- Flat file flag: simple, but harder to query and extend with structured metadata.
- Local HTTP service: flexible, but creates more moving parts before they are justified.

## Consequences

- Positive: The safe state survives process restarts and machine reboots.
- Positive: Operators and review tools can inspect trigger history with standard SQLite tooling.
- Negative: Runtime code must handle SQLite availability and locking carefully.
- Risk: A stale active flag can block startup; that is acceptable because the safe default is no trading.

## Implementation Notes

Potential Phase 2 schema, subject to review before implementation:

```sql
CREATE TABLE IF NOT EXISTS kill_switch (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    triggered_at_utc TEXT NOT NULL,
    triggered_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);
```

Timestamp values must be UTC ISO 8601 strings such as `2026-05-10T14:23:45Z`. Python code must use timezone-aware UTC values, for example `datetime.now(timezone.utc)`.

## Follow-up Actions

- Create the schema in Phase 2 only after tests and review are in place.
- Define activation and reset workflows in a deployment log before first dry-run use.
- Add reconciliation and heartbeat integration tests when those components exist.

## Related ADRs

- ADR-003: Broker Reconciliation Discipline
- ADR-004: UTC and Timezone Discipline
- ADR-005: Operator Availability Heartbeat
- ADR-006: Deployment and Rollback Logs
