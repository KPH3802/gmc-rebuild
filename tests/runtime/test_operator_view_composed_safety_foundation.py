"""P5-05 operator-view x composed safety-foundation x simulation tripwires.

This module is a **tripwire-only** integration test suite that composes
the merged P4-07 read-only operator view
(:class:`gmc_rebuild.runtime.OperatorSafetyView`,
:func:`gmc_rebuild.runtime.format_safety_verdict`) with the merged
P4-06 / P4-07 / P4-08 safety foundation
(:class:`gmc_rebuild.runtime.RuntimeShell`,
:class:`gmc_rebuild.runtime.SafetyVerdict`), the merged
P3-03 / P3-04 / P3-05 in-memory fakes
(:class:`gmc_rebuild.heartbeat.InMemoryHeartbeat`,
:class:`gmc_rebuild.kill_switch.InMemoryKillSwitch`,
:class:`gmc_rebuild.reconciliation.InMemoryReconciliation`), and the
merged P5-01 / P5-02 :class:`SimulationBoundary` (both
:meth:`SimulationBoundary.propose` and
:meth:`SimulationBoundary.propose_order`).

The tests verify that operator-view text remains consistent with
``SimulationBoundary.propose`` and ``SimulationBoundary.propose_order``
behavior across blocker outcomes: a clear verdict produces a ``CLEAR``
view *and* both boundary methods return the supplied intent by
identity; a blocked verdict (for each of the five ``BLOCKER_*`` codes
and for the multi-blocker case) produces a ``BLOCKED`` view that names
the relevant blocker(s) *and* causes both boundary methods to raise
:class:`SimulationBoundaryError` with the same blocker code(s) present
in the message.

Authorization: ``governance/authorizations/2026-05-18_p5-05.md``.

This module introduces **no new production behaviour**: every test
composes already-merged public surfaces from ``gmc_rebuild.heartbeat``,
``gmc_rebuild.kill_switch``, ``gmc_rebuild.reconciliation``,
``gmc_rebuild.risk``, ``gmc_rebuild.runtime``, and
``gmc_rebuild.simulation``. It adds no module under ``src/**``, no new
public symbol, no new field, no new method, and no
``SimulationLane`` / ``SimulatedOrderSide`` / ``SimulatedOrderType``
member. Tests avoid ``pytest.raises`` and fixture-typed parameters so
the mypy-strict pre-commit hook does not need a pytest-stub
dependency, mirroring the existing
``tests/runtime/test_operator_view.py``,
``tests/simulation/test_composed_safety_foundation.py``, and the other
``tests/simulation/`` modules.
"""

from __future__ import annotations

import ast
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
    VERDICT_BLOCKED,
    VERDICT_CLEAR,
    OperatorSafetyView,
    RuntimeShell,
    SafetyVerdict,
    format_safety_verdict,
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

_FIXED_CLOCK = datetime(2026, 5, 18, 14, 0, 0, tzinfo=UTC)
_FIXED_CLOCK_Z = "2026-05-18T14:00:00Z"


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
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    reconciliation.enqueue(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"operator-view-composed-scenario": "clear"},
    )
    shell = RuntimeShell(
        heartbeat=heartbeat,
        kill_switch=kill_switch,
        reconciliation=reconciliation,
        required_components=("operator",),
    )
    return heartbeat, kill_switch, reconciliation, shell


def _market_order(*, intent_id: str = "order-p5-05-A") -> SimulatedOrderIntent:
    return SimulatedOrderIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_FIXED_CLOCK_Z,
        symbol="SIM-P5-05-A",
        side=SimulatedOrderSide.BUY,
        quantity=10,
        order_type=SimulatedOrderType.MARKET,
        limit_price=None,
    )


def _limit_order(*, intent_id: str = "order-p5-05-B") -> SimulatedOrderIntent:
    return SimulatedOrderIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_FIXED_CLOCK_Z,
        symbol="SIM-P5-05-B",
        side=SimulatedOrderSide.SELL,
        quantity=25,
        order_type=SimulatedOrderType.LIMIT,
        limit_price=7.5,
    )


def _placeholder_intent(*, intent_id: str = "intent-p5-05-X") -> SimulatedIntent:
    return SimulatedIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_FIXED_CLOCK_Z,
    )


# ---------------------------------------------------------------------------
# Invariant 1 — Clear verdict: operator view is CLEAR and the boundary accepts
# ---------------------------------------------------------------------------


def test_clear_verdict_operator_view_is_clear_and_boundary_accepts() -> None:
    """A real-pipeline-clear SafetyVerdict yields a CLEAR view and
    identity-return propose/propose_order.
    """
    _heartbeat, _kill_switch, _reconciliation, shell = _build_clear_pipeline()
    verdict = shell.evaluate()
    assert verdict.clear is True
    assert verdict.blockers == ()
    view = format_safety_verdict(verdict)
    assert isinstance(view, OperatorSafetyView)
    assert view.status == VERDICT_CLEAR
    assert view.blocker_lines == ()
    rendered = view.render()
    assert "safety: CLEAR" in rendered
    assert "blockers:" not in rendered
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    order = _market_order()
    assert boundary.propose(intent=placeholder, verdict=verdict) is placeholder
    assert boundary.propose_order(order_intent=order, verdict=verdict) is order


# ---------------------------------------------------------------------------
# Invariant 2 — Heartbeat STALE: view says BLOCKED with heartbeat description; boundary rejects
# ---------------------------------------------------------------------------


def test_heartbeat_stale_blocks_view_and_propose_and_propose_order() -> None:
    """Real-pipeline heartbeat STALE shows BLOCKED in the view and surfaces
    the blocker in both boundary errors.
    """
    heartbeat, _kill_switch, _reconciliation, shell = _build_clear_pipeline()
    heartbeat.advance(9 * 3600.0)
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert BLOCKER_HEARTBEAT_STALE in verdict.blockers
    assert verdict.heartbeat_statuses["operator"] is HeartbeatStatus.STALE
    view = format_safety_verdict(verdict)
    assert view.status == VERDICT_BLOCKED
    rendered = view.render()
    assert "safety: BLOCKED" in rendered
    assert "blockers:" in rendered
    assert any("heartbeat stale" in line for line in view.blocker_lines)
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
# Invariant 3 — Kill switch TRIPPED: view says BLOCKED with kill-switch
# description; boundary rejects
# ---------------------------------------------------------------------------


def test_kill_switch_tripped_blocks_view_and_propose_and_propose_order() -> None:
    """Real-pipeline kill-switch TRIPPED shows BLOCKED in the view and
    surfaces the blocker in both boundary errors.
    """
    _heartbeat, kill_switch, _reconciliation, shell = _build_clear_pipeline()
    kill_switch.trip(
        reason="operator-view composed tripwire trip",
        triggered_by="operator",
    )
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert BLOCKER_KILL_SWITCH_TRIPPED in verdict.blockers
    assert verdict.kill_switch_state is KillSwitchState.TRIPPED
    view = format_safety_verdict(verdict)
    assert view.status == VERDICT_BLOCKED
    assert any("kill switch tripped" in line for line in view.blocker_lines)
    rendered = view.render()
    assert "kill switch tripped" in rendered
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
# Invariant 4 — Reconciliation FAILED: view says BLOCKED with reconciliation
# description; boundary rejects
# ---------------------------------------------------------------------------


def test_reconciliation_failed_blocks_view_and_propose_and_propose_order() -> None:
    """Real-pipeline reconciliation FAILED shows BLOCKED in the view and
    surfaces the blocker in both boundary errors.
    """
    _heartbeat, _kill_switch, reconciliation, shell = _build_clear_pipeline()
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=42.5,
        details={"operator-view-composed-scenario": "failed"},
    )
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert BLOCKER_RECONCILIATION_FAILED in verdict.blockers
    assert verdict.reconciliation_status is ReconciliationStatus.FAILED
    view = format_safety_verdict(verdict)
    assert view.status == VERDICT_BLOCKED
    assert any("reconciliation failed" in line for line in view.blocker_lines)
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
# Invariant 5 — Reconciliation UNAVAILABLE: view says BLOCKED with unavailable
# description; boundary rejects
# ---------------------------------------------------------------------------


def test_reconciliation_unavailable_blocks_view_and_propose_and_propose_order() -> None:
    """Real-pipeline reconciliation UNAVAILABLE shows BLOCKED in the view and
    surfaces the blocker in both boundary errors.
    """
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
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
    view = format_safety_verdict(verdict)
    assert view.status == VERDICT_BLOCKED
    assert any("unavailable" in line for line in view.blocker_lines)
    assert not any("reconciliation failed" in line for line in view.blocker_lines)
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
# Invariant 6 — Reconciliation WARNING: view says BLOCKED with advisory
# description; boundary rejects
# ---------------------------------------------------------------------------


def test_reconciliation_warning_blocks_view_and_propose_and_propose_order() -> None:
    """ADR-003 WARNING reconciliation shows BLOCKED in the view and surfaces
    the advisory blocker in both boundary errors.
    """
    _heartbeat, _kill_switch, reconciliation, shell = _build_clear_pipeline()
    reconciliation.set_next(
        status=ReconciliationStatus.WARNING,
        tolerance=10.0,
        observed_delta=3.0,
        details={"operator-view-composed-scenario": "advisory"},
    )
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert BLOCKER_RECONCILIATION_WARNING in verdict.blockers
    assert verdict.reconciliation_status is ReconciliationStatus.WARNING
    view = format_safety_verdict(verdict)
    assert view.status == VERDICT_BLOCKED
    assert any("advisory" in line for line in view.blocker_lines)
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
# Invariant 7 — Multi-blocker: view renders every blocker; both boundary
# errors carry every blocker code
# ---------------------------------------------------------------------------


def test_multi_blocker_view_text_matches_propose_and_propose_order_error_codes() -> None:
    """Heartbeat STALE + kill switch TRIPPED + reconciliation FAILED fan into
    view text AND both error messages.
    """
    heartbeat, kill_switch, reconciliation, shell = _build_clear_pipeline()
    heartbeat.advance(9 * 3600.0)
    kill_switch.trip(reason="multi-blocker view tripwire", triggered_by="operator")
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=99.0,
        details={"operator-view-composed-scenario": "multi-blocker"},
    )
    verdict = shell.evaluate()
    assert verdict.clear is False
    expected_codes = (
        BLOCKER_HEARTBEAT_STALE,
        BLOCKER_KILL_SWITCH_TRIPPED,
        BLOCKER_RECONCILIATION_FAILED,
    )
    for code in expected_codes:
        assert code in verdict.blockers, (
            f"expected blocker {code!r} missing from verdict.blockers={verdict.blockers!r}"
        )
    view = format_safety_verdict(verdict)
    assert view.status == VERDICT_BLOCKED
    assert len(view.blocker_lines) == len(verdict.blockers)
    rendered = view.render()
    assert "heartbeat stale" in rendered
    assert "kill switch tripped" in rendered
    assert "reconciliation failed" in rendered
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
    for code in expected_codes:
        assert code in propose_msg, f"propose error {propose_msg!r} missing blocker {code!r}"
        assert code in propose_order_msg, (
            f"propose_order error {propose_order_msg!r} missing blocker {code!r}"
        )


# ---------------------------------------------------------------------------
# Invariant 8 — View status matches boundary accept/reject across blocker outcomes
# ---------------------------------------------------------------------------


def test_view_status_clear_iff_boundary_accepts_across_all_blockers() -> None:
    """The operator view's status is CLEAR iff both boundary methods would
    return the supplied intent by identity.

    Exercises every named ``BLOCKER_*`` outcome plus the clear case and
    asserts a strict biconditional: ``view.status == VERDICT_CLEAR`` if
    and only if ``boundary.propose(...)`` and
    ``boundary.propose_order(...)`` would each return the supplied
    intent by identity. Tripwires against future drift in either
    direction (a view labelled CLEAR while the boundary rejects, or a
    view labelled BLOCKED while the boundary accepts).
    """

    def _accepts(verdict: SafetyVerdict) -> bool:
        boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
        placeholder = _placeholder_intent()
        order = _market_order()
        try:
            propose_returned = boundary.propose(intent=placeholder, verdict=verdict)
            propose_order_returned = boundary.propose_order(order_intent=order, verdict=verdict)
        except SimulationBoundaryError:
            return False
        return propose_returned is placeholder and propose_order_returned is order

    # Clear case.
    _heartbeat, _kill_switch, _reconciliation, shell = _build_clear_pipeline()
    clear_verdict = shell.evaluate()
    assert clear_verdict.clear is True
    clear_view = format_safety_verdict(clear_verdict)
    assert clear_view.status == VERDICT_CLEAR
    assert _accepts(clear_verdict) is True

    # Heartbeat stale.
    heartbeat, _kill_switch_b, _reconciliation_b, shell_b = _build_clear_pipeline()
    heartbeat.advance(9 * 3600.0)
    hb_verdict = shell_b.evaluate()
    hb_view = format_safety_verdict(hb_verdict)
    assert hb_view.status == VERDICT_BLOCKED
    assert _accepts(hb_verdict) is False

    # Kill switch tripped.
    _heartbeat_c, kill_switch_c, _reconciliation_c, shell_c = _build_clear_pipeline()
    kill_switch_c.trip(reason="biconditional trip", triggered_by="operator")
    ks_verdict = shell_c.evaluate()
    ks_view = format_safety_verdict(ks_verdict)
    assert ks_view.status == VERDICT_BLOCKED
    assert _accepts(ks_verdict) is False

    # Reconciliation FAILED.
    _heartbeat_d, _kill_switch_d, reconciliation_d, shell_d = _build_clear_pipeline()
    reconciliation_d.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=12.0,
        details={"operator-view-composed-scenario": "biconditional-failed"},
    )
    rf_verdict = shell_d.evaluate()
    rf_view = format_safety_verdict(rf_verdict)
    assert rf_view.status == VERDICT_BLOCKED
    assert _accepts(rf_verdict) is False

    # Reconciliation UNAVAILABLE — no outcome staged.
    heartbeat_e = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    heartbeat_e.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    kill_switch_e = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation_e = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    shell_e = RuntimeShell(
        heartbeat=heartbeat_e,
        kill_switch=kill_switch_e,
        reconciliation=reconciliation_e,
        required_components=("operator",),
    )
    ru_verdict = shell_e.evaluate()
    ru_view = format_safety_verdict(ru_verdict)
    assert ru_view.status == VERDICT_BLOCKED
    assert _accepts(ru_verdict) is False

    # Reconciliation WARNING.
    _heartbeat_f, _kill_switch_f, reconciliation_f, shell_f = _build_clear_pipeline()
    reconciliation_f.set_next(
        status=ReconciliationStatus.WARNING,
        tolerance=10.0,
        observed_delta=2.0,
        details={"operator-view-composed-scenario": "biconditional-warning"},
    )
    rw_verdict = shell_f.evaluate()
    rw_view = format_safety_verdict(rw_verdict)
    assert rw_view.status == VERDICT_BLOCKED
    assert _accepts(rw_verdict) is False


# ---------------------------------------------------------------------------
# Invariant 9 — format_safety_verdict is read-only / does not mutate any input
# ---------------------------------------------------------------------------


def test_format_safety_verdict_does_not_mutate_fakes_verdict_or_intents() -> None:
    """Rendering the operator view does not mutate the P3 fakes, the verdict, or the intents."""
    heartbeat, kill_switch, _reconciliation, shell = _build_clear_pipeline()
    verdict = shell.evaluate()
    assert verdict.clear is True
    placeholder = _placeholder_intent()
    order = _market_order()
    operator_status_before = heartbeat.status("operator")
    kill_switch_state_before = kill_switch.current()
    verdict_snapshot = (
        verdict.clear,
        verdict.blockers,
        verdict.kill_switch_state,
        verdict.reconciliation_status,
        verdict.observed_at,
    )
    verdict_heartbeats_snapshot = dict(verdict.heartbeat_statuses)
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
    # Render the view three times.
    first = format_safety_verdict(verdict)
    second = format_safety_verdict(verdict)
    third = format_safety_verdict(verdict)
    assert first == second == third
    assert first.render() == second.render() == third.render()
    # Verify nothing was mutated.
    operator_status_after = heartbeat.status("operator")
    kill_switch_state_after = kill_switch.current()
    assert operator_status_before == operator_status_after
    assert kill_switch_state_before == kill_switch_state_after
    assert (
        verdict.clear,
        verdict.blockers,
        verdict.kill_switch_state,
        verdict.reconciliation_status,
        verdict.observed_at,
    ) == verdict_snapshot
    assert dict(verdict.heartbeat_statuses) == verdict_heartbeats_snapshot
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


# ---------------------------------------------------------------------------
# Invariant 10 — Inertness self-check: imports are bounded
# ---------------------------------------------------------------------------


_AUTHORIZED_IMPORT_PREFIXES: tuple[str, ...] = (
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
)

_FORBIDDEN_IMPORT_ROOTS: frozenset[str] = frozenset(
    {
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
)


def _collect_imported_modules() -> set[str]:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
            imported.add(node.module)
    return imported


def test_operator_view_composed_module_has_no_forbidden_runtime_imports() -> None:
    """The new test module does not import any forbidden runtime root."""
    imported = _collect_imported_modules()
    roots = {name.split(".", 1)[0] for name in imported}
    overlap = roots & _FORBIDDEN_IMPORT_ROOTS
    assert overlap == set(), f"forbidden import roots present in test module: {sorted(overlap)!r}"


def test_operator_view_composed_module_only_imports_from_authorized_prefixes() -> None:
    """Every module-level import begins with one of the authorized prefixes."""
    imported = _collect_imported_modules()
    unauthorized: list[str] = []
    for name in sorted(imported):
        if not any(
            name == prefix or name.startswith(prefix + ".")
            for prefix in _AUTHORIZED_IMPORT_PREFIXES
        ):
            unauthorized.append(name)
    assert unauthorized == [], f"unauthorized imports in test module: {unauthorized!r}"
