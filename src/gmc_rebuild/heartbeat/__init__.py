"""HeartbeatProtocol in-memory test-fixture support (P3-03).

This subpackage provides a pure-Python, deterministic, in-memory fake
implementation of :class:`gmc_rebuild.risk.HeartbeatProtocol` (ADR-005)
for use **exclusively** by the test fixtures under ``tests/heartbeat/``.

Authorization: ``governance/authorizations/2026-05-13_p3-03.md``.

Design constraints — these are governance constraints, not stylistic
preferences:

- **No runtime activation.** The package has no ``__main__`` entry
  point, no daemon, no scheduler, no background thread, no
  long-running service.
- **No external I/O.** No filesystem, no network, no broker SDK, no
  ``time.sleep``, no ``os.environ`` / ``os.getenv`` reads.
- **No real-runtime consumer.** The fake is not imported by any
  ``__main__`` entry point, by any daemon, by any scheduler, by any
  broker integration, by any real-runtime path. It is not re-exported
  by :mod:`gmc_rebuild` as part of any runtime API. Its sole intended
  consumer is the test suite under ``tests/heartbeat/``.
- **P2-05 boundary preserved.** :mod:`gmc_rebuild.risk` continues to
  contain only the abstract :class:`typing.Protocol` definitions and
  supporting frozen dataclasses / enums. This subpackage implements no
  protocol inside :mod:`gmc_rebuild.risk`; the fake lives here.
- **ADR-005 safe defaults.** Unknown components report
  :attr:`gmc_rebuild.risk.HeartbeatStatus.STALE` rather than raising,
  preserving ADR-005's "safe default is paused" property.
- **ADR-004 UTC discipline.** All timestamps are
  ``datetime``-with-``tzinfo=UTC`` at the API boundary; naive
  ``datetime`` values are rejected by the helpers in
  :mod:`gmc_rebuild.time` / :mod:`gmc_rebuild.risk` that this module
  delegates to.
"""

from __future__ import annotations

from gmc_rebuild.heartbeat._fake import InMemoryHeartbeat

__all__ = ["InMemoryHeartbeat"]
