# ADR-006: Deployment & Rollback Logs Strategy

**Status**: Accepted

**Date**: 2026-05-10 (UTC)

**Participants**: Kevin Heaney

---

## Problem Statement

Every change deployed to production must be logged with full context: what changed, when, why, how it was verified, and how to rollback.

---

## Decision

**Use template-based deployment logs** with mandatory pre-deployment checklist and post-deployment verification.

---

## Implementation Details

### Before Deploying

1. Create: `docs/deploys/deploy_log_2026-05-10_14_30.md`
2. Complete pre-deployment checklist:
   - [ ] Code passes ruff/mypy/pytest
   - [ ] .gitignore confirmed
   - [ ] Dry-run test passed
   - [ ] Rollback procedure documented

### During Deployment

3. Execute deployment steps
4. Update log with timestamp

### After Deployment

5. Complete post-deployment verification:
   - [ ] Processes started
   - [ ] Logs clean
   - [ ] Reconciliation clean

6. Archive log as `_SUCCESS.md` or `_ROLLED_BACK.md`

### What Counts as Deployment

- Code changes
- Config changes
- Data migrations
- Policy changes
- Infrastructure changes

### Rollback Procedure

1. Stop trading (kill switch)
2. Revert code: `git revert [commit]`
3. Restart services
4. Verify reconciliation clean
5. Document incident postmortem

---

## Rationale

- Immediate: Works now without extra infrastructure
- Simple: Spreadsheet-level discipline
- Effective: Full audit trail with minimal overhead
- Scalable: Can upgrade to GitHub Actions Phase 3+

---

## Approval

**Decision Made By**: Kevin Heaney (2026-05-10)  
**Status**: Accepted  
**Implementation**: Phase 2
