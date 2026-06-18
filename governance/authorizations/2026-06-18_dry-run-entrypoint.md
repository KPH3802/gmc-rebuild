# Authorization — Runnable Dry-Run Loop Entrypoint (PR P6-DRYRUN-ENTRYPOINT)

Date: 2026-06-18
Authorizer: Kevin
Scope: Bounded `src/gmc_rebuild/dry_run/` subpackage plus the matching `tests/dry_run/` test directory and the §8 step 4a allowlist entry. Adds a runnable composition entrypoint (`python -m gmc_rebuild.dry_run`) that threads the merged P6-01..P6-07 surfaces end-to-end and prints a deterministic daily report. **Composes only already-merged public symbols; modifies no existing engine module.** Pure / deterministic / value-typed at the library boundary; the only side effect is a single `print` in the `__main__` module. No broker, no network, no real account, no market data, no persistence, no scheduler, no env-var read, no secrets, no clock read inside the library. **Lightweight-lane single PR** per Kevin's 2026-06-18 directive; no separate planning or Mode B PRs.

## Authorization

Kevin's written directive for this packet, reproduced verbatim. Per `AI_WORKFLOW.md` §7 the verbatim block in this file is the authorization of record.

### Original task directive

> TASK P6-07: Build the runnable dry-run loop — the first command I can execute
> and watch my trading system work end to end.
>
> CONTEXT
> The repo has eight tested engine components but NO single runnable entry point
> that takes a signal in one end and prints a daily report out the other. Every
> part already exists and is tested (748 passing tests). This task does NOT add a
> new component — it composes the existing, already-authorized surfaces into one
> watchable pipeline. This is low-risk LOCAL-ONLY simulation work: no money, no
> broker, no network, no secrets, no persistence, no clock-in-library. Treat it in
> the LIGHTWEIGHT lane.
>
> DEFINITION OF DONE (all three required)
> 1. I can run `python -m gmc_rebuild.dry_run` and SEE a human-readable daily
>    report printed to stdout (decisions total, would_trade/would_skip counts,
>    net positions, reconciliation status).
> 2. A new test runs the FULL loop end to end and asserts a DailyReport is
>    produced with the expected counts. Test-first: write the failing test, then
>    make it pass.
> 3. `python -m pytest -q` stays green (currently 748 passing).
>
> THE EXACT CHAIN TO COMPOSE (use these real public symbols — confirmed present)
> Use tests/reporting/test_reporting.py as the reference for how these compose.
>
>   from gmc_rebuild.signal_intake import SignalIntent, SignalSide, accept_signal_intent
>   from gmc_rebuild.eligibility import EligibilityConfig, check_eligibility
>   from gmc_rebuild.runtime import RuntimeShell / SafetyVerdict  (build a CLEAR verdict)
>   from gmc_rebuild.decision import compose_position_decision
>   from gmc_rebuild.simulation import (SimulationBoundary, SimulationLane,
>       SimulatedOrderIntent, SimulatedOrderSide, SimulatedOrderType,
>       SimulatedOrderTimeInForce, derive_simulated_order_intent_id)
>   from gmc_rebuild.portfolio_state import SimulatedPortfolio, apply_simulated_order_intent
>   from gmc_rebuild.reporting import build_daily_report, render_daily_report_event
>
> Pipeline for each of ~2-3 hardcoded sample signals (a small fixture list):
>   intent = accept_signal_intent(SignalIntent(...))
>   elig   = check_eligibility(intent, EligibilityConfig(...))
>   verdict = <a CLEAR SafetyVerdict — build the same way the runtime/reporting tests do>
>   decision = compose_position_decision(intent, elig, verdict)
>   order_intent = <build SimulatedOrderIntent for the decision; gate it through
>                   SimulationBoundary(lane=LOCAL_ONLY).propose_order(order_intent, verdict)>
>   portfolio = apply_simulated_order_intent(portfolio, decision=decision,
>                                            order_intent=order_intent)
>   # accumulate decisions; start from SimulatedPortfolio.empty()
> report = build_daily_report(report_date=..., decisions=tuple(decisions),
>                             portfolio=portfolio,
>                             reconciliation_status=ReconciliationStatus.CLEAN)
>
> NEW FILES (only these)
>   src/gmc_rebuild/dry_run/__init__.py        # run_dry_run() -> DailyReport, + a
>                                              #   format_report(report) -> str
>   src/gmc_rebuild/dry_run/__main__.py        # parse nothing fancy; call
>                                              #   run_dry_run(), print(format_report(...))
>   tests/dry_run/test_dry_run.py              # test-first: full-loop test asserting
>                                              #   a DailyReport with expected counts
>
> HARD CONSTRAINTS
> - Compose ONLY existing public symbols. Do NOT modify any existing engine module.
>   If a needed symbol seems missing, STOP and tell me — do not invent or guess.
> - Pure/deterministic: pass any timestamp explicitly (the report layer requires a
>   caller-supplied timestamp; no implicit clock). Use a fixed timestamp in the loop.
> - No network, no file writes, no env vars, no secrets, no broker, LOCAL_ONLY lane.
> - Follow the existing test conventions in tests/reporting/test_reporting.py
>   (the in-repo _expect_error helper pattern; no pytest.raises if that's the convention).
> - Keep it small. This is one sitting. Do not refactor anything else.
>
> When done, show me the exact command output of `python -m gmc_rebuild.dry_run` so
> I can see my system run.

### Re-aim and lightweight-lane confirmation

> Go with option (a): lightweight lane, single PR, this directive is the
> authorization. Add a verbatim authorization stub of my directive into the
> impl PR for the audit trail. Do NOT create separate planning/Mode B PRs.
>
> Relabel from "P6-07" (taken — merged operator view) to a non-colliding tag,
> e.g. P6-DRYRUN-ENTRYPOINT or the next free P6 number — you choose.
>
> Leave my open P6-09 planning PRs (#186/#187) OPEN and set aside; do not close
> them. This dry-run entry point is a separate, independent PR.
>
> If you need a Bash allow rule for read-only surveys this session, add it, then
> proceed. Everything else in my prior TASK prompt still stands: compose only
> existing public symbols, modify no existing engine module, test-first, end in
> a runnable `python -m gmc_rebuild.dry_run` whose output you show me. If you
> cannot build a CLEAR SafetyVerdict without modifying an engine module, STOP
> and ask me — do not guess.

## In-Tree Tag

This packet is recorded under the in-tree tag **`PR P6-DRYRUN-ENTRYPOINT`** rather than a numeric `P6-NN` label, because the original `P6-07` label is taken by the merged operator view (`governance/authorizations/2026-06-15_p6-07.md`, PR #181). The tag is used in the `MASTER_STATUS.md` §8 step 4a `pr_tag` arm and in the commit message; it does not pre-claim or block any future numeric P6-0N enumeration.

## Authorized Scope

The implementation PR adds **only** the following files; modifies no other:

| File | Change |
|---|---|
| `src/gmc_rebuild/dry_run/__init__.py` | new — package docstring + re-export of `run_dry_run`, `format_report` |
| `src/gmc_rebuild/dry_run/_loop.py` | new — composition implementation (private module) |
| `src/gmc_rebuild/dry_run/__main__.py` | new — `python -m gmc_rebuild.dry_run` entrypoint |
| `tests/dry_run/__init__.py` | new — empty test-package marker |
| `tests/dry_run/test_dry_run.py` | new — end-to-end pipeline tests (test-first) |
| `governance/authorizations/2026-06-18_dry-run-entrypoint.md` | new (this artifact) |
| `MASTER_STATUS.md` | modified — §8 step 4a only: one new `allowed_p2_infra` entry `src/gmc_rebuild/dry_run`, matching `for path` iteration, `pr_tag="PR P6-DRYRUN-ENTRYPOINT"` arm, OK-echo extension, and comment block |
| `tests/test_package_skeleton.py` | modified — one new authorized-package entry `dry_run` plus its docstring entry |

No file under `src/gmc_rebuild/{config,time,logging,risk,heartbeat,kill_switch,reconciliation,runtime,simulation,signal_intake,eligibility,decision,portfolio_state,reporting,operator_view}/` is modified. No existing test file under `tests/**` other than `tests/test_package_skeleton.py` is modified.

## Authorized Contract

### 1. Composed-only

The new module imports only public symbols from already-authorized merged modules:

- `gmc_rebuild.signal_intake.{SignalIntent, SignalSide, accept_signal_intent}`
- `gmc_rebuild.eligibility.{EligibilityConfig, check_eligibility}`
- `gmc_rebuild.decision.{PositionDecision, PositionDecisionOutcome, compose_position_decision}`
- `gmc_rebuild.simulation.{SimulatedOrderIntent, SimulatedOrderSide, SimulatedOrderTimeInForce, SimulatedOrderType, SimulationBoundary, SimulationLane, derive_simulated_order_intent_id}`
- `gmc_rebuild.portfolio_state.{SimulatedPortfolio, apply_simulated_order_intent}`
- `gmc_rebuild.reporting.{DailyReport, build_daily_report}`
- `gmc_rebuild.risk.{HeartbeatStatus, KillSwitchState, ReconciliationStatus}`
- `gmc_rebuild.runtime.{SafetyVerdict}` (constructed with `clear=True` directly, mirroring the merged `tests/reporting/test_reporting.py` `_clear_verdict` helper)

No engine module is modified. No new public symbol is added to any merged subpackage.

### 2. Determinism

- The library boundary (`run_dry_run`, `format_report`) is pure and deterministic. Two calls to `run_dry_run()` return byte-for-byte identical `DailyReport` instances.
- Every timestamp is a fixed inline literal — `"2026-06-18T00:00:00Z"` for the `SafetyVerdict.observed_at` / `SimulatedOrderIntent.created_at` fields and `datetime(2026, 6, 18, 12, 0, 0, tzinfo=UTC)` for the module-level `FIXED_TIMESTAMP` callers can pair with a future audit-event render.
- The module performs no `now_utc()` / `time.*` / `datetime.now()` call. It does not import `gmc_rebuild.time`.

### 3. Inertness

- No I/O at the library boundary. The single `print` in `__main__` is the only side effect anywhere in the package.
- No `audit_event` emission inside the library. `gmc_rebuild.logging` is not imported by either `_loop.py` or `__init__.py`. (The merged P6-06 `lifecycle.daily_report` event remains the canonical audit-record path; this packet does not render it.)
- No network, no socket, no `urllib`, no `requests`, no `http`, no `ssl`, no `smtplib`, no `ftplib`.
- No filesystem write, no `open(` for write, no `pickle`, no `shelve`, no SQLite/DuckDB/database, no on-disk artifact.
- No env-var read, no secrets, no broker SDK, no real-account API, no market-data feed.
- No scheduler, no daemon, no background thread, no `time.sleep`, no `asyncio.sleep`, no `logging.basicConfig`, no handler installation.

### 4. Closed lane

The `SimulationBoundary` is constructed with `lane=SimulationLane.LOCAL_ONLY` only. No paper-broker lane, no live lane, no backtest lane.

### 5. Sample fixture

Three hardcoded sample signals: two map to allowed symbols / sides and clear the pipeline to `WOULD_TRADE`; one uses a symbol outside `allowed_symbols` and short-circuits to `WOULD_SKIP` with the `ELIGIBILITY_INELIGIBLE` reason. The fixture is private to the module and lives entirely in the source — no JSON, YAML, or config file is read.

### 6. Reconciliation status

`reconciliation_status=ReconciliationStatus.CLEAN` is passed to `build_daily_report` explicitly. The merged `ReconciliationProtocol` is **not** instantiated; the merged P3-05 `InMemoryReconciliation` is **not** imported or runtime-activated. The `gmc_rebuild.reconciliation` module is not imported.

### 7. §8 allowlist

The `MASTER_STATUS.md` §8 step 4a allowlist grows by one entry (`src/gmc_rebuild/dry_run`) in the same PR that introduces the directory, per the standing `§8 step 4b` rule. The candidate name `dry_run` tokenizes to `dry`, `run` — neither forbidden — so the §8 step 4 / step 4c scans stay clean. The PR raises the step 4a allowlist from sixteen entries to seventeen.

## Required Tests

The implementation PR carries the following end-to-end tests under `tests/dry_run/test_dry_run.py`:

- `test_run_dry_run_returns_a_daily_report` — type check on the return value.
- `test_run_dry_run_counts_match_expected_sample` — pins the expected `decisions_total == 3`, `would_trade == 2`, `would_skip == 1` distribution and the `would_trade + would_skip == decisions_total` invariant.
- `test_run_dry_run_applies_traded_intents_to_portfolio` — pins the `len(applied_intent_ids) == would_trade` invariant plus the canonical (sorted, unique) tuple form.
- `test_run_dry_run_reports_clean_reconciliation_status` — pins `reconciliation_status is ReconciliationStatus.CLEAN`.
- `test_run_dry_run_is_deterministic` — pins `run_dry_run() == run_dry_run()`.
- `test_format_report_includes_human_readable_summary` — pins that the rendered string is non-empty, contains the report date, the decision counts (`would_trade` / `would_skip`), and `reconciliation`.

The full pre-existing suite (748 tests on `main` at authoring) continues to pass unchanged plus the 6 new dry-run tests, for a new total of **754 tests passing**. Pre-commit exits 0.

## Explicitly Not Authorized

- **Any modification of any merged engine module** (`signal_intake`, `eligibility`, `decision`, `simulation`, `portfolio_state`, `reporting`, `operator_view`, `runtime`, `risk`, `logging`, `time`, `config`, `heartbeat`, `kill_switch`, `reconciliation`).
- **Any new public symbol on a merged subpackage.**
- **Any broker, real-account, market-data, network, persistence, scheduler, daemon, or `time.sleep`.**
- **Any env-var read, any secret, any credential, any API key.**
- **Any clock read inside the library** (`now_utc()` / `time.*` / `datetime.now()`).
- **Any `audit_event` emission from this package** (including importing `gmc_rebuild.logging`).
- **Any runtime activation of `InMemoryHeartbeat`, `InMemoryKillSwitch`, or `InMemoryReconciliation`** from a `__main__` / daemon / scheduler / re-export / runtime path. The `SafetyVerdict` is constructed directly with `clear=True` rather than driven through a `RuntimeShell` + P3 fakes pipeline.
- **Any re-export from `src/gmc_rebuild/__init__.py`.**
- **Any change to the §8 step 4 / step 4c forbidden-token set or the §8 step 8 staleness check.**
- **Any tag, GitHub release, or version bump.**
- **Touching or committing `.claude/` or `Claude_Transfes/`.**

The always-forbidden categories in `MASTER_STATUS.md` §6 and `plan/phase4_entry_plan.md` / `plan/phase5_entry_plan.md` / `plan/phase6_entry_plan.md` §10 remain forbidden in all modes; this packet relaxes none of them.

## Required Sequencing — Lightweight Lane

Per Kevin's 2026-06-18 directive ("Go with option (a): lightweight lane, single PR, this directive is the authorization. Do NOT create separate planning/Mode B PRs"):

- This artifact, the new `src/gmc_rebuild/dry_run/`, the new `tests/dry_run/`, the `MASTER_STATUS.md` §8 entry, and the `tests/test_package_skeleton.py` entry are committed together on a single feature branch (`feat/dry-run-entrypoint`) and opened as one PR.
- **No separate planning packet PR.** **No separate Mode B sibling PR.** The §6 rule 5 "Mode A PR-review text" channel remains available to Kevin at his discretion.
- Kevin's open P6-09 planning PRs (#186 / #187) are not touched by this work and remain orthogonal.
- Kevin remains the only approver for the merge.

## Required Validation

Before this PR is presented as complete, on the implementation branch:

```bash
git status --short --branch
git diff --name-status main
.venv/bin/pre-commit run --all-files
.venv/bin/python -m pytest -q
python -m gmc_rebuild.dry_run
```

with `git diff --name-status main` showing exactly the eight files in §Authorized Scope; pre-commit exiting `0` with every hook passing and no second-pass `files were modified by this hook` message; pytest passing the prior 748-test baseline plus the 6 new dry-run tests for a new total of **754 tests passing**; and the `python -m gmc_rebuild.dry_run` invocation printing a human-readable daily report to stdout containing the date, the decision counts, the net positions, and the reconciliation status.

## Review Basis

- Kevin's verbatim 2026-06-18 directive reproduced in §Authorization above.
- `tests/reporting/test_reporting.py` (merged P6-06 tests) — the reference for composing the SafetyVerdict, eligibility config, and signal/decision/order-intent fixtures.
- `src/gmc_rebuild/signal_intake/`, `src/gmc_rebuild/eligibility/`, `src/gmc_rebuild/decision/`, `src/gmc_rebuild/simulation/`, `src/gmc_rebuild/portfolio_state/`, `src/gmc_rebuild/reporting/`, `src/gmc_rebuild/operator_view/` (merged P6-01..P6-07 surfaces, head `99e3112`) — the public surfaces composed by this packet.
- `src/gmc_rebuild/runtime/_shell.py` and `src/gmc_rebuild/risk/interfaces.py` — `SafetyVerdict` / `HeartbeatStatus` / `KillSwitchState` / `ReconciliationStatus` used to construct the clear verdict.
- `MASTER_STATUS.md` §6 (always-forbidden categories), §8 (step 4 / 4a / 4b / 4c gates, the previously sixteen-entry allowlist) at `main` head `99e3112`.
- `AI_WORKFLOW.md` §1 / §6 / §7 (one approver; authorization-of-record discipline).
- `governance/authorizations/2026-06-15_p6-07.md` and `governance/authorizations/2026-06-15_p6-08.md` — structural reference for in-tree implementation-authorization artifacts.
