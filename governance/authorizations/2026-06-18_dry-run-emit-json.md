# Authorization — Dry-Run `--emit-json` Opt-In Decision Export (PR DRY-RUN-EMIT-JSON)

Date: 2026-06-18
Authorizer: Kevin
Scope: Add a `--emit-json <path>` opt-in flag to the existing `gmc_rebuild.dry_run` entry point. When (and only when) the operator explicitly passes the flag alongside `--source insider_cluster`, the entry point writes the decision payload as JSON to the single caller-supplied path. No engine module is modified.

## Authorization

Kevin's written directives for this packet, reproduced verbatim. Per `AI_WORKFLOW.md` §7 the verbatim blocks in this file are the authorization of record. (Two messages: the original Step A directive plus the explicit narrowing.)

### Step A directive (original)

> Task: add a READ-ONLY dashboard panel showing today's dry-run decisions from the governed engine. Display layer only. No money, no broker, no credentials.
>
> Context: This is the GMC Flask dashboard at ~/Desktop/Claude_Programs/Trading_Programs/gmc_dashboard/gmc_dashboard.py. It serves panels via /api/... routes, each backed by a _fetch_*() function returning JSON, cached via cached(name, ttl, fetch_fn). The frontend is templates/dashboard.html. Separately, the governed engine gmc_rebuild (at ~/gmc-rebuild) has a runnable dry-run: python -m gmc_rebuild.dry_run --source insider_cluster prints today's would-trade decisions. I want those decisions visible on the cockpit.
>
> Architecture (file hand-off — do NOT make the dashboard import the engine):
>
> The engine writes its decisions to a JSON file; the dashboard reads that file. Loose coupling, separate venvs, fully inspectable.
>
> Hard constraints — read carefully:
>
> Do NOT touch config.py, positions.db, the IB Gateway code, COINBASE_CDP_KEY, FMP_API_KEY, or any credential, account number, or broker call. You are adding a display panel and nothing else.
>
> Do NOT modify any existing _fetch_* function or existing route. Only ADD new code.
>
> No network calls, no order placement, no writes to any trading database.
>
> The new dashboard route must be read-only: it reads a JSON file and returns it. If the file is missing, return an empty/"no decisions yet" payload gracefully — never crash the dashboard.
>
> Ask me before each file edit (Auto Mode is off on purpose).
>
> Step A — engine side (in ~/gmc-rebuild, on a new branch, test-first, this is the governed repo so follow its MASTER_STATUS gates):
>
> Add a small opt-in way for the dry-run to also write its decision report to a JSON file — e.g. python -m gmc_rebuild.dry_run --source insider_cluster --emit-json <path>. Default behavior (no flag) must stay byte-for-byte unchanged. Do NOT modify any engine module; this is an output option on the dry-run entry point only, same lane as PR #189.
>
> JSON shape: { "as_of": "<date>", "decisions": [ { "symbol", "side", "quantity", "outcome" (e.g. WOULD_TRADE), "rationale", "verdict_clear": true/false } ], "summary": { "total", "would_trade", "would_skip" } }.
>
> Add a test asserting the JSON file is written with that shape for the NKE fixture. Full suite must stay green (currently 759). Open a PR, do not merge, report back.

### Narrowing confirmation

> Keep "decisions" as an array — yes.
>
> Scope --emit-json to --source insider_cluster only — yes, don't refactor synthetic.
>
> Authorization stub — approved, but narrow the wording: write happens ONLY when --emit-json <path> is explicitly passed (no flag = never writes); writable surface is the single caller-supplied path only (no default path, no extra dir creation); output is decision JSON only — never write to any trading DB, positions.db, the engine source tree, or any governance/state file; relaxation applies to the dry_run entry point ONLY, not any engine module.
>
> One addition to the test plan: make the back-compat check a committed test — assert the no-flag run's stdout is byte-for-byte identical to current main, not just that the filesystem is untouched.
>
> Write the failing tests first, implement, open the PR, do NOT merge. Report back with the PR link, the --emit-json command, the sample JSON output, and your Step B plan.

## In-Tree Tag and Constraint Relaxation Note

This packet is recorded under the in-tree tag **`PR DRY-RUN-EMIT-JSON`**. It does **not** add a new `src/**` directory and therefore does **not** modify the `MASTER_STATUS.md` §8 step 4a `allowed_p2_infra` allowlist. The `src/gmc_rebuild/dry_run/` directory is already allowlisted (PR P6-DRYRUN-ENTRYPOINT, PR #188).

The earlier PR #188 authorization (`governance/authorizations/2026-06-18_dry-run-entrypoint.md`) stated **"No filesystem write, no `open(` for write, no `pickle`, no `shelve`, no SQLite/DuckDB/database, no on-disk artifact"** as a hard constraint on the dry-run entry point. **This PR explicitly relaxes that constraint in exactly one narrowly-scoped way, per Kevin's 2026-06-18 narrowing directive reproduced verbatim above**:

- **Write happens ONLY when `--emit-json <path>` is explicitly passed.** No flag = the entry point never writes anywhere. The default `python -m gmc_rebuild.dry_run` (with or without `--source insider_cluster`) is byte-for-byte unchanged and is asserted as such by `tests/dry_run/test_dry_run_emit_json.py::test_no_flag_stdout_is_byte_for_byte_unchanged_from_main` against a committed expected-stdout literal captured at commit `a808ed7`.
- **Writable surface is the single caller-supplied path only.** No default path; the flag has `default=None`. No `mkdir`, no `Path.mkdir(parents=True)`, no directory creation of any kind. The parent directory must already exist; if it does not, `Path.write_text` raises `FileNotFoundError` and the operator sees a clear failure.
- **Output is decision JSON only.** The package never writes to any trading database, `positions.db`, the engine source tree (`src/gmc_rebuild/**`), `governance/**`, `MASTER_STATUS.md`, `plan/**`, `monitoring/**`, the test suite, or any other governance/state file. The JSON content is exactly the shape documented in `build_decisions_json_payload` — six per-decision fields and a three-field summary — and nothing else.
- **Relaxation applies to the dry-run entry point ONLY.** No engine module (`signal_intake`, `eligibility`, `decision`, `simulation`, `portfolio_state`, `reporting`, `operator_view`, `runtime`, `risk`, `logging`, `time`, `config`, `heartbeat`, `kill_switch`, `reconciliation`) is modified, gains a new public symbol, or acquires a write capability. The `insider_cluster_intake` adapter (PR #189) is also unchanged. `gmc_rebuild.runtime` is not imported by the new code path. No `audit_event` emission. No clock read.

## Authorized Scope

The PR adds **only** the following files; modifies no other beyond the listed dry-run entry-point updates:

| File | Change |
|---|---|
| `src/gmc_rebuild/dry_run/_loop.py` | modified — adds frozen `InsiderClusterCycle` rich bundle, private `_run_insider_cluster_cycle()` returning it, and pure helper `build_decisions_json_payload()`. The existing public `run_dry_run_insider_cluster()` is refactored to delegate to the private cycle and preserves its 3-tuple return contract byte-for-byte. |
| `src/gmc_rebuild/dry_run/__main__.py` | modified — adds `--emit-json PATH` argparse argument; parser.error if combined with `--source synthetic`; on the insider-cluster path with the flag present, calls `Path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")`. |
| `src/gmc_rebuild/dry_run/__init__.py` | modified — re-exports `build_decisions_json_payload`; refines the package docstring to reflect the new opt-in surface. |
| `tests/dry_run/test_dry_run_emit_json.py` | new — seven tripwires (back-compat byte-for-byte stdout, --emit-json shape, pretty-print + sort-keys layout, no-flag no-write, --emit-json rejected on synthetic, helper unit test, helper length-mismatch rejection). |
| `governance/authorizations/2026-06-18_dry-run-emit-json.md` | new (this artifact) |

**No `MASTER_STATUS.md` change** (no new `src/**` directory). **No `plan/**` change.** **No existing engine module modified.** **No existing test file modified.** **No `.gitignore` change.**

## Authorized Contract

### 1. CLI surface

```
python -m gmc_rebuild.dry_run [--source {synthetic,insider_cluster}] [--db PATH] [--emit-json PATH]
```

- `--emit-json PATH` defaults to `None` (no write).
- `--emit-json PATH` requires `--source insider_cluster`. Passing it with `--source synthetic` triggers `argparse.ArgumentParser.error(...)` → `SystemExit(2)` with a stderr message naming `insider_cluster`. No file is created.
- `--emit-json PATH` does **not** create directories. If `PATH.parent` does not exist, `Path.write_text` raises `FileNotFoundError`.

### 2. JSON shape (exact)

```json
{
  "as_of": "<DailyReport.report_date>",
  "decisions": [
    {
      "symbol": "<SignalIntent.symbol>",
      "side": "<SignalIntent.side.value>",
      "quantity": "<SignalIntent.quantity>",
      "outcome": "<PositionDecision.outcome.value>",
      "rationale": "<SignalIntent.rationale>",
      "verdict_clear": "<SafetyVerdict.clear>"
    }
  ],
  "summary": {
    "total": "<DailyReport.decisions_total>",
    "would_trade": "<DailyReport.would_trade>",
    "would_skip": "<DailyReport.would_skip>"
  }
}
```

`"decisions"` is always an array (single-element today on the insider-cluster path; the shape is forward-compatible with multi-signal cycles a separately-authorized future packet could add). On-disk JSON is pretty-printed with `indent=2`, `sort_keys=True`, and a trailing newline so text diffs across runs are stable.

For the committed NKE fixture the resulting payload is:

```json
{
  "as_of": "2026-06-18",
  "decisions": [
    {
      "outcome": "WOULD_TRADE",
      "quantity": 163,
      "rationale": "3 insiders; $4.45M cluster; roles: CEO,Director",
      "side": "BUY",
      "symbol": "NKE",
      "verdict_clear": true
    }
  ],
  "summary": {
    "total": 1,
    "would_skip": 0,
    "would_trade": 1
  }
}
```

### 3. Determinism and inertness

- `build_decisions_json_payload` is a pure function with no I/O, no clock read, no `audit_event` emission, no `gmc_rebuild.runtime` import, no `gmc_rebuild.logging` import.
- The JSON is `json.dumps`-serialized deterministically (`sort_keys=True`).
- Repeated invocations of the CLI with the same inputs produce byte-for-byte identical JSON output.
- No network call. No env-var read. No secret/credential. No broker SDK. No `time.sleep`. No `asyncio.sleep`. No `__main__`-as-daemon.

## Required Tests

Seven tripwires under `tests/dry_run/test_dry_run_emit_json.py`:

1. `test_no_flag_stdout_is_byte_for_byte_unchanged_from_main` — back-compat. Locked `_EXPECTED_NO_FLAG_STDOUT` literal captured from `main` at commit `a808ed7`; any drift fails immediately.
2. `test_emit_json_writes_documented_shape_for_nke_fixture` — payload deep-equality against `_EXPECTED_NKE_PAYLOAD`.
3. `test_emit_json_output_is_pretty_printed_and_sorted_deterministically` — on-disk text is multi-line and keys appear in alphabetical order (`as_of` < `decisions` < `summary`).
4. `test_no_flag_creates_no_files_in_the_run_directory` — temp-directory snapshot before/after is identical.
5. `test_emit_json_rejected_on_synthetic_source` — `SystemExit` with non-zero code, stderr contains `insider_cluster`, no file created.
6. `test_build_decisions_json_payload_produces_documented_shape` — direct unit test of the helper.
7. `test_build_decisions_json_payload_rejects_length_mismatch` — `decisions` / `signals` length mismatch raises `ValueError`.

Total suite count grows from **759** to **766**.

## Explicitly Not Authorized

- **Any modification of any merged engine module** (`signal_intake`, `eligibility`, `decision`, `simulation`, `portfolio_state`, `reporting`, `operator_view`, `runtime`, `risk`, `logging`, `time`, `config`, `heartbeat`, `kill_switch`, `reconciliation`) or of `insider_cluster_intake/`.
- **Any default writable path.** The `--emit-json` argparse default is `None`. The CLI does not synthesize, derive, or fall back to any path of its own.
- **Any directory creation.** `Path.mkdir`, `os.makedirs`, `pathlib.Path.parent.mkdir`, or any equivalent is not used. The operator's `PATH.parent` must already exist.
- **Any write outside the caller-supplied `--emit-json PATH`.** No log file, no audit trail, no run journal, no cache, no `.last_run`. The single `Path.write_text` call to the operator's chosen path is the only filesystem write anywhere in the package.
- **Any write to a trading database, `positions.db`, the engine source tree (`src/gmc_rebuild/**`), `governance/**`, `MASTER_STATUS.md`, `plan/**`, `monitoring/**`, the test suite, `.gitignore`, `pyproject.toml`, `.pre-commit-config.yaml`, or any other governance/state file.**
- **Any synthetic-source JSON export.** `--emit-json` with `--source synthetic` is explicitly rejected. A separately-authorized future packet could relax this; this one does not.
- **Any new network call** (`socket`, `urllib`, `requests`, `http`, `ssl`, `smtplib`, `ftplib`, DNS).
- **Any broker, real-account, market-data, order placement, or order routing.**
- **Any env-var read, secret, credential, or API key.**
- **Any clock read.** No `now_utc()` / `time.*` / `datetime.now()` inside the new code path.
- **Any `audit_event` emission** from the dry-run package or the JSON helper.
- **Any runtime activation of `InMemoryHeartbeat`, `InMemoryKillSwitch`, or `InMemoryReconciliation`** from a `__main__` / daemon / scheduler / re-export / runtime path. The `SafetyVerdict` is still constructed directly with `clear=True`, mirroring PR #188.
- **Any re-export from `src/gmc_rebuild/__init__.py`.**
- **Any change to the `MASTER_STATUS.md` §8 step 4a allowlist**, the step 4 / 4c forbidden-token set, or the step 8 staleness check.
- **Any tag, GitHub release, or version bump.**
- **Touching, modifying, or closing PRs #186 / #187 (P6-09 planning).**
- **Touching the GMC Flask dashboard repo** at `~/Desktop/Claude_Programs/Trading_Programs/gmc_dashboard/`. Step B of the operator directive (dashboard side) is scaffolded in the PR description for review but is **not** executed in this PR.

The always-forbidden categories in `MASTER_STATUS.md` §6 remain forbidden in all modes; this packet relaxes none of them.

## Required Sequencing — Lightweight Lane

Per Kevin's 2026-06-18 directive ("Lightweight lane. Test-first. Read-only. No money."):

- This artifact, the `_loop.py` / `__main__.py` / `__init__.py` modifications, the new test file, and the new authorization stub are committed together on a single feature branch (`feat/dry-run-emit-json`) and opened as one PR.
- **No separate planning packet PR.** **No separate Mode B sibling PR.** Mode A PR-review text remains available at Kevin's discretion.
- Step B (dashboard side) is **not** part of this PR. It will be done in a separate session against the dashboard repo only after Kevin's explicit go-ahead.
- Kevin remains the only approver for the merge.

## Required Validation

Before this PR is presented as complete, on the implementation branch:

```bash
git status --short --branch
git diff --name-status main
.venv/bin/pre-commit run --all-files
.venv/bin/python -m pytest -q
python -m gmc_rebuild.dry_run --source insider_cluster                               # no-flag (unchanged)
python -m gmc_rebuild.dry_run --source insider_cluster --emit-json /tmp/decisions.json
cat /tmp/decisions.json
```

with `git diff --name-status main` showing exactly the five files in §Authorized Scope; pre-commit exiting `0`; pytest passing the prior 759-test baseline plus the 7 new tests for a new total of **766 tests passing**; the no-flag invocation printing the locked `_EXPECTED_NO_FLAG_STDOUT` text byte-for-byte; and the `--emit-json` invocation producing the documented JSON shape at `/tmp/decisions.json`.

## Review Basis

- Kevin's verbatim 2026-06-18 directives reproduced in §Authorization above.
- `governance/authorizations/2026-06-18_dry-run-entrypoint.md` (PR #188 authorization) — the constraint this PR explicitly and narrowly relaxes.
- `governance/authorizations/2026-06-18_insider-cluster-intake.md` (PR #189 authorization) — the immediate structural precedent and the source of the `run_dry_run_insider_cluster()` cycle the new helper refactors.
- `src/gmc_rebuild/signal_intake/_intent.py`, `src/gmc_rebuild/decision/_compose.py`, `src/gmc_rebuild/reporting/_report.py`, `src/gmc_rebuild/runtime/_shell.py` (merged engine surfaces, head `a808ed7`) — the field shapes the JSON payload echoes.
- `MASTER_STATUS.md` §6 (always-forbidden categories), §8 (step 4 / 4a / 4b / 4c gates) at `main` head `a808ed7`.
- `AI_WORKFLOW.md` §1 / §6 / §7 (one approver; authorization-of-record discipline).

---

## Addendum — `--emit-json -` stdout sink (in-lane follow-up)

Date: 2026-06-20
Status: In-lane, non-scope-expanding extension of the `--emit-json` flag above. Recorded here rather than as a separate phase-expanding artifact because it opens no new phase and expands no scope under `AI_WORKFLOW.md` §7 (it adds no `src/**` directory, no engine-module change, no new public symbol, no new filesystem surface, and no new always-forbidden capability). Kevin remains the only approver for the merge.

### What changed

`--emit-json` now accepts the single character `-` as a sentinel meaning "write the JSON to stdout instead of to a file." Everything else about the flag is unchanged:

- The payload is the **same** `build_decisions_json_payload` output, serialized **identically** (`json.dumps(..., indent=2, sort_keys=True) + "\n"`). The stdout text is byte-for-byte equal to what `--emit-json <path>` writes to disk for the same run (asserted by `test_emit_json_dash_stdout_matches_file_payload_byte_for_byte`).
- `--emit-json -` is still **rejected on `--source synthetic`** by the same `parser.error(...)` → `SystemExit(2)` path.
- The human summary is still printed first; the JSON follows it on stdout. The no-flag default stdout is unchanged (the back-compat tripwire still locks it byte-for-byte).

### Why this is in-lane and not scope-expanding

- **No new filesystem surface.** When the argument is `-`, **no file is created** — the JSON goes to stdout, which is the dry-run entry point's already-sanctioned side effect (the same `print` channel PR #188 authorized). The `Path.write_text` path is taken only for a real path argument, exactly as before. `test_emit_json_dash_writes_payload_to_stdout_and_creates_no_file` snapshots the run directory before/after and asserts no file appears.
- **No engine module changed.** The change is confined to `src/gmc_rebuild/dry_run/__main__.py` argument handling plus docstring touch-ups in `__init__.py` and `__main__.py`. No engine module gains a symbol or a capability. `build_decisions_json_payload` is unchanged.
- **No new `src/**` directory** ⇒ no `MASTER_STATUS.md` §8 step 4a allowlist change, no `plan/**` change, no new always-forbidden capability (no network, no broker, no clock read, no env-var, no secret, no `audit_event`, no root-package re-export).

### Files touched by this addendum's PR

| File | Change |
|---|---|
| `src/gmc_rebuild/dry_run/__main__.py` | modified — `--emit-json` arg drops `type=Path`, gains the `-`→stdout branch; usage/docstring updated. |
| `src/gmc_rebuild/dry_run/__init__.py` | modified — package docstring notes the `-` stdout sink. |
| `tests/dry_run/test_dry_run_emit_json.py` | modified — three new tripwires (stdout payload + no file, byte-for-byte equality with the file payload, synthetic rejection of `-`); module docstring updated. |
| `governance/authorizations/2026-06-18_dry-run-emit-json.md` | modified — this addendum. |

### Still explicitly not authorized

Everything in the parent "Explicitly Not Authorized" list above remains forbidden. In particular: no default path or default stdout (no flag = no emission), no directory creation, no second file sink, no synthetic-source export, no engine-module change, no broker / real-account / market-data / order path, and no governance/state write beyond this addendum.
