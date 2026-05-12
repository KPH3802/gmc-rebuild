"""gmc_rebuild.time — minimal UTC-only time utility (P2-03).

This subpackage is authorized by PR P2-03 (see
``governance/authorizations/2026-05-12_p2-03.md`` and
``plan/phase2_entry_plan.md`` §4). It provides the canonical "now UTC"
function, an ISO-8601 formatter that uses the ``Z`` suffix, and a parser
that rejects timezone-naive inputs, consistent with ADR-004 (UTC and
Timezone Discipline).

P2-03 deliberately does **not** introduce:

- broker, account, order, or execution logic,
- strategy, signal, scanner, or model code,
- market-data ingestion,
- persistence, schedulers, daemons, or any ``__main__`` entry point,
- live or paper trading toggles wired to a real venue,
- expansion into P2-04, P2-05, or later Phase 2 items.

See ``MASTER_STATUS.md`` §6, §7, and §8 for the phase-boundary controls
that continue to apply.
"""

from __future__ import annotations

from gmc_rebuild.time.utc import (
    NaiveDatetimeError,
    ensure_utc,
    format_utc,
    now_utc,
    parse_utc,
)

__all__ = [
    "NaiveDatetimeError",
    "ensure_utc",
    "format_utc",
    "now_utc",
    "parse_utc",
]
