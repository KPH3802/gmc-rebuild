# ADR-005: Operator Availability Heartbeat

## Status

Accepted

## Date

2026-05-10 UTC

## Context / Problem

GMC is operated by a single human decision maker. Future runtime systems must detect stale operator availability and enter a safe state when Kevin is unavailable beyond the accepted window. Phase 1 must define the governance rule without writing daemon or broker code.

## Decision

Use database-backed heartbeat records in the future monitoring database. Phase 2 design will include a local machine heartbeat and a Kevin operator heartbeat. If the operator heartbeat is stale beyond the approved threshold, future runtime monitoring must trigger the kill switch.

## Alternatives Considered

- No heartbeat: simplest, but leaves a solo-operator availability gap.
- Calendar-based availability only: useful context, but not reliable as a runtime safety input.
- Third-party monitoring service first: possible later, but premature for local dry-run Phase 2.

## Consequences

- Positive: Operator availability becomes auditable and machine-checkable.
- Positive: The project has a documented safe-state response before runtime code exists.
- Negative: Phase 2 must make heartbeat update ergonomics simple enough that Kevin actually uses it.
- Risk: False stale alerts can pause trading; that is preferable to unattended unsafe behavior.

## Implementation Notes

Potential Phase 2 schema, subject to review before implementation:

```sql
CREATE TABLE IF NOT EXISTS heartbeat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component TEXT NOT NULL,
    last_update_utc TEXT NOT NULL,
    status TEXT NOT NULL,
    notes TEXT
);
```

Python examples must follow ADR-004:

```python
from datetime import datetime, timezone

now_utc = datetime.now(timezone.utc)
last_update = datetime.fromisoformat(row["last_update_utc"].replace("Z", "+00:00"))
age_seconds = (now_utc - last_update).total_seconds()
```

The operator stale threshold is 8 hours unless Kevin changes it through a documented governance update.

## Follow-up Actions

- Define the operator heartbeat command during Phase 2 setup.
- Add tests for stale heartbeat detection before any monitor is allowed to run.
- Link heartbeat status into the daily report template.

## Related ADRs

- ADR-002: Runtime Kill Switch Architecture
- ADR-004: UTC and Timezone Discipline
- ADR-006: Deployment and Rollback Logs
