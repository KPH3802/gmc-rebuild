# Authorization — Dry-Run `--source signals_json` MVP Learning-Loop Input (PR DRYRUN-SIGNALS-JSON)

Date: 2026-06-20
Authorizer: Kevin
Scope: Add a new `--source signals_json --signals-file PATH` source to
the dry-run operator entry point. The operator supplies a small local
JSON file describing a batch of trading-idea signals; the dry-run loop
threads each one through the same merged P6-01..P6-06 pipeline that the
synthetic and insider-cluster paths use, producing a multi-decision
cycle whose outputs (stdout summary, decision JSON, reconciliation text
and JSON, expected-positions comparison) flow through the same existing
operator surfaces. This is the MVP **learning-loop input** — the
smallest concrete capability that lets the operator describe an
experiment, run it, observe the outcome, and iterate by changing the
input file.

## Authorization

Kevin's written directive for tonight's work, reproduced verbatim. Per
`AI_WORKFLOW.md` §7 the verbatim block in this file is the authorization
of record for this narrow, tangible-progress packet.

> Continue gmc-rebuild from current main after merged PR #201.
>
> Kevin's working doctrine:
> Solid tested foundation first, then MVP velocity. Do not keep
> polishing dry-run surfaces. We now consider the dry-run
> operator-readiness gate complete enough: what happened, what would
> trade, what reconciles, and what failed all have runnable
> operator-facing surfaces.
>
> Goal:
> Move to the next milestone: the real trading-system learning loop.
>
> First, inspect the current project map/status just enough to choose
> the smallest concrete capability that starts using the dry-run
> operator loop for actual trading-system learning. Do not add another
> display/control flag unless absolutely necessary.
>
> Preference order:
> 1. Add a small end-to-end "operator runbook" or smoke workflow only if
>    it directly enables repeated learning runs.
> 2. Add a bounded signal/idea evaluation input path that feeds the
>    dry-run loop from a simple local fixture.
> 3. Add a minimal strategy/research queue primitive if that is the next
>    clear bridge from dry-run execution to learning.
> 4. Add a small report artifact that captures decision + reconciliation
>    + failure status from one run in a way we can compare across
>    experiments.
>
> Avoid:
> - More dry-run polish.
> - Broad architecture rewrites.
> - Broker/paper/live trading.
> - Network, secrets, scheduler, env vars, persistence beyond a small
>   local file if needed.
> - Excess governance ceremony beyond repo rules.
>
> Implement ONE bounded, runnable MVP step that moves us from "dry-run
> operator loop exists" toward "we can run simple trading ideas, observe
> outcomes, and iterate."

This packet resolves Kevin's preference **#2** (bounded signal/idea
evaluation input from a simple local fixture). Preference #1 (runbook
docs) does not enable iteration; preference #3 (research queue
primitive) is heavier architecture and skips the actual learning input;
preference #4 (report artifact) is already served by the existing
`--emit-json` surface — but without a batch-of-ideas input there is
nothing to *compare* across. This packet provides that input.

## Authorized Scope

A single implementation PR on branch `feat/dryrun-signals-json`
(commit message `feat: add --source signals_json MVP learning-loop
input`) may touch **only** the following files:

1. `src/gmc_rebuild/dry_run/_signals_file.py` — new private module
   inside the already-authorized `gmc_rebuild.dry_run` subpackage. Holds
   the pure deterministic `load_signals(path)` function and the
   `SignalsFileSchemaError(ValueError)` exception. Reuses the merged
   P6-01 `SignalIntent` / `SignalSide` value types by value; constructs
   no new value type and changes no merged surface.
2. `src/gmc_rebuild/dry_run/_loop.py` — add the `SignalsFileCycle`
   dataclass (frozen, slotted, multi-signal sibling of
   `InsiderClusterCycle`), the `_eligibility_config_for_signals(...)`
   helper, the `_run_signals_file_cycle(signals)` function (parallel to
   `_run_insider_cluster_cycle`), the `format_signals_file_summary(...)`
   multi-decision formatter, and the two new `__all__` entries.
3. `src/gmc_rebuild/dry_run/__main__.py` — add the
   `--source signals_json` argparse choice, the `--signals-file PATH`
   argument, the cross-flag gating (the recon / emit-json /
   expected-positions flags now admit either `insider_cluster` *or*
   `signals_json`; `--signals-file` is required iff
   `--source=signals_json`), the eager
   `_load_signals_or_operator_error(path)` wrapper that catches
   `FileNotFoundError` and `SignalsFileSchemaError` and renders each as
   a single-line `error: ...` stderr diagnostic + exit 1, and the
   source dispatch that routes the loaded signals through the new cycle
   builder and the existing JSON / reconciliation surfaces. Existing
   behavior on `--source synthetic` and `--source insider_cluster` is
   preserved byte-for-byte.
4. `tests/dry_run/test_dry_run_signals_json.py` — focused, deterministic
   tripwire suite.
5. `tests/dry_run/fixtures/signals_two_ideas.json` — committed two-idea
   fixture (AAPL long, TSLA short).
6. `tests/dry_run/fixtures/signals_three_ideas.json` — committed
   three-idea fixture (AAPL, MSFT, TSLA) used for cross-experiment
   comparison.
7. `tests/dry_run/fixtures/expected_positions_match_two_ideas.json` —
   committed expected-positions fixture matching the two-ideas cycle.
8. `governance/authorizations/2026-06-20_dryrun-signals-json.md` — this
   artifact.
9. `monitoring/daily/2026-06-20.md` — append the ADR-008 §D3 Mode B §D4
   self-trigger addendum for this packet (same UTC active workday as
   P6-10, P6-11, P6-12, DRYRUN-OPERATOR-ERRORS, and
   DRYRUN-EXPECTED-POSITIONS).

This packet adds **no** new `src/**` directory and therefore makes
**no** change to the `MASTER_STATUS.md` §8 step-4a `allowed_p2_infra`
allowlist or to `tests/test_package_skeleton.py`.

## Closed Inputs / Outputs

- **File schema:**

      {
        "signals": [
          {
            "intent_id": "<str>",
            "symbol": "<str>",
            "side": "BUY" | "SELL",
            "quantity": <positive int>,
            "rationale": "<str>"
          },
          ...
        ]
      }

  Caller-supplied order is preserved through the pipeline so the
  operator can reason about ordering effects on the simulated portfolio.
  Empty `signals` is admitted as a degenerate "no ideas" case.
  Duplicate `intent_id` is rejected. Booleans and floats are rejected as
  `quantity`. All `SignalIntent` invariants (non-empty fields, positive
  quantity, typed side) flow through as operator-readable
  `SignalsFileSchemaError` diagnostics.
- **Pipeline:** the loaded signals tuple is threaded through
  `accept_signal_intent` → `check_eligibility` →
  `compose_position_decision` → `SimulationBoundary.propose_order` →
  `apply_simulated_order_intent`, in caller-supplied order, into a
  running `SimulatedPortfolio`. The eligibility config is permissive —
  `allowed_symbols` is the set of every symbol present in the file —
  because the signals file *is* the operator's experimental input; the
  eligibility gate's job here is type discipline, not external-universe
  validation. A single clear `SafetyVerdict` covers the whole cycle, so
  every signal's decision outcome is driven by eligibility alone.
- **CLI surfaces extended:** `--emit-json`, `--show-reconciliation`,
  `--emit-reconciliation-json`, and `--expected-positions` now admit
  either `--source=insider_cluster` or `--source=signals_json` (any
  source that produces a cycle bundle with a portfolio).
  `--source=synthetic` remains report-only.
- **Caught operator errors:** exactly two — `FileNotFoundError` (missing
  signals file) and `SignalsFileSchemaError` (any parse / schema /
  validation failure). The CLI renders each as a single-line
  `error: ...` stderr diagnostic + `SystemExit(1)`. Eager validation:
  the loader runs **before** the cycle so a bad file produces a clean
  stderr diagnostic and no partial stdout summary.
- **Side effects:** exactly one — the single local file read of the
  caller-supplied path (or, with `--expected-positions`, a second
  read of that path). No network, no env-var read, no clock read, no
  broker, no real account, no persistence beyond the reads.

## Required Tests / Invariants

The implementation PR carries a focused, deterministic suite under
`tests/dry_run/test_dry_run_signals_json.py` covering: documented
multi-decision stdout summary; three-symbol portfolio aggregation
in caller-supplied order; per-signal `--emit-json` payload;
self-comparison `--show-reconciliation` MATCH; independent
`--expected-positions` MATCH and MISMATCH (the latter exercising the
quantity_mismatches + only_in_simulated paths); a
"cross-experiment comparison" tripwire that runs two different signals
files against the same expected-positions and asserts the resulting
reconciliation outcomes differ; seven operator-readable error paths
(missing file, malformed JSON, missing `signals` key, invalid side,
non-integer quantity, duplicate intent_id, empty-rationale invariant
violation); two CLI usage-error paths (`--signals-file` without
`--source=signals_json`; `--source=signals_json` without
`--signals-file`); default-no-flag synthetic stdout unchanged; and
three pure-loader unit tests (typed ordering, empty array, top-level
list rejected). The prior **875-test** baseline is preserved (net
additive); post-PR the suite reports **895 tests passing**.

## Explicitly Not Authorized

- **Any new `src/**` directory.** No new subpackage; no
  `MASTER_STATUS.md` §8 step-4a `allowed_p2_infra` allowlist change; no
  `tests/test_package_skeleton.py` change.
- **Any new engine, reconciliation, or decision logic.** The loader is a
  pure consumer of the merged P6-01 `SignalIntent` / `SignalSide` value
  types and the merged P6-02..P6-06 pipeline. No new value type, no
  change to closed surfaces.
- **Any re-export from `src/gmc_rebuild/__init__.py`.** The new symbols
  live under the already-authorized `gmc_rebuild.dry_run` subpackage.
- **Any broker / paper / live / real-account / market-data / orders
  path.** The signals file is the operator's experimental input;
  decisions and the resulting portfolio are entirely in-memory.
- **Any I/O beyond the caller-supplied file read** and the same
  stdout / stderr the dry-run loop already writes. No directory
  creation, no network, no env-var read, no `audit_event` emission, no
  scheduler, no daemon, no background thread, no clock read.
- **Any future-packet work** — e.g. a research/strategy queue
  primitive, multi-cycle batch comparison, automated experiment
  scoring, persistence of run history, real-account expected-positions,
  or scheduler integration. Successor packets remain future / not
  authorized; each requires its own separate written authorization from
  Kevin per `AI_WORKFLOW.md` §7.

## In-Tree Tag

This packet is recorded under the in-tree tag
**`PR DRYRUN-SIGNALS-JSON`**. It adds no new `src/**` directory and
therefore does **not** extend the `MASTER_STATUS.md` §8 step-4a
`allowed_p2_infra` allowlist.
