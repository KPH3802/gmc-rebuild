# Authorization — Dry-Run Operator-Readable DB Error Handling (PR DRYRUN-OPERATOR-ERRORS)

Date: 2026-06-20
Authorizer: Kevin
Scope: Catch the three expected operator-data failures on the
`python -m gmc_rebuild.dry_run --source insider_cluster --db PATH`
operator path — missing `--db` file, unreadable / wrong-schema database,
and an empty `backtest_results` table — at the CLI boundary, and render
each as a single-line `error: ...` diagnostic on stderr followed by
`SystemExit(1)`. No engine logic change, no new reconciliation logic, no
new `src/**` directory, no new CLI flag. This packet advances the
"what failed" axis of the dry-run operator-readiness milestone Kevin
explicitly named in his directive.

## Authorization

Kevin's written directive for tonight's work, reproduced verbatim. Per
`AI_WORKFLOW.md` §7 the verbatim block in this file is the authorization of
record for this narrow, tangible-progress packet.

> Continue gmc-rebuild from current main after merged PR #199 / P6-12.
>
> Important working correction from Kevin:
> We are not trying to create endless P6-XX micro-slices. We need tangible
> progress toward a concrete launch-readiness milestone. Treat the next
> milestone as: "Dry-run operator readiness," not "the next task number."
>
> Goal:
> Define and implement the smallest concrete change that moves the repo
> toward a complete dry-run operator workflow: one runnable local operator
> path that answers what happened, what would trade, what reconciles, and
> what failed, without broker/live/paper trading.
>
> First, briefly inspect current Phase 6 state and identify the shortest
> remaining gap to dry-run operator readiness. Then implement ONE bounded,
> runnable change that closes the highest-value gap.
>
> Preference order:
> 1. If there is already enough output surface, add a single
>    operator-facing smoke/report command or fixture-backed workflow that
>    demonstrates the full dry-run path end-to-end.
> 2. If failure handling is the biggest missing gap, add deterministic
>    handling/tests for one concrete failure case that an operator would
>    actually hit.
> 3. If reconciliation is still too artificial, add a clearly bounded
>    local expected-position fixture/source for dry-run only, with no
>    broker/account/network/persistence.
> 4. Avoid another tiny display-only flag unless it materially advances
>    the dry-run readiness gate.
>
> Constraints:
> - Pure/local/dry-run only.
> - No broker, paper/live trading, real account, network, secrets,
>   scheduler, env vars, or money movement.
> - Minimal governance/status artifacts only if repo rules require them.
> - Preserve existing no-flag behavior and existing JSON/text flags unless
>   explicitly extending them.
> - Add focused tests.
> - Run targeted tests, ruff, format check, mypy, full pytest, and
>   pre-commit if feasible.
> - Commit, push, and open a PR.

This packet resolves Kevin's preference #2 (failure handling). A survey
of the current dry-run operator surface (PR P6-12 at `1b4788f`) found
that the JSON / text output surfaces are sufficient for the "what
happened / what would trade / what reconciles" axes, but every routine
operator-data failure on the insider-cluster path — typo'd `--db` path,
fresh DB without schema, empty `backtest_results` — currently surfaces
as a 20+-line Python traceback rather than a "what failed" diagnostic.
That is the highest-value gap on the operator-readiness checklist that
fits inside the directive's constraints.

## Authorized Scope

A single implementation PR on branch `feat/dryrun-operator-errors`
(commit message
`feat: operator-readable insider-cluster DB error handling`) may touch
**only** the following files:

1. `src/gmc_rebuild/dry_run/__main__.py` — add the private
   `_run_insider_cluster_cycle_or_operator_error(db_path)` wrapper that
   catches the three expected operator-data exceptions
   (`FileNotFoundError`, `LookupError`, `sqlite3.DatabaseError`),
   prints a single-line `error: ...` diagnostic to stderr, and raises
   `SystemExit(1)`. The existing happy path is unchanged.
2. `tests/dry_run/test_dry_run_operator_errors.py` — the focused,
   deterministic tripwire suite locking in the diagnostic message,
   exit code, empty stdout, and absence of any Python traceback for
   each of the three failure modes, plus the happy-path back-compat
   tripwire and the argparse-usage-error exit-code distinction.
3. `governance/authorizations/2026-06-20_dryrun-operator-errors.md` —
   this artifact.
4. `monitoring/daily/2026-06-20.md` — append the ADR-008 §D3 Mode B §D4
   self-trigger addendum for this packet (same UTC active workday as
   P6-10, P6-11, and P6-12).

This packet adds **no** new `src/**` directory and therefore makes
**no** change to the `MASTER_STATUS.md` §8 step-4a `allowed_p2_infra`
allowlist or to `tests/test_package_skeleton.py`.

## Closed Inputs / Outputs

- **Caught exceptions:** exactly three — `FileNotFoundError` (raised by
  the merged `insider_cluster_intake._connect_read_only` when the
  `--db` path does not exist), `LookupError` (raised by the merged
  `insider_cluster_intake.load_insider_cluster_row` when
  `backtest_results` returns no row), and `sqlite3.DatabaseError`
  (the base class of `OperationalError` and `DatabaseError`, raised by
  stdlib `sqlite3` when the file exists but is not a valid SQLite
  database or has no `backtest_results` table). All other exceptions
  propagate unchanged so genuine bugs still surface a traceback.
- **Diagnostic shape:** one line on stderr, no traceback, no leading
  whitespace, no trailing whitespace beyond the single newline; ends
  with the offending `--db` path so the operator can copy/paste it.
- **Exit code:** `1` for operator-data errors. Distinct from `2`, which
  argparse already uses for usage errors (e.g. `--emit-json` on
  `--source synthetic`).
- **stdout:** empty on any operator-data error. On the happy path,
  stdout is byte-for-byte unchanged from the locked
  `_EXPECTED_NO_FLAG_STDOUT` tripwire that PR #196 / P6-11 / P6-12
  already enforce.

## Required Tests / Invariants

The implementation PR carries a focused, deterministic suite under
`tests/dry_run/test_dry_run_operator_errors.py` covering: missing DB →
documented diagnostic + exit 1 + empty stdout + no traceback;
wrong-schema DB (real SQLite file without `backtest_results`) →
documented diagnostic + exit 1 + no `OperationalError` substring;
non-SQLite garbage file → documented diagnostic + exit 1; empty
`backtest_results` table → documented diagnostic + exit 1 + no
`LookupError` substring; happy path with the committed NKE fixture →
exit 0 + byte-for-byte unchanged stdout; argparse usage error
(`--emit-json` on synthetic) → exit 2 (distinct from operator-data
exit 1). The prior **850-test** baseline is preserved (net additive);
post-PR the suite reports **856 tests passing**.

## Explicitly Not Authorized

- **Any new `src/**` directory.** This packet adds no new subpackage
  and therefore makes **no** change to the `MASTER_STATUS.md` §8 step-4a
  `allowed_p2_infra` allowlist or to `tests/test_package_skeleton.py`.
- **Any new CLI flag** or change to the existing `--source` / `--db` /
  `--emit-json` / `--emit-reconciliation-json` / `--show-reconciliation`
  surfaces.
- **Any new engine or reconciliation logic.** No new comparison logic,
  no new value type, no change to the merged
  `insider_cluster_intake`, `dry_run_reconciliation`, or
  `dry_run_reconciliation_view` closed surfaces. The wrapper is a pure
  consumer of the merged exception contract those modules already document.
- **Any re-export from `src/gmc_rebuild/__init__.py`.**
- **Any I/O beyond the same single stdout / stderr the dry-run loop
  already writes.** No file write, no directory creation, no network,
  no persistence, no secrets, no env-var read, no `audit_event`
  emission, no scheduler, no daemon, no background thread, no clock
  read.
- **Any broker / paper / live trading, real account, market data,
  orders, or money movement.**
- **Any future-packet work.** Subsequent operator-readiness slices
  (additional failure modes, ticker selection, real expected-positions
  fixture, end-to-end smoke command, etc.) remain future / not
  authorized and each requires its own separate written authorization
  from Kevin per `AI_WORKFLOW.md` §7.

## In-Tree Tag

This packet is recorded under the in-tree tag
**`PR DRYRUN-OPERATOR-ERRORS`**. It adds no new `src/**` directory and
therefore does **not** extend the `MASTER_STATUS.md` §8 step-4a
`allowed_p2_infra` allowlist.
