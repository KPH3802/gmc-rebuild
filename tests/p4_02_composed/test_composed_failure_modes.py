"""P4-05 composed-failure-modes test.

Pure-Python, in-memory, pytest-only composed-failure-modes coverage extending
the merged P4-02 composed-fixture, P4-03 composed-invariants, and P4-04
composed-edge-cases tests. This module exercises the already-merged
``InMemoryHeartbeat``, ``InMemoryKillSwitch``, and ``InMemoryReconciliation``
fakes together against their abstract Protocol boundaries declared in
``gmc_rebuild.risk``.

Authorization: ``governance/authorizations/2026-05-16_p4-05.md``.

Design constraints — these are governance constraints, not stylistic
preferences:

- **No new ``src/**`` directory or file.** This test lives only as one new
  file in the existing ``tests/p4_02_composed/`` directory.
- **No modification of existing test files.** The merged composed test files
  are preserved unchanged.
- **No new test directories.** The single new test file lives in the existing
  ``tests/p4_02_composed/`` package.
- **No ``conftest.py``.** No shared fixture export is added.
- **No new fakes / helpers under ``src/**``.** The private helpers below are
  test-local only and model a proof assertion, not runtime behaviour.
- **No runtime activation.** No ``__main__``, daemon, scheduler, background
  thread, long-running service, broker integration, market-data feed, order
  placement, secrets, network, or filesystem write.
- **Deterministic.** Uses only fixed timestamps and the in-memory
  ``advance(seconds)`` helpers on the three fakes; no wall-clock read.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from gmc_rebuild.heartbeat import InMemoryHeartbeat
from gmc_rebuild.kill_switch import InMemoryKillSwitch
from gmc_rebuild.reconciliation import InMemoryReconciliation
from gmc_rebuild.risk import HeartbeatStatus, KillSwitchState, ReconciliationStatus

_FIXED_CLOCK = datetime(2026, 5, 16, 14, 0, 0, tzinfo=UTC)


def _make_trio() -> tuple[InMemoryHeartbeat, InMemoryKillSwitch, InMemoryReconciliation]:
    """Construct the three in-memory fakes against a shared fixed clock."""
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    return heartbeat, kill_switch, reconciliation


def _blocking_reasons(
    heartbeat_status: HeartbeatStatus,
    kill_switch_state: KillSwitchState,
    reconciliation_status: ReconciliationStatus,
) -> tuple[str, ...]:
    """Return test-local blocking reasons for a composed safety observation.

    This is deliberately a private test helper, not production logic. It proves
    that every composed failure signal remains visible to a future runtime
    gate: stale heartbeat is blocking, a tripped kill switch is blocking, and
    any reconciliation status other than CLEAN is blocking because unknown
    reconciliation state must not be treated as safe.
    """
    reasons: list[str] = []
    if heartbeat_status is not HeartbeatStatus.FRESH:
        reasons.append(f"heartbeat:{heartbeat_status.value}")
    if kill_switch_state is KillSwitchState.TRIPPED:
        reasons.append("kill_switch:tripped")
    if reconciliation_status is not ReconciliationStatus.CLEAN:
        reasons.append(f"reconciliation:{reconciliation_status.value}")
    return tuple(reasons)


def test_failure_mode_stale_heartbeat_blocks_even_when_other_controls_are_clean() -> None:
    """A stale heartbeat remains a blocking composed signal by itself."""
    heartbeat, kill_switch, reconciliation = _make_trio()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(hours=9))
    reconciliation.set_next(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"composed-failure-mode": "stale-heartbeat-only"},
    )

    reasons = _blocking_reasons(
        heartbeat.status("operator").status,
        kill_switch.current().state,
        reconciliation.reconcile().status,
    )

    assert reasons == ("heartbeat:stale",)


def test_failure_mode_reconciliation_unavailable_blocks_until_clean_report() -> None:
    """UNAVAILABLE reconciliation is blocking and distinct from CLEAN / FAILED."""
    heartbeat, kill_switch, reconciliation = _make_trio()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))

    unavailable_reasons = _blocking_reasons(
        heartbeat.status("operator").status,
        kill_switch.current().state,
        reconciliation.reconcile().status,
    )
    assert unavailable_reasons == ("reconciliation:unavailable",)

    reconciliation.set_next(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"composed-failure-mode": "clean-after-unavailable"},
    )
    clean_reasons = _blocking_reasons(
        heartbeat.status("operator").status,
        kill_switch.current().state,
        reconciliation.reconcile().status,
    )
    assert clean_reasons == ()


def test_failure_mode_failed_reconciliation_then_explicit_trip_exposes_two_blockers() -> None:
    """FAILED reconciliation stays visible before and after an explicit trip."""
    heartbeat, kill_switch, reconciliation = _make_trio()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=42.0,
        details={"composed-failure-mode": "failed-reconciliation"},
    )

    failed_report = reconciliation.reconcile()
    before_trip = _blocking_reasons(
        heartbeat.status("operator").status,
        kill_switch.current().state,
        failed_report.status,
    )
    assert before_trip == ("reconciliation:failed",)

    kill_switch.trip(
        reason="failed reconciliation in composed failure-mode test", triggered_by="operator"
    )
    after_trip = _blocking_reasons(
        heartbeat.status("operator").status,
        kill_switch.current().state,
        failed_report.status,
    )
    assert after_trip == ("kill_switch:tripped", "reconciliation:failed")


def test_failure_mode_multiple_blockers_remain_visible_after_independent_advances() -> None:
    """Independent clocks do not hide simultaneous composed failure signals."""
    heartbeat, kill_switch, reconciliation = _make_trio()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    kill_switch.trip(reason="operator safety stop", triggered_by="operator")
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=99.0,
        details={"composed-failure-mode": "multiple-blockers"},
    )

    heartbeat.advance(9 * 3600.0)
    kill_switch.advance(60.0)
    reconciliation.advance(120.0)

    reasons = _blocking_reasons(
        heartbeat.status("operator").status,
        kill_switch.current().state,
        reconciliation.reconcile().status,
    )

    assert reasons == (
        "heartbeat:stale",
        "kill_switch:tripped",
        "reconciliation:failed",
    )


def test_failure_mode_all_clear_requires_fresh_armed_and_clean_together() -> None:
    """The composed observation is clear only when all three controls are safe."""
    heartbeat, kill_switch, reconciliation = _make_trio()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    reconciliation.set_next(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"composed-failure-mode": "all-clear"},
    )

    reasons = _blocking_reasons(
        heartbeat.status("operator").status,
        kill_switch.current().state,
        reconciliation.reconcile().status,
    )

    assert reasons == ()
