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

Authorizations:
    - ``governance/authorizations/2026-06-18_dry-run-entrypoint.md``
    - ``governance/authorizations/2026-06-18_insider-cluster-intake.md``
    - ``governance/authorizations/2026-06-18_dry-run-emit-json.md``
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gmc_rebuild.dry_run._loop import (
    _run_insider_cluster_cycle,
    build_decisions_json_payload,
    format_insider_cluster_summary,
    format_report,
    run_dry_run,
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
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    # Reject --emit-json on synthetic — out of scope for this PR.
    if args.emit_json is not None and args.source != "insider_cluster":
        parser.error("--emit-json is supported only with --source=insider_cluster")

    if args.source == "insider_cluster":
        cycle = _run_insider_cluster_cycle(args.db)
        print(format_insider_cluster_summary(cycle.report, cycle.verdict, cycle.decision))
        if args.emit_json is not None:
            payload = build_decisions_json_payload(
                report=cycle.report,
                verdict=cycle.verdict,
                decisions=(cycle.decision,),
                signals=(cycle.signal,),
            )
            # Pretty-printed + sorted keys = stable text diffs across runs.
            rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
            if args.emit_json == "-":
                # Stdout sink: print after the human summary, no file created.
                print(rendered, end="")
            else:
                Path(args.emit_json).write_text(rendered, encoding="utf-8")
    else:
        report = run_dry_run()
        print(format_report(report))


if __name__ == "__main__":
    main()
