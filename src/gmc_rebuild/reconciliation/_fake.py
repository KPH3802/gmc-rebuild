"""In-memory ``ReconciliationProtocol`` fake (P3-05 test-fixture support).

Pure-Python, deterministic, in-memory fake implementation of
:class:`gmc_rebuild.risk.ReconciliationProtocol` (ADR-003). The sole
intended consumer is the test suite under ``tests/reconciliation/``.

See :mod:`gmc_rebuild.reconciliation` for the full design constraints.
In particular: no I/O, no network, no ``time.sleep``, no
``os.environ`` / ``os.getenv``, no broker SDK, no scheduler / daemon /
background thread, no ``__main__`` entry point, no runtime consumer,
no order placement, no broker activity, no market-data feed, no
persistence.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from gmc_rebuild.risk import (
    ReconciliationReport,
    ReconciliationStatus,
    RiskControlError,
    to_utc_string,
)
from gmc_rebuild.time import ensure_utc


@dataclass(frozen=True, slots=True)
class _PendingOutcome:
    """Outcome the next :meth:`InMemoryReconciliation.reconcile` call will report.

    Test-only record used to drive the in-memory fake deterministically.
    Carries the same shape as :class:`ReconciliationReport` minus the
    ``checked_at`` timestamp, which is supplied at ``reconcile()`` time
    from the fake's in-memory clock.
    """

    status: ReconciliationStatus
    tolerance: float
    observed_delta: float
    details: Mapping[str, Any]


class InMemoryReconciliation:
    """Deterministic in-memory fake conforming to ``ReconciliationProtocol``.

    The fake stores a fixed in-memory ``checked_at`` clock and an
    optional FIFO queue of pending outcomes. It conforms structurally
    to :class:`gmc_rebuild.risk.ReconciliationProtocol`, so
    ``isinstance(fake, ReconciliationProtocol)`` is ``True``.

    A freshly constructed fake reports
    :attr:`ReconciliationStatus.UNAVAILABLE` — no upstream data has
    been provided, so the fake cannot claim ``CLEAN`` and must not
    conflate the no-data case with a confirmed material mismatch
    (``FAILED``). Tests stage outcomes via :meth:`enqueue` (or the
    one-shot :meth:`set_next` helper) and then call :meth:`reconcile`
    to consume them; if no outcome is queued, :meth:`reconcile`
    continues to report ``UNAVAILABLE``. The clock is fixed at
    construction and advances only via the explicit :meth:`advance`
    helper; there is no wall-clock read, no ``time.sleep``, no
    scheduler, no background activity, no broker fetch, no
    market-data fetch, no order / position / fill / execution
    surface.
    """

    __slots__ = ("_checked_at", "_outcomes")

    def __init__(self, checked_at: datetime) -> None:
        self._checked_at: datetime = ensure_utc(checked_at)
        self._outcomes: deque[_PendingOutcome] = deque()

    def advance(self, seconds: float) -> None:
        """Advance the in-memory clock by ``seconds`` (must be non-negative)."""
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
            raise RiskControlError("InMemoryReconciliation.advance seconds must be a number")
        if seconds < 0:
            raise RiskControlError("InMemoryReconciliation.advance seconds must be non-negative")
        self._checked_at = self._checked_at + timedelta(seconds=float(seconds))

    def enqueue(
        self,
        *,
        status: ReconciliationStatus,
        tolerance: float,
        observed_delta: float,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        """Append one outcome the next :meth:`reconcile` call will report.

        Test-only helper. ``status`` must be a
        :class:`ReconciliationStatus`. ``tolerance`` and
        ``observed_delta`` must be non-negative numbers. When ``status``
        is ``CLEAN`` or ``UNAVAILABLE``, ``observed_delta`` must be
        ``0.0`` to match the :class:`ReconciliationReport` invariants.
        ``details`` defaults to an empty mapping and is copied into a
        ``MappingProxyType`` by :class:`ReconciliationReport` at the
        boundary. There is no broker fetch, no market-data fetch, no
        order / position / fill surface; ``details`` keys are
        clearly-synthetic strings supplied by tests.
        """
        if not isinstance(status, ReconciliationStatus):
            raise RiskControlError(
                f"InMemoryReconciliation.enqueue status must be a ReconciliationStatus, "
                f"got {type(status).__name__}"
            )
        if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)):
            raise RiskControlError("InMemoryReconciliation.enqueue tolerance must be a number")
        if tolerance < 0:
            raise RiskControlError(
                "InMemoryReconciliation.enqueue tolerance must be non-negative"
            )
        if isinstance(observed_delta, bool) or not isinstance(observed_delta, (int, float)):
            raise RiskControlError(
                "InMemoryReconciliation.enqueue observed_delta must be a number"
            )
        if observed_delta < 0:
            raise RiskControlError(
                "InMemoryReconciliation.enqueue observed_delta must be non-negative"
            )
        if status in (ReconciliationStatus.CLEAN, ReconciliationStatus.UNAVAILABLE):
            if observed_delta != 0:
                raise RiskControlError(
                    "InMemoryReconciliation.enqueue observed_delta must be 0.0 "
                    "when status is CLEAN or UNAVAILABLE"
                )
        if details is None:
            details = {}
        if not isinstance(details, Mapping):
            raise RiskControlError("InMemoryReconciliation.enqueue details must be a Mapping")
        self._outcomes.append(
            _PendingOutcome(
                status=status,
                tolerance=float(tolerance),
                observed_delta=float(observed_delta),
                details=dict(details),
            )
        )

    def set_next(
        self,
        *,
        status: ReconciliationStatus,
        tolerance: float,
        observed_delta: float,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        """Replace any queued outcomes with exactly one new outcome.

        Convenience helper for the common one-shot test pattern. Clears
        the pending-outcome queue before calling :meth:`enqueue`.
        """
        self._outcomes.clear()
        self.enqueue(
            status=status,
            tolerance=tolerance,
            observed_delta=observed_delta,
            details=details,
        )

    def reconcile(self) -> ReconciliationReport:
        """Return a :class:`ReconciliationReport` for the next staged outcome.

        Conforms to
        :class:`gmc_rebuild.risk.ReconciliationProtocol.reconcile`. When
        no outcome has been staged, returns
        :attr:`ReconciliationStatus.UNAVAILABLE` with
        ``observed_delta=0.0``, ``tolerance=0.0``, and empty
        ``details`` — explicitly distinct from
        :attr:`ReconciliationStatus.FAILED`, which requires a confirmed
        material mismatch supplied by a test via :meth:`enqueue` /
        :meth:`set_next`. Steady-state callers do not see exceptions.
        """
        if not self._outcomes:
            return ReconciliationReport(
                status=ReconciliationStatus.UNAVAILABLE,
                checked_at=to_utc_string(self._checked_at),
                tolerance=0.0,
                observed_delta=0.0,
                details={},
            )
        outcome = self._outcomes.popleft()
        return ReconciliationReport(
            status=outcome.status,
            checked_at=to_utc_string(self._checked_at),
            tolerance=outcome.tolerance,
            observed_delta=outcome.observed_delta,
            details=outcome.details,
        )


__all__ = ["InMemoryReconciliation"]
