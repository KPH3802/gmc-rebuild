# AI WORKFLOW

This document defines the separation of duties between the AI assistants and the human decision-maker working on `gmc-rebuild`. It exists to keep the work auditable, to keep accountability with the human, and to avoid AI chaos — multiple AIs making conflicting changes, overwriting each other, or drifting outside the current phase.

If anything in another document conflicts with this file, this file wins for workflow questions until it is updated. `MASTER_STATUS.md` still wins for the current phase and the Phase 2 boundary.

---

## 1. Roles

There are exactly four roles. Each role has a single, well-defined responsibility.

### 1.1 Codex — Builder

- Writes and edits code, configuration, documentation, and tests.
- Makes the smallest change that satisfies the request.
- Stays inside the current phase as defined in `MASTER_STATUS.md`.
- Does **not** decide whether work is accepted.
- Does **not** decide whether a phase gate is passed.
- Does **not** verify its own output.

### 1.2 Perplexity Computer — Supervisor, Auditor, Verifier, Status Keeper

- Owns `MASTER_STATUS.md` and keeps it current.
- Owns the verification step for every Codex change before it is offered to Kevin.
- Audits diffs against the current phase boundary.
- Runs and reports the required proof (see Section 3) before declaring any task complete.
- Records and tracks blockers, open questions, and decisions awaiting Kevin.
- Does **not** approve Phase 2 work. Does **not** approve PRs.
- Does **not** silently rewrite Codex's work — verification findings are written up and returned to Codex for revision.

### 1.3 Kevin — Approver

- The only role that can accept work, approve a phase gate, authorize Phase 2, or merge a PR.
- The only role that can override an invariant, and only by recording the override as a governance change.
- Defines scope. Codex and Perplexity Computer execute and verify; they do not redefine scope.

### 1.4 Backup AI — Adversarial Reviewer (Optional, Conditional)

- Used **only** in three situations, defined in Section 4: phase gates, high-risk architecture decisions, and safety-critical decisions.
- Reviews adversarially: looks for ways the proposed change can fail, violate an invariant, or expand scope.
- Does **not** build, does **not** decide, does **not** edit files.
- Output is a written critique. Kevin reads it. Codex addresses it. Perplexity Computer re-verifies.

---

## 2. Standard Workflow

Every change follows the same path. No shortcuts.

1. **Kevin states the task** in writing, with the intended scope and phase.
2. **Perplexity Computer confirms** the task fits the current phase (per `MASTER_STATUS.md`) and records it. If it does not fit, Perplexity Computer pushes back before any work begins.
3. **Codex builds** the smallest change that satisfies the task. Codex pushes to a feature branch and opens a draft PR. Codex does not claim completion.
4. **Perplexity Computer verifies** using the required proof in Section 3. Findings are written up and returned to Codex if anything fails.
5. **Codex revises** without expanding scope. If a fix requires expanding scope, Codex stops and asks Kevin.
6. **Backup AI reviews adversarially** only if the task meets a Section 4 trigger.
7. **Kevin decides** whether to accept, request changes, or reject.
8. **Perplexity Computer updates** `MASTER_STATUS.md` to reflect the accepted state, including any new blockers or decisions.

---

## 3. Required Proof Before Accepting Completion

Perplexity Computer must collect and report **all** of the following before a task is declared complete. "It worked on my machine" is not proof. Screenshots are not proof. A claim with no command output is not proof.

### 3.1 Git state

```bash
git status                       # working tree must be clean after commit
git log --oneline -10            # head commit and recent history
git rev-parse HEAD               # exact commit hash under review
git diff <baseline>..HEAD        # full diff against the baseline being verified
```

`<baseline>` is the commit named in `MASTER_STATUS.md` §3 (the candidate or verified Phase 1 baseline). Verifiers may not silently substitute a different baseline; if a different baseline is appropriate for the task at hand, that must be agreed with Kevin and recorded before verification begins.

The reported commit hash must match the commit referenced in the PR.

### 3.2 Tests and pre-commit

```bash
pre-commit run --all-files       # required to pass, or every failure must be documented
pytest                           # required to pass
```

Full output, not summaries. If any hook is skipped, the reason must be in the report.

### 3.3 Phase-boundary check

Confirm the diff does not introduce any of the items listed in `MASTER_STATUS.md` Section 6 ("What Is Explicitly Not Present"). At minimum:

- No new top-level directories outside the documented set.
- No new modules under names like `strategy/`, `signals/`, `broker/`, `execution/`, `live/`, `daemons/`, `data/`, or similar.
- No new long-running entry points (`if __name__ == "__main__"` services, scheduler configs, background workers).
- No new secrets, credentials, or generated data files.

### 3.4 File-specific evidence

For each file changed, the verification report names the file and states what was verified for it. Examples:

- For a new ADR: required headings present, decision recorded, status set, links valid.
- For a template change: structure preserved, instructions still clear, no placeholder leakage.
- For a config change: settings match what the README, ADRs, and `MASTER_STATUS.md` claim.
- For a documentation change: cross-references still resolve, phase claims still accurate.

A verification report with no file-specific evidence is not a verification.

---

## 4. When to Use the Backup AI

The backup AI is opt-in and conditional. It is not part of the default flow. Use it **only** for:

1. **Phase gates.** Before Kevin is asked to close a phase or open the next phase, the backup AI reviews the artifacts and the verification report adversarially.
2. **High-risk architecture decisions.** Any ADR that defines a new control surface, a new trust boundary, or a non-reversible decision. Examples: secrets management, kill switch, reconciliation, deployment process.
3. **Safety-critical decisions.** Any change that, if wrong, could cause real-world loss: live trading authorization, broker integration, kill switch behavior, operator heartbeat policy, data retention or destruction policy.

Do not invoke the backup AI for routine documentation edits, template tweaks, dependency bumps that match committed versions, or typo fixes. Routine use erodes its signal.

---

## 5. How to Constrain the Backup AI

The backup AI is adversarial, not authoritative. To keep it useful and bounded:

- Give it a **narrow brief**: the single decision under review, the relevant invariants, and the verification report. Do not give it the whole repository unless the review is repository-wide.
- Ask it to produce a **written critique only**. No code edits, no PRs, no commits.
- Ask it to identify **specific failure modes**, not generic warnings. "This violates invariant 8 because X" is useful. "Consider security" is not.
- Treat its output as **input to Codex and Kevin**, not a verdict. Kevin decides. Codex revises. Perplexity Computer re-verifies after the revision.
- If the backup AI flags something outside the current phase, scope it down rather than expanding the work.

---

## 6. How to Avoid AI Chaos

Rules that exist specifically to prevent multiple AIs from creating contradictory state, overwriting each other, or drifting outside the current phase.

1. **One builder at a time.** Only Codex writes to the repository in a given task. The backup AI never writes. Perplexity Computer never silently rewrites Codex's work — it returns findings.
2. **One status keeper.** Only Perplexity Computer updates `MASTER_STATUS.md`. Codex may propose updates in a PR but does not land them without Perplexity Computer's verification.
3. **One approver.** Only Kevin accepts, merges, or authorizes phase transitions. No AI may infer approval from silence.
4. **One branch per task.** Codex works on a feature branch named for the task. No direct commits to the default branch. This rule applies prospectively from the adoption of `AI_WORKFLOW.md` on `main` (commit `b39d036`, which introduced this file); pre-adoption history on the default branch is not retroactively invalidated by this rule, but every change after adoption goes through a feature branch and PR.
5. **No cross-AI chatter in the repo.** AIs do not commit "notes to each other" into the codebase. Discussion belongs in PR comments or session logs, not in files under version control. Tool attribution in commit messages and PR descriptions (e.g., a trailer line indicating which assistant produced a change) is allowed and is not considered "chatter"; this rule covers content that lands under version control. Any AI-authored claim that does land in a file — including commit trailers, PR-description boilerplate, and inline notes — must be factually verifiable, must not assert verification that has not actually been performed, and must not impersonate a human reviewer or claim authority the AI does not have. If an AI cannot back a claim with the proof bundle in §3, the claim must be removed before merge.
6. **No retroactive scope changes.** If verification reveals the task as stated is wrong, stop and ask Kevin. Do not silently broaden the scope to fix it.
7. **No phase drift.** If a change starts to require Phase 2 capability to be useful, stop. Either narrow the change or wait for Phase 2 authorization. Phase 1 stays Phase 1.
8. **No tooling relaxation under pressure.** If pre-commit, mypy strict, or detect-secrets fails, fix the underlying issue. Do not weaken the hook to make the failure go away.
9. **Every claim has evidence.** "Tests pass" without output is not a claim Perplexity Computer accepts. "It should be safe" without an invariant cite is not a claim Kevin accepts.
10. **When in doubt, stop.** A paused task is recoverable. A merged Phase 2 change made by accident is not.
