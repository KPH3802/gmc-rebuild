"""Run the dry-run loop and print the result to stdout.

Usage::

    python -m gmc_rebuild.dry_run                              # synthetic
    python -m gmc_rebuild.dry_run --source synthetic           # explicit synthetic
    python -m gmc_rebuild.dry_run --source insider_cluster     # real-signal path
    python -m gmc_rebuild.dry_run --source insider_cluster \\
        --db tests/insider_cluster_intake/fixtures/sample.db
    python -m gmc_rebuild.dry_run --source insider_cluster \\
        --emit-json /tmp/decisions.json                        # opt-in JSON sidecar
    python -m gmc_rebuild.dry_run --source insider_cluster \\
        --emit-json -                                          # JSON to stdout
    python -m gmc_rebuild.dry_run --source insider_cluster \\
        --emit-reconciliation-json -                           # recon JSON to stdout
    python -m gmc_rebuild.dry_run --source insider_cluster \\
        --show-reconciliation                                  # recon TEXT to stdout
    python -m gmc_rebuild.dry_run --source signals_json \\
        --signals-file ideas.json --emit-json ideas_run.json   # MVP learning loop

By default the module performs **one** side effect: it writes the
formatted output to stdout via :func:`print`. No network, no env-var
read, no broker, no scheduler. The insider-cluster source path opens
the supplied SQLite DB in **read-only URI mode** and reads exactly one
row.

The ``--emit-json`` flag, when explicitly passed alongside
``--source insider_cluster``, adds **one** further side effect: it
emits the decision payload as JSON. When the argument is a path, the
JSON is written to that single caller-supplied path (the parent
directory must already exist; no directory creation). When the
argument is the single character ``-``, the JSON is written to stdout
instead — no file is created — so the report can be piped to another
process without a temporary file. The flag is rejected on the
synthetic source. No flag = no JSON emission and no file write.

The ``--emit-reconciliation-json`` flag (P6-11) behaves the same way —
path or ``-``, insider-cluster only, rejected on synthetic — but emits a
**reconciliation** payload instead of the decision payload. It runs a
pure, deterministic, read-only self-comparison of the cycle's in-memory
simulated portfolio against
:meth:`ExpectedPositions.from_simulated_portfolio`, projects the P6-09
result through the P6-10
:func:`build_dry_run_reconciliation_json_payload` builder, and emits the
resulting ``dict`` (always ``outcome=MATCH`` by construction). The two
flags are independent: either, both, or neither may be passed.

The ``--show-reconciliation`` flag (P6-12) is the human-readable text
counterpart to ``--emit-reconciliation-json``. It runs the same pure,
deterministic, read-only self-comparison and appends a deterministic
``dry_run_reconciliation:`` text block to stdout after the existing human
summary. Insider-cluster only, rejected on synthetic. Independent of the
two JSON flags; any subset of the three may be passed.

Three operator-data failures on the ``--source insider_cluster`` path —
missing ``--db`` file, unreadable / wrong-schema database, and an empty
``backtest_results`` table — are caught at the CLI boundary and rendered
as single-line ``error: ...`` diagnostics on stderr with exit code 1, so
the operator sees "what failed" instead of a Python traceback. Argparse
usage errors (e.g. ``--emit-json`` on ``--source synthetic``) keep their
existing exit code 2.

The ``--expected-positions PATH`` flag opts the reconciliation surfaces
out of their default self-comparison and into an independent comparison
against a small caller-supplied local JSON file (see
``src/gmc_rebuild/dry_run/_expected_positions.py`` for the schema). When
present, both ``--emit-reconciliation-json`` and ``--show-reconciliation``
render the result of comparing the in-memory simulated portfolio against
the loaded :class:`ExpectedPositions` — so MATCH and MISMATCH outcomes
are now both reachable from the operator path. Missing / malformed
expected-positions files are caught at the CLI boundary and rendered as
``error: ...`` diagnostics on stderr with exit code 1, same as the
insider-cluster DB error path. Without the flag the existing
self-comparison MATCH behavior is preserved byte-for-byte.

The ``--source signals_json --signals-file PATH`` source is the MVP
**learning-loop input**: the operator describes a batch of trading-idea
signals in a small local JSON file, and the dry-run loop threads every
signal through the same merged P6-01..P6-06 pipeline that the synthetic
and insider-cluster paths use. The resulting cycle exposes the multi-
decision summary, the simulated portfolio, the decision JSON payload,
and the reconciliation surfaces — so the operator can compare outcomes
across experiments by changing the input file and re-running. All four
opt-in flags (``--emit-json``, ``--show-reconciliation``,
``--emit-reconciliation-json``, ``--expected-positions``) work over the
``signals_json`` source. Missing / malformed signals files are caught at
the CLI boundary and rendered as ``error: ...`` diagnostics on stderr
with exit code 1.

Authorizations:
    - ``governance/authorizations/2026-06-18_dry-run-entrypoint.md``
    - ``governance/authorizations/2026-06-18_insider-cluster-intake.md``
    - ``governance/authorizations/2026-06-18_dry-run-emit-json.md``
    - ``governance/authorizations/2026-06-20_p6-11.md``
    - ``governance/authorizations/2026-06-20_p6-12.md``
    - ``governance/authorizations/2026-06-20_dryrun-operator-errors.md``
    - ``governance/authorizations/2026-06-20_dryrun-expected-positions.md``
    - ``governance/authorizations/2026-06-20_dryrun-signals-json.md``
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

from gmc_rebuild.decision import PositionDecision
from gmc_rebuild.dry_run._expected_positions import (
    ExpectedPositionsSchemaError,
    load_expected_positions,
)
from gmc_rebuild.dry_run._loop import (
    InsiderClusterCycle,
    SignalsFileCycle,
    _run_insider_cluster_cycle,
    _run_signals_file_cycle,
    build_decisions_json_payload,
    format_dry_run_reconciliation_block,
    format_insider_cluster_summary,
    format_report,
    format_signals_file_summary,
    run_dry_run,
)
from gmc_rebuild.dry_run._signals_file import (
    SignalsFileSchemaError,
    load_signals,
)
from gmc_rebuild.dry_run_reconciliation import (
    ExpectedPositions,
    reconcile_dry_run_positions,
)
from gmc_rebuild.dry_run_reconciliation_view import (
    build_dry_run_reconciliation_json_payload,
)
from gmc_rebuild.signal_intake import SignalIntent

#: Default ``--db`` path for the insider-cluster source. Points at the
#: committed one-row fixture under ``tests/`` so the command is runnable
#: out of the box from a fresh checkout. The operator may override it via
#: ``--db PATH`` (the adapter will copy / open it read-only).
_DEFAULT_INSIDER_DB: Path = (
    Path(__file__).resolve().parents[3]
    / "tests"
    / "insider_cluster_intake"
    / "fixtures"
    / "sample.db"
)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m gmc_rebuild.dry_run",
        description=(
            "Run the dry-run loop and print the daily report to stdout. "
            "Two sources are supported: 'synthetic' (the original three "
            "hardcoded sample signals) and 'insider_cluster' (one real "
            "row read from a backtest_results SQLite database, opened "
            "read-only)."
        ),
    )
    parser.add_argument(
        "--source",
        choices=("synthetic", "insider_cluster", "signals_json"),
        default="synthetic",
        help=(
            "signal source for the dry-run loop (default: synthetic). "
            "'synthetic' runs the original hardcoded sample signals. "
            "'insider_cluster' reads one row from a SQLite backtest_results "
            "database. 'signals_json' reads a batch of operator-supplied "
            "trading-idea signals from a small local JSON file (see "
            "--signals-file) — the learning-loop input that lets the "
            "operator describe and compare experiments."
        ),
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=_DEFAULT_INSIDER_DB,
        help=(
            "Path to an insider-cluster backtest_results SQLite database. "
            "Used only when --source=insider_cluster. Opened in read-only "
            "URI mode; never written. Defaults to the committed one-row "
            "fixture under tests/."
        ),
    )
    parser.add_argument(
        "--signals-file",
        type=Path,
        default=None,
        dest="signals_file",
        metavar="PATH",
        help=(
            "Path to a small local JSON file describing a batch of "
            "operator-supplied trading-idea signals. Required when "
            "--source=signals_json; rejected on other sources. Schema: "
            '{"signals": [{"intent_id": "...", "symbol": "...", "side": '
            '"BUY"|"SELL", "quantity": <int>, "rationale": "..."}, ...]}. '
            "Read once in text mode; no network, no env-var read, no "
            "broker, no real account."
        ),
    )
    parser.add_argument(
        "--emit-json",
        default=None,
        dest="emit_json",
        metavar="PATH",
        help=(
            "Optional. Emit the decision payload as JSON. Supported only "
            "with --source=insider_cluster. Pass a filesystem path to "
            "write the JSON there (the parent directory must already "
            "exist; this command will not create directories), or pass a "
            "single '-' to write the JSON to stdout. No flag = no JSON "
            "emission and no file write."
        ),
    )
    parser.add_argument(
        "--emit-reconciliation-json",
        default=None,
        dest="emit_reconciliation_json",
        metavar="PATH",
        help=(
            "Optional. Emit the dry-run reconciliation payload as JSON. "
            "Supported only with --source=insider_cluster. Runs a pure, "
            "read-only self-comparison of the simulated portfolio (always "
            "MATCH by construction). Pass a filesystem path to write the "
            "JSON there (the parent directory must already exist; this "
            "command will not create directories), or pass a single '-' to "
            "write the JSON to stdout. Independent of --emit-json. No flag = "
            "no reconciliation emission and no file write."
        ),
    )
    parser.add_argument(
        "--show-reconciliation",
        action="store_true",
        dest="show_reconciliation",
        help=(
            "Optional. Append a deterministic human-readable "
            "'dry_run_reconciliation:' text block to stdout after the "
            "existing summary. Supported only with --source=insider_cluster. "
            "Runs the same pure, read-only self-comparison of the simulated "
            "portfolio as --emit-reconciliation-json (always MATCH by "
            "construction). Independent of --emit-json and "
            "--emit-reconciliation-json; any subset of the three flags may be "
            "passed. No flag = no text block appended; existing stdout is "
            "byte-for-byte unchanged."
        ),
    )
    parser.add_argument(
        "--expected-positions",
        default=None,
        type=Path,
        dest="expected_positions",
        metavar="PATH",
        help=(
            "Optional. Path to a small local JSON file describing the "
            "independent expected positions to reconcile against. Schema: "
            '{"positions": [{"symbol": "...", "quantity": <int>}, ...]}. '
            "When passed alongside --emit-reconciliation-json and/or "
            "--show-reconciliation, the reconciliation surfaces compare the "
            "simulated portfolio against this independent input — so both "
            "MATCH and MISMATCH outcomes are reachable. Supported only with "
            "--source=insider_cluster. No flag = the existing "
            "self-comparison MATCH behavior is preserved byte-for-byte. "
            "No network, no broker, no real account."
        ),
    )
    return parser


def _load_signals_or_operator_error(path: Path) -> tuple[SignalIntent, ...]:
    """Load a signals JSON file, surfacing operator-data failures.

    Catches the two expected operator-data failures on the
    ``--signals-file`` path — missing file and malformed file — and
    renders each as a single-line ``error: ...`` diagnostic on stderr
    followed by :class:`SystemExit` with code 1. All other exceptions
    propagate unchanged so genuine bugs still surface a traceback.
    """
    try:
        return load_signals(path)
    except FileNotFoundError:
        print(f"error: signals file not found: {path}", file=sys.stderr)
        raise SystemExit(1) from None
    except SignalsFileSchemaError as exc:
        print(f"error: invalid signals file {path}: {exc}", file=sys.stderr)
        raise SystemExit(1) from None


def _load_expected_positions_or_operator_error(path: Path) -> ExpectedPositions:
    """Load an ``--expected-positions`` JSON file, surfacing operator-data failures.

    Catches the two expected operator-data failures on the
    ``--expected-positions`` path — missing file and malformed file — and
    renders each as a single-line ``error: ...`` diagnostic on stderr
    followed by :class:`SystemExit` with code 1. All other exceptions
    propagate unchanged so genuine bugs still surface a traceback.
    """
    try:
        return load_expected_positions(path)
    except FileNotFoundError:
        print(f"error: expected-positions file not found: {path}", file=sys.stderr)
        raise SystemExit(1) from None
    except ExpectedPositionsSchemaError as exc:
        print(f"error: invalid expected-positions file {path}: {exc}", file=sys.stderr)
        raise SystemExit(1) from None


def _run_insider_cluster_cycle_or_operator_error(db_path: Path) -> InsiderClusterCycle:
    """Run the insider-cluster cycle, surfacing operator-data failures.

    Catches the three expected operator-data failures on the
    insider-cluster path — missing ``--db`` file, unreadable / wrong-schema
    database, and an empty ``backtest_results`` table — and renders each
    as a single-line ``error: ...`` diagnostic on stderr followed by
    :class:`SystemExit` with code 1. All other exceptions propagate
    unchanged so genuine bugs still surface a traceback.
    """
    try:
        return _run_insider_cluster_cycle(db_path)
    except FileNotFoundError:
        print(f"error: insider-cluster DB not found: {db_path}", file=sys.stderr)
        raise SystemExit(1) from None
    except LookupError:
        print(
            f"error: insider-cluster DB has no rows in backtest_results: {db_path}",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
    except sqlite3.DatabaseError:
        print(
            f"error: insider-cluster DB is not a valid backtest_results database: {db_path}",
            file=sys.stderr,
        )
        raise SystemExit(1) from None


def _emit_payload(sink: str, payload: dict[str, Any]) -> None:
    """Render ``payload`` as deterministic JSON and route it to ``sink``.

    ``sink`` is either ``-`` (stdout, after the human summary, no file) or
    a filesystem path (written there; the parent directory must already
    exist — no directory creation). Pretty-printed with ``sort_keys=True``
    so text diffs across runs are stable.
    """
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if sink == "-":
        print(rendered, end="")
    else:
        Path(sink).write_text(rendered, encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    # The synthetic source returns a plain DailyReport (no cycle bundle,
    # no portfolio exposed), so the JSON / recon / expected-positions
    # flags are out of scope there. The insider_cluster and signals_json
    # sources both produce a cycle bundle and admit all four flags.
    _CYCLE_BUNDLE_SOURCES = ("insider_cluster", "signals_json")
    if args.emit_json is not None and args.source not in _CYCLE_BUNDLE_SOURCES:
        parser.error(
            "--emit-json is supported only with --source=insider_cluster or --source=signals_json"
        )
    if args.emit_reconciliation_json is not None and args.source not in _CYCLE_BUNDLE_SOURCES:
        parser.error(
            "--emit-reconciliation-json is supported only with "
            "--source=insider_cluster or --source=signals_json"
        )
    if args.show_reconciliation and args.source not in _CYCLE_BUNDLE_SOURCES:
        parser.error(
            "--show-reconciliation is supported only with "
            "--source=insider_cluster or --source=signals_json"
        )
    if args.expected_positions is not None and args.source not in _CYCLE_BUNDLE_SOURCES:
        parser.error(
            "--expected-positions is supported only with "
            "--source=insider_cluster or --source=signals_json"
        )

    # --signals-file is required with signals_json and only meaningful there.
    if args.source == "signals_json" and args.signals_file is None:
        parser.error("--signals-file is required with --source=signals_json")
    if args.signals_file is not None and args.source != "signals_json":
        parser.error("--signals-file is supported only with --source=signals_json")

    if args.source in ("insider_cluster", "signals_json"):
        # Validate --expected-positions and --signals-file eagerly so a
        # missing / malformed file fails fast with a clean stderr
        # diagnostic before any stdout summary is printed.
        loaded_expected: ExpectedPositions | None = None
        if args.expected_positions is not None:
            loaded_expected = _load_expected_positions_or_operator_error(args.expected_positions)

        cycle: InsiderClusterCycle | SignalsFileCycle
        decisions_tuple: tuple[PositionDecision, ...]
        signals_tuple: tuple[SignalIntent, ...]
        if args.source == "insider_cluster":
            cycle = _run_insider_cluster_cycle_or_operator_error(args.db)
            print(format_insider_cluster_summary(cycle.report, cycle.verdict, cycle.decision))
            decisions_tuple = (cycle.decision,)
            signals_tuple = (cycle.signal,)
        else:
            signals_tuple = _load_signals_or_operator_error(args.signals_file)
            cycle = _run_signals_file_cycle(signals_tuple)
            print(format_signals_file_summary(cycle.report, cycle.verdict, cycle.decisions))
            decisions_tuple = cycle.decisions

        recon_result = None
        if args.emit_reconciliation_json is not None or args.show_reconciliation:
            # Two reconciliation modes:
            #
            # 1. Default (no --expected-positions): pure read-only
            #    self-comparison of the simulated portfolio against itself;
            #    MATCH by construction. Existing behavior preserved.
            # 2. --expected-positions PATH: independent comparison against
            #    the caller-supplied local JSON file already loaded above.
            #    Both MATCH and MISMATCH outcomes are reachable. No broker,
            #    no real account, no network.
            #
            # The shared result drives both the JSON and the text surfaces
            # so the two flags render the same underlying outcome.
            expected = (
                loaded_expected
                if loaded_expected is not None
                else ExpectedPositions.from_simulated_portfolio(cycle.portfolio)
            )
            recon_result = reconcile_dry_run_positions(
                simulated=cycle.portfolio,
                expected=expected,
                reconciliation_status=cycle.report.reconciliation_status,
            )
        if args.show_reconciliation:
            assert recon_result is not None
            print(format_dry_run_reconciliation_block(recon_result))
        if args.emit_json is not None:
            _emit_payload(
                args.emit_json,
                build_decisions_json_payload(
                    report=cycle.report,
                    verdict=cycle.verdict,
                    decisions=decisions_tuple,
                    signals=signals_tuple,
                ),
            )
        if args.emit_reconciliation_json is not None:
            assert recon_result is not None
            _emit_payload(
                args.emit_reconciliation_json,
                build_dry_run_reconciliation_json_payload(recon_result),
            )
    else:
        report = run_dry_run()
        print(format_report(report))


if __name__ == "__main__":
    main()
