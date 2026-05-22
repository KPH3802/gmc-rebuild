# Phase 6 Entry Plan

**Status:** This document is **documentation-only**, created at Kevin's direction on 2026-05-19 as [`docs/FOUNDATION_TO_DRY_RUN_ROADMAP.md`](../docs/FOUNDATION_TO_DRY_RUN_ROADMAP.md) §8 Packet 2 (the dry-run entry plan). It is **planning / enumeration only**: it records the post-foundation-complete state, names the proposed Phase 6 capability sequence as the local dry-run trading engine skeleton, names the entry criteria, the proof bundle, the review protocol, the rollback / stop conditions, and the ADR follow-ups, and originally named every candidate Phase 6 task as **future / not authorized** at authoring time (P6-01, P6-02, P6-03 planning, P6-03 implementation, and P6-04 implementation (Direction A) have since merged on `main`; the P6-05 planning packet (PR #162) and the P6-05 implementation authorization (PR #164) have also merged on `main`, so P6-05 implementation is **authorized but not yet implemented** — see the §4 entries below; P6-06 / P6-07 remain **future / not authorized**). It does **not** itself authorize implementation (the P6-05 implementation authorization of record is the separate artifact `governance/authorizations/2026-05-22_p6-05.md`, not this plan). It does **not** open any successor Phase 6 task. It does **not** authorize any runtime activation of any merged Phase 3 fixture, P4-06 / P4-07 / P4-08 safety surface, or P5-01 / P5-02 simulation surface, does **not** authorize any broker / paper-trading / live-trading / market-data / order-routing / strategy / scheduler / daemon / persistence / deployment work, does **not** authorize any ops execution work, does **not** extend the `MASTER_STATUS.md` §8 step 4a `allowed_p2_infra` allowlist (preserved exactly at the ten entries synced by GOV-01), does **not** relax any quality gate, does **not** modify any `src/**` file, does **not** modify any `tests/**` file, and does **not** create any tag or release. The authorization of record for any future Phase 6 implementation packet is itself a separate written authorization from Kevin per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §7, recorded in a sibling artifact under `governance/authorizations/`; this plan does not stand in for that authorization.

**Created:** 2026-05-19 UTC

**Owner:** Claude Code (builder, per the GOV-02 execution-environment workflow rule), opening this planning packet at Kevin's written direction on 2026-05-19.

**Naming choice:** The user's instruction suggested `phase6_dry_run_entry_plan.md`. This plan uses `phase6_entry_plan.md` to match the existing repo convention established by `plan/phase2_entry_plan.md`, `plan/phase3_entry_plan.md`, `plan/phase4_entry_plan.md`, and `plan/phase5_entry_plan.md`, none of which carries a descriptive suffix beyond the phase number. The descriptive label "dry-run trading engine skeleton" is carried in the document title (§2) and throughout the prose rather than in the filename.

**Scope:** This document records the Phase 6 entry plan, restates the post-foundation-complete state at the planning level only, and originally named P6-01 / P6-02 / … as **future / not authorized** at authoring time (P6-01 has since merged on `main` at `d52551a`, P6-02 at `4785e24`, P6-03 planning via PR #144 at `583f457`, P6-03 implementation via PR #146 at `8d98a41`, and P6-04 implementation (Direction A) via PR #158 at `cea8553`; the P6-05 planning packet merged via PR #162 at `5d1c743` and the P6-05 implementation authorization merged via PR #164 at `cb4574e`, so P6-05 implementation is **authorized but not yet implemented**; P6-06 / … remain **future / not authorized** — see §4 below). It does not authorize any successor P6 task, any runtime activation, any broker / paper-trading / live-trading / market-data / order-routing / strategy / scheduler / daemon / persistence / deployment work, any ops execution work, any extension of the §8 step 4a allowlist, any quality-gate modification, any new `src/**` change, any new `tests/**` change, any tag, any release, or any always-forbidden category change under `MASTER_STATUS.md` §6.

If anything here conflicts with `MASTER_STATUS.md`, `AI_WORKFLOW.md`, [`docs/GMC_PROJECT_MAP.md`](../docs/GMC_PROJECT_MAP.md), or [`docs/FOUNDATION_TO_DRY_RUN_ROADMAP.md`](../docs/FOUNDATION_TO_DRY_RUN_ROADMAP.md), those files win. This document is supporting planning and status material; it does not redefine the phase boundary, and it does not make any new phase-gate decision itself.

This plan is the Phase 6 analogue to `plan/phase5_entry_plan.md`. It mirrors that file's structure deliberately so the pattern is the same and is reviewable on the same axes. Where this plan names a successor Phase 6 task, the task is **future / not authorized** and requires its own separate written authorization from Kevin, a sibling artifact under `governance/authorizations/`, applicable Mode A / Mode B review per `AI_WORKFLOW.md` §4 and ADR-008 / ADR-009, and (where it introduces a new directory) a corresponding update to the §8 step 4a allowlist in the same PR.

---

## 1. Current Post-Foundation-Complete State

The facts below are taken from `MASTER_STATUS.md`, [`docs/FOUNDATION_TO_DRY_RUN_ROADMAP.md`](../docs/FOUNDATION_TO_DRY_RUN_ROADMAP.md), [`docs/decisions/2026-05-19_foundation_complete_confirmation.md`](../docs/decisions/2026-05-19_foundation_complete_confirmation.md), and the durable authorization artifacts under `governance/authorizations/`. This section restates them at planning level only and does not change any of them.

- **Phase 1 accepted baseline:** `1f101fc` (`docs: fix Phase 1 verification blockers`), accepted per Kevin's written acceptance note on PR #3 (see `MASTER_STATUS.md` §3). Phase 1 baseline is unchanged by this plan.
- **Phase 2:** Formally closed (governance-only) per `governance/authorizations/2026-05-12_phase-2-closure.md`. The `plan/phase2_entry_plan.md` §4 P2-01..P2-05 sequence is merged on `main` (config, time, logging, risk submodules plus the package skeleton).
- **Phase 3:** Formally closed (governance-only) per `governance/authorizations/2026-05-14_phase-3-closure.md`. The three merged in-memory single-protocol test fixtures are `InMemoryHeartbeat` (P3-03, `src/gmc_rebuild/heartbeat/`), `InMemoryKillSwitch` (P3-04, `src/gmc_rebuild/kill_switch/`), and `InMemoryReconciliation` (P3-05, `src/gmc_rebuild/reconciliation/`). None is re-exported from `src/gmc_rebuild/__init__.py`; none is consumed from a `__main__`, a daemon, a scheduler, or any runtime path on `main`.
- **Phase 4 safety foundation:** Closed (governance-only) per P4-08. `src/gmc_rebuild/runtime/` contains the composed `RuntimeShell` boundary, the immutable `SafetyVerdict`, the five `BLOCKER_*` constants, the immutable `OperatorSafetyView`, and the pure `format_safety_verdict` function. Inert: no `__main__`, no daemon, no scheduler, no network, no broker SDK.
- **Phase 5 local simulation boundary:** The P5-01..P5-07 sequence is merged on `main`. `src/gmc_rebuild/simulation/` contains the closed `SimulationLane` (`LOCAL_ONLY`), the immutable `SimulatedIntent` placeholder, the eight-field frozen `SimulatedOrderIntent` (closed `SimulatedOrderSide` = `BUY` / `SELL`, closed `SimulatedOrderType` = `MARKET` / `LIMIT`), the `SimulationBoundary` class with `propose` (P5-01) and `propose_order` (P5-02), and the `SimulationBoundaryError` exception. The P5-03..P5-07 tripwire suite covers simulated-order-intent invariants, composed safety-foundation × simulation integration, operator-view × composed-safety integration, `propose` ↔ `propose_order` symmetry, and operator-view determinism / idempotence.
- **OPS series:** OPS-01 project resilience checkpoint, OPS-02 Backblaze restore drill, OPS-03 X10 Pro panic-history investigation, OPS-04 memory-pressure baseline, OPS-04B baseline measurement record, and OPS-06 backup-monitoring plan are all merged. `RECOVERY.md` carries the rules and thresholds; the plan is rules-only and the periodic execution remains an operator-side action.
- **GOV-01 governance reconciliation:** Merged via PR #106 at `4df8074`. Synchronizes the `MASTER_STATUS.md` §8 step 4a `allowed_p2_infra` bash gate to the ten entries that match the actual authorized tree.
- **GOV-02 execution-environment workflow correction:** Merged via PR #132 at `94d30bf` (reconciled via PR #134 at `fb13994`). Local Claude Code / Claude Max is the default execution environment for `gmc-rebuild` repo edits; Perplexity Computer's `AI_WORKFLOW.md` §1.2 Supervisor / Verifier / Status Keeper role is preserved unchanged; Perplexity-managed codebase subagents must not perform repo edits absent Kevin's explicit written authorization for the specific packet.
- **Roadmap and project map:** [`docs/GMC_PROJECT_MAP.md`](../docs/GMC_PROJECT_MAP.md) (the strategic compass) and [`docs/FOUNDATION_TO_DRY_RUN_ROADMAP.md`](../docs/FOUNDATION_TO_DRY_RUN_ROADMAP.md) (the 30-to-60-day operating bridge) are merged on `main` (commits `e62e27c` and `a13cdf9` respectively). The roadmap names Layer 2 (the local dry-run trading engine skeleton) as the next major product layer and lists six suggested next Claude Code work packets in §8 — two documentation-only (Packets 1 and 2) and four implementation-shaped (Packets 3 through 6).
- **Foundation-complete confirmation:** [`docs/decisions/2026-05-19_foundation_complete_confirmation.md`](../docs/decisions/2026-05-19_foundation_complete_confirmation.md) (commit `a92568e`) walked the roadmap §3 "Definition of Foundation Complete" checklist item by item against the actual repo state and identified two remaining gaps: a wording gap in the roadmap §3 enumeration (closed by Packet 1-FU-A at commit `ce010cb`) and a pre-commit cleanliness gap (closed by Packet 1-FU-B at commit `8dc7a2d`). With both follow-ups merged, every item on the roadmap §3 checklist is now satisfied and verifiable from the repository.
- **§8 step 4a `allowed_p2_infra` allowlist:** Exactly ten entries — `src`, `src/gmc_rebuild/config`, `src/gmc_rebuild/time`, `src/gmc_rebuild/logging`, `src/gmc_rebuild/risk`, `src/gmc_rebuild/heartbeat`, `src/gmc_rebuild/kill_switch`, `src/gmc_rebuild/reconciliation`, `src/gmc_rebuild/runtime`, `src/gmc_rebuild/simulation`. This plan preserves the allowlist unchanged. Any future P6 PR that introduces a new directory must add it to the allowlist in the same PR that introduces the directory, per the standing rule in `MASTER_STATUS.md` §8 step 4b, and must be authorized in writing for the specific directory by Kevin.
- **Tests and pre-commit on the current `main` head:** The foundation-complete confirmation report (commit `a92568e`) identified a pre-commit cleanliness blocker — 29 ruff errors in two test files, two files that `ruff format` would reformat, and a pre-commit `pytest` hook that failed with `Executable pytest not found`. Tests themselves were already passing 411/411 at that point. Packet 1-FU-B (commit `8dc7a2d`) closed that blocker by resolving the 29 ruff errors in the two test files, applying `ruff format`, and changing the pre-commit `pytest` hook entry from `pytest` to `.venv/bin/pytest`. Current `main` now has `.venv/bin/python -m pytest -q` passing 411/411 deterministically and `.venv/bin/pre-commit run --all-files` exiting 0 with every hook passing and no second-pass `files were modified by this hook` side effects.
- **Always-forbidden categories per `MASTER_STATUS.md` §6:** Trading strategy code, broker execution code, live or paper trading wired to a real broker, runtime daemons affecting accounts, real market data ingestion, order placement, real secrets — remain forbidden in all modes. None is reintroduced by this plan.
- **Workflow in effect (per GOV-02):** local Claude Code / Claude Max is the default builder for `gmc-rebuild` repo edits → Perplexity Computer verifies in the `AI_WORKFLOW.md` §1.2 Supervisor / Verifier / Status Keeper role → Kevin approves → Backup AI reviews adversarially at gates and high-risk decisions (Mode A) per `AI_WORKFLOW.md` §1, §2, §4 and authors monitoring packet text under Mode B per ADR-008 (and ADR-009 once runtime exists on `main` per ADR-009 D7's bootstrap-avoidance clause). Perplexity-managed codebase subagents that consume Perplexity credits must not perform repo edits absent Kevin's explicit written authorization for the specific packet. Where prior governance prose refers to "Codex" as the builder, that role is now filled by local Claude Code / Claude Max under GOV-02 unless Kevin explicitly authorizes otherwise for a specific packet.

Until Kevin records a separate written authorization for any successor P6 task, the only allowed work beyond routine maintenance is interpreting this plan, verifying existing state, and preparing decision packages. No successor P6 task is opened by this document.

---

## 2. Phase 6 Objective (Planning Level Only)

This section restates the Phase 6 objective at the **planning level** only. Naming an objective here does not authorize implementation. Each successor Phase 6 task requires its own separate written authorization from Kevin.

Phase 6 is conceived, **for planning purposes only**, as the **local dry-run trading engine skeleton phase** that sits on top of the closed P4-08 safety foundation and the merged P5-01..P5-07 simulation surface. Its planning-level purpose is to build, at a documentation level first and then at narrowly scoped implementation level under separate written authorization, the first observable trading-loop-shaped capabilities of the gmc-rebuild project: a typed signal intake boundary, eligibility checks, a composed position / risk decision producing a structured "would-trade" or "would-skip" outcome with reasons, an extended simulated order intent surface, a deterministic in-memory simulated portfolio state, a richer deterministic operator view, and a deterministic daily-report record. Each capability is local-only, in-memory, deterministic, exercised only from the test suite, and reachable only through the existing `SimulationBoundary` and `SafetyVerdict` gating.

In planning scope only (§3 below defines what may be discussed; §4 names the candidate task sequence; **none of this is implementation authorization**):

- Bounded, local-only, sandboxed, deterministic in-memory capabilities under `src/gmc_rebuild/` that compose the already-merged P2 / P3 / P4 / P5 public surfaces into the trading-loop-shaped operations named in [`docs/FOUNDATION_TO_DRY_RUN_ROADMAP.md`](../docs/FOUNDATION_TO_DRY_RUN_ROADMAP.md) §4. Each capability is reachable only from the test suite or from an explicit, local, non-broker entry point — no `__main__`, no daemon, no scheduler.
- Tripwire-only test coverage that pins invariants, idempotence, and composed-pipeline behavior for each new capability, modeled on the merged P5-03 / P5-04 / P5-05 / P5-06 / P5-07 precedents.
- Per-PR proof-bundle expectations that align with `plan/phase5_entry_plan.md` §6 and `AI_WORKFLOW.md` §3.
- ADR follow-ups that any future P6-0N decision would require — at minimum any ADR-009 implications that surface at the time of authorization, with implications for ADR-001 (secrets management, which stays untouched), ADR-002 (kill switch), ADR-003 (reconciliation), ADR-005 (heartbeat), ADR-006 (deployment logs), and ADR-007 (minimal CI).

**Out of planning scope**, and forbidden until a successor P6 task is opened in writing by Kevin (and forbidden at the always-forbidden category level per `MASTER_STATUS.md` §6 independent of phase):

- Trading strategy code (signals, scanners, models, portfolio rules, backtests against real history). A typed signal-intake boundary that accepts a structured intent object is **not** strategy code; an algorithm that decides what to trade **is** strategy code.
- Broker execution code (order placement, position management, broker SDK integration, broker authentication).
- Paper-trading wired to a real broker (paper-broker connector, paper-account identifier, paper-API surface, paper-trading execution loop).
- Live-trading wired to a real broker (live-broker connector, live-account identifier, live-API surface, live-trading execution loop).
- Runtime daemons, schedulers, long-running services, background workers, operator-availability heartbeats wired to a real operator, or anything with a `__main__` entry point that touches accounts, markets, or money.
- Runtime activation of any merged Phase 3 fixture — `InMemoryHeartbeat`, `InMemoryKillSwitch`, or `InMemoryReconciliation` — from a `__main__`, a daemon, a scheduler, a re-export in `src/gmc_rebuild/__init__.py`, or any other runtime path.
- Market-data ingestion code, real data pipelines, committed datasets, real or historical feeds.
- Real secrets, real credentials, real account identifiers, real broker / venue identifiers, real endpoints.
- Any concrete implementation of `KillSwitchProtocol`, `ReconciliationProtocol`, or `HeartbeatProtocol` that talks to a broker, network, filesystem outside the test sandbox, or scheduler.
- Persistence to disk: SQLite, DuckDB, Postgres, on-disk reconciliation snapshot, on-disk portfolio snapshot, on-disk heartbeat state, log sink, or any file artifact written by runtime code under this plan.
- Network: `socket`, `urllib`, `requests`, `http`, `ssl`, `smtplib`, `ftplib`, or any outbound or inbound network code.
- Any change that loosens `.gitignore`, `.pre-commit-config.yaml`, mypy strict mode, `detect-secrets`, the `MASTER_STATUS.md` §8 step 4 always-forbidden scan, the §8 step 4a per-PR Phase 2 / Phase 3 / Phase 4 / Phase 5 / Phase 6 infrastructure allowlist scan, or the §8 step 4c recursive forbidden-token scan.
- Any new git tag, GitHub release, or version bump.

This split is intentional and mirrors the line `MASTER_STATUS.md` §6 / §7 already draws and that `plan/phase4_entry_plan.md` §2 and `plan/phase5_entry_plan.md` §2 restated for prior phases. Phase 6 planning does not move that line; it discusses what would sit underneath it.

---

## 3. Allowed Planning Topics

While Phase 6 entry planning is in this opened-but-unscoped state, the builder may discuss and write planning artifacts on the following topics. Planning artifacts are documents, not code, and must be reviewable as documents.

1. **Current post-foundation-complete state in prose.** §1 of this plan is the canonical planning-level statement.
2. **Any unmerged P6-0N task named only as future / not authorized.** Naming a task in §4 of this plan does **not** authorize it; the shape of each task remains a decision Kevin must make in writing at the time of authorization. The plan must not pre-commit any P6-0N shape (no specific test file, no specific module beyond a candidate directory name and capability description, no specific field, no specific method, no specific class, no specific enum member). (P6-01, P6-02, P6-03 planning, P6-03 implementation, and P6-04 implementation (Direction A) have since merged on `main`; §4 entries below reflect their merged status. The P6-05 planning packet and the P6-05 implementation authorization have also merged, so P6-05 implementation is authorized but not yet implemented — no P6-05 `src/**` or `tests/**` exists on `main`, and the authorization of record is `governance/authorizations/2026-05-22_p6-05.md`. P6-06 / P6-07 remain unmerged and continue to be named only as future / not authorized.)
3. **Phase 6 entry criteria.** What must be true before any future P6-0N implementation PR could open. §5 of this plan is the canonical planning-level statement.
4. **Per-PR proof-bundle expectations for any future P6-0N PR.** Restated from `AI_WORKFLOW.md` §3 and `plan/phase5_entry_plan.md` §6. §6 of this plan is the canonical planning-level statement.
5. **Rollback and stop conditions.** Restated for Phase 6 from `plan/phase5_entry_plan.md` §8. §8 of this plan is the canonical planning-level statement.
6. **Phase-boundary enforcement.** How any future P6-0N PR would prove it did not cross into broker execution, paper-trading wired to a real broker, live-trading wired to a real broker, real market data ingestion, real order routing, real strategy logic, real scheduler / daemon, real persistence, real deployment, real env-var loading, real secrets, real network, allowlist expansion beyond what its own authorization names, quality-gate relaxation, X10 Layer 5 promotion, backup-monitoring automation, or DR drill execution.
7. **ADR follow-ups.** Listed in §9 of this plan at planning level only.

Any planning topic that does not fit the list above must be raised with Kevin before a document is written, per `AI_WORKFLOW.md` §6 rule 7 ("No phase drift").

---

## 4. Candidate Future Phase 6 Task Sequence (Future / Not Authorized)

This section enumerates the candidate Phase 6 task sequence at the **planning level only**. Naming a task in this section does **not** authorize it. The shape of each task remains a decision Kevin must make in writing at the time of the relevant authorization, in a separate authorization artifact under `governance/authorizations/`, and that future authorization is free to replace any element of the candidate shape recorded here.

Per the standing sequencing rules (mirroring `plan/phase4_entry_plan.md` §4 and `plan/phase5_entry_plan.md` §4):

- Tasks land one at a time. PR P6-(N+1) is not opened until PR P6-N is accepted by Kevin.
- Each PR is small enough that the diff and the proof bundle (§6) fit a single review.
- Any PR that grows beyond its stated scope during implementation is split or stopped per `AI_WORKFLOW.md` §6 rule 6 / rule 7.
- Each implementation packet may be preceded by a separate planning / enumeration packet, mirroring the merged P5-06-planning / P5-07-planning pattern, where Kevin wants the candidate shape recorded before opening implementation.

1. **PR P6-01 — first Phase 6 implementation task — merged on `main` as of 2026-05-19 at commit `d52551a`.**
   - **Objective (planning level):** Introduce a typed signal-intake boundary as the dry-run engine's first observable trading-loop-shaped capability. A signal is a structured intent object describing a candidate trade idea — not an algorithm that decides what to trade.
   - **Touched directories (candidate):** New submodule under `src/gmc_rebuild/signal_intake/` with a single `__init__.py` and a single internal module. New tests directory under `tests/signal_intake/` with one new test file. No modification of any existing `src/**` file. No modification of any existing test file.
   - **Docs-only or implementation:** Implementation. A separate planning / enumeration packet may precede it under Kevin's separate written authorization.
   - **Expected tests (planning level):** Determinism, frozen-dataclass / `__slots__` shape, exact-field-set invariants, equality / hashability, validation behavior at field boundaries, inertness self-check (no forbidden runtime imports; every import from an authorized prefix).
   - **§8 step 4a allowlist implication:** Adds exactly one new entry `src/gmc_rebuild/signal_intake` to the `allowed_p2_infra` allowlist in the same PR that introduces the directory, per `MASTER_STATUS.md` §8 step 4b.
   - **Explicit non-authorizations:** Does not authorize any signal-generation algorithm, any scanner, any market-data ingestion, any broker integration, any runtime activation, any scheduler, any persistence, any network call, any env-var read, any concrete protocol implementation, any expansion of any merged simulation surface, any change to `propose` / `propose_order` semantics, any ops execution work, or any later P6-0N task.

2. **PR P6-02 — second Phase 6 implementation task — merged on `main` as of 2026-05-19 at commit `4785e24`.**
   - **Objective (planning level):** Introduce pure-function eligibility checks that accept the P6-01 signal-intake dataclass plus a project-config slice and return a structured eligibility decision (`ELIGIBLE` / `INELIGIBLE` with reasons). The reasons are a closed enum or frozen tuple of named codes.
   - **Touched directories (candidate):** New submodule under `src/gmc_rebuild/eligibility/`. New tests directory under `tests/eligibility/`.
   - **Docs-only or implementation:** Implementation.
   - **Expected tests (planning level):** Pure-function determinism, closed-set reason enumeration, exhaustive coverage of named reason codes, non-mutation of inputs, frozen / `__slots__` shape on any introduced dataclass, inertness self-check.
   - **§8 step 4a allowlist implication:** Adds exactly one new entry `src/gmc_rebuild/eligibility` to the allowlist in the same PR.
   - **Explicit non-authorizations:** Does not authorize any I/O, any time dependence beyond the existing `gmc_rebuild.time` UTC utility, any network call, any persistence, any broker integration, any runtime activation, any scheduler, or any later P6-0N task. No real symbol allow / deny list backed by external data lands in this packet; the eligibility decision operates on the supplied dataclass alone.

3. **PR P6-03 — third Phase 6 implementation task — merged on `main` as of 2026-05-20 via PR #146 at `8d98a41`, with sibling Mode B monitoring PR #147 merged first at `87c95cd` per ADR-008 §D5; the prior planning / enumeration packet `governance/authorizations/2026-05-19_p6-03-planning.md` merged on `main` as of 2026-05-19 via PR #144 at `583f457`, with sibling Mode B PR #145 merged first at `0727fbd`; the implementation authorization commit on main at `245a6fd` preceded PR #146.**
   - **Objective (planning level):** Introduce a composed position / risk decision module that composes the P6-01 signal-intake output, the P6-02 eligibility-decision output, and the existing in-memory Protocol fakes (`InMemoryHeartbeat`, `InMemoryKillSwitch`, `InMemoryReconciliation`) into a structured "would-trade" or "would-skip" decision with reasons. The composition reuses the merged P4-06 `RuntimeShell` / `SafetyVerdict` gating without re-implementing it.
   - **Touched directories (candidate):** New submodule under `src/gmc_rebuild/decision/` (or similarly named). New tests directory under `tests/decision/` including composed edge-case tests mirroring the P4-04 pattern.
   - **Docs-only or implementation:** Implementation. The P6-03 planning / enumeration packet at `governance/authorizations/2026-05-19_p6-03-planning.md` was the planning-only precursor and did **not** itself authorize implementation; the separate P6-03 implementation authorization at `governance/authorizations/2026-05-20_p6-03.md` (on `main` at `245a6fd`) is the implementation-of-record.
   - **Expected tests (planning level):** Determinism, identity-return on the would-trade path, non-mutation across repeated calls, biconditional between `would_trade` and (`eligibility == ELIGIBLE` and `verdict.clear`), per-blocker propagation for each of the five `BLOCKER_*` codes, ineligibility surfacing, composed edge cases, inertness self-check.
   - **§8 step 4a allowlist implication:** Adds exactly one new entry `src/gmc_rebuild/decision` to the allowlist in the same PR.
   - **Explicit non-authorizations:** Does not authorize any runtime activation, any broker integration, any order placement, any persistence, any scheduler, any network call. Does not modify `SafetyVerdict.clear` semantics or the `BLOCKER_*` set. Does not expand the runtime surface beyond composition of already-authorized submodules. Does not pre-authorize P6-04 or any later P6-0N task.
   - **Planning packet cross-reference:** `governance/authorizations/2026-05-19_p6-03-planning.md` §3 records the planning-level candidate shape (intended module/package location, typed input boundary from P6-01 / P6-02, typed output boundary, reason taxonomy, deterministic pure-function contract, safety / non-goals, proposed test matrix and invariants, integration expectations, acceptance criteria, and validation commands). The planning packet was **planning only** and did not pre-commit any element of the subsequent P6-03 implementation authorization; Kevin's merged P6-03 implementation authorization at `governance/authorizations/2026-05-20_p6-03.md` (on `main` at `245a6fd`) was free to replace any element of that candidate shape.

4. **PR P6-04 — fourth Phase 6 implementation task (Direction A) — merged on `main` as of 2026-05-21 via PR #158 at `cea8553`, with sibling Mode B monitoring PR #159 merged first at `1c2d63a` per ADR-008 §D5.**
   - **Implemented direction:** Direction A was selected and authorized per `governance/authorizations/2026-05-21_p6-04.md`: extend the existing `SimulatedOrderIntent` surface in place inside `src/gmc_rebuild/simulation/` with a closed `SimulatedOrderTimeInForce` enum carried as a ninth `SimulatedOrderIntent` field (defaulting to `DAY`) and a deterministic `derive_simulated_order_intent_id` identity helper. Direction (b) (a separately named composed record class in a new sibling subpackage) was **not** selected and remains future / not authorized. The two planning-level candidate directions are preserved below as the historical planning record.
   - **Objective (planning level):** Extend the existing `SimulatedOrderIntent` model into a richer dry-run order intent surface. Two planning-level candidate directions: (a) add deterministic intent-identifier generation and a time-in-force closed enum on the existing `SimulatedOrderIntent`; or (b) add a separately named record class that composes `SimulatedOrderIntent` with the P6-03 decision output to produce a "decided order intent." The chosen direction was itself a decision Kevin made in writing at the time of authorization (Direction A); the authorization was free to replace both candidates with a third shape.
   - **Touched directories (candidate):** Extends `src/gmc_rebuild/simulation/` within its existing §8 step 4a allowlist entry, OR introduces a new submodule under `src/gmc_rebuild/` named in the authorization. New tests under `tests/simulation/` or a new `tests/<name>/` directory matching the authorized choice.
   - **Docs-only or implementation:** Implementation.
   - **Expected tests (planning level):** Determinism of intent-identifier generation, frozen / `__slots__` shape, closed-enum invariants on any new enum, equality / hashability, non-mutation invariants, idempotence of the identifier-generation function, inertness self-check.
   - **§8 step 4a allowlist implication:** Either preserves the allowlist at its current state (direction (a), extends inside existing entry) or adds exactly one new entry in the same PR (direction (b)).
   - **Explicit non-authorizations:** Does not authorize any broker SDK, any order placement, any real account identifier, any real venue identifier, any network call, any persistence, any runtime activation, any scheduler, any change to `propose` / `propose_order` identity-return semantics, or any later P6-0N task.

5. **PR P6-05 — fifth Phase 6 implementation task — implementation authorized (not yet implemented) per `governance/authorizations/2026-05-22_p6-05.md`, merged via PR #164 at `cb4574e` with sibling Mode B monitoring PR #165 merged first at `005b6ca` per ADR-008 §D5; the prior planning / enumeration packet `governance/authorizations/2026-05-22_p6-05-planning.md` merged via PR #162 at `5d1c743`, with sibling Mode B PR #163 merged first at `03e71fc`. No P6-05 `src/**` or `tests/**` exists on `main`; the implementation is a separate future PR that must conform to the authorization.**
   - **Authorized shape (resolved by the implementation authorization; not yet implemented):** The merged P6-05 implementation authorization resolves the open choices the planning packet left open: (1) **state model** — a frozen / value-typed replaceable snapshot (an event-sourced / append-only model is **not** authorized); (2) **idempotence** — idempotent application keyed on the deterministic P6-04 simulated order intent ID, so re-applying the same accepted intent ID does not double-apply position changes (the snapshot carries an applied-intent-ID dedup structure); (3) **directory** — `src/gmc_rebuild/portfolio_state/` with tests under `tests/portfolio_state/` (the candidate `src/gmc_rebuild/portfolio/` is **not** authorized); (4) **closed inputs** — the P6-03 `PositionDecision` acceptance surface, the P6-04 `SimulatedOrderIntent`, the deterministic intent ID, and optional fixture-only fill information (value-typed, not market data); (5) **closed outputs** — an in-memory value object (positions keyed by symbol, deterministic quantity changes, applied-intent-ID dedup set; no cash ledger unless strictly local / value-typed; no P&L, broker reconciliation, balances, live account, valuation, or external state).
   - **Objective (planning level):** Introduce a deterministic in-memory simulated portfolio state that applies accepted intents (the output of P6-03 / P6-04) to a position book under explicit, deterministic, fixture-only fill assumptions. The portfolio is a value-typed, frozen / replaceable record; there is no real market data and no broker confirmation.
   - **Touched directories (authorized):** New submodule under `src/gmc_rebuild/portfolio_state/`. New tests directory under `tests/portfolio_state/`.
   - **Docs-only or implementation:** Implementation (authorized, not yet performed).
   - **Expected tests (planning level):** Determinism of application, non-mutation of inputs, identity / equality semantics on the returned snapshot, idempotent duplicate-intent handling keyed on the deterministic intent ID, composed-pipeline integration with P6-01 / P6-02 / P6-03 / P6-04, inertness self-check.
   - **§8 step 4a allowlist implication:** The future implementation PR adds exactly one new entry `src/gmc_rebuild/portfolio_state` to the allowlist in the same PR that introduces the directory. Note that `portfolio_state` tokenizes to `portfolio` + `state` and so trips the forbidden `portfolio` token in the §8 step 4 / step 4c scans — exactly as the merged `src/gmc_rebuild/signal_intake` trips the forbidden `signal` token — so the implementation PR must add the step 4a allowlist entry and document the expected token flag as authorized per the P6-01 `signal_intake` precedent, without weakening the forbidden set. This reconciliation packet does **not** add the allowlist entry (no directory exists yet).
   - **Explicit non-authorizations:** Does not authorize any real position book, any real account identifier, any broker, any market data, any persistence, any filesystem snapshot, any network call, any scheduler, any daemon, any runtime activation, any `__main__`, any env-var read, any secrets, any tag / release, any P6-06+ work, or any P&L / cash ledger / valuation / order execution / fill engine / broker reconciliation / account sync. The portfolio remains purely in-memory and value-typed; no on-disk snapshot lands in this packet.

6. **PR P6-06 — candidate sixth Phase 6 implementation task (future / not authorized).**
   - **Objective (planning level):** Introduce a deterministic daily-report record summarizing, for a given simulated cycle, the intents generated, decisions made, simulated fills applied, reconciliation status, and any tripped invariants. The report is written via the existing `gmc_rebuild.logging.audit_event` helper to the standard logger only — no external sink, no file artifact, no scheduler.
   - **Touched directories (candidate):** Extends `src/gmc_rebuild/logging/` within its existing §8 step 4a allowlist entry, OR introduces a new submodule named in the authorization. New tests under `tests/logging/` or a new `tests/<name>/` directory matching the authorized choice.
   - **Docs-only or implementation:** Implementation.
   - **Expected tests (planning level):** Determinism of the report record for fixed inputs, frozen / `__slots__` shape, exact-field-set invariants, idempotence under repeated rendering, non-mutation of inputs, exact match against the `audit_event` structured-record contract, inertness self-check.
   - **§8 step 4a allowlist implication:** Either preserves the allowlist (extends inside existing `logging/` entry) or adds exactly one new entry in the same PR.
   - **Explicit non-authorizations:** Does not authorize any external sink, any file artifact, any `__main__` report-generation entry point, any scheduler, any persistence beyond what the standard logger does in process, any runtime activation, any network call.

7. **PR P6-07 — candidate seventh Phase 6 implementation task (future / not authorized).**
   - **Objective (planning level):** Consolidate the failure-handling and exception-typing discipline across the Phase 6 surface introduced by P6-01..P6-06. Tripwire-only tests modeled on the P5-03 / P5-04 / P5-05 / P5-06 / P5-07 precedent that pin: explicit named exception types at each layer boundary, no swallowed exceptions, structured `audit_event` records for every refusal / skip / kill-switch trip / reconciliation mismatch / unhandled error.
   - **Touched directories (candidate):** New test file (or files) under the existing `tests/` tree. No new `src/**` directory. No `src/**` modification.
   - **Docs-only or implementation:** Tripwire-only test packet, no production behavior change.
   - **Expected tests (planning level):** Closed-set exception-type invariants, structured-record contract assertions against `audit_event` output, no-swallow invariants, composed-pipeline coverage, inertness self-check.
   - **§8 step 4a allowlist implication:** Preserves the allowlist unchanged.
   - **Explicit non-authorizations:** Does not authorize any new production behaviour. Does not authorize any change to existing exception classes. Does not authorize any runtime activation, any broker integration, any ops execution work, or any later P6-0N task.

Further candidate tasks beyond P6-07 (P6-08, P6-09, …) are deliberately **not enumerated** in this plan. The shape of any successor to P6-07 — including any further dry-run engine work, any first connection of any simulation surface to a real broker (which is forbidden at the always-forbidden category level per `MASTER_STATUS.md` §6 independent of phase), any first connection to a real market-data feed (likewise forbidden), or any Phase 7 / Layer 4 paper-readiness work (which would require its own separate written authorization and a new phase plan entirely) — is itself a decision that Kevin must make in writing at the time of the relevant authorization. Any later enumeration of P6-08 / P6-09 / … must itself be authorized as a separate documentation-only update to this plan and must not authorize implementation.

**Roadmap §8 mapping.** [`docs/FOUNDATION_TO_DRY_RUN_ROADMAP.md`](../docs/FOUNDATION_TO_DRY_RUN_ROADMAP.md) §8 named Packets 3 through 6 as the four implementation-shaped packets following the two documentation-only packets (Packets 1 and 2). The candidate Phase 6 sequence above maps onto those roadmap packets as follows: P6-01 corresponds to Roadmap Packet 3 (signal-intake typed boundary); P6-02 corresponds to Roadmap Packet 4 (eligibility-check pure functions); P6-03 corresponds to Roadmap Packet 5 (position / risk decision composer); P6-04 corresponds to Roadmap Packet 6 (simulated-order-intent extension); P6-05, P6-06, and P6-07 are additional planning-level candidates beyond the roadmap's named six packets, recorded here so that the Phase 6 capability surface enumerated in roadmap §4 (Layer 2) is fully covered at the planning level.

**§8 step 4a allowlist note.** The `allowed_p2_infra` allowlist on `main` after GOV-01 contains exactly ten entries. This plan preserves the allowlist unchanged. Any future P6 PR that introduces a new directory must add it to the allowlist in the same PR that introduces the directory, per `MASTER_STATUS.md` §8 step 4b.

---

## 5. Phase 6 Entry Criteria (Planning Level Only)

The criteria below govern any successor Phase 6 task by analogy to `plan/phase5_entry_plan.md` §5. None of these criteria is satisfied by this plan alone; each successor P6-0N PR must independently satisfy the applicable criteria and be separately authorized by Kevin in writing.

1. The accepted Phase 1 baseline is `1f101fc` (per `MASTER_STATUS.md` §3) and `main` is a descendant of it (`MASTER_STATUS.md` §8 step 3 returns OK). **Satisfied as of every commit on `main`.**
2. Phase 2 is formally closed (governance-only) per `governance/authorizations/2026-05-12_phase-2-closure.md`. **Satisfied as of 2026-05-12.**
3. Phase 3 is formally closed (governance-only) per `governance/authorizations/2026-05-14_phase-3-closure.md`. **Satisfied as of 2026-05-14.**
4. Phase 4 safety foundation closure is recorded by P4-08 per `governance/authorizations/2026-05-16_p4-08.md`. **Satisfied as of 2026-05-16.**
5. The merged P5-01..P5-07 sequence is on `main`. **Satisfied as of 2026-05-18.**
6. The foundation-complete confirmation report ([`docs/decisions/2026-05-19_foundation_complete_confirmation.md`](../docs/decisions/2026-05-19_foundation_complete_confirmation.md)) is merged on `main`. **Satisfied as of 2026-05-19 (commit `a92568e`).**
7. The roadmap-§3 wording reconciliation (Packet 1-FU-A) is merged on `main`. **Satisfied as of 2026-05-19 (commit `ce010cb`).**
8. The pre-commit cleanliness restoration (Packet 1-FU-B) is merged on `main`, with `.venv/bin/pre-commit run --all-files` exiting 0 and `.venv/bin/python -m pytest -q` passing 411/411 deterministically. **Satisfied as of 2026-05-19 (commit `8dc7a2d`).**
9. This Phase 6 Entry Plan (`plan/phase6_entry_plan.md`) has been merged on `main` as planning-only documentation. (This document targets that merge; merging this document does not by itself open any successor P6 task.)
10. Kevin has explicitly authorized each successor P6 task in writing — commit message, PR comment, or governance entry, not a chat message — per `MASTER_STATUS.md` §7.3 and recorded in a sibling artifact under `governance/authorizations/` per `AI_WORKFLOW.md` §7. Each successor P6 PR's scope must also be named in the authorization, per the §7.4 pattern that `plan/phase5_entry_plan.md` §5 applied to P5-0N.
11. Each successor P6 PR has been reviewed in **Mode A** by the Backup AI per `AI_WORKFLOW.md` §4(2) as applicable. The Mode A critique is delivered as PR-review text and is **not** committed to the repository (per `AI_WORKFLOW.md` §6 rule 5).
12. A **Mode B** monitoring packet has been authored by the Backup AI per ADR-008 §D3 (or ADR-009 D3 once in force per ADR-009 D7's bootstrap-avoidance clause) and committed by the default builder (local Claude Code / Claude Max under GOV-02) under `monitoring/daily/` per ADR-008 §D4 (or ADR-009 D4) for the active workday on which each successor P6 PR is open / merged.
13. Each successor P6 implementation PR is infrastructure-only at the planning-level definition of §2 above (sandboxed, local-only, no broker, no paper-trading or live-trading wired to a real broker, no market data, no order placement, no scheduler / daemon, no real secrets, no runtime activation of any merged Phase 3 fixture, no expansion of any merged simulation surface beyond what its own authorization names, no order semantics change beyond what its own authorization names, no ops execution work).

If any criterion fails, the relevant successor P6 task stays closed. Phase 5 closure stays recorded. Phase 4 safety foundation closure stays recorded. Phase 3 stays formally closed. Phase 2 stays formally closed. Routine governance maintenance under `MASTER_STATUS.md` §9 continues.

---

## 6. Required Proof For Each Future Phase 6 PR

Each future Phase 6 PR must include the proof bundle defined in `AI_WORKFLOW.md` §3 and restated in `plan/phase5_entry_plan.md` §6. Restated here for Phase 6 scope.

1. **Git state.**
   - `git status` showing a clean tree after commit.
   - `git log --oneline -10` showing the head commit and recent history.
   - `git rev-parse HEAD` showing the exact commit hash under review.
   - `git diff <baseline>..HEAD` against the accepted Phase 1 baseline `1f101fc` (or a later accepted baseline if one has been recorded in `MASTER_STATUS.md` §3 by that time).
2. **Tests and pre-commit.**
   - Full output of `.venv/bin/pre-commit run --all-files` (must pass with no second-pass modifications, or every failure documented and resolved before merge).
   - Full output of `.venv/bin/python -m pytest -q` (must pass; the existing 411 baseline must be preserved unless the PR adds tests, in which case the new count must be documented and all tests must pass).
3. **Phase-boundary checklist.** For each Phase 6 PR, the verification report explicitly confirms:
   - No new top-level directories outside the documented set.
   - No new modules under `strategy/`, `signals/`, `broker/`, `execution/`, `live/`, `daemons/`, `data/`, `market_data/`, `orders/`, `secrets/`, or any name on the `MASTER_STATUS.md` §8 step 4 always-forbidden list, anywhere in the tree (the §8 step 4c recursive forbidden-token scan returns OK / subshell exit `0`). A `signal_intake/` directory is on the candidate list at §4 above; it is not a forbidden name because `signal_intake` (a typed boundary that accepts a structured object) is not `signals` (an algorithm that generates them). The authorization for P6-01 must name the directory by exact path.
   - No new long-running entry points (`if __name__ == "__main__"` services, scheduler configs, background workers, daemons).
   - No new secrets, real credentials, real account identifiers, real broker / venue identifiers, real endpoints, or generated data files.
   - No new broker SDK dependency, no new market-data SDK dependency, no new scheduler or background-job dependency.
   - No runtime activation of any merged Phase 3 fixture — `InMemoryHeartbeat`, `InMemoryKillSwitch`, or `InMemoryReconciliation` — from a `__main__`, a daemon, a scheduler, a re-export in `src/gmc_rebuild/__init__.py`, or any other runtime path, unless the specific activation is named in Kevin's separate written authorization for the PR and is itself subject to Mode A per `AI_WORKFLOW.md` §4(2).
   - No simulation expansion beyond what the PR's own authorization names. No order semantics change beyond what the PR's own authorization names. No ops execution work beyond what the PR's own authorization names.
   - No new concrete implementation of `KillSwitchProtocol` / `ReconciliationProtocol` / `HeartbeatProtocol` that talks to a broker, network, filesystem outside the test sandbox, or scheduler.
   - No relaxation of `.gitignore`, `.pre-commit-config.yaml`, mypy strict mode, `detect-secrets`, `.secrets.baseline`, the `MASTER_STATUS.md` §8 step 4 always-forbidden scan, the §8 step 4a per-PR infrastructure allowlist scan, or the §8 step 4c recursive forbidden-token scan.
   - Any new authorized directory is added to the `MASTER_STATUS.md` §8 step 4a allowlist in the same PR that introduces the directory, per the standing rule in §8 step 4b.
4. **File-specific evidence.** Per `AI_WORKFLOW.md` §3.4, each changed file is named and the verifier states what was verified for it.
5. **Docs updated.** Any change to interfaces or conventions is reflected in the relevant document (ADR update, new ADR, or `MASTER_STATUS.md` entry) in the same PR — no orphaned code without a governance hook.
6. **ADR-009 cadence status.** The verification report names whether ADR-008 §D3 / §D5 (governance-phase cadence) or ADR-009 D3 / D5 (runtime-phase cadence) governs the PR per ADR-009 D7's bootstrap-avoidance clause. Until runtime exists on `main`, ADR-008 §D3 / §D5 continue to govern. The candidate Phase 6 sequence in §4 above introduces no runtime, so ADR-008 governance-phase cadence is expected to remain in force across the sequence; if any future authorization changes that, the verification report must say so.
7. **Mode A / Mode B status.** The verification report names whether `AI_WORKFLOW.md` §4 Mode A and ADR-008 §D3 (or ADR-009 D3) Mode B apply to the PR, and where each artifact lives.
8. **Canonical-doc staleness check.** Per `MASTER_STATUS.md` §8 step 8, the verification report confirms that the canonical docs do not contain stale `**pending merge**` language for already-merged packets.

A Phase 6 PR that does not carry this bundle is not eligible for Kevin's review.

---

## 7. Review Protocol

Standard review per `AI_WORKFLOW.md` §2:

1. Kevin states the task in writing.
2. Perplexity Computer confirms the task fits the current phase and records it.
3. The default builder (local Claude Code / Claude Max under GOV-02) builds the smallest change on a feature branch and opens a draft PR.
4. Perplexity Computer verifies using the proof bundle (§6) and returns findings if anything fails.
5. The default builder revises without expanding scope.
6. Kevin decides.

Per the GOV-02 execution-environment workflow rule (merged via PR #132 / reconciled via PR #134), local Claude Code / Claude Max is the default execution environment for `gmc-rebuild` repo edits. Perplexity-managed codebase subagents that consume Perplexity credits must not perform repo edits absent Kevin's explicit written authorization for the specific packet; Perplexity Computer's `AI_WORKFLOW.md` §1.2 Supervisor / Verifier / Status Keeper role and read-only `gh` / `git` metadata-check role are preserved unchanged.

**Mode A adversarial backup review** per `AI_WORKFLOW.md` §4 and §5 is required at:

- Any successor Phase 6 PR that defines a new control surface, a new trust boundary, or a non-reversible decision — `AI_WORKFLOW.md` §4(2). Examples include any first runtime activation of any merged Phase 3 fixture, any first connection of any simulation or dry-run surface to a real broker, real market data feed, real order router, or real persistence layer, any ADR update that changes the kill-switch / reconciliation / heartbeat policy, and any change that touches the secrets-management discipline.
- Any Phase 6 PR that would, if wrong, cause real-world loss — `AI_WORKFLOW.md` §4(3). Such a PR is by definition **out of Phase 6 scope** per §2 (no live-trading authorization, no broker integration, no paper-trading wired to a real broker, no real data retention or destruction policy that affects real accounts or markets). The correct response is to treat it as scope drift and stop per `AI_WORKFLOW.md` §6 rule 7 and §8 of this plan.

**Mode B continuous governance monitor** per ADR-008 §D3 (or ADR-009 D3 once in force) is required on any active workday on which the default branch changes or a pull request is open, updated, or merged. The Backup AI authors packet text; the default builder (local Claude Code / Claude Max under GOV-02) commits it per `AI_WORKFLOW.md` §1.4 and §6 rule 1 and ADR-008 §D1 (or ADR-009 D1).

The Backup AI produces a written critique only (Mode A) or packet text only (Mode B). It does not edit other files, does not commit, does not push, does not merge, and does not approve. `AI_WORKFLOW.md` §6 rule 1 ("One builder at a time") is preserved: under GOV-02, local Claude Code / Claude Max is the default — and absent a Kevin-authorized exception, the only — role that writes to the repository.

---

## 8. Rollback and Stop Conditions

Each future Phase 6 PR must support a clean rollback.

Rollback rules:

- Every Phase 6 PR is reversible by a single `git revert` on the merge commit. PRs that bundle unrelated changes are split until this is true.
- The accepted Phase 1 baseline (`1f101fc` per `MASTER_STATUS.md` §3) is the last-known-good state. Reverting all Phase 2, Phase 3, Phase 4, Phase 5, and Phase 6 work returns the tree to a descendant of that baseline.
- A deployment log entry per `docs/deploys/deploy-log-template.md` is required if any Phase 6 change affects developer environments (e.g. new tooling requirement, new pre-commit hook), even though no runtime is being deployed under the planning-level definition of §2.
- Once runtime exists on `main`, ADR-009 D5's missed-packet severity replaces ADR-008 §D5 on a going-forward basis per ADR-009 D7's bootstrap-avoidance clause. Until runtime exists, ADR-008 §D5 continues to apply.

Stop conditions — if any of the following occurs, Phase 6 work pauses and the situation is escalated to Kevin before further changes:

1. A Phase 6 PR cannot satisfy the proof bundle in §6 without expanding scope.
2. A Phase 6 PR is found to cross into strategy, broker, paper-trading wired to a real broker, live-trading, market data ingestion, real secrets, order placement, scheduler / daemon, persistence outside the test sandbox, runtime-daemon territory, runtime activation of any merged Phase 3 fixture beyond what is named in the PR's separate written authorization, simulation expansion beyond what is named in the PR's separate written authorization, order semantics change beyond what is named in the PR's separate written authorization, or ops execution work beyond what is named in the PR's separate written authorization — at review time or after merge.
3. `pre-commit` or `pytest` fails and the proposed fix is to weaken the hook, loosen mypy strict mode, relax `detect-secrets`, or modify `.secrets.baseline` to silence a real finding.
4. `MASTER_STATUS.md` and a Phase 6 PR disagree about the current phase, the accepted baseline, the `allowed_p2_infra` allowlist, the canonical post-foundation-complete state, or the allowed next decisions.
5. Two changes attempt to land on the default branch simultaneously, violating `AI_WORKFLOW.md` §6 rule 4 (one builder, one branch per task).
6. The Backup AI (when invoked per §7) identifies a specific invariant violation that the verifier did not catch.
7. A required Mode B monitoring packet under ADR-008 §D3 (or ADR-009 D3 once in force) is missing for a prior active workday and no catch-up note per ADR-008 §D5 (or ADR-009 D5) has been committed.
8. A Phase 6 PR proposes to re-export any merged Phase 3 fixture or any new Phase 6 type from `src/gmc_rebuild/__init__.py`, or to consume any merged Phase 3 fixture from a `__main__` / daemon / scheduler / runtime path, without that specific activation being named in Kevin's separate written authorization and without Mode A per `AI_WORKFLOW.md` §4(2).
9. A Phase 6 PR proposes any reintroduction of stale `**pending merge**` language for already-merged packets.

In any stop condition, the default is to pause and ask Kevin. Per `AI_WORKFLOW.md` §6 rule 10: "When in doubt, stop. A paused task is recoverable. A merged Phase 6 change made by accident is not."

---

## 9. ADR Follow-ups That Phase 6 Successor Work Requires

Listed here for planning visibility. None of these follow-ups is authorized by this plan. Each requires its own separate written authorization from Kevin, a sibling artifact under `governance/authorizations/`, and the applicable Mode A / Mode B review.

- **ADR-009 — runtime monitoring cadence.** ADR-009 D7's bootstrap-avoidance clause keeps ADR-008 §D3 / §D5 in force until runtime exists on `main`. The candidate Phase 6 sequence in §4 introduces no runtime; ADR-008 cadence is expected to remain in force across P6-01..P6-07. Any future Phase 6 PR that proposes to introduce runtime must satisfy the ADR-009 D3 / D5 cadence as it takes effect, and that proposal is itself outside the Phase 6 planning-level scope of §2.
- **ADR-001 — secrets management.** Phase 6 introduces no real secrets under §2. If any later Phase 6 or Phase 7 task ever needs to reference a real secret (it must not, under §2), ADR-001's secrets-management discipline must be revisited in a separate PR before the reference lands.
- **ADR-002 — runtime kill-switch architecture.** Any Phase 6 use of `InMemoryKillSwitch` or its composed boundary must align with ADR-002 and must not add broker side effects, order placement, or network calls.
- **ADR-003 — broker reconciliation discipline.** Any Phase 6 use of `InMemoryReconciliation` must align with ADR-003 and must preserve the `UNAVAILABLE` / `FAILED` / `WARNING` distinctions end-to-end.
- **ADR-005 — operator availability heartbeat.** Any Phase 6 use of `InMemoryHeartbeat` must align with ADR-005 and must not add a scheduler, an operator-availability daemon, or an external sink.
- **ADR-006 — deployment logs.** Any Phase 6 change that affects developer environments requires a deployment log entry. No runtime deployment is authorized under §2.
- **ADR-007 — minimal CI strategy.** Any Phase 6 PR that proposes a CI change must do so as a separate ADR update reviewed under `AI_WORKFLOW.md` §4(2).

The list above is not exhaustive. Any later ADR follow-up that surfaces during the planning workstream must be raised with Kevin and recorded in a sibling artifact under `governance/authorizations/` before the follow-up PR opens.

---

## 10. Explicitly Not Authorized

For audit clarity, the following categories remain forbidden under this planning document. Each is forbidden by default per `MASTER_STATUS.md` §6; mirroring them here is **not** a re-authorization and is **not** a relaxation. Each requires Kevin's separate written authorization per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 / rule 7, a sibling artifact under `governance/authorizations/`, the applicable Mode A / Mode B review, and (where it introduces a new directory) a corresponding update to the §8 step 4a allowlist in the same PR.

- **Any successor Phase 6 task.** P6-01 (`d52551a`), P6-02 (`4785e24`), P6-03 planning (PR #144 at `583f457`), P6-03 implementation (PR #146 at `8d98a41`), and P6-04 implementation (Direction A) (PR #158 at `cea8553`) have merged on `main`; P6-05 implementation is **authorized but not yet implemented** per `governance/authorizations/2026-05-22_p6-05.md` (PR #164 at `cb4574e`, with the prior P6-05 planning packet at PR #162 / `5d1c743`); P6-06 / P6-07 / … remain **future / not authorized**. Each successor task requires its own separate written authorization and, if merely enumerated first, a separate docs-only enumeration update that does not authorize implementation.
- **Trading strategy code.** No trading signals, no scanners, no models, no portfolio rules, no backtests against real history. A typed signal-intake boundary that accepts a structured object is not strategy code; an algorithm that decides what to trade is.
- **Broker integration.** No broker SDK, no broker connector, no broker reconciliation runtime, no broker authentication, no broker credentials.
- **Paper-trading wired to a real broker.** No paper-broker connector, no paper-account identifier, no paper-API surface, no paper-trading execution loop.
- **Live-trading wired to a real broker.** No live-broker connector, no live-account identifier, no live-API surface, no live-trading execution loop.
- **Market-data integration.** No market-data ingestion code, no market-data pipeline, no committed dataset, no live / delayed / paper data feed.
- **Order management / routing.** No order placement, no position management, no fills tied to a real broker, no trade reports, no order routing logic, no venue selection, no execution adapter, no FIX session, no REST client, no WebSocket client.
- **Scheduling.** No cron-style scheduler, no APScheduler, no background-job framework, no operator-heartbeat daemon, no kill-switch runtime, no reconciliation runtime.
- **Persistence.** No SQLite, no DuckDB, no Postgres, no on-disk database, no on-disk reconciliation snapshot, no on-disk portfolio snapshot, no on-disk heartbeat state, no on-disk log sink, no file artifact written by runtime code under this plan.
- **Deployment.** No deployment workflow, no rollout, no rollback runtime, no CI/CD pipeline beyond the existing local pre-commit and pytest gates.
- **Secrets / env-var loading.** No real secrets, no real credentials, no `.env` files, no `os.environ` / `os.getenv` reads, no real account identifiers, no real broker / venue identifiers, no real endpoints embedded anywhere in the repository under this plan.
- **Network.** No `socket`, no `urllib`, no `requests`, no `http`, no `ssl`, no `smtplib`, no `ftplib`, no outbound or inbound network code.
- **Concrete risk implementations inside the runtime package.** The P2-05 boundary (types and abstract `typing.Protocol` definitions only) is preserved.
- **Runtime activation of any merged Phase 3 fixture.** No `__main__` entry point, no daemon, no scheduler, no background worker, no long-running service, no live execution loop, no re-export of any merged Phase 3 fixture from `src/gmc_rebuild/__init__.py` or any other runtime path under this plan.
- **Simulation expansion.** No additional `SimulationLane` / `SimulatedOrderSide` / `SimulatedOrderType` member, no ninth field on `SimulatedOrderIntent`, no additional method on `SimulationBoundary` beyond the merged `propose` and `propose_order`, no additional placeholder / order record class — except as specifically named in a future P6-0N written authorization for the relevant packet.
- **Order semantics change.** No change to the meaning of `propose` or `propose_order`, no change to the `SafetyVerdict.clear` precondition, no change to the identity-return contract, no addition of side effects.
- **Ops execution work.** No X10 Layer 5 promotion (OPS-05 remains future / not authorized). No backup-monitoring automation (the OPS-06 plan remains rules and thresholds only). No DR drill execution (OPS-07 remains future / not authorized).
- **Tooling relaxation.** No weakening of pre-commit, Ruff, mypy strict mode, `detect-secrets`, `.gitignore`, `.secrets.baseline`, or any §8 step 4 / step 4a / step 4c scan.
- **§8 step 4a allowlist expansion.** The `allowed_p2_infra` allowlist is **not** extended by this plan. Any future addition requires a separate written authorization that names a specific implementation task, a sibling artifact under `governance/authorizations/`, and an allowlist update made in the same PR that introduces the new directory.
- **Source / test changes.** No file under `src/**` or `tests/**` is modified or created by this plan or by the PR that lands it.
- **New tags or releases.** No git tag, no GitHub release, no version bump.
- **Reintroduction of stale "pending merge" language.** This plan preserves the canonical status reconciliations recorded by the prior PRs.
- **Mode A / Mode B substitution.** This plan is governance prose, not a control-surface decision; it does not substitute for adversarial review of any future P6-0N implementation PR.
- **GOV-02 reinterpretation.** This plan does **not** reinterpret or relax the GOV-02 execution-environment workflow rule. Local Claude Code / Claude Max remains the default execution environment for `gmc-rebuild` repo edits; Perplexity-managed codebase subagents that consume Perplexity credits must not perform repo edits absent Kevin's explicit written authorization for the specific packet.

The always-forbidden categories in `MASTER_STATUS.md` §6 — strategy code, broker execution code, paper-trading or live-trading wired to a real broker, runtime daemons affecting accounts, real market data ingestion, order placement, and real secrets — remain forbidden in all modes. This plan does not relax them and does not record any relaxation.

---

## 11. Recommended First Dry-Run Implementation Packet (Merged)

The recommended first dry-run implementation packet was **PR P6-01 — the typed signal-intake boundary** (§4 above), corresponding to Roadmap §8 Packet 3, which has since merged on `main` as of 2026-05-19 at commit `d52551a`. The reasoning recorded here at planning level only:

- It is the smallest possible packet that introduces a new dry-run engine capability: a single new submodule (`src/gmc_rebuild/signal_intake/`) containing a single internal module and a frozen, slotted dataclass defining the signal-intake intent shape, plus a tests directory under `tests/signal_intake/` covering determinism, shape, validation, and inertness.
- It depends on no later packet. P6-02 (eligibility) depends on the P6-01 dataclass; P6-03 (decision composer) depends on both; P6-04..P6-07 depend on the earlier capabilities. P6-01 stands alone and is reversible by a single `git revert`.
- It introduces no new public name beyond the new submodule's exports, no new behavior beyond accepting the new dataclass, no broker reference, no real-venue identifier, no env-var read, no network call, no scheduler, no `__main__`, no persistence, no concrete protocol implementation, no simulation expansion, no order semantics change.
- It adds exactly one `§8 step 4a allowlist` entry (`src/gmc_rebuild/signal_intake`) in the same PR that introduces the directory.
- It can be preceded by a separate planning / enumeration packet at Kevin's option, mirroring the merged P5-06-planning / P5-07-planning precedent, if Kevin wants the candidate shape recorded before implementation.

**This recommendation did not itself open P6-01.** Opening P6-01 required Kevin's separate written authorization per `MASTER_STATUS.md` §7.3, recorded in a sibling artifact under `governance/authorizations/` per `AI_WORKFLOW.md` §7, with Mode A and Mode B as applicable per `AI_WORKFLOW.md` §4 and ADR-008 / ADR-009. That authorization was recorded at `governance/authorizations/2026-05-19_p6-01.md`, and P6-01 merged on `main` at `d52551a`.

---

## 12. Supporting References (Non-Authoritative)

- Phase 1 accepted baseline: `1f101fc` (`MASTER_STATUS.md` §3).
- Phase 2 entry plan: `plan/phase2_entry_plan.md`.
- Phase 2 closure authorization: `governance/authorizations/2026-05-12_phase-2-closure.md`.
- Phase 3 entry plan: `plan/phase3_entry_plan.md`.
- Phase 3 closure authorization: `governance/authorizations/2026-05-14_phase-3-closure.md`.
- Phase 4 entry plan: `plan/phase4_entry_plan.md`.
- Phase 4 safety foundation closure (P4-08): `governance/authorizations/2026-05-16_p4-08.md`.
- Phase 5 entry plan (the immediate pattern reference for this Phase 6 entry plan): `plan/phase5_entry_plan.md`.
- P5-07 implementation authorization (most recent merged Phase 5 packet): `governance/authorizations/2026-05-18_p5-07.md`.
- GOV-01 governance reconciliation authorization: `governance/authorizations/2026-05-17_gov-01.md` — merged via PR #106 at `4df8074`.
- GOV-02 execution-environment workflow correction authorization: `governance/authorizations/2026-05-18_gov-02.md` — merged via PR #132 at `94d30bf`, reconciled via PR #134 at `fb13994`.
- GMC Project Map (strategic compass): [`docs/GMC_PROJECT_MAP.md`](../docs/GMC_PROJECT_MAP.md) — merged at `e62e27c`.
- Foundation-to-Dry-Run Roadmap (30-to-60-day operating bridge): [`docs/FOUNDATION_TO_DRY_RUN_ROADMAP.md`](../docs/FOUNDATION_TO_DRY_RUN_ROADMAP.md) — merged at `a13cdf9`, reconciled at `ce010cb` (Packet 1-FU-A).
- Foundation-Complete Confirmation Report: [`docs/decisions/2026-05-19_foundation_complete_confirmation.md`](../docs/decisions/2026-05-19_foundation_complete_confirmation.md) — merged at `a92568e`.
- Packet 1-FU-A (roadmap §3 wording reconciliation): commit `ce010cb`.
- Packet 1-FU-B (pre-commit cleanliness restoration): commit `8dc7a2d`.
- ADR-008 (governance-phase monitoring cadence): `docs/decisions/ADR-008_monitoring_cadence_and_ai_monitor_role.md` §D3 / §D5.
- ADR-009 (runtime-phase monitoring cadence): `docs/decisions/ADR-009_runtime_monitoring_cadence.md` — Accepted on 2026-05-13; D7 bootstrap-avoidance clause keeps ADR-008 §D3 / §D5 in force until runtime exists on `main`.
- Workflow separation of duties: `AI_WORKFLOW.md` §1 (roles), §2 (standard workflow), §3 (required proof), §4 (when to use the Backup AI), §6 (anti-chaos rules), §7 (durable authorization artifacts).
