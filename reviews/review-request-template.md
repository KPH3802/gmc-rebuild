# Independent Review Request: [Artifact or Phase Gate]

## Status

Draft | Sent | In Review | Passed | Concerns | Failed

## Request Metadata

**Requested At (UTC)**: YYYY-MM-DDTHH:MM:SSZ  
**Requested By**: [Name]  
**Reviewer**: [Perplexity, ChatGPT, Gemini, other]  
**Decision Owner**: Kevin Heaney  
**Deadline**: YYYY-MM-DD  

## Project Context

`gmc-rebuild` is a governance-first rebuild of systematic trading infrastructure. The current phase is [Phase]. The reviewer should verify the submitted artifact against the stated phase boundary and must not recommend starting a later phase unless Kevin explicitly requested that assessment.

## Artifact Under Review

**Artifact Type**: ADR | README | Tooling | Template | Phase Gate | Other  
**Path(s)**: [Repository paths]  
**Commit(s)**: [Commit hash range]  

## Review Questions

1. Does the artifact satisfy the stated requirements?
2. Are there internal contradictions, dangling claims, or missing definitions?
3. Does the artifact stay inside the approved phase boundary?
4. Are safety controls, UTC rules, and secret-handling rules consistent?
5. What exact blockers, if any, must be fixed before approval?

## Out of Scope

- Do not propose trading strategy code.
- Do not propose broker execution code.
- Do not start a later phase.
- Do not request secrets, credentials, or local machine state.

## Required Reviewer Response Format

```text
Verdict: PASS | CONCERNS | FAIL

Blockers:
- [Blocker, file/path, and reason]

Non-blocking Concerns:
- [Concern and rationale]

Evidence Checked:
- [Artifacts reviewed]

Recommended Decision:
- [Approve, approve after fixes, reject, or defer]
```

## Submitted Evidence

Paste or link the artifact content, command output, and relevant diffs here.

## Kevin Decision

**Decision**: Accepted | Accepted with Conditions | Rejected | Deferred  
**Decided At (UTC)**: YYYY-MM-DDTHH:MM:SSZ  
**Notes**: [Decision notes]
