# Foundation to Dry-Run Roadmap

Last updated: 2026-05-19

## 1. Purpose

This document translates the strategic compass in [`docs/GMC_PROJECT_MAP.md`](GMC_PROJECT_MAP.md) into a practical 30 to 60 day operating plan. It exists to answer one question:

> What must be true before the foundation rebuild is considered complete enough to begin building the dry-run trading engine in earnest, and how do we get there without losing the trading-engine objective behind another wave of process artifacts?

The Project Map is the strategic compass. `MASTER_STATUS.md` is the audit and status log. This roadmap is the bridge between them — a forward-looking planning document that names visible moves toward Layer 2 (dry-run trading engine) of the Project Map.

This roadmap does not authorize any new work. Every implementation packet named here remains gated by Kevin's separate written authorization per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 (one approver) and rule 7 (no phase drift). Naming a packet in this document is not the same as opening it.

## 2. Current State Summary

The foundation rebuild has produced a meaningful operating chassis. At a capability level (not commit level — refer to `MASTER_STATUS.md` for SHAs and authorization artifacts), the repository currently contains:

- A governance-first project layout with written authorization for every implementation slice, Mode A adversarial review on high-risk slices, and Mode B sibling monitoring packets where applicable.
- A clean `src/gmc_rebuild/` package skeleton with no runtime behavior, no `__main__`, no daemon, no scheduler, no broker SDK, no env-var loading, and no embedded credentials.
- A safe-by-default `ProjectConfig` schema with local-only defaults.
- A UTC time utility that rejects timezone-naive datetimes at the API boundary (ADR-004).
- A structured-logging and `audit_event` helper that writes to the standard logger only — no external sink.
- Abstract `typing.Protocol` boundaries for the kill switch (ADR-002), reconciliation (ADR-003), and heartbeat (ADR-005), with supporting frozen dataclasses and enums. Types only; no concrete runtime implementations inside the runtime package.
- Three deterministic in-memory test fixtures conforming structurally to those Protocols (`InMemoryHeartbeat`, `InMemoryKillSwitch`, `InMemoryReconciliation`), wired only into the test suite — not re-exported from `src/gmc_rebuild/__init__.py` and not imported by any runtime path.
- A composed-fixture test surface that exercises the three fakes together and asserts cross-fixture invariants and edge cases.
- An inert local simulation boundary plus simulated-order-intent model and tripwire test coverage exercising invariants, composed integration, and operator-view determinism and idempotence.
- Operational records: a backup restore drill, an X10 panic investigation, a memory-pressure baseline, and a backup-monitoring plan.
- A governance reconciliation pass (GOV-01) and a risk register.
- ADR-008's monitoring cadence and backup-AI monitor role.

The honest assessment from the Project Map still applies: the rebuild has produced strong controls, but the project has also drifted toward status reconciliation and tripwire work. The missing piece is the visible path from this foundation into a working local dry-run trading loop skeleton. Closing that gap is the purpose of the next 30 to 60 days.

## 3. Definition of "Foundation Complete"

The foundation is complete enough to begin the dry-run engine in earnest when all of the following are true and verifiable from the repository itself — not from prose claims in status documents.

Code and tests:

- `src/gmc_rebuild/` contains the P2-01..P2-05 submodules (`config/`, `time/`, `logging/`, `risk/`, plus the package skeleton), the P3-03..P3-05 in-memory protocol fakes (`heartbeat/`, `kill_switch/`, `reconciliation/`), the P4-06 inert local runtime shell boundary (`runtime/`), and the P5-01 inert local simulation boundary skeleton (`simulation/`), with no runtime activation, no `__main__`, no daemon, no scheduler, no broker SDK, no network or filesystem call, and no env-var read.
- The composed-fixture test surface exercises the three Protocol fakes together and the invariants and edge-case tripwires pass deterministically on a clean checkout.
- The inert local simulation boundary and the simulated-order-intent model and their tripwire tests pass deterministically on a clean checkout.
- `pre-commit run --all-files` is green: `ruff`, `ruff format`, `mypy`, trailing-whitespace, end-of-file, YAML/JSON, AST, large-file, merge-conflict, mixed-line-ending, `detect-secrets`, and `pytest`.
- The `MASTER_STATUS.md` §8 startup verification commands pass on a fresh clone with no manual fix-ups.

Governance and operating discipline:

- The always-forbidden list in `MASTER_STATUS.md` §6 holds: no trading strategy code, no broker execution code, no live or paper-broker-wired workflow, no runtime daemon or scheduler touching accounts/markets/money, no real market-data ingestion, no secrets or `.env` files or local databases or generated reports.
- The §8 step 4a allowlist matches the merged set of authorized directories exactly — no orphaned entries, no missing entries.
- The risk register, backup-monitoring plan, and memory-pressure baseline are current and consistent with the most recent operational reality.
- Every merged implementation slice has a durable in-tree authorization artifact under `governance/authorizations/`.

Strategic readiness:

- The Project Map, this roadmap, and `MASTER_STATUS.md` agree on what is shipped, what is forbidden, and what is next.
- Kevin can answer, from the repository alone and without reconstructing context, the question: "What is the next bounded packet, why does it move us toward Layer 2, and what is the verification standard for accepting it?"

If any item above is not true, the foundation is not yet complete. Reaching that state is the precondition for opening dry-run engine implementation. It is not a precondition for the planning, design, and research work described in §6 and §7 below.

## 4. What the Dry-Run Trading Engine Skeleton Should Eventually Include

The dry-run engine is Layer 2 of the Project Map. It models the real trading loop without any money movement, any broker connection, any real market-data feed, or any persistence beyond local files explicitly authorized for the purpose.

The eventual skeleton is expected to include, at a minimum, the following local-only capabilities. Each becomes its own narrowly scoped, separately authorized implementation packet — none of them are opened by this document.

- **Signal intake.** A typed boundary for accepting a candidate trade idea as a structured object. Source-agnostic at this layer; input is either a fixture or an explicitly local, non-broker, non-live source.
- **Eligibility checks.** Pure functions that reject ineligible signals (symbol allow/deny, instrument type, market hours assumed by configuration, basic sanity checks) before any further processing.
- **Position and risk checks.** Composition of the existing `KillSwitchProtocol`, `ReconciliationProtocol`, and `HeartbeatProtocol` boundaries with eligibility output to produce an explicit "would-trade" or "would-skip" decision with structured reasons.
- **Simulated order intent.** Extension of the existing simulated-order-intent model into a full intent object capturing instrument, side, size, limit/stop semantics, and a generated intent identifier. No broker call. No order placement.
- **Simulated portfolio state.** A deterministic, in-memory portfolio object that applies accepted intents to a position book under explicit assumptions about fills, with no real market data and no broker confirmation.
- **Operator view.** A read-only, deterministic projection of current intents, decisions, and portfolio state suitable for human review — initially as structured text or JSON, not a live dashboard.
- **Reconciliation.** Use of the existing `ReconciliationProtocol` boundary to compare simulated portfolio state against an explicit, local, fixture-provided "expected" state. The `UNAVAILABLE` versus `FAILED` distinction must be preserved end-to-end.
- **Daily report.** A deterministic end-of-cycle structured record summarizing intents generated, decisions made, simulated fills applied, reconciliation status, and any tripped invariants — written to the standard logger via the existing `audit_event` helper, not to an external sink.
- **Failure and exception handling.** Explicit, named exception types at each layer boundary; no swallowed exceptions; structured `audit_event` records for every refusal, skip, kill-switch trip, reconciliation mismatch, and unhandled error.

Three properties must hold across every capability above:

1. The capability is reachable only from the test suite or from an explicit, local, non-broker entry point. No `__main__`, no daemon, no scheduler.
2. The capability uses only the in-memory Protocol fakes from `src/gmc_rebuild/heartbeat/`, `src/gmc_rebuild/kill_switch/`, and `src/gmc_rebuild/reconciliation/` at this layer. Concrete broker-backed implementations belong to Layer 4 and are not opened here.
3. Every behavior is covered by deterministic tests, including invariants and at least one composed edge-case test per capability.

## 5. What Remains Explicitly Forbidden

This roadmap does not change the always-forbidden list in `MASTER_STATUS.md` §6. It restates it here so that no packet proposed downstream can quietly drift across it.

Always forbidden until a separate written authorization and a named Layer 4 gate opens it:

- Trading strategy code: signals, scanners, models, portfolio rules, backtests, alpha factors, parameter sweeps.
- Broker execution code: order placement, position management, fill handling, broker SDK imports, account identifiers.
- Live trading workflows of any kind.
- Paper-trading workflows wired to a real broker, including paper accounts on Interactive Brokers, Alpaca, or any other venue.
- Runtime daemons, schedulers, long-running services, cron entries, `systemd` units, or background workers that touch accounts, markets, money, or external networks.
- Market-data ingestion code, real data pipelines, vendor SDKs, or stored datasets sourced from a real venue.
- Secrets of any kind: API keys, private keys, certificates, OAuth tokens, `.env` files, `.envrc` files, vault references, or credential files.
- Local databases (SQLite, DuckDB, Postgres) or generated report artifacts checked into the repository.
- Network calls from runtime code paths, including from the in-memory Protocol fakes and the dry-run engine modules described in §4.
- `time.sleep`, blocking I/O, or any wall-clock dependency in tests or in runtime code paths that the dry-run engine uses.
- Re-exporting the in-memory Protocol fakes from `src/gmc_rebuild/__init__.py` or importing them from any runtime path.

Reaching for any of the above as a shortcut is the failure mode this project is structured to prevent. A dry-run engine that quietly acquires a network call, a `time.sleep`, or a real broker import is not a dry-run engine.

## 6. What Can Proceed in Parallel

Per Project Map §"Where We Are Going" Layer 3, research and alpha pipeline work should not wait forever behind safety work. It can run in parallel with the foundation-completion and dry-run-skeleton work described in §3 and §4, provided it creates no live-trading risk and respects the §5 forbidden list.

Work that can proceed in parallel as planning, documentation, or local fixture-only artifacts:

- **Research queue design.** A documented schema for capturing a candidate trading idea: hypothesis, mechanism, instrument scope, data requirements, regime assumptions, falsification criteria, and promotion/demotion rules. Documentation only at this stage; no scanner code, no live data, no broker reference.
- **Signal inventory review.** A documented review of the prior-system signal set (PEAD, 8-K Item 1.01 shorts, SI squeeze, COT, CEL, 13F, Form 4, dividend initiations and cuts, options volume, Congress trading) capturing, for each, what is known, what is unknown, and what evidence quality would be required to promote it into the dry-run engine. Documentation only.
- **Regime and conditional analysis framework.** A documented method for describing market regimes and conditioning signal use on them. Documentation only at this stage.
- **Signal promotion/demotion rules.** A documented separation between "interesting idea," "deployable in dry-run," and "deployable in paper/live." Documentation only.
- **Operator-view design.** Mockups or structured-text examples of what the dry-run operator view should show, independent of implementation.
- **Daily-report design.** Field-level specification of the dry-run daily report, independent of implementation.
- **ADR drafts.** New ADRs covering decisions that the dry-run engine will need (for example: how the engine handles partial fills in simulation, how it resolves intent identifiers, how it represents time-in-force in a simulated context).
- **Risk-register maintenance.** Ongoing updates to the risk register as new risks are identified during planning.
- **Operational drills.** Continued backup-restore drills, memory-pressure observation, and incident-response rehearsal, consistent with the OPS series.

Work that **must not** proceed in parallel:

- Any scanner, ingestion, or feed code touching a real venue or real data vendor.
- Any backtest implementation that imports real market data or a real broker SDK.
- Any "research environment" that quietly creates a live or paper broker connection.
- Any signal implementation in `src/**` — signals remain Layer 3 and Layer 5 work, not foundation-completion work.

The professional-fund standard is that idea generation is encouraged; idea deployment is gated. Parallel research work documents future capability without acquiring the failure modes the rebuild was started to eliminate.

## 7. Next 30 to 60 Day Milestones

The following milestones are sequenced to close the foundation-complete gap in §3 and produce the first visible Layer 2 capability. Dates are illustrative and assume Kevin's separate written authorization for each implementation packet; nothing here opens any packet.

**Milestone A — Foundation-complete confirmation (week 1 to week 2).**

- Confirm against the §3 checklist that each item is true and verifiable from the repository.
- If any item is not true, identify the smallest packet that would make it true and propose it. Do not bundle.
- Reconcile any `MASTER_STATUS.md` drift discovered in the process as documentation-only, narrowly scoped reconciliation packets — not as opportunistic content expansion.

**Milestone B — Dry-run engine entry plan (week 2 to week 3).**

- Author `plan/phase6_dry_run_entry_plan.md` (or the next available phase plan name, consistent with prior `plan/phaseN_entry_plan.md` style) modeled on `plan/phase2_entry_plan.md`. It should name the bounded packets for the §4 capabilities, each packet's authorization slice and implementation halves, and the §8 step 4a allowlist entry each would add.
- Author the entry-gate ADR if one is required to justify opening Layer 2 implementation on the existing chassis.

**Milestone C — Signal intake and eligibility skeleton (week 3 to week 5).**

- Open the first dry-run capability as a narrowly scoped implementation packet: a typed signal-intake boundary and a pure-function eligibility-check module, with composed tests against the existing in-memory Protocol fakes.
- Acceptance criteria: deterministic tests, no runtime activation, no `__main__`, no network or filesystem dependency, no expansion beyond the named scope.

**Milestone D — Position/risk decision and simulated order intent (week 5 to week 7).**

- Open the second dry-run capability as the next implementation packet: a position/risk decision module that composes the three Protocol fakes with the eligibility output to produce a "would-trade" or "would-skip" decision, and an extension of the existing simulated-order-intent model into a full intent object.
- Acceptance criteria: deterministic tests including composed edge cases, no broker SDK, no order placement, no real account identifiers.

**Milestone E — Operator view and daily report (week 7 to week 9).**

- Open the third dry-run capability as the next implementation packet: a deterministic read-only operator view and a deterministic daily-report record written via the existing `audit_event` helper.
- Acceptance criteria: deterministic tests including idempotence tripwires, structured-text or JSON output, no external sink, no scheduler.

**Cross-cutting throughout the 60 days:**

- Maintain the §5 forbidden list. A single accidental drift across it resets the relevant milestone.
- Keep packets narrow. If a packet feels like more than one PR, split it.
- Preserve the FAA closed-loop and verification rule on every packet.

## 8. Suggested Next Claude Code Work Packets

The packets below are written so that each can be opened, authorized, and reviewed as a single bounded PR. Each respects the §5 forbidden list and the §7 governance discipline. None of these are opened by this document.

For each packet, the standard shape is: a governance-only authorization slice (or in-tree authorization artifact under `governance/authorizations/`) followed by a narrowly scoped implementation PR; both halves merged before the next packet opens. Where a new directory is introduced, the same PR updates the `MASTER_STATUS.md` §8 step 4a allowlist.

**Packet 1 — Foundation-complete confirmation report.** Documentation-only. A new file under `docs/decisions/` that walks the §3 checklist item-by-item, records the current state of each item, and either confirms "foundation complete" or names the smallest packets required to reach it. No `src/**` or `tests/**` change. Single approver: Kevin.

**Packet 2 — Dry-run entry plan.** Documentation-only. Author `plan/phaseN_entry_plan.md` (next available phase name) modeled on the existing entry plans, naming each §4 capability as a separately authorized packet with its allowlist implications. No `src/**` or `tests/**` change.

**Packet 3 — Signal-intake typed boundary.** Implementation. New submodule `src/gmc_rebuild/signal_intake/` containing a frozen-dataclass `SignalIntent` (or similarly named) plus a typed acceptance function. New tests under `tests/signal_intake/`. No runtime activation, no `__main__`, no broker reference, no real-venue identifier. Adds one §8 step 4a allowlist entry.

**Packet 4 — Eligibility-check pure functions.** Implementation. New submodule `src/gmc_rebuild/eligibility/` containing pure functions that accept the Packet 3 dataclass plus a project-config slice and return a structured eligibility decision. New tests under `tests/eligibility/`. No I/O, no time dependence outside the existing UTC utility. Adds one §8 step 4a allowlist entry.

**Packet 5 — Position/risk decision composer.** Implementation. New submodule `src/gmc_rebuild/decision/` (or similarly named) that composes Packet 3 input, Packet 4 output, and the existing in-memory Protocol fakes to produce a structured "would-trade" or "would-skip" decision with reasons. New tests under `tests/decision/` including composed edge cases mirroring the existing P4-04 pattern. Adds one §8 step 4a allowlist entry. Does not extend the runtime surface beyond composition of already-authorized submodules.

**Packet 6 — Simulated-order-intent extension.** Implementation. Extension of the existing simulated-order-intent model into a full intent object capturing side, size, and limit/stop semantics, with deterministic intent-identifier generation. New tests covering invariants and idempotence. No broker SDK, no order placement, no real account identifier. Adds one §8 step 4a allowlist entry if a new directory is introduced; otherwise extends within the existing simulation directory under its existing allowlist entry.

Packets 1 and 2 are documentation-only and can be drafted before any new implementation authorization. Packets 3 through 6 are sequenced and each requires its own separate written authorization per `MASTER_STATUS.md` §7.

## 9. Verification and Sign-Off Standard

The Project Map's verification rule applies to every packet named above:

1. Verify the change worked by reading back the actual file, output, state, or test result.
2. Verify the surrounding context did not break.

Absence of errors is not proof of success. Sign-off requires positive verification.

The FAA closed-loop also applies to every meaningful step:

1. Repeat back the instruction.
2. State the intended output.
3. Execute one bounded step.
4. Show the verified result.
5. Wait for confirmation before moving to the next major step when appropriate.

For each implementation packet, sign-off requires all of the following:

- The diff is restricted to the authorized directories on the `MASTER_STATUS.md` §8 step 4a allowlist, plus the authorization artifact under `governance/authorizations/` and any conservative `MASTER_STATUS.md` reflection.
- `pre-commit run --all-files` is green on the post-merge `main` head.
- The `MASTER_STATUS.md` §8 startup verification commands pass on a fresh clone.
- The §5 forbidden list is intact: no new broker SDK import, no new `__main__`, no new daemon or scheduler, no new env-var read, no new network or filesystem call from a runtime path, no new secret, no real account or venue identifier, no re-export of an in-memory Protocol fake from `src/gmc_rebuild/__init__.py`, no `time.sleep` in any runtime path or test.
- Tests are deterministic on a clean checkout; flaky tests are treated as failing tests.
- The packet's authorization artifact accurately describes what the PR did and did not do, and what was and was not authorized.

Sign-off is recorded in writing by Kevin per `AI_WORKFLOW.md` §7. Claude Code does not self-sign-off, and neither does any reviewing model.

The professional-fund standard is that a change is not done when the code compiles, not done when the tests pass, and not done when the diff looks clean. A change is done when Kevin, reading the repository alone, can verify what shipped, why, against what authorization, and at what cost to the §5 forbidden list — and that answer is "no cost."
