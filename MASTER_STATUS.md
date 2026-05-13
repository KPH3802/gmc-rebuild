# MASTER STATUS

**Read this document first at the start of every serious work session.** It is the canonical, single source of truth for the current state of `gmc-rebuild`. If anything in another document conflicts with this file, this file wins until it is updated.

**Last updated:** 2026-05-13 UTC (P3-02 entry — governance/documentation-only Phase 3 entry decision formally opening Phase 3 as a governance state per `governance/authorizations/2026-05-13_p3-02.md`; no Phase 3 implementation is authorized, P3-03 remains future / not authorized, no §8 step 4a allowlist change, no `src/**` or `tests/**` change, no runtime/broker/scheduler/persistence/deployment/env-var/secrets change, no tag/release; pending Mode A review of the entry PR and a separate sibling Mode B monitoring packet merged to `main` before this entry PR merges per ADR-008 §D5)
**Maintained by:** Perplexity Computer (supervisor / status keeper), approved by Kevin

---

## 1. Current Phase

**Phase 2 — Infrastructure foundation is *formally closed* (governance-only) at the current `main` checkpoint after the merge of PR #23 (commit `0193d45`), with the `plan/phase2_entry_plan.md` §4 P2-01..P2-05 sequence fully merged and reachable at `5c390ff`. Closing Phase 2 does *not* open Phase 3 or any new Phase 2 task beyond P2-05. Opening Phase 3, opening any new Phase 2 task, or authorizing any runtime / broker / market-data / order / strategy / scheduler / persistence / deployment work requires Kevin's separate written authorization per §7 below and `AI_WORKFLOW.md` §6 rule 3 / rule 7, a sibling artifact under `governance/authorizations/`, and (where it introduces a new directory) a corresponding update to the §8 step 4a allowlist in the same PR.**

Phase 1 (governance cleanup) was accepted per `1f101fc` (see §3). Phase 2 is **formally closed (governance-only) at the current `main` checkpoint after PR #23** following Kevin's written authorization recorded at `governance/authorizations/2026-05-12_phase-2-closure.md`. Phase 2 implementation work was conducted as the §4 P2-01..P2-05 sequence: Kevin authorized PR P2-01 (package skeleton and test harness), PR P2-02 (minimal safe config schema with fake/example values only), PR P2-03 (UTC time utility), PR P2-04 (structured logging and audit event conventions), and PR P2-05 (risk-control interfaces). Each task was opened as a governance-only authorization slice followed by a narrowly scoped implementation PR; both halves have merged for each task as of 2026-05-12. P2-01 created the importable `src/gmc_rebuild/` layout with no runtime behavior; P2-02 added the `src/gmc_rebuild/config/` submodule that exposes an immutable, safe-by-default project metadata object with no runtime behavior; P2-03 added the `src/gmc_rebuild/time/` UTC time utility submodule (ADR-004-aligned `now_utc()` and parsing/formatting helpers that reject naive datetimes at the API boundary); P2-04 added the `src/gmc_rebuild/logging/` structured-logging and audit-event submodule (logging configuration and an `audit_event` helper that emits structured records to the standard logger only — no external sink, no daemon, no env-var loading); P2-05 added the `src/gmc_rebuild/risk/` risk-control interfaces submodule (ADR-002 / ADR-003 / ADR-005-aligned abstract `typing.Protocol` definitions plus supporting frozen dataclasses and enums for the kill-switch, reconciliation, and heartbeat boundaries — **types and abstract boundaries only**; no broker integration, no concrete runtime implementation of the protocols inside the runtime package, no `__main__` entry point, no scheduler / background thread / daemon, no order objects or order placement, no market-data ingestion). See `plan/phase2_entry_plan.md` §4 for the full P2-01..P2-05 sequence; all five tasks are now merged on `main`. P2-05 is the final task in the P2-01..P2-05 sequence; the formal Phase 2 closure recorded at `governance/authorizations/2026-05-12_phase-2-closure.md` is governance-only and **does not open Phase 3, does not open any new Phase 2 task beyond P2-05, does not extend the §8 step 4a allowlist, does not relax any quality gate, and does not create any tag or release**. The durable in-tree records of the P2-01..P2-05 authorizations are at `governance/authorizations/2026-05-11_p2-01.md`, `governance/authorizations/2026-05-11_p2-02.md`, `governance/authorizations/2026-05-12_p2-03.md`, `governance/authorizations/2026-05-12_p2-04.md`, and `governance/authorizations/2026-05-12_p2-05.md`; the Phase 2 closure authorization is recorded at `governance/authorizations/2026-05-12_phase-2-closure.md`.

The repository still contains no trading strategy code, no broker execution code, no live trading workflow, no runtime daemon, no market data ingestion, and no real secrets or account identifiers. Phase 2 is formally closed; any future work — Phase 3 entry, a Phase 2 task not in the §4 P2-01..P2-05 sequence, runtime work, broker integration, market-data integration, order management, strategy logic, scheduling, persistence, or deployment — requires its own separate written authorization per §7 and must satisfy the proof bundle in `plan/phase2_entry_plan.md` §6 plus any applicable runtime-cadence ADR follow-up (ADR-008 §D6) and Mode A / Mode B review per `AI_WORKFLOW.md` §4 and ADR-008.

A documentation-only point-in-time inventory of the merged P2-01..P2-05 sequence at `main` checkpoint `5c390ff` is recorded at `docs/decisions/PHASE_2_P2_01_TO_P2_05_CHECKPOINT_SUMMARY.md`. That summary is documentation-only and is not itself the closure authorization; the formal closure authorization is recorded at `governance/authorizations/2026-05-12_phase-2-closure.md` and **does not open Phase 3, open any new Phase 2 task beyond P2-05, extend the §8 step 4a allowlist, relax any quality gate, or create any tag or release**.

**P3-01 completion, P3-02 preparation, and P3-02 entry status (governance/documentation reflection, 2026-05-13 UTC).** P3-01 has merged on `main`: ADR-009 (`docs/decisions/ADR-009_runtime_monitoring_cadence.md`) was drafted in Proposed status under `governance/authorizations/2026-05-13_p3-01.md` (PR #30), revised in Proposed status by PR #32 to address Mode A blocking findings, and accepted (`Status: Proposed` → `Status: Accepted`) under `governance/authorizations/2026-05-13_p3-01-acceptance.md` (PR #34). The ADR-008 §D6 runtime-monitoring-cadence follow-up is therefore **closed** on `main`, with ADR-009 as the accepted follow-up ADR; ADR-008 §D3 / §D5 continue to govern the governance phase, and ADR-009 D3 / D5 will replace them on a going-forward basis once runtime exists on `main` per ADR-009 D7's bootstrap-avoidance clause. P3-02 preparation prose has merged on `main` under `governance/authorizations/2026-05-13_p3-02-preparation.md` (PR #36). **P3-02 entry has been authorized by Kevin in writing per `governance/authorizations/2026-05-13_p3-02.md` and formally opens Phase 3 as a governance state** on the merge of the P3-02 entry PR. The P3-02 entry is governance/documentation only and **does not authorize any Phase 3 implementation, does not authorize P3-03, does not extend the §8 step 4a allowlist (the five P2-01..P2-05 entries are preserved exactly), does not add or modify any file under `src/**` or `tests/**`, does not authorize any runtime / broker / market-data / order / strategy / scheduler / persistence / deployment / env-var / secrets / concrete-risk implementation, and does not create any tag or release**. **Phase 2 remains formally closed.** Per ADR-008 §D3 / §D5, a Mode B monitoring packet for the active workday is required, authored by the Backup AI and committed by Codex in a separate sibling monitoring PR that merges to `main` before the P3-02 entry PR merges. Per `AI_WORKFLOW.md` §4(1) (phase gate by definition), the P3-02 entry PR also requires Mode A adversarial review delivered as PR-review text (not committed to the repository). Per `AI_WORKFLOW.md` §1.2 and §6 rule 2 ("One status keeper"), this reflection is conservative and remains subject to Perplexity Computer's verification before being treated as the canonical status; it records the Phase 3 governance opening without authorizing any Phase 3 implementation and without changing any phase-boundary control beyond opening Phase 3 as a governance state (the §8 step 4a allowlist remains exactly the five P2-01..P2-05 entries).

Governance monitoring is governed by `docs/decisions/ADR-008_monitoring_cadence_and_ai_monitor_role.md`. Until runtime exists, a monitoring packet under `monitoring/daily/YYYY-MM-DD.md` is required on any **active workday** (defined audit-visibly in ADR-008 §D3 by GitHub-observable events) on which the default branch changes **or** a pull request is open, updated, or merged. The Backup AI is named in ADR-008 §D1 as the **author of packet text** under Mode B; Codex commits the packet under the safety boundary in `AI_WORKFLOW.md` §1.4 and §6 rule 1 (the Backup AI never writes code, governance decisions, or any non-packet content, and never commits directly). Mode A (gate reviewer) and Mode B (monitor) are independent; when both fire on the same PR, both artifacts are required per ADR-008 §D7. Missed packets are handled per ADR-008 §D5: a catch-up note is required **before the next merge to `main`** and again before any phase-opening or phase-expanding PR; no automatic rollback exists while no runtime exists. Runtime-phase cadence is deferred to a follow-up ADR per ADR-008 §D6.

---

## 2. Source of Truth

The authoritative artifacts, in priority order:

1. `MASTER_STATUS.md` — this file. Current phase, boundary, verification commands, allowed next decisions.
2. `AI_WORKFLOW.md` — separation of duties between Codex, Perplexity Computer, Kevin, and the optional backup AI.
3. `plan/rebuild_plan.md` — the canonical rebuild plan and the 12 governance invariants.
4. `README.md` — operating overview, setup, phase gates, safety rules.
5. `docs/decisions/ADR-*.md` — accepted architecture decision records.
6. `EXTERNAL_REVIEW_BRIEF.md` — scope and checklist for independent Phase 1 verification (the request side of the gate).
7. `docs/decisions/PHASE_1_COMPLETION_SUMMARY.md` — Phase 1 cleanup summary listing the artifacts presented for review (the submission side of the gate).
8. `docs/decisions/PHASE_2_P2_01_TO_P2_05_CHECKPOINT_SUMMARY.md` — documentation-only point-in-time inventory of the merged P2-01..P2-05 task sequence at `main` checkpoint `5c390ff`. Not an authorization artifact and not a phase-closure declaration; see §1 and §7 for the canonical phase boundary.
9. `governance/authorizations/` — durable in-tree copies of Kevin's phase-opening, phase-expanding, and phase-closing authorizations (including `2026-05-12_phase-2-closure.md`, the formal Phase 2 closure). Required by `AI_WORKFLOW.md` §7. PR history remains supporting evidence but is not a substitute for the in-tree record.

Anything not in this list is supporting material, not source of truth. If a conflict appears, escalate to Kevin before changing behavior.

---

## 3. Baseline

**Accepted Phase 1 baseline:** `1f101fc` (`docs: fix Phase 1 verification blockers`).

The accepted Phase 1 baseline is `1f101fc`, established by Kevin's written acceptance note on PR #3. That note is itself the audit-visible record (GitHub PR-comment history); it supersedes earlier candidate baselines. Any session on the default branch should start from `1f101fc` or a descendant of it. The current `main` head is a descendant of `1f101fc` (see §8 step 3 for the verification command).

This section deliberately does not require `MASTER_STATUS.md` to name the merge commit that lands a given PR as a "new baseline" — that recursion is unnecessary. The accepted Phase 1 baseline (`1f101fc`) is fixed; subsequent work lives as descendants of it.

### Candidate-baseline history

- **`ee3457f`** — earlier candidate during Phase 1 cleanup. Superseded.
- **`b39d036`** — candidate baseline proposed for external verification per `EXTERNAL_REVIEW_BRIEF.md` and `docs/decisions/PHASE_1_COMPLETION_SUMMARY.md`. Superseded by `1f101fc` when Kevin accepted Phase 1 on PR #3; not the accepted baseline.
- **`1f101fc`** — accepted Phase 1 baseline (current).

`EXTERNAL_REVIEW_BRIEF.md` and `docs/decisions/PHASE_1_COMPLETION_SUMMARY.md` still reference `b39d036` because they are point-in-time review artifacts from the Phase 1 verification request, not live state. They should not be read as overriding this section.

### P2-01 authorization is separate from the baseline

Kevin's written authorization for PR P2-01 (package skeleton and test harness, see `plan/phase2_entry_plan.md` §4) is recorded in §1, §5, §7, and §8. P2-01 does not change the accepted Phase 1 baseline; it opens Phase 2 implementation narrowly on top of that baseline. Any future change to the accepted Phase 1 baseline must be recorded audit-visibly — in this section and in the PR that lands it — and must not silently substitute a different baseline (`AI_WORKFLOW.md` §3 covers the proof-bundle requirements that make this enforceable).

---

## 4. Machine Setup

The repository is worked on from two machines. These are the current known checkout paths; the canonical reference is "the home-directory checkout on each machine," and the literal paths below are recorded for convenience, not as a constraint. If a machine's path changes, update this section.

| Machine | Current known checkout path |
| --- | --- |
| MacBook Pro | `~/gmc-rebuild` |
| Mac Studio | `~/gmc-rebuild` (i.e. `/Users/<kevin's user>/gmc-rebuild`) |

Rules:

- Never work on both machines simultaneously on the same branch.
- Before starting a session, `git fetch` and confirm the local branch matches the remote.
- Never commit machine-local files, virtual environments, caches, secrets, local databases, logs, or generated data. `.gitignore` enforces this; do not bypass it.
- Python 3.12 is the required interpreter on both machines. If `python3.12` is not the default, install it and use the explicit executable.

---

## 5. What Phase 1 (and the Merged P2-01..P2-05 Implementations) Contains

The repository contains, and only contains:

- Governance documents (`MASTER_STATUS.md`, `AI_WORKFLOW.md`, `README.md`, `plan/rebuild_plan.md`).
- Verification-facing documents: `EXTERNAL_REVIEW_BRIEF.md` (the request) and `docs/decisions/PHASE_1_COMPLETION_SUMMARY.md` (the submission).
- Accepted architecture decision records under `docs/decisions/ADR-*.md`.
- Templates for ADRs, deployment logs, daily monitoring reports, and review requests.
- Project configuration: `pyproject.toml`, `.pre-commit-config.yaml`, `.gitignore`, `.secrets.baseline`.
- Phase 1 governance placeholder tests plus the P2-01 skeleton tests, P2-02 config schema tests, P2-03 UTC time utility tests, P2-04 structured-logging and audit-event tests, and P2-05 risk-control interface tests under `tests/`.
- The P2-01 package skeleton at `src/gmc_rebuild/`: an importable package with `__init__.py`, a `__version__` string, and a `py.typed` marker. No runtime behavior.
- The P2-02 config submodule at `src/gmc_rebuild/config/`: an `__init__.py` and a single `schema.py` defining a frozen dataclass `ProjectConfig` (project metadata fields only) and a `default_config()` helper. Safe-by-default and local-only. No runtime-behavior boolean flags (even disabled ones). No env-var loading, no credentials, no real broker / account / venue identifiers, no live or paper toggles, no `__main__` entry point, no filesystem materialisation. The `local_data_dir` default is `./gmc_data` rather than `./data` so it cannot collide with the §8 step 4 always-forbidden top-level `data` if a future authorized caller were ever to create the directory. Authorized by `governance/authorizations/2026-05-11_p2-02.md`.
- The P2-03 UTC time utility submodule at `src/gmc_rebuild/time/`: ADR-004-aligned `now_utc()` plus parsing/formatting helpers that reject timezone-naive datetimes at the API boundary. No env-var loading, no `__main__` entry point, no filesystem materialisation. Authorized by `governance/authorizations/2026-05-12_p2-03.md`.
- The P2-04 structured-logging and audit-event submodule at `src/gmc_rebuild/logging/`: a logging configuration module and an `audit_event` helper that produces structured records with documented fields. Output is to the standard logger only — no external sink, no runtime daemon, no env-var loading, no `__main__` entry point. Authorized by `governance/authorizations/2026-05-12_p2-04.md`.
- The P2-05 risk-control interfaces submodule at `src/gmc_rebuild/risk/`: abstract `typing.Protocol` definitions (`KillSwitchProtocol`, `ReconciliationProtocol`, `HeartbeatProtocol`) and supporting frozen dataclasses and enums for the kill-switch (ADR-002), reconciliation (ADR-003), and heartbeat (ADR-005) boundaries. **Types and abstract boundaries only.** No broker SDK is imported, no network or filesystem call is made, no `__main__` entry point exists, no scheduler / background thread / daemon is started, no order object or order placement is added, no market-data ingestion is added, no env-var loading is performed, no concrete implementation of any of the protocols lives inside the runtime package, and no real account / venue / broker identifiers are embedded. Authorized by `governance/authorizations/2026-05-12_p2-05.md`.
- ADR-008 (`docs/decisions/ADR-008_monitoring_cadence_and_ai_monitor_role.md`): the governance decision that clarifies the backup-AI monitor role and the monitoring cadence rule. Governance only; no runtime code added.

---

## 6. What Is Explicitly Not Present

The repository contains **none** of the following. If any of these appear in a diff, the change is out of scope and must be rejected at review.

Always-forbidden (no current authorization, regardless of phase):

- Trading strategy code (signals, scanners, models, portfolio rules, backtests).
- Broker execution code (order placement, position management, broker SDK integration).
- Live trading workflows or paper-trading workflows wired to a real broker.
- Runtime daemons, schedulers, long-running services, or background workers that touch accounts, markets, or money.
- Market data ingestion code, real data pipelines, or stored datasets.
- Secrets, private keys, certificates, `.env` files, local databases, or generated reports.

Phase 2 implementation is forbidden **except** for tasks named in an accepted Phase 2 PR and recorded on the §8 step 4a allowlist. At the time of writing, the authorized Phase 2 implementation tasks are:

- **PR P2-01 — package skeleton and test harness.** Authorizes the importable `src/gmc_rebuild/` layout, the corresponding pytest fixtures under `tests/`, and the minimal `pyproject.toml` package-discovery wiring. Does not authorize unrelated submodules, runtime behavior, or any of the always-forbidden categories above.
- **PR P2-02 — minimal safe config schema.** Authorizes the `src/gmc_rebuild/config/` submodule with a single `schema.py` defining an immutable, safe-by-default `ProjectConfig` dataclass and a `default_config()` helper, plus matching tests under `tests/`. Does not authorize env-var loading, real credentials, real broker / account / venue identifiers, any runtime-behavior boolean toggle (even disabled), filesystem materialisation of any default path, or any of the always-forbidden categories above. Recorded at `governance/authorizations/2026-05-11_p2-02.md`.
- **PR P2-03 — UTC time utility.** Authorizes the `src/gmc_rebuild/time/` submodule (ADR-004-aligned `now_utc()` plus parsing/formatting helpers that reject naive datetimes at the API boundary), plus matching tests under `tests/`. Authorization slice landed at `governance/authorizations/2026-05-12_p2-03.md`; both halves (authorization slice and implementation) are merged. Does not authorize trading signals, broker / account / order-management logic, market-data ingestion, persistent storage, schedulers or background jobs, expansion into P2-04/P2-05, or any of the always-forbidden categories above.
- **PR P2-04 — Structured logging and audit event conventions.** Authorizes the `src/gmc_rebuild/logging/` submodule (logging configuration and an `audit_event` helper that emits structured records to the standard logger only — no external sink, no runtime daemon, no env-var loading, no `__main__` entry point), plus matching tests under `tests/`. Authorization slice landed at `governance/authorizations/2026-05-12_p2-04.md`; both halves (authorization slice and implementation) are merged. Does not authorize trading signals, broker / account / order-management logic, market-data ingestion, persistent storage, schedulers or background jobs, external log sinks, expansion into P2-05, or any of the always-forbidden categories above.
- **PR P2-05 — Risk-control interfaces.** Authorizes the `src/gmc_rebuild/risk/` submodule restricted to abstract `typing.Protocol` definitions and supporting frozen dataclasses and enums for the kill-switch (ADR-002), reconciliation (ADR-003), and heartbeat (ADR-005) boundaries, plus matching tests under `tests/`. Authorization slice landed at `governance/authorizations/2026-05-12_p2-05.md`; both halves (authorization slice and implementation) are merged. **Types and abstract boundaries only.** Does not authorize trading signals, broker / account / order-management logic (no broker SDK, no order objects, no order placement), market-data ingestion, persistent storage, schedulers / background jobs / runtime daemons, external sinks, env-var loading inside the risk submodule, any concrete runtime implementation of the protocols inside the runtime package, any Phase 3+ behavior, or any of the always-forbidden categories above.

P2-05 is the final task in `plan/phase2_entry_plan.md` §4. No Phase 2 task beyond P2-05 and no Phase 3+ item is authorized; any such work requires its own separate written authorization per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 ("One approver") / rule 7 ("No phase drift"). A PR that introduces work outside the §8 step 4a allowlist must be rejected at review.

---

## 7. Phase 2 Boundary

Phase 1 was accepted by Kevin in writing on PR #3 against `1f101fc` (see §3). Phase 2 implementation was conducted under the following conditions, which have already been recorded. **Phase 2 is now formally closed (governance-only) at the current `main` checkpoint after PR #23 per Kevin's written authorization at `governance/authorizations/2026-05-12_phase-2-closure.md`; the closure does not open Phase 3 or any new implementation path.**

1. Accepted Phase 1 baseline established at `1f101fc` and recorded in §3.
2. `plan/phase2_entry_plan.md` merged on `main` (commit `04faaa1`) and referenced from `README.md`.
3. `MASTER_STATUS.md` §8 reconciled to distinguish always-forbidden categories (step 4) from a per-PR Phase 2 infrastructure allowlist (step 4a). The reconciliation landed in commit `5c84d85` ("docs: reconcile MASTER_STATUS startup checks").
4. Kevin's explicit written authorization for PR P2-01 (package skeleton and test harness, per `plan/phase2_entry_plan.md` §4), PR P2-02 (minimal safe config schema, per `plan/phase2_entry_plan.md` §4), PR P2-03 (UTC time utility — governance-only authorization slice; allowlist extension only, no implementation, per `plan/phase2_entry_plan.md` §4), PR P2-04 (structured logging and audit event conventions — governance-only authorization slice; allowlist extension only, no implementation, per `plan/phase2_entry_plan.md` §4), and PR P2-05 (risk-control interfaces — governance-only authorization slice; allowlist extension only, no implementation, per `plan/phase2_entry_plan.md` §4). The durable in-tree copies of those authorizations are recorded at `governance/authorizations/2026-05-11_p2-01.md`, `governance/authorizations/2026-05-11_p2-02.md`, `governance/authorizations/2026-05-12_p2-03.md`, `governance/authorizations/2026-05-12_p2-04.md`, and `governance/authorizations/2026-05-12_p2-05.md`; GitHub PR #6 history (merged at `e0278c4`) remains supporting evidence for P2-01, the merged P2-02 PR is the corresponding evidence for P2-02, the merged P2-03 authorization PR is the corresponding evidence for the P2-03 authorization slice, the merged P2-04 authorization PR is the corresponding evidence for the P2-04 authorization slice, and the P2-05 authorization PR is the corresponding evidence for the P2-05 authorization slice.

What this means in practice:

- The §8 step 4a allowlist currently contains exactly `src/` (authorizing P2-01's importable `src/gmc_rebuild/` skeleton), `src/gmc_rebuild/config/` (authorizing the P2-02 config schema submodule), `src/gmc_rebuild/time/` (authorizing the P2-03 UTC time utility submodule), `src/gmc_rebuild/logging/` (authorizing the P2-04 structured-logging and audit-event submodule), and `src/gmc_rebuild/risk/` (authorizing the P2-05 risk-control interfaces submodule — types and abstract boundaries only). All five P2-01..P2-05 tasks are merged on `main`. **Phase 2 is formally closed (governance-only) at the current `main` checkpoint after PR #23 per `governance/authorizations/2026-05-12_phase-2-closure.md`; the closure does not extend this allowlist.** No other Phase 2 infrastructure paths are authorized.
- P2-05 is the final task in `plan/phase2_entry_plan.md` §4 P2-01..P2-05 sequence and is merged. Phase 2 is formally closed. Any work beyond this closure — Phase 3 entry, a Phase 2 task not in the §4 sequence, runtime work, broker integration, market-data integration, order management, strategy logic, scheduling, persistence, or deployment — is **not** authorized by this closure. It requires its own written authorization from Kevin per `AI_WORKFLOW.md` §6 rule 3 ("One approver") and rule 7 ("No phase drift"), a sibling authorization artifact under `governance/authorizations/` per `AI_WORKFLOW.md` §7, any applicable runtime-cadence ADR follow-up (ADR-008 §D6), Mode A / Mode B review per `AI_WORKFLOW.md` §4 and ADR-008 where required, and (where it introduces a directory) a corresponding update to the §8 step 4a allowlist in the PR that introduces the directory.
- The always-forbidden categories in §6 and `plan/phase2_entry_plan.md` §2 remain forbidden regardless of mode. Authorizing and merging P2-01..P2-05, and formally closing Phase 2 governance-only, does not authorize any Phase 3+ behavior, does not authorize env-var loading of secrets, and does not authorize any runtime entry point. The P2-05 implementation in particular is restricted to abstract `typing.Protocol` definitions and supporting frozen dataclasses; **no concrete runtime implementation that talks to a broker, network, filesystem, or scheduler lands under `src/gmc_rebuild/risk/`**.
- Any pull request that introduces strategy logic, broker integration, live or paper trading wired to a real broker, runtime daemons affecting accounts, real market data ingestion, order placement, or real secrets must be closed without merge, even if it is presented as "Phase 2 infrastructure."

The proof bundle required for every Phase 2 PR is defined in `plan/phase2_entry_plan.md` §6.

---

## 8. Required Startup Verification Commands

Run these in order at the start of every serious work session. Do not skip steps. Stop at the first failure and resolve it before continuing.

The boundary check in step 4 distinguishes two modes. Phase 2 implementation is **partially open** at the time of writing: Kevin has authorized PR P2-01 (package skeleton and test harness), PR P2-02 (minimal safe config schema), PR P2-03 (UTC time utility), PR P2-04 (structured logging and audit event conventions), and PR P2-05 (risk-control interfaces — types and abstract boundaries only) per `plan/phase2_entry_plan.md` §4, which name `src/`, `src/gmc_rebuild/config/`, `src/gmc_rebuild/time/`, `src/gmc_rebuild/logging/`, and `src/gmc_rebuild/risk/` as the authorized Phase 2 infrastructure directories. All five tasks are merged on `main`; Phase 2 is *not* declared closed by these merges. Step 4a below therefore runs in Phase 2 implementation mode restricted to that allowlist. The Phase 2 implementation mode applies only to directories named in an accepted Phase 2 task or PR; any other Phase 2 infrastructure path is STOP. Switching modes does not silently relax controls: forbidden categories (strategy, broker execution, live or paper trading wired to a real broker, runtime daemons affecting accounts, real market data ingestion, order placement, secrets) remain STOP unless and until a later gate specifically authorizes them.

Step 4 only inspects top-level paths. Step 4c below augments it with a recursive scan that walks every path component in the working tree, tokenizes each component on dot, hyphen, and underscore, and flags any token (or consecutive `_`-joined token pair) that matches the forbidden set. Tokenization is what catches forbidden concepts hiding under the now-allowlisted `src/` subtree (`src/strategy/`, `src/gmc_rebuild/broker.py`, `src/gmc_rebuild/orders/`, `src/gmc_rebuild/signals.py`), multi-dot extensions (`strategy.tar.gz`, `broker.test.py`), and hyphen/underscore compounds (`market-data.py`, `order_book.py`, `sub-strategy/`). Whole-token matching means innocuous names that merely contain a forbidden substring (e.g. `database.py`, `dataclass_helper.py`) are not flagged. The recursive scan is a human-run startup gate, not a substitute for code review: it matches names, not intent, and it cannot detect a forbidden concept implemented under a benign filename. Code review and the `plan/phase2_entry_plan.md` §6 proof bundle remain the authoritative checks. Step 4c's subshell exits non-zero on any STOP, so automation and `set -e` callers can rely on `$?`.

```bash
# 1. Confirm working tree state
git status

# 2. Confirm branch and recent history
git log --oneline -10
git rev-parse HEAD

# 3. Confirm you are on or descended from the accepted Phase 1 baseline
#    Accepted Phase 1 baseline: 1f101fc (per Kevin's written acceptance on PR #3;
#    supersedes the candidate b39d036 noted in §3). Current main descendant at
#    time of writing: 04faaa1 (plan: add Phase 2 entry plan).
git merge-base --is-ancestor 1f101fc HEAD && echo "OK: descended from 1f101fc" || echo "STOP: not descended from accepted Phase 1 baseline 1f101fc"

# 4. Confirm the Phase 1 / Phase 2 boundary is intact.
#    Always-forbidden categories (STOP in both modes unless a later, specific
#    gate authorizes them): strategy, signals, scanners, models, portfolio,
#    backtests, broker, execution, live, paper trading wired to a real broker,
#    runtime daemons affecting accounts, real market data ingestion, order
#    placement, secrets. These names are illustrative; the categories apply
#    regardless of where the code is placed. The loop below reports each
#    forbidden path individually and matches both files and directories, so a
#    single forbidden entry (e.g. an `orders/` directory or a `secrets` file)
#    cannot hide behind sibling missing paths the way it could with a
#    multi-arg `ls`.
unset found
for path in strategy strategies signal signals scanner scanners model models \
            portfolio backtest backtests broker execution live paper daemons \
            data market_data orders secrets; do
  if [ -e "$path" ]; then
    echo "STOP: always-forbidden category present: $path"
    found=1
  fi
done
[ "${found:-0}" -eq 0 ] && echo "OK: no always-forbidden category paths"

# 4a. Phase 2 implementation mode — restricted to directories authorized by an
#     accepted Phase 2 task or PR. The allowlist below is exactly the set of
#     Phase 2 infrastructure paths Kevin has authorized in writing:
#       - src/                       → authorized by PR P2-01 (package skeleton
#                                      and test harness), see
#                                      plan/phase2_entry_plan.md §4 and the
#                                      durable in-tree record at
#                                      governance/authorizations/2026-05-11_p2-01.md.
#       - src/gmc_rebuild/config/    → authorized by PR P2-02 (minimal safe
#                                      config schema), see
#                                      plan/phase2_entry_plan.md §4 and the
#                                      durable in-tree record at
#                                      governance/authorizations/2026-05-11_p2-02.md.
#       - src/gmc_rebuild/time/      → authorized by PR P2-03 (UTC time
#                                      utility); authorization slice and
#                                      implementation both merged. See
#                                      plan/phase2_entry_plan.md §4 and the
#                                      durable in-tree record at
#                                      governance/authorizations/2026-05-12_p2-03.md.
#       - src/gmc_rebuild/logging/   → authorized by PR P2-04 (structured
#                                      logging and audit event conventions);
#                                      authorization slice and implementation
#                                      both merged. See
#                                      plan/phase2_entry_plan.md §4 and the
#                                      durable in-tree record at
#                                      governance/authorizations/2026-05-12_p2-04.md.
#       - src/gmc_rebuild/risk/      → authorized by PR P2-05 (risk-control
#                                      interfaces — abstract Protocols and
#                                      supporting frozen dataclasses for the
#                                      kill-switch (ADR-002), reconciliation
#                                      (ADR-003), and heartbeat (ADR-005)
#                                      boundaries; types and abstract
#                                      boundaries only, no broker integration);
#                                      authorization slice and implementation
#                                      both merged. See
#                                      plan/phase2_entry_plan.md §4 and the
#                                      durable in-tree record at
#                                      governance/authorizations/2026-05-12_p2-05.md.
#     A Phase 2 infrastructure path present but not on this allowlist is STOP;
#     reconcile before continuing. The always-forbidden categories in step 4
#     still apply unchanged in this mode.
allowed_p2_infra="src src/gmc_rebuild/config src/gmc_rebuild/time src/gmc_rebuild/logging src/gmc_rebuild/risk"
unset p2_infra_found
for path in src src/gmc_rebuild/config src/gmc_rebuild/time src/gmc_rebuild/logging src/gmc_rebuild/risk; do
  if [ -e "$path" ]; then
    case " $allowed_p2_infra " in
      *" $path "*)
        case "$path" in
          src)                       pr_tag="PR P2-01" ;;
          src/gmc_rebuild/config)    pr_tag="PR P2-02" ;;
          src/gmc_rebuild/time)      pr_tag="PR P2-03" ;;
          src/gmc_rebuild/logging)   pr_tag="PR P2-04" ;;
          src/gmc_rebuild/risk)      pr_tag="PR P2-05" ;;
          *)                         pr_tag="(allowlisted)" ;;
        esac
        echo "OK: Phase 2 infrastructure present and authorized: $path ($pr_tag)"
        ;;
      *)
        echo "STOP: Phase 2 infrastructure present but not authorized: $path (see plan/phase2_entry_plan.md)"
        p2_infra_found=1
        ;;
    esac
  fi
done
[ "${p2_infra_found:-0}" -eq 0 ] && echo "OK: Phase 2 infrastructure paths conform to P2-01/P2-02/P2-03/P2-04/P2-05 allowlist"

# 4b. Phase 2 implementation mode is operating under the P2-01, P2-02, P2-03,
#     P2-04, and P2-05 allowlist in step 4a. P2-05 is the final task in the
#     `plan/phase2_entry_plan.md` §4 P2-01..P2-05 sequence and is merged;
#     extending the allowlist for any task beyond P2-05 requires a separate
#     written authorization from Kevin, a sibling authorization artifact
#     under `governance/authorizations/`, and a corresponding update to the
#     `allowed_p2_infra` variable above (and the matching comment block
#     referencing the authorizing PR number) in the same PR that adds the new
#     directory. Step 4 (always-forbidden categories) still applies in this
#     mode; switching modes never relaxes those categories. All five
#     allowlisted directories have been materialised on `main` by their
#     respective implementation PRs; the `src/gmc_rebuild/risk/` directory in
#     particular contains only types and abstract `typing.Protocol`
#     boundaries, with no concrete runtime implementation of any protocol
#     inside the runtime package.

# 4c. Recursive audit of forbidden category names anywhere in the tree.
#     Step 4 only inspects top-level paths, so a forbidden concept could in
#     principle hide one level down (e.g. src/strategy/, src/gmc_rebuild/
#     broker.py, src/gmc_rebuild/orders/, src/gmc_rebuild/signals.py). This
#     step walks the working tree and, for every path component, tokenizes
#     the name on dot, hyphen, and underscore and compares each token
#     case-insensitively against the forbidden set. Each consecutive pair
#     of tokens joined by underscore is also compared, so compound entries
#     like `market_data` still match `market-data.py` and `market.data.py`.
#     Tokenizing instead of stem-stripping is what closes the multi-dot
#     (e.g. `strategy.tar.gz`, `broker.test.py`) and hyphen/underscore
#     compound (e.g. `market-data.py`, `order_book.py`, `sub-strategy/`)
#     gaps. Whole-token comparison avoids broad substring false positives:
#     `database.py` tokenizes to [database, py] and does not match `data`;
#     `dataclass_helper.py` tokenizes to [dataclass, helper, py] and does
#     not match either. Three files are explicitly allowlisted by exact
#     relative path; nothing else is exempt.
#
#     The prune list uses -name (not -path), so the excluded directories
#     are skipped at any depth — a nested .venv/, __pycache__/, build/,
#     dist/, .tox/, etc. is not walked.
#
#     This is a human-run startup gate intended to catch obvious phase-
#     drift mistakes early. It is a name-based audit, not a substitute
#     for code review: it cannot judge intent, semantics, or content,
#     and a forbidden concept implemented inside a benignly-named file
#     will not be caught. Code review and the proof bundle in
#     plan/phase2_entry_plan.md §6 remain the authoritative checks. A
#     non-zero exit from this step is a STOP.
# Wrapped in a subshell so the exit 1 below only terminates the
# subshell, not the surrounding interactive shell. The subshell's exit
# status is then available as $? for automation or `set -e` callers.
(
  forbidden=" strategy strategies signal signals scanner scanners model \
              models portfolio backtest backtests broker brokers execution \
              executions live paper daemon daemons market_data order \
              orders secret secrets "
  matches=$(
    find . \
        \( -name .git -o -name .venv -o -name venv -o -name env \
           -o -name .mypy_cache -o -name .pytest_cache -o -name .ruff_cache \
           -o -name __pycache__ -o -name build -o -name dist \
           -o -name '*.egg-info' -o -name node_modules -o -name .tox \
        \) -prune -o \( -type f -o -type d \) -print \
      | awk -v forb="$forbidden" '
          {
            rel = $0; sub(/^\.\//, "", rel)
            if (rel == "." || rel == "") next
            # Audit-visible allowlist. Each entry is an exact relative path.
            if (rel == "src/gmc_rebuild/__init__.py") next
            if (rel == "src/gmc_rebuild/py.typed") next
            if (rel == ".secrets.baseline") next
            if (rel == "docs/decisions/ADR-001_secrets_management.md") next
            n = split(rel, parts, "/")
            for (i = 1; i <= n; i++) {
              comp = parts[i]
              m = split(comp, toks, /[._-]+/)
              for (j = 1; j <= m; j++) {
                tk = tolower(toks[j])
                if (tk == "") continue
                if (index(forb, " " tk " ") > 0) {
                  printf "STOP: forbidden token %s in path: %s\n", tk, rel
                }
                if (j < m) {
                  nx = tolower(toks[j+1])
                  if (nx != "") {
                    pair = tk "_" nx
                    if (index(forb, " " pair " ") > 0) {
                      printf "STOP: forbidden compound %s in path: %s\n", \
                             pair, rel
                    }
                  }
                }
              }
            }
          }')
  if [ -n "$matches" ]; then
    printf '%s\n' "$matches"
    exit 1
  fi
  echo "OK: no forbidden category names found anywhere in tree"
)

# 5. Confirm tooling is installed and matches committed versions
python --version          # expect Python 3.12.x
pre-commit --version

# 6. Run the full quality gate
pre-commit run --all-files

# 7. Run tests
pytest
```

If any step fails, document the failure in the session log and stop. Do not "fix" by widening scope. In particular, do not extend the `allowed_p2_infra` allowlist in step 4a, the `forbidden` set or per-path allowlist in step 4c, or any other startup-gate filter without Kevin's explicit written authorization per §7 and a specific accepted Phase 2 task or PR that names the directory; per `AI_WORKFLOW.md` §6 rule 3 ("One approver") and rule 7 ("No phase drift"), the phase boundary cannot be moved by Codex or Perplexity Computer alone, and per rule 8, tooling hooks (pre-commit, mypy strict, detect-secrets) may not be weakened to make a failure go away. The directories currently on the allowlist are `src/` (PR P2-01, merged), `src/gmc_rebuild/config/` (PR P2-02, merged), `src/gmc_rebuild/time/` (PR P2-03, merged), `src/gmc_rebuild/logging/` (PR P2-04, merged), and `src/gmc_rebuild/risk/` (PR P2-05, merged — types and abstract boundaries only) — see `plan/phase2_entry_plan.md` for the full P2-01..P2-05 sequence and the Phase 2 entry criteria.

---

## 9. Next Allowed Decisions

Only the following decisions are in scope right now. Any other change requires Kevin's explicit approval.

1. Editing or extending governance documentation: `MASTER_STATUS.md`, `AI_WORKFLOW.md`, `README.md`, `plan/rebuild_plan.md`, `EXTERNAL_REVIEW_BRIEF.md`.
2. Authoring and committing monitoring packets under `monitoring/daily/` (including catch-up notes per ADR-008 §D5) when the cadence rule in ADR-008 §D3 requires one. The Backup AI may author packet text under Mode B; Codex commits it (see `AI_WORKFLOW.md` §1.4 and §6 rule 1).
3. Editing or extending ADRs and the four templates under `docs/` and adjacent directories, in line with the existing structure.
4. Fixing documented blockers raised by external verification, scoped to Phase 1 only.
5. Repository hygiene: `.gitignore`, `.pre-commit-config.yaml`, `pyproject.toml`, `.secrets.baseline`, where the change strictly preserves Phase 1 invariants.
6. Updating Phase 1 placeholder tests in `tests/` so they continue to verify governance artifacts, not behavior.
7. Recording Kevin's decisions to open, expand, or close phases. Phase 2 is formally closed (governance-only) at the current `main` checkpoint after PR #23 per `governance/authorizations/2026-05-12_phase-2-closure.md`. **Phase 3 entry planning** has been authorized on 2026-05-13 as a governance/documentation-only workstream per `governance/authorizations/2026-05-13_phase-3-entry-planning.md`; that authorization is planning-only and does **not** open Phase 3, does **not** authorize any Phase 3 implementation, does **not** extend the §8 step 4a allowlist, and does **not** modify any quality gate. **P3-01 has merged on `main`** (ADR-009 drafted under `governance/authorizations/2026-05-13_p3-01.md`, revised by PR #32, accepted under `governance/authorizations/2026-05-13_p3-01-acceptance.md`), closing the ADR-008 §D6 follow-up. **P3-02 preparation** has merged on 2026-05-13 as governance/documentation-only preparation prose per `governance/authorizations/2026-05-13_p3-02-preparation.md` (PR #36); preparation is preparation-only and did **not** open Phase 3, did **not** authorize P3-02 itself, did **not** extend the §8 step 4a allowlist, did **not** modify any quality gate, and did **not** add or modify any file under `src/**` or `tests/**`. **P3-02 entry** has been authorized on 2026-05-13 by Kevin's separate written authorization per `governance/authorizations/2026-05-13_p3-02.md` and **formally opens Phase 3 as a governance state** on the merge of the P3-02 entry PR; the entry is governance/documentation only and does **not** authorize any Phase 3 implementation, does **not** authorize P3-03, does **not** extend the §8 step 4a allowlist (the five P2-01..P2-05 entries are preserved exactly), does **not** modify any quality gate, and does **not** add or modify any file under `src/**` or `tests/**` — it is pending Mode A review per `AI_WORKFLOW.md` §4(1) (phase gate) and a separate sibling Mode B monitoring packet merged to `main` before the P3-02 entry PR merges per ADR-008 §D5. Every phase-opening, phase-expanding, or phase-closing authorization (P2-02, P2-03, …, the Phase 2 closure, Phase 3 entry planning, P3-01 drafting, P3-01 acceptance, P3-02 preparation, P3-02 entry, and any later phase) must be mirrored as a durable in-tree artifact under `governance/authorizations/` per `AI_WORKFLOW.md` §7, before or as part of the authorized PR. *(Maintainer note: the P3-02 entry cross-reference is added by the P3-02 entry PR itself; per `AI_WORKFLOW.md` §1.2 / §6 rule 2 ("One status keeper"), this status edit is subject to Perplexity Computer's verification before being treated as the canonical status, and is intentionally conservative — it records the Phase 3 governance opening without authorizing any Phase 3 implementation and without changing any phase-boundary control beyond opening Phase 3 as a governance state.)*

Decisions that are **not** allowed without a new approval from Kevin:

- Opening Phase 3 or any new Phase 2 task beyond the merged P2-01..P2-05 sequence.
- Adding any code path that touches market data, signals, orders, brokers, or accounts.
- Adding runtime services, schedulers, or long-running processes.
- Relaxing pre-commit, mypy strict mode, or detect-secrets.
- Loosening `.gitignore` to allow secrets, data, or generated state.
