# Phase 2 Entry Plan

**Status:** Planning only — Phase 2 implementation is not yet open.
**Created:** 2026-05-11 UTC
**Owner:** Perplexity Computer (supervisor), approved by Kevin.
**Scope:** This document plans the entry to Phase 2. It does not implement Phase 2 and does not authorize any change to runtime, strategy, broker, market data, or live trading behavior.

If anything here conflicts with `MASTER_STATUS.md` or `AI_WORKFLOW.md`, those files win. This document is supporting material for the Phase 2 boundary; it does not redefine it.

---

## 1. Current Status

- **Phase 1 accepted baseline:** `1f101fc` (`docs: fix Phase 1 verification blockers`), accepted per the written GitHub acceptance note on PR #3. This is the accepted Phase 1 baseline; earlier candidates referenced in `MASTER_STATUS.md` §3 (`b39d036`, `ee3457f`) are superseded by Kevin's written acceptance of `1f101fc` and any subsequent `MASTER_STATUS.md` update must record that promotion in the same audit-visible way described in `AI_WORKFLOW.md` §6 rule 2.
- **Phase 2 planning:** Authorized by Kevin. This document is the only Phase 2 artifact in flight.
- **Phase 2 implementation:** Not yet open. No source code, no runtime, no strategy, no broker integration, no live data, no order placement, no daemons, no scanners, no signal rules, no scheduled services are authorized at this time.
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

1. **PR P2-01 — Package skeleton and test harness.** Create the empty `src/<package>/` layout, `__init__.py` files, and a pytest harness that runs against the new package. No runtime behavior. Confirms that imports, typing, and tests still pass under mypy strict.
2. **PR P2-02 — Config schema with fake examples only.** Add a config schema module (e.g. pydantic or dataclasses + validator) with example fixtures containing obviously fake values. No real credentials, no real endpoints, no real account identifiers. Tests cover schema validation and rejection of malformed input.
3. **PR P2-03 — UTC and time utility module.** Add a small module that exposes the canonical "now UTC" function, parsers, and formatters, and forbids timezone-naive datetimes at the API boundary. Aligns with ADR-004. Tests cover round-trip and rejection of naive inputs.
4. **PR P2-04 — Structured logging and audit event conventions.** Add a logging configuration module and an `audit_event` helper that produces structured records with documented fields. No external sink; output is to the standard logger only. Tests cover record shape and redaction.
5. **PR P2-05 — Risk-control interfaces (no broker).** Add abstract interfaces / protocols for kill switch, reconciliation, and heartbeat aligned with ADR-002, ADR-003, and ADR-005. Provide test-only fake implementations. No broker SDK, no network calls, no order objects.

Sequencing rules:

- PRs land one at a time. PR P2-(N+1) is not opened until PR P2-N is accepted by Kevin.
- Each PR is small enough that the diff and the proof bundle (Section 6) fit a single review.
- Any PR that grows beyond its stated scope during implementation is split or stopped.

---

## 5. Phase 2 Entry Criteria

Phase 2 implementation may begin only when **all** of the following are true and recorded:

1. The Phase 1 accepted baseline is `1f101fc` (per PR #3 written acceptance) and `MASTER_STATUS.md` §3 has been updated to reflect that acceptance.
2. No unresolved blocker remains in ADRs, templates, README, tooling, or repo hygiene.
3. Kevin has explicitly authorized Phase 2 in writing — commit message, PR comment, or governance entry, not a chat message — per `MASTER_STATUS.md` §7.3.
4. This Phase 2 Entry Plan has been merged and is referenced from `MASTER_STATUS.md` and/or `README.md`.
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
- Any Phase 2 PR that defines a new control surface or trust boundary (e.g. the risk-control interface PR, the config schema PR if it touches secret references, the audit/logging conventions PR).
- Any future change that, if wrong, could cause real-world loss — this should not appear in Phase 2 at all; if it does, treat it as scope drift per `AI_WORKFLOW.md` §6 rule 7.

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
