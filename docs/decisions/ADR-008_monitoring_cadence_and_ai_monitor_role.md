# ADR-008: Monitoring Cadence and Backup-AI Monitor Role

## Status

Accepted

## Date

2026-05-11 UTC

## Context / Problem

Phase 1 verification surfaced an ambiguity that `AI_WORKFLOW.md` and `MASTER_STATUS.md` did not resolve on their own:

1. **Role ambiguity.** The backup / adversarial AI is defined in `AI_WORKFLOW.md` §1.4 and §4 as an optional adversarial reviewer used at phase gates, high-risk architecture decisions, and safety-critical decisions. It is not defined as a continuous monitor. `monitoring/daily/daily-report-template.md` implies a continuous monitoring cadence exists, but does not say who is responsible for it or when packets are due.
2. **Cadence ambiguity.** The daily monitoring template implies a daily packet, but the repository currently has no runtime, no live trading, no market data ingestion, no broker integration, and no runtime implementing the operator availability heartbeat defined in ADR-005. A literal "daily" cadence in this state would generate noise packets that future readers cannot distinguish from real evidence and that the project has no realistic ability to maintain.
3. **Missed-packet ambiguity.** Neither `AI_WORKFLOW.md` nor `MASTER_STATUS.md` says what happens when a required monitoring packet is missing. Without a stated rule, missed packets either become silent (defeating the point) or trigger ad-hoc rollback responses (over-correcting against a control that does not exist yet).

This ADR resolves all three questions in one place so future agents and reviewers have a single reference. It is a governance decision only. It does not authorize Phase 2 work beyond the already-authorized P2-01, does not introduce runtime code, and does not change any always-forbidden category in `MASTER_STATUS.md` §6.

## Decision

### D1. Roles and the safety boundary on what the Backup AI may write

The four roles in `AI_WORKFLOW.md` §1 stand unchanged: Codex (Builder), Perplexity Computer (Supervisor / Verifier / Status Keeper), Kevin (Approver), and the Backup AI (Adversarial Reviewer). This ADR clarifies that the Backup AI has **two distinct modes** with independent triggers:

- **Mode A — Gate Reviewer (existing).** Invoked per `AI_WORKFLOW.md` §4 at phase gates, high-risk architecture decisions, and safety-critical decisions. Produces a written critique only. Does not build. Does not decide. Does not produce any file under version control.
- **Mode B — Continuous Governance Monitor (clarified by this ADR).** Once the cadence rule in D3 fires, the Backup AI **authors the text** of a monitoring packet (reading the working tree and recent PR activity) for the path in D4. The packet is **committed to the repository by Codex**, never by the Backup AI directly. The Backup AI does not push, merge, or commit on its own in either mode.

The **safety boundary** is the same in both modes: the Backup AI never writes code, source files, configuration, trading logic, broker logic, strategy logic, execution logic, daemon logic, market-data logic, order logic, secrets, or governance decisions (ADRs, `AI_WORKFLOW.md`, `MASTER_STATUS.md`, plans, README, tests, tooling). Mode B's "authoring packet text" is the **only** content the Backup AI may produce that lands in the working tree, and Codex still owns the commit. `AI_WORKFLOW.md` §6 rule 1 ("One builder at a time") is preserved: Codex is still the only role that writes to the repo.

Mode A and Mode B are independent. Mode A can fire without Mode B (e.g., a critique requested on an external-facing plan that never lands as a commit). Mode B can fire without Mode A (e.g., a routine governance documentation PR that triggers D3 but is not a Section 4 trigger). Both can fire on the same PR — see D7 below.

### D2. Monitoring packets are governance artifacts, not runtime evidence

Until runtime exists in the repository (no Phase 2 daemon, no broker integration, no live trading, no real market data ingestion, no runtime implementation of the ADR-005 operator availability heartbeat — see `MASTER_STATUS.md` §6), a monitoring packet is a governance artifact that documents repository state, phase compliance, and PR activity. It is not runtime evidence and must not claim to be. The Runtime Safety section of the daily template stays `N/A` in this state, as the template already instructs.

Once runtime exists, monitoring packets become runtime evidence as well. The semantics shift is governed by a follow-up ADR (see D6).

### D3. Cadence

Cadence is defined by phase, not by calendar.

- **Governance / build phase (current state).** A packet is required on any **active workday** on which **either** of the following is true:
  - The repository state changes on the default branch (any merge to `main`), **or**
  - A pull request is open for review, updated, or merged during that workday.

  An **active workday** is defined externally and audit-visibly so the rule does not depend on the maintainer's recollection: an active workday is any UTC calendar date on which **at least one** of the following GitHub-observable events is attributable to a maintainer on this repository:

  - a commit lands on `main` (committer or author timestamp in UTC),
  - a pull request is opened, updated (new commits pushed), reviewed, commented on, or merged,
  - an issue is opened or commented on as part of repository work.

  A UTC date with **none** of the above events is not an active workday under this ADR and does not require a packet. A maintainer may also explicitly mark a UTC date as a documented no-work day by adding a one-line entry to `monitoring/daily/no-work-days.md` (creating the file on first use); explicitly documented no-work days override the inference above and never require a packet. Using `git log` and `gh pr list` (or equivalent) a reviewer can reconstruct the list of active workdays without asking the maintainer.

  The packet documents what changed and what did not change; it is not a heartbeat against wall-clock time.

- **Runtime / live phase (future, not authorized here).** Cadence may become **every trading day** or **every weekday** depending on what runtime is active. The specific cadence for that phase is **deferred to a follow-up ADR** (see D6) and is not decided by this ADR. Until that ADR exists, the runtime cadence question is unresolved and live trading remains forbidden by `MASTER_STATUS.md` §6 independent of cadence.

This ADR explicitly does **not** mandate a daily packet during the current phase. The intent is to define the rule, not to backfill packets.

### D4. Location and format

- All monitoring packets live under `monitoring/daily/` and are named `YYYY-MM-DD.md` (UTC date).
- The packet uses the existing template at `monitoring/daily/daily-report-template.md`. The template is not modified by this ADR.
- **Same-day naming convention.** The **first** packet on a given UTC date is named `YYYY-MM-DD.md` (no slug), regardless of which event triggered it. Any **second or subsequent** packet on the same UTC date is named `YYYY-MM-DD_<short-slug>.md`, with the short slug describing the trigger (e.g. `2026-05-11_pr-9.md`). The first packet is never renamed retroactively. If a maintainer cannot decide whether a second packet is warranted, prefer appending to the first packet over creating a slugged second file.
- **Template-only edits** (changes to `daily-report-template.md` itself, or to `no-work-days.md`) do not require a packet under D3 because they do not change `main` state outside `monitoring/` and do not constitute a workday of substantive activity. Substantive governance PRs do require a packet under D3.
- **Self-trigger handling for the PR that adopts this ADR.** The PR that introduces this ADR is itself an active-workday event under D3 (it is an open governance PR and, when merged, will change `main`). To avoid an impossible self-trigger loop where the rule requires a packet that documents the rule that requires the packet, the first packet under D3 may be created **either** inside the PR that introduces the rule **or** as a follow-up packet committed before the next merge to `main`. For PR #9 (the PR that adopts ADR-008), the chosen path is **follow-up**: the first packet is committed after PR #9 merges, dated for the active workday on which PR #9 was open or merged, and before any subsequent merge to `main`.

### D5. Missed-packet handling

A missed required packet is treated by phase. The rule is tightened so a missed packet cannot sit indefinitely.

- **Governance / build phase.** A missed packet is an **audit issue**, not an automatic rollback trigger. There is no runtime to roll back. The catch-up rule has two parts:

  1. **Hard deadline — before the next merge to `main`.** If a required packet for a past active workday is missing when the next PR is ready to merge, a catch-up note must be added under `monitoring/daily/` **before that merge**. The catch-up note is named `YYYY-MM-DD_catchup.md` (dated for the day the catch-up note is written, not the missed day) and names the missed workdays and what was or was not changed. The catch-up note may consolidate multiple missed workdays into one file; it does not need to retroactively fabricate per-day detail that does not exist.
  2. **Reinforced deadline — before any phase-opening or phase-expanding PR.** Independent of (1), no phase-opening or phase-expanding PR (per `AI_WORKFLOW.md` §7) may merge while any required packet from any prior active workday is missing without a catch-up note covering it. Perplexity Computer confirms this before verifying a phase-opening or phase-expanding PR.

  Once a catch-up note exists for a given missed workday, that workday is considered remediated and does not re-trigger D5 for subsequent merges.

  Perplexity Computer records the omission and its remediation in `MASTER_STATUS.md` §1 (last-updated paragraph) in the same update that records the next merge. Recording in §3 is reserved for baseline changes and is not used for missed-packet tracking; §1 is where active drift surfaces.

  A missed packet inside a routine governance edit is **not** waived; it is remediated at the next-merge hard deadline above.

- **Runtime / live phase.** The severity of a missed packet **must be revisited before live trading can exist**, in the same follow-up ADR that fixes runtime cadence (see D6). This ADR does not authorize live trading and does not pre-decide how strict that rule will be. It only records that the current rule is **not** the right rule once runtime exists.

The point of D5 is to prevent two failure modes: silently dropping packets, and over-reacting by inventing a rollback control for a runtime that does not yet exist.

### D6. Deferred follow-up

The runtime cadence and the runtime missed-packet severity are deferred to a follow-up ADR, to be opened **before** the first PR that introduces runtime (a daemon, broker integration, market data ingestion, paper trading wired to a real broker, or live trading). That follow-up ADR replaces D3's runtime-phase guidance and D5's runtime-phase guidance. It does not retroactively change D3 or D5 for governance-phase history.

This ADR is therefore **complete** for the current phase and **explicitly partial** for the runtime phase.

### D7. Overlap between Mode A and Mode B on the same PR

When a PR triggers both Mode A (it is a phase gate, high-risk architecture decision, or safety-critical decision per `AI_WORKFLOW.md` §4) **and** Mode B (it meets the D3 conditions on an active workday), **both artifacts are required**:

1. The **Mode A written critique**, delivered to Kevin and Codex as a review. The critique is **not** committed to the repository; it lives in PR-review comments or in a session log per `AI_WORKFLOW.md` §6 rule 5.
2. The **Mode B monitoring packet**, committed by Codex under `monitoring/daily/` per D4.

The packet **may link to or quote** the critique to give the dated artifact context. The packet does **not** replace the critique: the critique is the adversarial review of the specific decision, the packet is the dated governance record of the workday. Producing only one of the two when both are required is a `AI_WORKFLOW.md` §6 rule 9 ("Every claim has evidence") failure.

A single artifact may satisfy both **only** if it explicitly contains a clearly-labeled Mode A critique section (specific failure modes, invariant cites) **and** the Mode B packet fields (the template's metadata, phase compliance, repository hygiene, UTC audit, issues, evidence links, sign-off). The default expectation is two artifacts; a combined artifact is the exception and must be explicit.

## Alternatives Considered

- **Make the Backup AI a continuous monitor only, dropping the gate-reviewer mode.** Rejected: the gate-reviewer mode is already useful and is referenced from `AI_WORKFLOW.md` §4; removing it would weaken existing review at phase gates.
- **Make the Backup AI a gate reviewer only, with no continuous mode.** Rejected: it leaves `monitoring/daily/` unowned and turns the daily template into dead documentation.
- **Mandate a daily packet immediately, regardless of repository state.** Rejected: with no runtime, daily packets become low-signal noise that future readers cannot distinguish from real evidence. This also creates a maintenance obligation the project has no realistic ability to meet.
- **Let the Backup AI commit packets directly.** Rejected: this would require carving out a "Backup AI writes" exception to `AI_WORKFLOW.md` §6 rule 1 ("One builder at a time"). Routing packets through Codex preserves the rule and keeps a single role responsible for commits.
- **Define "active workday" only by maintainer intent.** Rejected: an unfalsifiable rule lets any missing packet be retroactively excused. Tying the definition to GitHub-observable events makes the rule auditable from `git log` + `gh pr list` alone.
- **Define runtime cadence in this ADR.** Rejected: the runtime context is not yet decided (which broker, what trading day calendar, what timezone discipline applies to "weekday"). Deciding cadence before runtime exists would prematurely lock a control surface. Deferring to a follow-up ADR is consistent with how ADR-002 (kill switch), ADR-003 (reconciliation), and ADR-005 (operator availability heartbeat) leave runtime-specific behavior for later.
- **Make missed packets an automatic rollback now.** Rejected: there is no runtime to roll back. The rule would be unenforceable in the current phase and overly strict for governance edits.

## Consequences

- Positive: Future agents have a single reference that names who watches the process, when a packet is required, and what counts as evidence that a packet should have existed.
- Positive: The Backup AI role is no longer ambiguous between "gate reviewer" and "continuous monitor" — it is both, under explicit conditions, and the safety boundary on what it may write is preserved.
- Positive: The current phase is not burdened with low-signal daily packets; the rule is defined without backfilling noise.
- Positive: "Active workday" is defined by observable events, so a reviewer can audit compliance without asking the maintainer.
- Positive: Missed-packet drift is bounded by the next merge to `main`, not just the next phase gate, so drift cannot sit indefinitely.
- Positive: The missed-packet rule is bounded by phase, so it cannot be used to silently weaken future runtime controls.
- Negative: The runtime cadence question is deferred. A follow-up ADR is required before runtime exists; if that ADR is not written, runtime cannot land.
- Negative: A maintainer who works on the repository without producing any GitHub-observable event (e.g., reading only) has a UTC date that does not count as an active workday under D3. This is intentional — silent reading does not need a governance packet — but is worth flagging.
- Risk: A maintainer could selectively mark UTC days as no-work in `monitoring/daily/no-work-days.md` to dodge packets. Mitigation: the no-work-days file is part of the working tree, is reviewed at every PR, and contradicts itself if a packet later proves the day was an active workday after all.

## Implementation Notes

- This ADR adds no runtime code, no source modules, no broker logic, no execution logic, no strategy logic, no market data logic, no order logic, no daemons, no secrets, and no new top-level directories. The `MASTER_STATUS.md` §8 step 4 and §8 step 4c forbidden-category scans are not weakened.
- This ADR does not extend the `MASTER_STATUS.md` §8 step 4a allowlist. P2-01 remains the only authorized Phase 2 implementation task; P2-02 and beyond remain closed.
- This ADR does not modify `daily-report-template.md`. The template's existing `N/A` instruction for Runtime Safety covers the governance-phase case.
- `monitoring/daily/no-work-days.md` is **not** created by this PR. It is created on first use when a maintainer first needs to document a no-work UTC date. Its absence means no UTC dates have been explicitly marked.
- Cross-references made by the companion governance edits in the PR that adopts this ADR:
  - `AI_WORKFLOW.md` §1.4, §4 (including the new Overlap subsection), and §6 rule 1 reference this ADR for the Mode A / Mode B clarification and the safety boundary on what the Backup AI may write.
  - `MASTER_STATUS.md` §1 (last-updated paragraph and a new monitoring paragraph), §5 (artifact list), and §9 (next allowed decisions, split into two items) reference this ADR. §2's "Source of Truth" priority list is **not** modified by this PR: §2 already includes `docs/decisions/ADR-*.md` as the source-of-truth entry for ADRs (item 5), so ADR-008 is covered without a new entry. A future PR may revisit §2 if a top-level governance ADR ever needs to be elevated above other ADRs, but that is not in scope here.
  - `README.md` ADR list adds ADR-008. The list heading is renamed from "Accepted Phase 1 ADRs" to "Accepted ADRs" because ADR-008 was written after Phase 2 opened at P2-01 and sits cross-phase.
  - `tests/test_phase1_governance.py` is extended to assert ADR-008 exists and contains the Mode A / Mode B language, with per-path assertion messages so a deletion is diagnosed clearly.

## Follow-up Actions

- [ ] Future ADR: define runtime monitoring cadence and missed-packet severity (D6). Owner: whoever opens the first runtime PR. Target phase: before any Phase 2 PR that introduces runtime (daemon, broker integration, market data ingestion, paper or live trading). *(Drafted in **Proposed** status as `docs/decisions/ADR-009_runtime_monitoring_cadence.md` under `governance/authorizations/2026-05-13_p3-01.md`; acceptance remains pending and requires separate written authorization from Kevin plus Mode A adversarial review per `AI_WORKFLOW.md` §4(2). This follow-up action is **not** closed until ADR-009 is Accepted.)*
- [ ] No retroactive packet backfill. If a packet was due under D3 and is missing, the catch-up note in D5 is the remediation, not fabricated per-day history.
- [ ] First D3 packet for PR #9 (the PR that adopts this ADR): committed as a follow-up under `monitoring/daily/` before the next merge to `main` after PR #9, per D4.

## Related ADRs

- ADR-002: Runtime Kill Switch Architecture (runtime-phase control that D6 must coordinate with).
- ADR-003: Broker Reconciliation Discipline (runtime-phase control that D6 must coordinate with).
- ADR-005: Operator Availability Heartbeat (runtime-phase control that D6 must coordinate with; ADR-005 defines the policy, the runtime that implements it does not yet exist).
- ADR-007: Minimal CI Strategy (the local quality gate stack is unchanged by this ADR).
