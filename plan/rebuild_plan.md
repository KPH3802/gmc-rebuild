# GMC Rebuild Plan

**Status:** v0.4 — Section 3 (Engineering Standards) filled with all five confirmed specifications
**Created:** 2026-05-08
**Last Updated:** 2026-05-08
**Location:** `~/gmc-rebuild/plan/rebuild_plan.md`
**Repo:** `gmc-rebuild` (local; GitHub hosting decision pending)

---

## 1. Purpose

This plan governs the structured rebuild of Grist Mill Capital's systematic trading infrastructure, undertaken May 2026 after a series of audit findings revealed that the existing project's signal foundation, audit trails, and documentation-based enforcement had drifted below the standard required for live capital deployment. The rebuild follows a strict seven-step sequence — data, validation, backtest, stress test, execution, safety stress test, execute — with no step proceeding until the previous step is verifiably complete. Every constraint that can become runtime enforcement becomes runtime enforcement; documentation governs only what genuinely cannot be encoded. Independent AI review gates designated artifacts before they advance. Work follows test-driven, build-it-correctly-from-the-start discipline; patching holes after the fact is explicitly out of bounds — if a defect surfaces, the affected work returns to the appropriate step and is rebuilt to standard, not patched in place. Existing components from the prior project — code, signals, infrastructure — may be carried forward into the rebuild only after passing the same audit bar new work is held to; nothing is grandfathered. The existing project remains in dry-run, unchanged, until the rebuild produces a replacement of equivalent or higher rigor; the live crypto autotrader continues running independently and is itself subject to re-audit before being designated part of the rebuilt system. This plan is the canonical artifact — when scope, sequence, or acceptance criteria change, this plan changes, and the change is committed with a reasoned message.

---

## 2. Principles — The Seven Steps

The rebuild follows a strict sequence. No step proceeds until the previous step is verifiably complete.

1. Get data
2. Verify the data is clean and correct
3. Backtest the data
4. Stress test the findings
5. Build execution
6. Stress test the execution and safety monitors
7. Execute

[Each step's definition and exit criteria filled in Section 7.]

---

## 3. Engineering Standards

The continuous baseline discipline that applies to every artifact produced by this rebuild, regardless of which of the seven steps it belongs to. Engineering standards are the floor; review gates (Section 4) and audit standard (Section 5) are additional bars on top of this floor for designated artifacts.

The no-patches-later principle from Section 1 binds here: when a defect surfaces, work returns to the appropriate step and is rebuilt to standard. Tests catch the bugs we know how to test for; review gates catch the design errors and reasoning failures we don't know to test for; the audit standard is the explicit pass/fail bar. All three layers operate together.

### 3.1 Test-Driven Development

Strict TDD is the default discipline. Every piece of production code begins as a failing test that specifies the behavior the code must exhibit. Code is then written to make the test pass. Refactoring follows, with the test as the safety net. No production code is written without a failing test in front of it.

Exploratory work — checking whether a signal has alpha, whether a data source has the structure expected, whether a hypothesis is worth pursuing — is permitted under different rules. Such work lives in `~/gmc-rebuild/scratch/`, a gitignored directory not subject to TDD or the engineering standards in this section. Code in scratch is never executed against production data, never imported by production code, never counted toward coverage.

Promotion of work from scratch to the main rebuild is a deliberate operation. A scratch script that explores a signal does not become a production scanner by being moved; it becomes a specification, and the production scanner is then written test-first against that specification. The scratch artifact may be referenced in the production module's docstring as historical context, but the production code is written fresh under TDD discipline.

### 3.2 Test Framework and Coverage

The test framework is **pytest**, with **coverage.py** (via the `pytest-cov` plugin) measuring coverage. Both are pinned in the project's dependency manifest with specific versions; updates require a deliberate version bump committed with rationale.

Coverage thresholds are enforced as pre-commit blockers and as CI checks (when CI is added):

- **Signal logic and runtime enforcement code: 100% line + branch coverage.** Includes signal scanners, the autotrader's signal-handling code, runtime safety checks, schema validation, and any code path whose failure could result in incorrect trading behavior.
- **Glue and utility code: 80% line coverage minimum.** Includes data loading helpers, logging, configuration parsing, and similar non-signal infrastructure.
- **Every module containing executable logic must have at least one corresponding test module.** Empty `__init__.py` and pure-data constants modules are exempt because they contain no executable paths.

Coverage thresholds and directory-to-category mapping are stored in `pyproject.toml` (`[tool.coverage.run]` and `[tool.coverage.report]` sections). Threshold changes require a commit with rationale.

### 3.3 Pre-commit Hooks

Pre-commit hooks are blocking, not advisory. A failing hook prevents the commit from being created. The `--no-verify` bypass workflow is treated as a violation of engineering standards; if a hook is wrong, the hook is fixed via a deliberate change, not bypassed.

The required hook stack:

- **ruff (lint + format).** Replaces flake8, isort, black, and pyupgrade with one fast tool. Runs as both linter (catching errors and style violations) and formatter (auto-fixing).
- **mypy (strict mode).** All new code is type-annotated and passes `mypy --strict`. Existing code carried forward from the prior project must add type annotations to clear the audit standard before being designated rebuilt.
- **pytest (all tests pass).** The full test suite must pass before a commit is created. Slow tests can be marked with `@pytest.mark.slow` and excluded from pre-commit but must run in CI.
- **coverage check.** Coverage thresholds in 3.2 must be met. If coverage drops below threshold, the commit is rejected.

Hook configuration lives in `.pre-commit-config.yaml`, committed to the repository, and version-pinned. Hook installation is a setup step documented in the project README and verified by an installation test.

### 3.4 Reproducibility Tests

Every numerical claim made in this rebuild — every backtest result, every benchmark number, every reported alpha — is required to have a reproducibility test that re-runs the producing code and verifies the same number is produced.

The format:

- The producing code (e.g., a backtest script) writes its output to a JSON file alongside the script: `{script_name}_expected_output.json`.
- The JSON file is committed to git.
- A reproducibility test imports the script's main entry point, runs it on the fixed inputs documented in the script, and asserts deep equality between the actual output and the JSON file.
- The test runs on every commit via pre-commit.
- If the producing code or its inputs change in a way that legitimately changes the output, the JSON is regenerated via an explicit `python -m {script_name} --regenerate-expected` workflow. The regeneration commit must include a rationale message explaining why the expected output changed, and the reproducibility test must re-pass against the new expected.

This pattern prevents the CEL_BEAR class of failure: benchmark says one number, backtest output says another, no test catches the gap. With reproducibility tests, the gap is structurally impossible — the test fails and the commit is rejected.

### 3.5 Schema and Migration Discipline

All schema changes — to `signal_benchmarks`, `signal_log`, `positions`, or any other database table this rebuild creates — are managed via **Alembic**.

For every schema change, the same commit must contain:

- **The up migration** (`upgrade()` function in the Alembic revision file).
- **The down migration** (`downgrade()` function in the same file).
- **A test for the up migration** that verifies the schema is in the correct post-upgrade state.
- **A test for the down migration** that verifies the schema is in the correct pre-upgrade state after rollback.

All four artifacts must be in the same commit. A commit containing only some of them is rejected by pre-commit. This prevents the prior project's pattern of one-way schema changes that cannot be rolled back.

Migration test files live under `~/gmc-rebuild/data/migrations/tests/` and follow the naming convention `test_{revision_id}_{up|down}.py`.

### 3.6 Tooling Choices

| Concern | Tool | Notes |
|---|---|---|
| Python | 3.12 | Pinned in `pyproject.toml`. Default choice for current stability and performance; later upgrade is a deliberate operation. |
| Test framework | pytest | Pinned to latest stable. |
| Coverage | coverage.py via pytest-cov | Pinned to latest stable. |
| Linter + formatter | ruff | Replaces flake8 + isort + black + pyupgrade. |
| Type checker | mypy (strict mode) | Required on all new code. |
| Pre-commit framework | pre-commit (https://pre-commit.com) | Hooks defined in `.pre-commit-config.yaml`. |
| Schema migrations | Alembic | Up/down/tests in same commit per 3.5. |
| SQL toolkit | SQLAlchemy 2.x | For typed query construction. |
| Dependency manager | TBD | Open question — Section 10. |

### 3.7 What Good Looks Like

This subsection is filled progressively as the rebuild produces concrete examples that exemplify the standards in 3.1–3.6. It will contain reference examples for:

- A signal scanner with proper test coverage, type annotations, and reproducibility test
- A schema migration with up/down/tests
- A backtest with JSON expected-output and reproducibility test
- A runtime safety check with associated tests

Until those examples exist, this subsection is a placeholder. The first concrete example added here marks the first artifact that has cleared the engineering standards in full.

---

## 4. External Review Gates

Independent AI review is required for designated artifacts before they can be merged or acted on. Reviews are git-tracked artifacts under `~/gmc-rebuild/reviews/`, not conversations.

[Section will define: which artifacts require review, at which points in the sequence, the format of the review request, the format of the review response, how disagreements are adjudicated. To be drafted before Step 1 begins.]

---

## 5. Audit Standard

The concrete specification of the bar every component — newly built or carried forward from the prior project — must clear before being designated part of the rebuilt system. The audit standard is what makes "the same bar new work is held to" (Section 1) a measurable test rather than a phrase.

[Section will define: required artifacts (e.g., backtest script, raw output, methodology document, reproducibility test, test coverage), traceability requirements (every claimed number maps to a specific output), runtime requirements (e.g., schema fields populated, startup checks pass), engineering standard requirements (linked to Section 3), review requirements (which gates from Section 4 apply), and the explicit pass/fail criteria. Carried-forward components and new components are evaluated identically.]

---

## 6. Current State Assessment

Honest read of where each of the seven steps actually stands today, component by component and signal by signal. Distinguishes verified facts from unverified claims. Every entry marked (verified) or (claim, needs verification) with the verification step or claim source named explicitly.

[To be filled. Will draw on the May 8 audit findings, the existing project's git history, and per-signal verification of backtest provenance.]

---

## 7. Step-by-Step Plan

For each of the seven steps in Section 2:

- What "done" looks like (acceptance criteria)
- The work it requires (sub-tasks)
- Dependencies on prior steps
- Engineering standards requirements (linked to Section 3)
- External review requirements (linked to Section 4)
- Audit standard requirements (linked to Section 5)
- Estimated scope (rough order of magnitude only — not a deadline)

[Filled step by step, in order, after Sections 1-6 are complete.]

---

## 8. Order of Work

Sequencing within and across the seven steps, including:

- Critical-path identification
- Parallel tracks where they exist
- Stop-points where the rebuild explicitly pauses for review or decision

[Filled after Section 7.]

---

## 9. Out of Scope

Explicit list of items this rebuild is NOT doing, to prevent scope creep. Items move out of scope by deliberate decision, recorded with rationale.

[Filled progressively as scope decisions are made.]

---

## 10. Open Questions

Items not yet known that need to be resolved before specific phases can begin. Each open question has an owner (Kevin or Claude) and a target resolution point in the sequence.

- **Dependency manager choice (Section 3.6).** Options: Poetry, pip + requirements.txt, uv. Owner: Kevin. Resolution: before Step 1 implementation begins.

---

*v0.4 — Section 3 (Engineering Standards) filled with subsections 3.1 through 3.7. Sections 4 (External Review Gates) and 5 (Audit Standard) are next priority for filling, in that order, before Section 6.*
