# Deployment Log: YYYY-MM-DD-HHMM UTC

## Status

Planned | In Progress | Successful | Rolled Back | Failed

## Scope

**Operator**: [Name]  
**Environment**: Local | Dry-run | Production  
**Related ADRs**: [ADR links]  
**Related Review**: [Review file or N/A]  
**Commit(s)**: [Commit hash range]  

## Change Summary

- [What changed]
- [Why the change is needed]
- [What is explicitly out of scope]

## Safety Classification

- [ ] Documentation/governance only
- [ ] Local infrastructure
- [ ] Dry-run runtime
- [ ] Production runtime
- [ ] Live trading impact

Live trading impact requires Kevin's explicit approval and independent review before execution.

## Pre-deployment Verification

- [ ] Current phase allows this change.
- [ ] No secrets, local databases, logs, or generated data are staged.
- [ ] `git status --short` reviewed.
- [ ] `pre-commit run --all-files` passed or blocker documented.
- [ ] Rollback procedure below is complete.
- [ ] UTC timestamp discipline confirmed for all new examples or code.

## Execution Timeline

| UTC Time | Step | Operator | Result |
| --- | --- | --- | --- |
| YYYY-MM-DDTHH:MM:SSZ | [Step] | [Name] | [Result] |

## Post-deployment Verification

- [ ] Expected files changed.
- [ ] Unexpected files absent.
- [ ] Logs reviewed if runtime components were touched.
- [ ] Reconciliation reviewed if account state was touched.
- [ ] Kill switch state reviewed if runtime safety was touched.

## Rollback Plan

1. [Stop or pause affected component, if any.]
2. [Run rollback command or revert commit.]
3. [Verify rollback result.]
4. [Record follow-up issue or review request.]

## Final Sign-off

**Completed At (UTC)**: YYYY-MM-DDTHH:MM:SSZ  
**Deployed By**: [Name]  
**Verified By**: [Name or independent reviewer]  
**Kevin Decision**: Approved | Rejected | Deferred  

## Notes

- [Operational notes, blockers, or follow-up actions]
