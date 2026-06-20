"""Pure deterministic loader for the dry-run ``--signals-file`` JSON input.

Internal module. Reads a small caller-supplied JSON file describing a
batch of trading-idea signals (each one a value-typed
:class:`~gmc_rebuild.signal_intake.SignalIntent`) from local disk, in
read-text mode. The loaded tuple of signals is the operator's
experimental input — multiple ideas threaded through the same dry-run
pipeline in one run so outcomes can be compared across experiments via
the existing ``--emit-json`` / ``--show-reconciliation`` /
``--emit-reconciliation-json`` / ``--expected-positions`` surfaces.

Authorization: ``governance/authorizations/2026-06-20_dryrun-signals-json.md``.

Schema::

    {
      "signals": [
        {
          "intent_id": "<str>",
          "symbol": "<str>",
          "side": "BUY"|"SELL",
          "quantity": <positive int>,
          "rationale": "<str, length >= 5>"
        },
        ...
      ]
    }

The loader preserves caller-supplied order — each signal is threaded
through the pipeline in the order it appears in the file, so the
operator can reason about ordering effects on the simulated portfolio.
An empty ``signals`` list is legal and represents the degenerate "no
ideas" case.

All schema / parse / validation failures raise
:class:`SignalsFileSchemaError`; the only other expected error is
:class:`FileNotFoundError` for a missing path.
"""

from __future__ import annotations

import json
from pathlib import Path

from gmc_rebuild.signal_intake import SignalIntent, SignalSide


class SignalsFileSchemaError(ValueError):
    """Raised when a signals file is malformed or invalid.

    Covers: not valid JSON, top-level not an object, missing ``signals``
    key, ``signals`` not a list, per-entry not an object, missing /
    wrong-typed / out-of-range field, duplicate ``intent_id``. Carries a
    single operator-readable string message; never chains a Python
    traceback into the operator-facing diagnostic.
    """


_REQUIRED_FIELDS: tuple[str, ...] = ("intent_id", "symbol", "side", "quantity", "rationale")


def _validate_entry(entry: object, index: int) -> SignalIntent:
    if not isinstance(entry, dict):
        raise SignalsFileSchemaError(
            f"signals[{index}] must be a JSON object with {', '.join(_REQUIRED_FIELDS)} keys"
        )
    for field in _REQUIRED_FIELDS:
        if field not in entry:
            raise SignalsFileSchemaError(f"signals[{index}] is missing '{field}'")

    raw_side = entry["side"]
    if not isinstance(raw_side, str):
        raise SignalsFileSchemaError(
            f"signals[{index}].side must be 'BUY' or 'SELL' (got {type(raw_side).__name__})"
        )
    try:
        side = SignalSide(raw_side)
    except ValueError as exc:
        raise SignalsFileSchemaError(
            f"signals[{index}].side must be 'BUY' or 'SELL', got {raw_side!r}"
        ) from exc

    raw_quantity = entry["quantity"]
    if isinstance(raw_quantity, bool) or not isinstance(raw_quantity, int):
        raise SignalsFileSchemaError(
            f"signals[{index}].quantity must be a positive integer "
            f"(got {type(raw_quantity).__name__})"
        )

    # SignalIntent.__post_init__ does the rest of the validation
    # (non-empty intent_id/symbol/rationale, no-whitespace, positive
    # quantity, min-rationale-length). Surface its ValueError / TypeError
    # as a SignalsFileSchemaError so the operator sees a single, uniform
    # diagnostic class.
    try:
        return SignalIntent(
            intent_id=entry["intent_id"],
            symbol=entry["symbol"],
            side=side,
            quantity=raw_quantity,
            rationale=entry["rationale"],
        )
    except (TypeError, ValueError) as exc:
        raise SignalsFileSchemaError(f"signals[{index}] is invalid: {exc}") from exc


def load_signals(path: Path) -> tuple[SignalIntent, ...]:
    """Read ``path`` and return a tuple of value-typed
    :class:`~gmc_rebuild.signal_intake.SignalIntent` instances.

    Pure / deterministic / read-only. Reads exactly one file in text mode
    with UTF-8 encoding. Preserves caller-supplied entry order. The only
    side effect is the single file read; no network, no env-var read, no
    clock read, no broker, no real account.

    :raises FileNotFoundError: if ``path`` does not exist.
    :raises SignalsFileSchemaError: for any parse, schema, or validation
        failure (invalid JSON, missing keys, wrong types, duplicate
        intent_id, signal-intent invariant violation).
    """
    if not isinstance(path, Path):
        raise TypeError(f"path must be a Path, got {type(path).__name__}")
    if not path.exists():
        raise FileNotFoundError(f"signals file not found: {path}")

    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SignalsFileSchemaError(f"file is not valid UTF-8 text: {exc.reason}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SignalsFileSchemaError(
            f"file is not valid JSON: {exc.msg} (line {exc.lineno} column {exc.colno})"
        ) from exc

    if not isinstance(data, dict):
        raise SignalsFileSchemaError("top-level value must be a JSON object with a 'signals' array")
    if "signals" not in data:
        raise SignalsFileSchemaError("missing required 'signals' key")
    raw_signals = data["signals"]
    if not isinstance(raw_signals, list):
        raise SignalsFileSchemaError("'signals' must be a JSON array")

    signals: list[SignalIntent] = []
    seen_intent_ids: set[str] = set()
    for index, entry in enumerate(raw_signals):
        signal = _validate_entry(entry, index)
        if signal.intent_id in seen_intent_ids:
            raise SignalsFileSchemaError(
                f"signals[{index}].intent_id {signal.intent_id!r} is a duplicate "
                f"(each intent_id must appear at most once)"
            )
        seen_intent_ids.add(signal.intent_id)
        signals.append(signal)

    return tuple(signals)


__all__ = [
    "SignalsFileSchemaError",
    "load_signals",
]
