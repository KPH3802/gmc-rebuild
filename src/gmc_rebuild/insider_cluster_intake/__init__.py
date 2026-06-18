"""Insider-cluster signal intake adapter (PR INSIDER-CLUSTER-INTAKE).

Reads ONE row from a committed SQLite fixture (or any caller-supplied
``backtest_results`` database with the same schema) and adapts it into a
valid :class:`~gmc_rebuild.signal_intake.SignalIntent` that the merged
dry-run engine consumes unchanged. The database is opened in SQLite
**read-only URI mode**; the adapter never writes to it. The caller is
responsible for copying the operator's real DB to a temp path before
passing it in — tests do this explicitly via :mod:`tempfile`.

This subpackage adds **no new engine logic**. It is an **intake adapter**
(I/O boundary) on the same side of the engine as
:mod:`gmc_rebuild.signal_intake`, not a strategy/scanner. It does not
generate signals, score candidates, rank alternatives, fetch market
data, talk to a broker, or place orders. The data it reads is the output
of a separate, external research process (the form4_scanner backtest
DB); this adapter only marshals one row of that output into the engine's
typed `SignalIntent` shape.

Authorization: ``governance/authorizations/2026-06-18_insider-cluster-intake.md``.

Design constraints — these are governance constraints, not stylistic
preferences:

- **No engine module modified.** Imports only the existing public
  ``gmc_rebuild.signal_intake.SignalIntent`` / ``SignalSide`` types.
- **Read-only DB access.** ``sqlite3.connect(uri, uri=True)`` with
  ``file:<path>?mode=ro`` guarantees the connection cannot write.
- **No network, no broker, no real account state.** ``sqlite3`` is the
  only I/O surface; no ``socket``, ``urllib``, ``requests``, ``http``,
  ``ssl``, ``smtplib``, ``ftplib``. No env-var read, no secrets, no
  credentials, no API keys.
- **Deterministic.** Identical input rows produce byte-for-byte
  identical ``SignalIntent`` outputs. The share-quantity derivation is
  ``int(TARGET_NOTIONAL_USD / entry_price)`` floored to whole shares
  with a minimum of 1; the ``intent_id`` is a deterministic composition
  of ticker and signal_date; the rationale is a deterministic string.
- **No clock read.** The adapter reads only what the DB row carries.
- **No persistence.** No writes, no caches, no module-level mutable
  state.
- **Not re-exported from package root.** ``gmc_rebuild`` is unchanged
  by this packet; the public surface is reachable only via
  ``from gmc_rebuild.insider_cluster_intake import ...``.
"""

from __future__ import annotations

from gmc_rebuild.insider_cluster_intake._adapter import (
    TARGET_NOTIONAL_USD,
    InsiderClusterRow,
    adapt_to_signal_intent,
    load_insider_cluster_row,
    load_insider_cluster_signal,
)

__all__ = [
    "TARGET_NOTIONAL_USD",
    "InsiderClusterRow",
    "adapt_to_signal_intent",
    "load_insider_cluster_row",
    "load_insider_cluster_signal",
]
