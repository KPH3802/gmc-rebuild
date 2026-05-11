# GMC Rebuild Plan

**Status:** v0.6 — Sections 5 through 10 filled. Initial structural pass complete.
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

Each step's definition and exit criteria are filled in Section 7.

### 2.1 The 12 Governance Invariants

These invariants are mandatory constraints for the rebuild. If an artifact conflicts with an invariant, the artifact is blocked until Kevin approves a documented governance change.

1. **Phase approval controls scope.** No work may enter the next phase until Kevin explicitly approves that phase gate.
2. **No live trading before approval.** Live capital is out of scope until the execute phase has passed all prior gates.
3. **No broker execution before authorization.** Broker execution code and order placement workflows are blocked until Kevin authorizes the implementation phase that contains them.
4. **No trading strategy during governance cleanup.** Phase 1 may document controls only; it may not implement signals, scanners, models, or portfolio rules.
5. **Secrets never enter Git.** Credentials, private keys, certificates, tokens, and local environment files must stay outside version control.
6. **Generated state stays outside Git.** Local databases, logs, raw data, processed data, model outputs, and generated reports are not committed unless a future ADR creates a narrow reproducibility exception.
7. **UTC is mandatory.** Runtime code, docs, reports, and examples use timezone-aware UTC and unambiguous UTC strings.
8. **Safety controls fail closed.** Missing secrets, stale operator heartbeat, reconciliation mismatch, unavailable broker state, or active kill switch must stop future runtime trading behavior.
9. **Reconciliation precedes live use.** Automated reconciliation must exist, be tested, and be reviewed before live trading can be considered.
10. **Operator availability is a safety input.** Future runtime monitoring must detect stale Kevin availability and route stale state to the kill switch policy.
11. **Deployments are auditable and reversible.** Material operational changes require a deployment log with verification evidence and rollback instructions.
12. **Claims must match tooling and evidence.** README, ADRs, plan, pre-commit, `pyproject.toml`, tests, and external-review claims must be mutually consistent.

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

External review catches the class of failures that engineering standards and tests cannot: design errors, reasoning mistakes, sequencing failures across paraphrase, and conclusions that don't follow from evidence. Tests prove code does what it says; review evaluates whether what it says is right. The two layers operate together — neither is sufficient alone.

### 4.1 Scope: What Requires Review

Review is required for the following artifact classes:

- **Backtest results.** Every backtest produces a numerical claim that becomes a row in `signal_benchmarks`. Review evaluates whether the claim follows from the data, whether the methodology is sound, and whether the conclusion is appropriate given the evidence. Required before the row is added to `signal_benchmarks`.
- **Schema changes.** Every Alembic migration (up + down + tests) is reviewed before merge. Review evaluates whether the change is reversible, whether tests adequately cover the migration, and whether downstream code handles the new schema correctly.
- **Plan section drafts (Sections 1–5).** Sections 1, 2, 3, 4, 5 are load-bearing — they govern everything downstream. Drafts and major revisions to these sections are reviewed before commit. Sections 6–10 are populated progressively and don't require per-edit review.
- **Audit standard test designs.** When Section 5 (Audit Standard) defines specific tests that gate components, the test designs themselves are reviewed before being adopted as the standard.
- **Runtime enforcement code.** Startup checks, schema validators, safety gates — code whose failure would result in incorrect trading behavior. Reviewed before merge.
- **Major architectural decisions.** Dependency manager choice, broker migration, deployment strategy. Reviewed at decision point, before implementation begins.
- **Live trading changes.** Any change that affects live capital — removing `--dry-run`, raising the position cap, modifying loss breakers. Reviewed before commit AND independently signed off by Kevin at execution time. Two-key requirement.

Review is NOT required for:

- Routine refactoring with full test coverage and no behavior change
- Glue and utility code with engineering-standards coverage
- Exploratory scratch work in `~/gmc-rebuild/scratch/`
- Documentation cleanup that does not affect Sections 1–5

### 4.2 Timing: When Review Happens

Review is per-artifact-class, not per-merge or per-step. Specific gates per class:

| Artifact Class | Review Point |
|---|---|
| Backtest results | Before adding the row to `signal_benchmarks` |
| Schema changes | Before merge to main |
| Plan section drafts (1–5) | Before merge to main |
| Audit standard tests | Before adoption |
| Runtime enforcement code | Before merge to main |
| Architectural decisions | At decision point, before implementation |
| Live trading changes | Before commit; second sign-off at execution |

Review gates are independent of the seven-step sequence boundaries. An artifact in any step is gated by its class, not its step.

### 4.3 Reviewer Selection: Which Independent AI

Reviews are conducted by AI models from at least two different providers, with no shared conversation context with the work being reviewed.

Default reviewer pool:

- **OpenAI ChatGPT** (current GPT-5 or latest GPT-4 model)
- **Google Gemini** (latest Pro model)
- **Claude in a separate conversation with no shared context** (used as third opinion for high-stakes reviews)

For each review, at least two reviewers from different providers are required. For high-stakes reviews (live trading changes, migrations affecting production data, major architectural decisions), all three are required.

Different model families have different blind spots; a single reviewer can have systematic failure modes that match Claude's. Independent providers reduce the probability of a shared blind spot. The third Claude review is for triangulation on the highest-stakes decisions.

### 4.4 Mechanics: How a Review Happens

For v1, the mechanism is paste-and-record:

1. Claude writes the review request file at `~/gmc-rebuild/reviews/pending/{date}_{artifact_id}_request.md` using the format in 4.5.
2. Kevin opens the request file, copies its contents into the relevant AI provider's chat interface (e.g., chatgpt.com, gemini.google.com).
3. Kevin pastes the AI response into a review file at `~/gmc-rebuild/reviews/{date}_{artifact_id}_{reviewer}.md` using the format in 4.6.
4. The review file is committed to git with a message identifying the artifact and reviewer.
5. The artifact's merge or action is gated on the review file existing and indicating PASS or CONCERNS-resolved per Section 4.7.

API integration to automate steps 2–3 is a future enhancement, deferred to a later phase. The paste-and-record workflow is the v1 baseline because it ships immediately, requires no infrastructure build, and forces a structured artifact (the review file) regardless of whether automation is added later.

### 4.5 Review Request Format

Every review request follows this template:

```
# Review Request: {artifact_id}

## Project Context
[Stable paragraph describing GMC's rebuild and the role of external review.]

## Artifact Under Review
[Type of artifact: backtest result, schema migration, plan section, etc.]
[Path to the artifact in the repo]
[Inline copy of the artifact's content]

## Specific Questions
[Numbered questions the reviewer must answer. Varies by artifact class.]

## Required Response Format
[Reference to 4.6 — verdict, concerns with reasoning, optional re-derivations.]

## What Is Out of Scope
[Things the reviewer should NOT comment on.]
```

The request must NOT include Claude's conclusions on the artifact. The reviewer evaluates the artifact independently, not Claude's framing of it.

### 4.6 Review Response Format

Every review response is structured:

```
# Review Response: {artifact_id} by {reviewer}
Date: {YYYY-MM-DD}
Reviewer: {ChatGPT 5 / Gemini Pro / Claude separate session}

Verdict: PASS | CONCERNS | FAIL

Concerns (if any):
For each concern:
- Concern: [What the issue is]
- Reasoning: [Why it's a concern]
- Recommendation: [What to do about it]

Re-derivations (if applicable):
[For backtest reviews: explicit recomputation of any specific numerical claim.]

Overall Reasoning:
[One-paragraph summary of the reviewer's evaluation.]
```

If the reviewer's response doesn't fit this format, the request is re-issued with explicit format requirements until a structured response is produced. Free-form responses are not accepted as final reviews.

### 4.7 Disagreement Adjudication

The review system surfaces disagreements; it does not replace Kevin's judgment. Final adjudication authority is always Kevin's.

Workflow for non-PASS reviews:

1. **Review verdict is FAIL or CONCERNS.** Claude responds to each concern with one of:
   - **Fix:** Modify the artifact to address the concern, request a re-review.
   - **Counterargument:** Argue the concern is wrong, with reasoning. Kevin adjudicates.
   - **Defer:** Acknowledge the concern is valid but should be deferred to a later phase. Kevin adjudicates.
2. **Reviewer disagrees with Claude's response (re-review still raises the concern).** A third reviewer is solicited. Kevin reads all responses and decides.
3. **High-stakes artifact (live trading change, production schema):** Kevin reviews independently and signs off, even if all reviewers PASS. The two-key requirement from 4.1 binds here.

Disagreements are recorded in the artifact's review file under a "Disagreement Resolution" section so the rationale is preserved across sessions.

---

## 5. Audit Standard

The concrete specification of the bar every component — newly built or carried forward from the prior project — must clear before being designated part of the rebuilt system. The audit standard is what makes "the same bar new work is held to" (Section 1) a measurable test rather than a phrase.

The audit standard applies to anything claiming to be production: a signal scanner, a backtest result, a schema, a runtime enforcement check, an autotrader. Carried-forward components and new components are evaluated identically; the only difference is which of the standard's checkboxes need filling versus which already exist.

### 5.1 Required Artifacts

For any component to clear audit, the following artifacts must exist and be committed to the repository:

- **Backtest script.** Single entry point (e.g., `python -m {signal}.backtest`) that reproduces the signal's reported alpha. Lives under `~/gmc-rebuild/research/signals/{signal_name}/backtest.py`.
- **Raw output.** Trade-level CSV produced by the backtest script, containing every signal-driven trade with date, ticker, direction, entry, exit, return, and realized alpha. Committed to git alongside the backtest script.
- **Methodology document.** Markdown file at `~/gmc-rebuild/research/signals/{signal_name}/methodology.md` documenting: signal definition, universe construction, entry rule, exit rule, holding period, trade-construction logic, exclusion rules, and known caveats. Sufficient detail that an independent reader can re-implement the backtest from this document alone.
- **Reproducibility test.** Per Section 3.4. JSON expected-output file plus a pytest test that imports the backtest's main entry point, runs it on the documented fixed inputs, and asserts deep equality.
- **Test coverage.** Per Section 3.2. 100% line + branch on the signal logic; 80% on glue.
- **Schema entry.** Row in `signal_benchmarks` populated with the signal's reported alpha, t-stat, holding period, and a `provenance` field linking to the commit hash + relative path of the producing backtest script.

### 5.2 Traceability Requirements

Every numerical claim made about a component must be traceable in a single, mechanical step from the claim to the producing artifact:

- **Benchmark to backtest.** Every row in `signal_benchmarks` carries a `provenance` field of the form `{commit_hash}:{relative_path}`. Querying that pair must yield the backtest script that produced the number.
- **Backtest to raw output.** The backtest script's reproducibility test re-runs the script and verifies it produces the same JSON expected-output. The raw CSV is committed alongside; the JSON is the summary; both are verifiable.
- **Methodology to backtest.** The methodology document and the backtest script are co-located. A diff showing one changed without the other is a violation of the audit standard.
- **No untraceable numbers.** A number that cannot be produced by re-running a committed script does not appear in `signal_benchmarks`, in the methodology document, or in any other artifact designated rebuilt. Numbers in scratch don't count and don't propagate.

### 5.3 Runtime Requirements

Components designated rebuilt must satisfy a set of runtime checks, enforced at autotrader startup and on every commit affecting the runtime path:

- **Schema completeness.** All required columns in `signal_benchmarks` are non-null for the component. Missing fields fail startup.
- **Provenance check.** The `provenance` field resolves to a real commit hash and an existing path. Stale or invalid provenance fails startup.
- **Reproducibility check (pre-deploy).** Before any live trading change, the reproducibility test for every wired signal is re-run; failure blocks the deploy.
- **Loss breaker presence.** The autotrader cannot start without daily, weekly, and monthly loss breakers configured and active.
- **Dry-run flag default.** The autotrader defaults to dry-run unless explicitly invoked with the live flag and a current live-trading review file (per Section 4.1) exists.

### 5.4 Engineering Standard Requirements

Every component clears Section 3 in full:

- TDD discipline (3.1) — production code has tests written first.
- Coverage thresholds (3.2) met for every module.
- Pre-commit hooks (3.3) install and pass without bypass.
- Reproducibility test (3.4) exists for every numerical claim.
- Schema migrations (3.5) — if the component creates or changes schema, up/down/tests are present in the originating commit.

A component that fails any of these is not eligible for audit. Engineering standards are pre-audit, not part of audit; audit assumes engineering standards are already met.

### 5.5 Review Requirements

Every component clears the relevant Section 4 review gates:

- **Backtest review.** At least two external AI reviews from different providers, both PASS or CONCERNS-resolved.
- **Schema migration review.** If the component creates or changes schema, at least two external reviews on the migration.
- **Architectural decision reviews.** Any architectural choices the component embeds (e.g., choice of broker, choice of data source) have been reviewed at decision point.
- **Live trading review.** For components in the live trading path, a current live-trading review with Kevin's independent sign-off.

Review files for the component are linked from the methodology document so an auditor can find them in a single navigation step.

### 5.6 Pass/Fail Criteria

A component passes audit if and only if **all** of the following are true:

1. All required artifacts (5.1) exist and are committed.
2. All traceability requirements (5.2) hold.
3. All runtime requirements (5.3) pass at the time of audit and at autotrader startup.
4. All engineering standard requirements (5.4) hold.
5. All applicable review requirements (5.5) are satisfied.
6. The reproducibility test for the component passes at the audit commit.

Any single failure is a fail. There is no partial credit. A failing component is not designated rebuilt; work returns to the appropriate step per the no-patches-later principle (Section 1).

### 5.7 Carried-Forward Component Workflow

Components from the prior project (existing scanners, the equity autotrader, the crypto autotrader, macro runner, etc.) follow this workflow before being designated rebuilt:

1. **Inventory.** List every artifact the existing component has — backtest script, output, methodology, tests, etc. Note what's present and what's missing.
2. **Gap analysis.** Compare the inventory against 5.1–5.5. Each missing artifact is a gap.
3. **Gap closure.** Each gap is closed individually:
   - Missing methodology → write methodology document.
   - Missing reproducibility test → add JSON expected-output and test.
   - Missing tests → write tests to coverage threshold, with TDD discipline.
   - Stale benchmark row → re-run backtest, update row, verify reproducibility.
   - Missing reviews → request reviews per Section 4.
4. **Re-audit.** Once all gaps are closed, the component is re-audited per 5.6.
5. **Designation.** If audit passes, the component is designated rebuilt. The designation is committed to a registry at `~/gmc-rebuild/docs/rebuilt_components.md` with the date, audit commit hash, and reviewer files.

The carried-forward workflow is identical to the new-component workflow except in the inventory step. Whether a component "already worked" in the prior project is not a defense against the audit standard; the question is whether it meets standard now, not whether it produced trades before.

If a component fails audit and the gap closure would cost more than rebuilding from scratch, rebuilding from scratch is preferred. The audit standard does not reward sunk cost.

---

## 6. Current State Assessment

Honest read of where each of the seven steps actually stands today, component by component and signal by signal. Distinguishes verified facts from unverified claims. Every entry is marked **(verified)** when confirmed by direct inspection of the relevant artifact during this rebuild's setup phase, or **(claim, needs verification)** when sourced from prior session memory or third-party reporting that has not been audit-verified in this rebuild.

This section's contents will be tightened during Step 1 of the rebuild as data and artifact verification proceeds. Until then, treat (claim, needs verification) entries as starting hypotheses, not load-bearing facts.

### 6.1 Step 1 — Get Data

**Existing data sources, reported as operational:**

- FMP (Ultimate plan, `/stable/` endpoints) **(claim, needs verification)** — used for fundamental and price data; `/historical-price-full/` returns 403, yfinance used for OHLCV instead.
- yfinance **(claim, needs verification)** — historical OHLCV, prices, earnings calendar.
- FRED **(claim, needs verification)** — macro indicators.
- CFTC **(claim, needs verification)** — COT data, weekly Tue/Fri update.
- SEC EDGAR **(claim, needs verification)** — Form 4, 13F, 8-K filings.
- FINRA free API **(claim, needs verification)** — short-interest data.
- Alternative.me **(claim, needs verification)** — Crypto Fear & Greed Index.
- Coinbase **(claim, needs verification)** — crypto autotrader execution.

**Databases on disk, reported existing:**

- `~/gmc_data/signal_intelligence.db` (table `signal_log`) **(claim, needs verification)**
- `~/gmc_data/positions.db` (includes `signal_benchmarks` table with 12 rows) **(verified May 8 audit)**
- `~/gmc_data/form4_scanner/form4_insider_trades.db` **(claim, needs verification)**
- `~/Desktop/Claude_Programs/Trading_Programs/pead_backtest/pead_results.db` **(claim, needs verification)**
- macro_runner DBs at `~/gmc_data/macro_data/` (eia_data, flows, geopolitical_indices, cot_data, vix_skew_data) **(claim, needs verification)**
- `fred_economic.db` does NOT exist **(verified April 27)**

**Status against audit standard:** No data source is currently audit-cleared. None has the documented validation (Section 5.1 methodology document, 5.2 traceability, 5.3 runtime check) the rebuild requires. All data sources currently in use must be brought under audit standard before being designated rebuilt.

### 6.2 Step 2 — Verify the Data Is Clean and Correct

**Reported state:**

- macro_runner has 5/5 collectors passing **(claim, needs verification)**.
- 3/5 macro DBs update daily; cot_data updates Tue/Fri (CFTC schedule), vix_skew_data has a possible silent skip **(claim, needs verification)**.
- Sync scripts (`sync_signal_intelligence.py`, `sync_form4_db.py`) exist but their iCloud-vs-non-iCloud location and current operational state is uncertain **(claim, needs verification)**.

**Status against audit standard:** No formal data validation suite exists per Section 5.1's methodology document and Section 5.3's runtime check. Existing collectors run, but "runs without error" is not equivalent to "data is clean and correct" under the audit standard. Step 2 of the rebuild produces this missing layer.

### 6.3 Step 3 — Backtest the Data

Per-signal status, reflecting the May 8 audit findings on `signal_benchmarks`:

| Signal | Reported Result | Backtest Exists | Repro Test | Audit Status |
|---|---|---|---|---|
| PEAD_BULL | +4.24% / 28d / t=17.08 | yes (claim) | no | claim, needs verification |
| PEAD_BEAR | +1.74% / 28d | yes (claim) | no | claim, needs verification |
| SI_SQUEEZE | +10.29% | yes (claim) | no | claim, needs verification |
| 8K_1.01 SHORT | +3.17% / t=-9.98 | yes (claim) | no | claim, needs verification |
| THIRTEENF_BULL (13F) | +5.26% / 3+ initiators | yes (claim) | no | claim, needs verification |
| COT_WHEAT_BEAR / S4 / S5 | clean monotonic gradient | yes (claim) | no | claim, needs verification |
| COT_BULL / COT_BEAR | mixed | yes (claim) | no | claim, needs verification |
| CEL_BEAR | +0.21% / 5d (benchmark); -0.55%/-0.71% (scanner docstring) | yes **(verified)** | no | **SUSPENDED pending re-run (May 8 audit)** |
| DIV_CUT | -2.15% broad universe; benchmark row stale at 15.77% | yes (claim) | no | **SUSPENDED (verified May 8); benchmark row stale** |
| DIV_INIT | +2.89% / 60d (first-ever only) | yes (claim) | no | claim, needs verification; not wired |
| F4_BUY_CLUSTER | (per `insider_cluster_backtest.py`) | yes (claim) | no | claim, needs verification |
| F4_SELL_S1 / F4_SELL_S2 | per `f4_sell_backtest_findings_2026-05-08.md` | yes **(verified May 8)** | no | claim, needs verification |
| Congress trader | NO ALPHA | yes (claim) | no | DO NOT DEPLOY (verdict) |
| Options unusual volume | DEAD in 2025 (t=-0.44) | yes (claim) | no | PARKED (verdict) |

**Status against audit standard:** No signal currently clears audit. The dominant gaps are: missing reproducibility tests (universal), stale or missing `signal_benchmarks` rows, missing or untraceable methodology documents, and missing test coverage at the rebuild's thresholds. The May 8 audit confirmed backtests do exist for the signals above; the failure mode is traceability and reproducibility, not absence of work.

### 6.4 Step 4 — Stress Test the Findings

**Reported state:**

- DIV_CUT was suspended after a broad-universe stress test produced -2.15% alpha versus the curated-universe positive result **(verified May 8 — `DIV_CUT_SUSPENDED=True`, commit 0131f7b)**.
- COT showed mixed regime-conditional behavior across commodities (wheat clean BEAR; corn/gold overextension mean reversion) **(claim, needs verification)**.
- CEL_BEAR scanner docstring claims regime-conditional alpha that doesn't match the benchmark row **(verified May 8 audit)**.
- No formal regime-conditioning framework exists per Section 5.1's methodology document standard **(verified by absence)**.

**Status against audit standard:** Stress testing has been performed ad-hoc on individual signals but no systematic stress framework exists. Step 4 of the rebuild produces this layer with documented methodology, regime taxonomy, and per-signal stress tests with reproducibility.

### 6.5 Step 5 — Build Execution

**Reported state:**

- `ib_autotrader.py` exists; runs via cron at 8:00 AM CT Mon–Fri **(verified by Master_status.md cron success record)**.
- 5 signals wired to autotrader: PEAD, SI Squeeze, COT, CEL, 13F **(claim, needs verification — wiring details)**.
- Autotrader is in dry-run; `run_ib_autotrader.sh` carries `--dry-run` flag at line ~32 **(verified)**.
- IB account `U5140084`; live NLV ~$6,069 **(verified May 8 audit pull)**.
- DIV_CUT suspended in autotrader **(verified)**.
- DIV_INIT scanner runs at 23:45 UTC; not wired to IB autotrader **(claim, needs verification)**.
- Mac Studio is the sole 24/7 trading machine; sleep=0; MBP off-network **(verified by ongoing operation)**.
- IB Client Portal Gateway runs on Mac Studio port 7462; daily 6 AM launchd restart; manual 2FA **(claim, needs verification)**.
- The CPG choice is acknowledged as wrong-tier infrastructure; intended replacement is IB Gateway + ib_insync, targeted Horizon 2 **(verified by April 28 postmortem in gmc-docs)**.

**Status against audit standard:** The autotrader's signal-handling code and runtime safety checks have not been audited under Section 5. Coverage thresholds (Section 3.2) are not currently enforced. The CPG architectural choice itself is a gap that the rebuild's broker migration addresses.

### 6.6 Step 6 — Stress Test the Execution and Safety Monitors

**Reported state:**

- Item 7 of go-live checklist (5/5 consecutive clean off-network MBP auths under daily-restart protocol) **closed today (verified May 8)**.
- Item 8 (iPhone auth) pending **(claim, needs verification)**.
- Daily, weekly, monthly loss breakers exist in some form **(claim, needs verification — exact configuration)**.
- April 28 postmortem documented the CPG architectural mistake with 5 NASA-format root causes **(verified by gmc-docs/postmortems/)**.

**Status against audit standard:** Execution stress testing is ad-hoc; no formal failure-mode catalog or stress-test suite per Section 5.1 exists. Safety monitors are not currently subject to runtime requirements per Section 5.3. Step 6 of the rebuild closes these gaps.

### 6.7 Step 7 — Execute

**Reported state:**

- Equity autotrader: in dry-run, has been since launch (Easter Monday April 6, 2026) **(verified)**.
- Crypto autotrader (Coinbase): live since March 9, 2026; 1-year backtest results +8.63%, Sharpe 1.262, Sortino 1.890 **(claim, needs verification — backtest methodology and reproducibility against rebuild standard)**.
- Crypto autotrader is independent of equity autotrader; runs continuously **(verified by ongoing operation)**.

**Status against audit standard:** The crypto autotrader has been live for two months but has not been audited under Section 5. Per Section 1, it is preserved running but is itself subject to re-audit before being designated part of the rebuilt system. The equity autotrader cannot move from dry-run to live until the entire seven-step rebuild is complete and the live-trading change clears Section 4.1's two-key requirement.

### 6.8 Documentation and Process

- `gmc-docs` repo exists (KPH3802/gmc-docs); contains April 28 postmortem, Constitution v1 in progress, Standards Doc skeleton **(claim, needs verification — current contents)**.
- Master_status.md is the canonical session log; entries verified on disk before session end **(verified by today's entry workflow)**.
- 4 confirmed iCloud failure modes documented **(verified by gmc-docs and current operational practice)**.

**Status against audit standard:** Existing documentation is descriptive, not prescriptive at the rebuild's required level. The rebuild plan (this document), once Sections 1–10 are filled, becomes the canonical prescriptive artifact.

---

## 7. Step-by-Step Plan

For each of the seven steps in Section 2, this section defines acceptance criteria, work items, dependencies, and links back to Sections 3, 4, and 5. Estimated scope is in rough order-of-magnitude only and is not a deadline; the operating philosophy is "right answer at any pace" (carried forward from the prior project's core invariants).

### 7.1 Step 1 — Get Data

**Acceptance criteria.** A canonical data store exists. Every data source the rebuild uses is documented (source, schema, update cadence, refresh mechanism), wrapped in code that is test-covered to Section 3.2 thresholds, and produces a deterministic output that downstream code can rely on.

**Sub-tasks:**

1. Inventory every data source the existing project uses and every data source the rebuild requires.
2. For each, write a methodology document (Section 5.1) describing what the source is, how the data is fetched, what schema it returns, and what the update cadence is.
3. For each, write a fetcher module test-first per Section 3.1. Fetcher returns typed structured data; failure modes (network, schema change, rate limit) raise typed exceptions, not silent zeros.
4. For each, write reproducibility tests per Section 3.4 against a fixed-input snapshot.
5. Define and create the canonical data store schema (Alembic migration, Section 3.5).
6. Wire fetchers to the data store with provenance (Section 5.2): every row carries source identifier, fetch timestamp, and fetcher commit hash.

**Dependencies.** None on prior steps; depends on engineering standards (Section 3) being installed in the repo as pre-commit hooks before any code is written.

**Engineering requirements.** Section 3 in full. Data fetchers and store code are signal-adjacent; coverage threshold is 100% line + branch.

**Review requirements.** Schema migrations reviewed per Section 4.1. Major data-source choices (e.g., choice of options data provider, if any) reviewed at decision point.

**Audit requirements.** Each data source clears Section 5 individually before being declared rebuilt. The data store as a whole clears Section 5 before Step 2 begins.

**Estimated scope.** Largest of the seven steps in code volume. Not gated on any external decision once dependency manager is chosen.

### 7.2 Step 2 — Verify the Data Is Clean and Correct

**Acceptance criteria.** A validation suite exists that runs against the canonical data store on every commit and on a daily schedule. Validation produces structured failure reports (not silent skips) and blocks downstream backtest execution if any validation fails.

**Sub-tasks:**

1. Define per-source validation rules: schema invariants, value ranges, freshness thresholds, cross-source consistency checks.
2. Implement validators test-first per Section 3.1.
3. Wire validators into a validation runner that executes on commit (pre-commit hook) and on schedule (daily cron).
4. Define structured failure reports: which validator, which row(s), what was expected, what was found, suggested action.
5. Wire failure reports to a notification path Kevin actually sees (email, Slack, dashboard — TBD per Section 9 / open question).
6. Add a runtime check (Section 5.3): autotrader startup verifies the most recent validation run passed, blocks startup if not.

**Dependencies.** Step 1 complete. Cannot validate data that doesn't have a defined source and store.

**Engineering requirements.** Section 3 in full. Validators are runtime enforcement; coverage threshold is 100% line + branch.

**Review requirements.** Validator design reviewed per Section 4.1 (audit standard test designs).

**Audit requirements.** The validation suite as a whole clears Section 5 before Step 3 begins.

**Estimated scope.** Smaller than Step 1 in code volume; comparable in design effort because validation rules are signal-specific.

### 7.3 Step 3 — Backtest the Data

**Acceptance criteria.** Each signal the rebuild adopts has a backtest that meets Section 5.1's required-artifacts list, traces per Section 5.2, and clears Section 5.6. `signal_benchmarks` is fully repopulated from these backtests; no stale rows remain.

**Sub-tasks (per signal):**

1. Inventory the existing signal's artifacts (script, output, methodology if any).
2. Gap-analyze against Section 5.1.
3. Write the methodology document.
4. Write the backtest test-first: fixed inputs, deterministic output, JSON expected-output committed, reproducibility test.
5. Verify the backtest against the existing trade-level data where possible.
6. Run the backtest, generate raw output CSV, generate `signal_benchmarks` row.
7. Request external review per Section 4.1 (backtest results).
8. Address reviewer concerns per Section 4.7.
9. Commit the row to `signal_benchmarks` with provenance.

**Per-signal independence.** Each signal is a separate audit unit. Step 3 is parallelizable across signals; one signal's failure does not block others.

**Signals in initial scope:** PEAD_BULL, PEAD_BEAR, SI_SQUEEZE, 8K_1.01_SHORT, THIRTEENF_BULL, COT_WHEAT_BEAR, F4_BUY_CLUSTER, F4_SELL_S1/S2, DIV_INIT.

**Signals out of initial scope:** CEL_BEAR (suspended pending re-run; methodology mismatch must be resolved before re-entry), DIV_CUT (suspended; -2.15% broad-universe finding stands), Congress (no alpha), Options unusual volume (dead).

**Dependencies.** Steps 1 and 2 complete.

**Engineering requirements.** Section 3 in full. Signal logic is the highest-stakes code; 100% line + branch coverage strict.

**Review requirements.** Two external reviews per signal per Section 4.3.

**Audit requirements.** Each signal clears Section 5 individually. `signal_benchmarks` is fully repopulated from cleared signals only.

**Estimated scope.** Largest in audit/review effort; per-signal volume modest. Sequential bottleneck is review turnaround, not coding.

### 7.4 Step 4 — Stress Test the Findings

**Acceptance criteria.** Each cleared signal from Step 3 has an associated stress test suite covering: regime conditioning (where applicable), broader-universe robustness, transaction cost sensitivity, and parameter sensitivity. Suite outputs are committed; the signal's audit status reflects stress test results.

**Sub-tasks (per signal):**

1. Define applicable stress dimensions for the signal.
2. Implement stress tests test-first.
3. Run stress tests, commit outputs.
4. If stress tests reveal a signal does not survive, the signal is suspended (DIV_CUT pattern) or restricted (universe narrowed, parameters re-tuned). Either action requires methodology document update and re-audit.
5. Update `signal_benchmarks` row with stress-test-conditioned alpha if different from headline.

**Dependencies.** Step 3 complete for the signal in question.

**Engineering requirements.** Section 3 in full.

**Review requirements.** Stress test design reviewed per Section 4.1; if a stress test changes a signal's status, the change is reviewed per Section 4.1 (architectural decision class).

**Audit requirements.** Section 5 clears at the post-stress state.

**Estimated scope.** Comparable to Step 3 per signal; can parallel-track with later Step 3 signals.

### 7.5 Step 5 — Build Execution

**Acceptance criteria.** An execution layer exists that consumes signals from `signal_log`, places orders against the broker, enforces position cap and loss breakers, and produces a complete audit trail of every action. The execution layer is not the existing autotrader carried forward; the existing autotrader is a candidate for Section 5.7 carried-forward audit, but the rebuild's execution layer is built test-first against the rebuild's standards regardless.

**Sub-tasks:**

1. Resolve broker choice: IB Client Portal Gateway is acknowledged wrong tier; IB Gateway + ib_insync is the intended replacement. Decision is reviewed per Section 4.1 (architectural decision).
2. Implement the broker abstraction test-first.
3. Implement the order-placement layer with idempotency, retry, and structured failure reports.
4. Implement runtime safety: position cap, daily/weekly/monthly loss breakers, dry-run flag default.
5. Implement startup checks per Section 5.3.
6. Implement the audit trail: every action logged with signal source, timestamp, broker response, and outcome.
7. Wire the rebuilt execution layer to a paper account before any live capital touches it.

**Dependencies.** Steps 1 and 2 complete (data store exists). Step 3 partial — at least one cleared signal exists for the execution layer to consume during testing.

**Engineering requirements.** Section 3 in full. Execution is the highest-stakes runtime code; coverage is 100% line + branch.

**Review requirements.** Broker choice reviewed at decision point. Runtime enforcement code reviewed before merge per Section 4.1. Two external reviews on the integrated execution layer before Step 6 begins.

**Audit requirements.** The execution layer as a whole clears Section 5 before Step 6 begins.

**Estimated scope.** Comparable to Step 1 in code volume. Major external dependency: ib_insync API behavior under failure modes.

### 7.6 Step 6 — Stress Test the Execution and Safety Monitors

**Acceptance criteria.** The execution layer has been exercised against simulated failure modes — broker disconnects, partial fills, schema-mismatch responses, network partitions, gateway auth expiration, signal source absence, loss-breaker tripping under various scenarios. Each failure mode has a documented expected behavior; the test suite verifies actual behavior matches expected.

**Sub-tasks:**

1. Build a failure-mode catalog: every realistic failure of the execution layer's external dependencies.
2. For each, define expected behavior (e.g., broker disconnect → retry N times, fail loudly, halt new orders, preserve existing).
3. Implement stress tests test-first; mock the failure modes.
4. Run the suite; verify all expected behaviors hold.
5. Run the execution layer against a paper account for a sufficient period to catch failures the catalog missed.
6. Document any catalog additions discovered during paper trading.

**Dependencies.** Step 5 complete.

**Engineering requirements.** Section 3 in full.

**Review requirements.** Failure-mode catalog reviewed per Section 4.1. The full stress test suite reviewed before being adopted as the gate to Step 7.

**Audit requirements.** The execution layer clears Section 5 in its post-stress state. This is the last audit before live capital.

**Estimated scope.** Modest in code; significant in design and paper-trading observation period.

### 7.7 Step 7 — Execute

**Acceptance criteria.** Live trading commences only after Steps 1–6 have all cleared audit individually and as an integrated system. The transition from dry-run to live is gated by Section 4.1's live-trading review (two-key requirement) and a documented capital-deployment plan.

**Sub-tasks:**

1. Confirm all prior steps are audit-cleared at the live-deploy commit.
2. Submit a live-trading change for Section 4.1 review (three reviewers required for high-stakes change).
3. Independent Kevin sign-off per Section 4.7.3.
4. Remove `--dry-run` flag, deploy with conservative initial position cap.
5. Monitor for a documented observation period before incrementing the cap.
6. Per the prior project's $50K NLV deployment target, expand cap on observed-stable behavior, not on calendar.

**Dependencies.** Steps 1–6 complete.

**Engineering requirements.** Section 3 enforced as ongoing baseline.

**Review requirements.** Live-trading review per Section 4.1; cap increments treated as live-trading changes (each requires its own review).

**Audit requirements.** Section 5 enforced as ongoing runtime check; any audit violation halts live trading.

**Estimated scope.** Smallest in code; largest in care.

---

## 8. Order of Work

Sequencing within and across the seven steps.

**Critical path:** Step 1 → Step 2 → Step 3 (per signal) → Step 4 (per signal) → Step 5 → Step 6 → Step 7. No live capital changes (Step 7 actions) before Steps 1–6 complete.

**Parallel tracks possible:**

- Step 3 across signals (each signal is independent). Once Step 1 and Step 2 are complete, multiple signals can proceed through Step 3 in parallel.
- Step 4 across signals, similarly.
- Step 5's broker abstraction can be designed and prototyped against a paper account in parallel with later-stage Step 3 work, provided that the rebuilt execution layer's integration testing waits for at least one Step 3 cleared signal.
- The Section 5.7 carried-forward workflow runs in parallel with new work for components Kevin elects to evaluate.

**Stop-points (mandatory pauses for review or decision):**

- Before any Step 1 code is written: dependency manager choice (Section 10), broker migration commitment.
- Before Step 3 begins: external review of Sections 1–5 of this plan (the load-bearing sections).
- Before Step 5 begins: broker choice reviewed and committed.
- Before Step 7: full-system audit (Sections 1–6 cleared as integrated system, not individually).

**Crypto autotrader (separate track):**

The crypto autotrader continues running in its existing form during the rebuild (per Section 1). It is subject to Section 5.7 re-audit before being designated part of the rebuilt system. Its re-audit is parallelizable with new equity work but does not gate equity progress. Failure of crypto re-audit does not halt equity rebuild; success does not accelerate equity rebuild.

---

## 9. Out of Scope

Explicit list of items this rebuild is NOT doing. Items move out of scope by deliberate decision; entries are added with rationale.

- **Building new signals.** The rebuild's focus is bringing existing signals to standard, not generating new alpha hypotheses. New signal research is a post-rebuild activity. Rationale: scope discipline; prior project produced more signals than were ever cleared, and additional signals don't help if existing ones aren't audit-clean.
- **Re-running options unusual volume work.** Verdict (DEAD in 2025, t=-0.44) stands; no further investigation in this rebuild. Rationale: signal verdict already established by prior backtest; rebuild does not re-litigate.
- **Re-running Congress tracker as a trading signal.** Verdict (no alpha) stands; the tracker may continue as monitor-only but is not eligible for autotrader wiring in the rebuild. Rationale: same as above.
- **Multi-broker support.** The rebuild commits to IB (with the Client Portal → IB Gateway + ib_insync migration). Other brokers are not in scope. Rationale: scope discipline; multi-broker abstraction is a tax on every change.
- **Web dashboard rebuild.** The existing Flask dashboard is preserved as-is in the prior project; the rebuild does not re-implement it. Section 5.7 re-audit applies if the dashboard is later designated part of the rebuilt system. Rationale: the dashboard is a viewer, not a trader; lower audit priority.
- **API automation of external review (Section 4.4).** Paste-and-record is the v1 mechanism. API integration is a future enhancement. Rationale: ships immediately; forces the structured-artifact discipline that automation would only formalize.
- **CI/CD pipeline.** Pre-commit hooks are the enforcement layer for the rebuild; CI is added when there's a clear need (e.g., multi-machine work or external contributors). Rationale: scope discipline; pre-commit hooks cover the immediate need.
- **Performance attribution (Phases 2–3 from prior project).** Deferred until after rebuild is live and producing trades against the rebuilt standard. Rationale: nothing to attribute against until trades are happening.
- **Replacement of the macro runner under rebuild standard at launch.** The macro runner is preserved as-is during equity rebuild; Section 5.7 re-audit applies if it is later designated part of the rebuilt system. Rationale: the macro runner's outputs are inputs to research, not direct trading triggers; lower audit priority.

---

## 10. Open Questions

Items not yet resolved. Each has an owner and a target resolution point in the sequence.

- **Dependency manager choice (Section 3.6).** Options: Poetry, pip + requirements.txt, uv. Owner: Kevin. Resolution: before Step 1 implementation begins.
- **Broker migration timing (Section 7.5).** IB Gateway + ib_insync is the committed direction. Open question is whether the migration happens before Step 5 implementation begins (clean cut) or whether Step 5 prototypes against the existing Client Portal Gateway and migrates partway through. Owner: Kevin, with Claude recommendation. Resolution: before Step 5 begins.
- **GitHub hosting for `gmc-rebuild` repo.** The repo is currently local. Decision is whether to push to KPH3802 GitHub (alongside other GMC repos) and at what point. Owner: Kevin. Resolution: before any external review request is issued (since reviewers may need repo access).
- **Crypto autotrader re-audit prioritization.** Crypto runs live during rebuild. Question is whether its Section 5.7 re-audit happens early (parallel with Step 1) or late (after equity rebuild is live). Owner: Kevin, with Claude recommendation. Resolution: before Step 1 begins, since prioritization affects parallel-track planning.
- **Notification path for validation failures (Section 7.2.5).** Email vs. Slack vs. dashboard vs. multiple. Owner: Kevin. Resolution: before Step 2 implementation begins.
- **Failure-mode catalog source for Step 6.** Whether to base the catalog on prior project's known failure modes (April 28 postmortem, iCloud failures, gateway issues) plus net-new analysis, or to start from a clean catalog and re-derive. Owner: Claude proposes; Kevin adjudicates. Resolution: before Step 6 begins.
- **Capital deployment schedule for Step 7.** Initial position cap, increment trigger criteria, and target NLV path. Owner: Kevin. Resolution: before Step 7 begins; treated as architectural decision per Section 4.1.

---

*v0.6 — All ten sections drafted with substantive content. Sections 1–5 are load-bearing and gated by external review per Section 4.1 before being treated as final. Section 6 entries marked (claim, needs verification) are starting hypotheses to be tightened during Step 1. Section 7 estimated scope is order-of-magnitude only; per the prior project's invariant, time is not the constraint, right answer at any pace. Open questions in Section 10 must be resolved at their indicated resolution points before the gated work begins.*
