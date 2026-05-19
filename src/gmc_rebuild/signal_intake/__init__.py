"""Typed signal-intake boundary (P6-01).

This subpackage provides the first Phase 6 dry-run engine capability: a
typed boundary that accepts a candidate trade idea as a structured
:class:`SignalIntent` record. It is not strategy code — it does not
decide what to trade, does not generate signals, does not scan markets,
and does not fetch data. It is the upstream type-check before any
later eligibility, decision, or order-intent capability would touch the
record.

Authorization: ``governance/authorizations/2026-05-19_p6-01.md``.

Design constraints — these are governance constraints, not stylistic
preferences:

- **No runtime activation.** The package has no ``__main__`` entry
  point, no daemon, no scheduler, no background thread, no
  long-running service.
- **No external I/O.** No filesystem, no network, no broker SDK, no
  ``time.sleep``, no ``os.environ`` / ``os.getenv`` reads.
- **No real-runtime consumer.** This subpackage is not re-exported by
  :mod:`gmc_rebuild` as part of any runtime API. Its public surface is
  reachable only via ``from gmc_rebuild.signal_intake import ...``.
- **No strategy / scanner / model / portfolio / backtest logic.** The
  boundary accepts an already-structured candidate trade idea supplied
  by a caller; it does not produce one.
- **No order placement / broker integration / market data.** A signal
  intent is upstream of any order. The fields named here carry no
  venue, account, broker, fill, position, execution, market-data, or
  quote information.
- **No persistence.** Nothing on this subpackage writes to disk, opens
  a database, or maintains any cache.
- **Closed dataclass shape.** :class:`SignalIntent` has exactly five
  fields (``intent_id``, ``symbol``, ``side``, ``quantity``,
  ``rationale``). Closed :class:`SignalSide` enumeration with two
  members (``BUY``, ``SELL``). Any expansion of either requires a
  separate written authorization per ``AI_WORKFLOW.md`` §7.
"""

from __future__ import annotations

from gmc_rebuild.signal_intake._intent import (
    SignalIntent,
    SignalSide,
    accept_signal_intent,
)

__all__ = [
    "SignalIntent",
    "SignalSide",
    "accept_signal_intent",
]
