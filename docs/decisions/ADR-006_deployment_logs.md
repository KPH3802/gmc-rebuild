# ADR-006: Deployment and Rollback Logs

## Status

Accepted

## Date

2026-05-10 UTC

## Context / Problem

Every operational change needs an audit trail that records what changed, why it changed, how it was verified, and how it can be rolled back. This is required before Phase 2 creates any runtime component or local database.

## Decision

Use Markdown deployment logs under `docs/deploys/` for every material operational change. The deployment log template is the required structure for pre-deployment checks, execution notes, post-deployment verification, rollback instructions, and sign-off.

## Alternatives Considered

- Rely on Git commits only: captures code changes, but not runtime steps or verification evidence.
- External ticketing system: useful later, but unnecessary for Phase 1.
- Free-form notes: flexible, but inconsistent and hard to verify externally.

## Consequences

- Positive: Phase gates and rollback plans are visible in Git.
- Positive: External reviewers can audit deployments without needing chat history.
- Negative: Operators must maintain the log as part of the deployment, not after the fact.
- Risk: Incomplete logs can create false confidence; reviews must reject incomplete deployment evidence.

## Implementation Notes

- Template path: `docs/deploys/deploy-log-template.md`.
- Deployment timestamps must be UTC and follow ADR-004.
- Phase 1 governance changes do not deploy runtime trading systems.
- Future deployment logs should reference related ADRs, commits, reviews, and verification outputs.

## Follow-up Actions

- Create dated deployment logs for Phase 2 infrastructure setup.
- Add deployment-log review to Phase 2 entry criteria.
- Define archive naming for successful, failed, and rolled-back deployments.

## Related ADRs

- ADR-001: Secrets Management Strategy
- ADR-002: Runtime Kill Switch Architecture
- ADR-004: UTC and Timezone Discipline
- ADR-007: Minimal CI Strategy
