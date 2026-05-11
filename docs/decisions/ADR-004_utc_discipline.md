# ADR-004: UTC and Timezone Discipline

## Status

Accepted

## Date

2026-05-10 UTC

## Context / Problem

Trading systems are vulnerable to timezone bugs from daylight saving changes, local machine settings, ambiguous strings, and inconsistent broker timestamp formats. The rebuild needs one timestamp discipline before runtime code exists.

## Decision

Use strict UTC throughout the repository, runtime design, logs, reports, tests, and examples. Timezone-naive datetimes are not acceptable. Local time may appear only as an optional display field in human-facing reports, and the UTC source timestamp must remain present.

## Alternatives Considered

- Store local exchange time: familiar for market sessions, but fragile around daylight saving transitions.
- Store naive timestamps and document assumptions: easy to write, unsafe to audit.
- Store Unix timestamps only: unambiguous, but less readable in Markdown logs and review artifacts.

## Consequences

- Positive: Date comparisons and audit trails are globally consistent.
- Positive: External reviewers can inspect timestamps without guessing local timezone context.
- Negative: Human-facing reports may need explicit conversion for readability.
- Risk: Future code can regress by using naive datetime helpers; tooling and review must catch this.

## Implementation Notes

Python examples must use timezone-aware UTC:

```python
from datetime import datetime, timezone

now_utc = datetime.now(timezone.utc)
timestamp = now_utc.isoformat().replace("+00:00", "Z")
```

Do not use:

```python
from datetime import datetime

datetime.now()
```

Also avoid any helper that returns a timezone-naive UTC value. Stored and documented strings should use either `2026-05-10T14:23:45Z` or a clearly documented equivalent UTC format. SQLite examples should store explicit UTC text rather than relying on local-time interpretation.

## Follow-up Actions

- Add tests for timestamp serialization when runtime modules exist.
- Add review checklist items for naive datetime usage.
- Consider a custom lint check only after actual Python modules exist.

## Related ADRs

- ADR-002: Runtime Kill Switch Architecture
- ADR-003: Broker Reconciliation Discipline
- ADR-005: Operator Availability Heartbeat
- ADR-006: Deployment and Rollback Logs
