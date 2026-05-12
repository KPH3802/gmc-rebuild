# Phase 2 Entry Plan

**Status:** Planning only — Phase 2 implementation is not yet open.
**Created:** 2026-05-11 UTC
**Owner:** Perplexity Computer (supervisor), approved by Kevin.
**Scope:** This document plans the entry to Phase 2. It does not implement Phase 2 and does not authorize any change to runtime, strategy, broker, market data, or live trading behavior.

If anything here conflicts with `MASTER_STATUS.md` or `AI_WORKFLOW.md`, those files win. This document is supporting material for the Phase 2 boundary; it does not redefine it.

---

## 1. Current Status

- **Phase 1 accepted baseline:** `1f101fc` (`docs: fix Phase 1 verification blockers`), accepted per the written GitHub acceptance note on PR #3. That written acceptance is itself the audit-visible record and, per its own terms, supersedes the stale `b39d036` reference inside `MASTER_STATUS.md` §3 at commit `1f101fc`. Editing §3 to restate the promotion is not required to make the acceptance valid; if §3 is ever revised, it must be revised in the audit-visible way required by `AI_WORKFLOW.md` §3.1 (no silent substitution of the baseline).
- **Phase 2 planning:** Authorized by Kevin. This document is the only Phase 2 artifact in flight.
- **Phase 2 implementation:** **Fully merged through P2-05; Phase 2 formally closed (governance-only).** The §4 P2-01..P2-05 sequence is merged on `main` as of 2026-05-12 (P2-01 at `e0278c4`, P2-02 at `6875b2d`, P2-03 at `b4e6d75`, P2-04 at `5dac8a0`, P2-05 at `a30e34b`); the current `main` checkpoint that contains all five merges is `5c390ff`. Phase 2 is formally closed at the current `main` checkpoint after PR #23 per Kevin's written authorization recorded at `governance/authorizations/2026-05-12_phase-2-closure.md`. The closure is governance-only and does **not** open Phase 3, does **not** open any new Phase 2 task beyond P2-05, does **not** extend the `MASTER_STATUS.md` §8 step 4a allowlist, does **not** relax any quality gate, and does **not** create any tag or release. Opening Phase 3, opening any new Phase 2 task beyond P2-05, or opening any runtime / broker / market-data / order / strategy / scheduler / persistence / deployment work requires Kevin's separate written authorization per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 / rule 7. No runtime, no strategy, no broker integration, no live data, no order placement, no daemons, no scanners, no signal rules, no scheduled services are authorized at this time; the P2-05 risk-control submodule contains only abstract `typing.Protocol` definitions and supporting frozen dataclasses (types and abstract boundaries only — no concrete runtime implementation of the protocols inside the runtime package). A documentation-only point-in-time inventory of this checkpoint is recorded at `docs/decisions/PHASE_2_P2_01_TO_P2_05_CHECKPOINT_SUMMARY.md`; that summary is not itself the closure authorization.
- **Workflow in effect:** Codex builds → Perplexity Computer verifies → Kevin approves → backup AI reviews adversarially at gates and high-risk decisions (per `AI_WORKFLOW.md` §1, §2, §4).

Until the entry criteria in Section 5 below are met and Kevin records authorization, the only allowed work is planning, governance documentation, and Phase 1 maintenance per `MASTER_STATUS.md` §9.

---

## 2. Phase 2 Objective

Phase 2 is **infrastructure foundation only**. Its purpose is to put in place the non-trading scaffolding that any future Phase 3+ work would have to use, with no runtime trading behavior of any kind.

In scope for Phase 2 (subject to Kevin's explicit per-task authorization):

- Python package skeleton with `src/` layout and a test harness that exercises pure-Python modules only.
- Configuration schema with fake/example values only, validated by a schema layer, with no real broker credentials, no real account identifiers, and no real data endpoints.
- A UTC and time utility module that enforces timezone-aware UTC per ADR-004.
- Structured logging and audit event conventions: log shape, redaction rules, audit event identifiers — without wiring to any external sink and without emitting any trading event.
- Risk-control **interfaces** (types, abstract boundaries, dataclasses) with no broker integration and no live behavior behind them.
- Test-only fakes/stubs to exercise the above interfaces.

Out of scope for Phase 2 — these remain forbidden until a future phase is opened by Kevin in writing:

- Trading strategy code (signals, scanners, models, portfolio rules, backtests against real history).
- Broker execution code (order placement, position management, broker SDK integration).
- Live trading workflows or paper-trading workflows wired to a real broker.
- Runtime daemons, schedulers, long-running services, background workers, or anything with a `__main__` entry point that touches accounts, markets, or money.
- Market data ingestion code, real data pipelines, or any committed datasets.
- Real secrets, real credentials, real account identifiers, real endpoints.
- Any change that loosens `.gitignore`, `.pre-commit-config.yaml`, mypy strict mode, or `detect-secrets`.

This split is intentional and is the line `MASTER_STATUS.md` §6–§7 already draws. Phase 2 does not move that line; it builds underneath it.

---

## 3. Allowed Planning Topics

While Phase 2 is in the planning state, Codex and Perplexity Computer may discuss and write planning artifacts on the following topics. Planning artifacts are documents, not code, and must be reviewable as documents.

1. Package layout: directory structure, `src/` vs. flat layout, package names, module boundaries.
2. Test harness: pytest layout, fixture conventions, what kinds of tests are allowed (unit only, no integration tests against external systems).
3. Config schema design: shape, validators, fake/example values, how secrets would be referenced in a future phase (without putting any in Phase 2).
4. UTC/time utility: API surface, what it forbids (naive datetimes, local time), interaction with ADR-004.
5. Logging and audit event conventions: log record shape, log level discipline, audit event identifiers and field names, redaction rules.
6. Risk-control interface design: kill-switch interface, reconciliation interface, heartbeat interface — all as types and protocols only, with no implementation that talks to a broker.
7. Phase boundary enforcement: how Phase 2 PRs prove they did not cross into strategy, broker, live, or data territory.

Any planning topic that does not fit the above list must be raised with Kevin before a document is written.

---

## 4. Proposed First Phase 2 Task Sequence

These are **proposed future PRs**, not work to be done now. Each is intentionally small enough to verify independently. None of these may begin until the entry criteria in Section 5 are met and Kevin authorizes the specific task.

1. **PR P2-01 — Package skeleton and test harness.** Create the empty `src/<package>/` layout, `__init__.py` files, and a pytest harness that runs against the new package. No runtime behavior. Confirms that imports, typing, and tests still pass under mypy strict. **Authorized and merged** (PR #6 at `e0278c4`, durable record at `governance/authorizations/2026-05-11_p2-01.md`).
2. **PR P2-02 — Config schema with fake examples only.** Add a config schema module (dataclasses-based) with safe local-only defaults. Frozen `ProjectConfig` with metadata fields only (`project_name`, `package_name`, `phase`, `environment`, `local_data_dir`, `local_logs_dir`) plus a `default_config()` helper. No real credentials, no real endpoints, no real account identifiers, no real broker / venue names, no live or paper toggles, no runtime-behavior boolean flags (even disabled), no env-var loading, no filesystem materialisation. The `local_data_dir` default is `./gmc_data` so it cannot collide with the §8 step 4 always-forbidden top-level `data` path. Tests cover importability, frozen-ness, safe defaults, the absence of any runtime-behavior boolean toggle, the absence of forbidden runtime submodules, and the absence of forbidden field tokens. **Authorized and merged** (PR #11 at `6875b2d`, durable record at `governance/authorizations/2026-05-11_p2-02.md`). The §8 step 4a allowlist was extended in the same PR to include `src/gmc_rebuild/config/` alongside the existing `src/`.
3. **PR P2-03 — UTC and time utility module.** Add a small module that exposes the canonical "now UTC" function, parsers, and formatters, and forbids timezone-naive datetimes at the API boundary. Aligns with ADR-004. Tests cover round-trip and rejection of naive inputs. **Authorized as a governance-only slice and merged** (authorization slice landed in PR #14 at `cb5b8bf`, implementation landed in PR #15 at `b4e6d75`, durable record at `governance/authorizations/2026-05-12_p2-03.md`). The §8 step 4a allowlist was extended by the authorization slice PR to include `src/gmc_rebuild/time/` alongside the existing `src/` and `src/gmc_rebuild/config/`.
4. **PR P2-04 — Structured logging and audit event conventions.** Add a logging configuration module and an `audit_event` helper that produces structured records with documented fields. No external sink; output is to the standard logger only. Tests cover record shape and redaction. **Authorized as a governance-only slice and merged** (authorization slice landed in PR #16 at `94b570e`, implementation landed in PR #17 at `5dac8a0`, durable record at `governance/authorizations/2026-05-12_p2-04.md`). The §8 step 4a allowlist was extended by the authorization slice PR to include `src/gmc_rebuild/logging/` alongside the existing `src/`, `src/gmc_rebuild/config/`, and `src/gmc_rebuild/time/`.
5. **PR P2-05 — Risk-control interfaces (no broker).** Add abstract interfaces / protocols for kill switch, reconciliation, and heartbeat aligned with ADR-002, ADR-003, and ADR-005. No broker SDK, no network calls, no order objects, no concrete runtime implementation of the protocols inside the runtime package. **Authorized as a governance-only slice and merged** (authorization slice landed in PR #18 at `f6974bc`, implementation landed in PR #19 at `a30e34b`, durable record at `governance/authorizations/2026-05-12_p2-05.md`). The §8 step 4a allowlist was extended by the authorization slice PR to include `src/gmc_rebuild/risk/` alongside the existing `src/`, `src/gmc_rebuild/config/`, `src/gmc_rebuild/time/`, and `src/gmc_rebuild/logging/`. The implementation is restricted to abstract `typing.Protocol` definitions and supporting frozen dataclasses and enums (no broker SDK, no network, no concrete runtime behavior inside the runtime package). P2-05 is the final task in this P2-01..P2-05 sequence.

**Phase 2 is formally closed (governance-only) at the current `main` checkpoint after PR #23** per Kevin's written authorization recorded at `governance/authorizations/2026-05-12_phase-2-closure.md`. The closure does not open Phase 3, does not open any new Phase 2 task beyond P2-05, does not extend the §8 step 4a allowlist, does not relax any quality gate, and does not create any tag or release. Any work beyond this closure — Phase 3 entry, a Phase 2 task not in the §4 sequence, or any runtime / broker / market-data / order / strategy / scheduler / persistence / deployment work — requires its own separate written authorization, a sibling artifact under `governance/authorizations/`, any applicable runtime-cadence ADR follow-up (ADR-008 §D6), Mode A / Mode B review per `AI_WORKFLOW.md` §4 and ADR-008 where required, and (where it introduces a new directory) a corresponding update to the §8 step 4a allowlist in the same PR.

Sequencing rules:

- PRs land one at a time. PR P2-(N+1) is not opened until PR P2-N is accepted by Kevin.
- Each PR is small enough that the diff and the proof bundle (Section 6) fit a single review.
- Any PR that grows beyond its stated scope during implementation is split or stopped.

Pre-P2-01 planning note — `MASTER_STATUS.md` §8 startup check reconciliation:

- `MASTER_STATUS.md` §8 step 4 currently treats `src/` as a forbidden Phase 2 directory and reports `STOP: forbidden Phase 2 directories present` if it exists.
- P2-01 will create exactly that directory. Before P2-01 is opened, `MASTER_STATUS.md` §8 (and §6 if needed) must be updated in a separate, audit-visible governance PR to list `src/` (and the other Phase 2 infrastructure paths explicitly authorized by Kevin) as **allowed** Phase 2 paths, so the startup check distinguishes legitimate approved infrastructure from forbidden strategy/broker/live/data directories.
- This reconciliation is planning-only here. It does not modify `MASTER_STATUS.md` in this PR. It is not a tooling relaxation under `AI_WORKFLOW.md` §6 rule 8 because it does not weaken any quality hook, mypy strict mode, or `detect-secrets`; it only updates the boundary list to match Kevin's written Phase 2 authorization.
- If P2-01 is opened before this reconciliation lands, the §8 check will produce a false STOP. The fix is the reconciliation PR, not skipping the check.

---

## 5. Phase 2 Entry Criteria

Phase 2 implementation may begin only when **all** of the following are true and recorded:

1. The accepted Phase 1 baseline is `1f101fc`, established by Kevin's written acceptance on PR #3. That written acceptance is the audit-visible record and, per its own terms, supersedes the stale `b39d036` reference inside `MASTER_STATUS.md` §3 at commit `1f101fc`. No further §3 rewrite is required to satisfy this criterion; future work on the default branch starts from `1f101fc` or a descendant of it.
2. No unresolved blocker remains in ADRs, templates, README, tooling, or repo hygiene.
3. Kevin has explicitly authorized Phase 2 in writing — commit message, PR comment, or governance entry, not a chat message — per `MASTER_STATUS.md` §7.3. Authorization of "Phase 2 in general" does not by itself authorize any specific P2-0N PR; each first PR's scope must also be named in the authorization, per `MASTER_STATUS.md` §7.4.
4. This Phase 2 Entry Plan has been merged and is referenced from `README.md` (and optionally from `MASTER_STATUS.md` §9 "Next Allowed Decisions" if Perplexity Computer chooses to point to it from there).
5. The first Phase 2 PR is one of the proposals in Section 4 and is infrastructure-only, unless Kevin pre-approves a different narrow plan.

If any criterion fails, Phase 2 stays closed. Phase 1 maintenance continues under `MASTER_STATUS.md` §9.

---

## 6. Required Proof For Each Future Phase 2 PR

Each Phase 2 PR must include the proof bundle defined in `AI_WORKFLOW.md` §3. Restated here for convenience:

1. **Git state.**
   - `git status` showing a clean tree after commit.
   - `git log --oneline -10` showing the head commit and recent history.
   - `git rev-parse HEAD` showing the exact commit hash under review.
   - `git diff <baseline>..HEAD` against the accepted Phase 1 baseline `1f101fc` (or a later accepted baseline if one has been recorded).
2. **Tests and pre-commit.**
   - Full output of `pre-commit run --all-files` (must pass, or every failure documented).
   - Full output of `pytest` (must pass).
3. **Phase-boundary checklist.** For each Phase 2 PR, the verification report explicitly confirms:
   - No new top-level directories outside the documented set.
   - No new modules under `strategy/`, `signals/`, `broker/`, `execution/`, `live/`, `daemons/`, `data/`, or similar.
   - No new long-running entry points or schedulers.
   - No new secrets, real credentials, real endpoints, or generated data files.
   - No relaxation of `.gitignore`, `.pre-commit-config.yaml`, mypy strict mode, or `detect-secrets`.
4. **File-specific evidence.** Per `AI_WORKFLOW.md` §3.4, each changed file is named and the verifier states what was verified for it.
5. **Docs updated.** Any change to interfaces or conventions is reflected in the relevant document (ADR update, new ADR, or `MASTER_STATUS.md` entry) in the same PR — no orphaned code without a governance hook.

A Phase 2 PR that does not carry this bundle is not eligible for Kevin's review.

---

## 7. Review Protocol

Standard review per `AI_WORKFLOW.md` §2:

1. Kevin states the task in writing.
2. Perplexity Computer confirms the task fits the current phase and records it.
3. Codex builds the smallest change on a feature branch and opens a draft PR.
4. Perplexity Computer verifies using the proof bundle (Section 6) and returns findings if anything fails.
5. Codex revises without expanding scope.
6. Kevin decides.

Adversarial backup review per `AI_WORKFLOW.md` §4 and §5 is required at:

- The Phase 2 entry decision itself (opening Phase 2).
- Any Phase 2 PR that defines a new control surface or trust boundary — e.g. the risk-control interface PR, the config schema PR if it touches secret references, the audit/logging conventions PR.

A Phase 2 PR that, if wrong, could cause real-world loss (live trading authorization, broker integration, kill-switch behavior, operator-heartbeat policy, data retention or destruction policy) is by definition out of Phase 2 scope per Section 2. The correct response is to treat it as scope drift and stop per `AI_WORKFLOW.md` §6 rule 7 and Section 8 of this plan, not to invoke the backup AI as a substitute for stopping.

The backup AI produces a written critique only. It does not edit files, commit, or approve.

---

## 8. Rollback and Stop Conditions

Phase 2 entry, and each Phase 2 PR, must support a clean rollback.

Rollback rules:

- Every Phase 2 PR is reversible by a single `git revert` on the merge commit. PRs that bundle unrelated changes are split until this is true.
- The accepted Phase 1 baseline (`1f101fc` per PR #3) is the last-known-good state. Reverting all Phase 2 work returns the tree to a descendant of that baseline.
- A deployment log entry per `docs/deploys/deploy-log-template.md` is required if any Phase 2 change affects developer environments (e.g. new tooling requirement, new pre-commit hook), even though no runtime is being deployed.

Stop conditions — if any of the following occurs, Phase 2 work pauses and the situation is escalated to Kevin before further changes:

1. A Phase 2 PR cannot satisfy the proof bundle in Section 6 without expanding scope.
2. A Phase 2 PR is found to cross into strategy, broker, live trading, market data ingestion, real secrets, or runtime-daemon territory — at review time or after merge.
3. `pre-commit` or `pytest` fails and the proposed fix is to weaken the hook, loosen mypy strict mode, or relax `detect-secrets`.
4. `MASTER_STATUS.md` and a Phase 2 PR disagree about the current phase, the accepted baseline, or the allowed next decisions.
5. Two changes attempt to land on the default branch simultaneously, violating `AI_WORKFLOW.md` §6 rule 4 (one builder, one branch per task).
6. The backup AI (when invoked per Section 7) identifies a specific invariant violation that the verifier did not catch.

In any stop condition, the default is to pause and ask Kevin. Per `AI_WORKFLOW.md` §6 rule 10: "When in doubt, stop. A paused task is recoverable. A merged Phase 2 change made by accident is not."
