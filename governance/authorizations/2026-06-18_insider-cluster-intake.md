# Authorization — Insider-Cluster Signal Intake Adapter (PR INSIDER-CLUSTER-INTAKE)

Date: 2026-06-18
Authorizer: Kevin
Scope: New `src/gmc_rebuild/insider_cluster_intake/` subpackage, new `tests/insider_cluster_intake/` test directory with one committed one-row SQLite fixture, a `--source insider_cluster` flag added to the existing `gmc_rebuild.dry_run` entry point, plus the §8 step 4a allowlist entry. Reads ONE row from a caller-supplied `backtest_results` SQLite database in **read-only URI mode** and adapts it into a typed `gmc_rebuild.signal_intake.SignalIntent`. Modifies no existing engine module. No network, no broker, no real account state, no credentials, no env-var read, no secrets, no order placement. **Lightweight-lane single PR** per Kevin's 2026-06-18 directive.

## Authorization

Kevin's written directive for this packet, reproduced verbatim. Per `AI_WORKFLOW.md` §7 the verbatim block in this file is the authorization of record.

> Task: feed ONE real insider-cluster signal into the existing dry-run engine. Lightweight lane. Test-first. Read-only. No money.
>
> Context: PR #188 added a runnable dry-run loop (python -m gmc_rebuild.dry_run) that composes the existing engine modules (signal_intake, eligibility, decision, simulation, portfolio_state, reporting). Right now it runs on synthetic/stub input. I want it to ingest ONE real signal from our validated insider-cluster backtest database and produce a clear SafetyVerdict — without modifying any engine module.
>
> Hard constraints:
>
> Do NOT modify any existing engine module (signal_intake, eligibility, decision, simulation, portfolio_state, reporting). If you cannot produce a clear SafetyVerdict without touching an engine module, STOP and report why.
>
> READ-ONLY against a COPY of the database. First copy the DB to a temp/fixture path and read from the copy, never the original. Original lives at ~/Desktop/Claude_Programs/Trading_Programs/form4_scanner/insider_backtest_results.db (this is a different machine/repo — if the path isn't present, ask me for a fixture; do NOT invent data).
>
> No network, no broker, no order placement. This must remain impossible to place a real trade.
>
> Leave PRs #186 and #187 (P6-09 planning) open and untouched.
>
> Use whatever label/scope your harness requires; do not collide with existing scopes. Relabel as needed.
>
> The real data — table backtest_results, relevant columns:
> ticker TEXT, company TEXT, signal_date TIMESTAMP, entry_date TIMESTAMP, entry_price REAL, num_insiders INTEGER, num_transactions INTEGER, total_dollars REAL, roles TEXT, has_csuite/has_ceo/has_cfo INTEGER, alpha_5d...alpha_60d REAL, year INTEGER.
>
> Mapping real row → the engine's SignalIntent (adapt to the actual SignalIntent fields in this repo — inspect them first):
>
> ticker → symbol
>
> side = BUY (insider clusters are long signals; this DB is buys only)
>
> entry_price → reference/entry price
>
> quantity → derive deterministically from a fixed notional (e.g. a constant TARGET_NOTIONAL ÷ entry_price, floored to whole shares) — do not hardcode a magic number without a named constant
>
> rationale/metadata → compose from num_insiders, total_dollars, roles, has_ceo/has_cfo (e.g. "3 insiders, $4.4M cluster, CEO+Director")
>
> signal_date/entry_date → the signal's timestamps
>
> Deliverable:
>
> A small adapter (new file, e.g. src/gmc_rebuild/signals/insider_cluster_adapter.py) that reads ONE row from the copied DB and returns a valid SignalIntent. Inspect the real SignalIntent definition before writing — match its actual fields/types.
>
> A test (new file under tests/) that uses a tiny committed SQLite fixture (one row, NKE-style: 3 insiders, ~$4.4M, roles "CEO,Director", entry ~$61) and asserts the adapter produces a valid SignalIntent, then runs it through the dry-run loop and asserts a clear SafetyVerdict comes out.
>
> Wire it so python -m gmc_rebuild.dry_run --source insider_cluster (or equivalent flag — your call on the interface) runs the real-signal path end-to-end and prints the verdict + a one-line decision summary.
>
> Run the full test suite; all existing 754 tests must still pass plus your new test(s).
>
> Then STOP and report: the adapter file, the test, the command to run it, and the SafetyVerdict for the sample signal. Open a PR; do not merge.

## In-Tree Tag and Naming Decision

This packet is recorded under the in-tree tag **`PR INSIDER-CLUSTER-INTAKE`**. The directive's suggested path `src/gmc_rebuild/signals/...` was **rejected** because the package-component token `signals` (plural) is in the §8 step 4 / step 4c always-forbidden token set (alongside `signal`, `strategy`, `scanner`, etc.) and is meant to flag any directory that *generates* signals — a category that remains forbidden in all modes per `MASTER_STATUS.md` §6 and `plan/phase6_entry_plan.md` §10. Renaming to `src/gmc_rebuild/insider_cluster_intake/` makes the intent (signal **intake / adapter**, not signal **generation**) visible at the import site and tokenizes cleanly to `insider`, `cluster`, `intake` — none of which is forbidden. The adapter's role is identical to `gmc_rebuild.signal_intake` (P6-01) in spirit: it accepts an already-rendered candidate from an external source; it does not score, scan, model, or generate.

## SignalIntent Inspection (Required by Directive)

Per the directive's instruction "inspect them first", the merged `SignalIntent` field set was confirmed before any code was written. The closed five-field shape declared at `src/gmc_rebuild/signal_intake/_intent.py` is:

- `intent_id: str` — non-empty.
- `symbol: str` — non-empty.
- `side: SignalSide` — closed `BUY` / `SELL` enum.
- `quantity: int` — positive; `bool` explicitly rejected.
- `rationale: str` — non-empty.

The real `backtest_results` columns `entry_price`, `signal_date`, `entry_date`, `num_insiders`, `total_dollars`, `roles`, `has_ceo`, `has_cfo`, `num_transactions` are **not** fields on `SignalIntent`. They are folded into:

- `intent_id` ← deterministic composition of ticker + `signal_date` date token.
- `symbol` ← ticker.
- `side` ← `SignalSide.BUY` (every row in this DB is a long insider cluster).
- `quantity` ← `floor(TARGET_NOTIONAL_USD / entry_price)` with a minimum of 1.
- `rationale` ← deterministic string composed from `num_insiders`, `total_dollars` (in millions, 2dp), and `roles`. Example: `"3 insiders; $4.45M cluster; roles: CEO,Director"`.

## Authorized Scope

The PR adds **only** the following files; modifies no other beyond the listed gate updates:

| File | Change |
|---|---|
| `src/gmc_rebuild/insider_cluster_intake/__init__.py` | new — re-exports the public surface |
| `src/gmc_rebuild/insider_cluster_intake/_adapter.py` | new — private adapter implementation |
| `tests/insider_cluster_intake/__init__.py` | new — empty test-package marker |
| `tests/insider_cluster_intake/test_insider_cluster_intake.py` | new — five end-to-end tests (test-first) |
| `tests/insider_cluster_intake/fixtures/build_sample_db.py` | new — one-shot fixture generator |
| `tests/insider_cluster_intake/fixtures/sample.db` | new — 8KB committed one-row SQLite fixture (deterministic output of the generator) |
| `governance/authorizations/2026-06-18_insider-cluster-intake.md` | new (this artifact) |
| `MASTER_STATUS.md` | modified — §8 step 4a: one new `allowed_p2_infra` entry, `pr_tag` arm, iteration entry, OK-echo extension, and comment block |
| `tests/test_package_skeleton.py` | modified — one new authorized-package entry plus docstring entry |
| `src/gmc_rebuild/dry_run/__init__.py` | modified — re-export `run_dry_run_insider_cluster` and `format_insider_cluster_summary` |
| `src/gmc_rebuild/dry_run/_loop.py` | modified — add `run_dry_run_insider_cluster()` and `format_insider_cluster_summary()` |
| `src/gmc_rebuild/dry_run/__main__.py` | modified — `argparse`-based `--source {synthetic,insider_cluster}` flag and `--db PATH` |

**No engine module** under `signal_intake/`, `eligibility/`, `decision/`, `simulation/`, `portfolio_state/`, `reporting/`, `operator_view/`, `runtime/`, `risk/`, `logging/`, `time/`, `config/`, `heartbeat/`, `kill_switch/`, or `reconciliation/` is modified by this packet, per the directive's hard constraint.

## Authorized Contract

### 1. Read-only filesystem access (no writes)

The adapter opens the DB via `sqlite3.connect("file:<path>?mode=ro", uri=True)`. SQLite's URI `?mode=ro` mode raises `sqlite3.OperationalError` on any attempt to write to the connection. The adapter never executes `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`, `ATTACH`, `BEGIN`, or `COMMIT`. The connection is opened, one `SELECT` runs, and the connection is closed in a `try`/`finally` block.

### 2. Per-directive read-from-a-copy discipline

The test copies the committed `sample.db` into a `tempfile.TemporaryDirectory()` via `shutil.copy` before opening it. The committed fixture itself is never read by the test directly — only its copy. At CLI runtime, the operator passes `--db PATH`; the adapter only reads (read-only URI mode), so the operator's real DB can never be modified through this path either.

### 3. Deterministic mapping

- `TARGET_NOTIONAL_USD = 10_000` (named constant; the directive forbids magic numbers).
- `quantity = max(1, int(TARGET_NOTIONAL_USD / entry_price))` — floored to whole shares.
- `intent_id = f"insider-{ticker}-{signal_date.split(' ')[0]}"` — pure, deterministic, no clock read.
- `rationale = f"{num_insiders} insiders; ${total_dollars / 1_000_000:.2f}M cluster; roles: {roles}"`.
- `side = SignalSide.BUY` for every row (the directive states this DB is buys-only).

### 4. Adapter import surface (closed)

`from __future__ import annotations`; stdlib `sqlite3`, `dataclasses`, `pathlib.Path`; in-repo `gmc_rebuild.signal_intake` only (for `SignalIntent`, `SignalSide`). **No** `os`, `socket`, `requests`, `urllib`, `http`, `ssl`, `smtplib`, `ftplib`, `threading`, `asyncio`, `subprocess`, `pickle`, `shelve`, `time`, `uuid`, `random`. **No** `gmc_rebuild.runtime`, `gmc_rebuild.logging`, `gmc_rebuild.config`, `gmc_rebuild.time`, `gmc_rebuild.simulation`, `gmc_rebuild.decision`, `gmc_rebuild.eligibility`, `gmc_rebuild.portfolio_state`, `gmc_rebuild.reporting`, or `gmc_rebuild.operator_view`. The adapter consumes only the P6-01 `SignalIntent` type; it has no view into downstream engine state and cannot place an order.

### 5. CLI integration

`python -m gmc_rebuild.dry_run --source insider_cluster [--db PATH]` runs the real-signal path end-to-end:

```
load_insider_cluster_signal(db_path)        # adapter
  -> accept_signal_intent(signal)           # P6-01
  -> check_eligibility(intent, config)      # P6-02 with allowed_symbols={signal.symbol}
  -> compose_position_decision(...)         # P6-03 against a clear SafetyVerdict
  -> SimulationBoundary.propose_order(...)  # P5-01/P5-02/P6-04 on LOCAL_ONLY lane
  -> apply_simulated_order_intent(...)      # P6-05
  -> build_daily_report(...)                # P6-06
  -> format_insider_cluster_summary(...)    # daily report + verdict + 1-line decision
  -> print(...)                             # the only side effect
```

Default `--db` is the committed fixture path under `tests/insider_cluster_intake/fixtures/sample.db` so the command is runnable from a fresh checkout. Default `--source` is `synthetic` for backward compatibility with PR #188.

### 6. §8 allowlist

The `MASTER_STATUS.md` §8 step 4a allowlist grows from seventeen entries (after PR #188) to eighteen with the addition of `src/gmc_rebuild/insider_cluster_intake`. The candidate name tokenizes to `insider`, `cluster`, `intake` — none of which is in the §8 forbidden-token set — so the step 4 / step 4c scans stay clean.

## Required Tests

The implementation PR carries the following end-to-end tests under `tests/insider_cluster_intake/test_insider_cluster_intake.py`:

- `test_committed_fixture_has_expected_nke_row` — sanity check that the committed `sample.db` contains exactly the documented NKE row.
- `test_adapter_returns_a_valid_signal_intent` — pins the field mapping: `symbol == "NKE"`, `side is SignalSide.BUY`, `quantity == int(TARGET_NOTIONAL_USD / 61.19)`, rationale contains `"3 insiders"`, `"CEO"`, and the dollars-in-millions string.
- `test_adapter_signal_intent_id_is_deterministic` — pins `load_insider_cluster_signal()` is referentially transparent.
- `test_insider_cluster_dry_run_emits_clear_verdict_and_would_trade` — full end-to-end: `verdict.clear is True`, `verdict.blockers == ()`, `decision.outcome is WOULD_TRADE`, `decision.reasons == ()`, daily report counts and applied-intent-ID tuple match.
- `test_format_insider_cluster_summary_includes_verdict_and_decision` — pins the rendered summary contains `"NKE"`, `"safety_verdict"`, `"clear=True"`, `"WOULD_TRADE"`, and the deterministic intent ID.

The full pre-existing suite (754 tests on `main` at authoring) continues to pass unchanged plus the 5 new insider-cluster tests, for a new total of **759 tests passing**. Pre-commit exits 0.

## Explicitly Not Authorized

- **Any modification of any merged engine module** (`signal_intake`, `eligibility`, `decision`, `simulation`, `portfolio_state`, `reporting`, `operator_view`, `runtime`, `risk`, `logging`, `time`, `config`, `heartbeat`, `kill_switch`, `reconciliation`).
- **Any new public symbol on a merged subpackage.**
- **Any DB write.** No `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`, `ATTACH`, `BEGIN`, `COMMIT`. The SQLite `?mode=ro` URI flag enforces this at the C library level.
- **Any network call** (`socket`, `urllib`, `requests`, `http`, `ssl`, `smtplib`, `ftplib`, DNS).
- **Any broker, real-account, market-data, order placement, or order routing.**
- **Any env-var read, secret, credential, or API key.**
- **Any clock read.** No `now_utc()` / `time.*` / `datetime.now()` inside the adapter or the loop.
- **Any `audit_event` emission** from this package (the package does not import `gmc_rebuild.logging`).
- **Any runtime activation of `InMemoryHeartbeat`, `InMemoryKillSwitch`, or `InMemoryReconciliation`** from a `__main__` / daemon / scheduler / re-export / runtime path.
- **Any re-export from `src/gmc_rebuild/__init__.py`.**
- **Any change to the §8 step 4 / step 4c forbidden-token set or the §8 step 8 staleness check.**
- **Any tag, GitHub release, or version bump.**
- **Touching or committing `.claude/` or `Claude_Transfes/`.**
- **Touching, closing, or modifying PRs #186 or #187 (P6-09 planning).** Those remain open and untouched per the directive.
- **Any "real signals" path** beyond reading ONE row from the caller-supplied SQLite DB. The adapter is single-row by design; batching, streaming, or scheduled polling is out of scope.

The always-forbidden categories in `MASTER_STATUS.md` §6 remain forbidden in all modes; this packet relaxes none of them. In particular, the package name `insider_cluster_intake/` is on the §8 step 4a allowlist as an authorized **intake adapter** (not a signal generator). Reusing or repurposing this allowlist entry for any signal-generation, strategy, scanner, model, broker, or paper/live execution surface would require a separate written authorization from Kevin.

## Required Sequencing — Lightweight Lane

Per Kevin's 2026-06-18 directive ("Lightweight lane. Test-first. Read-only. No money."):

- This artifact, the new `src/gmc_rebuild/insider_cluster_intake/`, the new `tests/insider_cluster_intake/`, the `MASTER_STATUS.md` §8 entry, the `tests/test_package_skeleton.py` entry, and the `gmc_rebuild.dry_run` CLI wiring are committed together on a single feature branch (`feat/insider-cluster-intake`) and opened as one PR.
- **No separate planning packet PR.** **No separate Mode B sibling PR.** Mode A PR-review text remains available at Kevin's discretion.
- Kevin's open P6-09 planning PRs (#186 / #187) are not touched by this work.
- Kevin remains the only approver for the merge.

## Required Validation

Before this PR is presented as complete, on the implementation branch:

```bash
git status --short --branch
git diff --name-status main
.venv/bin/pre-commit run --all-files
.venv/bin/python -m pytest -q
python -m gmc_rebuild.dry_run --source insider_cluster
```

with `git diff --name-status main` showing exactly the file set in §Authorized Scope; pre-commit exiting `0`; pytest passing the prior 754-test baseline plus the 5 new insider-cluster tests for a new total of **759 tests passing**; and the `python -m gmc_rebuild.dry_run --source insider_cluster` invocation printing a deterministic daily report followed by `safety_verdict: clear=True, blockers=none` and `decision: WOULD_TRADE ...` lines.

## Review Basis

- Kevin's verbatim 2026-06-18 directive reproduced in §Authorization above.
- `src/gmc_rebuild/signal_intake/_intent.py` (merged P6-01 surface, head `67196a3`) — the `SignalIntent` field shape the adapter targets.
- `src/gmc_rebuild/dry_run/` (merged PR #188 P6-DRYRUN-ENTRYPOINT, head `67196a3`) — the loop the new path plugs into.
- The real `backtest_results` schema and the NKE row shape (verified read-only on 2026-06-18 against `~/Desktop/Claude_Programs/Trading_Programs/form4_scanner/insider_backtest_results.db`).
- `MASTER_STATUS.md` §6 (always-forbidden categories), §8 (step 4 / 4a / 4b / 4c gates, the seventeen-entry allowlist post PR #188) at `main` head `67196a3`.
- `AI_WORKFLOW.md` §1 / §6 / §7 (one approver; authorization-of-record discipline).
- `governance/authorizations/2026-06-18_dry-run-entrypoint.md` — the immediate structural precedent for a lightweight-lane single-PR composition packet.
