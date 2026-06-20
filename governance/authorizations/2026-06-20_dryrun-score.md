# Authorization — Dry-Run Read-Only Score / Leaderboard Command (PR DRYRUN-SCORE)

Date: 2026-06-20
Authorizer: Kevin
Scope: Add a new read-only scoring / ranking command
`python -m gmc_rebuild.dry_run.score --history PATH [--top N]` that
reads an existing JSONL history file produced by the merged
`--append-run-history` packet (schema_version = 1), computes a small
deterministic score per record from the existing reconciliation count
fields, and prints a compact leaderboard sorted best-first. Records
with `reconciliation` = `null` are excluded from ranking. No file is
written, no network, no broker, no scheduler.

## Authorization

Kevin's written directive for tonight's work, reproduced verbatim. Per
`AI_WORKFLOW.md` §7 the verbatim block in this file is the
authorization of record for this narrow, tangible-progress packet.

> Merge current main, then implement the next aggressive MVP
> learning-loop step:
>
> Add a read-only dry-run history scoring/ranking command.
>
> Target shape:
> python -m gmc_rebuild.dry_run.score --history runs/history.jsonl
>     [--top N]
>
> Requirements:
> - Read an existing JSONL history file produced by --append-run-history.
> - Do not write files.
> - Reject missing/unreadable/malformed history with operator-readable
>   stderr errors, not tracebacks.
> - Support schema_version = 1 only for now.
> - Exclude records with reconciliation = null from ranking.
> - Compute a simple deterministic score from existing reconciliation
>   counts:
>     score = matches - quantity_mismatches - only_in_simulated
>             - only_in_expected
> - Print a compact leaderboard sorted best-first with run_id, score,
>   outcome, and count fields.
> - Add focused tests for ranking, null reconciliation exclusion,
>   malformed JSONL, unsupported schema_version, missing file, --top
>   behavior, and stable tie ordering.
> - Keep this bounded: no broker, no market data, no scheduler, no
>   network, no new persistence.

This is the third packet under the **MVP trading-system learning loop**
milestone (after DRYRUN-SIGNALS-JSON and DRYRUN-RUN-HISTORY). The
run-history packet recorded experiments to a JSONL file; this packet
turns that file into a ranked leaderboard so the operator can answer
"which experiment was best?" with one command instead of a `jq` recipe.

## Authorized Scope

A single implementation PR on branch `feat/dryrun-score` (commit
message `feat: read-only dry-run JSONL history scoring command`) may
touch **only** the following files:

1. `src/gmc_rebuild/dry_run/score.py` — new module inside the
   already-authorized `gmc_rebuild.dry_run` subpackage. Runnable as
   `python -m gmc_rebuild.dry_run.score`. Exports the pure deterministic
   `score_record(record)`, `parse_history_text(text)`,
   `rank_records(records)`, `format_leaderboard(...)` helpers, the
   `RankedRecord` frozen value object, the
   `ScoreHistoryError(ValueError)` exception, and the `main(argv=None)`
   CLI entry point. Reads exactly one file (the caller-supplied
   `--history` path) in read-text mode; writes nothing; reads no clock,
   no env-var, no network.
2. `tests/dry_run/test_dry_run_score.py` — focused, deterministic
   tripwire suite.
3. `governance/authorizations/2026-06-20_dryrun-score.md` — this
   artifact.
4. `monitoring/daily/2026-06-20.md` — append the ADR-008 §D3 Mode B
   §D4 self-trigger addendum for this packet.

This packet adds **no** new `src/**` directory and therefore makes
**no** change to the `MASTER_STATUS.md` §8 step-4a `allowed_p2_infra`
allowlist or to `tests/test_package_skeleton.py`.

## Closed Inputs / Outputs

- **Input:** exactly one positional-style required argument
  `--history PATH`. The file must exist, be a regular file (not a
  directory), be valid UTF-8 text, and contain zero or more JSONL
  records each satisfying `schema_version` = 1 with the merged
  run-history record shape. Blank / whitespace-only lines are skipped.
- **Optional:** `--top N` where `N >= 1`. When passed, only the top
  `N` ranked entries are printed; the trailing summary line indicates
  the truncation.
- **Score formula:**
      `score = matches - quantity_mismatches - only_in_simulated - only_in_expected`
  applied to the `reconciliation` block of every record whose
  `reconciliation` is not `null`. Negative scores are legal. Records
  with `reconciliation` = `null` are excluded and counted in the
  summary line.
- **Output:** a multi-line plain-text leaderboard on stdout. One line
  per ranked entry, `rank N. <run_id> score=<int> outcome=<MATCH|MISMATCH>
  matches=<int> quantity_mismatches=<int> only_in_simulated=<int>
  only_in_expected=<int>`, with run_id padded so the `score=` columns
  align across rows. A trailing summary line states how many records
  were ranked and how many were excluded.
- **Caught operator errors:**
  - Missing `--history` file → `error: history file not found: <path>`
    + exit 1.
  - `--history` path is a directory → `error: history path is a
    directory, not a file: <path>` + exit 1.
  - History file is not valid UTF-8 → operator-readable error + exit 1.
  - Any JSONL parse failure, schema-version mismatch, missing key, or
    schema invariant violation → `error: invalid history file <path>:
    <reason citing line number>` + exit 1.
  - Argparse usage errors (`--history` missing, `--top` not a positive
    integer) keep argparse's exit 2.
- **Side effects:** exactly one read of the caller-supplied file, plus
  the leaderboard `print` to stdout. No file write. No network, no
  env-var read, no clock read, no broker.

## Required Tests / Invariants

The implementation PR carries a focused, deterministic suite under
`tests/dry_run/test_dry_run_score.py` covering: ranking with mixed
MATCH/MISMATCH outcomes; null-reconciliation exclusion (mixed and
all-null); empty history file; blank-line skipping in the parser;
stable tie ordering (equal scores → file insertion order); `--top N`
truncation with summary; `--top` rejects 0 / negative / non-integer;
missing history file; history path is a directory; malformed JSONL
cites the line number; unsupported `schema_version` cited explicitly;
missing `reconciliation` key; missing reconciliation count field;
negative reconciliation count rejected; bool reconciliation count
rejected; `--history` required (argparse exit 2); an **end-to-end
tripwire** that drives the real `--append-run-history` packet twice
into a temp JSONL file (one MATCH run + one MISMATCH run) and asserts
the scorer's documented leaderboard; an end-to-end tripwire that
mixes a recon run and a no-recon run to verify the null exclusion
path; plus four pure-helper unit tests (`score_record` formula,
`rank_records` returns correct shape and excluded count, parser
rejects top-level list, `format_leaderboard` empty case). The prior
**911-test** baseline is preserved (net additive); post-PR the suite
reports **937 tests passing**.

## Explicitly Not Authorized

- **Any new `src/**` directory.** No new subpackage; no allowlist
  change; no `tests/test_package_skeleton.py` change.
- **Any write to the history file or any sidecar file.** The scorer
  is read-only. Annotating records, deduplicating, repairing, or
  rewriting any line on the history file is out of scope and forbidden.
- **Any new value type, decision logic, or reconciliation logic.**
  The scorer is a pure consumer of the run-history schema; the formula
  uses only fields already present in `schema_version = 1`.
- **Any re-export from `src/gmc_rebuild/__init__.py`.**
- **Schema evolution beyond `schema_version = 1`.** The scorer
  explicitly rejects any other version with an operator-readable
  error; future schema versions remain future / not authorized and
  require a separate written authorization.
- **Any broker / paper / live / real-account / market-data / orders
  path.** The scorer reads a local JSONL file and prints a leaderboard.
- **Any network, env-var read, clock read, scheduler, persistence
  beyond the read, or `audit_event` emission.**
- **Any configurable scoring formula** (e.g. weight knobs, alternate
  formulas) — the MVP scorer hardcodes the single deterministic
  formula in the directive.
- **Any future-packet work** — e.g. multi-experiment input, automated
  scoring of new dimensions, schema_version = 2, or persistence
  migration. Successor packets remain future / not authorized; each
  requires its own separate written authorization from Kevin per
  `AI_WORKFLOW.md` §7.

## In-Tree Tag

This packet is recorded under the in-tree tag **`PR DRYRUN-SCORE`**.
It adds no new `src/**` directory and therefore does **not** extend
the `MASTER_STATUS.md` §8 step-4a `allowed_p2_infra` allowlist.
