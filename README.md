# gmc-rebuild

`gmc-rebuild` is the governance-first rebuild of Grist Mill Capital's systematic trading infrastructure. The repository currently contains Phase 1 controls: planning, architecture decisions, templates, project configuration, and verification tooling.

## Current Phase

Phase 1 (governance cleanup) was accepted by Kevin in writing on PR #3 against commit `1f101fc`. Phase 2 implementation was conducted as the `plan/phase2_entry_plan.md` §4 P2-01..P2-05 sequence: Kevin authorized PR P2-01 (package skeleton and test harness), PR P2-02 (minimal safe config schema), PR P2-03 (UTC time utility), PR P2-04 (structured logging and audit event conventions), and PR P2-05 (risk-control interfaces — types and abstract boundaries only). Each task was opened as a governance-only authorization slice followed by a narrowly scoped implementation PR; both halves of each task merged as of 2026-05-12 (the §4 P2-01..P2-05 sequence is fully merged). P2-01 created the importable `src/gmc_rebuild/` layout with no runtime behavior; P2-02 added the `src/gmc_rebuild/config/` submodule that exposes a frozen `ProjectConfig` dataclass with safe local-only defaults and no runtime behavior; P2-03 added the `src/gmc_rebuild/time/` UTC time utility submodule (ADR-004-aligned `now_utc()` and parsing/formatting helpers that reject naive datetimes at the API boundary); P2-04 added the `src/gmc_rebuild/logging/` structured-logging and audit-event submodule (logging configuration and an `audit_event` helper that emits structured records to the standard logger only — no external sink, no daemon, no env-var loading); P2-05 added the `src/gmc_rebuild/risk/` risk-control interfaces submodule (ADR-002 / ADR-003 / ADR-005-aligned abstract `typing.Protocol` definitions plus supporting frozen dataclasses and enums — types and abstract boundaries only; no broker integration, no concrete runtime implementation of the protocols inside the runtime package, no `__main__` entry point, no scheduler / daemon, no order objects, no market-data ingestion). **Phase 2 is now formally closed (governance-only) at the current `main` checkpoint after PR #23 per Kevin's written authorization at `governance/authorizations/2026-05-12_phase-2-closure.md`.** The closure is governance-only and **does not open Phase 3, does not open any new Phase 2 task beyond P2-05, does not extend the `MASTER_STATUS.md` §8 step 4a allowlist, does not relax any quality gate, and does not create any tag or release.** Opening Phase 3 or any new Phase 2 task requires Kevin's separate written authorization per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 / rule 7. Strategy code, broker execution, live or paper trading wired to a real broker, runtime daemons affecting accounts, real market data ingestion, order placement, and real secrets remain forbidden — see `MASTER_STATUS.md` §6.

**Phase 3 entry planning** has been authorized on 2026-05-13 as a governance/documentation-only workstream per `governance/authorizations/2026-05-13_phase-3-entry-planning.md`. The authorization is planning-only: it opens the workstream that would draft a Phase 3 entry plan (modeled on `plan/phase2_entry_plan.md`), but it does **not** open Phase 3, does **not** authorize any Phase 3 implementation, does **not** extend the `MASTER_STATUS.md` §8 step 4a allowlist, does **not** modify any quality gate, and does **not** modify any file under `src/**` or `tests/**`. Opening Phase 3 itself remains a future, separate written authorization from Kevin subject to a Mode A adversarial review per `AI_WORKFLOW.md` §4(1).

**P3-01 (ADR-008 §D6 follow-up ADR) has merged.** ADR-009 was drafted in Proposed status under `governance/authorizations/2026-05-13_p3-01.md` (PR #30), revised in Proposed status by PR #32 to address Mode A blocking findings, and accepted (`Status: Proposed` → `Status: Accepted`) under `governance/authorizations/2026-05-13_p3-01-acceptance.md` (PR #34). The ADR-008 §D6 runtime-monitoring-cadence follow-up is therefore **closed** on `main`; ADR-008 §D3 / §D5 continue to govern the governance phase, and ADR-009 D3 / D5 will replace them on a going-forward basis once runtime exists on `main` per ADR-009 D7's bootstrap-avoidance clause. **P3-02 preparation** (governance/documentation-only preparation prose for the Phase 3 entry decision) has merged on 2026-05-13 per `governance/authorizations/2026-05-13_p3-02-preparation.md` (PR #36); preparation was preparation-only and did **not** open Phase 3, did **not** authorize P3-02 itself, did **not** extend the `MASTER_STATUS.md` §8 step 4a allowlist, did **not** modify any quality gate, and did **not** add or modify any file under `src/**` or `tests/**`.

**P3-02 entry has been authorized by Kevin in writing on 2026-05-13 per `governance/authorizations/2026-05-13_p3-02.md` and formally opens Phase 3 as a governance state** on the merge of the P3-02 entry PR. The entry is governance/documentation only and does **not** authorize any Phase 3 implementation, does **not** authorize P3-03, does **not** extend the `MASTER_STATUS.md` §8 step 4a allowlist (the five P2-01..P2-05 entries are preserved exactly), does **not** modify any quality gate, does **not** add or modify any file under `src/**` or `tests/**`, does **not** authorize any runtime / broker / market-data / order / strategy / scheduler / persistence / deployment / env-var / secrets / concrete-risk implementation, and does **not** create any tag or release. The P3-02 entry PR is a phase gate by definition and requires Mode A adversarial review per `AI_WORKFLOW.md` §4(1) and a separate sibling Mode B monitoring packet merged to `main` before the entry PR merges per ADR-008 §D3 / §D5. Opening Phase 3 as a governance state does **not** by itself authorize P3-03 or any further Phase 3 task; each future Phase 3 implementation PR requires its own separate written authorization from Kevin, a sibling artifact under `governance/authorizations/`, an §8 step 4a allowlist update in the same PR that introduces any new directory, and Mode A / Mode B review as applicable.

**P3-03 planning has been authorized by Kevin in writing on 2026-05-13 per `governance/authorizations/2026-05-13_p3-03-planning.md` as a governance/documentation-only workstream.** The planning artifact identifies the proposed first single-protocol test-fixture scope (one of `KillSwitchProtocol` / `ReconciliationProtocol` / `HeartbeatProtocol`; the specific protocol is to be named by Kevin in writing at the time of P3-03 implementation authorization), the expected future files / directories the future P3-03 implementation PR would introduce (anticipated `src/gmc_rebuild/<protocol>/` plus matching `tests/<protocol>/`), the required §8 step 4a allowlist update (planning-level reference only — **non-operative and pending Kevin's separate written authorization at the time of P3-03 implementation**), the expected quality gates for the future implementation PR, and the expected review risks. The planning artifact is governance/documentation only and does **not** authorize P3-03 implementation, does **not** authorize any Phase 3 implementation, does **not** extend the `MASTER_STATUS.md` §8 step 4a allowlist (the five P2-01..P2-05 entries are preserved exactly), does **not** modify any quality gate, does **not** add or modify any file under `src/**` or `tests/**`, does **not** authorize any runtime / broker / market-data / order / strategy / scheduler / persistence / deployment / env-var / secrets / concrete-risk implementation, and does **not** create any tag or release. The P3-03 planning PR receives Mode A adversarial review against the planning prose (delivered as PR-review text, not committed to the repository) and requires a separate sibling Mode B monitoring packet merged to `main` before the planning PR merges per ADR-008 §D3 / §D5. **P3-03 implementation remains future / not authorized**; the future P3-03 implementation PR will require Kevin's separate written authorization, a sibling artifact under `governance/authorizations/`, an §8 step 4a allowlist update in the same PR that introduces the new `src/gmc_rebuild/<protocol>/` directory, Mode A adversarial review per `AI_WORKFLOW.md` §4(2) (high-risk architecture decision — first concrete behaviour behind a control surface), and a Mode B monitoring packet per ADR-008 §D3 / §D5 (or ADR-009 D3 / D5 once in force per ADR-009 D7's bootstrap-avoidance clause).

## Repository Architecture

| Path | Purpose |
| --- | --- |
| `MASTER_STATUS.md` | Canonical first-read status: current phase, candidate baseline, startup verification, and next allowed decisions |
| `AI_WORKFLOW.md` | Separation of duties: Codex builds, Perplexity Computer verifies, Kevin approves, backup AI reviews adversarially |
| `README.md` | Operating overview, setup, phase gates, and safety rules |
| `plan/rebuild_plan.md` | Canonical rebuild plan and the 12 governance invariants |
| `plan/phase2_entry_plan.md` | Phase 2 entry plan and P2-01..P2-05 sequence (all five tasks merged on `main` as of 2026-05-12; Phase 2 formally closed governance-only at the current `main` checkpoint after PR #23 per `governance/authorizations/2026-05-12_phase-2-closure.md`; no Phase 2 task beyond P2-05 / no Phase 3+ task is authorized without separate written approval) |
| `docs/decisions/ADR-*.md` | Accepted architecture decision records |
| `docs/decisions/ADR-template.md` | Template for future ADRs |
| `docs/decisions/PHASE_1_COMPLETION_SUMMARY.md` | Point-in-time inventory of Phase 1 governance cleanup artifacts (submission side of the Phase 1 verification gate) |
| `docs/decisions/PHASE_2_P2_01_TO_P2_05_CHECKPOINT_SUMMARY.md` | Documentation-only checkpoint inventory recording the merged P2-01..P2-05 task sequence at `main` checkpoint `5c390ff`; not a Phase 2 closure and not a Phase 3 opening |
| `docs/deploys/deploy-log-template.md` | Template for deployment and rollback logs |
| `monitoring/daily/daily-report-template.md` | Template for daily monitoring reports |
| `reviews/review-request-template.md` | Template for independent review requests |
| `.pre-commit-config.yaml` | Local quality gate configuration |
| `pyproject.toml` | Python metadata and tool settings |
| `src/gmc_rebuild/` | Phase 2 infrastructure package skeleton (authorized by PR P2-01; no runtime trading behavior) |
| `src/gmc_rebuild/config/` | Minimal safe config schema (authorized by PR P2-02; frozen `ProjectConfig` dataclass + `default_config()` helper; metadata fields only; no runtime-behavior toggles, no env-var loading, no filesystem materialisation) |
| `src/gmc_rebuild/time/` | UTC time utility submodule (authorized by PR P2-03 — ADR-004-aligned `now_utc()` plus parsing/formatting helpers that reject naive datetimes at the API boundary; no env-var loading, no `__main__`, no filesystem materialisation; merged) |
| `src/gmc_rebuild/logging/` | Structured logging and audit event conventions submodule (authorized by PR P2-04 — logging configuration and an `audit_event` helper emitting structured records to the standard logger only; no external sink, no daemon, no env-var loading, no `__main__`; merged) |
| `src/gmc_rebuild/risk/` | Risk-control interfaces submodule (authorized by PR P2-05 — abstract `typing.Protocol` definitions plus supporting frozen dataclasses and enums for the kill-switch (ADR-002), reconciliation (ADR-003), and heartbeat (ADR-005) boundaries; **types and abstract boundaries only**, no broker integration, no concrete runtime implementation of the protocols inside the runtime package, no `__main__`, no scheduler, no order objects, no market-data ingestion; merged) |
| `governance/authorizations/` | Durable in-tree copies of Kevin's phase-opening, phase-expanding, and phase-closing authorizations, including the formal Phase 2 closure `2026-05-12_phase-2-closure.md` (per `AI_WORKFLOW.md` §7) |
| `tests/` | Governance placeholder tests plus P2-01..P2-05 module tests (config schema, UTC time utility, structured logging / audit events, risk-control interfaces) |

Generated data, logs, local databases, local environments, and secrets are intentionally excluded from Git.

## Governance Workflow

1. Codex builds or edits the requested artifact.
2. Kevin reviews intent, scope, and phase fit.
3. Perplexity Computer (or another independent reviewer) verifies the artifact against the stated requirements.
4. Codex fixes verification findings without expanding scope.
5. Kevin decides whether the phase gate is passed.

The AI workflow is advisory and auditable: Codex builds, Perplexity Computer verifies, Kevin decides. See `AI_WORKFLOW.md` for the full separation of duties (including the formal role definition of "Perplexity Computer" in §1.2), required verification proof, and rules for using a backup AI. See `MASTER_STATUS.md` for the current phase, candidate baseline commit, and required startup verification commands before any session.

## Phase Gates

Phase 1 exit criteria:

- `.gitignore` blocks secrets, local databases, logs, generated data, caches, build outputs, and local environment files.
- All seven ADRs use the same structure and contain complete decisions.
- The four templates are non-empty, practical, and located at the documented paths.
- `pyproject.toml` and `.pre-commit-config.yaml` agree on Ruff, mypy strict mode, pytest, and secret detection.
- `README.md` and `plan/rebuild_plan.md` define the 12 invariants without dangling claims.
- `pre-commit run --all-files` passes or any blocker is documented exactly.

Phase 2 entry criteria (status after the P2-05 implementation merge):

- Phase 1 accepted by Kevin in writing on PR #3 against `1f101fc`. **Satisfied.**
- No unresolved blocker in ADRs, templates, README, tooling, or repo hygiene. **Satisfied.**
- Kevin explicitly authorized Phase 2 implementation, narrowly scoped to PR P2-01, PR P2-02, PR P2-03, PR P2-04, and PR P2-05. **Satisfied for the P2-01..P2-05 sequence only**; all five tasks (each as an authorization slice followed by an implementation PR) are merged on `main`.
- The Phase 2 tasks are infrastructure-only (package skeleton and test harness; minimal safe config schema; UTC time utility; structured logging and audit event conventions; risk-control interfaces restricted to types and abstract `typing.Protocol` boundaries — no broker integration, no concrete runtime implementation of the protocols inside the runtime package; per `plan/phase2_entry_plan.md` §4). **Satisfied.**

P2-05 is the final task in the `plan/phase2_entry_plan.md` §4 P2-01..P2-05 sequence and is merged. **Phase 2 is formally closed (governance-only) at the current `main` checkpoint after PR #23 per `governance/authorizations/2026-05-12_phase-2-closure.md`.** The closure does **not** open Phase 3, does **not** open any new Phase 2 task beyond P2-05, does **not** extend the `MASTER_STATUS.md` §8 step 4a allowlist, does **not** relax any quality gate, and does **not** create any tag or release. Opening Phase 3 or any new Phase 2 task requires Kevin's separate written authorization per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 / rule 7, plus a sibling artifact under `governance/authorizations/`, any applicable runtime-cadence ADR follow-up (ADR-008 §D6), Mode A / Mode B review per `AI_WORKFLOW.md` §4 and ADR-008 where required, and (where it introduces a new directory) a corresponding update to the §8 step 4a allowlist in the same PR.

See `plan/phase2_entry_plan.md` for the full Phase 2 entry plan, the P2-01..P2-05 sequence, required proof per PR, and stop conditions. The point-in-time inventory of the merged P2-01..P2-05 sequence at `main` checkpoint `5c390ff` is recorded in `docs/decisions/PHASE_2_P2_01_TO_P2_05_CHECKPOINT_SUMMARY.md`; that document is documentation-only and is not itself the closure authorization (the closure authorization is `governance/authorizations/2026-05-12_phase-2-closure.md`).

## The 12 Invariants

The canonical definitions live in `plan/rebuild_plan.md`. In short:

1. No live trading before explicit phase approval.
2. No broker execution code before Phase 2 authorization.
3. No trading strategy implementation during Phase 1.
4. Secrets never enter Git.
5. Generated data, local databases, and logs stay out of Git.
6. UTC-aware timestamps are mandatory.
7. Kill switch behavior must fail closed.
8. Reconciliation must be automated before live use.
9. Operator availability must be monitored before live use.
10. Deployment changes require a rollback log.
11. Quality gates must match committed tooling.
12. Independent review is required for phase gates and high-risk changes.

## Setup

```bash
cd ~/gmc-rebuild
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

If Python 3.12 is not the default interpreter, install it first and repeat the setup with the correct executable.

## Pre-commit

Install hooks:

```bash
pre-commit install
```

Run all checks manually:

```bash
pre-commit run --all-files
```

The hook stack includes Ruff linting, Ruff formatting, mypy strict type checking, pytest, detect-secrets, and basic repository hygiene checks.

## Safety Rules

- Do not add live trading code, broker execution code, or trading strategy code without explicit per-task written authorization from Kevin. See `MASTER_STATUS.md` §6 for the always-forbidden category list; none of those categories are authorized at this time.
- Do not commit secrets, private keys, certificates, `.env` files, local databases, logs, or generated market data.
- Use timezone-aware UTC timestamps such as `datetime.now(timezone.utc)` in all future Python examples and code.
- If a safety control is missing or uncertain, stop at the phase gate and document the blocker.

## Decisions

Accepted ADRs:

- ADR-001: Secrets Management Strategy
- ADR-002: Runtime Kill Switch Architecture
- ADR-003: Broker Reconciliation Discipline
- ADR-004: UTC and Timezone Discipline
- ADR-005: Operator Availability Heartbeat
- ADR-006: Deployment and Rollback Logs
- ADR-007: Minimal CI Strategy
- ADR-008: Monitoring Cadence and Backup-AI Monitor Role
- ADR-009: Runtime Monitoring Cadence and Missed-Packet Severity (ADR-008 §D6 follow-up; accepted under `governance/authorizations/2026-05-13_p3-01-acceptance.md`; D3 and D5 replace ADR-008 §D3 / §D5 runtime-phase guidance on a going-forward basis once runtime exists on `main`)

## License

MIT
