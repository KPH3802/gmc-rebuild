"""Internal insider-cluster intake adapter module.

See :mod:`gmc_rebuild.insider_cluster_intake` for the package-level
docstring, the authorization reference, and the design constraints.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from gmc_rebuild.signal_intake import SignalIntent, SignalSide

#: USD notional used to derive the integer share quantity for each
#: insider-cluster signal. ``quantity = floor(TARGET_NOTIONAL_USD /
#: entry_price)``, minimum 1.
TARGET_NOTIONAL_USD: int = 10_000


@dataclass(frozen=True, slots=True)
class InsiderClusterRow:
    """Closed projection of one ``backtest_results`` row.

    Carries only the columns the adapter actually uses; the wider table
    (alpha returns, SPY benchmarks, year, etc.) is intentionally ignored
    because the adapter's job is to produce a typed
    :class:`SignalIntent`, not to forward the entire row.
    """

    ticker: str
    entry_price: float
    num_insiders: int
    total_dollars: float
    roles: str
    has_ceo: int
    has_cfo: int
    signal_date: str
    entry_date: str


def _connect_read_only(db_path: Path) -> sqlite3.Connection:
    """Open ``db_path`` in SQLite read-only URI mode.

    Raises :class:`FileNotFoundError` if the path does not exist (SQLite
    URI mode silently *creates* a missing DB, which would mask operator
    errors). Raises :class:`sqlite3.OperationalError` on any subsequent
    write attempt.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"insider-cluster DB not found: {db_path}")
    uri = f"file:{db_path}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def load_insider_cluster_row(db_path: Path, *, ticker: str | None = None) -> InsiderClusterRow:
    """Read ONE row from ``backtest_results`` and return it as a value.

    Read-only. If ``ticker`` is given, returns the earliest matching row
    by ``signal_date``; otherwise returns the row with the earliest
    ``signal_date`` overall (breaking ties by ticker ascending). Raises
    :class:`LookupError` if no row matches.

    :raises TypeError: if ``db_path`` is not a :class:`pathlib.Path` or
        ``ticker`` is not a ``str`` / ``None``.
    :raises FileNotFoundError: if ``db_path`` does not exist.
    :raises LookupError: if the table contains no matching row.
    """
    if not isinstance(db_path, Path):
        raise TypeError(f"db_path must be a Path, got {type(db_path).__name__}")
    if ticker is not None and not isinstance(ticker, str):
        raise TypeError(f"ticker must be a str or None, got {type(ticker).__name__}")

    conn = _connect_read_only(db_path)
    try:
        conn.row_factory = sqlite3.Row
        if ticker is None:
            cursor = conn.execute(
                "SELECT ticker, entry_price, num_insiders, total_dollars, "
                "roles, has_ceo, has_cfo, signal_date, entry_date "
                "FROM backtest_results "
                "ORDER BY signal_date ASC, ticker ASC "
                "LIMIT 1"
            )
        else:
            cursor = conn.execute(
                "SELECT ticker, entry_price, num_insiders, total_dollars, "
                "roles, has_ceo, has_cfo, signal_date, entry_date "
                "FROM backtest_results "
                "WHERE ticker = ? "
                "ORDER BY signal_date ASC "
                "LIMIT 1",
                (ticker,),
            )
        row = cursor.fetchone()
    finally:
        conn.close()

    if row is None:
        raise LookupError(f"no insider-cluster row found in backtest_results (ticker={ticker!r})")
    return InsiderClusterRow(
        ticker=str(row["ticker"]),
        entry_price=float(row["entry_price"]),
        num_insiders=int(row["num_insiders"]),
        total_dollars=float(row["total_dollars"]),
        roles=str(row["roles"]),
        has_ceo=int(row["has_ceo"]),
        has_cfo=int(row["has_cfo"]),
        signal_date=str(row["signal_date"]),
        entry_date=str(row["entry_date"]),
    )


def _compose_rationale(row: InsiderClusterRow) -> str:
    """Build a deterministic human-readable rationale from the row.

    Example: ``"3 insiders; $4.45M cluster; roles: CEO,Director"``.
    """
    dollars_millions = row.total_dollars / 1_000_000.0
    parts = [
        f"{row.num_insiders} insiders",
        f"${dollars_millions:.2f}M cluster",
        f"roles: {row.roles}",
    ]
    return "; ".join(parts)


def _derive_quantity(entry_price: float) -> int:
    """Floor ``TARGET_NOTIONAL_USD / entry_price`` to whole shares.

    Returns a minimum of 1 so the resulting ``SignalIntent.quantity``
    stays strictly positive even for very expensive symbols. Raises
    :class:`ValueError` for non-positive ``entry_price``.
    """
    if not isinstance(entry_price, (int, float)) or isinstance(entry_price, bool):
        raise TypeError(f"entry_price must be a number, got {type(entry_price).__name__}")
    if entry_price <= 0:
        raise ValueError(f"entry_price must be positive, got {entry_price}")
    return max(1, int(TARGET_NOTIONAL_USD / entry_price))


def _intent_id_for(row: InsiderClusterRow) -> str:
    """Deterministic ``intent_id`` of the form
    ``insider-<TICKER>-<DATE>``. ``signal_date`` whitespace is stripped
    so the result is a single token suitable for downstream propagation.
    """
    date_token = row.signal_date.split(" ", 1)[0]
    return f"insider-{row.ticker}-{date_token}"


def adapt_to_signal_intent(row: InsiderClusterRow) -> SignalIntent:
    """Map a value-typed :class:`InsiderClusterRow` to a
    :class:`SignalIntent`.

    Pure / deterministic. No I/O.
    """
    if not isinstance(row, InsiderClusterRow):
        raise TypeError(f"row must be an InsiderClusterRow, got {type(row).__name__}")
    return SignalIntent(
        intent_id=_intent_id_for(row),
        symbol=row.ticker,
        side=SignalSide.BUY,
        quantity=_derive_quantity(row.entry_price),
        rationale=_compose_rationale(row),
    )


def load_insider_cluster_signal(db_path: Path, *, ticker: str | None = None) -> SignalIntent:
    """Convenience: read one row from ``db_path`` and adapt it.

    Equivalent to ``adapt_to_signal_intent(load_insider_cluster_row(db_path,
    ticker=ticker))``.
    """
    return adapt_to_signal_intent(load_insider_cluster_row(db_path, ticker=ticker))


__all__ = [
    "TARGET_NOTIONAL_USD",
    "InsiderClusterRow",
    "adapt_to_signal_intent",
    "load_insider_cluster_row",
    "load_insider_cluster_signal",
]
