# Authorization — Dry-Run `--append-run-history` Structured Local History (PR DRYRUN-RUN-HISTORY)

Date: 2026-06-20
Authorizer: Kevin
Scope: Add an opt-in `--append-run-history PATH` flag (with the required
`--run-id ID` companion) that appends one deterministic JSONL record per
dry-run cycle to a small caller-supplied local file, so repeated
experiments accrete into a comparable record. Insider-cluster and
signals_json sources only. No new reconciliation or decision logic; pure
consumer of the merged cycle bundle. The record schema (documented in
`src/gmc_rebuild/dry_run/_run_history.py`, `schema_version` = 1) carries
the run_id, source, report date, input summary (signal count, sorted
symbols, paths to the inputs), decision counts plus per-signal
outcomes, net positions, and the reconciliation outcome (if
reconciliation was requested).

## Authorization

Kevin's written directive for tonight's work, reproduced verbatim. Per
`AI_WORKFLOW.md` §7 the verbatim block in this file is the authorization
of record for this narrow, tangible-progress packet.

> Continue gmc-rebuild from current main after merged PR #202.
>
> Kevin's working doctrine:
> Solid tested foundation, then MVP velocity. We are now past dry-run
> operator-readiness and into the MVP trading-system learning loop. Do
> not polish old surfaces unless required. Build the smallest useful
> capability that lets us run experiments, observe outcomes, and iterate.
>
> Goal:
> Implement the next aggressive MVP step: structured local run history.
>
> Problem:
> The operator can now run experiments, but outputs are still loose
> one-off files. We need a small local record format so repeated
> experiment runs become comparable history.
>
> Preferred shape:
> Add an opt-in flag such as:
>   --append-run-history PATH
>   --run-id ID
> or a similarly simple local-only mechanism.
>
> Requirements:
> - Pure/local/dry-run only.
> - No broker, real account, paper/live trading, network, secrets,
>   scheduler, env vars, database, or money movement.
> - Append-only JSONL local file is preferred over a larger persistence
>   system.
> - If --append-run-history is passed, require --run-id so records are
>   identifiable.
> - Preserve default behavior when flags are absent.
> - Operator-readable errors for missing/invalid parent directory,
>   duplicate/empty run_id if appropriate, malformed write target if
>   applicable.
> - Add focused tests proving: default unchanged; one run appends one
>   JSONL record; two different signals files produce two comparable
>   records; run_id required; bad path → operator error; works with
>   --emit-json, --show-reconciliation, --expected-positions.
> - Minimal governance/status artifacts only.

This packet resolves the directive directly. It is the second packet
under the **MVP trading-system learning loop** milestone (after
DRYRUN-SIGNALS-JSON). It turns one-off `--emit-json` outputs into an
append-only record an operator can grep, diff, and (in the next packet)
rank.

## Authorized Scope

A single implementation PR on branch `feat/dryrun-run-history` (commit
message `feat: --append-run-history structured local history JSONL`) may
touch **only** the following files:

1. `src/gmc_rebuild/dry_run/_run_history.py` — new private module inside
   the already-authorized `gmc_rebuild.dry_run` subpackage. Holds the
   pure deterministic `build_run_history_record(...)` function, the
   `append_run_history_record(path, record)` writer (single-file
   append-text mode), and the `RunHistoryWriteError(OSError)` exception.
2. `src/gmc_rebuild/dry_run/__main__.py` — add the
   `--append-run-history PATH` and `--run-id ID` argparse arguments,
   the source-gating (insider_cluster / signals_json only), the
   `--run-id ↔ --append-run-history` mutual-requirement validation, the
   empty/whitespace `--run-id` rejection (all argparse-level, exit code
   2), and the post-cycle append call. Catches `RunHistoryWriteError`
   from the writer and renders a single-line `error: ...` stderr
   diagnostic + `SystemExit(1)`. Existing behavior with neither flag
   passed is preserved byte-for-byte.
3. `tests/dry_run/test_dry_run_run_history.py` — focused, deterministic
   tripwire suite.
4. `governance/authorizations/2026-06-20_dryrun-run-history.md` — this
   artifact.
5. `monitoring/daily/2026-06-20.md` — append the ADR-008 §D3 Mode B §D4
   self-trigger addendum for this packet.

This packet adds **no** new `src/**` directory and therefore makes
**no** change to the `MASTER_STATUS.md` §8 step-4a `allowed_p2_infra`
allowlist or to `tests/test_package_skeleton.py`.

## Closed Inputs / Outputs

- **Record schema (`schema_version` = 1):**

      {
        "schema_version": 1,
        "run_id": "<non-empty whitespace-free str>",
        "source": "insider_cluster" | "signals_json",
        "report_date": "<DailyReport.report_date>",
        "inputs": {
          "signals_file": "<str>" | null,
          "db": "<str>" | null,
          "expected_positions_file": "<str>" | null,
          "signal_count": <int>,
          "symbols": ["<str>", ...]            // sorted ascending
        },
        "decisions": {
          "total": <int>,
          "would_trade": <int>,
          "would_skip": <int>,
          "by_signal": [
            {
              "intent_id": "<str>", "symbol": "<str>",
              "side": "BUY"|"SELL", "quantity": <int>,
              "outcome": "<PositionDecisionOutcome.value>"
            }, ...
          ]
        },
        "net_positions": [
          {"symbol": "<str>", "quantity": <int>}, ...
        ],
        "reconciliation": {
          "outcome": "MATCH" | "MISMATCH",
          "matches": <int>, "quantity_mismatches": <int>,
          "only_in_simulated": <int>, "only_in_expected": <int>,
          "reconciliation_status": "<str>"
        } | null
      }

  Each line is `json.dumps`'d with `sort_keys=True`, no indent, single
  trailing `\n`. Caller-supplied signal order is preserved in
  `by_signal`; `symbols` is sorted ascending for deterministic
  set-comparison across runs.
- **Write surface:** one local file opened in append-text mode (UTF-8).
  Parent directory must already exist (no directory creation). Target
  path that is itself a directory is rejected. Existing lines are
  never rewritten.
- **CLI gating:**
  - `--append-run-history` is supported only with
    `--source=insider_cluster` or `--source=signals_json`
    (argparse-level, exit 2).
  - `--run-id` is required iff `--append-run-history` is passed
    (argparse-level, exit 2).
  - `--run-id` must be non-empty and whitespace-free (argparse-level,
    exit 2).
- **Caught operator errors:** `RunHistoryWriteError` (parent directory
  missing, target is a directory) → single-line
  `error: cannot append run history: ...` stderr + `SystemExit(1)`.
- **Side effects:** exactly one — the single append-text write of the
  caller-supplied path. No network, no env-var read, no clock read, no
  broker, no real account.

## Required Tests / Invariants

The implementation PR carries a focused, deterministic suite under
`tests/dry_run/test_dry_run_run_history.py` covering: default behavior
unchanged (no flag → no filesystem write); one run appends one record
matching the documented shape exactly; record line is compact and
`sort_keys`-ordered; two runs accrete two records in insertion order; a
**cross-experiment comparison** tripwire (same expected-positions, two
different signals files, one record MATCH + one MISMATCH — the
structural delta a scoring function will rank on);
`--append-run-history` without `--run-id` is exit 2; `--run-id` without
`--append-run-history` is exit 2; empty / whitespace `--run-id` is exit
2; missing parent directory is exit 1 + `error: ...`; target path that
is a directory is exit 1; reconciliation block is `null` when no recon
was requested, populated when `--show-reconciliation` was; `--emit-json`
and `--append-run-history` compose independently in one run; source
gating rejects `--source synthetic`; the flag works over
`--source insider_cluster` and carries the right inputs. The prior
**895-test** baseline is preserved (net additive); post-PR the suite
reports **911 tests passing**.

## Explicitly Not Authorized

- **Any new `src/**` directory.** No new subpackage; no allowlist
  change; no `tests/test_package_skeleton.py` change.
- **Any new value type, decision logic, or reconciliation logic.** The
  record builder is a pure consumer of the merged P6-01..P6-11 surfaces.
- **Any re-export from `src/gmc_rebuild/__init__.py`.**
- **Any persistence beyond the append-text JSONL file.** No SQLite, no
  HDF5, no Parquet, no per-run sidecar directories, no metadata catalog.
- **Any broker / paper / live / real-account / market-data / orders
  path.** The record summarizes the in-memory cycle outcome only.
- **Any I/O beyond the caller-supplied append** and the same
  stdout / stderr the dry-run loop already writes. No directory
  creation, no read of the existing history file (write-only), no
  network, no env-var read, no `audit_event` emission, no scheduler.
- **Any duplicate-`run_id` detection across the file.** Future packets
  may add a separate query/scoring tool that reads the file and flags
  duplicates; this packet only writes.
- **Any future-packet work** — e.g. a scoring/ranking function over
  history records, automated experiment comparison, persistence
  migration, or schema evolution beyond `schema_version` = 1. Successor
  packets remain future / not authorized; each requires its own
  separate written authorization from Kevin per `AI_WORKFLOW.md` §7.

## In-Tree Tag

This packet is recorded under the in-tree tag **`PR DRYRUN-RUN-HISTORY`**.
It adds no new `src/**` directory and therefore does **not** extend the
`MASTER_STATUS.md` §8 step-4a `allowed_p2_infra` allowlist.
