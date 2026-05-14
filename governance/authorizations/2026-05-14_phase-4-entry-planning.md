# Phase 4 Entry Planning Authorization

Date: 2026-05-14
Authorizer: Kevin
Scope: Phase 4 **entry planning only** — governance / documentation scope (**does not open Phase 4, does not authorize any Phase 4 implementation, does not authorize any runtime activation of any merged Phase 3 fixture, does not extend any allowlist**)

## Authorization

I authorize opening **Phase 4 entry planning** for the Grist Mill Capital rebuild. This authorization is governance-only and **documentation-only**. It records that Codex and Perplexity Computer may begin to plan the entry to Phase 4 in writing, on the same pattern previously used to plan the entry to Phase 2 via `plan/phase2_entry_plan.md` and the entry to Phase 3 via `plan/phase3_entry_plan.md` (the latter opened by `governance/authorizations/2026-05-13_phase-3-entry-planning.md`).

This authorization is the **planning analogue** to the Phase 3 entry planning authorization at `governance/authorizations/2026-05-13_phase-3-entry-planning.md` and to the formal Phase 3 closure recorded at `governance/authorizations/2026-05-14_phase-3-closure.md`. It is intentionally narrower than each of those: it does **not** name a specific Phase 4 task, it does **not** extend the `MASTER_STATUS.md` §8 step 4a `allowed_p2_infra` allowlist, it does **not** add any directory or path to the working tree under `src/**` or `tests/**`, and it does **not** open or pre-approve any Phase 4 implementation work or any runtime activation of any merged Phase 3 fixture.

The closure of Phase 3 at `governance/authorizations/2026-05-14_phase-3-closure.md` (merged on `main` as of 2026-05-14 via PR #56 at `3131a69`, with sibling Mode B packet PR #57 merged first at `302dff6`, and post-merge status reconciliation PR #58 merged at `0a91261` with sibling Mode B packet PR #59 merged first at `c910c9a`) explicitly stated that Phase 3 closure does **not** open Phase 4. That statement is unchanged by this authorization. This authorization opens **only** the planning workstream that any future Phase 4 entry decision would have to descend from.

## Scope

The work authorized by this artifact is restricted to:

- This authorization artifact at `governance/authorizations/2026-05-14_phase-4-entry-planning.md`.
- Minimal governance-prose cross-reference updates to `MASTER_STATUS.md` §9 and `README.md` that record that Phase 4 entry planning has been authorized (planning only; no Phase 4 implementation authorized; no runtime activation authorized). The updates name this artifact, do not relax any boundary, do not change the §8 step 4a allowlist, and do not declare Phase 4 open. Per `AI_WORKFLOW.md` §1.2 and §6 rule 2 ("One status keeper"), any `MASTER_STATUS.md` edit in the authorizing PR is conservative and remains subject to Perplexity Computer's verification before being treated as the canonical status.
- A **planning document** for Phase 4 entry at `plan/phase4_entry_plan.md` (modeled on the existing `plan/phase3_entry_plan.md`) may be opened under this authorization in the same PR or in a separate planning PR. That document is **planning-only**: it does not implement Phase 4, does not authorize any P4-0N task, does not authorize any runtime activation of any merged Phase 3 fixture, does not extend the §8 step 4a allowlist, does not modify `src/**` or `tests/**`, and does not modify any quality gate. It is treated, like `plan/phase3_entry_plan.md` was at its creation, as a document under `AI_WORKFLOW.md` §6 rule 7 ("No phase drift"): planning content only, with phase opening still gated on a later, separate written authorization from Kevin.

The §8 step 4a `allowed_p2_infra` allowlist is **not** extended by this authorization or by any future planning document opened under it. It continues to contain exactly the eight entries currently on `main` after the merged P2-01..P2-05 + P3-03 + P3-04 + P3-05 sequence (`src`, `src/gmc_rebuild/config`, `src/gmc_rebuild/time`, `src/gmc_rebuild/logging`, `src/gmc_rebuild/risk`, `src/gmc_rebuild/heartbeat`, `src/gmc_rebuild/kill_switch`, `src/gmc_rebuild/reconciliation`). Any Phase 4 directory, including the eventual on-disk location of any Phase 4 module, requires a separate written authorization that introduces the directory in the same PR that adds it to the allowlist (per the standing rule in `MASTER_STATUS.md` §8 step 4b).

## Allowed Planning Topics

While Phase 4 entry planning is in this opened-but-unscoped state, Codex and Perplexity Computer may draft planning artifacts on the following topics. Planning artifacts are documents, not code, and must be reviewable as documents. The list mirrors `plan/phase3_entry_plan.md` §3 and `governance/authorizations/2026-05-13_phase-3-entry-planning.md` "Allowed Planning Topics" deliberately so the pattern is the same and is reviewable on the same axes:

1. The Phase 4 objective in prose: what step Phase 4 would build on top of the merged P2-01..P2-05 + P3-03 + P3-04 + P3-05 foundation (the three in-memory single-protocol test fixtures plus the abstract `typing.Protocol` definitions in `src/gmc_rebuild/risk/`), restated at a level that does not authorize any specific implementation and does not authorize any runtime activation of any merged Phase 3 fixture.
2. Proposed Phase 4 task sequence (`P4-01`, `P4-02`, …) named only as **future** PRs that would each require their own separate written authorization slice and sibling artifact under `governance/authorizations/`. Naming a task in the plan does not authorize it.
3. Phase 4 entry criteria — what must be true (baseline, governance, ADRs, monitoring cadence under ADR-008 §D3 / §D5 during the governance phase and ADR-009 D3 / D5 once runtime exists on `main` per ADR-009 D7's bootstrap-avoidance clause, Mode A / Mode B review per `AI_WORKFLOW.md` §4) before any Phase 4 implementation PR could open.
4. Per-PR proof-bundle expectations for any future Phase 4 PR (restated from `AI_WORKFLOW.md` §3 and `plan/phase3_entry_plan.md` §6, adjusted for Phase 4 scope where the ADRs require it).
5. Rollback and stop conditions, restated for Phase 4 from `plan/phase3_entry_plan.md` §8.
6. Phase-boundary enforcement — how Phase 4 PRs would prove they did not cross into trading strategy, broker execution, live or paper trading wired to a real broker, real market data ingestion, real secrets, or any other always-forbidden category in `MASTER_STATUS.md` §6.
7. ADR follow-ups that Phase 4 entry would require — at minimum any ADR-009 implications that surface at the time of Phase 4 authorization, plus any kill-switch (ADR-002), reconciliation (ADR-003), heartbeat (ADR-005), secrets-management (ADR-001), deployment-log (ADR-006), and minimal-CI (ADR-007) implications that any further phase would have to address before opening.

Any planning topic that does not fit the list above must be raised with Kevin before a document is written.

## Explicitly Not Authorized

The authorization above does not permit, by implication or otherwise, any of the following. Each remains forbidden until Kevin records a separate written authorization per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 ("One approver") / rule 7 ("No phase drift"), with a sibling artifact under `governance/authorizations/` and (where it introduces a new directory) a corresponding update to the §8 step 4a allowlist in the same PR that introduces the directory:

- **Opening Phase 4.** This authorization opens **planning** of Phase 4 entry, not Phase 4 itself. No Phase 4 task is opened, no Phase 4 directory is created, no Phase 4 module lands, and no Phase 4 PR may merge under this authorization. Opening Phase 4 requires a separate written authorization from Kevin and is itself a phase gate per `AI_WORKFLOW.md` §4(1).
- **Runtime activation of any merged Phase 3 fixture.** The `InMemoryHeartbeat` (P3-03), `InMemoryKillSwitch` (P3-04), and `InMemoryReconciliation` (P3-05) fakes remain test-fixture infrastructure only. No re-export from `src/gmc_rebuild/__init__.py`, no consumption from a `__main__`, no consumption from a daemon, no consumption from a scheduler, no consumption from any runtime path is authorized.
- **Any new Phase 3 task beyond P3-05.** The three in-memory protocol-conformance test fixtures (P3-03 HeartbeatProtocol, P3-04 KillSwitchProtocol, P3-05 ReconciliationProtocol) are exhausted; no fourth protocol fixture, no P3-06, and no sibling Phase 3 task is opened by this planning authorization. Phase 3 is formally closed.
- **Any new Phase 2 task beyond P2-05.** The `plan/phase2_entry_plan.md` §4 P2-01..P2-05 sequence is exhausted and Phase 2 is formally closed (`governance/authorizations/2026-05-12_phase-2-closure.md`). No P2-06 or sibling Phase 2 task is opened by this planning authorization.
- **Runtime work of any kind.** No `__main__` entry point, no daemon, no scheduler, no background worker, no long-running service, no live execution loop is authorized, planned-into-existence, or pre-approved by this authorization.
- **Broker integration.** No broker SDK, no broker connector, no broker reconciliation runtime, no broker authentication, no broker credentials.
- **Market-data integration.** No market-data ingestion code, no market-data pipeline, no committed dataset, no live or historical data feed.
- **Order management.** No order objects, no order placement, no position management, no fills, no trade reports, no executions, no order book.
- **Strategy logic.** No trading signals, no scanners, no models, no portfolio rules, no backtests.
- **Scheduling.** No cron-style scheduler, no APScheduler, no background-job framework, no operator-heartbeat daemon, no kill-switch runtime, no reconciliation runtime.
- **Persistence.** No SQLite, no on-disk database, no on-disk reconciliation snapshot, no on-disk heartbeat state, no log sink, no file artifact written by runtime code.
- **Deployment.** No deployment workflow, no rollout, no rollback runtime, no CI/CD pipeline beyond the existing local pre-commit and pytest gates.
- **Secrets / env-var loading.** No real secrets, no real credentials, no `.env` files, no `os.environ` / `os.getenv` reads, no real account identifiers, no real broker / venue identifiers, no real endpoints embedded anywhere in the repository under this authorization. ADR-001's secrets-management discipline is not relaxed.
- **Network.** No `socket`, no `urllib`, no `requests`, no HTTP client, no outbound or inbound network code under this authorization.
- **Concrete risk implementations inside the runtime package.** No concrete implementation of `KillSwitchProtocol` / `ReconciliationProtocol` / `HeartbeatProtocol` lands inside `src/gmc_rebuild/risk/` under this authorization. The P2-05 boundary (`src/gmc_rebuild/risk/` is types and abstract `typing.Protocol` definitions only) is preserved, and the three merged P3-03 / P3-04 / P3-05 fakes remain test-fixture-only outside `src/gmc_rebuild/risk/`.
- **New trading behavior.** No change that introduces, simulates, or wires up trading behavior — in any module, under any name, anywhere in the tree.
- **Tooling relaxation.** No weakening of pre-commit, Ruff, mypy strict mode, `detect-secrets`, `.gitignore`, `.secrets.baseline`, the `MASTER_STATUS.md` §8 step 4 always-forbidden scan, the §8 step 4a per-PR Phase 2 / Phase 3 infrastructure allowlist scan, or the §8 step 4c recursive forbidden-token scan.
- **§8 step 4a allowlist expansion.** The `allowed_p2_infra` allowlist is **not** extended by this authorization or by any future planning document opened under it. It remains exactly the eight entries on `main` after the merged P2-01..P2-05 + P3-03 + P3-04 + P3-05 sequence. Any future addition requires a separate written authorization that names a specific implementation task, a sibling artifact under `governance/authorizations/`, and an allowlist update made in the same PR that introduces the new directory.
- **Source / test changes.** No file under `src/**` or `tests/**` is modified or created by the authorizing PR for this artifact, nor by any planning document opened under it. Planning documents live under `governance/`, `plan/`, `docs/`, or `README.md`.
- **New tags or releases.** No git tag, no GitHub release, no version bump is created by this authorization or its PR.
- **Mode A / Mode B substitution.** This authorization is governance prose, not a control-surface decision; it does not substitute for adversarial review of any future Phase 4 entry decision or any future runtime / broker / market-data / order / strategy / scheduler / persistence / deployment PR. Any such future PR must independently satisfy `AI_WORKFLOW.md` §4 (Mode A) and ADR-008 / ADR-009 (Mode B) as applicable. Opening Phase 4 will itself be a phase-gate decision under `AI_WORKFLOW.md` §4(1) and will require Mode A adversarial review at that time.

The always-forbidden categories in `MASTER_STATUS.md` §6 and `plan/phase3_entry_plan.md` §10 — strategy code, broker execution code, live or paper trading wired to a real broker, runtime daemons affecting accounts, real market data ingestion, order placement, and real secrets — remain forbidden in all modes. This authorization does not relax them and does not record any relaxation. The mirroring above is intentional and is not a re-authorization of any category: those categories remain forbidden by default, and naming them here records that Kevin did not silently relax them when authorizing Phase 4 entry **planning**.

## Preserved Gates for Any Future Phase 4 Work

Any work beyond this planning authorization — Phase 4 entry itself, any specific Phase 4 task (`P4-01`, `P4-02`, …), any runtime activation of any merged Phase 3 fixture, or any runtime / broker / market-data / order / strategy / scheduler / persistence / deployment work — requires **all** of the following, none of which is satisfied by this planning authorization:

1. **Separate written authorization from Kevin** per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 ("One approver") / rule 7 ("No phase drift"), with a sibling artifact under `governance/authorizations/`.
2. **Runtime-cadence ADR follow-up where applicable.** ADR-008 §D6 has been closed by ADR-009 (accepted under `governance/authorizations/2026-05-13_p3-01-acceptance.md`). ADR-008 §D3 / §D5 continue to govern the governance phase, and ADR-009 D3 / D5 will replace them on a going-forward basis once runtime exists on `main` per ADR-009 D7's bootstrap-avoidance clause. Any runtime work must satisfy the ADR-009 D3 / D5 cadence as it takes effect, plus any further ADR follow-up that surfaces at the time of authorization.
3. **Mode A adversarial review.** `AI_WORKFLOW.md` §4 reserves Mode A for phase gates, new control surfaces, new trust boundaries, non-reversible decisions, and safety-critical decisions. Opening Phase 4 is a phase gate by definition under §4(1); any first runtime activation of any merged Phase 3 fixture is also a new control surface under §4(2). The Phase 4 entry decision (when proposed) must carry a Mode A adversarial critique before merge.
4. **Mode B monitoring packet where required.** ADR-008 §D3 / §D5 (and ADR-009 D3 / D5 once in force) requires a monitoring packet on any active workday on which the default branch changes or a pull request is open, updated, or merged. This planning-authorization PR itself triggers ADR-008 §D3 and a Mode B packet under `monitoring/daily/` is required per the existing cadence rule; that packet is committed under Codex's authorship per `AI_WORKFLOW.md` §1.4 and §6 rule 1, and is produced as a separate change, not bundled into this authorization PR.
5. **§8 step 4a allowlist updates in the same PR.** Any new authorized directory must be added to `allowed_p2_infra` (and the matching comment block) in the same PR that introduces the directory, per the standing rule in `MASTER_STATUS.md` §8 step 4b.

## Mode A Status For This Authorization

This planning-authorization PR is governance / documentation only and does **not** introduce a runtime control surface, a new trust boundary, or a non-reversible decision. It does not itself open Phase 4. By the precedent of `governance/authorizations/2026-05-13_phase-3-entry-planning.md` (the Phase 3 entry planning authorization, which was treated under `AI_WORKFLOW.md` §4's routine-exclusion sentence at that time), Mode A adversarial review is **not independently mandated** by `AI_WORKFLOW.md` §4(1) (phase gate) or §4(2) (high-risk architecture decision) for this planning-only authorization.

However, because this authorization is **phase-gate-adjacent** (it is the planning workstream from which any future Phase 4 entry decision would descend), Kevin may elect to invoke Mode A on this PR. If Kevin elects to do so, the Mode A critique is delivered as PR-review text and is **not** committed to the repository, per `AI_WORKFLOW.md` §6 rule 5. The Mode A status for this PR is therefore: **maintainer-elected only; not independently mandated.** Opening Phase 4 itself, when proposed, **will** independently require Mode A per `AI_WORKFLOW.md` §4(1).

## Exit Criteria

This planning-authorization PR may merge only after the full required check suite passes on the planning-authorization branch:

- `pre-commit run --all-files` (clean, or every failure documented).
- `pytest` (clean, or every failure documented as pre-existing and environment-only).
- `MASTER_STATUS.md` §8 step 3 (baseline ancestry from `1f101fc`).
- `MASTER_STATUS.md` §8 step 4 (always-forbidden scan).
- `MASTER_STATUS.md` §8 step 4a (per-PR Phase 2 / Phase 3 infrastructure allowlist scan; allowlist is unchanged at exactly eight entries).
- `MASTER_STATUS.md` §8 step 4c (recursive forbidden-token scan; subshell exit `0`).
- A sibling Mode B monitoring packet for the active workday on which this planning-authorization PR is open / merged has been authored by the Backup AI per ADR-008 §D1, committed by Codex per ADR-008 §D4, and merged to `main` **before** this planning-authorization PR merges per ADR-008 §D5.

After this authorization merges, the next allowed decisions remain those listed in `MASTER_STATUS.md` §9, augmented by the narrow planning workstream described in "Allowed Planning Topics" above. Phase 4 is **not** opened; Phase 3 remains formally closed; Phase 2 remains formally closed; no new Phase 2 task beyond P2-05 is opened; no new Phase 3 task beyond P3-05 is opened; no Phase 4 task is opened; no runtime activation of any merged Phase 3 fixture is authorized. Any subsequent step — including the eventual Phase 4 entry decision PR — requires its own separate written authorization per the preserved gates above.

## Supporting Evidence (Non-Authoritative)

The following are pointers to the surrounding governance record. They are evidence, not the authorization itself; this file is the authorization of record for Phase 4 entry **planning**.

- Phase 1 accepted baseline: `1f101fc` (`MASTER_STATUS.md` §3).
- Phase 2 closure authorization: `governance/authorizations/2026-05-12_phase-2-closure.md`.
- Phase 3 entry planning authorization (pattern reference for this planning authorization): `governance/authorizations/2026-05-13_phase-3-entry-planning.md`.
- Phase 3 entry plan (pattern reference for `plan/phase4_entry_plan.md`): `plan/phase3_entry_plan.md`.
- Phase 3 closure authorization: `governance/authorizations/2026-05-14_phase-3-closure.md` — merged on `main` via PR #56 at `3131a69`, with sibling Mode B packet PR #57 merged first at `302dff6`.
- Phase 3 closure post-merge status reconciliation: PR #58 merged on `main` at `0a91261`, with sibling Mode B packet PR #59 merged first at `c910c9a`.
- ADR-009 (runtime monitoring cadence): `docs/decisions/ADR-009_runtime_monitoring_cadence.md` — Accepted under `governance/authorizations/2026-05-13_p3-01-acceptance.md`; D7 bootstrap-avoidance clause keeps ADR-008 §D3 / §D5 in force until runtime exists on `main`.
- Monitoring cadence rule that governs the sibling Mode B packet for this PR: `docs/decisions/ADR-008_monitoring_cadence_and_ai_monitor_role.md` §D3 / §D5.
