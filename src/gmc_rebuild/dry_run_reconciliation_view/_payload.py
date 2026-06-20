"""P6-10 deterministic read-only dry-run reconciliation JSON projection — internal module.

Defines the pure :func:`build_dry_run_reconciliation_json_payload` builder
authorized by PR P6-10 (see ``governance/authorizations/2026-06-20_p6-10.md``).

This module projects a merged P6-09
:class:`~gmc_rebuild.dry_run_reconciliation.DryRunReconciliationResult` value
object into a deterministic, JSON-serializable ``dict`` so the structured
reconciliation outcome can be surfaced through the same operator-facing
``--emit-json`` lane that PR #196 established for dry-run decisions. It is the
tenth Phase 6 dry-run capability: a pure, read-only consumer of the P6-09
public surface that adds **no** new reconciliation logic.

Design constraints — these are governance constraints, not stylistic
preferences (``governance/authorizations/2026-06-20_p6-10.md``):

- **Pure read-only consumer of the merged P6-09 surface.** The builder
  consumes an already-constructed
  :class:`~gmc_rebuild.dry_run_reconciliation.DryRunReconciliationResult`
  by value and modifies it in no way. It does **not** re-run
  ``reconcile_dry_run_positions``, does **not** construct an
  ``ExpectedPositions`` or a ``SimulatedPortfolio``, and imports only the
  P6-09 public types it needs to type its single input.
- **Pure / deterministic / no clock read.** Identical inputs return an
  equal payload on every call. The payload contains only data echoed from
  the input ``result``; this module never calls ``now_utc()`` / ``time.*``
  / ``datetime.now()`` and holds no module-level mutable state.
- **JSON-serializable, value-typed output.** Every leaf is a ``str`` or an
  ``int`` (the P6-09 quantities are already ``int``; the enum members are
  rendered via their ``.value`` string). The result is a plain ``dict`` of
  plain lists of plain dicts — ``json.dumps`` accepts it with no custom
  encoder.
- **No side effects.** No I/O, no filesystem write, no file handle, no
  network, no persistence, no broker, no account, no market data, no
  orders, no secrets, no env-var read. The builder emits no ``audit_event``
  and does **not** import :mod:`gmc_rebuild.logging`. Serializing the
  returned ``dict`` and writing it anywhere is the caller's decision.
- **No runtime activation.** No ``__main__`` entry point, no daemon, no
  scheduler, no background thread, no ``time.sleep``, no handler
  installation.
- **No re-export from package root.** :mod:`gmc_rebuild` is unchanged by
  this packet; the public surface is reachable only via
  ``from gmc_rebuild.dry_run_reconciliation_view import ...``.
"""

from __future__ import annotations

from typing import Any

from gmc_rebuild.dry_run_reconciliation import DryRunReconciliationResult


def _quantity_pair_records(pairs: tuple[tuple[str, int], ...]) -> list[dict[str, Any]]:
    """Render a canonical ``(symbol, quantity)`` tuple as JSON records.

    Order is preserved verbatim from the input; the P6-09 result already
    canonicalizes each such tuple (sorted by symbol ascending, unique,
    non-zero), so the rendered list is canonical without re-sorting here.
    """
    return [{"symbol": symbol, "quantity": quantity} for symbol, quantity in pairs]


def build_dry_run_reconciliation_json_payload(
    result: DryRunReconciliationResult,
) -> dict[str, Any]:
    """Build the deterministic JSON-serializable reconciliation payload.

    Pure function. Projects a merged P6-09
    :class:`~gmc_rebuild.dry_run_reconciliation.DryRunReconciliationResult`
    into a plain ``dict`` whose every leaf is a ``str`` or an ``int``, so
    the caller can ``json.dumps`` it with no custom encoder and surface it
    through the same operator-facing ``--emit-json`` lane that PR #196
    established for dry-run decisions. Mutates nothing and reads no clock.

    Schema::

        {
          "outcome": "<MATCH|MISMATCH>",
          "reconciliation_status": "<ReconciliationStatus.value>",
          "matches": [{"symbol": "<str>", "quantity": <int>}, ...],
          "quantity_mismatches": [
            {
              "symbol": "<str>",
              "simulated_quantity": <int>,
              "expected_quantity": <int>
            },
            ...
          ],
          "only_in_simulated": [{"symbol": "<str>", "quantity": <int>}, ...],
          "only_in_expected": [{"symbol": "<str>", "quantity": <int>}, ...],
          "summary": {
            "matches": <int>,
            "quantity_mismatches": <int>,
            "only_in_simulated": <int>,
            "only_in_expected": <int>
          }
        }

    The ``outcome`` and ``reconciliation_status`` strings are the enum
    members' ``.value`` strings; the ADR-003 ``UNAVAILABLE`` vs ``FAILED``
    distinction carried by the P6-09 result is preserved verbatim. Every
    list preserves the canonical symbol-ascending order already enforced by
    the P6-09 result; this builder re-sorts nothing.

    :raises TypeError: if ``result`` is not a
        :class:`~gmc_rebuild.dry_run_reconciliation.DryRunReconciliationResult`.
    """
    if not isinstance(result, DryRunReconciliationResult):
        raise TypeError(f"result must be a DryRunReconciliationResult, got {type(result).__name__}")

    quantity_mismatch_records = [
        {
            "symbol": mismatch.symbol,
            "simulated_quantity": mismatch.simulated_quantity,
            "expected_quantity": mismatch.expected_quantity,
        }
        for mismatch in result.quantity_mismatches
    ]

    return {
        "outcome": result.outcome.value,
        "reconciliation_status": result.reconciliation_status.value,
        "matches": _quantity_pair_records(result.matches),
        "quantity_mismatches": quantity_mismatch_records,
        "only_in_simulated": _quantity_pair_records(result.only_in_simulated),
        "only_in_expected": _quantity_pair_records(result.only_in_expected),
        "summary": {
            "matches": len(result.matches),
            "quantity_mismatches": len(result.quantity_mismatches),
            "only_in_simulated": len(result.only_in_simulated),
            "only_in_expected": len(result.only_in_expected),
        },
    }


__all__ = [
    "build_dry_run_reconciliation_json_payload",
]
