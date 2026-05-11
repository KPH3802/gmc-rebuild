# ADR-007: Minimal CI Strategy

## Status

Accepted

## Date

2026-05-10 UTC

## Context / Problem

The rebuild needs enforceable local quality gates before production code exists. Phase 1 should keep CI lightweight while ensuring claims about linting, formatting, typing, tests, and secret detection match committed configuration.

## Decision

Use local pre-commit hooks as the Phase 1 and Phase 2 minimum quality gate. The committed configuration must include Ruff linting, Ruff formatting, mypy strict type checking, pytest, and secret detection. GitHub Actions can be added in a later phase if external automation becomes necessary.

## Alternatives Considered

- No automated checks until code exists: too weak for governance claims.
- GitHub Actions immediately: useful later, but heavier than needed before Phase 2 modules exist.
- Manual checklist only: not enforceable and easy to skip.

## Consequences

- Positive: The repository can prove baseline quality checks are runnable before Phase 2 starts.
- Positive: Secrets and local artifacts are less likely to enter Git.
- Negative: First-time setup requires installing pre-commit environments.
- Risk: Hook versions can drift; version bumps must be deliberate and committed.

## Implementation Notes

The Phase 1 hook stack is defined in `.pre-commit-config.yaml`:

- Ruff lint with automatic fixes.
- Ruff format.
- mypy with `strict = true` and `disallow_untyped_defs = true` in `pyproject.toml`.
- pytest, with a governance placeholder test until Phase 2 production modules exist.
- detect-secrets with a committed baseline.
- Basic repository hygiene hooks for YAML, JSON, line endings, merge conflicts, and file size.

The Python project settings are defined in `pyproject.toml` and must stay consistent with this ADR and the README.

## Follow-up Actions

- Install hooks locally with `pre-commit install`.
- Replace the governance placeholder test with real tests as Phase 2 modules are introduced.
- Add coverage enforcement thresholds only when executable production modules exist.
- Revisit GitHub Actions at Phase 3 or earlier if Kevin wants hosted verification.

## Related ADRs

- ADR-001: Secrets Management Strategy
- ADR-004: UTC and Timezone Discipline
- ADR-006: Deployment and Rollback Logs
