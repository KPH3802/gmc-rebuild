# ADR-007: Minimal CI Strategy

**Status**: Accepted

**Date**: 2026-05-10 (UTC)

**Participants**: Kevin Heaney

---

## Problem Statement

Code quality checks (linting, type checking, tests) must run automatically to prevent regressions. For a solo operator in Phase 2, CI infrastructure should be minimal and lightweight.

---

## Decision

**Phase 2**: Use **local pre-commit hooks only** (MVP, zero external CI).

**Phase 3**: Upgrade to GitHub Actions (if team members added or regulatory requirements).

---

## Implementation Details

### Phase 2: Local Pre-Commit Hooks

**Tools configured** (in `.pre-commit-config.yaml`):

1. **Ruff (lint & format)**
   - Auto-fix violations
   - Checks: syntax, complexity, unused imports, style

2. **Mypy (type checking)**
   - Type check with `disallow_untyped_defs = true` (strict)

3. **Pytest (tests)**
   - Run unit + integration tests
   - Coverage target: 80%+

4. **Secret Detection**
   - Find leaked credentials (IB tokens, Coinbase keys, etc.)

5. **Trailing Whitespace / End-of-File**
   - Removes trailing whitespace, ensures newline at EOF

### Installation

```bash
cd ~/gmc-rebuild
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

Hook is now at `.git/hooks/pre-commit`. Runs automatically before every commit.

### Developer Workflow

```bash
git add .
git commit -m "Add PEAD signal"

# Pre-commit checks run automatically:
# ✓ ruff check --fix
# ✓ ruff format
# ✓ mypy
# ✓ pytest
# ✓ detect-secrets

# If checks pass → commit succeeds
# If checks fail → commit blocked, developer fixes and tries again
```

### Phase 3: GitHub Actions (Future)

When Phase 3 begins (go-live or team members added), add GitHub Actions:

```yaml
name: CI
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with: {python-version: '3.12'}
      - run: pip install -e ".[dev]"
      - run: ruff check .

  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with: {python-version: '3.12'}
      - run: pip install -e ".[dev]"
      - run: mypy src/

  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with: {python-version: '3.12'}
      - run: pip install -e ".[dev]"
      - run: pytest --cov=src
```

---

## Rationale

Why local pre-commit MVP for Phase 2?

- Setup: 5 min
- Feedback: Instant
- Offline: Works without network
- Enforced: Cannot commit without passing
- Phase 2 fit: Solo operator, no external CI needed
- Scalable: GitHub Actions added Phase 3 if team grows

---

## Follow-Up Actions

| Action | Timeline |
|--------|----------|
| Install pre-commit locally | Phase 2 start |
| Create tests/ directory structure | Phase 2 |
| Write unit tests for core modules | Phase 2 |
| Prepare GitHub Actions workflow (Phase 3) | Phase 3 start |

---

## Approval

**Decision Made By**: Kevin Heaney (2026-05-10)  
**Status**: Accepted  
**Implementation**: Phase 2 (pre-commit), Phase 3 (GitHub Actions)
