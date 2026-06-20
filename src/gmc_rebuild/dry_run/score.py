"""Read-only scoring / ranking command for the dry-run JSONL run-history log.

Usage::

    python -m gmc_rebuild.dry_run.score --history runs/history.jsonl
    python -m gmc_rebuild.dry_run.score --history runs/history.jsonl --top 5

Reads a JSONL file produced by ``python -m gmc_rebuild.dry_run
--append-run-history ...`` (schema_version = 1), computes a small
deterministic score per record from the existing reconciliation count
fields, and prints a compact leaderboard sorted best-first. Records with
``reconciliation`` = ``null`` are excluded from ranking (they were
recorded without a reconciliation request, so there is nothing to
score) but the count of excluded records is shown.

The score formula is intentionally simple — this is the MVP scorer
that consumes the schema the run-history packet already produces::

    score = matches
          - quantity_mismatches
          - only_in_simulated
          - only_in_expected

This module is **read-only**: it never writes the history file or any
sidecar file. No network, no broker, no scheduler, no env-var read, no
clock read, no persistence. The only side effect is the single file
read and the leaderboard ``print`` to stdout.

Authorization: ``governance/authorizations/2026-06-20_dryrun-score.md``.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_SUPPORTED_SCHEMA_VERSION: int = 1
_RECONCILIATION_COUNT_FIELDS: tuple[str, ...] = (
    "matches",
    "quantity_mismatches",
    "only_in_simulated",
    "only_in_expected",
)


class ScoreHistoryError(ValueError):
    """Raised when the history file is malformed or carries an unsupported
    schema_version. Carries a single operator-readable string message;
    the CLI catches it and renders a single-line ``error: ...`` stderr
    diagnostic.
    """


@dataclass(frozen=True, slots=True)
class RankedRecord:
    """A single ranked entry in the leaderboard.

    Frozen value object holding everything the leaderboard formatter
    needs from one history record. ``file_index`` is the 0-based line
    number of the record in the source file, used as a stable
    tie-breaker so equal-score records sort in insertion order.
    """

    run_id: str
    score: int
    outcome: str
    matches: int
    quantity_mismatches: int
    only_in_simulated: int
    only_in_expected: int
    file_index: int


def score_record(record: dict[str, Any]) -> int:
    """Compute the MVP score for one history record's reconciliation block.

    ``score = matches - quantity_mismatches - only_in_simulated - only_in_expected``.
    Assumes the record has already been schema-validated by
    :func:`parse_history_text`. Returns an ``int`` (negative scores are
    legal).
    """
    recon = record["reconciliation"]
    return (
        int(recon["matches"])
        - int(recon["quantity_mismatches"])
        - int(recon["only_in_simulated"])
        - int(recon["only_in_expected"])
    )


def _validate_record(record: object, line_number: int) -> None:
    """Schema-validate one history record, raising :class:`ScoreHistoryError`
    on any violation. ``line_number`` is the 1-based line number in the
    source file, used in error messages.
    """
    if not isinstance(record, dict):
        raise ScoreHistoryError(
            f"line {line_number} is not a JSON object (got {type(record).__name__})"
        )
    if "schema_version" not in record:
        raise ScoreHistoryError(f"line {line_number} is missing 'schema_version'")
    schema_version = record["schema_version"]
    if schema_version != _SUPPORTED_SCHEMA_VERSION:
        raise ScoreHistoryError(
            f"line {line_number} has unsupported schema_version "
            f"(got {schema_version!r}, this scorer supports "
            f"{_SUPPORTED_SCHEMA_VERSION} only)"
        )
    if "run_id" not in record or not isinstance(record["run_id"], str) or not record["run_id"]:
        raise ScoreHistoryError(f"line {line_number} is missing a non-empty 'run_id' string")
    if "reconciliation" not in record:
        raise ScoreHistoryError(f"line {line_number} is missing 'reconciliation'")
    recon = record["reconciliation"]
    if recon is None:
        return
    if not isinstance(recon, dict):
        raise ScoreHistoryError(
            f"line {line_number}: 'reconciliation' must be null or a JSON object "
            f"(got {type(recon).__name__})"
        )
    if "outcome" not in recon or not isinstance(recon["outcome"], str):
        raise ScoreHistoryError(f"line {line_number}: reconciliation is missing 'outcome' string")
    for field in _RECONCILIATION_COUNT_FIELDS:
        if field not in recon:
            raise ScoreHistoryError(f"line {line_number}: reconciliation is missing '{field}'")
        value = recon[field]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ScoreHistoryError(
                f"line {line_number}: reconciliation.{field} must be an integer "
                f"(got {type(value).__name__})"
            )
        if value < 0:
            raise ScoreHistoryError(
                f"line {line_number}: reconciliation.{field} must be non-negative (got {value})"
            )


def parse_history_text(text: str) -> list[dict[str, Any]]:
    """Parse a JSONL history file's content into a list of validated records.

    Blank / whitespace-only lines are skipped silently (so trailing
    newlines and editor artifacts don't break parsing). Every other line
    must be a valid JSON object satisfying the
    :data:`_SUPPORTED_SCHEMA_VERSION` = 1 schema. Raises
    :class:`ScoreHistoryError` on the first violation, citing the
    1-based line number.
    """
    records: list[dict[str, Any]] = []
    for index, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ScoreHistoryError(
                f"line {index} is not valid JSON: {exc.msg} (column {exc.colno})"
            ) from exc
        _validate_record(parsed, index)
        records.append(parsed)
    return records


def rank_records(records: Sequence[dict[str, Any]]) -> tuple[list[RankedRecord], int]:
    """Project history records onto ranked leaderboard entries.

    Records with ``reconciliation`` = ``null`` are excluded from the
    leaderboard (they were recorded without a reconciliation request, so
    they have no comparable counts). Returns ``(ranked, excluded_count)``
    where ``ranked`` is sorted best-first by score descending. Ties are
    broken by ``file_index`` ascending (stable insertion order) so the
    output is fully deterministic for equal-score records.
    """
    entries: list[RankedRecord] = []
    excluded = 0
    for file_index, record in enumerate(records):
        recon = record["reconciliation"]
        if recon is None:
            excluded += 1
            continue
        entries.append(
            RankedRecord(
                run_id=str(record["run_id"]),
                score=score_record(record),
                outcome=str(recon["outcome"]),
                matches=int(recon["matches"]),
                quantity_mismatches=int(recon["quantity_mismatches"]),
                only_in_simulated=int(recon["only_in_simulated"]),
                only_in_expected=int(recon["only_in_expected"]),
                file_index=file_index,
            )
        )
    entries.sort(key=lambda e: (-e.score, e.file_index))
    return entries, excluded


def format_leaderboard(
    ranked: Sequence[RankedRecord],
    excluded_count: int,
    *,
    top: int | None = None,
) -> str:
    """Render a compact leaderboard string.

    Pure function. One line per ranked entry, ``rank N. <run_id>
    score=<int> outcome=<MATCH|MISMATCH> matches=<int>
    quantity_mismatches=<int> only_in_simulated=<int>
    only_in_expected=<int>``, with run_id padded so the right-hand
    ``score=`` column lines up across rows. A trailing summary line
    states how many records were ranked and how many were excluded.
    """
    visible = list(ranked if top is None else ranked[:top])
    lines: list[str] = []
    if visible:
        # Pad run_id so score= columns align across lines.
        max_run_id_w = max(len(entry.run_id) for entry in visible)
        max_rank_w = len(str(len(visible)))
        for rank, entry in enumerate(visible, start=1):
            lines.append(
                f"rank {rank:>{max_rank_w}}. "
                f"{entry.run_id:<{max_run_id_w}} "
                f"score={entry.score} "
                f"outcome={entry.outcome} "
                f"matches={entry.matches} "
                f"quantity_mismatches={entry.quantity_mismatches} "
                f"only_in_simulated={entry.only_in_simulated} "
                f"only_in_expected={entry.only_in_expected}"
            )
    else:
        if excluded_count > 0:
            lines.append("(no records to rank — all excluded for null reconciliation)")
        else:
            lines.append("(no records to rank — history file is empty)")

    if top is not None and top < len(ranked):
        summary = (
            f"showing top {len(visible)} of {len(ranked)} ranked records, "
            f"excluded {excluded_count} (no reconciliation)"
        )
    else:
        summary = f"ranked {len(ranked)} records, excluded {excluded_count} (no reconciliation)"
    lines.append(summary)
    return "\n".join(lines)


def _read_history_or_operator_error(path: Path) -> str:
    """Read ``path`` as UTF-8 text, surfacing operator-data failures."""
    if not path.exists():
        print(f"error: history file not found: {path}", file=sys.stderr)
        raise SystemExit(1) from None
    if path.is_dir():
        print(f"error: history path is a directory, not a file: {path}", file=sys.stderr)
        raise SystemExit(1) from None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        print(
            f"error: history file is not valid UTF-8 text: {path}: {exc.reason}",
            file=sys.stderr,
        )
        raise SystemExit(1) from None


def _positive_int(value: str) -> int:
    """argparse-friendly positive integer parser for --top."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"must be a positive integer (got {value!r})") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError(f"must be >= 1 (got {parsed})")
    return parsed


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m gmc_rebuild.dry_run.score",
        description=(
            "Read-only scoring / ranking of a dry-run JSONL history file. "
            "Computes a simple deterministic score per record from the "
            "reconciliation count fields (schema_version = 1) and prints "
            "a compact leaderboard sorted best-first. Records with "
            "reconciliation = null are excluded from ranking. No network, "
            "no broker, no writes."
        ),
    )
    parser.add_argument(
        "--history",
        required=True,
        type=Path,
        metavar="PATH",
        help="Path to a JSONL history file produced by --append-run-history.",
    )
    parser.add_argument(
        "--top",
        default=None,
        type=_positive_int,
        metavar="N",
        help=(
            "Optional. Show only the top N entries in the leaderboard. "
            "Must be a positive integer. No flag = show every ranked entry."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    text = _read_history_or_operator_error(args.history)
    try:
        records = parse_history_text(text)
    except ScoreHistoryError as exc:
        print(f"error: invalid history file {args.history}: {exc}", file=sys.stderr)
        raise SystemExit(1) from None

    ranked, excluded = rank_records(records)
    print(format_leaderboard(ranked, excluded, top=args.top))


__all__ = [
    "RankedRecord",
    "ScoreHistoryError",
    "format_leaderboard",
    "main",
    "parse_history_text",
    "rank_records",
    "score_record",
]


if __name__ == "__main__":
    main()
