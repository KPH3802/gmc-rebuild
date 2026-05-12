# gmc-rebuild

`gmc-rebuild` is the governance-first rebuild of Grist Mill Capital's systematic trading infrastructure. The repository currently contains Phase 1 controls: planning, architecture decisions, templates, project configuration, and verification tooling.

## Current Phase

Phase 1 (governance cleanup) was accepted by Kevin in writing on PR #3 against commit `1f101fc`. Phase 2 implementation is **partially open**: Kevin has authorized PR P2-01 (package skeleton and test harness, see `plan/phase2_entry_plan.md` §4), PR P2-02 (minimal safe config schema), PR P2-03 (UTC time utility — governance-only authorization slice; no implementation lands in the authorizing PR), and PR P2-04 (structured logging and audit event conventions — governance-only authorization slice; no implementation lands in the authorizing PR). P2-01 created the importable `src/gmc_rebuild/` layout with no runtime behavior; P2-02 adds the `src/gmc_rebuild/config/` submodule that exposes a frozen `ProjectConfig` dataclass with safe local-only defaults and no runtime behavior; the P2-03 authorization slice extends the §8 step 4a allowlist to include the future `src/gmc_rebuild/time/` UTC time utility submodule (ADR-004-aligned) but lands no code, no directory, and no tests; the P2-04 authorization slice extends the §8 step 4a allowlist to include the future `src/gmc_rebuild/logging/` structured-logging and audit-event submodule but lands no code, no directory, and no tests. No other Phase 2 task is authorized. Strategy code, broker execution, live or paper trading wired to a real broker, runtime daemons affecting accounts, real market data ingestion, order placement, and real secrets remain forbidden — see `MASTER_STATUS.md` §6.

P2-05 in `plan/phase2_entry_plan.md` §4 is **not** authorized and may not be started without separate written authorization from Kevin, per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 ("One approver"). The P2-03 implementation PR (which lands the actual UTC time utility module under the path authorized for it) is gated by the exit criteria in `governance/authorizations/2026-05-12_p2-03.md`. The P2-04 implementation PR (which would later land the actual structured-logging and audit-event module under the path authorized here) is gated by the exit criteria in `governance/authorizations/2026-05-12_p2-04.md`.

## Repository Architecture

| Path | Purpose |
| --- | --- |
| `MASTER_STATUS.md` | Canonical first-read status: current phase, candidate baseline, startup verification, and next allowed decisions |
| `AI_WORKFLOW.md` | Separation of duties: Codex builds, Perplexity Computer verifies, Kevin approves, backup AI reviews adversarially |
| `README.md` | Operating overview, setup, phase gates, and safety rules |
| `plan/rebuild_plan.md` | Canonical rebuild plan and the 12 governance invariants |
| `plan/phase2_entry_plan.md` | Phase 2 entry plan and P2-01..P2-05 sequence (Phase 2 implementation open for P2-01 and P2-02; P2-03 open as a governance-only authorization slice for `src/gmc_rebuild/time/`; P2-04 open as a governance-only authorization slice for `src/gmc_rebuild/logging/`; P2-05 requires separate written authorization) |
| `docs/decisions/ADR-*.md` | Accepted architecture decision records |
| `docs/decisions/ADR-template.md` | Template for future ADRs |
| `docs/deploys/deploy-log-template.md` | Template for deployment and rollback logs |
| `monitoring/daily/daily-report-template.md` | Template for daily monitoring reports |
| `reviews/review-request-template.md` | Template for independent review requests |
| `.pre-commit-config.yaml` | Local quality gate configuration |
| `pyproject.toml` | Python metadata and tool settings |
| `src/gmc_rebuild/` | Phase 2 infrastructure package skeleton (authorized by PR P2-01; no runtime trading behavior) |
| `src/gmc_rebuild/config/` | Minimal safe config schema (authorized by PR P2-02; frozen `ProjectConfig` dataclass + `default_config()` helper; metadata fields only; no runtime-behavior toggles, no env-var loading, no filesystem materialisation) |
| `src/gmc_rebuild/time/` | UTC time utility submodule (authorization-only slice under PR P2-03 — path added to the §8 step 4a allowlist; not materialised yet; implementation deferred to a separate P2-03 implementation PR per `governance/authorizations/2026-05-12_p2-03.md`) |
| `src/gmc_rebuild/logging/` | Structured logging and audit event conventions submodule (authorization-only slice under PR P2-04 — path added to the §8 step 4a allowlist; not materialised yet; implementation deferred to a separate P2-04 implementation PR per `governance/authorizations/2026-05-12_p2-04.md`) |
| `governance/authorizations/` | Durable in-tree copies of Kevin's phase-opening / phase-expanding authorizations (per `AI_WORKFLOW.md` §7) |
| `tests/` | Phase 1 governance placeholder tests and P2-01 skeleton tests |

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

Phase 2 entry criteria (status as of the P2-04 authorization slice):

- Phase 1 accepted by Kevin in writing on PR #3 against `1f101fc`. **Satisfied.**
- No unresolved blocker in ADRs, templates, README, tooling, or repo hygiene. **Satisfied.**
- Kevin explicitly authorized Phase 2 implementation, narrowly scoped to PR P2-01, PR P2-02, the P2-03 authorization slice, and the P2-04 authorization slice. **Satisfied for P2-01, P2-02, the P2-03 authorization slice, and the P2-04 authorization slice only.**
- The first two Phase 2 tasks are infrastructure-only (package skeleton and test harness; minimal safe config schema; per `plan/phase2_entry_plan.md` §4). **Satisfied.** The P2-03 authorization slice adds `src/gmc_rebuild/time/` to the §8 step 4a allowlist with no implementation; the P2-03 implementation PR remains gated. The P2-04 authorization slice adds `src/gmc_rebuild/logging/` to the §8 step 4a allowlist with no implementation; the P2-04 implementation PR remains gated.

P2-05 requires its own written authorization; the above criteria do not auto-extend to it. The P2-03 implementation PR is governed by the exit criteria in `governance/authorizations/2026-05-12_p2-03.md`. The P2-04 implementation PR is governed by the exit criteria in `governance/authorizations/2026-05-12_p2-04.md`.

See `plan/phase2_entry_plan.md` for the full Phase 2 entry plan, the P2-01..P2-05 sequence, required proof per PR, and stop conditions.

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

## License

MIT
