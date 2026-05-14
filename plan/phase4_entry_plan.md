# Phase 4 Entry Plan

**Status:** Planning only — Phase 4 is **not** open. No Phase 4 task is authorized by this document. No runtime activation of any merged Phase 3 fixture is authorized by this document.
**Created:** 2026-05-14 UTC
**Owner:** Perplexity Computer (supervisor), planning workstream authorized by Kevin on 2026-05-14 per `governance/authorizations/2026-05-14_phase-4-entry-planning.md`.
**Scope:** This document plans the entry to Phase 4. It does not implement Phase 4, does not authorize any Phase 4 task (`P4-01`, `P4-02`, …), does not authorize any runtime activation of any merged Phase 3 fixture (`InMemoryHeartbeat`, `InMemoryKillSwitch`, `InMemoryReconciliation`), does not extend the `MASTER_STATUS.md` §8 step 4a `allowed_p2_infra` allowlist, does not modify any quality gate, does not modify any file under `src/**` or `tests/**`, and does not change any always-forbidden category in `MASTER_STATUS.md` §6.

If anything here conflicts with `MASTER_STATUS.md` or `AI_WORKFLOW.md`, those files win. This document is supporting planning material for a future Phase 4 entry decision; it does not redefine the phase boundary, and it does not make the phase gate decision itself.

This plan is the Phase 4 analogue to `plan/phase3_entry_plan.md`. It mirrors that file's structure deliberately so the pattern is the same and is reviewable on the same axes. Where this plan names a future Phase 4 task (`P4-01`, `P4-02`, …), the task is **future / not-authorized** and requires its own separate written authorization from Kevin, a sibling artifact under `governance/authorizations/`, applicable Mode A / Mode B review per `AI_WORKFLOW.md` §4 and ADR-008 / ADR-009 before it may be opened, and (where it introduces a new directory) a corresponding update to the §8 step 4a allowlist in the same PR.

---

## 1. Current Status

- **Phase 1 accepted baseline:** `1f101fc` (`docs: fix Phase 1 verification blockers`), accepted per Kevin's written acceptance note on PR #3 (see `MASTER_STATUS.md` §3). Phase 1 baseline is unchanged by this plan.
- **Phase 2 implementation:** **Fully merged through P2-05; Phase 2 formally closed (governance-only).** The `plan/phase2_entry_plan.md` §4 P2-01..P2-05 sequence is merged on `main`. Phase 2 closure is recorded at `governance/authorizations/2026-05-12_phase-2-closure.md`.
- **Phase 3 implementation:** **Limited to the three merged in-memory test fixtures (P3-03 HeartbeatProtocol, P3-04 KillSwitchProtocol, and P3-05 ReconciliationProtocol).** P3-03 merged via PR #42 at `c5e868c` (with sibling Mode B PR #43 at `07aee55` and follow-on lint remediation PR #44 at `db6d6fb` with sibling Mode B PR #45 at `70ebc8f`); P3-04 merged via PR #48 at `1a7949c` (with sibling Mode B PR #49 at `2db57db`); P3-05 merged via PR #52 at `5abf8c8` (with sibling Mode B PR #53 at `b886e19`). Their post-merge status reconciliations PR #46 / PR #50 / PR #54 are also on `main`.
- **Phase 3 closure status:** **Merged on `main` as of 2026-05-14** per Kevin's written authorization at `governance/authorizations/2026-05-14_phase-3-closure.md`. The Mode B sibling monitoring PR — PR #57 — merged first at `302dff6`, and the Phase 3 closure PR — PR #56 — then merged at `3131a69`. The closure is governance-only and **does not open Phase 4, does not authorize any runtime activation of any merged Phase 3 fixture, does not authorize a fourth protocol fixture or any further Phase 3 implementation, does not extend the §8 step 4a allowlist (the eight P2-01..P2-05 + P3-03 + P3-04 + P3-05 entries are preserved exactly), does not relax any quality gate, did not add or modify any file under `src/**` or `tests/**`, and did not create any tag or release**. The post-merge status reconciliation PR #58 merged at `0a91261` with sibling Mode B packet PR #59 merged first at `c910c9a`; that reconciliation is on the current `main` head.
- **Phase 4 entry planning:** Authorized by Kevin on 2026-05-14 as a **governance/documentation-only** workstream per `governance/authorizations/2026-05-14_phase-4-entry-planning.md`. That authorization is **planning-only**: it opens the planning workstream that drafts this document; it does **not** open Phase 4, does **not** authorize any Phase 4 implementation, does **not** authorize any runtime activation of any merged Phase 3 fixture, does **not** name a specific Phase 4 task, does **not** extend the `MASTER_STATUS.md` §8 step 4a allowlist, and does **not** modify any quality gate.
- **Phase 4 implementation:** **None.** No Phase 4 task is opened, no Phase 4 directory exists, no `src/**` or `tests/**` file has been added under any Phase 4 name, and no §8 step 4a allowlist entry has been added. Phase 4 entry itself remains a future, separate written authorization from Kevin and is itself a phase gate per `AI_WORKFLOW.md` §4(1).
- **Workflow in effect:** Codex builds → Perplexity Computer verifies → Kevin approves → Backup AI reviews adversarially at gates and high-risk decisions (per `AI_WORKFLOW.md` §1, §2, §4) and authors monitoring packet text under Mode B per ADR-008 (and ADR-009 once runtime exists on `main` per ADR-009 D7's bootstrap-avoidance clause).

Until Kevin records a separate written authorization that opens Phase 4 (or a specific Phase 4 task) and the entry criteria in Section 5 below are met, the only allowed work is the planning workstream defined in `governance/authorizations/2026-05-14_phase-4-entry-planning.md` and the routine maintenance categories listed in `MASTER_STATUS.md` §9.

---

## 2. Phase 4 Objective (Planning Level Only)

This section restates a candidate Phase 4 objective at the **planning level** only. Naming an objective here does not authorize implementation. Phase 4 implementation requires a separate written authorization from Kevin. Phase 4 may, when authorized, be redefined in writing by Kevin to a narrower or different objective than the one sketched here; this section is a starting point for that authorization conversation, not a forward commitment.

Phase 4 is conceived, **for planning purposes only**, as the **next infrastructure phase** that would sit on top of the merged P2-01..P2-05 + P3-03 + P3-04 + P3-05 foundation. Its planning-level purpose is to define, at a documentation level, how the three merged in-memory single-protocol fixtures (`InMemoryHeartbeat`, `InMemoryKillSwitch`, `InMemoryReconciliation`) could be **composed, governed, and exercised together** under unit-test conditions — still without any broker integration, without any live or paper trading wired to a real broker, without any market data ingestion, without any order placement, and without any scheduler / daemon / background worker / runtime activation affecting accounts or markets.

In planning scope only (Section 3 below defines what may be discussed; Section 4 names candidate task sequences; **none of this is implementation authorization**):

- Local-only, sandboxed scaffolding that would allow a future composed test-fixture exercise of the three in-memory fakes under `pytest`, with no network, no broker SDK, no real account identifiers, no real venue identifiers, no real endpoints, and no real secrets.
- Per-control proof-bundle expectations that align with `plan/phase3_entry_plan.md` §6 and `AI_WORKFLOW.md` §3, adjusted for any additional ADR follow-up that surfaces at the time of Phase 4 authorization.
- ADR follow-ups that any Phase 4 entry decision would require — at minimum any ADR-009 implications that surface at the time of authorization, with implications for ADR-001 (secrets management), ADR-002 (kill switch), ADR-003 (reconciliation), ADR-005 (heartbeat), ADR-006 (deployment logs), and ADR-007 (minimal CI).

**Out of planning scope**, and forbidden until a Phase 4 task is opened in writing by Kevin (and forbidden at the always-forbidden category level per `MASTER_STATUS.md` §6 independent of phase):

- Trading strategy code (signals, scanners, models, portfolio rules, backtests against real history).
- Broker execution code (order placement, position management, broker SDK integration, broker authentication).
- Live or paper trading workflows wired to a real broker.
- Runtime daemons, schedulers, long-running services, background workers, operator-availability heartbeats wired to a real operator, or anything with a `__main__` entry point that touches accounts, markets, or money.
- Runtime activation of any merged Phase 3 fixture — `InMemoryHeartbeat`, `InMemoryKillSwitch`, or `InMemoryReconciliation` — from a `__main__`, a daemon, a scheduler, a re-export in `src/gmc_rebuild/__init__.py`, or any other runtime path.
- Market data ingestion code, real data pipelines, committed datasets, real or historical feeds.
- Real secrets, real credentials, real account identifiers, real broker / venue identifiers, real endpoints.
- Any concrete implementation of `KillSwitchProtocol`, `ReconciliationProtocol`, or `HeartbeatProtocol` that talks to a broker, network, filesystem outside the test sandbox, or scheduler.
- Any change that loosens `.gitignore`, `.pre-commit-config.yaml`, mypy strict mode, `detect-secrets`, the `MASTER_STATUS.md` §8 step 4 always-forbidden scan, the §8 step 4a per-PR Phase 2 / Phase 3 infrastructure allowlist scan, or the §8 step 4c recursive forbidden-token scan.
- Any new git tag, GitHub release, or version bump.

This split is intentional and mirrors the line `MASTER_STATUS.md` §6 / §7 already draws and that `plan/phase3_entry_plan.md` §2 restated for Phase 3. Phase 4 planning does not move that line; it discusses what would sit underneath it.

---

## 3. Allowed Planning Topics

While Phase 4 entry planning is in this opened-but-unscoped state (per `governance/authorizations/2026-05-14_phase-4-entry-planning.md`), Codex and Perplexity Computer may discuss and write planning artifacts on the following topics. Planning artifacts are documents, not code, and must be reviewable as documents. This list mirrors `plan/phase3_entry_plan.md` §3 and the "Allowed Planning Topics" list in `governance/authorizations/2026-05-14_phase-4-entry-planning.md` deliberately, so the pattern is the same:

1. **Phase 4 objective in prose.** What step Phase 4 would build on top of the merged P2-01..P2-05 + P3-03 + P3-04 + P3-05 foundation, restated at a level that does not authorize any specific implementation and does not authorize any runtime activation. Section 2 of this plan is the canonical planning-level statement.
2. **Candidate future Phase 4 task sequence** (`P4-01`, `P4-02`, …). Named only as **future / not-authorized** PRs that would each require their own separate written authorization slice and sibling artifact under `governance/authorizations/`. Naming a task in Section 4 of this plan does **not** authorize it.
3. **Phase 4 entry criteria.** What must be true (baseline, governance, ADRs, monitoring cadence under ADR-008 §D3 / §D5 during the governance phase and ADR-009 D3 / D5 once runtime exists on `main` per ADR-009 D7's bootstrap-avoidance clause, Mode A / Mode B review per `AI_WORKFLOW.md` §4) before any Phase 4 implementation PR could open. Section 5 of this plan is the canonical planning-level statement.
4. **Per-PR proof-bundle expectations for any future Phase 4 PR.** Restated from `AI_WORKFLOW.md` §3 and `plan/phase3_entry_plan.md` §6. Section 6 of this plan is the canonical planning-level statement.
5. **Rollback and stop conditions.** Restated for Phase 4 from `plan/phase3_entry_plan.md` §8. Section 8 of this plan is the canonical planning-level statement.
6. **Phase-boundary enforcement.** How Phase 4 PRs would prove they did not cross into trading strategy, broker execution, live or paper trading wired to a real broker, real market data ingestion, real secrets, or any other always-forbidden category in `MASTER_STATUS.md` §6. Section 6 and Section 8 of this plan record the planning-level expectations.
7. **ADR follow-ups.** Listed in Section 9 of this plan at planning level only.

Any planning topic that does not fit the list above must be raised with Kevin before a document is written, per `governance/authorizations/2026-05-14_phase-4-entry-planning.md` "Allowed Planning Topics" and `AI_WORKFLOW.md` §6 rule 7 ("No phase drift").

---

## 4. Candidate Future Phase 4 Task Sequence (Future / Not Authorized)

The following sequence is a **planning-level proposal**. It names candidate future PRs only. **Every item below is future / not-authorized.** None of these tasks may begin, no Phase 4 directory may be created, no `src/**` or `tests/**` file may be added under any of these names, no runtime activation of any merged Phase 3 fixture may occur, and no §8 step 4a allowlist entry may be added until each of the gates listed in Section 7 below is independently satisfied for the specific task being opened.

This sequence is deliberately **minimal**. Enumerating a long list of candidate tasks here would invite scope drift before the Phase 4 entry decision has been made. Any future enumeration beyond what is listed below must itself be authorized as a documentation-only update to this plan, per `governance/authorizations/2026-05-14_phase-4-entry-planning.md` "Allowed Planning Topics" item 2.

1. **PR P4-01 — (future / not authorized) Phase 4 entry decision (phase-gate PR).** The actual decision to **open Phase 4**. Records Kevin's written authorization to enter Phase 4, names the first Phase 4 task scope, and (where it introduces a directory) extends the `MASTER_STATUS.md` §8 step 4a allowlist in the same PR per the standing rule in §8 step 4b. **Not authorized.** This is a **phase gate** by definition and requires Mode A adversarial review per `AI_WORKFLOW.md` §4(1) and a Mode B monitoring packet per ADR-008 §D3 / §D5 (or ADR-009 D3 / D5 once in force per ADR-009 D7's bootstrap-avoidance clause).

Further candidate tasks (P4-02, P4-03, …) are deliberately **not enumerated** in this plan. The shape of Phase 4 — whether it is a composed-fixture test-only phase, a runtime-bootstrapping phase, an ADR-driven follow-up phase, or a different shape entirely — is itself a decision that Kevin must make in writing at the time of the Phase 4 entry authorization. This plan therefore stops at naming the entry-decision PR (P4-01) and explicitly does **not** pre-commit any successor task. Any later enumeration of P4-02 / P4-03 / … must be authorized as a documentation-only update to this plan and must not authorize implementation.

Sequencing rules (planning-level, mirroring `plan/phase3_entry_plan.md` §4):

- Tasks land one at a time. PR P4-(N+1) is not opened until PR P4-N is accepted by Kevin.
- Each PR is small enough that the diff and the proof bundle (Section 6) fit a single review.
- Any PR that grows beyond its stated scope during implementation is split or stopped per `AI_WORKFLOW.md` §6 rule 6 / rule 7.
- The Phase 4 entry decision (P4-01 above) must land **before** any test-fixture or runtime work under any later Phase 4 task is authorized.

**§8 step 4a allowlist note.** The `allowed_p2_infra` allowlist contains exactly eight entries on the post-merge `main` (`src`, `src/gmc_rebuild/config`, `src/gmc_rebuild/time`, `src/gmc_rebuild/logging`, `src/gmc_rebuild/risk`, `src/gmc_rebuild/heartbeat`, `src/gmc_rebuild/kill_switch`, `src/gmc_rebuild/reconciliation`); the sixth entry was added by PR #42 (P3-03 implementation), the seventh entry was added by PR #48 (P3-04 implementation), and the eighth entry was added by PR #52 (P3-05 implementation). This plan does **not** extend that allowlist further. Any future Phase 4 PR that introduces a new directory must add it to the allowlist in the same PR that introduces the directory, per the standing rule in `MASTER_STATUS.md` §8 step 4b, and must be authorized in writing for the specific directory by Kevin.

---

## 5. Phase 4 Entry Criteria (Planning Level Only)

Phase 4 implementation may begin only when **all** of the following are true and recorded. Listing the criteria here does not by itself open Phase 4; opening Phase 4 requires Kevin's written authorization recorded in a sibling artifact under `governance/authorizations/` per `AI_WORKFLOW.md` §7.

1. The accepted Phase 1 baseline is `1f101fc` (per `MASTER_STATUS.md` §3) and `main` is a descendant of it (`MASTER_STATUS.md` §8 step 3 returns OK).
2. Phase 2 is formally closed (governance-only) per `governance/authorizations/2026-05-12_phase-2-closure.md`. **Satisfied as of 2026-05-12.**
3. Phase 3 is formally closed (governance-only) per `governance/authorizations/2026-05-14_phase-3-closure.md`. **Satisfied as of 2026-05-14.**
4. Phase 4 entry **planning** has been authorized by Kevin in writing per `governance/authorizations/2026-05-14_phase-4-entry-planning.md`. **Satisfied as of 2026-05-14.** Note that this planning authorization does **not** by itself satisfy criterion 6 below — opening Phase 4 requires a separate authorization.
5. This Phase 4 Entry Plan (`plan/phase4_entry_plan.md`) has been merged on `main` as planning-only documentation. (This document targets that merge; merging this document does not by itself open Phase 4.)
6. Kevin has explicitly authorized Phase 4 entry in writing — commit message, PR comment, or governance entry, not a chat message — per `MASTER_STATUS.md` §7.3 and recorded in a sibling artifact under `governance/authorizations/` per `AI_WORKFLOW.md` §7. Authorization of "Phase 4 in general" does not by itself authorize any specific P4-0N implementation PR; each first PR's scope must also be named in the authorization, per the §7.4 pattern that `plan/phase3_entry_plan.md` §5 applied to P3-0N and that `plan/phase2_entry_plan.md` §5 applied to P2-0N.
7. The Phase 4 entry decision has been reviewed in **Mode A** by the Backup AI per `AI_WORKFLOW.md` §4(1) (phase gate). The Mode A critique is delivered as PR-review text and is **not** committed to the repository (per `AI_WORKFLOW.md` §6 rule 5).
8. A **Mode B** monitoring packet has been authored by the Backup AI per ADR-008 §D3 (or ADR-009 D3 once in force per ADR-009 D7's bootstrap-avoidance clause) and committed by Codex under `monitoring/daily/` per ADR-008 §D4 (or ADR-009 D4) for the active workday on which the Phase 4 entry PR is open / merged. Per ADR-008 §D5, no phase-opening or phase-expanding PR may merge while any required packet from any prior active workday is missing without a catch-up note covering it; Perplexity Computer confirms this before verifying the Phase 4 entry PR.
9. The first Phase 4 PR is the candidate task named in Section 4 above (P4-01 phase-gate decision), unless Kevin pre-approves a different narrow plan in writing. The first Phase 4 implementation PR (if and when one is authorized after P4-01) must be infrastructure-only at the planning-level definition of Section 2 above (sandboxed, local-only, no broker, no live or paper trading wired to a real broker, no market data, no order placement, no scheduler / daemon, no real secrets, no runtime activation of any merged Phase 3 fixture).

If any criterion fails, Phase 4 stays closed. Phase 3 stays formally closed. Phase 2 stays formally closed. Routine governance maintenance under `MASTER_STATUS.md` §9 continues.

---

## 6. Required Proof For Each Future Phase 4 PR

Each future Phase 4 PR must include the proof bundle defined in `AI_WORKFLOW.md` §3 and restated in `plan/phase3_entry_plan.md` §6. Restated here for Phase 4 scope.

1. **Git state.**
   - `git status` showing a clean tree after commit.
   - `git log --oneline -10` showing the head commit and recent history.
   - `git rev-parse HEAD` showing the exact commit hash under review.
   - `git diff <baseline>..HEAD` against the accepted Phase 1 baseline `1f101fc` (or a later accepted baseline if one has been recorded in `MASTER_STATUS.md` §3 by that time).
2. **Tests and pre-commit.**
   - Full output of `pre-commit run --all-files` (must pass, or every failure documented).
   - Full output of `pytest` (must pass).
3. **Phase-boundary checklist.** For each Phase 4 PR, the verification report explicitly confirms:
   - No new top-level directories outside the documented set.
   - No new modules under `strategy/`, `signals/`, `broker/`, `execution/`, `live/`, `daemons/`, `data/`, `market_data/`, `orders/`, `secrets/`, or any name on the `MASTER_STATUS.md` §8 step 4 always-forbidden list, anywhere in the tree (the §8 step 4c recursive forbidden-token scan returns OK / subshell exit `0`).
   - No new long-running entry points (`if __name__ == "__main__"` services, scheduler configs, background workers, daemons).
   - No new secrets, real credentials, real account identifiers, real broker / venue identifiers, real endpoints, or generated data files.
   - No new broker SDK dependency, no new market-data SDK dependency, no new scheduler or background-job dependency.
   - No runtime activation of any merged Phase 3 fixture — `InMemoryHeartbeat`, `InMemoryKillSwitch`, or `InMemoryReconciliation` — from a `__main__`, a daemon, a scheduler, a re-export in `src/gmc_rebuild/__init__.py`, or any other runtime path, unless the specific activation is named in Kevin's separate written authorization for the PR and is itself subject to Mode A per `AI_WORKFLOW.md` §4(2).
   - No new concrete implementation of `KillSwitchProtocol` / `ReconciliationProtocol` / `HeartbeatProtocol` that talks to a broker, network, filesystem outside the test sandbox, or scheduler.
   - No relaxation of `.gitignore`, `.pre-commit-config.yaml`, mypy strict mode, `detect-secrets`, `.secrets.baseline`, the `MASTER_STATUS.md` §8 step 4 always-forbidden scan, the §8 step 4a per-PR Phase 2 / Phase 3 infrastructure allowlist scan, or the §8 step 4c recursive forbidden-token scan.
   - Any new authorized directory is added to the `MASTER_STATUS.md` §8 step 4a allowlist in the same PR that introduces the directory, per the standing rule in §8 step 4b.
4. **File-specific evidence.** Per `AI_WORKFLOW.md` §3.4, each changed file is named and the verifier states what was verified for it (required headings present, decision recorded, status set, links valid for ADRs; structure preserved, instructions still clear, no placeholder leakage for templates; settings match what the README, ADRs, and `MASTER_STATUS.md` claim for config changes; cross-references still resolve, phase claims still accurate for documentation changes).
5. **Docs updated.** Any change to interfaces or conventions is reflected in the relevant document (ADR update, new ADR, or `MASTER_STATUS.md` entry) in the same PR — no orphaned code without a governance hook.
6. **ADR-009 cadence status.** The verification report names whether ADR-008 §D3 / §D5 (governance-phase cadence) or ADR-009 D3 / D5 (runtime-phase cadence) governs the PR per ADR-009 D7's bootstrap-avoidance clause. Until runtime exists on `main`, ADR-008 §D3 / §D5 continue to govern.
7. **Mode A / Mode B status.** The verification report names whether `AI_WORKFLOW.md` §4 Mode A and ADR-008 §D3 (or ADR-009 D3) Mode B apply to the PR, and where each artifact lives (PR-review text for Mode A; `monitoring/daily/YYYY-MM-DD.md` for Mode B). For phase-gate PRs and high-risk-architecture PRs, **both** artifacts are required per ADR-008 §D7 (or ADR-009 D7 once in force).

A Phase 4 PR that does not carry this bundle is not eligible for Kevin's review.

---

## 7. Review Protocol

Standard review per `AI_WORKFLOW.md` §2:

1. Kevin states the task in writing.
2. Perplexity Computer confirms the task fits the current phase and records it.
3. Codex builds the smallest change on a feature branch and opens a draft PR.
4. Perplexity Computer verifies using the proof bundle (Section 6) and returns findings if anything fails.
5. Codex revises without expanding scope.
6. Kevin decides.

**Mode A adversarial backup review** per `AI_WORKFLOW.md` §4 and §5 is required at:

- The Phase 4 entry decision itself (the phase gate that opens Phase 4 — `AI_WORKFLOW.md` §4(1) by definition).
- Any subsequent Phase 4 PR that defines a new control surface, a new trust boundary, or a non-reversible decision — `AI_WORKFLOW.md` §4(2). Examples include any first runtime activation of any merged Phase 3 fixture, any ADR update that changes the kill-switch / reconciliation / heartbeat policy, and any change that touches the secrets-management discipline.
- Any Phase 4 PR that would, if wrong, cause real-world loss — `AI_WORKFLOW.md` §4(3). Such a PR is by definition **out of Phase 4 scope** per Section 2 (no live trading authorization, no broker integration, no live or paper trading wired to a real broker, no operator-availability heartbeat wired to a real operator, no data retention or destruction policy that affects real accounts or markets). The correct response is to treat it as scope drift and stop per `AI_WORKFLOW.md` §6 rule 7 and Section 8 of this plan, **not** to invoke the Backup AI in Mode A as a substitute for stopping.

**Mode B continuous governance monitor** per ADR-008 §D3 (or ADR-009 D3 once in force per ADR-009 D7's bootstrap-avoidance clause) is required on any active workday on which the default branch changes or a pull request is open, updated, or merged. The Backup AI authors packet text; Codex commits per `AI_WORKFLOW.md` §1.4 and §6 rule 1 and ADR-008 §D1 (or ADR-009 D1). When both Mode A and Mode B fire on the same PR — and every Phase 4 phase-gate or high-risk-architecture PR will — **two distinct artifacts are required** per ADR-008 §D7 (or ADR-009 D7 once in force): the Mode A written critique (PR-review text only, not committed to the repo) and the Mode B monitoring packet (committed by Codex under `monitoring/daily/`). The packet may link to or quote the critique for context, but does not replace it.

The Backup AI produces a written critique only (Mode A) or packet text only (Mode B). It does not edit other files, does not commit, does not push, does not merge, and does not approve. `AI_WORKFLOW.md` §6 rule 1 ("One builder at a time") is preserved: Codex remains the only role that writes to the repository.

---

## 8. Rollback and Stop Conditions

Phase 4 entry, and each future Phase 4 PR, must support a clean rollback.

Rollback rules:

- Every Phase 4 PR is reversible by a single `git revert` on the merge commit. PRs that bundle unrelated changes are split until this is true.
- The accepted Phase 1 baseline (`1f101fc` per `MASTER_STATUS.md` §3) is the last-known-good state. Reverting all Phase 2, Phase 3, and Phase 4 work returns the tree to a descendant of that baseline.
- A deployment log entry per `docs/deploys/deploy-log-template.md` is required if any Phase 4 change affects developer environments (e.g. new tooling requirement, new pre-commit hook), even though no runtime is being deployed under the planning-level definition of Section 2.
- Once runtime exists on `main`, ADR-009 D5's missed-packet severity replaces ADR-008 §D5 on a going-forward basis per ADR-009 D7's bootstrap-avoidance clause. Until runtime exists, ADR-008 §D5 continues to apply.

Stop conditions — if any of the following occurs, Phase 4 work pauses and the situation is escalated to Kevin before further changes:

1. A Phase 4 PR cannot satisfy the proof bundle in Section 6 without expanding scope.
2. A Phase 4 PR is found to cross into strategy, broker, live or paper trading wired to a real broker, market data ingestion, real secrets, order placement, scheduler / daemon, persistence outside the test sandbox, runtime-daemon territory, or runtime activation of any merged Phase 3 fixture beyond what is named in the PR's separate written authorization — at review time or after merge.
3. `pre-commit` or `pytest` fails and the proposed fix is to weaken the hook, loosen mypy strict mode, relax `detect-secrets`, or modify `.secrets.baseline` to silence a real finding.
4. `MASTER_STATUS.md` and a Phase 4 PR disagree about the current phase, the accepted baseline, the `allowed_p2_infra` allowlist, or the allowed next decisions.
5. Two changes attempt to land on the default branch simultaneously, violating `AI_WORKFLOW.md` §6 rule 4 (one builder, one branch per task).
6. The Backup AI (when invoked per Section 7) identifies a specific invariant violation that the verifier did not catch.
7. A required Mode B monitoring packet under ADR-008 §D3 (or ADR-009 D3 once in force) is missing for a prior active workday and no catch-up note per ADR-008 §D5 (or ADR-009 D5) has been committed. Per ADR-008 §D5, no phase-opening or phase-expanding PR may merge under that condition.
8. A Phase 4 PR proposes to re-export `InMemoryHeartbeat`, `InMemoryKillSwitch`, or `InMemoryReconciliation` from `src/gmc_rebuild/__init__.py`, or to consume any of them from a `__main__` / daemon / scheduler / runtime path, without that specific activation being named in Kevin's separate written authorization and without Mode A per `AI_WORKFLOW.md` §4(2).

In any stop condition, the default is to pause and ask Kevin. Per `AI_WORKFLOW.md` §6 rule 10: "When in doubt, stop. A paused task is recoverable. A merged Phase 4 change made by accident is not."

---

## 9. ADR Follow-ups That Phase 4 Entry Requires

Listed here for planning visibility. None of these follow-ups is authorized by this plan. Each requires its own separate written authorization from Kevin, a sibling artifact under `governance/authorizations/`, and the applicable Mode A / Mode B review per `AI_WORKFLOW.md` §4 and ADR-008 (or ADR-009 once in force).

- **ADR-009 — runtime monitoring cadence and missed-packet severity.** Accepted on 2026-05-13 per `governance/authorizations/2026-05-13_p3-01-acceptance.md`. ADR-009 D7's bootstrap-avoidance clause keeps ADR-008 §D3 / §D5 in force until runtime exists on `main`. Any Phase 4 PR that introduces runtime must satisfy the ADR-009 D3 / D5 cadence as it takes effect, plus any further ADR follow-up that surfaces at the time of authorization. If a Phase 4 implementation PR ever introduces runtime, the verification report names the cadence transition explicitly.
- **ADR-001 — secrets management.** Phase 4 introduces no real secrets, no real credentials, no real account identifiers, no real broker / venue identifiers, and no real endpoints under the Section 2 planning-level definition. If any later Phase 4 task ever needs to reference a real secret (it must not, under Section 2), ADR-001's secrets-management discipline must be revisited in a separate PR before the reference lands. This plan does not authorize that revisit.
- **ADR-002 — runtime kill-switch architecture.** The P3-04 `InMemoryKillSwitch` fake conforms to `KillSwitchProtocol` (ADR-002) at the test-fixture level. Any Phase 4 use of the fake must align with ADR-002 and must not add broker side effects, order placement, or network calls. If a Phase 4 use surfaces a gap in ADR-002, the gap is recorded in an ADR update, not silently coded around.
- **ADR-003 — broker reconciliation discipline.** The P3-05 `InMemoryReconciliation` fake conforms to `ReconciliationProtocol` (ADR-003) at the test-fixture level with `UNAVAILABLE` / `FAILED` distinguished. Any Phase 4 use of the fake must align with ADR-003 and must not add broker integration, account fetch, fills, or order objects.
- **ADR-005 — operator availability heartbeat.** The P3-03 `InMemoryHeartbeat` fake conforms to `HeartbeatProtocol` (ADR-005) at the test-fixture level. Any Phase 4 use of the fake must align with ADR-005 and must not add a scheduler, an operator-availability daemon, or an external sink.
- **ADR-006 — deployment logs.** Any Phase 4 change that affects developer environments requires a deployment log entry per `docs/deploys/deploy-log-template.md`. No runtime deployment is authorized; the deployment-log discipline applies to developer-environment changes only.
- **ADR-007 — minimal CI strategy.** The local quality-gate stack (pre-commit, Ruff, mypy strict, detect-secrets, pytest) is unchanged by this plan. Any Phase 4 PR that proposes a CI change must do so as a separate ADR update reviewed under `AI_WORKFLOW.md` §4(2).

The list above is not exhaustive. Any later ADR follow-up that surfaces during the planning workstream must be raised with Kevin and recorded in a sibling artifact under `governance/authorizations/` before the follow-up PR opens.

---

## 10. Explicitly Not Authorized

For audit clarity, the following categories remain forbidden under this planning document. Each is forbidden by default per `MASTER_STATUS.md` §6 and `governance/authorizations/2026-05-14_phase-4-entry-planning.md` "Explicitly Not Authorized"; mirroring them here is **not** a re-authorization and is **not** a relaxation. Each requires Kevin's separate written authorization per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 / rule 7, a sibling artifact under `governance/authorizations/`, the applicable Mode A / Mode B review, and (where it introduces a new directory) a corresponding update to the §8 step 4a allowlist in the same PR.

- **Opening Phase 4.** This document plans Phase 4 entry; it does not open Phase 4. The Phase 4 entry decision is a future, separate written authorization (candidate task P4-01 in Section 4) and is itself a phase gate per `AI_WORKFLOW.md` §4(1).
- **Any specific Phase 4 task (P4-01, P4-02, …).** Naming a candidate task in Section 4 above is planning-level discussion, not authorization. Each task requires its own separate written authorization.
- **Runtime activation of any merged Phase 3 fixture.** The `InMemoryHeartbeat` (P3-03), `InMemoryKillSwitch` (P3-04), and `InMemoryReconciliation` (P3-05) fakes remain test-fixture infrastructure only. No re-export from `src/gmc_rebuild/__init__.py`, no consumption from a `__main__`, no consumption from a daemon, no consumption from a scheduler, no consumption from any runtime path is authorized by this plan.
- **Any new Phase 3 task beyond P3-05.** The three in-memory protocol-conformance test fixtures (P3-03 HeartbeatProtocol, P3-04 KillSwitchProtocol, P3-05 ReconciliationProtocol) are exhausted; no fourth protocol fixture, no P3-06, and no sibling Phase 3 task is opened by this plan. Phase 3 is formally closed.
- **Any new Phase 2 task beyond P2-05.** The `plan/phase2_entry_plan.md` §4 P2-01..P2-05 sequence is exhausted and Phase 2 is formally closed.
- **Runtime work of any kind.** No `__main__` entry point, no daemon, no scheduler, no background worker, no long-running service, no live execution loop.
- **Broker integration.** No broker SDK, no broker connector, no broker reconciliation runtime, no broker authentication, no broker credentials.
- **Market-data integration.** No market-data ingestion code, no market-data pipeline, no committed dataset, no live or historical data feed.
- **Order management.** No order objects, no order placement, no position management, no fills, no trade reports.
- **Strategy logic.** No trading signals, no scanners, no models, no portfolio rules, no backtests.
- **Scheduling.** No cron-style scheduler, no APScheduler, no background-job framework, no operator-heartbeat daemon, no kill-switch runtime, no reconciliation runtime.
- **Persistence.** No SQLite, no on-disk database, no on-disk reconciliation snapshot, no on-disk heartbeat state, no log sink, no file artifact written by runtime code.
- **Deployment.** No deployment workflow, no rollout, no rollback runtime, no CI/CD pipeline beyond the existing local pre-commit and pytest gates.
- **Secrets / env-var loading.** No real secrets, no real credentials, no `.env` files, no `os.environ` / `os.getenv` reads, no real account identifiers, no real broker / venue identifiers, no real endpoints embedded anywhere in the repository under this plan.
- **Network.** No `socket`, no `urllib`, no `requests`, no HTTP client, no outbound or inbound network code.
- **Concrete risk implementations inside the runtime package.** No concrete implementation of `KillSwitchProtocol` / `ReconciliationProtocol` / `HeartbeatProtocol` lands inside `src/gmc_rebuild/risk/` under this plan. The P2-05 boundary (types and abstract `typing.Protocol` definitions only) is preserved.
- **New trading behavior.** No change that introduces, simulates, or wires up trading behavior — in any module, under any name, anywhere in the tree.
- **Tooling relaxation.** No weakening of pre-commit, Ruff, mypy strict mode, `detect-secrets`, `.gitignore`, `.secrets.baseline`, the `MASTER_STATUS.md` §8 step 4 always-forbidden scan, the §8 step 4a per-PR Phase 2 / Phase 3 infrastructure allowlist scan, or the §8 step 4c recursive forbidden-token scan.
- **§8 step 4a allowlist expansion.** The `allowed_p2_infra` allowlist is **not** extended by this plan. Any future addition requires a separate written authorization that names a specific implementation task, a sibling artifact under `governance/authorizations/`, and an allowlist update made in the same PR that introduces the new directory.
- **Source / test changes.** No file under `src/**` or `tests/**` is modified or created by this plan or by the PR that lands it.
- **New tags or releases.** No git tag, no GitHub release, no version bump.
- **Mode A / Mode B substitution.** This plan is governance prose, not a control-surface decision; it does not substitute for adversarial review of any future Phase 4 entry decision or any future runtime / broker / market-data / order / strategy / scheduler / persistence / deployment PR. Any such future PR must independently satisfy `AI_WORKFLOW.md` §4 (Mode A) and ADR-008 / ADR-009 (Mode B) as applicable.

The always-forbidden categories in `MASTER_STATUS.md` §6 and `plan/phase3_entry_plan.md` §10 — strategy code, broker execution code, live or paper trading wired to a real broker, runtime daemons affecting accounts, real market data ingestion, order placement, and real secrets — remain forbidden in all modes. This plan does not relax them and does not record any relaxation.

---

## 11. Supporting References (Non-Authoritative)

- Phase 1 accepted baseline: `1f101fc` (`MASTER_STATUS.md` §3).
- Phase 2 entry plan: `plan/phase2_entry_plan.md`.
- Phase 2 closure authorization: `governance/authorizations/2026-05-12_phase-2-closure.md`.
- Phase 3 entry planning authorization (pattern reference for Phase 4 entry planning authorization): `governance/authorizations/2026-05-13_phase-3-entry-planning.md`.
- Phase 3 entry plan (pattern reference for this Phase 4 entry plan): `plan/phase3_entry_plan.md`.
- Phase 3 closure authorization: `governance/authorizations/2026-05-14_phase-3-closure.md` — merged on `main` via PR #56 at `3131a69`, with sibling Mode B packet PR #57 merged first at `302dff6`.
- Phase 3 closure post-merge status reconciliation: PR #58 merged on `main` at `0a91261`, with sibling Mode B packet PR #59 merged first at `c910c9a`.
- Phase 4 entry planning authorization (the governance/documentation-only authorization that opens this planning workstream): `governance/authorizations/2026-05-14_phase-4-entry-planning.md`.
- ADR-008 (governance-phase monitoring cadence): `docs/decisions/ADR-008_monitoring_cadence_and_ai_monitor_role.md` §D3 / §D5.
- ADR-009 (runtime-phase monitoring cadence): `docs/decisions/ADR-009_runtime_monitoring_cadence.md` — Accepted on 2026-05-13; D7 bootstrap-avoidance clause keeps ADR-008 §D3 / §D5 in force until runtime exists on `main`.
- Workflow separation of duties: `AI_WORKFLOW.md` §1 (roles), §2 (standard workflow), §3 (required proof), §4 (when to use the Backup AI), §6 (anti-chaos rules), §7 (durable authorization artifacts).
