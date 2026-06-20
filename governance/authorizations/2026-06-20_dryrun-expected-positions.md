# Authorization — Dry-Run `--expected-positions` Local JSON Input (PR DRYRUN-EXPECTED-POSITIONS)

Date: 2026-06-20
Authorizer: Kevin
Scope: Add an opt-in `--expected-positions PATH` CLI flag and a pure,
deterministic loader for a small caller-supplied local JSON file
describing the independent expected positions for the dry-run
reconciliation surfaces. When the flag is passed,
`--emit-reconciliation-json` and `--show-reconciliation` compare the
in-memory simulated portfolio against the loaded
:class:`~gmc_rebuild.dry_run_reconciliation.ExpectedPositions` instead of
the existing `from_simulated_portfolio` self-comparison, so both MATCH
and MISMATCH outcomes are reachable from the operator path. No new
reconciliation logic, no new value type, no new `src/**` directory.

## Authorization

Kevin's written directive for tonight's work, reproduced verbatim. Per
`AI_WORKFLOW.md` §7 the verbatim block in this file is the authorization
of record for this narrow, tangible-progress packet.

> Continue gmc-rebuild from current main after merged PR #200.
>
> Kevin's working doctrine:
> The original system failed because it was built on a weak foundation
> without enough testing, creating endless patches. The rebuild must keep
> a solid tested foundation. But once the foundation is solid, do not
> optimize for perfect code or endless micro-slices. We need MVP
> velocity: build the smallest viable capability, test the seam, accept
> controlled breakage, and push toward a powerful trading system.
>
> Goal:
> Implement the smallest bounded local change that gives reconciliation
> real teeth by allowing the dry-run operator path to compare the
> simulated portfolio against an independent local expected-positions
> input and demonstrate both MATCH and MISMATCH.
>
> Preferred shape:
> Add an opt-in local-only expected positions input, likely something
> like `--expected-positions PATH` where PATH is a small JSON
> fixture/file read locally. Use the existing P6-09 ExpectedPositions
> value type if possible.
>
> Requirements:
> - Pure/local/dry-run only.
> - No broker, real account, paper/live trading, network, secrets,
>   scheduler, env vars, or money movement.
> - Keep default behavior unchanged: without --expected-positions,
>   current self-comparison MATCH behavior remains.
> - With --expected-positions, --emit-reconciliation-json and/or
>   --show-reconciliation should use that independent expected-position
>   input.
> - Support at least: a MATCH fixture, a MISMATCH fixture, an
>   operator-readable error for malformed/missing expected-position file.
> - Add focused tests proving: default behavior unchanged; MATCH works;
>   MISMATCH works; JSON and text surfaces reflect the independent input;
>   malformed/missing input gives clean operator diagnostics.
> - Minimal required governance/status artifacts only.

This packet resolves the directive directly. It closes the "what
reconciles" gap on the dry-run operator-readiness checklist that PR #200
explicitly named as the most material remaining gap (the previous
reconciliation surface only ever produced `outcome=MATCH` because it
self-compared the simulated portfolio against itself).

## Authorized Scope

A single implementation PR on branch `feat/dryrun-expected-positions`
(commit message `feat: add --expected-positions JSON input for dry-run
reconciliation`) may touch **only** the following files:

1. `src/gmc_rebuild/dry_run/_expected_positions.py` — new private module
   inside the already-authorized `gmc_rebuild.dry_run` subpackage. Holds
   the pure deterministic `load_expected_positions(path)` function and
   the `ExpectedPositionsSchemaError(ValueError)` exception. Reuses the
   merged P6-09 `ExpectedPositions` value type by value; constructs no
   new reconciliation value type and changes no merged surface.
2. `src/gmc_rebuild/dry_run/__main__.py` — add the
   `--expected-positions` argparse flag, its synthetic-source rejection
   (argparse-level, exit 2 like the other recon flags), the eager
   `_load_expected_positions_or_operator_error(path)` wrapper that
   catches `FileNotFoundError` and `ExpectedPositionsSchemaError` and
   renders each as a single-line `error: ...` stderr diagnostic + exit
   1, and the routing of the loaded `ExpectedPositions` into the shared
   `reconcile_dry_run_positions` call so both `--emit-reconciliation-json`
   and `--show-reconciliation` reflect the independent input. Existing
   behavior with no `--expected-positions` flag is preserved
   byte-for-byte.
3. `tests/dry_run/test_dry_run_expected_positions.py` — focused,
   deterministic tripwire suite.
4. `tests/dry_run/fixtures/expected_positions_match_nke.json` — committed
   one-symbol MATCH fixture equal to the simulated NKE portfolio.
5. `tests/dry_run/fixtures/expected_positions_mismatch_nke.json` —
   committed two-symbol MISMATCH fixture (NKE quantity differs; AAPL is
   only_in_expected).
6. `governance/authorizations/2026-06-20_dryrun-expected-positions.md` —
   this artifact.
7. `monitoring/daily/2026-06-20.md` — append the ADR-008 §D3 Mode B §D4
   self-trigger addendum for this packet (same UTC active workday as
   P6-10, P6-11, P6-12, and DRYRUN-OPERATOR-ERRORS).

This packet adds **no** new `src/**` directory and therefore makes
**no** change to the `MASTER_STATUS.md` §8 step-4a `allowed_p2_infra`
allowlist or to `tests/test_package_skeleton.py`.

## Closed Inputs / Outputs

- **File schema (mirrors the P6-10 / P6-11 reconciliation JSON output
  shape for symmetry so an operator can take a recon JSON and use it as
  an expected-positions input):**

      {
        "positions": [
          {"symbol": "<str>", "quantity": <int>},
          ...
        ]
      }

  Entries may appear in any order; the loader sorts by symbol ascending
  before constructing the immutable `ExpectedPositions`. Duplicate
  symbols and zero-quantity entries are rejected. Booleans and floats are
  rejected as `quantity` so JSON numbers like `1.0` do not silently
  round.
- **Caught operator errors:** exactly two — `FileNotFoundError` (missing
  path) and `ExpectedPositionsSchemaError` (any parse / schema /
  validation failure). The CLI renders each as a single-line
  `error: ...` stderr diagnostic + `SystemExit(1)`. Eager validation:
  the loader runs **before** the insider-cluster cycle so a bad
  `--expected-positions` file produces a clean stderr diagnostic and no
  partial stdout summary.
- **Side effects:** exactly one — the single local file read of the
  caller-supplied path. No network, no env-var read, no clock read, no
  broker, no real account, no orders, no market data, no persistence
  beyond the read.

## Required Tests / Invariants

The implementation PR carries a focused, deterministic suite under
`tests/dry_run/test_dry_run_expected_positions.py` covering: default
behavior byte-for-byte unchanged with and without `--show-reconciliation`
(self-comparison MATCH preserved); MATCH path through both
`--show-reconciliation` and `--emit-reconciliation-json` with the
committed MATCH fixture; MISMATCH path through both surfaces with the
committed MISMATCH fixture; JSON ↔ text agreement for the same
expected-positions input; six operator-readable error paths (missing
file, malformed JSON, missing `positions` key, duplicate symbol, zero
quantity, float quantity) each verifying exit 1 + empty stdout + no
traceback; eager-validation ordering (expected-positions error fires
before any DB error or stdout summary); synthetic-source argparse
rejection at exit 2; and four pure-loader unit tests (canonical sort,
empty positions array accepted, top-level list rejected, bool quantity
rejected). The prior **856-test** baseline is preserved (net additive);
post-PR the suite reports **875 tests passing**.

## Explicitly Not Authorized

- **Any new `src/**` directory.** This packet adds no new subpackage
  and therefore makes **no** change to the `MASTER_STATUS.md` §8 step-4a
  `allowed_p2_infra` allowlist or to `tests/test_package_skeleton.py`.
- **Any change to the merged P6-09 `ExpectedPositions` value type or the
  P6-09 / P6-10 / P6-11 closed public surfaces.** This packet is a pure
  consumer of those surfaces.
- **Any re-export from `src/gmc_rebuild/__init__.py`.** The new loader
  is a private module under the already-authorized `gmc_rebuild.dry_run`
  subpackage.
- **Any real-account / broker / paper / live expected-positions source.**
  The expected-positions input is exclusively a small local JSON file the
  operator points at; the loader knows nothing about brokers, accounts,
  market data, or external feeds.
- **Any I/O beyond the single caller-supplied file read** and the same
  stdout / stderr the dry-run loop already writes. No directory creation,
  no network, no env-var read, no `audit_event` emission, no scheduler,
  no daemon, no background thread, no clock read.
- **Any future-packet work** — e.g. multi-cycle reconciliation,
  scheduler integration, broker reconciliation, real-account snapshot
  inputs, or expected-positions schema versioning. Successor packets
  remain future / not authorized; each requires its own separate written
  authorization from Kevin per `AI_WORKFLOW.md` §7.

## In-Tree Tag

This packet is recorded under the in-tree tag
**`PR DRYRUN-EXPECTED-POSITIONS`**. It adds no new `src/**` directory
and therefore does **not** extend the `MASTER_STATUS.md` §8 step-4a
`allowed_p2_infra` allowlist.
