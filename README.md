# gmc-rebuild

`gmc-rebuild` is the governance-first rebuild of Grist Mill Capital's systematic trading infrastructure. The repository currently contains Phase 1 controls: planning, architecture decisions, templates, project configuration, and verification tooling.

## Current Phase

Phase 1 is governance cleanup only. There is no trading strategy code, no broker execution code, no live trading integration, and no Phase 2 implementation in this repository yet.

Phase 2 may start only after Phase 1 passes external verification and Kevin explicitly decides to proceed.

## Repository Architecture

| Path | Purpose |
| --- | --- |
| `MASTER_STATUS.md` | Canonical first-read status: current phase, candidate baseline, startup verification, and next allowed decisions |
| `AI_WORKFLOW.md` | Separation of duties: Codex builds, Perplexity Computer verifies, Kevin approves, backup AI reviews adversarially |
| `README.md` | Operating overview, setup, phase gates, and safety rules |
| `plan/rebuild_plan.md` | Canonical rebuild plan and the 12 governance invariants |
| `docs/decisions/ADR-*.md` | Accepted architecture decision records |
| `docs/decisions/ADR-template.md` | Template for future ADRs |
| `docs/deploys/deploy-log-template.md` | Template for deployment and rollback logs |
| `monitoring/daily/daily-report-template.md` | Template for daily monitoring reports |
| `reviews/review-request-template.md` | Template for independent review requests |
| `.pre-commit-config.yaml` | Local quality gate configuration |
| `pyproject.toml` | Python metadata and tool settings |
| `tests/` | Phase 1 governance placeholder tests |

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

Phase 2 entry criteria:

- Phase 1 external verification is accepted by Kevin.
- No unresolved blocker remains in ADRs, templates, README, tooling, or repo hygiene.
- Kevin explicitly authorizes Phase 2.
- The first Phase 2 task is infrastructure-only unless Kevin approves a narrower implementation plan.

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

The Phase 1 hook stack includes Ruff linting, Ruff formatting, mypy strict type checking, pytest, detect-secrets, and basic repository hygiene checks.

## Safety Rules

- Do not add live trading code in Phase 1.
- Do not add broker execution code in Phase 1.
- Do not add trading strategy code in Phase 1.
- Do not commit secrets, private keys, certificates, `.env` files, local databases, logs, or generated market data.
- Use timezone-aware UTC timestamps such as `datetime.now(timezone.utc)` in all future Python examples and code.
- If a safety control is missing or uncertain, stop at the phase gate and document the blocker.

## Decisions

Accepted Phase 1 ADRs:

- ADR-001: Secrets Management Strategy
- ADR-002: Runtime Kill Switch Architecture
- ADR-003: Broker Reconciliation Discipline
- ADR-004: UTC and Timezone Discipline
- ADR-005: Operator Availability Heartbeat
- ADR-006: Deployment and Rollback Logs
- ADR-007: Minimal CI Strategy

## License

MIT
