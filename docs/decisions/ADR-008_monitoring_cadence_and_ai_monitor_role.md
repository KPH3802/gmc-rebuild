# ADR-008: Monitoring Cadence and Backup-AI Monitor Role

## Status

Accepted

## Date

2026-05-11 UTC

## Context / Problem

Phase 1 verification surfaced an ambiguity that `AI_WORKFLOW.md` and `MASTER_STATUS.md` did not resolve on their own:

1. **Role ambiguity.** The backup / adversarial AI is defined in `AI_WORKFLOW.md` §1.4 and §4 as an optional adversarial reviewer used at phase gates, high-risk architecture decisions, and safety-critical decisions. It is not defined as a continuous monitor. `monitoring/daily/daily-report-template.md` implies a continuous monitoring cadence exists, but does not say who is responsible for it or when packets are due.
2. **Cadence ambiguity.** The daily monitoring template implies a daily packet, but the repository currently has no runtime, no live trading, no market data ingestion, no broker integration, and no operator heartbeat. A literal "daily" cadence in this state would generate noise packets that future readers cannot distinguish from real evidence and that the project has no realistic ability to maintain.
3. **Missed-packet ambiguity.** Neither `AI_WORKFLOW.md` nor `MASTER_STATUS.md` says what happens when a required monitoring packet is missing. Without a stated rule, missed packets either become silent (defeating the point) or trigger ad-hoc rollback responses (over-correcting against a control that does not exist yet).

This ADR resolves all three questions in one place so future agents and reviewers have a single reference. It is a governance decision only. It does not authorize Phase 2 work beyond the already-authorized P2-01, does not introduce runtime code, and does not change any always-forbidden category in `MASTER_STATUS.md` §6.

## Decision

### D1. Roles (clarification, not change)

The four roles in `AI_WORKFLOW.md` §1 stand unchanged: Codex (Builder), Perplexity Computer (Supervisor / Verifier / Status Keeper), Kevin (Approver), and the Backup AI (Adversarial Reviewer). This ADR clarifies that the Backup AI has **two distinct modes** with non-overlapping triggers:

- **Mode A — Gate Reviewer (existing).** Invoked per `AI_WORKFLOW.md` §4 at phase gates, high-risk architecture decisions, and safety-critical decisions. Produces a written critique only. Does not build. Does not decide. Does not edit files.
- **Mode B — Continuous Governance Monitor (clarified by this ADR).** Once monitoring cadence is active per D3 below, the Backup AI is the named author of monitoring packets when invoked, reading the working tree and recent PR activity and writing a packet under the path in D4. Still does not build, decide, or merge. Still does not edit files outside `monitoring/daily/`. Producing a monitoring packet is not approval and does not substitute for Perplexity Computer's verification or Kevin's decision.

The two modes share the same adversarial stance and the same constraint surface; the difference is the trigger.

### D2. Monitoring packets are governance artifacts, not runtime evidence

Until runtime exists in the repository (no Phase 2 daemon, no broker integration, no live trading, no real market data ingestion — see `MASTER_STATUS.md` §6), a monitoring packet is a governance artifact that documents repository state, phase compliance, and PR activity. It is not runtime evidence and must not claim to be. The Runtime Safety section of the daily template stays `N/A` in this state, as the template already instructs.

Once runtime exists, monitoring packets become runtime evidence as well. The semantics shift is governed by a future ADR (see D6).

### D3. Cadence

Cadence is defined by phase, not by calendar.

- **Governance / build phase (current state).** A packet is required on any **active workday** on which **either** of the following is true:
  - The repository state changes on the default branch (any merge to `main`), **or**
  - A pull request is open for review or is merged during that workday.

  An "active workday" is a calendar day on which a maintainer is working on the repository. Days on which no work occurs do not require a packet. The packet documents what changed and what did not change; it is not a heartbeat against wall-clock time.

- **Runtime / live phase (future, not authorized here).** Cadence may become **every trading day** or **every weekday** depending on what runtime is active. The specific cadence for that phase is **deferred to a later ADR** (see D6) and is not decided by this ADR. Until that ADR exists, the runtime cadence question is unresolved and live trading remains forbidden by `MASTER_STATUS.md` §6 independent of cadence.

This ADR explicitly does **not** mandate a daily packet during the current phase. The intent is to define the rule, not to backfill packets.

### D4. Location and format

- All monitoring packets live under `monitoring/daily/` and are named `YYYY-MM-DD.md` (UTC date).
- The packet uses the existing template at `monitoring/daily/daily-report-template.md`. The template is not modified by this ADR.
- Multiple packets on the same day are named `YYYY-MM-DD.md`, `YYYY-MM-DD_<short-slug>.md` (e.g. `2026-05-11_pr-9.md`), with the short slug describing the trigger.
- Template-only edits (changes to `daily-report-template.md` itself) do not require a packet under D3 because they do not change `main` state outside `monitoring/` and do not constitute a workday of substantive activity. Substantive governance PRs do require a packet under D3.

### D5. Missed-packet handling

A missed required packet is treated by phase:

- **Governance / build phase.** A missed packet is an **audit issue**, not an automatic rollback trigger. There is no runtime to roll back. The catch-up rule is:
  - Before the next phase-opening or phase-expanding PR opens (per `AI_WORKFLOW.md` §7), a **catch-up note** must be added under `monitoring/daily/` covering the missed workdays. The catch-up note may be a single file naming the missed workdays and what was or was not changed; it does not need to retroactively fabricate per-day detail that does not exist.
  - Perplexity Computer records the omission in `MASTER_STATUS.md` (the next time §1 or §3 is updated) and confirms the catch-up note exists before verifying the next phase-opening or phase-expanding PR.
  - A missed packet inside a routine governance edit (no phase change) is documented in the next packet but does not block ordinary work.

- **Runtime / live phase.** The severity of a missed packet **must be revisited before live trading can exist**, in the same future ADR that fixes runtime cadence (see D6). This ADR does not authorize live trading and does not pre-decide how strict that rule will be. It only records that the current rule is **not** the right rule once runtime exists.

The point of D5 is to prevent two failure modes: silently dropping packets, and over-reacting by inventing a rollback control for a runtime that does not yet exist.

### D6. Deferred follow-up

The runtime cadence and the runtime missed-packet severity are deferred to a follow-up ADR, to be opened **before** the first PR that introduces runtime (a daemon, broker integration, market data ingestion, paper trading wired to a real broker, or live trading). That follow-up ADR replaces D3's runtime-phase guidance and D5's runtime-phase guidance. It does not retroactively change D3 or D5 for governance-phase history.

This ADR is therefore **complete** for the current phase and **explicitly partial** for the runtime phase.

## Alternatives Considered

- **Make the Backup AI a continuous monitor only, dropping the gate-reviewer mode.** Rejected: the gate-reviewer mode is already useful and is referenced from `AI_WORKFLOW.md` §4; removing it would weaken existing review at phase gates.
- **Make the Backup AI a gate reviewer only, with no continuous mode.** Rejected: it leaves `monitoring/daily/` unowned and turns the daily template into dead documentation.
- **Mandate a daily packet immediately, regardless of repository state.** Rejected: with no runtime, daily packets become low-signal noise that future readers cannot distinguish from real evidence. This also creates a maintenance obligation the project has no realistic ability to meet.
- **Define runtime cadence in this ADR.** Rejected: the runtime context is not yet decided (which broker, what trading day calendar, what timezone discipline applies to "weekday"). Deciding cadence before runtime exists would prematurely lock a control surface. Deferring to a follow-up ADR is consistent with how ADR-002 (kill switch), ADR-003 (reconciliation), and ADR-005 (heartbeat) leave runtime-specific behavior for later.
- **Make missed packets an automatic rollback now.** Rejected: there is no runtime to roll back. The rule would be unenforceable in the current phase and overly strict for governance edits.

## Consequences

- Positive: Future agents have a single reference that names who watches the process and when a packet is required.
- Positive: The Backup AI role is no longer ambiguous between "gate reviewer" and "continuous monitor" — it is both, under explicit conditions.
- Positive: The current phase is not burdened with low-signal daily packets; the rule is defined without backfilling noise.
- Positive: The missed-packet rule is bounded by phase, so it cannot be used to silently weaken future runtime controls.
- Negative: The runtime cadence question is deferred. A follow-up ADR is required before runtime exists; if that ADR is not written, runtime cannot land.
- Risk: An agent could interpret "active workday" loosely and skip packets that should exist. The rule is mitigated by D5's catch-up requirement before the next phase-opening or phase-expanding PR, which makes drift visible at the next gate.

## Implementation Notes

- This ADR adds no runtime code, no source modules, no broker logic, no execution logic, no strategy logic, no market data logic, no order logic, no daemons, no secrets, and no new top-level directories. The `MASTER_STATUS.md` §8 step 4 and §8 step 4c forbidden-category scans are not weakened.
- This ADR does not extend the `MASTER_STATUS.md` §8 step 4a allowlist. P2-01 remains the only authorized Phase 2 implementation task; P2-02 and beyond remain closed.
- This ADR does not modify `daily-report-template.md`. The template's existing `N/A` instruction for Runtime Safety covers the governance-phase case.
- Cross-references added by the companion governance edits:
  - `AI_WORKFLOW.md` §1.4 and §4 reference this ADR for the Mode A / Mode B clarification.
  - `MASTER_STATUS.md` §1, §2, §5, and §9 reference this ADR as the source of the monitoring cadence and missed-packet rule.
  - `README.md` ADR list adds ADR-008.
  - `tests/test_phase1_governance.py` adds this ADR to the required-paths list to keep its existence audit-visible.

## Follow-up Actions

- [ ] Future ADR: define runtime monitoring cadence and missed-packet severity (D6). Owner: whoever opens the first runtime PR. Target phase: before any Phase 2 PR that introduces runtime (daemon, broker integration, market data ingestion, paper or live trading).
- [ ] No retroactive packet backfill. If a packet was due under D3 and is missing, the catch-up note in D5 is the remediation, not fabricated per-day history.

## Related ADRs

- ADR-002: Runtime Kill Switch Architecture (runtime-phase control that D6 must coordinate with).
- ADR-003: Broker Reconciliation Discipline (runtime-phase control that D6 must coordinate with).
- ADR-005: Operator Availability Heartbeat (runtime-phase control that D6 must coordinate with).
- ADR-007: Minimal CI Strategy (the local quality gate stack is unchanged by this ADR).
