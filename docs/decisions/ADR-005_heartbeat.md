# ADR-005: Kevin-Unavailable Safe-State Handling

**Status**: Accepted

**Date**: 2026-05-10 (UTC)

**Participants**: Kevin Heaney

---

## Problem Statement

Solo operator (Kevin) is single point of failure. If Kevin goes offline unexpectedly (sleep, travel, emergency), the system must detect unavailability and automatically engage safe-state (kill switch). The system must detect operator unavailability within 30 minutes and auto-trigger kill switch if unavailable > 8 hours.

---

## Decision

**Use database heartbeat** stored in `gmc_data/monitor.db` with two-part detection:
1. **File-based local heartbeat** (cron on Mac Studio every 5 min) detects Mac Studio crashes
2. **Operator heartbeat** (Kevin manual update) detects operator availability

---

## Implementation Details

### Database Schema

```sql
CREATE TABLE IF NOT EXISTS heartbeat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component TEXT NOT NULL,  -- "mac_studio" or "kevin"
    last_update DATETIME NOT NULL,  -- UTC timestamp
    status TEXT,              -- "online", "offline", "delayed"
    notes TEXT                -- Human-readable notes
);
```

### Heartbeat Signals

**1. Mac Studio Local Heartbeat** (automatic, every 5 min):
- Cron job on Mac Studio: `*/5 * * * * update_heartbeat.sh`
- Updates `heartbeat` table: `component="mac_studio"`, `last_update=NOW(UTC)`
- If Mac Studio crashes, no update = heartbeat stales
- If `mac_studio` heartbeat > 30 min old → alert (but don't kill switch yet)

**2. Operator Heartbeat** (manual, Kevin updates when available):
- Kevin action: At terminal, run `update_operator_heartbeat.sh`
- Updates `heartbeat` table: `component="kevin"`, `last_update=NOW(UTC)`
- If Kevin unavailable > 8 hours, no update = heartbeat stales
- If `kevin` heartbeat > 8 hours old → **auto-trigger kill switch**

### Monitoring Daemon Logic

Every 100ms iteration:

```python
def check_operator_availability():
    conn = sqlite3.connect("~/gmc_data/monitor.db")
    cursor = conn.cursor()
    
    # Check Kevin operator heartbeat (CRITICAL)
    cursor.execute("""
        SELECT last_update FROM heartbeat 
        WHERE component='kevin' 
        ORDER BY last_update DESC LIMIT 1
    """)
    kevin_row = cursor.fetchone()
    
    if kevin_row:
        kevin_last_update = datetime.fromisoformat(kevin_row[0])
        kevin_age_sec = (datetime.utcnow() - kevin_last_update).total_seconds()
        
        if kevin_age_sec > 28800:  # 8 hours
            # AUTO-TRIGGER KILL SWITCH
            trigger_kill_switch(
                reason=f"Kevin unavailable: {kevin_age_sec/3600:.1f}h"
            )
    
    conn.close()
```

### Kevin's Workflow

**Scenario 1: Normal trading day**
1. Kevin wakes up (or arrives at trading desk)
2. Opens terminal on Mac Studio
3. Runs: `update_operator_heartbeat.sh` (one-keystroke macro)
4. Heartbeat updated in DB
5. Kill switch remains disengaged (if previously triggered)
6. Trading resumes

**Scenario 2: Going to sleep (Asia trading hours)**
1. Kevin stops active monitoring
2. System will auto-stop after 8 hours (safe default)
3. Goes to sleep
4. System trades unattended for < 8 hours
5. After 8 hours, kill switch auto-engages (safe)
6. When Kevin wakes up, manually resets kill switch and resumes

**Scenario 3: Traveling / no access**
1. Kevin leaves Mac Studio at home
2. Knows heartbeat will stale after 8 hours
3. Kill switch auto-engages after 8 hours (automatic safe-state)
4. When Kevin returns/regains access, manually resets

### Update Scripts

**update_operator_heartbeat.sh**:
```bash
#!/bin/bash
sqlite3 ~/gmc_data/monitor.db << EOF
INSERT OR REPLACE INTO heartbeat (component, last_update, status)
VALUES ('kevin', datetime('now'), 'online');
EOF
```

Can be called by:
- macOS login (script in ~/.profile or launchd)
- Alfred workflow (one keystroke: "heartbeat")
- Daily cron (if Kevin at terminal, e.g., 09:00 ET daily)

---

## Rationale

Why database heartbeat with file + operator signals?

- **Dual-layer detection**: File heartbeat (Mac Studio health) + operator heartbeat (Kevin presence)
- **Safe default**: 8-hour auto-stop means overnight/travel is covered
- **Durable**: Survives reboots, integrated with monitoring DB
- **Manual override**: Kevin controls when to resume (explicit choice)
- **Audit trail**: Every heartbeat logged (forensics)

---

## Follow-Up Actions

| Action | Timeline |
|--------|----------|
| Create heartbeat table in monitor.db | Phase 2 start |
| Implement Mac Studio cron (5 min) | Phase 2 start |
| Create update_operator_heartbeat.sh | Phase 2 |
| Add macOS login hook | Phase 2 |
| Daily report integration | Phase 2 |

---

## Approval

**Decision Made By**: Kevin Heaney (2026-05-10)  
**Status**: Accepted  
**Implementation**: Phase 2
