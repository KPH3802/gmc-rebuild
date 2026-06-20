"""Pure deterministic loader for the dry-run ``--expected-positions`` JSON file.

Internal module. Reads a small caller-supplied JSON file from local disk
(in read-text mode; no network, no env-var read, no clock read) and
projects it onto the merged P6-09
:class:`~gmc_rebuild.dry_run_reconciliation.ExpectedPositions` value type
so the dry-run reconciliation surfaces can compare the simulated
portfolio against an independent input rather than only the
``from_simulated_portfolio`` self-comparison sanity check.

Authorization: ``governance/authorizations/2026-06-20_dryrun-expected-positions.md``.

Schema (mirrors the P6-10 / P6-11 reconciliation JSON output for
symmetry, so an operator can take a recon JSON and use it as an
expected-positions input)::

    {
      "positions": [
        {"symbol": "<str>", "quantity": <int>},
        ...
      ]
    }

Entries may appear in any order in the file; the loader sorts by symbol
ascending before constructing the immutable
:class:`~gmc_rebuild.dry_run_reconciliation.ExpectedPositions` value.
Duplicate symbols and zero-quantity entries are rejected with operator-
readable error messages. All schema / parse / validation failures raise
:class:`ExpectedPositionsSchemaError`; the only other expected error is
:class:`FileNotFoundError` for a missing path.
"""

from __future__ import annotations

import json
from pathlib import Path

from gmc_rebuild.dry_run_reconciliation import ExpectedPositions


class ExpectedPositionsSchemaError(ValueError):
    """Raised when an expected-positions file is malformed or invalid.

    Covers: not valid JSON, top-level not an object, missing ``positions``
    key, ``positions`` not a list, per-entry not an object, missing /
    wrong-typed ``symbol`` or ``quantity``, duplicate symbol, zero
    quantity. Carries a single operator-readable string message; never
    chains a Python traceback into the operator-facing diagnostic.
    """


def _validate_entry(entry: object, index: int) -> tuple[str, int]:
    if not isinstance(entry, dict):
        raise ExpectedPositionsSchemaError(
            f"positions[{index}] must be a JSON object with 'symbol' and 'quantity' keys"
        )
    if "symbol" not in entry:
        raise ExpectedPositionsSchemaError(f"positions[{index}] is missing 'symbol'")
    if "quantity" not in entry:
        raise ExpectedPositionsSchemaError(f"positions[{index}] is missing 'quantity'")
    symbol = entry["symbol"]
    quantity = entry["quantity"]
    if not isinstance(symbol, str) or not symbol:
        raise ExpectedPositionsSchemaError(f"positions[{index}].symbol must be a non-empty string")
    if any(ch.isspace() for ch in symbol):
        raise ExpectedPositionsSchemaError(f"positions[{index}].symbol must not contain whitespace")
    # Reject bool (which is a subclass of int) and floats so JSON numbers
    # like 1.0 don't silently round to 1.
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise ExpectedPositionsSchemaError(
            f"positions[{index}].quantity must be an integer (got {type(quantity).__name__})"
        )
    if quantity == 0:
        raise ExpectedPositionsSchemaError(
            f"positions[{index}].quantity must be non-zero "
            f"(a flat symbol is represented by absence)"
        )
    return symbol, quantity


def load_expected_positions(path: Path) -> ExpectedPositions:
    """Read ``path`` and return the value-typed
    :class:`~gmc_rebuild.dry_run_reconciliation.ExpectedPositions`.

    Pure / deterministic / read-only. Reads exactly one file in text mode
    with UTF-8 encoding. Sorts entries by symbol ascending before
    constructing the immutable value. The only side effect is the single
    file read; no network, no env-var read, no clock read, no broker, no
    real account.

    :raises FileNotFoundError: if ``path`` does not exist.
    :raises ExpectedPositionsSchemaError: for any parse, schema, or
        validation failure (invalid JSON, missing keys, wrong types,
        duplicate symbols, zero quantity).
    """
    if not isinstance(path, Path):
        raise TypeError(f"path must be a Path, got {type(path).__name__}")
    if not path.exists():
        raise FileNotFoundError(f"expected-positions file not found: {path}")

    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ExpectedPositionsSchemaError(f"file is not valid UTF-8 text: {exc.reason}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ExpectedPositionsSchemaError(
            f"file is not valid JSON: {exc.msg} (line {exc.lineno} column {exc.colno})"
        ) from exc

    if not isinstance(data, dict):
        raise ExpectedPositionsSchemaError(
            "top-level value must be a JSON object with a 'positions' array"
        )
    if "positions" not in data:
        raise ExpectedPositionsSchemaError("missing required 'positions' key")
    raw_positions = data["positions"]
    if not isinstance(raw_positions, list):
        raise ExpectedPositionsSchemaError("'positions' must be a JSON array")

    pairs: list[tuple[str, int]] = []
    seen: set[str] = set()
    for index, entry in enumerate(raw_positions):
        symbol, quantity = _validate_entry(entry, index)
        if symbol in seen:
            raise ExpectedPositionsSchemaError(
                f"positions[{index}].symbol {symbol!r} is a duplicate "
                f"(each symbol must appear at most once)"
            )
        seen.add(symbol)
        pairs.append((symbol, quantity))

    pairs.sort(key=lambda p: p[0])
    return ExpectedPositions(positions=tuple(pairs))


__all__ = [
    "ExpectedPositionsSchemaError",
    "load_expected_positions",
]
