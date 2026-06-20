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

Authorizations:
    - ``governance/authorizations/2026-06-18_dry-run-entrypoint.md``
    - ``governance/authorizations/2026-06-18_insider-cluster-intake.md``
    - ``governance/authorizations/2026-06-18_dry-run-emit-json.md``
    - ``governance/authorizations/2026-06-20_p6-11.md``
    - ``governance/authorizations/2026-06-20_p6-12.md``
    - ``governance/authorizations/2026-06-20_dryrun-operator-errors.md``
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

from gmc_rebuild.dry_run._loop import (
    InsiderClusterCycle,
    _run_insider_cluster_cycle,
    build_decisions_json_payload,
    format_dry_run_reconciliation_block,
    format_insider_cluster_summary,
    format_report,
    run_dry_run,
)
from gmc_rebuild.dry_run_reconciliation import (
    ExpectedPositions,
    reconcile_dry_run_positions,
)
from gmc_rebuild.dry_run_reconciliation_view import (
    build_dry_run_reconciliation_json_payload,
)

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
        choices=("synthetic", "insider_cluster"),
        default="synthetic",
        help="signal source for the dry-run loop (default: synthetic)",
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
    return parser


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

    # All reconciliation-aware flags are insider-cluster only — out of scope
    # on synthetic.
    if args.emit_json is not None and args.source != "insider_cluster":
        parser.error("--emit-json is supported only with --source=insider_cluster")
    if args.emit_reconciliation_json is not None and args.source != "insider_cluster":
        parser.error("--emit-reconciliation-json is supported only with --source=insider_cluster")
    if args.show_reconciliation and args.source != "insider_cluster":
        parser.error("--show-reconciliation is supported only with --source=insider_cluster")

    if args.source == "insider_cluster":
        cycle = _run_insider_cluster_cycle_or_operator_error(args.db)
        print(format_insider_cluster_summary(cycle.report, cycle.verdict, cycle.decision))
        recon_result = None
        if args.emit_reconciliation_json is not None or args.show_reconciliation:
            # Pure read-only self-comparison of the simulated portfolio
            # against itself; MATCH by construction. No real account, no
            # broker, no external expected-positions source. Shared across
            # both the JSON and the text surfaces so the two flags render
            # the same underlying result.
            recon_result = reconcile_dry_run_positions(
                simulated=cycle.portfolio,
                expected=ExpectedPositions.from_simulated_portfolio(cycle.portfolio),
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
                    decisions=(cycle.decision,),
                    signals=(cycle.signal,),
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
