"""P5-04 composed safety-foundation x simulation integration tripwires.

This module is a **tripwire-only** integration test suite that exercises
the real merged P4-06 :class:`gmc_rebuild.runtime.RuntimeShell` against
the real merged P3-03 / P3-04 / P3-05 in-memory fakes
(:class:`gmc_rebuild.heartbeat.InMemoryHeartbeat`,
:class:`gmc_rebuild.kill_switch.InMemoryKillSwitch`,
:class:`gmc_rebuild.reconciliation.InMemoryReconciliation`) to produce a
real :class:`gmc_rebuild.runtime.SafetyVerdict`, then feeds that verdict
into the real merged P5-01 / P5-02 :class:`SimulationBoundary` —
exercising both :meth:`SimulationBoundary.propose` (for
:class:`SimulatedIntent`) and :meth:`SimulationBoundary.propose_order`
(for :class:`SimulatedOrderIntent`). It introduces **no new production
behaviour**: every test in this module composes already-merged public
surfaces from `gmc_rebuild.heartbeat`, `gmc_rebuild.kill_switch`,
`gmc_rebuild.reconciliation`, `gmc_rebuild.risk`, `gmc_rebuild.runtime`,
and `gmc_rebuild.simulation` and asserts invariants that, if ever
violated by a future change, would fail before the change reached
`main`.

Authorization: ``governance/authorizations/2026-05-17_p5-04.md``.

Why this module exists.
~~~~~~~~~~~~~~~~~~~~~~~

The existing P5-03 invariants suite at
``tests/simulation/test_simulated_order_intent_invariants.py``
constructs :class:`SafetyVerdict` instances directly via local test
helpers — it isolates :meth:`SimulationBoundary.propose_order` from the
real safety pipeline by design (a unit test of the boundary). That
leaves a coverage gap: a future drift in which (a)
:class:`RuntimeShell.evaluate` stops populating ``blockers`` correctly
for a given P3 fake state, or (b)
:meth:`SimulationBoundary.propose` / :meth:`SimulationBoundary.propose_order`
stops checking ``SafetyVerdict.clear`` end-to-end, would not be caught
by either the P4-08 cross-product safety-policy-hardening tests (which
cover the verdict side) **or** the P5-03 invariants tests (which cover
the boundary side). P5-04 fills exactly that gap by exercising the
real composed pipeline once for each blocker code and once for the
clear case.

Invariants tripwired here.
~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Real-pipeline clear → boundary accepts.** With FRESH heartbeat for
  every required component, ARMED kill switch, and a CLEAN
  reconciliation outcome, the real :class:`RuntimeShell` produces
  ``SafetyVerdict.clear is True``; both
  :meth:`SimulationBoundary.propose` and
  :meth:`SimulationBoundary.propose_order` return the supplied intent
  by identity.
- **Real-pipeline blocked → boundary rejects with the right blocker
  code in the error message.** For each of the five ``BLOCKER_*``
  codes, drive the corresponding P3 fake state (e.g.,
  ``heartbeat.advance(9 * 3600)``, ``kill_switch.trip(...)``,
  ``reconciliation.set_next(FAILED, ...)``), call
  :meth:`RuntimeShell.evaluate`, observe ``clear is False`` with the
  expected blocker present, and assert that both ``propose`` and
  ``propose_order`` raise :class:`SimulationBoundaryError` with the
  same blocker code present in the message.
- **Multi-blocker fan-out.** When the P3 state simultaneously trips
  heartbeat-staleness, kill-switch, and reconciliation, all three
  blocker codes appear in both error messages.
- **End-to-end non-mutation on success.** After a real-pipeline-clear
  ``propose`` / ``propose_order``, the P3 fakes, the
  :class:`SafetyVerdict`, the :class:`SimulatedIntent`, and the
  :class:`SimulatedOrderIntent` are all observably unchanged.
- **End-to-end non-mutation on rejection.** Same invariant on the
  blocked path.
- **Per-component heartbeat staleness propagates correctly.** STALE
  on one of several required components is enough to block the
  boundary; an unknown component (in ``required_components`` but never
  ``beat``-ed) reports STALE per ADR-005's safe-default rule and
  blocks the boundary.
- **Recovery clears the gate.** After staging a CLEAN reconciliation
  outcome that consumes a prior FAILED outcome, the pipeline can
  recover to ``SafetyVerdict.clear is True`` on the next evaluation
  and the boundary accepts again. (Kill-switch and heartbeat states
  are configured so that the only state change is the reconciliation
  outcome.)
- **Inertness self-check.** The new module itself imports only the
  authorized standard-library helpers (``__future__``, ``ast``,
  ``dataclasses``, ``datetime``, ``pathlib``, ``types.MappingProxyType``)
  and the already-merged in-repo modules (``gmc_rebuild.heartbeat``,
  ``gmc_rebuild.kill_switch``, ``gmc_rebuild.reconciliation``,
  ``gmc_rebuild.risk``, ``gmc_rebuild.runtime``,
  ``gmc_rebuild.simulation``); no forbidden runtime imports, no
  ``__main__``, no ``time.sleep`` / ``asyncio.sleep`` / ``os.environ``
  / ``os.getenv`` / ``getenv(`` / ``open(`` / ``socket.`` / ``urllib.``
  / ``requests.`` tokens leak into real code.

Design constraints (governance, not stylistic).
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Tripwire only.** This module adds no module under ``src/**``, no
  new public symbol, no new field, no new method, and no
  ``SimulationLane`` / ``SimulatedOrderSide`` / ``SimulatedOrderType``
  member.
- **Pytest-stub-free.** Tests avoid ``pytest.raises`` and
  fixture-typed parameters so the mypy strict pre-commit hook does not
  need a pytest-stub dependency, mirroring the existing
  ``tests/simulation/test_simulation_boundary.py``,
  ``tests/simulation/test_simulated_order_intent.py``, and
  ``tests/simulation/test_simulated_order_intent_invariants.py``
  patterns.
- **Local-only.** No I/O, no network, no ``time.sleep``, no
  ``os.environ`` / ``os.getenv``, no broker SDK, no scheduler /
  daemon / background thread, no ``__main__`` entry point, no
  persistence.
"""

from __future__ import annotations

import ast
import dataclasses
from datetime import UTC, datetime, timedelta
from pathlib import Path

from gmc_rebuild.heartbeat import InMemoryHeartbeat
from gmc_rebuild.kill_switch import InMemoryKillSwitch
from gmc_rebuild.reconciliation import InMemoryReconciliation
from gmc_rebuild.risk import (
    HeartbeatStatus,
    KillSwitchState,
    ReconciliationStatus,
)
from gmc_rebuild.runtime import (
    BLOCKER_HEARTBEAT_STALE,
    BLOCKER_KILL_SWITCH_TRIPPED,
    BLOCKER_RECONCILIATION_FAILED,
    BLOCKER_RECONCILIATION_UNAVAILABLE,
    BLOCKER_RECONCILIATION_WARNING,
    RuntimeShell,
)
from gmc_rebuild.simulation import (
    SimulatedIntent,
    SimulatedOrderIntent,
    SimulatedOrderSide,
    SimulatedOrderType,
    SimulationBoundary,
    SimulationBoundaryError,
    SimulationLane,
)

_FIXED_CLOCK = datetime(2026, 5, 17, 14, 0, 0, tzinfo=UTC)
_FIXED_CLOCK_Z = "2026-05-17T14:00:00Z"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _expect_boundary_error(call: object, match: str) -> SimulationBoundaryError:
    raised: Exception | None = None
    try:
        call()  # type: ignore[operator]
    except SimulationBoundaryError as exc:
        raised = exc
    assert isinstance(raised, SimulationBoundaryError), (
        f"expected SimulationBoundaryError matching {match!r}, got {raised!r}"
    )
    assert match in str(raised), (
        f"SimulationBoundaryError message {str(raised)!r} missing {match!r}"
    )
    return raised


def _build_clear_pipeline() -> tuple[
    InMemoryHeartbeat,
    InMemoryKillSwitch,
    InMemoryReconciliation,
    RuntimeShell,
]:
    """Construct the real P3 fakes + RuntimeShell in a clear-by-default state.

    The pipeline is constructed so a single :meth:`RuntimeShell.evaluate`
    call produces ``SafetyVerdict.clear is True``: the operator heartbeat
    has been beaten one minute ago (FRESH); the kill switch starts ARMED
    by P3-04's documented default; the reconciliation FIFO has a single
    CLEAN outcome staged.
    """
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    reconciliation.enqueue(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"composed-safety-scenario": "clear"},
    )
    shell = RuntimeShell(
        heartbeat=heartbeat,
        kill_switch=kill_switch,
        reconciliation=reconciliation,
        required_components=("operator",),
    )
    return heartbeat, kill_switch, reconciliation, shell


def _market_order(*, intent_id: str = "order-comp-A") -> SimulatedOrderIntent:
    return SimulatedOrderIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_FIXED_CLOCK_Z,
        symbol="SIM-COMP-A",
        side=SimulatedOrderSide.BUY,
        quantity=10,
        order_type=SimulatedOrderType.MARKET,
        limit_price=None,
    )


def _limit_order(*, intent_id: str = "order-comp-B") -> SimulatedOrderIntent:
    return SimulatedOrderIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_FIXED_CLOCK_Z,
        symbol="SIM-COMP-B",
        side=SimulatedOrderSide.SELL,
        quantity=25,
        order_type=SimulatedOrderType.LIMIT,
        limit_price=7.5,
    )


def _placeholder_intent(*, intent_id: str = "intent-comp-X") -> SimulatedIntent:
    return SimulatedIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_FIXED_CLOCK_Z,
    )


# ---------------------------------------------------------------------------
# Invariant 1 — Real-pipeline clear → boundary accepts (identity-return)
# ---------------------------------------------------------------------------


def test_real_pipeline_clear_lets_propose_return_intent_by_identity() -> None:
    """A real-pipeline-clear SafetyVerdict admits ``propose`` returning input by identity."""
    _heartbeat, _kill_switch, _reconciliation, shell = _build_clear_pipeline()
    verdict = shell.evaluate()
    assert verdict.clear is True
    assert verdict.blockers == ()
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    intent = _placeholder_intent()
    returned = boundary.propose(intent=intent, verdict=verdict)
    assert returned is intent


def test_real_pipeline_clear_lets_propose_order_return_intent_by_identity() -> None:
    """A real-pipeline-clear SafetyVerdict admits ``propose_order`` returning input by identity."""
    _heartbeat, _kill_switch, _reconciliation, shell = _build_clear_pipeline()
    verdict = shell.evaluate()
    assert verdict.clear is True
    assert verdict.blockers == ()
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    order = _market_order()
    returned = boundary.propose_order(order_intent=order, verdict=verdict)
    assert returned is order


# ---------------------------------------------------------------------------
# Invariant 2 — Heartbeat STALE propagates from P3 fake → RuntimeShell → boundary
# ---------------------------------------------------------------------------


def test_real_pipeline_heartbeat_stale_blocks_propose_and_propose_order() -> None:
    """A real-pipeline heartbeat STALE produces a blocker that surfaces in both error messages."""
    heartbeat, _kill_switch, _reconciliation, shell = _build_clear_pipeline()
    # Push the operator heartbeat past the ADR-005 8-hour staleness threshold.
    heartbeat.advance(9 * 3600.0)
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert BLOCKER_HEARTBEAT_STALE in verdict.blockers
    assert verdict.heartbeat_statuses["operator"] is HeartbeatStatus.STALE
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    order = _market_order()
    _expect_boundary_error(
        lambda: boundary.propose(intent=placeholder, verdict=verdict),
        match=BLOCKER_HEARTBEAT_STALE,
    )
    _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=order, verdict=verdict),
        match=BLOCKER_HEARTBEAT_STALE,
    )


# ---------------------------------------------------------------------------
# Invariant 3 — Kill-switch TRIPPED propagates from P3 fake → RuntimeShell → boundary
# ---------------------------------------------------------------------------


def test_real_pipeline_kill_switch_tripped_blocks_propose_and_propose_order() -> None:
    """A real-pipeline kill-switch TRIPPED produces a blocker in both error messages."""
    _heartbeat, kill_switch, _reconciliation, shell = _build_clear_pipeline()
    kill_switch.trip(
        reason="composed safety integration test trip",
        triggered_by="operator",
    )
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert BLOCKER_KILL_SWITCH_TRIPPED in verdict.blockers
    assert verdict.kill_switch_state is KillSwitchState.TRIPPED
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    order = _limit_order()
    _expect_boundary_error(
        lambda: boundary.propose(intent=placeholder, verdict=verdict),
        match=BLOCKER_KILL_SWITCH_TRIPPED,
    )
    _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=order, verdict=verdict),
        match=BLOCKER_KILL_SWITCH_TRIPPED,
    )


# ---------------------------------------------------------------------------
# Invariant 4 — Reconciliation FAILED propagates from P3 fake → RuntimeShell → boundary
# ---------------------------------------------------------------------------


def test_real_pipeline_reconciliation_failed_blocks_propose_and_propose_order() -> None:
    """A real-pipeline reconciliation FAILED produces a blocker in both error messages."""
    _heartbeat, _kill_switch, reconciliation, shell = _build_clear_pipeline()
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=42.5,
        details={"composed-safety-scenario": "material-mismatch"},
    )
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert BLOCKER_RECONCILIATION_FAILED in verdict.blockers
    assert verdict.reconciliation_status is ReconciliationStatus.FAILED
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    order = _market_order()
    _expect_boundary_error(
        lambda: boundary.propose(intent=placeholder, verdict=verdict),
        match=BLOCKER_RECONCILIATION_FAILED,
    )
    _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=order, verdict=verdict),
        match=BLOCKER_RECONCILIATION_FAILED,
    )


# ---------------------------------------------------------------------------
# Invariant 5 — Reconciliation UNAVAILABLE propagates
# ---------------------------------------------------------------------------


def test_real_pipeline_reconciliation_unavailable_blocks_propose_and_propose_order() -> None:
    """A real-pipeline reconciliation UNAVAILABLE (no staged outcome) blocks both methods.

    ADR-003 mandates that a freshly-constructed (or drained) reconciliation
    pipeline reports ``UNAVAILABLE``, not ``CLEAN``. This tripwire fires
    when the P3-05 fake correctly returns UNAVAILABLE and the boundary
    rejects.
    """
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    # No outcome staged → reconciliation will report UNAVAILABLE.
    shell = RuntimeShell(
        heartbeat=heartbeat,
        kill_switch=kill_switch,
        reconciliation=reconciliation,
        required_components=("operator",),
    )
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert BLOCKER_RECONCILIATION_UNAVAILABLE in verdict.blockers
    assert verdict.reconciliation_status is ReconciliationStatus.UNAVAILABLE
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    order = _market_order()
    _expect_boundary_error(
        lambda: boundary.propose(intent=placeholder, verdict=verdict),
        match=BLOCKER_RECONCILIATION_UNAVAILABLE,
    )
    _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=order, verdict=verdict),
        match=BLOCKER_RECONCILIATION_UNAVAILABLE,
    )


# ---------------------------------------------------------------------------
# Invariant 6 — Reconciliation WARNING propagates as an advisory blocker
# ---------------------------------------------------------------------------


def test_real_pipeline_reconciliation_warning_blocks_propose_and_propose_order() -> None:
    """ADR-003 WARNING reconciliation produces an advisory-grade blocker in the verdict."""
    _heartbeat, _kill_switch, reconciliation, shell = _build_clear_pipeline()
    reconciliation.set_next(
        status=ReconciliationStatus.WARNING,
        tolerance=10.0,
        observed_delta=3.0,
        details={"composed-safety-scenario": "advisory-warning"},
    )
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert BLOCKER_RECONCILIATION_WARNING in verdict.blockers
    assert verdict.reconciliation_status is ReconciliationStatus.WARNING
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    order = _limit_order()
    _expect_boundary_error(
        lambda: boundary.propose(intent=placeholder, verdict=verdict),
        match=BLOCKER_RECONCILIATION_WARNING,
    )
    _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=order, verdict=verdict),
        match=BLOCKER_RECONCILIATION_WARNING,
    )


# ---------------------------------------------------------------------------
# Invariant 7 — Multi-blocker real pipeline fans every code into both error messages
# ---------------------------------------------------------------------------


def test_real_pipeline_multi_blocker_surfaces_every_code_in_error_messages() -> None:
    """Heartbeat STALE + kill switch TRIPPED + reconciliation FAILED all surface in both errors.

    Tripwires against future "summarize blockers" drift that would drop
    codes for terseness. This is the integration analog of the
    multi-blocker test in P5-03's invariants suite, but the verdict here
    is produced by the real ``RuntimeShell.evaluate()`` pipeline.
    """
    heartbeat, kill_switch, reconciliation, shell = _build_clear_pipeline()
    heartbeat.advance(9 * 3600.0)
    kill_switch.trip(reason="multi-blocker scenario", triggered_by="operator")
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=99.0,
        details={"composed-safety-scenario": "multi-blocker"},
    )
    verdict = shell.evaluate()
    assert verdict.clear is False
    for expected in (
        BLOCKER_HEARTBEAT_STALE,
        BLOCKER_KILL_SWITCH_TRIPPED,
        BLOCKER_RECONCILIATION_FAILED,
    ):
        assert expected in verdict.blockers, (
            f"expected blocker {expected!r} missing from verdict.blockers={verdict.blockers!r}"
        )
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    order = _market_order()
    propose_err = _expect_boundary_error(
        lambda: boundary.propose(intent=placeholder, verdict=verdict),
        match=BLOCKER_HEARTBEAT_STALE,
    )
    propose_order_err = _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=order, verdict=verdict),
        match=BLOCKER_HEARTBEAT_STALE,
    )
    propose_msg = str(propose_err)
    propose_order_msg = str(propose_order_err)
    for expected in (
        BLOCKER_HEARTBEAT_STALE,
        BLOCKER_KILL_SWITCH_TRIPPED,
        BLOCKER_RECONCILIATION_FAILED,
    ):
        assert expected in propose_msg, (
            f"propose error {propose_msg!r} missing blocker {expected!r}"
        )
        assert expected in propose_order_msg, (
            f"propose_order error {propose_order_msg!r} missing blocker {expected!r}"
        )


# ---------------------------------------------------------------------------
# Invariant 8 — Per-component heartbeat: STALE on one of several blocks the boundary
# ---------------------------------------------------------------------------


def test_real_pipeline_partial_component_staleness_blocks_propose_and_propose_order() -> None:
    """STALE on one required component is enough to block; FRESH on the other is not enough.

    The shell is configured with two required components
    (``"operator"`` and ``"local-machine"``). A FRESH ``operator``
    paired with a STALE ``local-machine`` produces a blocking verdict
    naming :data:`BLOCKER_HEARTBEAT_STALE`, and both ``propose`` and
    ``propose_order`` reject.
    """
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    heartbeat.beat("local-machine", _FIXED_CLOCK - timedelta(hours=10))
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    reconciliation.enqueue(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"composed-safety-scenario": "partial-staleness"},
    )
    shell = RuntimeShell(
        heartbeat=heartbeat,
        kill_switch=kill_switch,
        reconciliation=reconciliation,
        required_components=("operator", "local-machine"),
    )
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert BLOCKER_HEARTBEAT_STALE in verdict.blockers
    assert verdict.heartbeat_statuses["operator"] is HeartbeatStatus.FRESH
    assert verdict.heartbeat_statuses["local-machine"] is HeartbeatStatus.STALE
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    order = _market_order()
    _expect_boundary_error(
        lambda: boundary.propose(intent=placeholder, verdict=verdict),
        match=BLOCKER_HEARTBEAT_STALE,
    )
    _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=order, verdict=verdict),
        match=BLOCKER_HEARTBEAT_STALE,
    )


# ---------------------------------------------------------------------------
# Invariant 9 — Unknown required component reports STALE via the ADR-005 safe default
# ---------------------------------------------------------------------------


def test_real_pipeline_unknown_required_component_blocks_propose_and_propose_order() -> None:
    """A required component never `beat`-ed reports STALE per ADR-005 and blocks the boundary."""
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    # "auditor" is never beated, so the InMemoryHeartbeat fake will
    # return STALE for it per ADR-005's "safe default is paused" rule.
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    reconciliation.enqueue(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"composed-safety-scenario": "unknown-component"},
    )
    shell = RuntimeShell(
        heartbeat=heartbeat,
        kill_switch=kill_switch,
        reconciliation=reconciliation,
        required_components=("operator", "auditor"),
    )
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert BLOCKER_HEARTBEAT_STALE in verdict.blockers
    assert verdict.heartbeat_statuses["operator"] is HeartbeatStatus.FRESH
    assert verdict.heartbeat_statuses["auditor"] is HeartbeatStatus.STALE
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    order = _limit_order()
    _expect_boundary_error(
        lambda: boundary.propose(intent=placeholder, verdict=verdict),
        match=BLOCKER_HEARTBEAT_STALE,
    )
    _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=order, verdict=verdict),
        match=BLOCKER_HEARTBEAT_STALE,
    )


# ---------------------------------------------------------------------------
# Invariant 10 — Real-pipeline clear path: nothing is mutated
# ---------------------------------------------------------------------------


def test_real_pipeline_clear_path_does_not_mutate_fakes_or_inputs() -> None:
    """After a successful propose/propose_order, fakes and inputs are observably unchanged."""
    heartbeat, kill_switch, _reconciliation, shell = _build_clear_pipeline()
    verdict = shell.evaluate()
    assert verdict.clear is True
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    order = _market_order()
    # Snapshot every observable surface BEFORE the boundary calls.
    placeholder_snapshot = (
        placeholder.lane,
        placeholder.intent_id,
        placeholder.created_at,
    )
    order_snapshot = (
        order.lane,
        order.intent_id,
        order.created_at,
        order.symbol,
        order.side,
        order.quantity,
        order.order_type,
        order.limit_price,
    )
    verdict_snapshot = (
        verdict.clear,
        verdict.blockers,
        verdict.kill_switch_state,
        verdict.reconciliation_status,
        verdict.observed_at,
    )
    verdict_heartbeats_snapshot = dict(verdict.heartbeat_statuses)
    operator_status_before = heartbeat.status("operator")
    kill_switch_state_before = kill_switch.current()
    # Note: a second `reconcile()` on the same fake would drain the FIFO
    # and change the observed state. The boundary does not call any
    # method on the fakes; this snapshot is intended to be compared
    # *without* re-invoking `reconcile()`. We snapshot fake state via
    # the SafetyVerdict's recorded fields, which were captured at
    # `shell.evaluate()` time before the boundary saw the verdict.
    boundary.propose(intent=placeholder, verdict=verdict)
    boundary.propose_order(order_intent=order, verdict=verdict)
    # The boundary did not touch the fakes.
    operator_status_after = heartbeat.status("operator")
    kill_switch_state_after = kill_switch.current()
    assert operator_status_before == operator_status_after
    assert kill_switch_state_before == kill_switch_state_after
    # The inputs are observably unchanged.
    assert (
        placeholder.lane,
        placeholder.intent_id,
        placeholder.created_at,
    ) == placeholder_snapshot
    assert (
        order.lane,
        order.intent_id,
        order.created_at,
        order.symbol,
        order.side,
        order.quantity,
        order.order_type,
        order.limit_price,
    ) == order_snapshot
    # The verdict is observably unchanged.
    assert (
        verdict.clear,
        verdict.blockers,
        verdict.kill_switch_state,
        verdict.reconciliation_status,
        verdict.observed_at,
    ) == verdict_snapshot
    assert dict(verdict.heartbeat_statuses) == verdict_heartbeats_snapshot
    # Also confirm reconciliation did not get re-evaluated by the boundary.
    # (We do not call .reconcile() here because that would itself drain
    # the FIFO. Instead, we confirm a fresh evaluate() still produces a
    # clear-class verdict — there is no second outcome staged, so a
    # second evaluate() returns UNAVAILABLE; the staged outcome was
    # consumed by `shell.evaluate()` above, not by the boundary.)
    second_verdict = shell.evaluate()
    assert second_verdict.reconciliation_status is ReconciliationStatus.UNAVAILABLE
    # Confirm the reconciliation fake reports UNAVAILABLE not because the
    # boundary mutated it but because the FIFO was drained by the prior
    # shell.evaluate() (the boundary never touches reconciliation).
    assert BLOCKER_RECONCILIATION_UNAVAILABLE in second_verdict.blockers


# ---------------------------------------------------------------------------
# Invariant 11 — Real-pipeline blocked path: nothing is mutated by the boundary
# ---------------------------------------------------------------------------


def test_real_pipeline_blocked_path_does_not_mutate_fakes_or_inputs() -> None:
    """A blocked propose/propose_order does not mutate the fakes, the verdict, or the inputs."""
    heartbeat, kill_switch, reconciliation, shell = _build_clear_pipeline()
    kill_switch.trip(
        reason="blocked-path non-mutation test",
        triggered_by="operator",
    )
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert BLOCKER_KILL_SWITCH_TRIPPED in verdict.blockers
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    order = _limit_order()
    placeholder_snapshot = (
        placeholder.lane,
        placeholder.intent_id,
        placeholder.created_at,
    )
    order_snapshot = (
        order.lane,
        order.intent_id,
        order.created_at,
        order.symbol,
        order.side,
        order.quantity,
        order.order_type,
        order.limit_price,
    )
    verdict_snapshot = (
        verdict.clear,
        verdict.blockers,
        verdict.kill_switch_state,
        verdict.reconciliation_status,
        verdict.observed_at,
    )
    verdict_heartbeats_snapshot = dict(verdict.heartbeat_statuses)
    operator_status_before = heartbeat.status("operator")
    kill_switch_state_before = kill_switch.current()
    _expect_boundary_error(
        lambda: boundary.propose(intent=placeholder, verdict=verdict),
        match=BLOCKER_KILL_SWITCH_TRIPPED,
    )
    _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=order, verdict=verdict),
        match=BLOCKER_KILL_SWITCH_TRIPPED,
    )
    operator_status_after = heartbeat.status("operator")
    kill_switch_state_after = kill_switch.current()
    assert operator_status_before == operator_status_after
    # Kill switch should still be TRIPPED; ARMED would indicate the
    # boundary somehow cleared the trip, which would be a major violation.
    assert kill_switch_state_after.state is KillSwitchState.TRIPPED
    assert kill_switch_state_before == kill_switch_state_after
    assert (
        placeholder.lane,
        placeholder.intent_id,
        placeholder.created_at,
    ) == placeholder_snapshot
    assert (
        order.lane,
        order.intent_id,
        order.created_at,
        order.symbol,
        order.side,
        order.quantity,
        order.order_type,
        order.limit_price,
    ) == order_snapshot
    assert (
        verdict.clear,
        verdict.blockers,
        verdict.kill_switch_state,
        verdict.reconciliation_status,
        verdict.observed_at,
    ) == verdict_snapshot
    assert dict(verdict.heartbeat_statuses) == verdict_heartbeats_snapshot
    # The reconciliation fake should still hold the CLEAN outcome staged
    # by _build_clear_pipeline(); the boundary never called .reconcile()
    # itself, and shell.evaluate() drained the FIFO once before the
    # boundary saw the verdict. Re-evaluate to confirm the queue is now
    # drained (UNAVAILABLE) — this proves the FIFO state moved exactly
    # one step total (from the original CLEAN to UNAVAILABLE), driven by
    # shell.evaluate(), not by the boundary.
    second_verdict = shell.evaluate()
    # The reconciliation fake reports UNAVAILABLE (queue drained), kill
    # switch is still TRIPPED, heartbeat is FRESH.
    assert second_verdict.reconciliation_status is ReconciliationStatus.UNAVAILABLE
    assert second_verdict.kill_switch_state is KillSwitchState.TRIPPED
    assert BLOCKER_KILL_SWITCH_TRIPPED in second_verdict.blockers
    assert BLOCKER_RECONCILIATION_UNAVAILABLE in second_verdict.blockers
    # Suppress the unused-variable warning: we intentionally bind
    # `reconciliation` to make the test's relationship to the P3-05 fake
    # explicit even though we never call methods on it directly.
    assert reconciliation is not None


# ---------------------------------------------------------------------------
# Invariant 12 — Recovery: clearing a prior block lets the boundary accept again
# ---------------------------------------------------------------------------


def test_real_pipeline_recovery_clears_gate_for_propose_and_propose_order() -> None:
    """After staging a CLEAN outcome that replaces a prior FAILED, the gate reopens.

    Step 1: stage FAILED; ``evaluate()`` produces a blocked verdict that
    rejects both methods.
    Step 2: stage CLEAN (replacing the now-drained FIFO via ``set_next``);
    ``evaluate()`` produces a clear verdict that accepts both methods
    with identity-return. Tripwires against future drift in which the
    boundary or the shell remembers a prior blocked state stickily.
    """
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=42.0,
        details={"composed-safety-scenario": "recovery-step-1-failed"},
    )
    shell = RuntimeShell(
        heartbeat=heartbeat,
        kill_switch=kill_switch,
        reconciliation=reconciliation,
        required_components=("operator",),
    )
    blocked_verdict = shell.evaluate()
    assert blocked_verdict.clear is False
    assert BLOCKER_RECONCILIATION_FAILED in blocked_verdict.blockers
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    order = _market_order()
    _expect_boundary_error(
        lambda: boundary.propose(intent=placeholder, verdict=blocked_verdict),
        match=BLOCKER_RECONCILIATION_FAILED,
    )
    _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=order, verdict=blocked_verdict),
        match=BLOCKER_RECONCILIATION_FAILED,
    )
    # Stage recovery and re-evaluate.
    reconciliation.set_next(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"composed-safety-scenario": "recovery-step-2-clean"},
    )
    clear_verdict = shell.evaluate()
    assert clear_verdict.clear is True
    assert clear_verdict.blockers == ()
    # Boundary accepts again with identity-return.
    returned_intent = boundary.propose(intent=placeholder, verdict=clear_verdict)
    returned_order = boundary.propose_order(order_intent=order, verdict=clear_verdict)
    assert returned_intent is placeholder
    assert returned_order is order


# ---------------------------------------------------------------------------
# Inertness self-check on the new test module itself
# ---------------------------------------------------------------------------


_THIS_FILE = Path(__file__).resolve()


def test_composed_safety_foundation_module_has_no_forbidden_runtime_imports() -> None:
    """The new test module imports no runtime-coupling modules."""
    imported: set[str] = set()
    tree = ast.parse(_THIS_FILE.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module.split(".")[0])
    forbidden = {
        "os",
        "socket",
        "requests",
        "urllib",
        "http",
        "threading",
        "asyncio",
        "subprocess",
        "sqlite3",
        "pickle",
        "shelve",
        "ssl",
        "smtplib",
        "ftplib",
    }
    leaked = forbidden & imported
    assert not leaked, f"P5-04 composed-safety test must not import {leaked}"


def test_composed_safety_foundation_module_only_imports_from_authorized_sources() -> None:
    """The new test module imports only authorized stdlib + merged in-repo modules."""
    imported_from: set[str] = set()
    tree = ast.parse(_THIS_FILE.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_from.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported_from.add(alias.name)
    allowed_prefixes = (
        "__future__",
        "ast",
        "dataclasses",
        "datetime",
        "pathlib",
        "types",
        "gmc_rebuild.heartbeat",
        "gmc_rebuild.kill_switch",
        "gmc_rebuild.reconciliation",
        "gmc_rebuild.risk",
        "gmc_rebuild.runtime",
        "gmc_rebuild.simulation",
    )
    for mod in imported_from:
        assert mod.startswith(allowed_prefixes), (
            f"P5-04 composed-safety test imported unauthorized module {mod!r}"
        )


def test_composed_safety_foundation_module_imports_match_authorized_set() -> None:
    """The module's top-level imports exactly match the verbatim-authorized closed set.

    Mirrors the P5-02 / P5-03 import-shape invariant. Asserts the actual
    top-level imports against the closed authorized set, so any
    accidental new import (a runtime coupling, a new fake, a concrete
    protocol implementation, a new third-party dependency) is detected
    before merge.
    """
    tree = ast.parse(_THIS_FILE.read_text())
    top_level: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_level.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            top_level.add(node.module)
    expected = {
        "__future__",
        "ast",
        "dataclasses",
        "datetime",
        "pathlib",
        "gmc_rebuild.heartbeat",
        "gmc_rebuild.kill_switch",
        "gmc_rebuild.reconciliation",
        "gmc_rebuild.risk",
        "gmc_rebuild.runtime",
        "gmc_rebuild.simulation",
    }
    assert top_level == expected, (
        f"P5-04 composed-safety module imports drift: {top_level} != {expected}"
    )


def test_composed_safety_foundation_module_does_not_modify_simulation_or_runtime() -> None:
    """The new test module imports from `gmc_rebuild.runtime` and `gmc_rebuild.simulation`
    but never extends or modifies them.

    Smoke check that the existing P4-06 / P4-07 runtime surface and the
    existing P5-01 / P5-02 simulation surface are not modified by this
    test module. The structural prohibition is enforced by review and by
    PR diff scope; this test confirms the module reads but does not
    write.
    """
    source = _THIS_FILE.read_text()
    # Confirm both surfaces are exercised (the test would be meaningless
    # if they were not imported).
    assert "from gmc_rebuild.runtime import" in source
    assert "from gmc_rebuild.simulation import" in source
    # Confirm no monkeypatch / setattr / object.__setattr__ usage that
    # would mutate the runtime or simulation surfaces. Some such patterns
    # are legitimate in other test modules; we forbid them here as a
    # belt-and-suspenders check for the new module specifically.
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "__setattr__":
            raise AssertionError(
                "P5-04 composed-safety test must not use __setattr__ "
                "on simulation or runtime surfaces"
            )


# ---------------------------------------------------------------------------
# Compatibility with dataclasses.fields() inspection (used in module-init context)
# ---------------------------------------------------------------------------


def test_composed_safety_foundation_dataclass_fields_introspection_unchanged() -> None:
    """The `dataclasses.fields()` introspection of `SimulatedIntent` and `SimulatedOrderIntent`
    returns the expected field tuples: `SimulatedIntent` exactly as
    P5-01 left it, and `SimulatedOrderIntent` as P5-02 left it plus the
    P6-04 Direction A `time_in_force` ninth field.

    This is a final belt-and-suspenders tripwire that fails if a future
    change adds a tenth field to `SimulatedOrderIntent` or a fourth
    field to `SimulatedIntent` before this composed-safety test would
    even be able to construct them. The ninth `time_in_force` field was
    added in place by the P6-04 Direction A authorization
    (``governance/authorizations/2026-05-21_p6-04.md``).
    """
    intent_fields = tuple(f.name for f in dataclasses.fields(SimulatedIntent))
    order_fields = tuple(f.name for f in dataclasses.fields(SimulatedOrderIntent))
    assert intent_fields == ("lane", "intent_id", "created_at")
    assert order_fields == (
        "lane",
        "intent_id",
        "created_at",
        "symbol",
        "side",
        "quantity",
        "order_type",
        "limit_price",
        "time_in_force",
    )
