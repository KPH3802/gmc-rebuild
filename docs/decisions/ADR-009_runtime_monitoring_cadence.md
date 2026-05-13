# ADR-009: Runtime Monitoring Cadence and Missed-Packet Severity (ADR-008 §D6 Follow-up)

## Status

Proposed

## Date

2026-05-13 UTC

## Context / Problem

ADR-008 (`docs/decisions/ADR-008_monitoring_cadence_and_ai_monitor_role.md`) defines the monitoring cadence and the Backup-AI monitor role for the **current governance / build phase**. ADR-008 §D3 defines cadence by "active workday" (audit-visibly inferred from GitHub-observable events), and ADR-008 §D5 makes a missed packet an audit issue remediable by a catch-up note before the next merge to `main`. ADR-008 §D6 explicitly **defers** the runtime-phase rule:

> The runtime cadence and the runtime missed-packet severity are deferred to a follow-up ADR, to be opened **before** the first PR that introduces runtime (a daemon, broker integration, market data ingestion, paper trading wired to a real broker, or live trading). That follow-up ADR replaces D3's runtime-phase guidance and D5's runtime-phase guidance. It does not retroactively change D3 or D5 for governance-phase history.

This ADR is that follow-up. It is opened in **Proposed** status under `governance/authorizations/2026-05-13_p3-01.md` as candidate task P3-01 per `plan/phase3_entry_plan.md` §4 item 1. Drafting in Proposed status is the first half of the `plan/phase3_entry_plan.md` §5 criterion 5 prerequisite for any future runtime PR; **acceptance** (changing `Status` to `Accepted`) is a separate, future decision that requires its own written authorization from Kevin, a Mode A adversarial review per `AI_WORKFLOW.md` §4(2) and `plan/phase3_entry_plan.md` §7, and a Mode B monitoring packet per ADR-008 §D3 / §D5.

The problem this ADR resolves, **at the policy level only**:

1. **Runtime-phase cadence.** ADR-008 §D3's "active workday" rule is correct for a repository with no runtime, because GitHub-observable events are the only signal that anything happened. Once runtime exists — a daemon, a scheduler, a broker connector, a market-data ingester, a paper or live trading loop wired to a real broker — the "what happened today" signal is no longer GitHub events alone. A repository can be GitHub-quiet on a day the daemon ran, placed orders, lost the broker session, or missed a heartbeat. A cadence rule pinned to GitHub events alone would silently drop those days.
2. **Runtime-phase missed-packet severity.** ADR-008 §D5 explicitly states the governance-phase rule ("audit issue, not an automatic rollback trigger; no runtime to roll back") is the **wrong rule** once runtime exists, and reserves the question for this ADR. A missed packet during live operation is materially different from a missed packet during a governance edit: it can mean nobody noticed the daemon halted, the broker session expired, the kill switch tripped, or the operator-availability heartbeat went stale. Treating it as a quiet audit issue would defeat the point of the packet.
3. **UTC and "runtime day" discipline.** ADR-004 establishes strict UTC throughout the repository. Cadence terms like "every trading day" or "every weekday" need a UTC-anchored definition before runtime exists, otherwise they collapse into ambiguity at daylight-saving transitions, between exchange-local and operator-local timezones, and between weekends-by-calendar and weekends-by-trading-session.
4. **Interaction with Mode A.** ADR-008 §D7 defines the Mode A + Mode B dual-artifact rule for the governance phase. The runtime phase has new Mode A triggers (broker failure modes, kill-switch trips, reconciliation breaks, heartbeat loss) that interact with cadence in ways §D7 did not have to address.

This ADR is a **governance decision only**. It does not introduce runtime code, does not create a daemon, scheduler, automation, notification, or enforcement implementation, does not authorize Phase 3 or any Phase 3 task, does not extend the `MASTER_STATUS.md` §8 step 4a allowlist, and does not change any always-forbidden category in `MASTER_STATUS.md` §6.

## Decision

This ADR is **policy-only**. Every clause below defines the rule a reviewer can apply; none of the clauses authorizes or instructs Codex to write code that implements the rule. The implementation of any rule defined below requires its own separate written authorization from Kevin, a sibling artifact under `governance/authorizations/`, an applicable `MASTER_STATUS.md` §8 step 4a allowlist update where it introduces a directory, and Mode A / Mode B review per ADR-008 and `AI_WORKFLOW.md` §4.

### D1. Scope: when this ADR applies (before runtime vs. after runtime-adjacent work begins)

This ADR's runtime-phase rules apply only **once runtime exists** in the repository. "Runtime" is defined as any of the following landing on `main`:

- a `__main__` entry point or any other long-running service / daemon / scheduler / background worker, including the operator-availability heartbeat daemon described in ADR-005,
- a broker SDK import, broker connector, broker authentication, or any code that talks to a real broker (live or paper),
- a market-data ingester, real data pipeline, or live or historical data feed wired to a real source,
- an order object, order placement, position management, fills, or trade reports,
- a concrete implementation of `KillSwitchProtocol`, `ReconciliationProtocol`, or `HeartbeatProtocol` inside the runtime package (i.e. under `src/gmc_rebuild/risk/`) that talks to a broker, network, filesystem outside the test sandbox, or scheduler,
- a paper-trading workflow wired to a real broker, or a live-trading workflow.

Until **any** of the above first lands on `main`, the **current governance-phase rules in ADR-008 §D3 and §D5 continue to apply unchanged**. ADR-009 does not retroactively reinterpret governance-phase history, does not invalidate any monitoring packet committed under ADR-008 §D3, and does not change ADR-008 §D5's catch-up rule for any governance-phase active workday.

Once **any** runtime item in the list above lands on `main`, ADR-009's runtime-phase cadence (D3 below) and runtime-phase missed-packet severity (D5 below) **replace** ADR-008 §D3's runtime-phase guidance and ADR-008 §D5's runtime-phase guidance, on a going-forward basis. ADR-008 §D6 explicitly anticipates this replacement; ADR-009 does not modify ADR-008 itself and does not require ADR-008 to be amended.

A **runtime-adjacent governance PR** — for example, the Phase 3 entry decision, an ADR update that defines a runtime control surface, or a per-task authorization slice for a future P3-0N implementation — does **not** by itself constitute "runtime exists" under this ADR. Such a governance PR continues to be governed by ADR-008 §D3 / §D5 until the implementation it authorizes lands on `main`. This is intentional: governance prose is not runtime, and treating it as runtime would over-tighten the rule prematurely.

### D2. UTC discipline

All cadence terms, deadlines, timestamps, and audit references in this ADR are **UTC**, consistent with ADR-004 (`docs/decisions/ADR-004_utc_discipline.md`). Specifically:

- A "day" is a UTC calendar day (`YYYY-MM-DD` from `YYYY-MM-DDT00:00:00Z` to `YYYY-MM-DDT23:59:59Z`). No local exchange timezone, no operator-local timezone, no daylight-saving-adjusted timezone may be used as the cadence reference.
- A "weekday" is a UTC weekday (Monday through Friday by `datetime(..., tzinfo=timezone.utc).weekday()`). The UTC weekday may differ from the exchange-local weekday near midnight UTC; this is intentional, because UTC is the auditable reference.
- A "trading day" is defined by reference to a **named, committed** trading-day calendar that lives in the repository as documentation (not as runtime code). Until such a calendar exists, ADR-009 D3 does **not** rely on "trading day" as the cadence reference; it uses UTC weekday plus a published list of UTC dates the calendar marks as closed. Naming the specific calendar (e.g. NYSE half-day handling, holiday list, special-session handling) is **not** in scope for this ADR; that naming is a separate ADR update or a separate committed reference document, authorized in its own PR.
- All timestamps in monitoring packets, runtime logs (when runtime exists), and runtime audit events use the UTC discipline already required by ADR-004 and applied by `src/gmc_rebuild/time/` (`now_utc()` and the timezone-aware parsing / formatting helpers that reject naive datetimes at the API boundary).
- A monitoring packet may include local time as a secondary display field per ADR-004, but the cadence rule itself is evaluated on UTC.

### D3. Runtime-phase cadence (replaces ADR-008 §D3's runtime-phase guidance)

In the runtime phase, cadence is defined by **runtime day**, not by GitHub activity.

**Runtime day definition.** A "runtime day" is a UTC calendar day on which **any** of the following is true:

1. A runtime process (daemon, scheduler, broker connector, market-data ingester, paper or live trading loop, operator-availability heartbeat daemon, kill-switch runtime, reconciliation runtime) **was scheduled to be active for any portion of that UTC day**, per the runtime's own configuration as of `main`. A process is "scheduled to be active" if its committed schedule says it would have run; it does not need to have actually run.
2. A runtime process **did run** for any portion of that UTC day, regardless of whether it was scheduled to.
3. The repository's default branch changed on that UTC day, **or** a pull request was open for review, updated, or merged during that UTC day — i.e. an ADR-008 §D3-style "active workday" event also occurred.

A runtime day that satisfies condition 1 or 2 but not 3 is a **runtime-only day**. A runtime day that satisfies condition 3 but not 1 or 2 is a **governance-only day**. A runtime day that satisfies both is a **combined day**. The three categories have different packet expectations below.

**Packet requirement by runtime-day category.**

- **Combined day or runtime-only day.** A Mode B monitoring packet is required. The packet documents what runtime ran, what runtime did not run, broker session state at end of day (whether the connector was alive, whether reconciliation cleared, whether the operator-availability heartbeat stayed fresh), kill-switch state (tripped / armed / disabled), order activity (count of new orders, filled orders, working orders carried over, rejected orders) at a summary level, and the same governance-side checks ADR-008 §D3 already required for governance-only days. The packet lives at `monitoring/daily/YYYY-MM-DD.md` per ADR-008 §D4, using the existing template at `monitoring/daily/daily-report-template.md`. The Runtime Safety section is filled in (no longer `N/A`).
- **Governance-only day.** ADR-008 §D3 applies unchanged. A packet is required, but the Runtime Safety section stays `N/A` for that day because no runtime ran or was scheduled to run.
- **No-runtime, no-governance-activity day.** No packet is required, consistent with ADR-008 §D3's "active workday" handling for days with no GitHub-observable events.

**Same-day naming.** ADR-008 §D4's same-day naming convention is preserved. The **first** packet on a given UTC date is `YYYY-MM-DD.md`; subsequent packets on the same date are slugged (e.g. `YYYY-MM-DD_<short-slug>.md`). The slug may identify either the PR that triggered the additional packet (governance side) or the runtime event that triggered it (runtime side, e.g. `2026-08-04_reconciliation-break.md`). If multiple distinct runtime events occur on the same UTC day, a single combined packet is preferred over many slugged files; multiple slugged files are reserved for distinct events that materially benefit from separate audit records (kill-switch trip, broker session loss, reconciliation break, missed heartbeat window).

**Trading-day calendar (named separately).** The runtime-day definition above intentionally does **not** require a named trading-day calendar. A future ADR update or a separate committed reference document may add the trading-day calendar as a supplementary cadence rule (e.g. "on a UTC date the trading-day calendar marks as a market session, condition 1 / 2 always applies even if the runtime process did not actually start"). Until that document exists, the three conditions above are the cadence rule.

**Operator-availability interaction.** ADR-005 defines the operator-availability heartbeat policy; its runtime implementation does not yet exist. Once a runtime implementation of ADR-005 lands, "the operator-availability heartbeat daemon was scheduled to be active" is itself a runtime-day-1 condition. A UTC day on which the operator-availability daemon was scheduled but did not run is a runtime-only day and requires a packet — the packet documents the gap, which is itself an audit signal.

### D4. Location and format

ADR-008 §D4 is preserved. Packets continue to live under `monitoring/daily/`, named `YYYY-MM-DD.md` (or slugged for second / subsequent packets on the same UTC date), and use the existing template at `monitoring/daily/daily-report-template.md`. The Runtime Safety section is filled in for combined days and runtime-only days, and stays `N/A` for governance-only days under ADR-008 §D3.

ADR-009 does **not** create a new template, does **not** modify the existing template, does **not** add a new top-level directory, and does **not** add a new packet schema. Any extension of the template to capture runtime-specific fields (kill-switch state, reconciliation status, heartbeat freshness, order activity) is a separate documentation PR authorized in its own right; ADR-009 records the policy expectation, not the schema.

The `monitoring/daily/no-work-days.md` mechanism in ADR-008 §D3 (explicit no-work UTC dates) is preserved for governance-only days. It does **not** apply to runtime-only days: a maintainer cannot mark a runtime-only day as no-work simply because no governance edits happened. The point of D3 is that runtime activity is itself the trigger.

### D5. Runtime-phase missed-packet severity (replaces ADR-008 §D5's runtime-phase guidance)

A missed required packet in the runtime phase has different severity by category. The rule is tightened so a missed runtime packet cannot sit silently.

**Combined day or governance-only day, missed packet.** ADR-008 §D5's governance-phase rule continues to apply: it is an **audit issue**, remediable by a catch-up note at `monitoring/daily/YYYY-MM-DD_catchup.md` written before the next merge to `main`, and again before any phase-opening or phase-expanding PR. The catch-up rule is not relaxed by ADR-009; the runtime portion of a combined day is captured at next-merge level alongside the governance portion.

**Runtime-only day, missed packet.** Severity is tightened. A missed runtime-only-day packet is a **runtime audit issue** that requires both of the following before any further merge to `main` and before the next scheduled runtime session begins:

1. **Catch-up note within 24 UTC hours of the missed day or at the earliest of the next active session, whichever is sooner.** The catch-up note names the missed runtime day, names the runtime processes that ran or were scheduled, reconstructs broker session state, kill-switch state, reconciliation status, heartbeat freshness, and order activity at a summary level from runtime logs and broker reconciliation snapshots, and names what is unknown (gaps in the audit trail are themselves recorded, not papered over). The catch-up note is named `YYYY-MM-DD_catchup.md` (dated for the day the catch-up note is written, not the missed day), consistent with ADR-008 §D5.
2. **Operator acknowledgement** that the gap has been investigated. Operator acknowledgement is recorded in the catch-up note itself (a "Operator Acknowledgement" subsection with a UTC timestamp). This is a documentation requirement, not a runtime control: ADR-009 does not create any automated check, dashboard, paging system, or enforcement mechanism that watches for catch-up notes.

A missed runtime-only-day packet is **not** an automatic rollback trigger by default. It is an audit issue with a tighter deadline and an operator-acknowledgement requirement. ADR-009 leaves the **automatic-rollback question** to runtime-specific ADRs as follows:

- **Kill-switch interaction.** ADR-002 (kill switch) defines the runtime kill-switch policy. If ADR-002 or a future ADR update requires the kill switch to trip on a stale operator-availability heartbeat (per ADR-005), then a missed runtime-only-day packet that coincides with the heartbeat-stale condition is **already** an automatic-rollback condition under ADR-002, independent of ADR-009. ADR-009 does not duplicate that trigger and does not create a parallel rollback path.
- **Reconciliation break.** ADR-003 (reconciliation) defines what happens when broker reconciliation does not clear. A missed runtime-only-day packet on a day with a reconciliation break is a **reconciliation issue** under ADR-003 plus a **packet audit issue** under ADR-009; the reconciliation issue takes precedence and follows ADR-003's escalation, with the packet audit issue tracked via the catch-up note.
- **Heartbeat staleness.** ADR-005 (operator-availability heartbeat) defines what happens when the heartbeat goes stale. A missed runtime-only-day packet on a day with a stale heartbeat is a **heartbeat policy issue** under ADR-005 plus a **packet audit issue** under ADR-009.

**Phase-opening or phase-expanding PR.** ADR-008 §D5's reinforced deadline is preserved: no phase-opening or phase-expanding PR (per `AI_WORKFLOW.md` §7) may merge while any required packet (runtime-only or governance-only) from any prior runtime day is missing without a catch-up note. Perplexity Computer confirms this before verifying a phase-opening or phase-expanding PR.

**Live-trading entry gate.** Once live trading is opened in writing by Kevin in a future authorization, ADR-009 records that **no live-trading session may begin on a UTC day on which a required packet from any prior runtime day is missing without a catch-up note**. This is a documentation-level rule that a future runtime-implementation PR must check at startup; ADR-009 does not create the startup check itself.

**Recording in `MASTER_STATUS.md`.** Perplexity Computer records the omission and its remediation in `MASTER_STATUS.md` §1 (last-updated paragraph) in the same update that records the next merge, consistent with ADR-008 §D5.

### D6. What this ADR does not create

ADR-009 is **governance prose only**. It does **not** create, and **must not** be cited as authorizing the creation of, any of the following:

- A monitoring daemon, scheduler, cron job, background worker, or any long-running process that watches the cadence rule.
- A notification system, paging system, email / SMS / chat / webhook integration, or any external sink that fires when a packet is missing.
- An automated enforcement mechanism, CI check, pre-commit hook, or merge gate that blocks merges on missing packets. ADR-008 §D5's "before the next merge to `main`" rule is enforced by Perplexity Computer's verification step (`AI_WORKFLOW.md` §1.2), not by tooling; ADR-009 preserves that approach.
- A new ADR-008 §D5-style automatic-rollback control. Rollback triggers are governed by ADR-002 (kill switch), ADR-003 (reconciliation), and ADR-005 (heartbeat). ADR-009 records when a missed packet **is** a rollback trigger only by reference to those ADRs.
- A new directory under `src/`, `tests/`, or anywhere else. ADR-009 lives entirely under `docs/decisions/`.
- An extension of the `MASTER_STATUS.md` §8 step 4a allowlist. The allowlist is unchanged by ADR-009.
- A modification of any quality gate, secrets baseline, always-forbidden category, or `MASTER_STATUS.md` §6 entry.
- A specific trading-day calendar binding. D2 explicitly defers the calendar-binding question to a separate document.

ADR-009 is the **rule**. Its implementation (anything that watches the clock, fires a notification, or blocks a merge) requires its own separate written authorization from Kevin, a sibling artifact under `governance/authorizations/`, an applicable allowlist update where it introduces a directory, and Mode A / Mode B review per `AI_WORKFLOW.md` §4 and ADR-008.

### D7. Interaction with Mode A

ADR-008 §D7 defines the Mode A + Mode B dual-artifact rule for the governance phase. ADR-009 preserves §D7 and extends it for the runtime phase as follows:

- **Mode A triggers in the runtime phase.** `AI_WORKFLOW.md` §4 already lists phase gates, high-risk architecture decisions, and safety-critical decisions. In the runtime phase, the following are added as concrete examples (not as new triggers):
  - Any change to the kill-switch behavior, the reconciliation policy, the heartbeat policy, or the secrets-management discipline.
  - Any change to the runtime-day definition in D3, the missed-packet severity in D5, the live-trading entry gate in D5, or any other ADR-009 clause.
  - Any change to a trading-day calendar that the runtime depends on for cadence.
  - Any first wiring of a runtime process to a real broker, a real market-data feed, or a real operator-availability sink.
- **Mode A + Mode B overlap.** When a Mode A trigger fires on a runtime-only day or a combined day, **both** the Mode A written critique (PR-review text, not committed) and the Mode B monitoring packet (committed by Codex under `monitoring/daily/`) are required per ADR-008 §D7. The packet may link to or quote the critique; the critique is not replaced by the packet.
- **Acceptance of ADR-009 itself.** Changing ADR-009's `Status` from `Proposed` to `Accepted` is a Mode A trigger under `AI_WORKFLOW.md` §4(2): it defines a runtime-phase control surface and is non-reversible without a follow-up ADR. The acceptance PR must carry a Mode A written critique and a Mode B monitoring packet for the active workday on which the acceptance PR is open or merged. The acceptance PR is **not** authorized by `governance/authorizations/2026-05-13_p3-01.md` and requires a separate written authorization from Kevin.
- **Mode A is judgment for the drafting PR.** The PR that introduces ADR-009 in Proposed status under `governance/authorizations/2026-05-13_p3-01.md` is governance documentation; the Mode A judgment for that drafting PR is recorded in its own monitoring packet and in `governance/authorizations/2026-05-13_p3-01.md` "Mode A Status". The default is Mode-B-only for the drafting PR (consistent with the PR #26 and PR #28 precedents); Mode A may still be invoked at Kevin's discretion.

## Alternatives Considered

- **Define runtime cadence as "every UTC weekday, unconditionally."** Rejected: a UTC-weekday cadence drops runtime-only weekends (e.g. an automated paper-trading session running over a weekend for testing, or an after-hours reconciliation job), and creates noise packets on UTC weekdays when nothing ran. The runtime-day definition in D3 is the smaller, more accurate rule.
- **Define runtime cadence by trading-day calendar.** Rejected for this ADR: a trading-day calendar is exchange-specific (NYSE, NASDAQ, CME, LSE, etc.), and binding ADR-009 to one calendar before runtime exists prematurely locks the broker / venue choice. D2 defers the calendar binding to a separate document. ADR-009 uses UTC weekday + runtime-process schedule as the cadence reference; a future ADR update may layer a calendar on top.
- **Make missed runtime-only-day packets an automatic rollback.** Rejected: rollback is governed by ADR-002 (kill switch), ADR-003 (reconciliation), and ADR-005 (heartbeat). Creating a parallel rollback control in ADR-009 would duplicate those ADRs, create a new failure mode (rollback-on-missed-packet without a corresponding runtime trigger), and conflict with the principle that ADR-009 is policy-only and does not create runtime mechanisms. The tightened deadline in D5 plus operator acknowledgement is the right severity for a documentation gap.
- **Make missed runtime-only-day packets equivalent to a missed governance-phase packet (ADR-008 §D5 unchanged).** Rejected: ADR-008 §D5 explicitly states the governance-phase rule is the **wrong** rule once runtime exists. Treating a missed runtime-only-day packet identically to a missed governance-phase packet ignores that a runtime gap can mean nobody noticed the daemon halted, the broker session expired, or the heartbeat went stale.
- **Create a monitoring daemon to enforce cadence.** Rejected: ADR-009 is governance prose, not runtime. Creating a daemon would invert the relationship (the rule would become the implementation rather than the discipline) and would itself require ADR-002 / ADR-003 / ADR-005 alignment, a separate authorization, and its own monitoring rule. D6 explicitly forbids this within ADR-009's scope.
- **Skip operator acknowledgement on missed runtime-only-day packets.** Rejected: a missed runtime-only-day packet is silent by definition (no one was watching, by hypothesis). Without an explicit acknowledgement record, the audit trail cannot show that anyone investigated the gap.
- **Bind cadence to a single named exchange timezone (e.g. America/New_York) instead of UTC.** Rejected: violates ADR-004's UTC discipline. Local-time cadence is fragile around daylight-saving transitions and varies by exchange. UTC is the auditable reference; local time is at most a secondary display field per ADR-004.
- **Accept ADR-009 in this drafting PR.** Rejected: acceptance is a runtime-phase control-surface decision and a high-risk architecture decision under `AI_WORKFLOW.md` §4(2). `governance/authorizations/2026-05-13_p3-01.md` authorizes drafting only. Acceptance requires a separate written authorization from Kevin, Mode A adversarial review, and a Mode B monitoring packet for the acceptance PR's active workday.

## Consequences

- Positive: Future agents and reviewers have a single policy reference for runtime-phase cadence and runtime-phase missed-packet severity, written **before** the first runtime PR can land. This satisfies the ADR-008 §D6 hard precondition for any Phase 3 PR that introduces runtime (subject to acceptance in a future PR).
- Positive: The runtime-day definition in D3 is auditable from the runtime's own committed schedule, runtime logs, and reconciliation snapshots, not from maintainer recollection. A reviewer can reconstruct which UTC dates were runtime days without asking the operator.
- Positive: The catch-up rule in D5 preserves ADR-008 §D5's structure (catch-up notes, dated for the day the note is written, allowed to consolidate, before-next-merge deadline). The runtime-phase tightening is additive (24-UTC-hour deadline and operator acknowledgement) rather than a rewrite, so the governance-phase audit pattern carries forward unchanged.
- Positive: ADR-009 explicitly does **not** invent a new rollback control. Rollback remains governed by ADR-002, ADR-003, and ADR-005. Missed packets are documentation gaps; the runtime control surfaces are the runtime control surfaces.
- Positive: The Mode A interaction in D7 names concrete runtime-phase examples that a reviewer can match against, reducing the ambiguity about when a runtime PR triggers Mode A.
- Positive: D2's deferral of the trading-day calendar binding keeps the broker / venue choice open. ADR-009 can be accepted before the calendar is named, and the calendar binding can be a separate ADR update.
- Negative: ADR-009 in Proposed status is not yet a precondition satisfied for any runtime PR. Acceptance is a separate decision; until ADR-009 is Accepted on `main`, the runtime-phase rule is **stated** but not **in force**.
- Negative: The runtime-day definition in D3 requires a "committed schedule" for each runtime process. Until each runtime process has a committed schedule, condition 1 cannot apply and the cadence rule depends on conditions 2 (process actually ran) and 3 (governance activity). This is intentional but may produce edge cases when a new runtime process lands without an associated schedule document; those edge cases are caught at the runtime PR's own review.
- Negative: Operator acknowledgement in D5 is a manual documentation step. It can be skipped by a forgetful operator; the catch-up-before-next-merge deadline in ADR-008 §D5 is the backstop, but the operator-acknowledgement gap is itself an audit signal.
- Risk: A maintainer could over-narrow the runtime-day definition in D3 ("the daemon was not scheduled today, so no packet needed") to avoid writing packets during slow weeks. Mitigation: condition 3 (governance activity) still triggers a packet, and the daemon's committed schedule lives in the repository and is reviewable.
- Risk: A maintainer could under-narrow the runtime-day definition in D3 (e.g. claim every UTC weekday is a runtime day even when no runtime is scheduled) and produce noise packets. Mitigation: noise packets are still better than missed packets; the daily template's Runtime Safety section captures "no runtime activity" cleanly, and the maintainer can consolidate slow weeks into a single weekly note rather than per-day noise, subject to ADR-008 §D4 same-day naming.
- Risk: A future reviewer reads ADR-009 in Proposed status and assumes the rule is in force. Mitigation: the Status field is `Proposed`, this Context section and D1 are explicit that acceptance is a separate decision, and `plan/phase3_entry_plan.md` §5 criterion 5 names "merged on `main` in Accepted status" as the precondition for any runtime PR.

## Implementation Notes

- This ADR adds no runtime code, no source modules, no daemons, no schedulers, no notification systems, no broker logic, no execution logic, no strategy logic, no market data logic, no order logic, no secrets, no env-var loading, and no new top-level directories. The `MASTER_STATUS.md` §8 step 4 and §8 step 4c forbidden-category scans are not weakened. The §8 step 4a allowlist is not extended.
- This ADR does not modify `daily-report-template.md`, `daily-report-template.md`'s Runtime Safety section, or `no-work-days.md`. Any extension of the template to capture runtime-specific fields is a separate documentation PR.
- This ADR does not modify ADR-008. ADR-008 §D3, §D5, and §D7 continue to apply unchanged for the governance phase. ADR-008 §D6 anticipated this follow-up ADR; the follow-up replaces ADR-008 §D3's runtime-phase guidance and ADR-008 §D5's runtime-phase guidance on a going-forward basis once runtime exists, without amending ADR-008.
- UTC examples in this ADR should follow ADR-004:
  ```python
  from datetime import datetime, timezone

  now_utc = datetime.now(timezone.utc)
  ```
  Stored timestamps in monitoring packets and runtime logs (when runtime exists) use `YYYY-MM-DDTHH:MM:SSZ` or a clearly documented equivalent UTC format.
- Cross-references made by the companion governance edits in the drafting PR for this ADR:
  - `README.md` adds a separate "Proposed ADRs (drafted, not yet accepted)" subsection naming ADR-009 in Proposed status, kept distinct from the "Accepted ADRs:" list so ADR-009 is not misread as accepted.
  - `docs/decisions/ADR-008_monitoring_cadence_and_ai_monitor_role.md` "Follow-up Actions" first entry gains a parenthetical note pointing to ADR-009 in Proposed status. The checkbox **remains unchecked** because acceptance of ADR-009 is still pending; drafting in Proposed status does not close the §D6 follow-up action. ADR-008's Decision sections (D3, D5, D6, D7) are **not** modified.
  - No `MASTER_STATUS.md` edit is made by the drafting PR (per `AI_WORKFLOW.md` §1.2 / §6 rule 2: status keeper is Perplexity Computer; the drafting PR is governance documentation only).
  - No file under `src/**` or `tests/**` is modified by the drafting PR.
- Acceptance of this ADR (changing `Status` to `Accepted`) is reserved for a future PR. That acceptance PR requires its own separate written authorization from Kevin per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 / rule 7, a sibling artifact under `governance/authorizations/`, Mode A adversarial review per `AI_WORKFLOW.md` §4(2) and `plan/phase3_entry_plan.md` §7, and a Mode B monitoring packet per ADR-008 §D3 / §D5. Acceptance does **not** by itself open Phase 3; opening Phase 3 is a separate phase-gate decision (candidate task P3-02 in `plan/phase3_entry_plan.md` §4 item 2).

## Follow-up Actions

- [ ] **Acceptance PR for ADR-009.** Future, separate written authorization from Kevin; Mode A adversarial review; Mode B monitoring packet for the acceptance PR's active workday. Owner: whoever drafts the acceptance PR. Target phase: before any Phase 3 PR that introduces runtime can open, per `plan/phase3_entry_plan.md` §5 criterion 5.
- [ ] **Trading-day calendar reference.** Separate documentation PR (or ADR update) that names the specific trading-day calendar ADR-009 D2 defers. Required only when a runtime PR depends on the calendar for cadence; not required for ADR-009 acceptance.
- [ ] **Daily template Runtime Safety section.** Optional separate documentation PR that extends `monitoring/daily/daily-report-template.md`'s Runtime Safety section to capture runtime-specific fields (kill-switch state, reconciliation status, heartbeat freshness, order activity at a summary level). Not required for ADR-009 acceptance.
- [ ] **No retroactive packet backfill.** Once ADR-009 is Accepted and runtime exists, the catch-up note in D5 is the remediation for any missed runtime-only-day packet, not fabricated per-day history. This is the same discipline as ADR-008 §D5.

## Related ADRs

- ADR-001: Secrets Management Strategy — runtime-phase control that ADR-009 D7 names as a Mode A trigger for any change.
- ADR-002: Runtime Kill Switch Architecture — runtime-phase control that ADR-009 D5 cross-references for the automatic-rollback interaction.
- ADR-003: Broker Reconciliation Discipline — runtime-phase control that ADR-009 D5 cross-references for the reconciliation-break interaction.
- ADR-004: UTC and Timezone Discipline — ADR-009 D2's UTC discipline derives from ADR-004; all cadence terms are UTC.
- ADR-005: Operator Availability Heartbeat — runtime-phase control that ADR-009 D3 (runtime-day condition 1) and D5 (heartbeat staleness interaction) cross-reference.
- ADR-006: Deployment and Rollback Logs — not modified by ADR-009; deployment-log discipline continues to apply unchanged to runtime PRs.
- ADR-007: Minimal CI Strategy — not modified by ADR-009; the local quality-gate stack is unchanged.
- ADR-008: Monitoring Cadence and Backup-AI Monitor Role — the ADR this is a follow-up to. ADR-008 §D6 explicitly defers the runtime-phase rule to this ADR. ADR-009 D3 / D5 replace ADR-008 §D3 / §D5's runtime-phase guidance on a going-forward basis once runtime exists; ADR-008 itself is **not** modified by ADR-009.
