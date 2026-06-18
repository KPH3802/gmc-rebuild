"""Run the dry-run loop and print the result to stdout.

Usage::

    python -m gmc_rebuild.dry_run                              # synthetic
    python -m gmc_rebuild.dry_run --source synthetic           # explicit synthetic
    python -m gmc_rebuild.dry_run --source insider_cluster     # real-signal path
    python -m gmc_rebuild.dry_run --source insider_cluster \\
        --db tests/insider_cluster_intake/fixtures/sample.db

The module performs **one** side effect: it writes the formatted output
to stdout via :func:`print`. No network, no file writes, no env-var
read, no broker, no scheduler. The insider-cluster source path opens
the supplied SQLite DB in **read-only URI mode** and reads exactly one
row.

Authorizations:
    - ``governance/authorizations/2026-06-18_dry-run-entrypoint.md``
    - ``governance/authorizations/2026-06-18_insider-cluster-intake.md``
"""

from __future__ import annotations

import argparse
from pathlib import Path

from gmc_rebuild.dry_run._loop import (
    format_insider_cluster_summary,
    format_report,
    run_dry_run,
    run_dry_run_insider_cluster,
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
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_arg_parser().parse_args(argv)
    if args.source == "insider_cluster":
        report, verdict, decision = run_dry_run_insider_cluster(args.db)
        print(format_insider_cluster_summary(report, verdict, decision))
    else:
        report = run_dry_run()
        print(format_report(report))


if __name__ == "__main__":
    main()
