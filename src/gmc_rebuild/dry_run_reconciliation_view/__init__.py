"""Deterministic read-only JSON projection of P6-09 reconciliation results (P6-10).

This subpackage provides the tenth Phase 6 dry-run engine capability: a pure,
deterministic, **read-only** projection of a merged P6-09
:class:`~gmc_rebuild.dry_run_reconciliation.DryRunReconciliationResult` into a
JSON-serializable ``dict``, so the structured reconciliation outcome can be
surfaced through the same operator-facing ``--emit-json`` lane that PR #196
established for dry-run decisions. It adds **no** new reconciliation logic; it
is a pure consumer of the already-merged P6-09 public surface.

Authorization: ``governance/authorizations/2026-06-20_p6-10.md``.

Design constraints — these are governance constraints, not stylistic
preferences:

- **Pure read-only consumer.** Consumes an already-constructed
  :class:`~gmc_rebuild.dry_run_reconciliation.DryRunReconciliationResult` by
  value and modifies nothing. Does **not** re-run
  ``reconcile_dry_run_positions`` and does **not** construct any P6-05 /
  P6-09 input value.
- **Pure / deterministic / no clock read.** Identical inputs return an equal
  payload on every call. The payload carries only data echoed from the input
  result; this module reads no clock and holds no module-level mutable state.
- **JSON-serializable output.** Every leaf is a ``str`` or an ``int``; the
  returned ``dict`` is accepted by ``json.dumps`` with no custom encoder. The
  ADR-003 ``UNAVAILABLE`` vs ``FAILED`` reconciliation-status distinction is
  preserved verbatim.
- **No side effects.** No I/O, no filesystem write, no network, no
  persistence, no broker, no account, no market data, no orders, no secrets,
  no env-var read, no ``audit_event`` emission, no
  :mod:`gmc_rebuild.logging` import. Writing the payload anywhere is the
  caller's decision.
- **No runtime activation.** No ``__main__`` entry point, no daemon, no
  scheduler, no background thread, no ``time.sleep``.
- **No re-export from package root.** :mod:`gmc_rebuild` is unchanged by this
  packet; the public surface is reachable only via
  ``from gmc_rebuild.dry_run_reconciliation_view import ...``.
"""

from __future__ import annotations

from gmc_rebuild.dry_run_reconciliation_view._payload import (
    build_dry_run_reconciliation_json_payload,
)

__all__ = [
    "build_dry_run_reconciliation_json_payload",
]
