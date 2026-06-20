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
- **No network, no broker, no real account, no market data, no
  scheduler, no env-var read, no secrets.** A separately-authorized
  insider-cluster intake path (see
  ``governance/authorizations/2026-06-18_insider-cluster-intake.md``)
  reads ONE row from a caller-supplied SQLite file in read-only URI
  mode. A separately-authorized ``--emit-json <path>`` opt-in (see
  ``governance/authorizations/2026-06-18_dry-run-emit-json.md``) is the
  **only** writable filesystem surface anywhere in the package; it
  fires only when the operator explicitly passes the flag with an
  insider-cluster source, writes JSON to that single caller-supplied
  path, creates no directories, and never touches the engine source
  tree, any trading database, or any governance file. Passing
  ``--emit-json -`` instead streams the same JSON payload to stdout and
  creates no file at all — an in-lane, non-scope-expanding sink that
  adds no new filesystem surface. Printing to stdout happens only in
  :mod:`gmc_rebuild.dry_run.__main__`.
- **Not re-exported from the package root.** ``gmc_rebuild`` is unchanged
  by this packet; the public surface is reachable only via
  ``from gmc_rebuild.dry_run import run_dry_run, format_report,
  run_dry_run_insider_cluster, format_insider_cluster_summary,
  build_decisions_json_payload`` or via
  ``python -m gmc_rebuild.dry_run [--source {synthetic,insider_cluster}]
  [--emit-json PATH]``.
"""

from __future__ import annotations

from gmc_rebuild.dry_run._loop import (
    build_decisions_json_payload,
    format_insider_cluster_summary,
    format_report,
    run_dry_run,
    run_dry_run_insider_cluster,
)

__all__ = [
    "build_decisions_json_payload",
    "format_insider_cluster_summary",
    "format_report",
    "run_dry_run",
    "run_dry_run_insider_cluster",
]
