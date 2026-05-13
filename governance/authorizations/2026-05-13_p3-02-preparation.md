# P3-02 Preparation — Draft Phase 3 Entry Authorization Text (Governance/Documentation-Only, Pending Mode A Review)

Date: 2026-05-13
Authorizer: Kevin (preparation scope only — see Section "Authorization Status" below)
Scope: P3-02 **preparation only** — governance / documentation scope (**does not open Phase 3, does not authorize any Phase 3 implementation, does not authorize P3-02 itself, does not extend the `MASTER_STATUS.md` §8 step 4a allowlist, does not add or modify any file under `src/**` or `tests/**`, does not authorize any runtime / broker / market-data / order / strategy / scheduler / persistence / deployment / env-var / secrets / concrete risk implementation / automation / notification / CI gate / tag / release**)

## Authorization Status

This artifact is the written **preparation** artifact for the future Phase 3 entry decision (candidate task P3-02 in `plan/phase3_entry_plan.md` §4 item 2). It is **not** Kevin's written authorization to open Phase 3, and it is **not** the P3-02 entry PR. It is the documentation-only preparation step that the Phase 3 entry planning workstream authorized at `governance/authorizations/2026-05-13_phase-3-entry-planning.md` ("Allowed Planning Topics" items 1–7) explicitly contemplates: drafting, in writing, the prose that any future Phase 3 entry authorization would have to contain, so that the Phase 3 entry decision — when and only when Kevin chooses to make it in writing — can be reviewed against a concrete, in-tree draft rather than reconstructed under time pressure.

The verbatim user authorization for this preparation work (Kevin, chat, 2026-05-13) is:

> "Authorize P3-02 preparation only: draft the written Phase 3 entry authorization and any necessary governance/status reflection for P3-01 completion, governance/documentation scope only. No Phase 3 opening yet, no implementation, no allowlist extension, no src/tests changes, no runtime/broker/scheduler/persistence/deployment changes, no tags/releases. Prepare for Mode A review before any P3-02 entry PR is drafted."

This preparation authorization is the **preparation analogue** to the governance-only authorization slices previously used for P2-03 (`governance/authorizations/2026-05-12_p2-03.md`), P2-04 (`governance/authorizations/2026-05-12_p2-04.md`), P2-05 (`governance/authorizations/2026-05-12_p2-05.md`), the Phase 3 entry planning authorization at `governance/authorizations/2026-05-13_phase-3-entry-planning.md`, the P3-01 drafting authorization at `governance/authorizations/2026-05-13_p3-01.md`, and the P3-01 acceptance authorization at `governance/authorizations/2026-05-13_p3-01-acceptance.md`. It is intentionally **narrower** than each of those: it does **not** open Phase 3, does **not** authorize P3-02 itself, does **not** name or open any task beyond P3-02 preparation, does **not** extend the `MASTER_STATUS.md` §8 step 4a `allowed_p2_infra` allowlist, does **not** add or modify any path under `src/**` or `tests/**`, and does **not** decide the Phase 3 entry question.

The closure of Phase 2 at `governance/authorizations/2026-05-12_phase-2-closure.md`, the Phase 3 entry planning authorization at `governance/authorizations/2026-05-13_phase-3-entry-planning.md`, the P3-01 drafting authorization at `governance/authorizations/2026-05-13_p3-01.md`, and the P3-01 acceptance authorization at `governance/authorizations/2026-05-13_p3-01-acceptance.md` each explicitly state that they do **not** open Phase 3 and do **not** authorize P3-02. Those statements are unchanged by this preparation artifact. **Phase 3 remains closed. Phase 2 remains formally closed. P3-02 has not been authorized.**

This artifact is pending Mode A adversarial review prior to any P3-02 entry PR being drafted under a separate, future Kevin-written authorization. The Mode A review of this preparation artifact targets the **prose only**; Mode A review of the actual Phase 3 entry decision (the phase gate per `AI_WORKFLOW.md` §4(1)) remains a future, separate review against the future P3-02 entry PR itself.

## Scope

The work authorized by this preparation artifact is restricted to:

- This preparation artifact at `governance/authorizations/2026-05-13_p3-02-preparation.md`.
- A narrow, conservative governance/status reflection of P3-01 completion in `MASTER_STATUS.md`. The reflection is documentation-only: it records that ADR-009 has been accepted (under `governance/authorizations/2026-05-13_p3-01-acceptance.md` and PR #34), that the ADR-008 §D6 follow-up has therefore been closed, that Phase 2 remains formally closed, that Phase 3 is **not** opened, and that P3-02 entry is **not yet authorized or merged**. Per `AI_WORKFLOW.md` §1.2 and §6 rule 2 ("One status keeper"), this `MASTER_STATUS.md` edit is conservative and remains subject to Perplexity Computer's verification before being treated as the canonical status. The reflection **does not** change phase, does **not** extend the §8 step 4a allowlist, and does **not** relax any quality gate.
- A minimal `README.md` cross-reference update naming this preparation artifact alongside the existing Phase 3 entry planning, P3-01 drafting, and P3-01 acceptance authorization references, so that a reader of `README.md` "Current Phase" can see the current state of the planning workstream without having to read every authorization file in turn. The update does **not** declare Phase 3 open, does **not** authorize P3-02, does **not** extend the §8 step 4a allowlist, and does **not** modify any quality gate.
- A narrow status update inside `plan/phase3_entry_plan.md` §1 "Current Status" recording that P3-01 has merged (ADR-009 accepted) and that P3-02 entry preparation is in progress under this artifact, pending Mode A review and a future separate written authorization. The update remains planning-only and explicitly preserves that Phase 3 is **not** opened. No new section is added to the plan; no §4 task is renamed, reordered, or escalated from "future / not authorized" to "authorized".
- No other file is modified. In particular: no file under `src/**`, no file under `tests/**`, no ADR text, no `.pre-commit-config.yaml`, no `pyproject.toml`, no `.gitignore`, no `.secrets.baseline`, no template, no test, no `monitoring/daily/` packet (any required Mode B packet for the workday on which this preparation PR is open / merged is a separate sibling PR per ADR-008 §D5, exactly as for PR #30 / PR #32 / PR #34 — this preparation PR does not bundle it).

The preparation artifact, by content, must:

1. Be explicitly **preparatory** and explicitly **pending Mode A review**. It is not Phase 3 entry authorization. It is the written draft of what such an authorization would have to contain.
2. Preserve the existing phase boundary unchanged. Phase 3 is **not** opened. Phase 2 remains formally closed (governance-only). The §8 step 4a `allowed_p2_infra` allowlist remains exactly the five P2-01..P2-05 entries (`src`, `src/gmc_rebuild/config`, `src/gmc_rebuild/time`, `src/gmc_rebuild/logging`, `src/gmc_rebuild/risk`).
3. Name the **intended first Phase 3 task scope at the planning level only** — see "Intended First Phase 3 Task Scope (Planning Level Only)" below — without authorizing implementation. The intended first task is the candidate P3-03 task named in `plan/phase3_entry_plan.md` §4 item 3 ("(future / not authorized) Test-fixture implementation of one risk-control protocol"), restated here at the planning level only.
4. Restate the **gates** that any future P3-02 entry PR must satisfy: Kevin's separate written authorization per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 / rule 7, a sibling authorization artifact under `governance/authorizations/`, Mode A adversarial review per `AI_WORKFLOW.md` §4(1) (phase gate), a Mode B monitoring packet for the active workday per ADR-008 §D3 / §D5 (until ADR-009 D3 / D5 governs — the bootstrap-avoidance clause in ADR-009 D7 keeps ADR-008 §D3 / §D5 in force for the P3-02 entry PR itself), and (where it introduces a directory) a corresponding update to the §8 step 4a allowlist in the same PR per `MASTER_STATUS.md` §8 step 4b.
5. Make explicit that the future P3-02 entry PR is a **separate** PR, with a **separate** written Kevin authorization, a **separate** Mode A critique recorded against the entry PR itself, and a **separate** sibling Mode B monitoring packet committed and merged to `main` in a separate monitoring PR per ADR-008 §D5 before the entry PR merges.

The preparation artifact must **not**, by content:

- Open Phase 3.
- Authorize P3-02 entry.
- Authorize P3-03 or any task beyond P3-02 preparation.
- Authorize runtime work, broker integration, market-data integration, order management, strategy logic, scheduling, persistence, deployment, env-var loading, or any concrete implementation of `KillSwitchProtocol`, `ReconciliationProtocol`, or `HeartbeatProtocol`.
- Extend the `MASTER_STATUS.md` §8 step 4a allowlist.
- Modify any quality gate, secrets baseline, or always-forbidden category.
- Create any git tag, GitHub release, or version bump.
- Embed real secrets, real credentials, real account identifiers, real broker / venue identifiers, or real endpoints.
- Add or modify any file under `src/**` or `tests/**`.

## Intended First Phase 3 Task Scope (Planning Level Only)

This section names the intended first Phase 3 task at the planning level only, to satisfy the `MASTER_STATUS.md` §7.4 pattern recorded in `plan/phase2_entry_plan.md` §5 that any phase-opening authorization "must also name the first PR's scope". Naming the scope here **does not authorize implementation**. The scope still requires its own separate written authorization at the time it is opened, and Mode A / Mode B review as applicable.

The intended first Phase 3 task is the candidate task already named in `plan/phase3_entry_plan.md` §4 item 3:

> **PR P3-03 — (future / not authorized) Test-fixture implementation of one risk-control protocol.** A first, narrowly scoped test-fixture implementation of exactly one of the P2-05 protocols (the specific protocol is to be named by Kevin in writing at the time of authorization). Restricted to a single protocol; restricted to test-fixture code that runs under `pytest`; no broker SDK, no network, no real account identifiers, no real venue identifiers, no real endpoints, no real secrets, no scheduler, no daemon, no `__main__` entry point, no order objects, no market-data ingestion.

The intended scope, at the planning level only, has these properties:

- **One protocol, not all three.** The first Phase 3 implementation task targets exactly one of `KillSwitchProtocol`, `ReconciliationProtocol`, or `HeartbeatProtocol`. Kevin names the specific protocol in writing at the time of P3-03 authorization; this preparation artifact does **not** name a protocol and does **not** narrow the choice.
- **Test-fixture only.** The implementation is a test-fixture artifact under `tests/**` (or a sandboxed helper under a future authorized `src/gmc_rebuild/<protocol>/` subdirectory specifically scoped to test-fixture support, named in writing by Kevin at the time of P3-03 authorization), exercised under `pytest`. No `__main__` entry point. No daemon. No scheduler. No background worker. No network. No broker SDK. No real account / venue / endpoint identifier. No real secret. No real or historical market data feed. No order object. No order placement.
- **One control surface at a time.** Even within the chosen protocol, the test-fixture exercise is narrow enough that a single review can verify it does not cross into trading strategy, broker execution, live or paper trading wired to a real broker, real market data ingestion, real secrets, order placement, scheduler / daemon, persistence outside the test sandbox, or runtime-daemon territory — i.e. the always-forbidden categories in `MASTER_STATUS.md` §6 and the stop conditions in `plan/phase3_entry_plan.md` §8.
- **Allowlist update in the same PR.** Any new directory introduced by the future P3-03 implementation must be added to the `MASTER_STATUS.md` §8 step 4a `allowed_p2_infra` allowlist in the same PR that introduces the directory, per the standing rule in `MASTER_STATUS.md` §8 step 4b. This preparation artifact does **not** extend the allowlist.
- **No expansion to P3-04, P3-05, ….** `plan/phase3_entry_plan.md` §4 deliberately does not enumerate further candidate tasks. Any later enumeration is itself a documentation-only update to the plan and remains subject to `governance/authorizations/2026-05-13_phase-3-entry-planning.md` "Allowed Planning Topics" item 2.

Naming this intended scope here lets the future P3-02 entry PR — when and only when Kevin authorizes it in writing — be reviewed against a concrete, in-tree planning-level statement rather than a reconstructed one. It does **not** narrow Kevin's later authorization; Kevin remains free to name a different first Phase 3 task scope, in which case the future P3-02 entry PR records the change and this preparation artifact's "Intended First Phase 3 Task Scope" section is treated as superseded by the entry PR's authorization text.

## Required Gates Before Any P3-02 Entry PR May Merge

Any future P3-02 entry PR must independently satisfy **all** of the following, none of which is satisfied by this preparation artifact:

1. **Separate written authorization from Kevin** per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 ("One approver") / rule 7 ("No phase drift"), with its own sibling artifact under `governance/authorizations/` per `AI_WORKFLOW.md` §7. The future authorization artifact may quote, adapt, or replace the prose of this preparation artifact, but it is the future artifact — not this one — that records the authorization of record for the Phase 3 entry decision.
2. **Mode A adversarial review of the P3-02 entry PR itself**, per `AI_WORKFLOW.md` §4(1). Opening Phase 3 is a phase gate by definition. The Mode A critique is delivered as PR-review text against the P3-02 entry PR and is **not** committed to the repository (per `AI_WORKFLOW.md` §6 rule 5 / ADR-008 §D7 dual-artifact rule). This preparation artifact's own Mode A review (see "Mode A Status" below) does **not** substitute for the P3-02 entry PR's Mode A review.
3. **Mode B monitoring packet** for the active workday on which the P3-02 entry PR is open / merged, authored by the Backup AI per ADR-008 §D1 and committed by Codex under `monitoring/daily/` per ADR-008 §D4 in a **separate** monitoring PR, **merged to `main` before the P3-02 entry PR merges** per ADR-008 §D5. ADR-009 D3 / D5 do not govern the P3-02 entry PR itself because ADR-009's bootstrap-avoidance clause keeps ADR-008 §D3 / §D5 in force until runtime exists on `main`; the P3-02 entry PR does not introduce runtime and therefore continues to fall under ADR-008's governance-phase cadence.
4. **§8 step 4a allowlist update in the same PR** for any new authorized directory the P3-02 entry PR introduces, per the standing rule in `MASTER_STATUS.md` §8 step 4b. If P3-02 entry as authorized by Kevin does not introduce a new directory, the allowlist remains unchanged.
5. **No silent expansion of scope.** The P3-02 entry PR's scope is exactly what Kevin's separate written authorization names, and no broader. Per `AI_WORKFLOW.md` §6 rule 6 / rule 7, any PR that grows beyond its stated scope during implementation is split or stopped, not merged.

The above gates do **not** add any new requirement on top of `MASTER_STATUS.md`, `AI_WORKFLOW.md`, `plan/phase3_entry_plan.md`, ADR-008, or ADR-009. They restate the existing rules in the specific context of the future P3-02 entry PR, so the Mode A reviewer of this preparation artifact can verify them at a glance.

## P3-01 Completion — Governance/Status Reflection

P3-01 is complete on `main` as of 2026-05-13 UTC:

- The P3-01 drafting authorization at `governance/authorizations/2026-05-13_p3-01.md` (PR #30) drafted ADR-009 in **Proposed** status.
- The P3-01 revision PR #32 addressed Mode A blocking findings B1–B5 against the Proposed ADR-009 text while preserving Proposed status.
- The P3-01 acceptance authorization at `governance/authorizations/2026-05-13_p3-01-acceptance.md` (PR #34) flipped ADR-009 from `Status: Proposed` to `Status: Accepted`, closed the ADR-008 §D6 follow-up checkbox with a pointer to ADR-009, and updated `README.md` to list ADR-009 under "Accepted ADRs".
- ADR-008 §D6's deferred follow-up is therefore closed on `main`. Any future runtime PR's cadence and missed-packet severity are governed by ADR-009 once runtime exists, with ADR-008 §D3 / §D5 continuing to govern the governance phase (including the P3-02 entry PR itself, per ADR-009's bootstrap-avoidance clause in D7).

`MASTER_STATUS.md` at the time of this preparation artifact's draft does not yet name ADR-009 or P3-01 acceptance in its §1 / §9 prose. The Mode A re-review and the PR #34 acceptance review noted that this absence increases friction for the Mode A reviewer of any future Phase 3 PR, because the canonical first-read document does not reflect that the ADR-008 §D6 follow-up is closed. Per `AI_WORKFLOW.md` §1.2 / §6 rule 2 ("One status keeper"), Perplexity Computer is the only role that can canonically update `MASTER_STATUS.md`. The conservative reflection edit in this preparation PR is bounded to:

- Adding a one-paragraph note in `MASTER_STATUS.md` §1 recording, in governance-prose only, that ADR-009 is accepted on `main` (citing `governance/authorizations/2026-05-13_p3-01-acceptance.md`), that the ADR-008 §D6 follow-up is therefore closed, that Phase 2 remains formally closed, that Phase 3 is **not** opened, and that P3-02 entry is **not yet authorized**.
- Adding a one-line note in `MASTER_STATUS.md` §9 item 7 referencing this preparation artifact alongside the existing references to `2026-05-13_phase-3-entry-planning.md`, with the same conservative framing (preparation only; Mode A review pending; Phase 3 not opened; P3-02 entry not yet authorized).
- Per `AI_WORKFLOW.md` §1.2 / §6 rule 2, these edits remain subject to Perplexity Computer's verification before being treated as the canonical status. The edits are intentionally conservative — they record state without opening Phase 3 or changing any phase-boundary control.

No other section of `MASTER_STATUS.md` is changed by this preparation PR. In particular: §3 (baseline), §6 (always-forbidden categories), §7 (Phase 2 boundary), and §8 (startup verification commands, including the §8 step 4a `allowed_p2_infra` allowlist) are unchanged. The five P2-01..P2-05 allowlist entries remain exactly `src`, `src/gmc_rebuild/config`, `src/gmc_rebuild/time`, `src/gmc_rebuild/logging`, and `src/gmc_rebuild/risk`.

## Mode A Status

This preparation artifact is **pending Mode A adversarial review** before any P3-02 entry PR is drafted. Per `AI_WORKFLOW.md` §4 and ADR-008 §D7:

- This preparation artifact is **governance-prose only** and does not itself open a phase or define a runtime control surface. It is preparation under the existing Phase 3 entry planning workstream (`governance/authorizations/2026-05-13_phase-3-entry-planning.md`). Strictly speaking, `AI_WORKFLOW.md` §4 does not mandate Mode A on preparation prose. Kevin has nevertheless directed in writing that this artifact "prepare for Mode A review before any P3-02 entry PR is drafted", so a Mode A critique is requested against this preparation PR.
- The Mode A critique is delivered as PR-review text against this preparation PR. Per `AI_WORKFLOW.md` §6 rule 5 / ADR-008 §D7, the Mode A critique is **not** committed to the repository.
- The Mode A review here targets the prose only: scope-boundary preservation (Phase 3 not opened, P3-02 not authorized, §8 step 4a allowlist unchanged, no `src/**` or `tests/**` change, no quality-gate change, no runtime / broker / market-data / order / strategy / scheduler / persistence / deployment / env-var / secrets / concrete-risk / automation / notification / CI-gate / tag / release change), accuracy of P3-01 completion reflection, accuracy of the cross-references to ADR-008 / ADR-009 / `MASTER_STATUS.md` / `AI_WORKFLOW.md` / `plan/phase3_entry_plan.md`, and clarity of the "Intended First Phase 3 Task Scope" framing as planning-level only.
- A Mode A critique against the future P3-02 entry PR itself remains a **separate** requirement and is **not** satisfied by the Mode A review of this preparation PR.

## Required Monitoring (Mode B)

Per ADR-008 §D3 / §D5, the preparation PR is an active-workday event on its open / merge UTC date. As of 2026-05-13, five 2026-05-13 packets already exist on `main`:

- `monitoring/daily/2026-05-13.md` — first packet, scoped to PR #26.
- `monitoring/daily/2026-05-13_pr28.md` — second packet, scoped to PR #28.
- `monitoring/daily/2026-05-13_p3-01.md` — third packet, scoped to PR #30 (P3-01 drafting).
- `monitoring/daily/2026-05-13_p3-01-revision.md` — fourth packet, scoped to PR #32 (P3-01 revision).
- `monitoring/daily/2026-05-13_adr-009-acceptance.md` — fifth packet, scoped to PR #34 (ADR-009 acceptance).

If this preparation PR opens on 2026-05-13 UTC, a **sixth slugged 2026-05-13 packet** is required (suggested name `monitoring/daily/2026-05-13_p3-02-preparation.md` or `monitoring/daily/2026-05-13_pr<N>.md` where `<N>` is the preparation PR number). The packet must be **committed and merged to `main` in a separate monitoring PR before the preparation PR merges**, per ADR-008 §D5 and the established 2026-05-13 precedents (PR #27 → PR #26, PR #29 → PR #28, PR #31 → PR #30, PR #33 → PR #32, PR #35 → PR #34). This preparation PR does **not** bundle the monitoring packet.

If the preparation PR opens on a later UTC date, the packet is the first or a slugged subsequent packet for that UTC date, per ADR-008 §D4 same-day naming.

Perplexity Computer confirms this sequencing before verifying the preparation PR for Kevin's review. The Mode B packet must reflect that the preparation PR's content is restricted to (a) this preparation artifact, (b) conservative `MASTER_STATUS.md` §1 / §9 reflection of P3-01 completion, (c) a minimal `README.md` cross-reference update, and (d) a narrow `plan/phase3_entry_plan.md` §1 status note — and must reflect that Phase 3 is **not** opened and P3-02 entry is **not** authorized.

## Explicitly Not Authorized

The authorization above does not permit, by implication or otherwise, any of the following. Each remains forbidden until Kevin records a separate written authorization per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 ("One approver") / rule 7 ("No phase drift"), with a sibling artifact under `governance/authorizations/` and (where it introduces a new directory) a corresponding update to the §8 step 4a allowlist in the same PR that introduces the directory:

- **Opening Phase 3.** This preparation artifact does not open Phase 3. Opening Phase 3 requires a separate written authorization from Kevin recorded in a future sibling artifact under `governance/authorizations/`, reviewed in Mode A against the actual P3-02 entry PR, and monitored in Mode B per ADR-008 §D3 / §D5.
- **Authorizing P3-02 itself.** This preparation artifact is **preparation**; it is not the P3-02 entry PR and not Kevin's written authorization to merge it. The future P3-02 entry PR must carry its own separate Kevin-written authorization artifact.
- **Authorizing P3-03 or any task beyond P3-02 preparation.** Naming P3-03's intended scope at the planning level (see "Intended First Phase 3 Task Scope" above) does **not** authorize P3-03. P3-03 still requires its own separate written authorization, a sibling artifact under `governance/authorizations/`, an §8 step 4a allowlist update in the same PR that introduces any new directory, Mode A adversarial review per `AI_WORKFLOW.md` §4(2) (high-risk architecture decision — first concrete behaviour behind a control surface), and a Mode B monitoring packet per ADR-008 §D3 / §D5 (governance phase) or, once runtime exists on `main`, per ADR-009 D3 / D5 (runtime phase). The Phase 3 entry decision (P3-02) must merge **before** P3-03 may be opened.
- **Any new Phase 2 task beyond P2-05.** Phase 2 is formally closed per `governance/authorizations/2026-05-12_phase-2-closure.md`. No P2-06 or sibling Phase 2 task is opened by this preparation artifact.
- **Runtime work of any kind.** No `__main__` entry point, no daemon, no scheduler, no background worker, no long-running service, no live execution loop. The preparation artifact is governance prose; its acceptance does not materialise runtime.
- **Broker integration.** No broker SDK, no broker connector, no broker reconciliation runtime, no broker authentication, no broker credentials.
- **Market-data integration.** No market-data ingestion code, no market-data pipeline, no committed dataset, no live or historical data feed.
- **Order management.** No order objects, no order placement, no position management, no fills, no trade reports.
- **Strategy logic.** No trading signals, no scanners, no models, no portfolio rules, no backtests.
- **Scheduling.** No cron-style scheduler, no APScheduler, no background-job framework, no operator-heartbeat daemon, no kill-switch runtime, no reconciliation runtime, no monitoring daemon, no notification daemon, and no automation that watches the cadence rule ADR-009 defines.
- **Persistence.** No SQLite, no on-disk database, no on-disk reconciliation snapshot, no on-disk heartbeat state, no log sink, no file artifact written by runtime code.
- **Deployment.** No deployment workflow, no rollout, no rollback runtime, no CI/CD pipeline beyond the existing local pre-commit and pytest gates.
- **Secrets / env-var loading.** No real secrets, no real credentials, no `.env` files, no `os.environ` / `os.getenv` reads, no real account identifiers, no real broker / venue identifiers, no real endpoints embedded anywhere in the repository under this preparation. ADR-001's secrets-management discipline is not relaxed.
- **Concrete risk implementations.** No concrete implementation of `KillSwitchProtocol`, `ReconciliationProtocol`, or `HeartbeatProtocol` lands inside the runtime package under this preparation. The P2-05 boundary (`src/gmc_rebuild/risk/` is types and abstract `typing.Protocol` definitions only) is preserved.
- **New trading behavior.** No change that introduces, simulates, or wires up trading behavior — in any module, under any name, anywhere in the tree.
- **Tooling relaxation.** No weakening of pre-commit, Ruff, mypy strict mode, `detect-secrets`, `.gitignore`, `.secrets.baseline`, the `MASTER_STATUS.md` §8 step 4 always-forbidden scan, the §8 step 4a per-PR Phase 2 infrastructure allowlist scan, or the §8 step 4c recursive forbidden-token scan.
- **§8 step 4a allowlist expansion.** The `allowed_p2_infra` allowlist is **not** extended by this preparation. It remains exactly `src`, `src/gmc_rebuild/config`, `src/gmc_rebuild/time`, `src/gmc_rebuild/logging`, and `src/gmc_rebuild/risk`.
- **Source / test changes.** No file under `src/**` or `tests/**` is modified or created by this preparation PR.
- **New tags or releases.** No git tag, no GitHub release, no version bump.
- **Live-trading entry gate triggering.** ADR-009 D5 records the implementation evidence / deferred-with-citation evidence requirement for any future PR that introduces a live-trading entry point. This preparation PR does **not** introduce a live-trading entry point; the §3.4 evidence requirement applies to future PRs, not to this one.
- **Mode A substitution.** The Mode A critique requested against this preparation PR is targeted at the preparation prose. It does **not** substitute for the Mode A critique against the future P3-02 entry PR itself, which remains a separate `AI_WORKFLOW.md` §4(1) phase-gate review.

The always-forbidden categories in `MASTER_STATUS.md` §6 and `plan/phase2_entry_plan.md` §2 — strategy code, broker execution code, live or paper trading wired to a real broker, runtime daemons affecting accounts, real market data ingestion, order placement, and real secrets — remain forbidden in all modes. This preparation does not relax them.

## Preserved Gates for Any Future Work

Any work beyond this preparation — opening Phase 3 (P3-02), opening any further Phase 3 task (P3-03, P3-04, …), or opening any runtime / broker / market-data / order / strategy / scheduler / persistence / deployment / monitoring-daemon work — requires **all** of the following, none of which is satisfied by this preparation:

1. **Separate written authorization from Kevin** per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 / rule 7, with a sibling artifact under `governance/authorizations/`.
2. **Mode A adversarial review** per `AI_WORKFLOW.md` §4. Opening Phase 3 is a phase gate (§4(1)); the first concrete behaviour behind any risk-control surface is a high-risk architecture decision (§4(2)).
3. **Mode B monitoring packet** per ADR-008 §D3 / §D5 (governance phase) or, once runtime exists on `main`, per ADR-009 D3 / D5 (runtime phase). Before-merge sequencing per ADR-008 §D5 (or ADR-009 D5 once in force) applies.
4. **§8 step 4a allowlist updates in the same PR** for any new authorized directory, per the standing rule in `MASTER_STATUS.md` §8 step 4b.
5. **Live-trading entry gate** per ADR-009 D5 for any PR that introduces a live-trading entry point: either named implementation evidence + named test path in the PR's diff, or named deferred-with-citation evidence pointing to an already-merged authorization artifact on `main`.

## Exit Criteria

This preparation PR may merge only after the full required check suite passes on the preparation branch:

- `pre-commit run --all-files` (clean, or every failure documented).
- `pytest` (clean).
- `MASTER_STATUS.md` §8 step 3 (baseline ancestry from `1f101fc`).
- `MASTER_STATUS.md` §8 step 4 (always-forbidden scan).
- `MASTER_STATUS.md` §8 step 4a (per-PR Phase 2 infrastructure allowlist scan; allowlist is unchanged).
- `MASTER_STATUS.md` §8 step 4c (recursive forbidden-token scan; subshell exit `0`).
- A slugged Mode B monitoring packet for the preparation PR's active workday has been authored under ADR-008 Mode B and committed and merged to `main` in a separate monitoring PR, **before** the preparation PR merges.
- A Mode A critique against the preparation PR has been recorded in PR-review text (not committed as a file).

After this preparation authorization merges, the next allowed decisions remain those listed in `MASTER_STATUS.md` §9, plus (a) the existing planning workstream described in `governance/authorizations/2026-05-13_phase-3-entry-planning.md`, (b) any further preparation prose updates strictly within the scope of this artifact, and (c) future separate written authorization for P3-02 (Phase 3 entry decision). Phase 3 is **not** opened; Phase 2 remains formally closed; no Phase 2 task beyond P2-05 is opened; no Phase 3 task beyond P3-01 (already merged) is opened.

## Supporting Evidence (Non-Authoritative)

The following are pointers to the surrounding governance record. They are evidence, not the authorization itself; this file is the authorization of record for the **preparation** workstream for the future Phase 3 entry decision.

- Phase 1 accepted baseline: `1f101fc` (`MASTER_STATUS.md` §3).
- Phase 2 closure authorization: `governance/authorizations/2026-05-12_phase-2-closure.md`.
- Phase 3 entry planning authorization: `governance/authorizations/2026-05-13_phase-3-entry-planning.md`.
- P3-01 drafting authorization: `governance/authorizations/2026-05-13_p3-01.md`.
- P3-01 acceptance authorization: `governance/authorizations/2026-05-13_p3-01-acceptance.md`.
- Phase 3 entry plan (criterion 5 references ADR-009 acceptance; §4 item 2 names P3-02 as future / not-authorized): `plan/phase3_entry_plan.md` §4 item 2, §5 criterion 5, §6, §7, §8.
- ADR accepted under P3-01: `docs/decisions/ADR-009_runtime_monitoring_cadence.md`.
- ADR whose §D6 follow-up is closed by P3-01: `docs/decisions/ADR-008_monitoring_cadence_and_ai_monitor_role.md` §D6.
- UTC discipline applicable to any Phase 3 work: `docs/decisions/ADR-004_utc_discipline.md`.
- Runtime-phase control surfaces a future Phase 3 PR would coordinate with: `docs/decisions/ADR-002_kill_switch.md`, `docs/decisions/ADR-003_reconciliation.md`, `docs/decisions/ADR-005_heartbeat.md`.
- Pattern reference (prior governance-only authorization slices): `governance/authorizations/2026-05-12_p2-03.md`, `governance/authorizations/2026-05-12_p2-04.md`, `governance/authorizations/2026-05-12_p2-05.md`.
- Monitoring cadence rule governing the sibling Mode B packet for this PR: `docs/decisions/ADR-008_monitoring_cadence_and_ai_monitor_role.md` §D3 / §D4 / §D5 (governs the preparation PR per ADR-009 D7's bootstrap-avoidance clause until runtime exists on `main`).
- Mode B monitoring packets for the surrounding 2026-05-13 PR cycle: `monitoring/daily/2026-05-13.md` (PR #26), `monitoring/daily/2026-05-13_pr28.md` (PR #28), `monitoring/daily/2026-05-13_p3-01.md` (PR #30), `monitoring/daily/2026-05-13_p3-01-revision.md` (PR #32), `monitoring/daily/2026-05-13_adr-009-acceptance.md` (PR #34).
