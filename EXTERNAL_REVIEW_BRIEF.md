# Phase 1 External Review Brief

**For**: Independent verification
**Date**: 2026-05-11 UTC
**Status**: Ready for verification after governance cleanup
**Repository**: https://github.com/KPH3802/gmc-rebuild

## Scope

This repository is in Phase 1 governance. It contains no trading strategy implementation, no broker execution implementation, and no live trading workflow.

## Artifacts for Review

Core config:

- `.gitignore`
- `.pre-commit-config.yaml`
- `pyproject.toml`
- `.secrets.baseline`
- `README.md`

Templates:

- `docs/decisions/ADR-template.md`
- `docs/deploys/deploy-log-template.md`
- `monitoring/daily/daily-report-template.md`
- `reviews/review-request-template.md`

Architecture decision records:

- `docs/decisions/ADR-001_secrets_management.md`
- `docs/decisions/ADR-002_kill_switch.md`
- `docs/decisions/ADR-003_reconciliation.md`
- `docs/decisions/ADR-004_utc_discipline.md`
- `docs/decisions/ADR-005_heartbeat.md`
- `docs/decisions/ADR-006_deployment_logs.md`
- `docs/decisions/ADR-007_minimal_ci.md`

Supporting plan:

- `plan/rebuild_plan.md`

## Verification Checklist

- All seven ADRs use the same required headings.
- ADR-003 is complete and no longer truncated.
- ADR-004 enforces timezone-aware UTC.
- ADR-005 does not use timezone-naive UTC examples.
- The four templates are non-empty and usable.
- `.gitignore` covers macOS files, Python caches, virtual environments, secrets, local databases, trading/data outputs, logs, build artifacts, and editor temp files.
- JSON files are not blanket-ignored.
- `.pre-commit-config.yaml` includes Ruff lint, Ruff format, mypy, pytest, and detect-secrets.
- `pyproject.toml` matches ADR-007 and README claims.
- README documents current phase, architecture, workflow, phase gates, setup, pre-commit, Phase 2 entry criteria, and safety rules.
- The 12 governance invariants are defined in `plan/rebuild_plan.md` and summarized in `README.md`.

## Phase 2 Boundary

Phase 2 has not started. Any request to add signal logic, broker execution, live trading behavior, or runtime daemons should be rejected until Kevin explicitly opens Phase 2.
