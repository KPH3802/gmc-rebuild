"""ReconciliationProtocol in-memory test-fixture support (P3-05).

This subpackage provides a pure-Python, deterministic, in-memory fake
implementation of :class:`gmc_rebuild.risk.ReconciliationProtocol`
(ADR-003) for use **exclusively** by the test fixtures under
``tests/reconciliation/``.

Authorization: ``governance/authorizations/2026-05-14_p3-05.md``.

Design constraints — these are governance constraints, not stylistic
preferences:

- **No runtime activation.** The package has no ``__main__`` entry
  point, no daemon, no scheduler, no background thread, no
  long-running service.
- **No external I/O.** No filesystem, no network, no broker SDK, no
  ``time.sleep``, no ``os.environ`` / ``os.getenv`` reads, no
  persistence (SQLite, snapshots, file I/O).
- **No real-runtime consumer.** The fake is not imported by any
  ``__main__`` entry point, by any daemon, by any scheduler, by any
  broker integration, by any real-runtime path. It is not re-exported
  by :mod:`gmc_rebuild` as part of any runtime API. Its sole intended
  consumer is the test suite under ``tests/reconciliation/``.
- **P2-05 boundary preserved.** :mod:`gmc_rebuild.risk` continues to
  contain only the abstract :class:`typing.Protocol` definitions and
  supporting frozen dataclasses / enums. This subpackage implements no
  protocol inside :mod:`gmc_rebuild.risk`; the fake lives here.
- **ADR-003 safe defaults.** Construction starts in
  :attr:`gmc_rebuild.risk.ReconciliationStatus.UNAVAILABLE` — no
  upstream data has been provided, so the fake explicitly cannot report
  ``CLEAN`` and must not conflate the no-data case with a confirmed
  material mismatch (``FAILED``). The distinction between
  ``UNAVAILABLE`` (no upstream data) and ``FAILED`` (confirmed material
  mismatch) is preserved end-to-end.
- **ADR-004 UTC discipline.** All timestamps are
  ``datetime``-with-``tzinfo=UTC`` at the API boundary; naive
  ``datetime`` values are rejected by the helpers in
  :mod:`gmc_rebuild.time` / :mod:`gmc_rebuild.risk` that this module
  delegates to.
- **No order / broker / market-data surface.** There is no broker
  account model, no ``account_id`` / ``broker_id`` / ``venue_id`` /
  endpoint URL, no order object, no ``order_id`` / fill / trade
  report / position / execution / ``exec_id`` / order-book reference,
  no real or fake market-data feed, no quotes / bars / symbol
  universe. ``details`` mapping entries used in tests are clearly
  synthetic strings.
"""

from __future__ import annotations

from gmc_rebuild.reconciliation._fake import InMemoryReconciliation

__all__ = ["InMemoryReconciliation"]
