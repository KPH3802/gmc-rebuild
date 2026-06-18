"""Run the dry-run loop and print the daily report to stdout.

Usage:

    python -m gmc_rebuild.dry_run

The module performs **one** side effect: it writes the formatted
:class:`~gmc_rebuild.reporting.DailyReport` rendering to stdout via
:func:`print`. No network, no file writes, no env-var read, no broker,
no scheduler.

Authorization: ``governance/authorizations/2026-06-18_dry-run-entrypoint.md``.
"""

from __future__ import annotations

from gmc_rebuild.dry_run._loop import format_report, run_dry_run


def main() -> None:
    report = run_dry_run()
    print(format_report(report))


if __name__ == "__main__":
    main()
