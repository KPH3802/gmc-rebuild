"""Runnable dry-run loop entrypoint (P6-DRYRUN-ENTRYPOINT).

Composes the already-merged P6-01..P6-07 surfaces into one watchable
pipeline:

  signal intake -> eligibility check -> position/risk decision
    -> simulated order intent -> portfolio update -> daily report

This subpackage adds **no new engine component**. It imports only public
symbols from the merged engine modules and threads a small hardcoded
fixture of sample signals through them. The loop is **local-only**
(``SimulationLane.LOCAL_ONLY``), pure, deterministic, in-memory, and
side-effect free aside from a single ``print`` in :mod:`__main__`.

Authorization: ``governance/authorizations/2026-06-18_dry-run-entrypoint.md``.

Design constraints — these are governance constraints, not stylistic
preferences:

- **Compose-only.** No new engine logic. No modification of any merged
  module. Every imported symbol is part of an already-authorized public
  surface (P6-01 / P6-02 / P6-03 / P6-04 / P6-05 / P6-06 / P4-06..P4-08
  / P2-04 / P2-05).
- **Deterministic and side-effect free at the library boundary.** The
  timestamp used to render the daily-report audit event is a fixed
  inline literal (no ``now_utc()`` / ``time.*`` / ``datetime.now()``).
  Two calls to :func:`run_dry_run` return byte-for-byte identical
  reports.
- **No I/O, no network, no broker, no real account, no market data,
  no persistence, no scheduler, no env-var read, no secrets.** The only
  output channel is the in-memory :class:`DailyReport` value object
  plus its plain-text :func:`format_report` rendering. Printing to
  stdout happens only in :mod:`gmc_rebuild.dry_run.__main__`.
- **Not re-exported from the package root.** ``gmc_rebuild`` is unchanged
  by this packet; the public surface is reachable only via
  ``from gmc_rebuild.dry_run import run_dry_run, format_report`` or via
  ``python -m gmc_rebuild.dry_run``.
"""

from __future__ import annotations

from gmc_rebuild.dry_run._loop import format_report, run_dry_run

__all__ = ["format_report", "run_dry_run"]
