"""Pure deterministic local run-history record builder and JSONL appender.

Internal module. Builds a compact, JSON-serializable record describing
the outcome of one dry-run cycle and appends it as a single line to a
caller-supplied local JSONL file. Together these form the MVP
structured run-history surface that turns repeated dry-run experiments
into a comparable local record.

Authorization: ``governance/authorizations/2026-06-20_dryrun-run-history.md``.

Record schema (``schema_version`` = 1; every record on the file shares
this shape so cross-experiment diffs and queries are stable)::

    {
      "schema_version": 1,
      "run_id": "<str>",
      "source": "insider_cluster" | "signals_json",
      "report_date": "<str>",
      "inputs": {
        "signals_file": "<str>" | null,
        "db": "<str>" | null,
        "expected_positions_file": "<str>" | null,
        "signal_count": <int>,
        "symbols": ["<str>", ...]            // sorted ascending
      },
      "decisions": {
        "total": <int>,
        "would_trade": <int>,
        "would_skip": <int>,
        "by_signal": [
          {
            "intent_id": "<str>",
            "symbol": "<str>",
            "side": "BUY" | "SELL",
            "quantity": <int>,
            "outcome": "<PositionDecisionOutcome.value>"
          },
          ...                                // caller-supplied signal order preserved
        ]
      },
      "net_positions": [
        {"symbol": "<str>", "quantity": <int>},
        ...                                  // canonical sort from SimulatedPortfolio
      ],
      "reconciliation": {                    // null when no recon was requested
        "outcome": "MATCH" | "MISMATCH",
        "matches": <int>,
        "quantity_mismatches": <int>,
        "only_in_simulated": <int>,
        "only_in_expected": <int>,
        "reconciliation_status": "<str>"
      } | null
    }

Each line in the JSONL file is :func:`json.dumps`'d with
``sort_keys=True`` and no indent, then terminated with a single ``\\n``,
so a deterministic per-record content lets text diffs across experiments
line up cleanly.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from gmc_rebuild.decision import PositionDecision
from gmc_rebuild.dry_run_reconciliation import DryRunReconciliationResult
from gmc_rebuild.portfolio_state import SimulatedPortfolio
from gmc_rebuild.reporting import DailyReport
from gmc_rebuild.signal_intake import SignalIntent

_SCHEMA_VERSION: int = 1
_CYCLE_SOURCES: frozenset[str] = frozenset({"insider_cluster", "signals_json"})


class RunHistoryWriteError(OSError):
    """Raised when the run-history file cannot be appended to for an
    operator-visible reason (parent directory missing, target is a
    directory, etc.). The CLI catches this and renders a single-line
    ``error: ...`` diagnostic.
    """


def build_run_history_record(
    *,
    run_id: str,
    source: str,
    report: DailyReport,
    decisions: Sequence[PositionDecision],
    signals: Sequence[SignalIntent],
    portfolio: SimulatedPortfolio,
    signals_file: Path | None,
    db_path: Path | None,
    expected_positions_file: Path | None,
    reconciliation: DryRunReconciliationResult | None,
) -> dict[str, Any]:
    """Build a deterministic JSON-serializable run-history record.

    Pure function. ``decisions`` and ``signals`` must be the same length
    and aligned (``decisions[i]`` is produced from ``signals[i]``); the
    ``by_signal`` block preserves caller-supplied order so the operator
    can reason about ordering effects. The ``symbols`` list is sorted
    ascending so it is stable across runs that reorder their signals.
    """
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("run_id must be a non-empty string")
    if any(ch.isspace() for ch in run_id):
        raise ValueError("run_id must not contain whitespace")
    if source not in _CYCLE_SOURCES:
        raise ValueError(f"source must be one of {sorted(_CYCLE_SOURCES)}, got {source!r}")
    if not isinstance(report, DailyReport):
        raise TypeError(f"report must be a DailyReport, got {type(report).__name__}")
    if not isinstance(portfolio, SimulatedPortfolio):
        raise TypeError(f"portfolio must be a SimulatedPortfolio, got {type(portfolio).__name__}")
    if len(decisions) != len(signals):
        raise ValueError(
            "decisions and signals must be the same length "
            f"(got decisions={len(decisions)}, signals={len(signals)})"
        )

    by_signal: list[dict[str, Any]] = []
    for decision, signal in zip(decisions, signals, strict=True):
        if not isinstance(decision, PositionDecision):
            raise TypeError(
                f"decisions members must be PositionDecision, got {type(decision).__name__}"
            )
        if not isinstance(signal, SignalIntent):
            raise TypeError(f"signals members must be SignalIntent, got {type(signal).__name__}")
        by_signal.append(
            {
                "intent_id": signal.intent_id,
                "symbol": signal.symbol,
                "side": signal.side.value,
                "quantity": signal.quantity,
                "outcome": decision.outcome.value,
            }
        )

    inputs: dict[str, Any] = {
        "signals_file": str(signals_file) if signals_file is not None else None,
        "db": str(db_path) if db_path is not None else None,
        "expected_positions_file": (
            str(expected_positions_file) if expected_positions_file is not None else None
        ),
        "signal_count": len(signals),
        "symbols": sorted({s.symbol for s in signals}),
    }

    decisions_block: dict[str, Any] = {
        "total": report.decisions_total,
        "would_trade": report.would_trade,
        "would_skip": report.would_skip,
        "by_signal": by_signal,
    }

    net_positions: list[dict[str, Any]] = [
        {"symbol": symbol, "quantity": quantity} for symbol, quantity in report.net_positions
    ]

    reconciliation_block: dict[str, Any] | None
    if reconciliation is None:
        reconciliation_block = None
    else:
        if not isinstance(reconciliation, DryRunReconciliationResult):
            raise TypeError(
                "reconciliation must be a DryRunReconciliationResult or None, "
                f"got {type(reconciliation).__name__}"
            )
        reconciliation_block = {
            "outcome": reconciliation.outcome.value,
            "matches": len(reconciliation.matches),
            "quantity_mismatches": len(reconciliation.quantity_mismatches),
            "only_in_simulated": len(reconciliation.only_in_simulated),
            "only_in_expected": len(reconciliation.only_in_expected),
            "reconciliation_status": reconciliation.reconciliation_status.value,
        }

    return {
        "schema_version": _SCHEMA_VERSION,
        "run_id": run_id,
        "source": source,
        "report_date": report.report_date,
        "inputs": inputs,
        "decisions": decisions_block,
        "net_positions": net_positions,
        "reconciliation": reconciliation_block,
    }


def append_run_history_record(path: Path, record: dict[str, Any]) -> None:
    """Append ``record`` to ``path`` as one JSONL line.

    Pure read-write of one local file. The file is opened in append-text
    mode (UTF-8); the parent directory must already exist (no directory
    creation). The record is :func:`json.dumps`'d with ``sort_keys=True``
    and no indent for stable text diffs, then terminated with a single
    ``\\n``. No network, no env-var read, no clock read, no broker, no
    real account.

    :raises TypeError: if ``path`` is not a :class:`pathlib.Path` or
        ``record`` is not a ``dict``.
    :raises RunHistoryWriteError: if the parent directory does not exist
        or ``path`` is itself a directory.
    """
    if not isinstance(path, Path):
        raise TypeError(f"path must be a Path, got {type(path).__name__}")
    if not isinstance(record, dict):
        raise TypeError(f"record must be a dict, got {type(record).__name__}")

    if path.is_dir():
        raise RunHistoryWriteError(f"run-history target is a directory, not a file: {path}")
    parent = path.parent
    if not parent.exists():
        raise RunHistoryWriteError(f"run-history parent directory does not exist: {parent}")
    if not parent.is_dir():
        raise RunHistoryWriteError(f"run-history parent path is not a directory: {parent}")

    line = json.dumps(record, sort_keys=True) + "\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)


__all__ = [
    "RunHistoryWriteError",
    "append_run_history_record",
    "build_run_history_record",
]
