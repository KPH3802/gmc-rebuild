"""One-shot generator for the committed insider-cluster sample fixture.

Run from the repo root to (re)create ``sample.db``::

    python tests/insider_cluster_intake/fixtures/build_sample_db.py

The committed ``sample.db`` is the deterministic output of this script. It
contains a single row mirroring a real NKE-style insider-cluster signal (3
insiders, ~$4.45M total, roles ``CEO,Director``, entry price ~$61). The
schema matches the real ``backtest_results`` table in the form4_scanner
project (verified read-only against the operator's local DB on
2026-06-18). No real account, no broker, no credentials, no network.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

_DB_PATH = Path(__file__).resolve().parent / "sample.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS "backtest_results" (
    "ticker" TEXT,
    "company" TEXT,
    "signal_date" TIMESTAMP,
    "entry_date" TIMESTAMP,
    "entry_price" REAL,
    "num_insiders" INTEGER,
    "num_transactions" INTEGER,
    "total_dollars" REAL,
    "avg_price" REAL,
    "roles" TEXT,
    "has_csuite" INTEGER,
    "has_ceo" INTEGER,
    "has_cfo" INTEGER,
    "ret_5d" REAL,
    "spy_5d" REAL,
    "alpha_5d" REAL,
    "ret_10d" REAL,
    "spy_10d" REAL,
    "alpha_10d" REAL,
    "ret_20d" REAL,
    "spy_20d" REAL,
    "alpha_20d" REAL,
    "ret_40d" REAL,
    "spy_40d" REAL,
    "alpha_40d" REAL,
    "ret_60d" REAL,
    "spy_60d" REAL,
    "alpha_60d" REAL,
    "price_vs_cluster" REAL,
    "year" INTEGER
);
"""

# One deterministic NKE row mirroring the real-DB shape (no real returns —
# alpha columns are zeroed so the fixture cannot be confused with a real
# performance report).
_SAMPLE_ROW = (
    "NKE",
    "NIKE, Inc.",
    "2025-12-29 00:00:00",
    "2025-12-30 00:00:00",
    61.19,
    3,
    3,
    4_449_886.94,
    60.85,
    "CEO,Director",
    1,
    1,
    0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    2025,
)


def main() -> None:
    if _DB_PATH.exists():
        _DB_PATH.unlink()
    conn = sqlite3.connect(_DB_PATH)
    try:
        conn.executescript(_SCHEMA)
        conn.execute(
            "INSERT INTO backtest_results VALUES (" + ",".join("?" * len(_SAMPLE_ROW)) + ")",
            _SAMPLE_ROW,
        )
        conn.commit()
    finally:
        conn.close()
    print(f"wrote {_DB_PATH}")


if __name__ == "__main__":
    main()
