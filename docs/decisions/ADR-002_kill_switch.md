# ADR-002: Runtime Kill Switch Architecture

**Status**: Accepted

**Date**: 2026-05-10 (UTC)

**Participants**: Kevin Heaney

---

## Problem Statement

The system must have an **emergency stop mechanism** that responds in < 1 second if unsafe market conditions are detected. The kill switch must stop all trading immediately, be manually triggerable by Kevin, and persist across reboots.

---

## Decision

**Use SQLite database flag** stored in `gmc_data/monitor.db` as the runtime kill switch mechanism.

---

## Implementation Details

### Database Schema

```sql
CREATE TABLE IF NOT EXISTS kill_switch (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    triggered_at DATETIME NOT NULL,           -- UTC timestamp
    triggered_by TEXT NOT NULL,               -- "kevin" or "auto_vix" or "auto_reconciliation"
    reason TEXT NOT NULL,                     -- Human-readable reason
    active BOOLEAN NOT NULL DEFAULT 1         -- 1=active, 0=reset by operator
);
```

### Auto-Trigger Conditions

| Condition | Trigger | Reason |
|-----------|---------|--------|
| VIX > 50 | INSERT kill_switch | "Auto: VIX extreme" |
| Daily drawdown < -2% | INSERT kill_switch | "Auto: Max daily loss" |
| Reconciliation mismatch | INSERT kill_switch | "Auto: Position mismatch" |
| IB Gateway unavailable | INSERT kill_switch | "Auto: IB timeout" |
| Kevin heartbeat stale | INSERT kill_switch | "Auto: Operator offline" |

### Manual Trigger

```bash
sqlite3 ~/gmc_data/monitor.db << EOF
INSERT INTO kill_switch (triggered_at, triggered_by, reason, active)
VALUES (datetime('now'), 'kevin', 'Manual override', 1);
EOF
```

### Check Status

```bash
sqlite3 ~/gmc_data/monitor.db "SELECT * FROM kill_switch ORDER BY triggered_at DESC LIMIT 1"
```

### Reset Kill Switch (Operator Manual)

```bash
sqlite3 ~/gmc_data/monitor.db << EOF
UPDATE kill_switch SET active=0 WHERE active=1;
EOF
```

---

## Rationale

Why SQLite database over alternatives?

- **Response Time**: ~1ms query + action (acceptable)
- **Audit Trail**: Tracks who triggered, when, and why
- **Durable**: Survives reboots; safe default is "still killed"
- **Integrated**: Same DB as daily monitoring (gmc_data/monitor.db)
- **Queryable**: Can inspect from CLI or monitoring dashboard
- **No extra services**: Uses existing SQLite; no Flask to manage

---

## Follow-Up Actions

| Action | Timeline |
|--------|----------|
| Create kill_switch table in monitor.db | Phase 2 start |
| Implement monitoring daemon query logic | Phase 2 |
| Add auto-trigger logic (VIX, drawdown, etc.) | Phase 2 |
| Test < 1 sec response time | Phase 2 |
| Daily report integration | Phase 2 |

---

## Approval

**Decision Made By**: Kevin Heaney (2026-05-10)  
**Status**: Accepted  
**Implementation**: Phase 2
