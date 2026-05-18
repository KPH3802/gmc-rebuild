# Phase 5 Entry Plan

**Status:** Phase 5 is open at the bounded scope of the merged P5-01 inert local simulation boundary skeleton, the merged P5-02 simulated order intent model, the merged P5-03 simulated-order-intent invariants tripwires, and the merged P5-04 composed safety-foundation × simulation integration tripwires. **P5-05 (and any later P5-0N task) is future / not authorized.** Any P5-05 implementation, any simulation expansion (additional `SimulationLane` member, additional `SimulatedOrderSide` / `SimulatedOrderType` member, additional `SimulatedOrderIntent` field, additional `SimulationBoundary` method, additional placeholder / order record class), any order semantics change, any runtime activation of any merged Phase 3 fixture, P4-06 / P4-07 / P4-08 safety surface, or P5-01 / P5-02 simulation surface, and any ops execution work (OPS-05 X10 Layer 5 promotion, OPS-06 backup-monitoring automation, OPS-07 DR drill execution, etc.) requires its own separate written authorization from Kevin per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 / rule 7, a sibling artifact under `governance/authorizations/`, applicable Mode A / Mode B review, and (where it introduces a new directory) a corresponding update to the `MASTER_STATUS.md` §8 step 4a `allowed_p2_infra` allowlist in the same PR that introduces the directory.
**Created:** 2026-05-18 UTC
**Owner:** Perplexity Computer (supervisor), planning workstream authorized by Kevin on 2026-05-18 per `governance/authorizations/2026-05-18_phase-5-entry-planning.md`.
**Scope:** This document records the Phase 5 entry plan, enumerates the current post-P5-04 state at the planning level only, and names P5-05 (and any later P5-0N task) only as **future / not authorized**. It does not authorize any successor P5 task, any simulation expansion, any order semantics change, any runtime activation, any ops execution work, any extension of the §8 step 4a allowlist, any quality-gate modification, any new `src/**` change, any new `tests/**` change, any tag, any release, or any always-forbidden category change under `MASTER_STATUS.md` §6.

If anything here conflicts with `MASTER_STATUS.md` or `AI_WORKFLOW.md`, those files win. This document is supporting planning and status material; it does not redefine the phase boundary, and it does not make any new phase-gate decision itself.

This plan is the Phase 5 analogue to `plan/phase4_entry_plan.md`. It mirrors that file's structure deliberately so the pattern is the same and is reviewable on the same axes. Where this plan names a successor Phase 5 task beyond the already merged P5-01 / P5-02 / P5-03 / P5-04 sequence, the task is **future / not authorized** and requires its own separate written authorization from Kevin, a sibling artifact under `governance/authorizations/`, applicable Mode A / Mode B review per `AI_WORKFLOW.md` §4 and ADR-008 / ADR-009, and (where it introduces a new directory) a corresponding update to the §8 step 4a allowlist in the same PR.

---

## 1. Current Post-P5-04 State

Reconciled at the canonical status reconciliation merged via PR #114 (`a02f17c`) and its sibling Mode B PR #115 (`75d6f28`). The reconciled facts below are taken from `MASTER_STATUS.md`, `plan/phase4_entry_plan.md`, and the durable authorization artifacts under `governance/authorizations/`; this section restates them at planning level only and does not change any of them.

- **Phase 1 accepted baseline:** `1f101fc` (`docs: fix Phase 1 verification blockers`), accepted per Kevin's written acceptance note on PR #3 (see `MASTER_STATUS.md` §3). Phase 1 baseline is unchanged by this plan.
- **Phase 2:** Formally closed (governance-only) per `governance/authorizations/2026-05-12_phase-2-closure.md`. The `plan/phase2_entry_plan.md` §4 P2-01..P2-05 sequence is merged on `main`. The merged subpackages under `src/gmc_rebuild/` are `config`, `time`, `logging`, and `risk` (the last contains types and abstract `typing.Protocol` definitions only).
- **Phase 3:** Formally closed (governance-only) per `governance/authorizations/2026-05-14_phase-3-closure.md`. The three merged in-memory single-protocol test fixtures are `InMemoryHeartbeat` (P3-03, `src/gmc_rebuild/heartbeat/`), `InMemoryKillSwitch` (P3-04, `src/gmc_rebuild/kill_switch/`), and `InMemoryReconciliation` (P3-05, `src/gmc_rebuild/reconciliation/`). None is re-exported from `src/gmc_rebuild/__init__.py`; none is consumed from a `__main__`, a daemon, a scheduler, or any runtime path on `main`.
- **Phase 4 governance entry:** Opened as a governance state only via P4-01 per `governance/authorizations/2026-05-14_p4-01.md` (PR #64 at `9f8bd92`).
- **Phase 4 composed-test sequence:** P4-02 composed-fixture test merged via PR #73 at `abec3e8`; P4-03 composed-invariants test merged via PR #79 at `70b0edb`; P4-04 composed-edge-cases test merged via PR #87 at `2439855`; P4-05 composed-failure-modes test merged via PR #95 at `ec8bd96`. All four live under `tests/p4_02_composed/`.
- **Phase 4 inert runtime shell (P4-06):** Merged. `src/gmc_rebuild/runtime/` contains the composed `RuntimeShell` boundary, the immutable `SafetyVerdict`, and the five `BLOCKER_*` constants. The boundary is inert: it accepts already-constructed `HeartbeatProtocol`, `KillSwitchProtocol`, and `ReconciliationProtocol` instances by dependency injection and exposes one read-only `evaluate()` method returning a `SafetyVerdict`. No `__main__`, no daemon, no scheduler, no network, no broker SDK.
- **Phase 4 read-only operator view (P4-07):** Merged. `src/gmc_rebuild/runtime/_operator_view.py` contains the immutable `OperatorSafetyView` frozen dataclass and the pure `format_safety_verdict` function. The view takes an already-built `SafetyVerdict` by value, never calls a protocol method, and cannot widen a blocked verdict.
- **Phase 4 safety-policy-hardening tests (P4-08):** Merged. `tests/runtime/test_safety_policy_hardening.py` proves that `SafetyVerdict` is `clear` if and only if every required heartbeat component is FRESH, the kill switch is ARMED, and reconciliation is CLEAN; every other observed state remains blocked or advisory-blocked and visible to the operator view. P4-08 records the **safety foundation closure** governance-only and defines the **next stage** as **local/paper simulation boundary planning, not live execution**.
- **OPS-01 project resilience checkpoint:** Merged. `RECOVERY.md` documents the source-of-truth model (`KPH3802/gmc-rebuild` `main`), the 3-2-1-1-0 style redundancy layers, the recovery drill, and the local-only forbidden-artifact discipline.
- **OPS-02 Backblaze single-file restore drill:** Merged. Recorded under `governance/authorizations/2026-05-16_ops-02.md`.
- **OPS-03 X10 Pro panic-history investigation:** Merged. Recorded under `governance/authorizations/2026-05-16_ops-03.md`.
- **OPS-04 memory-pressure baseline + OPS roadmap:** Merged. Recorded under `governance/authorizations/2026-05-16_ops-04.md`.
- **OPS-04B memory-pressure measurement record:** Merged. Recorded under `governance/authorizations/2026-05-17_ops-04b.md`.
- **OPS-06 backup monitoring plan:** Merged via the GOV-01 packet (PR #106 at `4df8074`). `RECOVERY.md` §17 captures the recurring backup-health checks (GitHub reachability, Time Machine recency, Backblaze daemon state, Backblaze selected-volume visibility, Backblaze backlog and last-success thresholds, X10 mount / offline-intent status, X10 storage and panic watch, periodic byte-for-byte restore drill) and the escalation thresholds. The plan is **rules and thresholds only**; the periodic execution remains an operator-side action. No backup-monitoring automation is authorized.
- **GOV-01 governance reconciliation:** Merged via PR #106 at `4df8074`. Synchronizes the §8 step 4a `allowed_p2_infra` bash gate to the ten entries that match the actual authorized tree (`src`, `src/gmc_rebuild/config`, `src/gmc_rebuild/time`, `src/gmc_rebuild/logging`, `src/gmc_rebuild/risk`, `src/gmc_rebuild/heartbeat`, `src/gmc_rebuild/kill_switch`, `src/gmc_rebuild/reconciliation`, `src/gmc_rebuild/runtime`, `src/gmc_rebuild/simulation`); adds the No Chat-Only Risk Rule and the Risk Register / Future Controls section to `RECOVERY.md`; and adds the OPS-06 backup monitoring plan.
- **P5-01 inert local simulation boundary skeleton:** Merged via PR #104 at `76e5986` per `governance/authorizations/2026-05-17_p5-01.md`. `src/gmc_rebuild/simulation/_boundary.py` contains the closed `SimulationLane` enumeration (`LOCAL_ONLY` only), the immutable `SimulatedIntent` placeholder dataclass, the `SimulationBoundary` class, the `SimulationBoundaryError` exception, and the `propose` operation that returns the supplied intent unchanged if and only if the boundary's lane matches the intent's lane and the supplied `gmc_rebuild.runtime.SafetyVerdict` is `clear`. The new module imports only `__future__`, `dataclasses`, `datetime`, `enum`, `gmc_rebuild.risk`, and `gmc_rebuild.runtime`; it does not import any concrete fixture under `gmc_rebuild.heartbeat` / `gmc_rebuild.kill_switch` / `gmc_rebuild.reconciliation` and does not authorize runtime activation. `tests/test_package_skeleton.py` was extended by exactly one entry — `simulation` — in the authorized phase-package set.
- **P5-02 simulated order intent model:** Merged via PR #107 at `76335f9` per `governance/authorizations/2026-05-17_p5-02.md`. Extends `src/gmc_rebuild/simulation/_boundary.py` with two new closed `StrEnum` types (`SimulatedOrderSide` = `BUY` / `SELL`; `SimulatedOrderType` = `MARKET` / `LIMIT`), a new frozen, slotted `SimulatedOrderIntent` dataclass with exactly eight fields (`lane`, `intent_id`, `created_at`, `symbol`, `side`, `quantity`, `order_type`, `limit_price`) and strict per-field validation, and a new `SimulationBoundary.propose_order` method that gates the new record using the same `SafetyVerdict.clear` invariant as the existing `propose` and returns the supplied intent by identity. No new subpackage directory was added; no new test directory was created. The §8 step 4a bash gate is preserved at the ten entries synced by GOV-01.
- **P5-03 simulated-order-intent invariants tripwires:** Merged via PR #110 at `e8e652b` per `governance/authorizations/2026-05-17_p5-03.md`. Adds one new test file at `tests/simulation/test_simulated_order_intent_invariants.py` that asserts invariants over the merged P5-01 / P5-02 simulation surface (equality / hashability, `.build()` ↔ direct-construct equivalence, frozen / `__slots__` / exact-eight-field shape, `propose_order` determinism and identity-return, non-mutation on clear and blocked paths, blocker-code surfacing, and P5-01 ↔ P5-02 separation). Adds no production behaviour; no `src/**` change. The §8 step 4a bash gate is preserved at ten entries.
- **P5-04 composed safety-foundation × simulation integration tripwires:** Merged via PR #112 at `a9d85ec` per `governance/authorizations/2026-05-17_p5-04.md`. Adds one new test file at `tests/simulation/test_composed_safety_foundation.py` that exercises the real composed pipeline of the merged P4-06 / P4-07 safety foundation (`RuntimeShell`, `SafetyVerdict`) driven by the real merged P3-03 / P3-04 / P3-05 in-memory fakes and fed into the merged P5-01 / P5-02 `SimulationBoundary` (`propose`, `propose_order`). The 18 focused tripwire tests cover real-pipeline-clear identity return, per-blocker propagation for each of the five `BLOCKER_*` codes, multi-blocker fan-out, end-to-end non-mutation on clear and blocked paths (direct tripwire guarding the `RECOVERY.md` §16.5 "Paper and live execution remain blocked" red line), per-component partial staleness and unknown-required-component cases, recovery from a prior blocked verdict, and an inertness self-check. Adds no production behaviour; no `src/**` change. The §8 step 4a bash gate is preserved at ten entries.
- **Canonical status reconciliation:** Merged via PR #114 at `a02f17c`, with sibling Mode B PR #115 at `75d6f28`. Corrects the four P5-01 / P5-02 / P5-03 / P5-04 status reflection paragraphs in `MASTER_STATUS.md` from `**pending merge**` to `**merged on \`main\`**`. Adds a §8 step 8 canonical-doc staleness check to catch future stale-language drift. This Phase 5 entry plan preserves that reconciliation and does not reintroduce stale `**pending merge**` claims for the already-merged P5-01 / P5-02 / P5-03 / P5-04 / GOV-01 / OPS-06 packets.
- **Phase 5 entry planning (this packet):** Authorized by Kevin on 2026-05-18 per `governance/authorizations/2026-05-18_phase-5-entry-planning.md`. This authorization is **planning / enumeration only**: it opens the planning workstream that drafts this document; it does **not** open any successor P5 task, does **not** authorize any P5-05 or later implementation, does **not** authorize any simulation expansion, does **not** authorize any order semantics change, does **not** authorize any runtime activation, does **not** authorize any ops execution work, does **not** extend the §8 step 4a allowlist (preserved exactly at ten entries), does **not** modify any quality gate, and does **not** create any tag or release.
- **§8 step 4a `allowed_p2_infra` allowlist (post-GOV-01, preserved by this plan):** Exactly ten entries — `src`, `src/gmc_rebuild/config`, `src/gmc_rebuild/time`, `src/gmc_rebuild/logging`, `src/gmc_rebuild/risk`, `src/gmc_rebuild/heartbeat`, `src/gmc_rebuild/kill_switch`, `src/gmc_rebuild/reconciliation`, `src/gmc_rebuild/runtime`, `src/gmc_rebuild/simulation`.
- **Workflow in effect:** Codex builds → Perplexity Computer verifies → Kevin approves → Backup AI reviews adversarially at gates and high-risk decisions (per `AI_WORKFLOW.md` §1, §2, §4) and authors monitoring packet text under Mode B per ADR-008 (and ADR-009 once runtime exists on `main` per ADR-009 D7's bootstrap-avoidance clause).

Until Kevin records a separate written authorization for P5-05 / P4-09 / OPS-05 / OPS-07 / … enumeration or implementation, the only allowed work beyond routine maintenance is interpreting this plan, verifying existing state, and preparing decision packages. No successor P5 task is opened by this document.

---

## 2. Phase 5 Objective (Planning Level Only)

This section restates the Phase 5 objective at the **planning level** only. Naming an objective here does not authorize implementation. Each successor Phase 5 task requires its own separate written authorization from Kevin.

Phase 5 is conceived, **for planning purposes only**, as the **local simulation boundary phase** that sits on top of the closed P4-08 safety foundation. Its planning-level purpose is to define, at a documentation level, how the P4-06 `RuntimeShell` / `SafetyVerdict` safety gate can be exercised under increasingly tight test coverage while keeping the simulation strictly local, inert, and safety-gated. The merged P5-01 / P5-02 / P5-03 / P5-04 sequence has executed that purpose at the bounded scope each authorization named; any further P5-0N work continues to require its own separate written authorization.

In planning scope only (Section 3 below defines what may be discussed; Section 4 names the candidate task sequence; **none of this is implementation authorization**):

- Bounded, local-only, sandboxed test-and-tripwire coverage that exercises the merged P3 in-memory fakes, the merged P4-06 / P4-07 / P4-08 safety surface, and the merged P5-01 / P5-02 simulation surface together under `pytest`, with no network, no broker SDK, no real account identifiers, no real venue identifiers, no real endpoints, and no real secrets.
- Per-PR proof-bundle expectations that align with `plan/phase4_entry_plan.md` §6 and `AI_WORKFLOW.md` §3.
- ADR follow-ups that any future P5-0N decision would require — at minimum any ADR-009 implications that surface at the time of authorization, with implications for ADR-001 (secrets management), ADR-002 (kill switch), ADR-003 (reconciliation), ADR-005 (heartbeat), ADR-006 (deployment logs), and ADR-007 (minimal CI).

**Out of planning scope**, and forbidden until a successor P5 task is opened in writing by Kevin (and forbidden at the always-forbidden category level per `MASTER_STATUS.md` §6 independent of phase):

- Trading strategy code (signals, scanners, models, portfolio rules, backtests against real history).
- Broker execution code (order placement, position management, broker SDK integration, broker authentication).
- Paper-trading wired to a real broker (paper-broker connector, paper-account identifier, paper-API surface, paper-trading execution loop).
- Live-trading wired to a real broker (live-broker connector, live-account identifier, live-API surface, live-trading execution loop).
- Runtime daemons, schedulers, long-running services, background workers, operator-availability heartbeats wired to a real operator, or anything with a `__main__` entry point that touches accounts, markets, or money.
- Runtime activation of any merged Phase 3 fixture — `InMemoryHeartbeat`, `InMemoryKillSwitch`, or `InMemoryReconciliation` — from a `__main__`, a daemon, a scheduler, a re-export in `src/gmc_rebuild/__init__.py`, or any other runtime path.
- Market data ingestion code, real data pipelines, committed datasets, real or historical feeds.
- Real secrets, real credentials, real account identifiers, real broker / venue identifiers, real endpoints.
- Any concrete implementation of `KillSwitchProtocol`, `ReconciliationProtocol`, or `HeartbeatProtocol` that talks to a broker, network, filesystem outside the test sandbox, or scheduler.
- Any simulation expansion: additional `SimulationLane` member beyond `LOCAL_ONLY`, additional `SimulatedOrderSide` member beyond `BUY` / `SELL`, additional `SimulatedOrderType` member beyond `MARKET` / `LIMIT`, ninth field on `SimulatedOrderIntent`, additional method on `SimulationBoundary` beyond the merged `propose` and `propose_order`, additional placeholder / order record class.
- Any order semantics change: change to the meaning of `propose` or `propose_order`, change to the `SafetyVerdict.clear` precondition, change to the identity-return contract, addition of side effects.
- Any ops execution work: OPS-05 X10 Layer 5 promotion, OPS-06 backup-monitoring automation, OPS-07 DR drill execution, change to any Backblaze / Time Machine / drive / FileVault / sleep / power / USB / network / macOS setting.
- Any change that loosens `.gitignore`, `.pre-commit-config.yaml`, mypy strict mode, `detect-secrets`, the `MASTER_STATUS.md` §8 step 4 always-forbidden scan, the §8 step 4a per-PR Phase 2 / Phase 3 / Phase 4 / Phase 5 infrastructure allowlist scan, or the §8 step 4c recursive forbidden-token scan.
- Any new git tag, GitHub release, or version bump.

This split is intentional and mirrors the line `MASTER_STATUS.md` §6 / §7 already draws and that `plan/phase4_entry_plan.md` §2 restated for Phase 4. Phase 5 planning does not move that line; it discusses what would sit underneath it.

---

## 3. Allowed Planning Topics

While Phase 5 entry planning is in this opened-but-unscoped state (per `governance/authorizations/2026-05-18_phase-5-entry-planning.md`), Codex and Perplexity Computer may discuss and write planning artifacts on the following topics. Planning artifacts are documents, not code, and must be reviewable as documents.

1. **Current post-P5-04 state in prose.** Section 1 of this plan is the canonical planning-level statement.
2. **P5-05 (and any later P5-0N task) named only as future / not authorized.** Naming a task in Section 4 of this plan does **not** authorize it; the shape of each task remains a decision Kevin must make in writing at the time of authorization. The plan must not pre-commit any P5-05 shape (no specific test file, no specific module, no specific field, no specific method, no specific simulation lane, no specific order side / type member, no specific helper).
3. **Phase 5 entry criteria.** What must be true (baseline, governance, ADRs, monitoring cadence under ADR-008 §D3 / §D5 during the governance phase and ADR-009 D3 / D5 once runtime exists on `main` per ADR-009 D7's bootstrap-avoidance clause, Mode A / Mode B review per `AI_WORKFLOW.md` §4) before any future P5-05 implementation PR could open. Section 5 of this plan is the canonical planning-level statement.
4. **Per-PR proof-bundle expectations for any future P5-0N PR.** Restated from `AI_WORKFLOW.md` §3 and `plan/phase4_entry_plan.md` §6. Section 6 of this plan is the canonical planning-level statement.
5. **Rollback and stop conditions.** Restated for Phase 5 from `plan/phase4_entry_plan.md` §8. Section 8 of this plan is the canonical planning-level statement.
6. **Phase-boundary enforcement.** How any future P5-0N PR would prove it did not cross into broker execution, paper-trading wired to a real broker, live-trading wired to a real broker, real market data ingestion, real order routing, real strategy logic, real scheduler / daemon, real persistence, real deployment, real env-var loading, real secrets, real network, allowlist expansion beyond what its own authorization names, quality-gate relaxation, X10 Layer 5 promotion, backup-monitoring automation, or DR drill execution.
7. **ADR follow-ups.** Listed in Section 9 of this plan at planning level only.

Any planning topic that does not fit the list above must be raised with Kevin before a document is written, per `AI_WORKFLOW.md` §6 rule 7 ("No phase drift").

---

## 4. Candidate Future Phase 5 Task Sequence (Future / Not Authorized)

This section enumerates the merged P5-01 / P5-02 / P5-03 / P5-04 sequence as a historical record of what has already been authorized and merged, and names P5-05 only as **future / not authorized**. The shape of P5-05 (and any later P5-0N task) is itself a decision that Kevin must make in writing at the time of the relevant authorization. Naming a task in this section does **not** authorize it.

Per the standing sequencing rules (mirroring `plan/phase4_entry_plan.md` §4):

- Tasks land one at a time. PR P5-(N+1) is not opened until PR P5-N is accepted by Kevin.
- Each PR is small enough that the diff and the proof bundle (Section 6) fit a single review.
- Any PR that grows beyond its stated scope during implementation is split or stopped per `AI_WORKFLOW.md` §6 rule 6 / rule 7.

1. **PR P5-01 — first Phase 5 implementation task (authorized 2026-05-17; merged via PR #104 at `76e5986`).** Bounded inert local simulation boundary skeleton under `src/gmc_rebuild/simulation/` with focused tests under `tests/simulation/`. See `governance/authorizations/2026-05-17_p5-01.md` for the verbatim authorization. No runtime activation; no broker integration; no new subpackage beyond `simulation/`; the §8 step 4a allowlist was preserved unchanged per the authorization's scope (the `simulation` entry was later synced into the bash gate by GOV-01).
2. **PR P5-02 — second Phase 5 implementation task (authorized 2026-05-17; merged via PR #107 at `76335f9`).** Simulated order intent model added on top of the merged P5-01 inert local simulation boundary skeleton: two new closed `StrEnum` types (`SimulatedOrderSide` = `BUY` / `SELL`; `SimulatedOrderType` = `MARKET` / `LIMIT`), a new frozen, slotted `SimulatedOrderIntent` dataclass with exactly eight fields, and a new `SimulationBoundary.propose_order` method that gates the new record using `SafetyVerdict.clear` and returns the supplied intent by identity. See `governance/authorizations/2026-05-17_p5-02.md` for the verbatim authorization. No new subpackage; no `SimulationLane` expansion; no third `SimulatedOrderSide` / `SimulatedOrderType` member; no ninth field; the §8 step 4a bash gate was preserved at the ten entries synced by GOV-01.
3. **PR P5-03 — third Phase 5 implementation task (authorized 2026-05-17; merged via PR #110 at `e8e652b`).** Tripwire-only test file at `tests/simulation/test_simulated_order_intent_invariants.py` asserting invariants over the merged P5-01 / P5-02 simulation surface (24 focused tests covering equality / hashability, `.build()` ↔ direct-construct equivalence, frozen / `__slots__` / exact-eight-field shape, `propose_order` determinism and identity-return, non-mutation on clear and blocked paths, blocker-code surfacing, and P5-01 ↔ P5-02 separation). See `governance/authorizations/2026-05-17_p5-03.md` for the verbatim authorization. No production behaviour added; no `src/**` change; no existing test modification; the §8 step 4a bash gate was preserved at ten entries.
4. **PR P5-04 — fourth Phase 5 implementation task (authorized 2026-05-17; merged via PR #112 at `a9d85ec`).** Tripwire-only test file at `tests/simulation/test_composed_safety_foundation.py` exercising the real composed pipeline of the merged P4-06 / P4-07 safety foundation driven by the real merged P3-03 / P3-04 / P3-05 in-memory fakes and fed into the merged P5-01 / P5-02 `SimulationBoundary` (18 focused tests covering real-pipeline-clear identity return, per-blocker propagation for each of the five `BLOCKER_*` codes, multi-blocker fan-out, end-to-end non-mutation on clear and blocked paths, per-component partial staleness and unknown-required-component cases, recovery from a prior blocked verdict, and an inertness self-check). See `governance/authorizations/2026-05-17_p5-04.md` for the verbatim authorization. No production behaviour added; no `src/**` change; no existing test modification; the §8 step 4a bash gate was preserved at ten entries.
5. **PR P5-05 — fifth Phase 5 implementation task (candidate, future / not authorized).** A future, not-yet-authorized fifth Phase 5 implementation PR whose **shape is itself a decision Kevin must make in writing at the time of P5-05 authorization**. P5-05 is enumerated here only as a candidate task in the per-PR candidate sequence, on the same pattern that `plan/phase4_entry_plan.md` §4 used to enumerate `P4-02` / `P4-03` / `P4-04` / `P4-05` as future / not authorized before each was opened. Naming `P5-05` in this list does **not** authorize it. P5-05 may, when Kevin authorizes it in writing, be any shape Kevin chooses — a further tripwire-only test file, a documentation-only enumeration update, a different shape entirely — and Kevin remains free to name a different fifth Phase 5 implementation scope (or to redefine P5-05 entirely, or to defer it indefinitely) at the time of authorization. In all cases, P5-05 must independently satisfy: (a) Kevin's separate written authorization, with a sibling artifact under `governance/authorizations/` per `AI_WORKFLOW.md` §7; (b) the proof bundle in §6 below; (c) Mode A adversarial review per `AI_WORKFLOW.md` §4(2) (high-risk architecture decision — subsequent concrete Phase 5 behaviour behind the P4-08 safety foundation, if applicable) and / or §4(1) / §4(3) as applicable, delivered as PR-review text and not committed to the repository per §6 rule 5; (d) a sibling Mode B monitoring packet per ADR-008 §D3 / §D5 (or ADR-009 D3 / D5 once in force per ADR-009 D7's bootstrap-avoidance clause), committed by Codex under `monitoring/daily/` and merged to `main` in a separate monitoring PR **before** P5-05 merges; (e) where P5-05 introduces a new directory, a corresponding update to the `MASTER_STATUS.md` §8 step 4a `allowed_p2_infra` allowlist in the **same PR** that introduces the directory, per `MASTER_STATUS.md` §8 step 4b; and (f) preservation of every always-forbidden category in `MASTER_STATUS.md` §6 and every non-goal in §10 below (no simulation expansion beyond what the authorization names; no order semantics change; no runtime activation of any merged Phase 3 fixture from `__main__` / daemon / scheduler / re-export / runtime path without a specific separate written authorization; no broker / paper-trading / live-trading / market-data / order-routing / strategy / scheduler / daemon / persistence / deployment / env-var / secrets / network change; no allowlist expansion without a specific separate written authorization; no quality-gate relaxation; no X10 Layer 5 promotion; no backup-monitoring automation; no DR drill execution; no tag; no release).

Further candidate tasks beyond P5-05 (P5-06, P5-07, …) are deliberately **not enumerated** in this plan. The shape of any successor to P5-05 — including any further local simulation boundary work, any paper-broker integration (which would require its own separate written authorization and would itself be a phase-gate-adjacent decision under `AI_WORKFLOW.md` §4), any live integration (which is forbidden at the always-forbidden category level per `MASTER_STATUS.md` §6 independent of phase), or any other Phase 5 follow-up — is itself a decision that Kevin must make in writing at the time of the relevant authorization. Any later enumeration of P5-06 / P5-07 / … must itself be authorized as a separate documentation-only update to this plan and must not authorize implementation.

**§8 step 4a allowlist note.** The `allowed_p2_infra` allowlist on `main` after GOV-01 contains exactly ten entries (`src`, `src/gmc_rebuild/config`, `src/gmc_rebuild/time`, `src/gmc_rebuild/logging`, `src/gmc_rebuild/risk`, `src/gmc_rebuild/heartbeat`, `src/gmc_rebuild/kill_switch`, `src/gmc_rebuild/reconciliation`, `src/gmc_rebuild/runtime`, `src/gmc_rebuild/simulation`). This plan preserves the allowlist unchanged. Any future P5 PR that introduces a new directory must add it to the allowlist in the same PR that introduces the directory, per the standing rule in `MASTER_STATUS.md` §8 step 4b, and must be authorized in writing for the specific directory by Kevin.

---

## 5. Phase 5 Entry Criteria (Planning Level Only)

The criteria below governed the original P5-01 entry decision and continue to govern successor Phase 5 tasks by analogy. P5-01 through P5-04 have already satisfied their separate authorization, review, and monitoring requirements as recorded in Section 1 and Section 4. Any future P5-05 / P5-0N work must independently satisfy the applicable criteria and be separately authorized by Kevin in writing.

1. The accepted Phase 1 baseline is `1f101fc` (per `MASTER_STATUS.md` §3) and `main` is a descendant of it (`MASTER_STATUS.md` §8 step 3 returns OK).
2. Phase 2 is formally closed (governance-only) per `governance/authorizations/2026-05-12_phase-2-closure.md`. **Satisfied as of 2026-05-12.**
3. Phase 3 is formally closed (governance-only) per `governance/authorizations/2026-05-14_phase-3-closure.md`. **Satisfied as of 2026-05-14.**
4. Phase 4 safety foundation closure is recorded by P4-08 per `governance/authorizations/2026-05-16_p4-08.md`. **Satisfied as of 2026-05-16.**
5. The merged P5-01 inert local simulation boundary skeleton, P5-02 simulated order intent model, P5-03 invariants tripwires, and P5-04 composed safety-foundation × simulation integration tripwires are on `main`. **Satisfied as of 2026-05-17.**
6. This Phase 5 Entry Plan (`plan/phase5_entry_plan.md`) has been merged on `main` as planning-only documentation. (This document targets that merge; merging this document does not by itself open any successor P5 task.)
7. Kevin has explicitly authorized each successor P5 task in writing — commit message, PR comment, or governance entry, not a chat message — per `MASTER_STATUS.md` §7.3 and recorded in a sibling artifact under `governance/authorizations/` per `AI_WORKFLOW.md` §7. Each successor P5 PR's scope must also be named in the authorization, per the §7.4 pattern that `plan/phase4_entry_plan.md` §5 applied to P4-0N.
8. Each successor P5 PR has been reviewed in **Mode A** by the Backup AI per `AI_WORKFLOW.md` §4(2) as applicable. The Mode A critique is delivered as PR-review text and is **not** committed to the repository (per `AI_WORKFLOW.md` §6 rule 5).
9. A **Mode B** monitoring packet has been authored by the Backup AI per ADR-008 §D3 (or ADR-009 D3 once in force per ADR-009 D7's bootstrap-avoidance clause) and committed by Codex under `monitoring/daily/` per ADR-008 §D4 (or ADR-009 D4) for the active workday on which each successor P5 PR is open / merged. Per ADR-008 §D5, no phase-opening or phase-expanding PR may merge while any required packet from any prior active workday is missing without a catch-up note covering it; Perplexity Computer confirms this before verifying each successor P5 PR.
10. Each successor P5 implementation PR is infrastructure-only at the planning-level definition of Section 2 above (sandboxed, local-only, no broker, no paper-trading or live-trading wired to a real broker, no market data, no order placement, no scheduler / daemon, no real secrets, no runtime activation of any merged Phase 3 fixture, no simulation expansion beyond what its own authorization names, no order semantics change, no ops execution work).

If any criterion fails, the relevant successor P5 task stays closed. Phase 4 safety foundation closure stays recorded. Phase 3 stays formally closed. Phase 2 stays formally closed. Routine governance maintenance under `MASTER_STATUS.md` §9 continues.

---

## 6. Required Proof For Each Future Phase 5 PR

Each future Phase 5 PR must include the proof bundle defined in `AI_WORKFLOW.md` §3 and restated in `plan/phase4_entry_plan.md` §6. Restated here for Phase 5 scope.

1. **Git state.**
   - `git status` showing a clean tree after commit.
   - `git log --oneline -10` showing the head commit and recent history.
   - `git rev-parse HEAD` showing the exact commit hash under review.
   - `git diff <baseline>..HEAD` against the accepted Phase 1 baseline `1f101fc` (or a later accepted baseline if one has been recorded in `MASTER_STATUS.md` §3 by that time).
2. **Tests and pre-commit.**
   - Full output of `pre-commit run --all-files` (must pass, or every failure documented).
   - Full output of `pytest` (must pass).
3. **Phase-boundary checklist.** For each Phase 5 PR, the verification report explicitly confirms:
   - No new top-level directories outside the documented set.
   - No new modules under `strategy/`, `signals/`, `broker/`, `execution/`, `live/`, `daemons/`, `data/`, `market_data/`, `orders/`, `secrets/`, or any name on the `MASTER_STATUS.md` §8 step 4 always-forbidden list, anywhere in the tree (the §8 step 4c recursive forbidden-token scan returns OK / subshell exit `0`).
   - No new long-running entry points (`if __name__ == "__main__"` services, scheduler configs, background workers, daemons).
   - No new secrets, real credentials, real account identifiers, real broker / venue identifiers, real endpoints, or generated data files.
   - No new broker SDK dependency, no new market-data SDK dependency, no new scheduler or background-job dependency.
   - No runtime activation of any merged Phase 3 fixture — `InMemoryHeartbeat`, `InMemoryKillSwitch`, or `InMemoryReconciliation` — from a `__main__`, a daemon, a scheduler, a re-export in `src/gmc_rebuild/__init__.py`, or any other runtime path, unless the specific activation is named in Kevin's separate written authorization for the PR and is itself subject to Mode A per `AI_WORKFLOW.md` §4(2).
   - No simulation expansion (no `SimulationLane` member beyond `LOCAL_ONLY`, no `SimulatedOrderSide` member beyond `BUY` / `SELL`, no `SimulatedOrderType` member beyond `MARKET` / `LIMIT`, no ninth field on `SimulatedOrderIntent`, no additional method on `SimulationBoundary` beyond the merged `propose` and `propose_order`, no additional placeholder / order record class) unless the specific expansion is named in Kevin's separate written authorization for the PR.
   - No order semantics change (no change to the meaning of `propose` or `propose_order`, no change to the `SafetyVerdict.clear` precondition, no change to the identity-return contract, no addition of side effects) unless the specific change is named in Kevin's separate written authorization for the PR.
   - No ops execution work (no X10 Layer 5 promotion, no backup-monitoring automation, no DR drill execution, no Backblaze / Time Machine / drive / FileVault / sleep / power / USB / network / macOS setting change) unless the specific work is named in Kevin's separate written authorization for the PR.
   - No new concrete implementation of `KillSwitchProtocol` / `ReconciliationProtocol` / `HeartbeatProtocol` that talks to a broker, network, filesystem outside the test sandbox, or scheduler.
   - No relaxation of `.gitignore`, `.pre-commit-config.yaml`, mypy strict mode, `detect-secrets`, `.secrets.baseline`, the `MASTER_STATUS.md` §8 step 4 always-forbidden scan, the §8 step 4a per-PR infrastructure allowlist scan, or the §8 step 4c recursive forbidden-token scan.
   - Any new authorized directory is added to the `MASTER_STATUS.md` §8 step 4a allowlist in the same PR that introduces the directory, per the standing rule in §8 step 4b.
4. **File-specific evidence.** Per `AI_WORKFLOW.md` §3.4, each changed file is named and the verifier states what was verified for it (required headings present, decision recorded, status set, links valid for ADRs; structure preserved, instructions still clear, no placeholder leakage for templates; settings match what the README, ADRs, and `MASTER_STATUS.md` claim for config changes; cross-references still resolve, phase claims still accurate for documentation changes).
5. **Docs updated.** Any change to interfaces or conventions is reflected in the relevant document (ADR update, new ADR, or `MASTER_STATUS.md` entry) in the same PR — no orphaned code without a governance hook.
6. **ADR-009 cadence status.** The verification report names whether ADR-008 §D3 / §D5 (governance-phase cadence) or ADR-009 D3 / D5 (runtime-phase cadence) governs the PR per ADR-009 D7's bootstrap-avoidance clause. Until runtime exists on `main`, ADR-008 §D3 / §D5 continue to govern.
7. **Mode A / Mode B status.** The verification report names whether `AI_WORKFLOW.md` §4 Mode A and ADR-008 §D3 (or ADR-009 D3) Mode B apply to the PR, and where each artifact lives (PR-review text for Mode A; `monitoring/daily/YYYY-MM-DD.md` for Mode B). For phase-gate PRs and high-risk-architecture PRs, **both** artifacts are required per ADR-008 §D7 (or ADR-009 D7 once in force).
8. **Canonical-doc staleness check.** Per `MASTER_STATUS.md` §8 step 8, the verification report confirms that the canonical docs (`MASTER_STATUS.md`, `README.md`, `RECOVERY.md`, `plan/phase4_entry_plan.md`, and — once merged — `plan/phase5_entry_plan.md`) do not contain stale `**pending merge**` language for the already-merged P5-01 / P5-02 / P5-03 / P5-04 / GOV-01 / OPS-06 packets. The PR may carefully scope its own pending state, but must not reintroduce stale claims about prior merged work.

A Phase 5 PR that does not carry this bundle is not eligible for Kevin's review.

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

- Any successor Phase 5 PR that defines a new control surface, a new trust boundary, or a non-reversible decision — `AI_WORKFLOW.md` §4(2). Examples include any first runtime activation of any merged Phase 3 fixture, any first connection of the simulation boundary to a real broker, real market data feed, real order router, or real persistence layer, any ADR update that changes the kill-switch / reconciliation / heartbeat policy, and any change that touches the secrets-management discipline.
- Any Phase 5 PR that would, if wrong, cause real-world loss — `AI_WORKFLOW.md` §4(3). Such a PR is by definition **out of Phase 5 scope** per Section 2 (no live-trading authorization, no broker integration, no paper-trading wired to a real broker, no operator-availability heartbeat wired to a real operator, no data retention or destruction policy that affects real accounts or markets). The correct response is to treat it as scope drift and stop per `AI_WORKFLOW.md` §6 rule 7 and Section 8 of this plan, **not** to invoke the Backup AI in Mode A as a substitute for stopping.

**Mode B continuous governance monitor** per ADR-008 §D3 (or ADR-009 D3 once in force per ADR-009 D7's bootstrap-avoidance clause) is required on any active workday on which the default branch changes or a pull request is open, updated, or merged. The Backup AI authors packet text; Codex commits per `AI_WORKFLOW.md` §1.4 and §6 rule 1 and ADR-008 §D1 (or ADR-009 D1). When both Mode A and Mode B fire on the same PR, **two distinct artifacts are required** per ADR-008 §D7 (or ADR-009 D7 once in force): the Mode A written critique (PR-review text only, not committed to the repo) and the Mode B monitoring packet (committed by Codex under `monitoring/daily/`). The packet may link to or quote the critique for context, but does not replace it.

The Backup AI produces a written critique only (Mode A) or packet text only (Mode B). It does not edit other files, does not commit, does not push, does not merge, and does not approve. `AI_WORKFLOW.md` §6 rule 1 ("One builder at a time") is preserved: Codex remains the only role that writes to the repository.

---

## 8. Rollback and Stop Conditions

Each future Phase 5 PR must support a clean rollback.

Rollback rules:

- Every Phase 5 PR is reversible by a single `git revert` on the merge commit. PRs that bundle unrelated changes are split until this is true.
- The accepted Phase 1 baseline (`1f101fc` per `MASTER_STATUS.md` §3) is the last-known-good state. Reverting all Phase 2, Phase 3, Phase 4, and Phase 5 work returns the tree to a descendant of that baseline.
- A deployment log entry per `docs/deploys/deploy-log-template.md` is required if any Phase 5 change affects developer environments (e.g. new tooling requirement, new pre-commit hook), even though no runtime is being deployed under the planning-level definition of Section 2.
- Once runtime exists on `main`, ADR-009 D5's missed-packet severity replaces ADR-008 §D5 on a going-forward basis per ADR-009 D7's bootstrap-avoidance clause. Until runtime exists, ADR-008 §D5 continues to apply.

Stop conditions — if any of the following occurs, Phase 5 work pauses and the situation is escalated to Kevin before further changes:

1. A Phase 5 PR cannot satisfy the proof bundle in Section 6 without expanding scope.
2. A Phase 5 PR is found to cross into strategy, broker, paper-trading wired to a real broker, live-trading, market data ingestion, real secrets, order placement, scheduler / daemon, persistence outside the test sandbox, runtime-daemon territory, runtime activation of any merged Phase 3 fixture beyond what is named in the PR's separate written authorization, simulation expansion beyond what is named in the PR's separate written authorization, order semantics change beyond what is named in the PR's separate written authorization, or ops execution work beyond what is named in the PR's separate written authorization — at review time or after merge.
3. `pre-commit` or `pytest` fails and the proposed fix is to weaken the hook, loosen mypy strict mode, relax `detect-secrets`, or modify `.secrets.baseline` to silence a real finding.
4. `MASTER_STATUS.md` and a Phase 5 PR disagree about the current phase, the accepted baseline, the `allowed_p2_infra` allowlist, the canonical post-P5-04 state, or the allowed next decisions.
5. Two changes attempt to land on the default branch simultaneously, violating `AI_WORKFLOW.md` §6 rule 4 (one builder, one branch per task).
6. The Backup AI (when invoked per Section 7) identifies a specific invariant violation that the verifier did not catch.
7. A required Mode B monitoring packet under ADR-008 §D3 (or ADR-009 D3 once in force) is missing for a prior active workday and no catch-up note per ADR-008 §D5 (or ADR-009 D5) has been committed. Per ADR-008 §D5, no phase-opening or phase-expanding PR may merge under that condition.
8. A Phase 5 PR proposes to re-export `InMemoryHeartbeat`, `InMemoryKillSwitch`, or `InMemoryReconciliation` from `src/gmc_rebuild/__init__.py`, or to consume any of them from a `__main__` / daemon / scheduler / runtime path, without that specific activation being named in Kevin's separate written authorization and without Mode A per `AI_WORKFLOW.md` §4(2).
9. A Phase 5 PR proposes any reintroduction of stale `**pending merge**` language for the already-merged P5-01 / P5-02 / P5-03 / P5-04 / GOV-01 / OPS-06 packets, violating the canonical status reconciliation merged via PR #114.

In any stop condition, the default is to pause and ask Kevin. Per `AI_WORKFLOW.md` §6 rule 10: "When in doubt, stop. A paused task is recoverable. A merged Phase 5 change made by accident is not."

---

## 9. ADR Follow-ups That Phase 5 Successor Work Requires

Listed here for planning visibility. None of these follow-ups is authorized by this plan. Each requires its own separate written authorization from Kevin, a sibling artifact under `governance/authorizations/`, and the applicable Mode A / Mode B review per `AI_WORKFLOW.md` §4 and ADR-008 (or ADR-009 once in force).

- **ADR-009 — runtime monitoring cadence and missed-packet severity.** Accepted on 2026-05-13 per `governance/authorizations/2026-05-13_p3-01-acceptance.md`. ADR-009 D7's bootstrap-avoidance clause keeps ADR-008 §D3 / §D5 in force until runtime exists on `main`. Any future Phase 5 PR that introduces runtime must satisfy the ADR-009 D3 / D5 cadence as it takes effect.
- **ADR-001 — secrets management.** Phase 5 introduces no real secrets, no real credentials, no real account identifiers, no real broker / venue identifiers, and no real endpoints under the Section 2 planning-level definition. If any later Phase 5 task ever needs to reference a real secret (it must not, under Section 2), ADR-001's secrets-management discipline must be revisited in a separate PR before the reference lands. This plan does not authorize that revisit.
- **ADR-002 — runtime kill-switch architecture.** The P3-04 `InMemoryKillSwitch` fake conforms to `KillSwitchProtocol` (ADR-002) at the test-fixture level. Any Phase 5 use of the fake (already exercised by the merged P5-04 composed tripwires) must align with ADR-002 and must not add broker side effects, order placement, or network calls. If a future Phase 5 use surfaces a gap in ADR-002, the gap is recorded in an ADR update, not silently coded around.
- **ADR-003 — broker reconciliation discipline.** The P3-05 `InMemoryReconciliation` fake conforms to `ReconciliationProtocol` (ADR-003) at the test-fixture level with `UNAVAILABLE` / `FAILED` / `WARNING` distinguished. Any Phase 5 use of the fake (already exercised by the merged P5-04 composed tripwires) must align with ADR-003 and must not add broker integration, account fetch, fills, or order objects.
- **ADR-005 — operator availability heartbeat.** The P3-03 `InMemoryHeartbeat` fake conforms to `HeartbeatProtocol` (ADR-005) at the test-fixture level. Any Phase 5 use of the fake (already exercised by the merged P5-04 composed tripwires) must align with ADR-005 and must not add a scheduler, an operator-availability daemon, or an external sink.
- **ADR-006 — deployment logs.** Any Phase 5 change that affects developer environments requires a deployment log entry per `docs/deploys/deploy-log-template.md`. No runtime deployment is authorized; the deployment-log discipline applies to developer-environment changes only.
- **ADR-007 — minimal CI strategy.** The local quality-gate stack (pre-commit, Ruff, mypy strict, detect-secrets, pytest) is unchanged by this plan. Any Phase 5 PR that proposes a CI change must do so as a separate ADR update reviewed under `AI_WORKFLOW.md` §4(2).

The list above is not exhaustive. Any later ADR follow-up that surfaces during the planning workstream must be raised with Kevin and recorded in a sibling artifact under `governance/authorizations/` before the follow-up PR opens.

---

## 10. Explicitly Not Authorized

For audit clarity, the following categories remain forbidden under this planning document. Each is forbidden by default per `MASTER_STATUS.md` §6 and `governance/authorizations/2026-05-18_phase-5-entry-planning.md` "Explicitly Not Authorized"; mirroring them here is **not** a re-authorization and is **not** a relaxation. Each requires Kevin's separate written authorization per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 / rule 7, a sibling artifact under `governance/authorizations/`, the applicable Mode A / Mode B review, and (where it introduces a new directory) a corresponding update to the §8 step 4a allowlist in the same PR.

- **Any successor Phase 5 task beyond P5-04.** P5-05 / P5-06 / … remain future / not authorized. Each requires its own separate written authorization and, if merely enumerated first, a separate docs-only enumeration update that does not authorize implementation.
- **Any simulation expansion.** No additional `SimulationLane` member beyond `LOCAL_ONLY`. No additional `SimulatedOrderSide` member beyond `BUY` / `SELL`. No additional `SimulatedOrderType` member beyond `MARKET` / `LIMIT`. No ninth field on `SimulatedOrderIntent`. No additional method on `SimulationBoundary` beyond the merged `propose` (P5-01) and `propose_order` (P5-02). No additional placeholder / order record class. No new public name on `gmc_rebuild.simulation`.
- **Any order semantics change.** No change to the meaning of `propose` or `propose_order`, no change to the `SafetyVerdict.clear` precondition, no change to the identity-return contract, no addition of side effects.
- **Any runtime activation.** No `__main__` entry point, no daemon, no scheduler, no background worker, no long-running service, no live execution loop, no re-export of any merged Phase 3 fixture from `src/gmc_rebuild/__init__.py` or any other runtime path, no consumption of any merged Phase 3 fixture from a `__main__`, a daemon, a scheduler, or any runtime path.
- **Any ops execution work.** No X10 Layer 5 promotion (OPS-05 remains future / not authorized). No backup-monitoring automation (the OPS-06 plan remains rules and thresholds only; the periodic execution remains an operator-side action). No DR drill execution (OPS-07 remains future / not authorized). No change to any Backblaze / Time Machine / drive / FileVault / sleep / power / USB / network / macOS setting.
- **Broker integration.** No broker SDK, no broker connector, no broker reconciliation runtime, no broker authentication, no broker credentials.
- **Paper-trading wired to a real broker.** No paper-broker connector, no paper-account identifier, no paper-API surface, no paper-trading execution loop.
- **Live-trading wired to a real broker.** No live-broker connector, no live-account identifier, no live-API surface, no live-trading execution loop.
- **Market-data integration.** No market-data ingestion code, no market-data pipeline, no committed dataset, no live / delayed / paper data feed.
- **Order management / routing.** No order objects beyond the merged P5-02 `SimulatedOrderIntent`, no order placement, no position management, no fills, no trade reports, no order routing logic, no venue selection, no execution adapter, no FIX session, no REST client, no WebSocket client.
- **Strategy logic.** No trading signals, no scanners, no models, no portfolio rules, no backtests.
- **Scheduling.** No cron-style scheduler, no APScheduler, no background-job framework, no operator-heartbeat daemon, no kill-switch runtime, no reconciliation runtime.
- **Persistence.** No SQLite, no on-disk database, no on-disk reconciliation snapshot, no on-disk heartbeat state, no log sink, no file artifact written by runtime code.
- **Deployment.** No deployment workflow, no rollout, no rollback runtime, no CI/CD pipeline beyond the existing local pre-commit and pytest gates.
- **Secrets / env-var loading.** No real secrets, no real credentials, no `.env` files, no `os.environ` / `os.getenv` reads, no real account identifiers, no real broker / venue identifiers, no real endpoints embedded anywhere in the repository under this plan.
- **Network.** No `socket`, no `urllib`, no `requests`, no `http`, no `ssl`, no `smtplib`, no `ftplib`, no outbound or inbound network code.
- **Concrete risk implementations inside the runtime package.** No concrete implementation of `KillSwitchProtocol` / `ReconciliationProtocol` / `HeartbeatProtocol` lands inside `src/gmc_rebuild/risk/` under this plan. The P2-05 boundary (types and abstract `typing.Protocol` definitions only) is preserved.
- **New trading behavior.** No change that introduces, simulates beyond the merged P5-01..P5-04 surface, or wires up trading behavior — in any module, under any name, anywhere in the tree.
- **Tooling relaxation.** No weakening of pre-commit, Ruff, mypy strict mode, `detect-secrets`, `.gitignore`, `.secrets.baseline`, the `MASTER_STATUS.md` §8 step 4 always-forbidden scan, the §8 step 4a per-PR infrastructure allowlist scan, or the §8 step 4c recursive forbidden-token scan.
- **§8 step 4a allowlist expansion.** The `allowed_p2_infra` allowlist is **not** extended by this plan. Any future addition requires a separate written authorization that names a specific implementation task, a sibling artifact under `governance/authorizations/`, and an allowlist update made in the same PR that introduces the new directory.
- **Source / test changes.** No file under `src/**` or `tests/**` is modified or created by this plan or by the PR that lands it.
- **New tags or releases.** No git tag, no GitHub release, no version bump.
- **Reintroduction of stale "pending merge" language.** The canonical status reconciliation merged via PR #114 corrected the four P5-01 / P5-02 / P5-03 / P5-04 status reflection paragraphs to `**merged on \`main\`**`. This plan and the PR that lands it preserve those corrections. The PR may, where it carefully scopes its own pending state (the planning PR itself is pending merge before it merges), describe that pending state without reintroducing stale claims about the already-merged P5-01 / P5-02 / P5-03 / P5-04 / GOV-01 / OPS-06 packets.
- **Mode A / Mode B substitution.** This plan is governance prose, not a control-surface decision; it does not substitute for adversarial review of any future P5-05 implementation PR or any future runtime / broker / market-data / order / strategy / scheduler / persistence / deployment PR. Any such future PR must independently satisfy `AI_WORKFLOW.md` §4 (Mode A) and ADR-008 / ADR-009 (Mode B) as applicable.

The always-forbidden categories in `MASTER_STATUS.md` §6 and `plan/phase4_entry_plan.md` §10 — strategy code, broker execution code, paper-trading or live-trading wired to a real broker, runtime daemons affecting accounts, real market data ingestion, order placement, and real secrets — remain forbidden in all modes. This plan does not relax them and does not record any relaxation.

---

## 11. Supporting References (Non-Authoritative)

- Phase 1 accepted baseline: `1f101fc` (`MASTER_STATUS.md` §3).
- Phase 2 entry plan: `plan/phase2_entry_plan.md`.
- Phase 2 closure authorization: `governance/authorizations/2026-05-12_phase-2-closure.md`.
- Phase 3 entry planning authorization (pattern reference for prior planning authorizations): `governance/authorizations/2026-05-13_phase-3-entry-planning.md`.
- Phase 3 entry plan: `plan/phase3_entry_plan.md`.
- Phase 3 closure authorization: `governance/authorizations/2026-05-14_phase-3-closure.md`.
- Phase 4 entry planning authorization (pattern reference for this Phase 5 entry planning authorization): `governance/authorizations/2026-05-14_phase-4-entry-planning.md`.
- Phase 4 entry plan (pattern reference for this Phase 5 entry plan): `plan/phase4_entry_plan.md`.
- Phase 4 safety foundation closure (P4-08): `governance/authorizations/2026-05-16_p4-08.md`.
- P5-01 authorization: `governance/authorizations/2026-05-17_p5-01.md` — merged via PR #104 at `76e5986`.
- P5-02 authorization: `governance/authorizations/2026-05-17_p5-02.md` — merged via PR #107 at `76335f9`.
- P5-03 authorization: `governance/authorizations/2026-05-17_p5-03.md` — merged via PR #110 at `e8e652b`.
- P5-04 authorization: `governance/authorizations/2026-05-17_p5-04.md` — merged via PR #112 at `a9d85ec`.
- GOV-01 governance reconciliation authorization: `governance/authorizations/2026-05-17_gov-01.md` — merged via PR #106 at `4df8074`.
- OPS-06 backup monitoring plan authorization: `governance/authorizations/2026-05-17_ops-06.md` — recorded in `RECOVERY.md` §17.
- Canonical status reconciliation (P5-01..P5-04 / OPS-06): PR #114 at `a02f17c`, with sibling Mode B PR #115 at `75d6f28`.
- Phase 5 entry planning authorization (this plan's authorization of record): `governance/authorizations/2026-05-18_phase-5-entry-planning.md`.
- ADR-008 (governance-phase monitoring cadence): `docs/decisions/ADR-008_monitoring_cadence_and_ai_monitor_role.md` §D3 / §D5.
- ADR-009 (runtime-phase monitoring cadence): `docs/decisions/ADR-009_runtime_monitoring_cadence.md` — Accepted on 2026-05-13; D7 bootstrap-avoidance clause keeps ADR-008 §D3 / §D5 in force until runtime exists on `main`.
- Workflow separation of duties: `AI_WORKFLOW.md` §1 (roles), §2 (standard workflow), §3 (required proof), §4 (when to use the Backup AI), §6 (anti-chaos rules), §7 (durable authorization artifacts).
