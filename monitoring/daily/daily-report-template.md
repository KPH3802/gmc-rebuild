# Daily Monitoring Report: YYYY-MM-DD UTC

## Report Metadata

**Environment**: Local | Dry-run | Production
**Operator**: [Name]
**Report Window**: YYYY-MM-DDT00:00:00Z to YYYY-MM-DDT23:59:59Z
**Overall Status**: Green | Yellow | Red

## Phase Compliance

- [ ] Current work stayed inside the approved phase.
- [ ] No live trading code was added without approval.
- [ ] No broker execution code was added without approval.
- [ ] No trading strategy code was added during Phase 1.

## Repository Hygiene

| Check | Result | Notes |
| --- | --- | --- |
| `git status --short` reviewed | Pass | [Notes] |
| Secrets absent from Git | Pass | [Notes] |
| Local DB/data/log artifacts absent | Pass | [Notes] |
| Pre-commit result captured | Pass | [Notes] |

## Runtime Safety

Use `N/A` until Phase 2 runtime components exist.

| Control | Expected | Actual | Status |
| --- | --- | --- | --- |
| Kill switch | Fail closed | [N/A or state] | Green | Yellow | Red |
| Reconciliation | Clean | [N/A or state] | Green | Yellow | Red |
| Mac heartbeat | Fresh | [N/A or age] | Green | Yellow | Red |
| Kevin heartbeat | Fresh | [N/A or age] | Green | Yellow | Red |

## UTC Timestamp Audit

- [ ] New timestamps use UTC.
- [ ] Python examples use timezone-aware UTC.
- [ ] Human-readable local time, if shown, is secondary to UTC.

## Issues and Follow-up

| Priority | Issue | Owner | Due |
| --- | --- | --- | --- |
| P1/P2/P3 | [Issue] | [Owner] | YYYY-MM-DD |

## Evidence Links

- Deployment log: [Path or N/A]
- Review request: [Path or N/A]
- ADRs: [Path list or N/A]
- Verification output: [Path, pasted output, or N/A]

## Sign-off

**Completed At (UTC)**: YYYY-MM-DDTHH:MM:SSZ
**Prepared By**: [Name]
**Kevin Decision**: Accepted | Needs Follow-up | Blocked
