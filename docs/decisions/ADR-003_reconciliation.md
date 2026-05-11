# ADR-003: Broker Reconciliation Discipline

## Status

Accepted

## Date

2026-05-10 UTC

## Context / Problem

Future trading infrastructure must detect mismatches between expected state and broker-reported state before they can compound into unsafe decisions. Phase 1 must define the reconciliation standard without implementing broker execution or trading strategy code.

## Decision

Require an automated reconciliation daemon in Phase 2 design. The daemon will compare expected positions, cash, and account state against broker-reported values on an hourly schedule, produce a daily UTC report, and trigger the kill switch when a material mismatch is confirmed.

## Alternatives Considered

- Manual reconciliation only: insufficient for a solo operator and too easy to miss during travel or sleep.
- Daily automated reconciliation only: useful for audit, but too slow for runtime safety.
- Per-order reconciliation only: valuable later, but requires broker execution code that is out of scope for Phase 1.

## Consequences

- Positive: Position and cash mismatches become visible within a bounded window.
- Positive: Reconciliation evidence can be attached to deployment logs and daily reports.
- Negative: Phase 2 must model tolerances precisely enough to avoid noisy false positives.
- Risk: Broker outages can look like mismatches; the daemon must distinguish unavailable data from confirmed disagreement.

## Implementation Notes

Initial tolerance policy for Phase 2 review:

`tolerance = max(10 USD, 0.1% of net liquidation value)`

| Net Liquidation Value | Tolerance |
| --- | --- |
| 10,000 USD | 10 USD |
| 50,000 USD | 50 USD |
| 100,000 USD | 100 USD |
| 1,000,000 USD | 1,000 USD |

Initial schedule:

| Cadence | Purpose |
| --- | --- |
| Hourly | Position, cash, and account-state reconciliation |
| Daily at 22:00 UTC | Detailed report for audit trail |
| Weekly Monday at 09:00 UTC | Deep audit against transaction history |

All reconciliation timestamps must follow ADR-004 and use UTC ISO 8601 strings with `Z` suffix.

## Follow-up Actions

- Write reconciliation specifications and tests before implementation.
- Define broker data fixtures for dry-run validation.
- Add daily-report fields for clean, warning, and failed reconciliation states.
- Define kill-switch trigger criteria for confirmed material mismatches.

## Related ADRs

- ADR-002: Runtime Kill Switch Architecture
- ADR-004: UTC and Timezone Discipline
- ADR-005: Operator Availability Heartbeat
- ADR-006: Deployment and Rollback Logs
