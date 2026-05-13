# Phase 3 Entry Planning Authorization

Date: 2026-05-13
Authorizer: Kevin
Scope: Phase 3 **entry planning only** — governance / documentation scope (**does not open Phase 3, does not authorize any Phase 3 implementation, does not extend any allowlist**)

## Authorization

I authorize opening **Phase 3 entry planning** for the Grist Mill Capital rebuild. This authorization is governance-only and **documentation-only**. It records that Codex and Perplexity Computer may begin to plan the entry to Phase 3 in writing, on the same pattern previously used to plan the entry to Phase 2 via `plan/phase2_entry_plan.md`.

This authorization is the **planning analogue** to the P2-03 / P2-04 / P2-05 governance-only authorization slices and to the formal Phase 2 closure recorded at `governance/authorizations/2026-05-12_phase-2-closure.md`. It is intentionally narrower than each of those: it does **not** name a specific Phase 3 task, it does **not** extend the `MASTER_STATUS.md` §8 step 4a `allowed_p2_infra` allowlist, it does **not** add any directory or path to the working tree under `src/**` or `tests/**`, and it does **not** open or pre-approve any Phase 3 implementation work.

The closure of Phase 2 at `governance/authorizations/2026-05-12_phase-2-closure.md` explicitly stated that Phase 2 closure does **not** open Phase 3. That statement is unchanged by this authorization. This authorization opens **only** the planning workstream that any future Phase 3 entry decision would have to descend from.

## Scope

The work authorized by this artifact is restricted to:

- This authorization artifact at `governance/authorizations/2026-05-13_phase-3-entry-planning.md`.
- Minimal governance-prose cross-reference updates to `MASTER_STATUS.md` §9 and `README.md` that record that Phase 3 entry planning has been authorized (planning only; no Phase 3 implementation authorized). The updates name this artifact, do not relax any boundary, do not change the §8 step 4a allowlist, and do not declare Phase 3 open. Per `AI_WORKFLOW.md` §1.2 and §6 rule 2 ("One status keeper"), any `MASTER_STATUS.md` edit in the authorizing PR is conservative and remains subject to Perplexity Computer's verification before being treated as the canonical status.
- A future, separate **planning document** for Phase 3 entry (modeled on the existing `plan/phase2_entry_plan.md`) may be opened under this authorization in a **separate** PR. That document, when opened, is **planning-only**: it does not implement Phase 3, does not authorize any Phase 2-style P3-0N task, does not extend the §8 step 4a allowlist, does not modify `src/**` or `tests/**`, and does not modify any quality gate. It is treated, like `plan/phase2_entry_plan.md` was at its creation, as a document under `AI_WORKFLOW.md` §6 rule 7 ("No phase drift"): planning content only, with phase opening still gated on a later, separate written authorization from Kevin.

The §8 step 4a `allowed_p2_infra` allowlist is **not** extended by this authorization or by any future planning document opened under it. It continues to contain exactly the five P2-01..P2-05 entries authorized in writing previously (`src`, `src/gmc_rebuild/config`, `src/gmc_rebuild/time`, `src/gmc_rebuild/logging`, `src/gmc_rebuild/risk`). Any Phase 3 directory, including the eventual on-disk location of any Phase 3 module, requires a separate written authorization that introduces the directory in the same PR that adds it to the allowlist (per the standing rule in `MASTER_STATUS.md` §8 step 4b).

## Allowed Planning Topics

While Phase 3 entry planning is in this opened-but-unscoped state, Codex and Perplexity Computer may draft planning artifacts on the following topics. Planning artifacts are documents, not code, and must be reviewable as documents. The list mirrors `plan/phase2_entry_plan.md` §3 deliberately so the pattern is the same and is reviewable on the same axes:

1. The Phase 3 objective in prose: what infrastructure step Phase 3 would build on top of the merged P2-01..P2-05 foundation, restated at a level that does not authorize any specific implementation.
2. Proposed Phase 3 task sequence (`P3-01`, `P3-02`, …) named only as **future** PRs that would each require their own separate written authorization slice and sibling artifact under `governance/authorizations/`. Naming a task in the plan does not authorize it.
3. Phase 3 entry criteria — what must be true (baseline, governance, ADRs, monitoring cadence under ADR-008 §D6, Mode A / Mode B review per `AI_WORKFLOW.md` §4) before any Phase 3 implementation PR could open.
4. Per-PR proof-bundle expectations for any future Phase 3 PR (restated from `AI_WORKFLOW.md` §3 and `plan/phase2_entry_plan.md` §6, adjusted for Phase 3 scope where the ADRs require it).
5. Rollback and stop conditions, restated for Phase 3 from `plan/phase2_entry_plan.md` §8.
6. Phase-boundary enforcement — how Phase 3 PRs would prove they did not cross into trading strategy, broker execution, live trading, real market data ingestion, real secrets, or any other always-forbidden category in `MASTER_STATUS.md` §6.
7. ADR follow-ups that Phase 3 entry would require — at minimum the runtime-phase monitoring cadence follow-up deferred by ADR-008 §D6, plus any kill-switch (ADR-002), reconciliation (ADR-003), heartbeat (ADR-005), secrets-management (ADR-001), deployment-log (ADR-006), and minimal-CI (ADR-007) implications that a runtime phase would have to address before opening.

Any planning topic that does not fit the list above must be raised with Kevin before a document is written.

## Explicitly Not Authorized

The authorization above does not permit, by implication or otherwise, any of the following. Each remains forbidden until Kevin records a separate written authorization per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 ("One approver") / rule 7 ("No phase drift"), with a sibling artifact under `governance/authorizations/` and (where it introduces a new directory) a corresponding update to the §8 step 4a allowlist in the same PR that introduces the directory:

- **Opening Phase 3.** This authorization opens **planning** of Phase 3 entry, not Phase 3 itself. No Phase 3 task is opened, no Phase 3 directory is created, no Phase 3 module lands, and no Phase 3 PR may merge under this authorization. Opening Phase 3 requires a separate written authorization from Kevin.
- **Any new Phase 2 task beyond P2-05.** The `plan/phase2_entry_plan.md` §4 P2-01..P2-05 sequence is exhausted and Phase 2 is formally closed (`governance/authorizations/2026-05-12_phase-2-closure.md`). No P2-06 or sibling Phase 2 task is opened by this planning authorization.
- **Runtime work of any kind.** No `__main__` entry point, no daemon, no scheduler, no background worker, no long-running service, no live execution loop is authorized, planned-into-existence, or pre-approved by this authorization.
- **Broker integration.** No broker SDK, no broker connector, no broker reconciliation runtime, no broker authentication, no broker credentials.
- **Market-data integration.** No market-data ingestion code, no market-data pipeline, no committed dataset, no live or historical data feed.
- **Order management.** No order objects, no order placement, no position management, no fills, no trade reports.
- **Strategy logic.** No trading signals, no scanners, no models, no portfolio rules, no backtests.
- **Scheduling.** No cron-style scheduler, no APScheduler, no background-job framework, no operator-heartbeat daemon, no kill-switch runtime, no reconciliation runtime.
- **Persistence.** No SQLite, no on-disk database, no on-disk reconciliation snapshot, no on-disk heartbeat state, no log sink, no file artifact written by runtime code.
- **Deployment.** No deployment workflow, no rollout, no rollback runtime, no CI/CD pipeline beyond the existing local pre-commit and pytest gates.
- **Secrets / env-var loading.** No real secrets, no real credentials, no `.env` files, no `os.environ` / `os.getenv` reads, no real account identifiers, no real broker / venue identifiers, no real endpoints embedded anywhere in the repository under this authorization. ADR-001's secrets-management discipline is not relaxed.
- **Concrete risk implementations.** No concrete implementation of any kill-switch / reconciliation / heartbeat protocol lands inside the runtime package under this authorization. The P2-05 boundary (`src/gmc_rebuild/risk/` is types and abstract `typing.Protocol` definitions only) is preserved.
- **New trading behavior.** No change that introduces, simulates, or wires up trading behavior — in any module, under any name, anywhere in the tree.
- **Tooling relaxation.** No weakening of pre-commit, Ruff, mypy strict mode, `detect-secrets`, `.gitignore`, `.secrets.baseline`, the `MASTER_STATUS.md` §8 step 4 always-forbidden scan, the §8 step 4a per-PR Phase 2 infrastructure allowlist, or the §8 step 4c recursive forbidden-token scan.
- **§8 step 4a allowlist expansion.** The `allowed_p2_infra` allowlist is **not** extended by this authorization or by any future planning document opened under it. Any future addition requires a separate written authorization that names a specific implementation task, a sibling artifact under `governance/authorizations/`, and an allowlist update made in the same PR that introduces the new directory.
- **Source / test changes.** No file under `src/**` or `tests/**` is modified or created by the authorizing PR for this artifact, nor by any planning document opened under it. Planning documents live under `governance/`, `plan/`, `docs/`, or `README.md`.
- **New tags or releases.** No git tag, no GitHub release, no version bump is created by this authorization or its PR.
- **Mode A / Mode B substitution.** This authorization is governance prose, not a control-surface decision; it does not substitute for adversarial review of any future Phase 3 entry decision or any future runtime / broker / market-data / order / strategy / scheduler / persistence / deployment PR. Any such future PR must independently satisfy `AI_WORKFLOW.md` §4 (Mode A) and ADR-008 (Mode B) as applicable. Opening Phase 3 will itself be a phase-gate decision under `AI_WORKFLOW.md` §4(1) and will require Mode A adversarial review at that time.

The always-forbidden categories in `MASTER_STATUS.md` §6 and `plan/phase2_entry_plan.md` §2 — strategy code, broker execution code, live or paper trading wired to a real broker, runtime daemons affecting accounts, real market data ingestion, order placement, and real secrets — remain forbidden in all modes. This authorization does not relax them and does not record any relaxation. The mirroring above is intentional and is not a re-authorization of any category: those categories remain forbidden by default, and naming them here records that Kevin did not silently relax them when authorizing Phase 3 entry **planning**.

## Preserved Gates for Any Future Phase 3 Work

Any work beyond this planning authorization — Phase 3 entry itself, any specific Phase 3 task (`P3-01`, `P3-02`, …), or any runtime / broker / market-data / order / strategy / scheduler / persistence / deployment work — requires **all** of the following, none of which is satisfied by this planning authorization:

1. **Separate written authorization from Kevin** per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 ("One approver") / rule 7 ("No phase drift"), with a sibling artifact under `governance/authorizations/`.
2. **Runtime-cadence ADR follow-up where applicable.** ADR-008 §D6 defers runtime-phase monitoring cadence to a follow-up ADR; any runtime work must address that follow-up before merge.
3. **Mode A adversarial review.** `AI_WORKFLOW.md` §4 reserves Mode A for phase gates, new control surfaces, new trust boundaries, non-reversible decisions, and safety-critical decisions. Opening Phase 3 is a phase gate by definition; the Phase 3 entry decision (when proposed) must carry a Mode A adversarial critique before merge.
4. **Mode B monitoring packet where required.** ADR-008 §D3 / §D5 requires a monitoring packet on any active workday on which the default branch changes or a pull request is open, updated, or merged. This planning-authorization PR itself triggers ADR-008 §D3 and a Mode B packet under `monitoring/daily/` is required per the existing cadence rule; that packet is committed under Codex's authorship per `AI_WORKFLOW.md` §1.4 and §6 rule 1, and is produced as a separate change, not bundled into this authorization PR.
5. **§8 step 4a allowlist updates in the same PR.** Any new authorized directory must be added to `allowed_p2_infra` (and the matching comment block) in the same PR that introduces the directory, per the standing rule in `MASTER_STATUS.md` §8 step 4b.

## Exit Criteria

This planning-authorization PR may merge only after the full required check suite passes on the planning-authorization branch:

- `pre-commit run --all-files` (clean, or every failure documented).
- `pytest` (clean).
- `MASTER_STATUS.md` §8 step 3 (baseline ancestry from `1f101fc`).
- `MASTER_STATUS.md` §8 step 4 (always-forbidden scan).
- `MASTER_STATUS.md` §8 step 4a (per-PR Phase 2 infrastructure allowlist scan; allowlist is unchanged).
- `MASTER_STATUS.md` §8 step 4c (recursive forbidden-token scan; subshell exit `0`).

After this authorization merges, the next allowed decisions remain those listed in `MASTER_STATUS.md` §9, augmented by the narrow planning workstream described in "Allowed Planning Topics" above. Phase 3 is **not** opened; Phase 2 remains formally closed; no Phase 2 task beyond P2-05 is opened; no Phase 3 task is opened. Any subsequent step — including the eventual Phase 3 entry plan document — requires its own separate written authorization per the preserved gates above.

## Supporting Evidence (Non-Authoritative)

The following are pointers to the surrounding governance record. They are evidence, not the authorization itself; this file is the authorization of record for Phase 3 entry **planning**.

- Phase 1 accepted baseline: `1f101fc` (`MASTER_STATUS.md` §3).
- Phase 2 closure authorization: `governance/authorizations/2026-05-12_phase-2-closure.md`.
- Phase 2 entry plan (pattern reference for any future Phase 3 entry plan): `plan/phase2_entry_plan.md`.
- P2-05 governance-only authorization slice (pattern reference for narrow scope language): `governance/authorizations/2026-05-12_p2-05.md`.
- Monitoring cadence rule that governs the sibling Mode B packet for this PR: `docs/decisions/ADR-008_monitoring_cadence_and_ai_monitor_role.md` §D3 / §D5.
