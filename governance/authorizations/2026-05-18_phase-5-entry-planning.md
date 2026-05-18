# Phase 5 Entry Planning Authorization

Date: 2026-05-18
Authorizer: Kevin
Scope: Phase 5 **entry planning / enumeration only** — bounded docs/governance-only scope (**does not open any successor P5 task, does not authorize any P5-05 or later implementation, does not authorize any simulation expansion, does not authorize any order semantics change, does not authorize any runtime activation, does not authorize any ops execution work, does not extend any allowlist, does not relax any quality gate, does not promote X10 Layer 5, does not automate backup-monitoring, and does not execute any DR drill**)

## Authorization

The user authorization for this packet is reproduced below verbatim. Per `AI_WORKFLOW.md` §7 the verbatim block in this file is the authorization of record.

> I authorize a bounded docs/governance-only Phase 5 planning packet for gmc-rebuild on 2026-05-18.
>
> Scope:
> - Add or update Phase 5 planning documentation, including a new plan/phase5_entry_plan.md if appropriate.
> - Enumerate the current post-P5-04 state.
> - Identify P5-05 only as future / not authorized.
> - Record that any P5-05 implementation, simulation expansion, order semantics change, runtime activation, or ops execution work requires separate written authorization.
>
> Constraints:
> - No src/** changes.
> - No tests/** changes.
> - No runtime activation.
> - No broker, paper-trading, live-trading, market-data, order-routing, strategy, scheduler, daemon, persistence, deployment, env-var, secrets, network, tag, or release changes.
> - No allowlist expansion.
> - No quality-gate relaxation.
> - No X10 Layer 5 promotion.
> - No backup-monitoring automation or DR drill execution.
>
> Governance:
> - This is planning/enumeration only.
> - Mode B sibling monitoring must be created from main and merged before the planning PR.
> - Mode A adversarial review is not independently required unless maintainer-elected.
> - The planning PR must preserve the reconciled canonical status established by PR #114 and must not reintroduce stale pending-merge language.
>
> Authorized by Kevin on 2026-05-18.

This authorization is the **planning / enumeration analogue** to `governance/authorizations/2026-05-14_phase-4-entry-planning.md` (Phase 4 entry planning) and to `governance/authorizations/2026-05-13_phase-3-entry-planning.md` (Phase 3 entry planning). It is intentionally narrower than each of those: it does **not** name any successor P5 implementation task, it does **not** extend the `MASTER_STATUS.md` §8 step 4a `allowed_p2_infra` allowlist (preserved exactly at the ten entries synced by GOV-01), it does **not** add or modify any file under `src/**` or `tests/**`, and it does **not** open or pre-approve any P5-05 / P4-09 / OPS-05 / OPS-07 / future ops work or any runtime activation of any merged Phase 3 fixture, P4-06 / P4-07 / P4-08 safety surface, or P5-01 / P5-02 simulation surface.

The canonical status reconciliation merged via PR #114 (`a02f17c`) and its sibling Mode B PR #115 (`75d6f28`) is preserved in full by this authorization. This planning packet must not reintroduce stale `**pending merge**` language for the already-merged P5-01 / P5-02 / P5-03 / P5-04 status reflection paragraphs in `MASTER_STATUS.md`. The reconciled canonical statuses (P5-01 merged via PR #104 at `76e5986`; P5-02 merged via PR #107 at `76335f9`; P5-03 merged via PR #110 at `e8e652b`; P5-04 merged via PR #112 at `a9d85ec`) are factual and not modified by this packet.

## Scope

The work authorized by this artifact is restricted to:

- This authorization artifact at `governance/authorizations/2026-05-18_phase-5-entry-planning.md`.
- A new Phase 5 entry plan at `plan/phase5_entry_plan.md`, modeled on `plan/phase4_entry_plan.md` but minimal and precise. It enumerates the post-P5-04 state at the planning level only, names P5-05 (and any later P5-0N task) as **future / not authorized**, and records that any P5-05 implementation, any simulation expansion (additional `SimulationLane` member, additional `SimulatedOrderSide` member, additional `SimulatedOrderType` member, additional `SimulatedOrderIntent` field, additional `SimulationBoundary` method), any order semantics change, any runtime activation, or any ops execution work (X10 Layer 5 promotion, backup-monitoring automation, DR drill execution, etc.) requires its own separate written authorization from Kevin per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 / rule 7.
- Conservative governance-prose cross-reference updates to `MASTER_STATUS.md` and `README.md` that record that Phase 5 entry planning has been authorized (planning only; no P5-05 or later implementation authorized; no runtime activation authorized; no allowlist expansion). The updates name this artifact, do not relax any boundary, do not change the §8 step 4a allowlist, and do not declare any successor P5 task open. Per `AI_WORKFLOW.md` §1.2 and §6 rule 2 ("One status keeper"), any `MASTER_STATUS.md` or `README.md` edit in this PR is conservative and remains subject to Perplexity Computer's verification before being treated as the canonical status. The edits must not reintroduce stale `**pending merge**` language for the merged P5-01 / P5-02 / P5-03 / P5-04 paragraphs.

The §8 step 4a `allowed_p2_infra` allowlist is **not** extended by this authorization or by the planning document opened under it. It continues to contain exactly the ten entries on `main` as synced by GOV-01 (`src`, `src/gmc_rebuild/config`, `src/gmc_rebuild/time`, `src/gmc_rebuild/logging`, `src/gmc_rebuild/risk`, `src/gmc_rebuild/heartbeat`, `src/gmc_rebuild/kill_switch`, `src/gmc_rebuild/reconciliation`, `src/gmc_rebuild/runtime`, `src/gmc_rebuild/simulation`). Any future P5-05 / P4-09 / … directory addition requires a separate written authorization that introduces the directory in the same PR that adds it to the allowlist (per the standing rule in `MASTER_STATUS.md` §8 step 4b).

## Allowed Planning Topics

While Phase 5 entry planning is opened by this authorization, Codex and Perplexity Computer may draft planning artifacts on the following topics. Planning artifacts are documents, not code, and must be reviewable as documents.

1. **Current post-P5-04 state in prose.** What has been merged on `main` through PR #114 (canonical status reconciliation) — the merged P2-01..P2-05 packages, the merged P3-03 / P3-04 / P3-05 in-memory fakes, the merged P4-01 governance entry / P4-02 / P4-03 / P4-04 / P4-05 composed tests / P4-06 inert runtime shell / P4-07 read-only operator view / P4-08 safety-policy-hardening tests, the merged OPS-01 / OPS-02 / OPS-03 / OPS-04 / OPS-04B / OPS-06 operations records, the merged GOV-01 governance reconciliation, and the merged P5-01 inert simulation boundary skeleton / P5-02 simulated order intent model / P5-03 invariants tripwires / P5-04 composed safety-foundation × simulation integration tripwires — restated at a level that does not authorize any specific implementation and does not authorize any runtime activation.
2. **Naming P5-05 (and any later P5-0N task) only as future / not authorized.** Naming the task in the plan does **not** authorize it; the shape of any P5-05 task remains a decision Kevin must make in writing at the time of P5-05 authorization. The plan must not pre-commit any P5-05 shape (no specific test file, no specific module, no specific field, no specific method, no specific simulation lane, no specific order side / type member).
3. **Phase 5 entry criteria.** What must be true (baseline, governance, ADRs, monitoring cadence under ADR-008 §D3 / §D5 during the governance phase and ADR-009 D3 / D5 once runtime exists on `main` per ADR-009 D7's bootstrap-avoidance clause, Mode A / Mode B review per `AI_WORKFLOW.md` §4) before any future P5-05 implementation PR could open.
4. **Per-PR proof-bundle expectations for any future P5-05 PR.** Restated from `AI_WORKFLOW.md` §3 and `plan/phase4_entry_plan.md` §6.
5. **Rollback and stop conditions.** Restated for Phase 5 from `plan/phase4_entry_plan.md` §8.
6. **Phase-boundary enforcement.** How any future P5-05 PR would prove it did not cross into broker execution, paper-trading wired to a real broker, live trading wired to a real broker, real market data ingestion, real order routing, real strategy logic, real scheduler / daemon, real persistence, real deployment, real env-var loading, real secrets, real network, allowlist expansion beyond what its own authorization names, quality-gate relaxation, X10 Layer 5 promotion, backup-monitoring automation, or DR drill execution.
7. **ADR follow-ups.** Restated from `plan/phase4_entry_plan.md` §9 for Phase 5 scope.

Any planning topic that does not fit the list above must be raised with Kevin before a document is written, per `AI_WORKFLOW.md` §6 rule 7 ("No phase drift").

## Explicitly Not Authorized

The authorization above does not permit, by implication or otherwise, any of the following. Each remains forbidden until Kevin records a separate written authorization per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 ("One approver") / rule 7 ("No phase drift"), with a sibling artifact under `governance/authorizations/` and (where it introduces a new directory) a corresponding update to the §8 step 4a allowlist in the same PR that introduces the directory:

- **Any P5-05 implementation.** P5-05 (and any later P5-0N task) is future / not authorized. The shape of P5-05 is a decision Kevin must make in writing at the time of P5-05 authorization.
- **Any simulation expansion.** No additional `SimulationLane` member beyond `LOCAL_ONLY`. No additional `SimulatedOrderSide` member beyond `BUY` / `SELL`. No additional `SimulatedOrderType` member beyond `MARKET` / `LIMIT`. No ninth field on `SimulatedOrderIntent`. No additional method on `SimulationBoundary` beyond the merged `propose` (P5-01) and `propose_order` (P5-02). No additional placeholder / order record class. No new public name on `gmc_rebuild.simulation`.
- **Any order semantics change.** No change to the meaning of `propose` or `propose_order`, no change to the `SafetyVerdict.clear` precondition, no change to the identity-return contract, no addition of side effects.
- **Any runtime activation.** No `__main__` entry point, no daemon, no scheduler, no background worker, no long-running service, no live execution loop, no re-export of any merged Phase 3 fixture (`InMemoryHeartbeat`, `InMemoryKillSwitch`, `InMemoryReconciliation`) from `src/gmc_rebuild/__init__.py` or any other runtime path, no consumption of any merged Phase 3 fixture from a `__main__`, a daemon, a scheduler, or any runtime path.
- **Any ops execution work.** No X10 Layer 5 promotion. No backup-monitoring automation (the OPS-06 plan remains rules and thresholds only; the periodic execution remains an operator-side action). No DR drill execution. No OPS-05 / OPS-07 opening. No change to any Backblaze / Time Machine / drive / FileVault / sleep / power / USB / network / macOS setting.
- **Broker integration.** No broker SDK, no broker connector, no broker reconciliation runtime, no broker authentication, no broker credentials.
- **Paper-trading wired to a real broker.** No paper-broker connector, no paper-account identifier, no paper-API surface, no paper-trading execution loop.
- **Live-trading.** No live-broker connector, no live-account identifier, no live-API surface, no live-trading execution loop.
- **Market-data integration.** No market-data ingestion code, no market-data pipeline, no committed dataset, no live / delayed / paper data feed.
- **Order-routing.** No order routing logic, no venue selection, no execution adapter, no FIX session, no REST client, no WebSocket client.
- **Strategy logic.** No trading signals, no scanners, no models, no portfolio rules, no backtests.
- **Scheduling.** No cron-style scheduler, no APScheduler, no background-job framework, no operator-heartbeat daemon, no kill-switch runtime, no reconciliation runtime.
- **Daemon.** No daemon, no `__main__` entry, no background thread, no long-running service.
- **Persistence.** No SQLite, no on-disk database, no on-disk reconciliation snapshot, no on-disk heartbeat state, no log sink, no file artifact written by runtime code.
- **Deployment.** No deployment workflow, no rollout, no rollback runtime, no CI/CD pipeline change beyond the existing local pre-commit and pytest gates.
- **Env-var loading.** No `os.environ` / `os.getenv` reads, no `.env` files in the repo.
- **Secrets.** No real secrets, no real credentials, no real account identifiers, no real broker / venue identifiers, no real endpoints embedded anywhere in the repository under this authorization.
- **Network.** No `socket`, no `urllib`, no `requests`, no `http`, no `ssl`, no `smtplib`, no `ftplib`, no outbound or inbound network code.
- **Tag.** No git tag.
- **Release.** No GitHub release, no version bump.
- **Allowlist expansion.** The `allowed_p2_infra` allowlist is **not** extended by this authorization or by the planning document opened under it. It remains exactly the ten entries on `main` as synced by GOV-01.
- **Quality-gate relaxation.** No weakening of pre-commit, Ruff, mypy strict mode, `detect-secrets`, `.gitignore`, `.secrets.baseline`, the `MASTER_STATUS.md` §8 step 4 always-forbidden scan, the §8 step 4a per-PR allowlist scan, or the §8 step 4c recursive forbidden-token scan.
- **Source / test changes.** No file under `src/**` or `tests/**` is modified or created by this planning authorization or by the planning document opened under it. Planning documents live under `governance/`, `plan/`, `docs/`, `MASTER_STATUS.md`, or `README.md`.
- **Reintroduction of stale "pending merge" language.** The canonical status reconciliation merged via PR #114 corrected the four P5-01 / P5-02 / P5-03 / P5-04 status reflection paragraphs to `**merged on \`main\`**`. The planning PR must preserve those corrections. The planning PR may, where it carefully scopes its own pending state (the planning PR itself is pending merge before it merges), describe that pending state without reintroducing stale claims about the already-merged P5-01 / P5-02 / P5-03 / P5-04 / GOV-01 / OPS-06 packets.
- **Mode A / Mode B substitution.** This authorization is governance prose, not a control-surface decision; it does not substitute for adversarial review of any future P5-05 implementation PR or any future runtime / broker / market-data / order / strategy / scheduler / persistence / deployment PR. Any such future PR must independently satisfy `AI_WORKFLOW.md` §4 (Mode A) and ADR-008 / ADR-009 (Mode B) as applicable.

The always-forbidden categories in `MASTER_STATUS.md` §6 and `plan/phase4_entry_plan.md` §10 — strategy code, broker execution code, live or paper trading wired to a real broker, runtime daemons affecting accounts, real market data ingestion, order placement, real secrets, network calls — remain forbidden in all modes. This authorization does not relax them and does not record any relaxation. The mirroring above is intentional and is not a re-authorization of any category: those categories remain forbidden by default, and naming them here records that Kevin did not silently relax them when authorizing Phase 5 entry **planning**.

## Preserved Gates for Any Future P5-05 / Successor P5 Work

Any work beyond this planning authorization — any P5-05 implementation, any simulation expansion, any order semantics change, any runtime activation, any ops execution work, or any runtime / broker / market-data / order / strategy / scheduler / persistence / deployment work — requires **all** of the following, none of which is satisfied by this planning authorization:

1. **Separate written authorization from Kevin** per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 ("One approver") / rule 7 ("No phase drift"), with a sibling artifact under `governance/authorizations/`.
2. **Runtime-cadence ADR follow-up where applicable.** ADR-008 §D3 / §D5 continue to govern the governance phase, and ADR-009 D3 / D5 will replace them on a going-forward basis once runtime exists on `main` per ADR-009 D7's bootstrap-avoidance clause. Any runtime work must satisfy the ADR-009 D3 / D5 cadence as it takes effect, plus any further ADR follow-up that surfaces at the time of authorization.
3. **Mode A adversarial review where applicable.** `AI_WORKFLOW.md` §4 reserves Mode A for phase gates, new control surfaces, new trust boundaries, non-reversible decisions, and safety-critical decisions. Any first runtime activation of any merged Phase 3 fixture is a new control surface under §4(2); any first connection of the simulation boundary to a real broker, real market data feed, real order router, or real persistence layer is a new control surface and a non-reversible decision under §4(2) / §4(3). Each future P5-05 / successor P5 PR must independently satisfy the applicable Mode A requirement at the time of authorization.
4. **Mode B monitoring packet where required.** ADR-008 §D3 / §D5 (and ADR-009 D3 / D5 once in force) requires a monitoring packet on any active workday on which the default branch changes or a pull request is open, updated, or merged. This planning-authorization PR itself triggers ADR-008 §D3 and a Mode B packet under `monitoring/daily/` is required per the existing cadence rule; that packet is committed under Codex's authorship per `AI_WORKFLOW.md` §1.4 and §6 rule 1, and is produced as a separate change from `main`, not bundled into this authorization PR.
5. **§8 step 4a allowlist updates in the same PR.** Any new authorized directory must be added to `allowed_p2_infra` (and the matching comment block / verification-script case arm) in the same PR that introduces the directory, per the standing rule in `MASTER_STATUS.md` §8 step 4b.

## Mode A Status For This Authorization

This planning-authorization PR is governance / documentation only and does **not** introduce a runtime control surface, a new trust boundary, or a non-reversible decision. It does not itself open any successor P5 task. By the precedent of `governance/authorizations/2026-05-13_phase-3-entry-planning.md` and `governance/authorizations/2026-05-14_phase-4-entry-planning.md` (both treated under `AI_WORKFLOW.md` §4's routine-exclusion sentence at the time), and per the verbatim authorization above ("Mode A adversarial review is not independently required unless maintainer-elected"), Mode A adversarial review is **not independently mandated** for this planning-only authorization.

If Kevin elects to invoke Mode A on this PR, the Mode A critique is delivered as PR-review text and is **not** committed to the repository, per `AI_WORKFLOW.md` §6 rule 5. The Mode A status for this PR is therefore: **maintainer-elected only; not independently mandated.** Any future P5-05 implementation PR remains subject to Mode A per `AI_WORKFLOW.md` §4(2) as applicable, independent of this planning authorization.

## Exit Criteria

This planning-authorization PR may merge only after:

- The sibling Mode B monitoring packet for the active workday is authored from `main` and merged to `main` **before** this planning PR merges, per the verbatim authorization above ("Mode B sibling monitoring must be created from main and merged before the planning PR") and ADR-008 §D5.
- `pytest` is green on the branch (the planning PR does not modify `src/**` or `tests/**`, so the existing 370 tests are expected to remain green).
- `pre-commit run --all-files` is clean, or every failure is documented as pre-existing and environment-only.
- Diff-scope verification confirms changes are confined to `governance/authorizations/2026-05-18_phase-5-entry-planning.md` (new), `plan/phase5_entry_plan.md` (new), and conservative governance/status reflections in `MASTER_STATUS.md` and `README.md`. No file under `src/**` or `tests/**` is added or modified; the §8 step 4a allowlist is unchanged at ten entries.
- The canonical status reconciliation merged via PR #114 is preserved: the four P5-01 / P5-02 / P5-03 / P5-04 status reflection paragraphs in `MASTER_STATUS.md` continue to read `**merged on \`main\`**` and not `**pending merge**`.

After this authorization merges, the next allowed decisions remain those listed in `MASTER_STATUS.md` §9, augmented by the planning workstream described in "Allowed Planning Topics" above. No successor P5 task (P5-05 and beyond) is opened by this authorization; any future P5-05 implementation, any simulation expansion, any order semantics change, any runtime activation, or any ops execution work requires its own separate written authorization per the preserved gates above.

## Supporting Evidence (Non-Authoritative)

The following are pointers to the surrounding governance record. They are evidence, not the authorization itself; this file is the authorization of record for Phase 5 entry **planning**.

- Phase 1 accepted baseline: `1f101fc` (`MASTER_STATUS.md` §3).
- Phase 2 closure authorization: `governance/authorizations/2026-05-12_phase-2-closure.md`.
- Phase 3 entry planning authorization (pattern reference for this planning authorization): `governance/authorizations/2026-05-13_phase-3-entry-planning.md`.
- Phase 3 closure authorization: `governance/authorizations/2026-05-14_phase-3-closure.md`.
- Phase 4 entry planning authorization (pattern reference for this planning authorization): `governance/authorizations/2026-05-14_phase-4-entry-planning.md`.
- Phase 4 entry plan (pattern reference for `plan/phase5_entry_plan.md`): `plan/phase4_entry_plan.md`.
- P5-01 authorization: `governance/authorizations/2026-05-17_p5-01.md` — merged via PR #104 at `76e5986`.
- P5-02 authorization: `governance/authorizations/2026-05-17_p5-02.md` — merged via PR #107 at `76335f9`.
- P5-03 authorization: `governance/authorizations/2026-05-17_p5-03.md` — merged via PR #110 at `e8e652b`.
- P5-04 authorization: `governance/authorizations/2026-05-17_p5-04.md` — merged via PR #112 at `a9d85ec`.
- GOV-01 governance reconciliation authorization: `governance/authorizations/2026-05-17_gov-01.md` — merged via PR #106 at `4df8074`.
- OPS-06 backup monitoring plan authorization: `governance/authorizations/2026-05-17_ops-06.md` — recorded in `RECOVERY.md` §17.
- Canonical status reconciliation (P5-01..P5-04 / OPS-06): PR #114 at `a02f17c`, with sibling Mode B PR #115 at `75d6f28`.
- ADR-008 (governance-phase monitoring cadence): `docs/decisions/ADR-008_monitoring_cadence_and_ai_monitor_role.md` §D3 / §D5.
- ADR-009 (runtime-phase monitoring cadence): `docs/decisions/ADR-009_runtime_monitoring_cadence.md` — Accepted on 2026-05-13; D7 bootstrap-avoidance clause keeps ADR-008 §D3 / §D5 in force until runtime exists on `main`.
- Workflow separation of duties: `AI_WORKFLOW.md` §1 (roles), §2 (standard workflow), §3 (required proof), §4 (when to use the Backup AI), §6 (anti-chaos rules), §7 (durable authorization artifacts).
