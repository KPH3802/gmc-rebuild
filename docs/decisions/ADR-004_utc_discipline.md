# ADR-004: UTC/Timezone Discipline

**Status**: Accepted

**Date**: 2026-05-10 (UTC)

**Participants**: Kevin Heaney

---

## Problem Statement

Timestamps in trading systems are a common source of subtle bugs: order execution timestamps off by 1 hour (DST transition), backtest timestamps in local time instead of market time, reconciliation mismatch due to timezone ambiguity. The system must eliminate the category of timezone bugs by enforcing **strict UTC everywhere**.

---

## Decision

**Enforce strict UTC-only timestamps throughout the system** with zero timezone conversions in trading logic.

---

## Implementation Details

### Core Rules

1. **Storage**: All timestamps stored as **UTC ISO 8601** with 'Z' suffix
```python
   # CORRECT:
   timestamp = "2026-05-10T14:23:45.123456Z"  # ISO 8601 UTC
   timestamp = datetime.datetime.now(datetime.timezone.utc)
   
   # WRONG:
   timestamp = "2026-05-10 14:23:45"  # No timezone info (ambiguous)
   timestamp = datetime.datetime.now()  # Naive datetime (local time)
```

2. **Computation**: All time operations in UTC
```python
   from datetime import datetime, timezone
   now_utc = datetime.now(timezone.utc)
   start_utc = datetime(2026, 5, 10, 0, 0, 0, tzinfo=timezone.utc)
   duration = (now_utc - start_utc).total_seconds()
```

3. **APIs**: All external APIs (IB, Coinbase, etc.) timestamps converted to UTC immediately
```python
   # When receiving from IB (Unix timestamp):
   ib_timestamp_unix = ib_response.get("timestamp")
   utc_timestamp = datetime.fromtimestamp(ib_timestamp_unix, tz=timezone.utc)
```

4. **Backtests**: All historical data processed in UTC
```python
   data = yfinance.download("AAPL", start="2026-01-01", end="2026-12-31")
   assert data.index.tz.zone == 'UTC', "Data not in UTC!"
```

5. **Display**: Local time conversion only for reports/logs
```python
   # In daily report (only place local time appears):
   utc_dt = datetime.fromisoformat("2026-05-10T14:23:45.000000Z")
   local_dt = utc_dt.astimezone()  # Convert for display only
```

### Code Standards

- All `datetime` objects have `tzinfo=timezone.utc`
- No `datetime.now()` (use `datetime.now(timezone.utc)`)
- Mypy type checking enforces correct datetime usage
- Unit tests include timezone edge cases (DST transitions)

---

## Rationale

Why strict UTC only?

- **Eliminate category of bugs**: No timezone conversions = no DST bugs
- **Simplest**: No library, no conversion logic, no edge cases
- **Fastest**: Direct timestamp comparison, no timezone lookups
- **Most auditable**: "All timestamps are UTC" is easy to verify
- **Aligned with governance**: Explicit requirement

---

## Follow-Up Actions

| Action | Timeline |
|--------|----------|
| Add mypy `disallow_untyped_defs` | Phase 2 start |
| Add UTC pre-commit hook | Phase 2 start |
| Review all IB API integrations for tz | Phase 2 |
| Document in development guide | Phase 2 |

---

## Approval

**Decision Made By**: Kevin Heaney (2026-05-10)  
**Status**: Accepted  
**Implementation**: Phase 2
