# Phase 3 Entry Plan

**Status:** Planning only — Phase 3 is **not** open. No Phase 3 task is authorized by this document.
**Created:** 2026-05-13 UTC
**Owner:** Perplexity Computer (supervisor), planning workstream authorized by Kevin.
**Scope:** This document plans the entry to Phase 3. It does not implement Phase 3, does not authorize any Phase 3 task (`P3-01`, `P3-02`, …), does not extend the `MASTER_STATUS.md` §8 step 4a `allowed_p2_infra` allowlist, does not modify any quality gate, does not modify any file under `src/**` or `tests/**`, and does not change any always-forbidden category in `MASTER_STATUS.md` §6.

If anything here conflicts with `MASTER_STATUS.md` or `AI_WORKFLOW.md`, those files win. This document is supporting planning material for a future Phase 3 entry decision; it does not redefine the phase boundary, and it does not make the phase gate decision itself.

This plan is the Phase 3 analogue to `plan/phase2_entry_plan.md`. It mirrors that file's structure deliberately so the pattern is the same and is reviewable on the same axes. Where this plan names a future Phase 3 task (`P3-01`, `P3-02`, …), the task is **future / not-authorized** and requires its own separate written authorization from Kevin, a sibling artifact under `governance/authorizations/`, applicable runtime-cadence ADR follow-up (ADR-008 §D6), and applicable Mode A / Mode B review per `AI_WORKFLOW.md` §4 and ADR-008 before it may be opened.

---

## 1. Current Status

- **Phase 1 accepted baseline:** `1f101fc` (`docs: fix Phase 1 verification blockers`), accepted per Kevin's written acceptance note on PR #3 (see `MASTER_STATUS.md` §3). Phase 1 baseline is unchanged by this plan.
- **Phase 2 implementation:** **Fully merged through P2-05; Phase 2 formally closed (governance-only).** The `plan/phase2_entry_plan.md` §4 P2-01..P2-05 sequence is merged on `main` (P2-01 at `e0278c4`, P2-02 at `6875b2d`, P2-03 at `b4e6d75`, P2-04 at `5dac8a0`, P2-05 at `a30e34b`); the `main` checkpoint containing all five merges is `5c390ff`. Phase 2 is formally closed at the current `main` checkpoint after PR #23 per Kevin's written authorization recorded at `governance/authorizations/2026-05-12_phase-2-closure.md`. The closure is governance-only and does **not** open Phase 3, does **not** open any new Phase 2 task beyond P2-05, does **not** extend the §8 step 4a allowlist, does **not** relax any quality gate, and does **not** create any tag or release.
- **Phase 3 entry planning:** Authorized by Kevin on 2026-05-13 as a **governance/documentation-only** workstream per `governance/authorizations/2026-05-13_phase-3-entry-planning.md`. That authorization is **planning-only**: it opens the planning workstream that would draft this document; it does **not** open Phase 3, does **not** authorize any Phase 3 implementation, does **not** name a specific Phase 3 task, does **not** extend the `MASTER_STATUS.md` §8 step 4a allowlist, and does **not** modify any quality gate.
- **P3-01 status:** **Merged on `main` as of 2026-05-13.** ADR-009 (`docs/decisions/ADR-009_runtime_monitoring_cadence.md`) was drafted in Proposed status under `governance/authorizations/2026-05-13_p3-01.md` (PR #30), revised in Proposed status by PR #32, and accepted (`Status: Proposed` → `Status: Accepted`) under `governance/authorizations/2026-05-13_p3-01-acceptance.md` (PR #34). The ADR-008 §D6 runtime-monitoring-cadence follow-up is therefore **closed** on `main`. ADR-009 D3 / D5 will replace ADR-008 §D3 / §D5 on a going-forward basis once runtime exists on `main` per ADR-009 D7's bootstrap-avoidance clause; until then, ADR-008 §D3 / §D5 continue to govern the governance phase.
- **P3-02 status:** **Entry authorized by Kevin on 2026-05-13 per `governance/authorizations/2026-05-13_p3-02.md`. The P3-02 entry PR formally opens Phase 3 as a governance state on merge.** P3-02 preparation prose merged earlier on 2026-05-13 under `governance/authorizations/2026-05-13_p3-02-preparation.md` (PR #36). The P3-02 entry is governance/documentation only and does **not** authorize any Phase 3 implementation, does **not** authorize P3-03, does **not** extend the `MASTER_STATUS.md` §8 step 4a allowlist, does **not** modify any quality gate, and does **not** add or modify any file under `src/**` or `tests/**`. The P3-02 entry PR is a phase gate by definition and requires Mode A adversarial review per `AI_WORKFLOW.md` §4(1) and a separate sibling Mode B monitoring packet merged to `main` before the entry PR merges per ADR-008 §D3 / §D5.
- **P3-03 implementation status:** **Merged on `main` as of 2026-05-13** under Kevin's separate written authorization per `governance/authorizations/2026-05-13_p3-03.md` as the first concrete Phase 3 implementation slice, narrowly scoped to a pure-Python in-memory test fixture for `HeartbeatProtocol` (ADR-005) only. Per ADR-008 §D3 / §D5, the Mode B monitoring packet for the active workday was opened as a separate sibling monitoring PR — **PR #43** — and merged first at `07aee55`; the implementation PR — **PR #42** — then merged at `c5e868c`, adding `src/gmc_rebuild/heartbeat/` (in-memory `InMemoryHeartbeat` fake — no runtime activation, no `__main__`, no daemon, no scheduler, no broker SDK, no network, no `time.sleep`, no `os.environ` / `os.getenv`, no filesystem) and `tests/heartbeat/test_heartbeat_fixture.py` (focused, deterministic tests exercising protocol-shape conformance and ADR-005 safe-default and staleness semantics), and extending the `MASTER_STATUS.md` §8 step 4a allowlist by exactly one entry — `src/gmc_rebuild/heartbeat` — with no other allowlist change. Mode A adversarial review per `AI_WORKFLOW.md` §4(2) (high-risk architecture decision — first concrete behaviour behind a P2-05 control surface) was delivered as PR-review text and not committed to the repository; the earlier Mode A review of the P3-03 planning artifact (PR #40) did not satisfy the Mode A requirement for the implementation PR and was treated as a separate review against a separate artifact. A follow-on lint remediation PR — **PR #44** — then merged at `db6d6fb` to fix lint violations in the Heartbeat fixture tests; PR #44 modified only `tests/heartbeat/` (no `src/**` change), did **not** extend the §8 step 4a allowlist, did **not** relax any quality gate, and was preceded by its own Mode B monitoring packet — **PR #45** — which merged at `70ebc8f` before PR #44. The authorization scope is unchanged by the merges: it does **not** authorize a second protocol fixture (for `KillSwitchProtocol` or `ReconciliationProtocol`), does **not** authorize any runtime activation, does **not** authorize any broker / market-data / order / strategy / scheduler / persistence / deployment / env-var / secrets change, and did **not** create any tag or release.
- **P3-04 implementation status:** **Merged on `main` as of 2026-05-14** under Kevin's separate written authorization per `governance/authorizations/2026-05-14_p3-04.md` as the second concrete Phase 3 implementation slice, narrowly scoped to a pure-Python in-memory test fixture for `KillSwitchProtocol` (ADR-002) only. Per ADR-008 §D3 / §D5, the Mode B monitoring packet for the active workday was opened as a separate sibling monitoring PR — **PR #49** — and merged first at `2db57db`; the P3-04 implementation PR — **PR #48** — then merged at `1a7949c`, adding `src/gmc_rebuild/kill_switch/` (in-memory `InMemoryKillSwitch` fake — no runtime activation, no `__main__`, no daemon, no scheduler, no broker SDK, no network, no `time.sleep`, no `os.environ` / `os.getenv`, no filesystem, no orders / market data / strategy, no real secrets / accounts / venues / endpoints) and `tests/kill_switch/test_kill_switch_fixture.py` (focused, deterministic tests exercising protocol-shape conformance and ADR-002 safe-default semantics), and extending the `MASTER_STATUS.md` §8 step 4a allowlist by exactly one entry — `src/gmc_rebuild/kill_switch` — bringing the allowlist to seven entries. Mode A adversarial review per `AI_WORKFLOW.md` §4(2) (high-risk architecture decision — second concrete behaviour behind a P2-05 control surface) was delivered as PR-review text and not committed to the repository; the Mode A review of the P3-03 implementation PR (PR #42) does **not** satisfy this Mode A requirement and was treated as a separate review against a separate artifact. The authorization scope is unchanged by the merges: it does **not** authorize a third protocol fixture (for `ReconciliationProtocol`), does **not** authorize any runtime activation, does **not** authorize any broker / market-data / order / strategy / scheduler / persistence / deployment / env-var / secrets change, and did **not** create any tag or release. The existing P3-03 HeartbeatProtocol fixture is preserved unchanged.
- **P3-05 implementation status:** **Merged on `main` as of 2026-05-14** under Kevin's separate written authorization per `governance/authorizations/2026-05-14_p3-05.md` as the third concrete Phase 3 implementation slice, narrowly scoped to a pure-Python in-memory test fixture for `ReconciliationProtocol` (ADR-003) only. Per ADR-008 §D3 / §D5, the Mode B monitoring packet for the active workday was opened as a separate sibling monitoring PR — **PR #53** — and merged first at `b886e19`; the P3-05 implementation PR — **PR #52** — then merged at `5abf8c8` (the current `main` head), adding `src/gmc_rebuild/reconciliation/` (in-memory `InMemoryReconciliation` fake — default returns `ReconciliationStatus.UNAVAILABLE` (not `FAILED`); preserves the `UNAVAILABLE` / `FAILED` distinction; no runtime activation, no `__main__`, no daemon, no scheduler, no broker SDK, no network, no `time.sleep`, no `os.environ` / `os.getenv`, no filesystem, no orders / positions / fills / executions / order book / market data / strategy / persistence, no real secrets / accounts / venues / endpoints) and `tests/reconciliation/test_reconciliation_fixture.py` (focused, deterministic test module exercising protocol-shape conformance and ADR-003 safe-default semantics), and extending the `MASTER_STATUS.md` §8 step 4a allowlist by exactly one entry — `src/gmc_rebuild/reconciliation` — bringing the allowlist to exactly eight entries. Mode A adversarial review per `AI_WORKFLOW.md` §4(2) was delivered as PR-review text and not committed to the repository; Mode A initially requested changes (B1 — ruff SIM102 + ruff-format; N1 — bullet order), addressed by fixup commit `4e7d19b` and cleared on re-review before merge. The Mode A reviews of the P3-03 (PR #42) and P3-04 (PR #48) implementation PRs did **not** satisfy this Mode A requirement and were treated as separate reviews against separate artifacts. The authorization scope is unchanged by the merges: it does **not** authorize a fourth protocol fixture, does **not** authorize any runtime activation, does **not** authorize any broker / market-data / order / strategy / scheduler / persistence / deployment / env-var / secrets change, and did **not** create any tag or release. The existing P3-03 HeartbeatProtocol fixture and P3-04 KillSwitchProtocol fixture are preserved unchanged.
- **P3-03 planning status:** **Authorized by Kevin on 2026-05-13 as a governance/documentation-only workstream per `governance/authorizations/2026-05-13_p3-03-planning.md`. P3-03 implementation is now authorized separately for HeartbeatProtocol only (see preceding bullet).** The P3-03 planning artifact identifies the proposed first single-protocol test-fixture scope (one of `KillSwitchProtocol` / `ReconciliationProtocol` / `HeartbeatProtocol`; the specific protocol is to be named by Kevin in writing at the time of P3-03 implementation authorization), the expected future files / directories (anticipated `src/gmc_rebuild/<protocol>/` plus matching `tests/<protocol>/`), the required `MASTER_STATUS.md` §8 step 4a allowlist update (planning-level reference only — **non-operative and pending Kevin's separate written authorization at the time of P3-03 implementation**), the expected quality gates for the future P3-03 implementation PR, and the expected review risks. The planning artifact is governance/documentation only and does **not** authorize P3-03 implementation, does **not** authorize any Phase 3 implementation, does **not** extend the `MASTER_STATUS.md` §8 step 4a allowlist, does **not** modify any quality gate, and does **not** add or modify any file under `src/**` or `tests/**`. The P3-03 planning PR receives Mode A adversarial review against the planning prose (delivered as PR-review text, not committed to the repository) and requires a separate sibling Mode B monitoring packet merged to `main` before the planning PR merges per ADR-008 §D3 / §D5. The Mode A review of the P3-03 planning artifact does **not** satisfy the Mode A requirement for the eventual P3-03 implementation PR; they are independent reviews against independent artifacts.
- **Phase 3 closure status:** **Merged on `main` as of 2026-05-14** per Kevin's written authorization at `governance/authorizations/2026-05-14_phase-3-closure.md`. Per ADR-008 §D3 / §D5, the Mode B monitoring packet for the active workday was opened as a separate sibling monitoring PR — **PR #57** — and merged first at `302dff6`; the Phase 3 closure PR — **PR #56** — then merged at `3131a69` (the current `main` head). Per `AI_WORKFLOW.md` §4(1), the closure PR also received Mode A adversarial review delivered as PR-review text and not committed to the repository. The closure is governance-only and records the three single-protocol in-memory test fixtures (P3-03 HeartbeatProtocol, P3-04 KillSwitchProtocol, P3-05 ReconciliationProtocol) as the complete and final set of merged Phase 3 implementations at the `main` checkpoint after the P3-01 / P3-02 / P3-03 / P3-04 / P3-05 sequence. The closure does **not** open Phase 4, does **not** authorize any runtime activation of any merged Phase 3 fixture, does **not** authorize a fourth protocol fixture or any further Phase 3 implementation, does **not** extend the `MASTER_STATUS.md` §8 step 4a allowlist (the eight P2-01..P2-05 + P3-03 + P3-04 + P3-05 entries are preserved exactly), does **not** relax any quality gate, did **not** add or modify any file under `src/**` or `tests/**`, and did **not** create any tag or release. **Phase 4 is not open or authorized.**
- **Phase 3 implementation:** **Limited to the three merged in-memory test fixtures (P3-03 HeartbeatProtocol, P3-04 KillSwitchProtocol, and P3-05 ReconciliationProtocol).** P3-03 (the test-fixture implementation of `HeartbeatProtocol` named in §4 item 3 below) has merged via PR #42 with PR #43 as its Mode B sibling, followed by lint remediation PR #44 with PR #45 as its Mode B sibling; the `src/gmc_rebuild/heartbeat/` directory exists on `main` and is on the §8 step 4a allowlist. P3-04 (the test-fixture implementation of `KillSwitchProtocol`) has merged via PR #48 with PR #49 as its Mode B sibling; the `src/gmc_rebuild/kill_switch/` directory exists on `main` and is on the §8 step 4a allowlist. P3-05 (the test-fixture implementation of `ReconciliationProtocol`) has merged via PR #52 with PR #53 as its Mode B sibling (PR #53 merged first at `b886e19`, PR #52 merged second at `5abf8c8`); the `src/gmc_rebuild/reconciliation/` directory exists on `main` and is on the §8 step 4a allowlist. No Phase 3 implementation beyond P3-03 / P3-04 / P3-05 is authorized: any runtime activation of any fixture and any other Phase 3 implementation slice each remain **future / not authorized**. Opening any further Phase 3 implementation task, or opening any runtime / broker / market-data / order / strategy / scheduler / persistence / deployment work requires Kevin's separate written authorization per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 / rule 7, a sibling artifact under `governance/authorizations/`, an §8 step 4a allowlist update in the same PR that introduces any new directory, and Mode A / Mode B review per `AI_WORKFLOW.md` §4 and ADR-008 where required.
- **Workflow in effect:** Codex builds → Perplexity Computer verifies → Kevin approves → Backup AI reviews adversarially at gates and high-risk decisions (per `AI_WORKFLOW.md` §1, §2, §4) and authors monitoring packet text under Mode B per ADR-008.

Until Kevin records a separate written authorization that opens Phase 3 (or a specific Phase 3 task) and the entry criteria in Section 5 below are met, the only allowed work is the planning workstream defined in `governance/authorizations/2026-05-13_phase-3-entry-planning.md` and the routine maintenance categories listed in `MASTER_STATUS.md` §9.

---

## 2. Phase 3 Objective (Planning Level Only)

This section restates the Phase 3 objective at the **planning level** only. Naming an objective here does not authorize implementation. Phase 3 implementation requires a separate written authorization from Kevin.

Phase 3 is conceived, **for planning purposes only**, as the **first runtime-adjacent infrastructure phase** that would sit on top of the merged P2-01..P2-05 foundation. Its planning-level purpose is to define how the abstract risk-control boundaries materialised in P2-05 (`KillSwitchProtocol`, `ReconciliationProtocol`, `HeartbeatProtocol` and their supporting frozen dataclasses and enums) could be **observed, exercised, and audited in a sandboxed local context** — still without any broker integration, without any live or paper trading wired to a real broker, without any market data ingestion, without any order placement, and without any scheduler / daemon / background worker affecting accounts or markets.

In planning scope only (Section 3 below defines what may be discussed; Section 4 names candidate task sequences; none of this is implementation authorization):

- Local-only, sandboxed scaffolding that would allow a future test-fixture implementation of one risk-control protocol at a time to be exercised under unit-test conditions, with no network, no broker SDK, no real account identifiers, no real venue identifiers, no real endpoints, and no real secrets.
- Per-control proof-bundle expectations that align with `plan/phase2_entry_plan.md` §6 and `AI_WORKFLOW.md` §3, adjusted for the additional runtime-cadence ADR follow-up that ADR-008 §D6 defers.
- ADR follow-ups that any Phase 3 entry decision would require — at minimum ADR-008 §D6 (runtime monitoring cadence and missed-packet severity), with implications for ADR-001 (secrets management), ADR-002 (kill switch), ADR-003 (reconciliation), ADR-005 (heartbeat), ADR-006 (deployment logs), and ADR-007 (minimal CI).

Out of planning scope, and forbidden until a Phase 3 task is opened in writing by Kevin (and forbidden at the always-forbidden category level per `MASTER_STATUS.md` §6 independent of phase):

- Trading strategy code (signals, scanners, models, portfolio rules, backtests against real history).
- Broker execution code (order placement, position management, broker SDK integration, broker authentication).
- Live or paper trading workflows wired to a real broker.
- Runtime daemons, schedulers, long-running services, background workers, operator-availability heartbeats wired to a real operator, or anything with a `__main__` entry point that touches accounts, markets, or money.
- Market data ingestion code, real data pipelines, committed datasets, real or historical feeds.
- Real secrets, real credentials, real account identifiers, real broker / venue identifiers, real endpoints.
- Any concrete implementation of `KillSwitchProtocol`, `ReconciliationProtocol`, or `HeartbeatProtocol` that talks to a broker, network, filesystem outside the test sandbox, or scheduler.
- Any change that loosens `.gitignore`, `.pre-commit-config.yaml`, mypy strict mode, `detect-secrets`, the `MASTER_STATUS.md` §8 step 4 always-forbidden scan, the §8 step 4a per-PR Phase 2 infrastructure allowlist scan, or the §8 step 4c recursive forbidden-token scan.
- Any new git tag, GitHub release, or version bump.

This split is intentional and mirrors the line `MASTER_STATUS.md` §6 / §7 already draws and that `plan/phase2_entry_plan.md` §2 restated for Phase 2. Phase 3 planning does not move that line; it discusses what would sit underneath it.

---

## 3. Allowed Planning Topics

While Phase 3 entry planning is in this opened-but-unscoped state (per `governance/authorizations/2026-05-13_phase-3-entry-planning.md`), Codex and Perplexity Computer may discuss and write planning artifacts on the following topics. Planning artifacts are documents, not code, and must be reviewable as documents. This list mirrors `plan/phase2_entry_plan.md` §3 and the "Allowed Planning Topics" list in `governance/authorizations/2026-05-13_phase-3-entry-planning.md` deliberately, so the pattern is the same:

1. **Phase 3 objective in prose.** What infrastructure step Phase 3 would build on top of the merged P2-01..P2-05 foundation, restated at a level that does not authorize any specific implementation. Section 2 of this plan is the canonical planning-level statement.
2. **Candidate future Phase 3 task sequence** (`P3-01`, `P3-02`, …). Named only as **future / not-authorized** PRs that would each require their own separate written authorization slice and sibling artifact under `governance/authorizations/`. Naming a task in Section 4 of this plan does **not** authorize it.
3. **Phase 3 entry criteria.** What must be true (baseline, governance, ADRs, monitoring cadence under ADR-008 §D6, Mode A / Mode B review per `AI_WORKFLOW.md` §4) before any Phase 3 implementation PR could open. Section 5 of this plan is the canonical planning-level statement.
4. **Per-PR proof-bundle expectations for any future Phase 3 PR.** Restated from `AI_WORKFLOW.md` §3 and `plan/phase2_entry_plan.md` §6, with the additional ADR-008 §D6 runtime-cadence follow-up that Phase 3 work would have to address. Section 6 of this plan is the canonical planning-level statement.
5. **Rollback and stop conditions.** Restated for Phase 3 from `plan/phase2_entry_plan.md` §8. Section 8 of this plan is the canonical planning-level statement.
6. **Phase-boundary enforcement.** How Phase 3 PRs would prove they did not cross into trading strategy, broker execution, live or paper trading wired to a real broker, real market data ingestion, real secrets, or any other always-forbidden category in `MASTER_STATUS.md` §6. Section 6 and Section 8 of this plan record the planning-level expectations.
7. **ADR follow-ups.** At minimum the runtime-phase monitoring cadence follow-up deferred by ADR-008 §D6, plus any kill-switch (ADR-002), reconciliation (ADR-003), heartbeat (ADR-005), secrets-management (ADR-001), deployment-log (ADR-006), and minimal-CI (ADR-007) implications that a runtime-adjacent phase would have to address before opening. Section 9 of this plan enumerates the planning-level follow-up list.

Any planning topic that does not fit the list above must be raised with Kevin before a document is written, per `governance/authorizations/2026-05-13_phase-3-entry-planning.md` "Allowed Planning Topics" and `AI_WORKFLOW.md` §6 rule 7 ("No phase drift").

---

## 4. Candidate Future Phase 3 Task Sequence (Future / Not Authorized)

The following sequence is a **planning-level proposal**. It names candidate future PRs only. **Every item below is future / not-authorized.** None of these tasks may begin, no Phase 3 directory may be created, no `src/**` or `tests/**` file may be added under any of these names, and no §8 step 4a allowlist entry may be added until each of the gates listed in Section 7 below is independently satisfied for the specific task being opened.

Each candidate is intentionally small enough that, **if and only if** Kevin later authorizes it, it could be verified independently as a governance-only authorization slice followed by a narrowly scoped implementation PR — the same two-step shape used for P2-03, P2-04, and P2-05.

1. **PR P3-01 — (future / not authorized) ADR for runtime monitoring cadence and missed-packet severity (ADR-008 §D6 follow-up).** Drafts the follow-up ADR that ADR-008 §D6 defers: defines runtime-phase cadence (trading day vs. calendar weekday, timezone discipline) and runtime-phase missed-packet severity (whether a missed packet is an automatic rollback control or remains an audit-issue catch-up). This ADR is required by ADR-008 §D6 **before** any Phase 3 PR that introduces runtime can open. The ADR PR itself adds no runtime, no broker integration, no order placement, no market-data ingestion, and no concrete risk implementation. **Not authorized.** Requires a separate written authorization from Kevin, a sibling artifact under `governance/authorizations/`, and (because it is a phase-gate-adjacent governance decision touching a control surface that future runtime depends on) Mode A adversarial review per `AI_WORKFLOW.md` §4(2). A Mode B monitoring packet for the active workday is also required per ADR-008 §D3 / §D5.
2. **PR P3-02 — (future / not authorized) Phase 3 entry decision (phase-gate PR).** The actual decision to **open Phase 3**. Records Kevin's written authorization to enter Phase 3, names the first Phase 3 task scope, and (where it introduces a directory) extends the `MASTER_STATUS.md` §8 step 4a allowlist in the same PR per the standing rule in §8 step 4b. **Not authorized.** This is a **phase gate** by definition and requires Mode A adversarial review per `AI_WORKFLOW.md` §4(1) and a Mode B monitoring packet per ADR-008 §D3 / §D5. The Phase 3 entry decision cannot land until the ADR-008 §D6 follow-up ADR (P3-01 above) has merged.
3. **PR P3-03 — (future / not authorized) Test-fixture implementation of one risk-control protocol.** A first, narrowly scoped test-fixture implementation of exactly one of the P2-05 protocols (the specific protocol is to be named by Kevin in writing at the time of authorization). Restricted to a single protocol; restricted to test-fixture code that runs under `pytest`; no broker SDK, no network, no real account identifiers, no real venue identifiers, no real endpoints, no real secrets, no scheduler, no daemon, no `__main__` entry point, no order objects, no market-data ingestion. **Not authorized.** Requires a separate written authorization from Kevin, a sibling artifact under `governance/authorizations/`, the §8 step 4a allowlist update in the same PR that introduces the directory, and (because it materialises a concrete behaviour behind a control surface defined by ADR-002 / ADR-003 / ADR-005) Mode A adversarial review per `AI_WORKFLOW.md` §4(2) and a Mode B monitoring packet per ADR-008 §D3 / §D5.

Further candidate tasks (P3-04, P3-05, …) are deliberately **not enumerated** in this plan. Enumerating them now would invite scope drift before the ADR-008 §D6 follow-up ADR exists and before the Phase 3 entry decision has been made. Any future enumeration must itself be authorized as a documentation-only update to this plan, per `governance/authorizations/2026-05-13_phase-3-entry-planning.md` "Allowed Planning Topics" item 2.

Sequencing rules (planning-level, mirroring `plan/phase2_entry_plan.md` §4):

- Tasks land one at a time. PR P3-(N+1) is not opened until PR P3-N is accepted by Kevin.
- Each PR is small enough that the diff and the proof bundle (Section 6) fit a single review.
- Any PR that grows beyond its stated scope during implementation is split or stopped per `AI_WORKFLOW.md` §6 rule 6 / rule 7.
- The ADR-008 §D6 follow-up ADR (P3-01 above) must land **before** the Phase 3 entry decision (P3-02 above), and the Phase 3 entry decision must land **before** any test-fixture implementation (P3-03 above).

**§8 step 4a allowlist note.** The `allowed_p2_infra` allowlist contains eight entries on the post-merge `main` (`src`, `src/gmc_rebuild/config`, `src/gmc_rebuild/time`, `src/gmc_rebuild/logging`, `src/gmc_rebuild/risk`, `src/gmc_rebuild/heartbeat`, `src/gmc_rebuild/kill_switch`, `src/gmc_rebuild/reconciliation`); the sixth entry was added by PR #42 (P3-03 implementation), the seventh entry was added by PR #48 (P3-04 implementation), and the eighth entry was added by PR #52 (P3-05 implementation). This plan does **not** extend that allowlist further. Any future Phase 3 PR that introduces a new directory must add it to the allowlist in the same PR that introduces the directory, per the standing rule in `MASTER_STATUS.md` §8 step 4b, and must be authorized in writing for the specific directory by Kevin.

---

## 5. Phase 3 Entry Criteria (Planning Level Only)

Phase 3 implementation may begin only when **all** of the following are true and recorded. Listing the criteria here does not by itself open Phase 3; opening Phase 3 requires Kevin's written authorization recorded in a sibling artifact under `governance/authorizations/` per `AI_WORKFLOW.md` §7.

1. The accepted Phase 1 baseline is `1f101fc` (per `MASTER_STATUS.md` §3) and `main` is a descendant of it (`MASTER_STATUS.md` §8 step 3 returns OK).
2. Phase 2 is formally closed (governance-only) per `governance/authorizations/2026-05-12_phase-2-closure.md`. **Satisfied as of 2026-05-12.**
3. Phase 3 entry **planning** has been authorized by Kevin in writing per `governance/authorizations/2026-05-13_phase-3-entry-planning.md`. **Satisfied as of 2026-05-13.** Note that this planning authorization does **not** by itself satisfy criterion 6 below — opening Phase 3 requires a separate authorization.
4. This Phase 3 Entry Plan (`plan/phase3_entry_plan.md`) has been merged on `main` as planning-only documentation. (This document targets that merge; merging this document does not by itself open Phase 3.)
5. The ADR-008 §D6 follow-up ADR (runtime monitoring cadence and missed-packet severity for the runtime phase) has been authorized in writing by Kevin, opened as P3-01 per Section 4, reviewed in Mode A per `AI_WORKFLOW.md` §4(2), and merged on `main`. ADR-008 §D6 makes this a hard precondition for any runtime PR.
6. Kevin has explicitly authorized Phase 3 entry in writing — commit message, PR comment, or governance entry, not a chat message — per `MASTER_STATUS.md` §7.3 and recorded in a sibling artifact under `governance/authorizations/` per `AI_WORKFLOW.md` §7. Authorization of "Phase 3 in general" does not by itself authorize any specific P3-0N implementation PR; each first PR's scope must also be named in the authorization, per the §7.4 pattern that `plan/phase2_entry_plan.md` §5 applied to P2-0N.
7. The Phase 3 entry decision has been reviewed in **Mode A** by the Backup AI per `AI_WORKFLOW.md` §4(1) (phase gate). The Mode A critique is delivered as PR-review text and is **not** committed to the repository (per `AI_WORKFLOW.md` §6 rule 5).
8. A **Mode B** monitoring packet has been authored by the Backup AI per ADR-008 §D3 and committed by Codex under `monitoring/daily/` per ADR-008 §D4 for the active workday on which the Phase 3 entry PR is open / merged. Per ADR-008 §D5, no phase-opening or phase-expanding PR may merge while any required packet from any prior active workday is missing without a catch-up note covering it; Perplexity Computer confirms this before verifying the Phase 3 entry PR.
9. The first Phase 3 PR is one of the candidate tasks named in Section 4 above (P3-01 ADR follow-up, then P3-02 phase-gate decision, then P3-03 single-protocol test-fixture), unless Kevin pre-approves a different narrow plan in writing. The first Phase 3 implementation PR is infrastructure-only at the planning-level definition of Section 2 above (sandboxed, local-only, no broker, no live or paper trading wired to a real broker, no market data, no order placement, no scheduler / daemon, no real secrets).

If any criterion fails, Phase 3 stays closed. Phase 2 stays formally closed. Routine governance maintenance under `MASTER_STATUS.md` §9 continues.

---

## 6. Required Proof For Each Future Phase 3 PR

Each future Phase 3 PR must include the proof bundle defined in `AI_WORKFLOW.md` §3 and restated in `plan/phase2_entry_plan.md` §6. Restated here for Phase 3 scope, with the additional ADR-008 §D6 follow-up that Phase 3 requires.

1. **Git state.**
   - `git status` showing a clean tree after commit.
   - `git log --oneline -10` showing the head commit and recent history.
   - `git rev-parse HEAD` showing the exact commit hash under review.
   - `git diff <baseline>..HEAD` against the accepted Phase 1 baseline `1f101fc` (or a later accepted baseline if one has been recorded in `MASTER_STATUS.md` §3 by that time).
2. **Tests and pre-commit.**
   - Full output of `pre-commit run --all-files` (must pass, or every failure documented).
   - Full output of `pytest` (must pass).
3. **Phase-boundary checklist.** For each Phase 3 PR, the verification report explicitly confirms:
   - No new top-level directories outside the documented set.
   - No new modules under `strategy/`, `signals/`, `broker/`, `execution/`, `live/`, `daemons/`, `data/`, `market_data/`, `orders/`, `secrets/`, or any name on the `MASTER_STATUS.md` §8 step 4 always-forbidden list, anywhere in the tree (the §8 step 4c recursive forbidden-token scan returns OK / subshell exit `0`).
   - No new long-running entry points (`if __name__ == "__main__"` services, scheduler configs, background workers, daemons).
   - No new secrets, real credentials, real account identifiers, real broker / venue identifiers, real endpoints, or generated data files.
   - No new broker SDK dependency, no new market-data SDK dependency, no new scheduler or background-job dependency.
   - No new concrete implementation of `KillSwitchProtocol` / `ReconciliationProtocol` / `HeartbeatProtocol` that talks to a broker, network, filesystem outside the test sandbox, or scheduler.
   - No relaxation of `.gitignore`, `.pre-commit-config.yaml`, mypy strict mode, `detect-secrets`, `.secrets.baseline`, the `MASTER_STATUS.md` §8 step 4 always-forbidden scan, the §8 step 4a per-PR Phase 2 infrastructure allowlist scan, or the §8 step 4c recursive forbidden-token scan.
   - Any new authorized directory is added to the `MASTER_STATUS.md` §8 step 4a allowlist in the same PR that introduces the directory, per the standing rule in §8 step 4b.
4. **File-specific evidence.** Per `AI_WORKFLOW.md` §3.4, each changed file is named and the verifier states what was verified for it (required headings present, decision recorded, status set, links valid for ADRs; structure preserved, instructions still clear, no placeholder leakage for templates; settings match what the README, ADRs, and `MASTER_STATUS.md` claim for config changes; cross-references still resolve, phase claims still accurate for documentation changes).
5. **Docs updated.** Any change to interfaces or conventions is reflected in the relevant document (ADR update, new ADR, or `MASTER_STATUS.md` entry) in the same PR — no orphaned code without a governance hook.
6. **ADR-008 §D6 follow-up status.** The verification report names the ADR-008 §D6 follow-up ADR status: if the PR introduces runtime under Section 2's planning-level definition, the follow-up ADR (P3-01 per Section 4) must already have merged on `main` and the PR must reference it. If the PR is the follow-up ADR itself (P3-01), the verification report records that it is the follow-up ADR and that it does not by itself introduce runtime.
7. **Mode A / Mode B status.** The verification report names whether `AI_WORKFLOW.md` §4 Mode A and ADR-008 §D3 Mode B apply to the PR, and where each artifact lives (PR-review text for Mode A; `monitoring/daily/YYYY-MM-DD.md` for Mode B). For phase-gate PRs and high-risk-architecture PRs, **both** artifacts are required per ADR-008 §D7.

A Phase 3 PR that does not carry this bundle is not eligible for Kevin's review.

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

- The Phase 3 entry decision itself (the phase gate that opens Phase 3 — `AI_WORKFLOW.md` §4(1) by definition).
- The ADR-008 §D6 follow-up ADR (runtime monitoring cadence and missed-packet severity), because it defines a runtime-phase control surface — `AI_WORKFLOW.md` §4(2) (high-risk architecture decision).
- Any subsequent Phase 3 PR that defines a new control surface, a new trust boundary, or a non-reversible decision — `AI_WORKFLOW.md` §4(2). Examples include the first test-fixture implementation of any risk-control protocol (P3-03 in Section 4), any ADR update that changes the kill-switch / reconciliation / heartbeat policy, and any change that touches the secrets-management discipline.
- Any Phase 3 PR that would, if wrong, cause real-world loss — `AI_WORKFLOW.md` §4(3). Such a PR is by definition **out of Phase 3 scope** per Section 2 (no live trading authorization, no broker integration, no live or paper trading wired to a real broker, no operator-availability heartbeat wired to a real operator, no data retention or destruction policy that affects real accounts or markets). The correct response is to treat it as scope drift and stop per `AI_WORKFLOW.md` §6 rule 7 and Section 8 of this plan, **not** to invoke the Backup AI in Mode A as a substitute for stopping.

**Mode B continuous governance monitor** per ADR-008 §D3 is required on any active workday on which the default branch changes or a pull request is open, updated, or merged. The Backup AI authors packet text; Codex commits per `AI_WORKFLOW.md` §1.4 and §6 rule 1 and ADR-008 §D1. When both Mode A and Mode B fire on the same PR — and every Phase 3 phase-gate or high-risk-architecture PR will — **two distinct artifacts are required** per ADR-008 §D7: the Mode A written critique (PR-review text only, not committed to the repo) and the Mode B monitoring packet (committed by Codex under `monitoring/daily/`). The packet may link to or quote the critique for context, but does not replace it.

The Backup AI produces a written critique only (Mode A) or packet text only (Mode B). It does not edit other files, does not commit, does not push, does not merge, and does not approve. `AI_WORKFLOW.md` §6 rule 1 ("One builder at a time") is preserved: Codex remains the only role that writes to the repository.

---

## 8. Rollback and Stop Conditions

Phase 3 entry, and each future Phase 3 PR, must support a clean rollback.

Rollback rules:

- Every Phase 3 PR is reversible by a single `git revert` on the merge commit. PRs that bundle unrelated changes are split until this is true.
- The accepted Phase 1 baseline (`1f101fc` per `MASTER_STATUS.md` §3) is the last-known-good state. Reverting all Phase 2 and Phase 3 work returns the tree to a descendant of that baseline.
- A deployment log entry per `docs/deploys/deploy-log-template.md` is required if any Phase 3 change affects developer environments (e.g. new tooling requirement, new pre-commit hook), even though no runtime is being deployed under the planning-level definition of Section 2.
- Once the ADR-008 §D6 follow-up ADR (P3-01 per Section 4) has merged, the rollback rule for missed monitoring packets is governed by the runtime-phase severity defined in that follow-up ADR, not by ADR-008 §D5. Until the follow-up ADR exists, the current governance-phase severity in ADR-008 §D5 applies.

Stop conditions — if any of the following occurs, Phase 3 work pauses and the situation is escalated to Kevin before further changes:

1. A Phase 3 PR cannot satisfy the proof bundle in Section 6 without expanding scope.
2. A Phase 3 PR is found to cross into strategy, broker, live or paper trading wired to a real broker, market data ingestion, real secrets, order placement, scheduler / daemon, persistence outside the test sandbox, or runtime-daemon territory — at review time or after merge.
3. `pre-commit` or `pytest` fails and the proposed fix is to weaken the hook, loosen mypy strict mode, relax `detect-secrets`, or modify `.secrets.baseline` to silence a real finding.
4. `MASTER_STATUS.md` and a Phase 3 PR disagree about the current phase, the accepted baseline, the `allowed_p2_infra` allowlist, or the allowed next decisions.
5. Two changes attempt to land on the default branch simultaneously, violating `AI_WORKFLOW.md` §6 rule 4 (one builder, one branch per task).
6. The Backup AI (when invoked per Section 7) identifies a specific invariant violation that the verifier did not catch.
7. A Phase 3 PR is opened **before** the ADR-008 §D6 follow-up ADR (P3-01 per Section 4) has merged, while introducing runtime under Section 2's planning-level definition.
8. A required Mode B monitoring packet under ADR-008 §D3 is missing for a prior active workday and no catch-up note per ADR-008 §D5 has been committed. Per ADR-008 §D5, no phase-opening or phase-expanding PR may merge under that condition.

In any stop condition, the default is to pause and ask Kevin. Per `AI_WORKFLOW.md` §6 rule 10: "When in doubt, stop. A paused task is recoverable. A merged Phase 3 change made by accident is not."

---

## 9. ADR Follow-ups That Phase 3 Entry Requires

Listed here for planning visibility. None of these follow-ups is authorized by this plan. Each requires its own separate written authorization from Kevin, a sibling artifact under `governance/authorizations/`, and the applicable Mode A / Mode B review per `AI_WORKFLOW.md` §4 and ADR-008.

- **ADR-008 §D6 — runtime monitoring cadence and missed-packet severity follow-up ADR.** Required before any Phase 3 PR that introduces runtime. Candidate task: P3-01 in Section 4. Required by ADR-008 §D6 as a hard precondition.
- **ADR-001 — secrets management.** Phase 3 introduces no real secrets, no real credentials, no real account identifiers, no real broker / venue identifiers, and no real endpoints under the Section 2 planning-level definition. If any later Phase 3 task ever needs to reference a real secret (it must not, under Section 2), ADR-001's secrets-management discipline must be revisited in a separate PR before the reference lands. This plan does not authorize that revisit.
- **ADR-002 — runtime kill-switch architecture.** P2-05 materialised the abstract `KillSwitchProtocol` and supporting types only. Any test-fixture implementation under P3-03 (Section 4) must align with ADR-002 and must not add broker side effects, order placement, or network calls. If a test fixture surfaces a gap in ADR-002, the gap is recorded in an ADR update, not silently coded around.
- **ADR-003 — broker reconciliation discipline.** P2-05 materialised the abstract `ReconciliationProtocol` and supporting types only. Any test-fixture implementation under P3-03 (Section 4) must align with ADR-003 and must not add broker integration, account fetch, fills, or order objects.
- **ADR-005 — operator availability heartbeat.** P2-05 materialised the abstract `HeartbeatProtocol` and supporting types only. Any test-fixture implementation under P3-03 (Section 4) must align with ADR-005 and must not add a scheduler, an operator-availability daemon, or an external sink.
- **ADR-006 — deployment logs.** Any Phase 3 change that affects developer environments requires a deployment log entry per `docs/deploys/deploy-log-template.md`. No runtime deployment is authorized; the deployment-log discipline applies to developer-environment changes only.
- **ADR-007 — minimal CI strategy.** The local quality-gate stack (pre-commit, Ruff, mypy strict, detect-secrets, pytest) is unchanged by this plan. Any Phase 3 PR that proposes a CI change must do so as a separate ADR update reviewed under `AI_WORKFLOW.md` §4(2).

The list above is not exhaustive. Any later ADR follow-up that surfaces during the planning workstream must be raised with Kevin and recorded in a sibling artifact under `governance/authorizations/` before the follow-up PR opens.

---

## 10. Explicitly Not Authorized

For audit clarity, the following categories remain forbidden under this planning document. Each is forbidden by default per `MASTER_STATUS.md` §6 and `governance/authorizations/2026-05-13_phase-3-entry-planning.md` "Explicitly Not Authorized"; mirroring them here is **not** a re-authorization and is **not** a relaxation. Each requires Kevin's separate written authorization per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 / rule 7, a sibling artifact under `governance/authorizations/`, the applicable Mode A / Mode B review, and (where it introduces a new directory) a corresponding update to the §8 step 4a allowlist in the same PR.

- **Opening Phase 3.** This document plans Phase 3 entry; it does not open Phase 3. The Phase 3 entry decision is a future, separate written authorization (candidate task P3-02 in Section 4) and is itself a phase gate per `AI_WORKFLOW.md` §4(1).
- **Any specific Phase 3 task (P3-01, P3-02, P3-03, …).** Naming a candidate task in Section 4 above is planning-level discussion, not authorization. Each task requires its own separate written authorization.
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
- **Concrete risk implementations inside the runtime package.** No concrete implementation of `KillSwitchProtocol` / `ReconciliationProtocol` / `HeartbeatProtocol` lands inside `src/gmc_rebuild/risk/` under this plan. The P2-05 boundary (types and abstract `typing.Protocol` definitions only) is preserved.
- **New trading behavior.** No change that introduces, simulates, or wires up trading behavior — in any module, under any name, anywhere in the tree.
- **Tooling relaxation.** No weakening of pre-commit, Ruff, mypy strict mode, `detect-secrets`, `.gitignore`, `.secrets.baseline`, the `MASTER_STATUS.md` §8 step 4 always-forbidden scan, the §8 step 4a per-PR Phase 2 infrastructure allowlist scan, or the §8 step 4c recursive forbidden-token scan.
- **§8 step 4a allowlist expansion.** The `allowed_p2_infra` allowlist is **not** extended by this plan. Any future addition requires a separate written authorization that names a specific implementation task, a sibling artifact under `governance/authorizations/`, and an allowlist update made in the same PR that introduces the new directory.
- **Source / test changes.** No file under `src/**` or `tests/**` is modified or created by this plan or by the PR that lands it.
- **New tags or releases.** No git tag, no GitHub release, no version bump.
- **Mode A / Mode B substitution.** This plan is governance prose, not a control-surface decision; it does not substitute for adversarial review of any future Phase 3 entry decision or any future runtime / broker / market-data / order / strategy / scheduler / persistence / deployment PR. Any such future PR must independently satisfy `AI_WORKFLOW.md` §4 (Mode A) and ADR-008 (Mode B) as applicable.

The always-forbidden categories in `MASTER_STATUS.md` §6 and `plan/phase2_entry_plan.md` §2 — strategy code, broker execution code, live or paper trading wired to a real broker, runtime daemons affecting accounts, real market data ingestion, order placement, and real secrets — remain forbidden in all modes. This plan does not relax them and does not record any relaxation.

---

## 11. Supporting References (Non-Authoritative)

- Phase 1 accepted baseline: `1f101fc` (`MASTER_STATUS.md` §3).
- Phase 2 entry plan (pattern reference for this Phase 3 entry plan): `plan/phase2_entry_plan.md`.
- Phase 2 closure authorization: `governance/authorizations/2026-05-12_phase-2-closure.md`.
- Phase 3 closure authorization (merged on `main` as of 2026-05-14 via PR #56 at `3131a69`, with sibling Mode B packet PR #57 merged first at `302dff6`): `governance/authorizations/2026-05-14_phase-3-closure.md`.
- Phase 3 entry planning authorization (the governance/documentation-only authorization that opens this planning workstream): `governance/authorizations/2026-05-13_phase-3-entry-planning.md`.
- Monitoring cadence rule governing the Mode B packet for the PR that lands this plan: `docs/decisions/ADR-008_monitoring_cadence_and_ai_monitor_role.md` §D3 / §D5, with the deferred runtime-phase follow-up in §D6.
- Workflow separation of duties: `AI_WORKFLOW.md` §1 (roles), §2 (standard workflow), §3 (required proof), §4 (when to use the Backup AI), §6 (anti-chaos rules), §7 (durable authorization artifacts).
