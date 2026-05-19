"""P5-06 ``propose`` ↔ ``propose_order`` symmetry tripwires.

This module is a **tripwire-only** integration test suite that pins
the structural symmetry between
:meth:`gmc_rebuild.simulation.SimulationBoundary.propose` (P5-01) and
:meth:`gmc_rebuild.simulation.SimulationBoundary.propose_order` (P5-02)
under the real composed P3-03 / P3-04 / P3-05 / P4-06 pipeline.

The tests verify that the two boundary methods behave **symmetrically**
across every observable axis: identical type validation (verdict and
intent argument shapes), identical lane-mismatch behavior, identical
``SafetyVerdict.clear`` precondition surfacing, identical
blocker-tuple propagation shape (including every named ``BLOCKER_*``
code and the multi-blocker fan-in), and identical non-mutation
contract on both the clear and blocked paths. Any future drift in
one method without a matching change in the other will produce a
test failure rather than silently breaking the
``propose`` / ``propose_order`` symmetry that the merged P5-01 / P5-02
contract relies on.

This is **direction (a)** of the four planning-level candidate
sketches recorded in
``governance/authorizations/2026-05-18_p5-06-planning.md``; the other
three candidate directions (operator-view determinism / idempotence;
closed-enum / closed-field defense-in-depth; ADR-005 / ADR-002 /
ADR-003 composed-policy alignment) remain planning-level candidates
only.

Authorization: ``governance/authorizations/2026-05-18_p5-06.md``.

This module introduces **no new production behaviour**: every test
composes already-merged public surfaces from
``gmc_rebuild.heartbeat``, ``gmc_rebuild.kill_switch``,
``gmc_rebuild.reconciliation``, ``gmc_rebuild.risk``,
``gmc_rebuild.runtime``, and ``gmc_rebuild.simulation``. It adds no
module under ``src/**``, no new public symbol, no new field, no new
method, and no ``SimulationLane`` / ``SimulatedOrderSide`` /
``SimulatedOrderType`` member. Tests avoid ``pytest.raises`` and
fixture-typed parameters so the mypy-strict pre-commit hook does not
need a pytest-stub dependency, mirroring the existing
``tests/runtime/test_operator_view.py``,
``tests/simulation/test_composed_safety_foundation.py``,
``tests/runtime/test_operator_view_composed_safety_foundation.py``,
and the other ``tests/simulation/`` modules.
"""

from __future__ import annotations

import ast
from dataclasses import replace
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
    SafetyVerdict,
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


def _expect_boundary_error(call: object) -> SimulationBoundaryError:
    raised: Exception | None = None
    try:
        call()  # type: ignore[operator]
    except SimulationBoundaryError as exc:
        raised = exc
    assert isinstance(raised, SimulationBoundaryError), (
        f"expected SimulationBoundaryError, got {raised!r}"
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
        details={"p5-06-propose-symmetry-scenario": "clear"},
    )
    shell = RuntimeShell(
        heartbeat=heartbeat,
        kill_switch=kill_switch,
        reconciliation=reconciliation,
        required_components=("operator",),
    )
    return heartbeat, kill_switch, reconciliation, shell


def _placeholder_intent(*, intent_id: str = "intent-p5-06-sym") -> SimulatedIntent:
    return SimulatedIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_FIXED_CLOCK_Z,
    )


def _market_order(*, intent_id: str = "order-p5-06-sym-A") -> SimulatedOrderIntent:
    return SimulatedOrderIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_FIXED_CLOCK_Z,
        symbol="SIM-P5-06-A",
        side=SimulatedOrderSide.BUY,
        quantity=10,
        order_type=SimulatedOrderType.MARKET,
        limit_price=None,
    )


def _limit_order(*, intent_id: str = "order-p5-06-sym-B") -> SimulatedOrderIntent:
    return SimulatedOrderIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_FIXED_CLOCK_Z,
        symbol="SIM-P5-06-B",
        side=SimulatedOrderSide.SELL,
        quantity=25,
        order_type=SimulatedOrderType.LIMIT,
        limit_price=7.5,
    )


def _snapshot_order(order: SimulatedOrderIntent) -> tuple[object, ...]:
    return (
        order.lane,
        order.intent_id,
        order.created_at,
        order.symbol,
        order.side,
        order.quantity,
        order.order_type,
        order.limit_price,
    )


def _snapshot_placeholder(intent: SimulatedIntent) -> tuple[object, ...]:
    return (intent.lane, intent.intent_id, intent.created_at)


def _snapshot_verdict(verdict: SafetyVerdict) -> tuple[object, ...]:
    return (
        verdict.clear,
        verdict.blockers,
        verdict.kill_switch_state,
        verdict.reconciliation_status,
        verdict.observed_at,
        tuple(sorted(verdict.heartbeat_statuses.items())),
    )


# ---------------------------------------------------------------------------
# Invariant 1 — Clear-path symmetry: both methods return supplied intent by identity
# ---------------------------------------------------------------------------


def test_clear_path_symmetry_propose_and_propose_order_return_by_identity() -> None:
    """On a real-pipeline-clear verdict, both methods accept by identity."""
    _heartbeat, _kill_switch, _reconciliation, shell = _build_clear_pipeline()
    verdict = shell.evaluate()
    assert verdict.clear is True
    assert verdict.blockers == ()
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    market = _market_order()
    limit = _limit_order()
    assert boundary.propose(intent=placeholder, verdict=verdict) is placeholder
    assert boundary.propose_order(order_intent=market, verdict=verdict) is market
    assert boundary.propose_order(order_intent=limit, verdict=verdict) is limit


# ---------------------------------------------------------------------------
# Invariant 2 — Verdict-type symmetry: non-SafetyVerdict raises symmetrically
# ---------------------------------------------------------------------------


def test_verdict_type_symmetry_non_safety_verdict_raises_from_both_methods() -> None:
    """Both methods raise SimulationBoundaryError with the wrong-type name
    when verdict is not a SafetyVerdict.
    """
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    market = _market_order()
    bogus = "not-a-verdict"
    propose_err = _expect_boundary_error(
        lambda: boundary.propose(intent=placeholder, verdict=bogus)  # type: ignore[arg-type]
    )
    propose_order_err = _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=market, verdict=bogus)  # type: ignore[arg-type]
    )
    assert "SafetyVerdict" in str(propose_err)
    assert "SafetyVerdict" in str(propose_order_err)
    assert "str" in str(propose_err)
    assert "str" in str(propose_order_err)


# ---------------------------------------------------------------------------
# Invariant 3 — Intent-type symmetry: wrong intent type raises symmetrically
# ---------------------------------------------------------------------------


def test_intent_type_symmetry_wrong_intent_type_raises_from_each_method() -> None:
    """propose raises on non-SimulatedIntent; propose_order raises on
    non-SimulatedOrderIntent — symmetric structure.
    """
    _heartbeat, _kill_switch, _reconciliation, shell = _build_clear_pipeline()
    verdict = shell.evaluate()
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    market = _market_order()
    placeholder = _placeholder_intent()
    propose_err = _expect_boundary_error(
        lambda: boundary.propose(intent=market, verdict=verdict)  # type: ignore[arg-type]
    )
    propose_order_err = _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=placeholder, verdict=verdict)  # type: ignore[arg-type]
    )
    assert "SimulatedIntent" in str(propose_err)
    assert "SimulatedOrderIntent" in str(propose_order_err)
    propose_err_bogus = _expect_boundary_error(
        lambda: boundary.propose(intent="not-an-intent", verdict=verdict)  # type: ignore[arg-type]
    )
    propose_order_err_bogus = _expect_boundary_error(
        lambda: boundary.propose_order(order_intent="not-an-order-intent", verdict=verdict)  # type: ignore[arg-type]
    )
    assert "SimulatedIntent" in str(propose_err_bogus)
    assert "SimulatedOrderIntent" in str(propose_order_err_bogus)


# ---------------------------------------------------------------------------
# Invariant 4 — Lane-mismatch symmetry: both methods reject lane mismatch identically
# ---------------------------------------------------------------------------


def test_lane_mismatch_symmetry_both_methods_reject_independently_of_verdict() -> None:
    """A lane-mismatched intent / order_intent is rejected by both methods even on a clear verdict.

    Constructs a boundary whose lane is a synthetic placeholder distinct
    from any intent's lane by monkey-mutating only the boundary's
    ``_lane`` private attribute on a freshly-built boundary, because
    ``SimulationLane`` is closed at one member. The mismatch test
    leverages that both methods compare ``intent.lane is self._lane``
    by identity, so substituting any non-``LOCAL_ONLY`` sentinel on the
    boundary triggers the lane-mismatch path in both methods.
    """
    _heartbeat, _kill_switch, _reconciliation, shell = _build_clear_pipeline()
    verdict = shell.evaluate()
    assert verdict.clear is True

    class _SentinelLane(str):
        """A distinct lane sentinel used only to drive the lane-mismatch path."""

    sentinel = _SentinelLane("sentinel_lane_p5_06")
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    # Force a lane mismatch by swapping the boundary's private lane to
    # a sentinel value that is not the LOCAL_ONLY member. This does not
    # add a SimulationLane member; the sentinel never escapes the test.
    object.__setattr__(boundary, "_lane", sentinel)
    placeholder = _placeholder_intent()
    market = _market_order()
    propose_err = _expect_boundary_error(
        lambda: boundary.propose(intent=placeholder, verdict=verdict)
    )
    propose_order_err = _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=market, verdict=verdict)
    )
    # Both error messages must name the intent's lane (LOCAL_ONLY) and
    # the boundary's mismatched sentinel lane, demonstrating identical
    # lane-mismatch surfacing across the two methods.
    propose_msg = str(propose_err)
    propose_order_msg = str(propose_order_err)
    assert "lane mismatch" in propose_msg
    assert "lane mismatch" in propose_order_msg
    assert str(SimulationLane.LOCAL_ONLY) in propose_msg
    assert str(SimulationLane.LOCAL_ONLY) in propose_order_msg
    assert "sentinel_lane_p5_06" in propose_msg
    assert "sentinel_lane_p5_06" in propose_order_msg


# ---------------------------------------------------------------------------
# Invariant 5 — Blocker-tuple propagation symmetry: every BLOCKER_* propagates identically
# ---------------------------------------------------------------------------


def _stage_heartbeat_stale() -> tuple[RuntimeShell, SafetyVerdict, str]:
    heartbeat, _kill_switch, _reconciliation, shell = _build_clear_pipeline()
    heartbeat.advance(9 * 3600.0)
    verdict = shell.evaluate()
    assert verdict.heartbeat_statuses["operator"] is HeartbeatStatus.STALE
    return shell, verdict, BLOCKER_HEARTBEAT_STALE


def _stage_kill_switch_tripped() -> tuple[RuntimeShell, SafetyVerdict, str]:
    _heartbeat, kill_switch, _reconciliation, shell = _build_clear_pipeline()
    kill_switch.trip(reason="p5-06 propose-symmetry trip", triggered_by="operator")
    verdict = shell.evaluate()
    assert verdict.kill_switch_state is KillSwitchState.TRIPPED
    return shell, verdict, BLOCKER_KILL_SWITCH_TRIPPED


def _stage_reconciliation_failed() -> tuple[RuntimeShell, SafetyVerdict, str]:
    _heartbeat, _kill_switch, reconciliation, shell = _build_clear_pipeline()
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=42.5,
        details={"p5-06-propose-symmetry-scenario": "failed"},
    )
    verdict = shell.evaluate()
    assert verdict.reconciliation_status is ReconciliationStatus.FAILED
    return shell, verdict, BLOCKER_RECONCILIATION_FAILED


def _stage_reconciliation_unavailable() -> tuple[RuntimeShell, SafetyVerdict, str]:
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
    assert verdict.reconciliation_status is ReconciliationStatus.UNAVAILABLE
    return shell, verdict, BLOCKER_RECONCILIATION_UNAVAILABLE


def _stage_reconciliation_warning() -> tuple[RuntimeShell, SafetyVerdict, str]:
    _heartbeat, _kill_switch, reconciliation, shell = _build_clear_pipeline()
    reconciliation.set_next(
        status=ReconciliationStatus.WARNING,
        tolerance=10.0,
        observed_delta=3.0,
        details={"p5-06-propose-symmetry-scenario": "advisory"},
    )
    verdict = shell.evaluate()
    assert verdict.reconciliation_status is ReconciliationStatus.WARNING
    return shell, verdict, BLOCKER_RECONCILIATION_WARNING


def test_blocker_tuple_propagation_symmetry_across_each_blocker_code() -> None:
    """For every BLOCKER_* code, both boundary methods raise with the same code
    and identical blockers tuple in the message.
    """
    stagers = (
        _stage_heartbeat_stale,
        _stage_kill_switch_tripped,
        _stage_reconciliation_failed,
        _stage_reconciliation_unavailable,
        _stage_reconciliation_warning,
    )
    for stager in stagers:
        _shell, verdict, expected_code = stager()
        assert verdict.clear is False
        assert expected_code in verdict.blockers, (
            f"stager {stager.__name__}: expected {expected_code!r} in "
            f"verdict.blockers={verdict.blockers!r}"
        )
        boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
        placeholder = _placeholder_intent()
        market = _market_order()
        propose_err = _expect_boundary_error(
            lambda b=boundary, p=placeholder, v=verdict: b.propose(intent=p, verdict=v)
        )
        propose_order_err = _expect_boundary_error(
            lambda b=boundary, m=market, v=verdict: b.propose_order(order_intent=m, verdict=v)
        )
        propose_msg = str(propose_err)
        propose_order_msg = str(propose_order_err)
        # Symmetric: identical blocker code present in both messages.
        assert expected_code in propose_msg, (
            f"stager {stager.__name__}: propose msg {propose_msg!r} missing {expected_code!r}"
        )
        assert expected_code in propose_order_msg, (
            f"stager {stager.__name__}: propose_order msg {propose_order_msg!r} "
            f"missing {expected_code!r}"
        )
        # Symmetric: identical verdict.blockers tuple representation
        # appears in both messages (both methods format the same
        # blocker tuple via ``blockers={verdict.blockers!r}``).
        blockers_repr = repr(verdict.blockers)
        assert blockers_repr in propose_msg, (
            f"stager {stager.__name__}: propose msg {propose_msg!r} missing "
            f"blockers repr {blockers_repr!r}"
        )
        assert blockers_repr in propose_order_msg, (
            f"stager {stager.__name__}: propose_order msg "
            f"{propose_order_msg!r} missing blockers repr {blockers_repr!r}"
        )


# ---------------------------------------------------------------------------
# Invariant 6 — Multi-blocker symmetry: every code surfaces in both error messages
# ---------------------------------------------------------------------------


def test_multi_blocker_symmetry_every_code_surfaces_in_both_error_messages() -> None:
    """Heartbeat STALE + kill switch TRIPPED + reconciliation FAILED fan into
    both boundary error messages identically.
    """
    heartbeat, kill_switch, reconciliation, shell = _build_clear_pipeline()
    heartbeat.advance(9 * 3600.0)
    kill_switch.trip(reason="multi-blocker propose-symmetry", triggered_by="operator")
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=99.0,
        details={"p5-06-propose-symmetry-scenario": "multi-blocker"},
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
            f"expected {code!r} missing from verdict.blockers={verdict.blockers!r}"
        )
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    market = _market_order()
    propose_err = _expect_boundary_error(
        lambda: boundary.propose(intent=placeholder, verdict=verdict)
    )
    propose_order_err = _expect_boundary_error(
        lambda: boundary.propose_order(order_intent=market, verdict=verdict)
    )
    propose_msg = str(propose_err)
    propose_order_msg = str(propose_order_err)
    for code in expected_codes:
        assert code in propose_msg, f"propose msg {propose_msg!r} missing blocker {code!r}"
        assert code in propose_order_msg, (
            f"propose_order msg {propose_order_msg!r} missing blocker {code!r}"
        )


# ---------------------------------------------------------------------------
# Invariant 7 — Clear-path non-mutation symmetry: repeated calls do not mutate
# ---------------------------------------------------------------------------


def test_clear_path_non_mutation_symmetry_repeated_calls_do_not_mutate() -> None:
    """Neither boundary method mutates inputs or fakes when called repeatedly on a clear verdict."""
    heartbeat, kill_switch, _reconciliation, shell = _build_clear_pipeline()
    verdict = shell.evaluate()
    assert verdict.clear is True
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    market = _market_order()
    limit = _limit_order()
    operator_status_before = heartbeat.status("operator")
    kill_switch_state_before = kill_switch.current()
    verdict_snapshot = _snapshot_verdict(verdict)
    placeholder_snapshot = _snapshot_placeholder(placeholder)
    market_snapshot = _snapshot_order(market)
    limit_snapshot = _snapshot_order(limit)
    boundary_lane_before = boundary.lane
    for _ in range(3):
        assert boundary.propose(intent=placeholder, verdict=verdict) is placeholder
        assert boundary.propose_order(order_intent=market, verdict=verdict) is market
        assert boundary.propose_order(order_intent=limit, verdict=verdict) is limit
    assert heartbeat.status("operator") == operator_status_before
    assert kill_switch.current() == kill_switch_state_before
    assert _snapshot_verdict(verdict) == verdict_snapshot
    assert _snapshot_placeholder(placeholder) == placeholder_snapshot
    assert _snapshot_order(market) == market_snapshot
    assert _snapshot_order(limit) == limit_snapshot
    assert boundary.lane is boundary_lane_before


# ---------------------------------------------------------------------------
# Invariant 8 — Blocked-path non-mutation symmetry: rejected calls do not mutate
# ---------------------------------------------------------------------------


def test_blocked_path_non_mutation_symmetry_rejected_calls_do_not_mutate() -> None:
    """Neither boundary method mutates inputs or fakes when called repeatedly
    on a blocked verdict.
    """
    heartbeat, kill_switch, _reconciliation, shell = _build_clear_pipeline()
    kill_switch.trip(reason="blocked-path symmetry", triggered_by="operator")
    verdict = shell.evaluate()
    assert verdict.clear is False
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    market = _market_order()
    operator_status_before = heartbeat.status("operator")
    kill_switch_state_before = kill_switch.current()
    verdict_snapshot = _snapshot_verdict(verdict)
    placeholder_snapshot = _snapshot_placeholder(placeholder)
    market_snapshot = _snapshot_order(market)
    boundary_lane_before = boundary.lane
    for _ in range(3):
        _expect_boundary_error(lambda: boundary.propose(intent=placeholder, verdict=verdict))
        _expect_boundary_error(lambda: boundary.propose_order(order_intent=market, verdict=verdict))
    assert heartbeat.status("operator") == operator_status_before
    assert kill_switch.current() == kill_switch_state_before
    assert _snapshot_verdict(verdict) == verdict_snapshot
    assert _snapshot_placeholder(placeholder) == placeholder_snapshot
    assert _snapshot_order(market) == market_snapshot
    assert boundary.lane is boundary_lane_before


# ---------------------------------------------------------------------------
# Invariant 9 — Re-evaluation symmetry: recovery restores symmetric accept
# ---------------------------------------------------------------------------


def test_re_evaluation_symmetry_recovery_restores_symmetric_accept() -> None:
    """After staging CLEAN reconciliation following a FAILED outcome, both
    methods accept again by identity.
    """
    _heartbeat, _kill_switch, reconciliation, shell = _build_clear_pipeline()
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=15.0,
        details={"p5-06-propose-symmetry-scenario": "pre-recovery-failed"},
    )
    bad_verdict = shell.evaluate()
    assert bad_verdict.clear is False
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    market = _market_order()
    _expect_boundary_error(lambda: boundary.propose(intent=placeholder, verdict=bad_verdict))
    _expect_boundary_error(lambda: boundary.propose_order(order_intent=market, verdict=bad_verdict))
    # Stage a CLEAN outcome that supersedes the FAILED one.
    reconciliation.set_next(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"p5-06-propose-symmetry-scenario": "post-recovery-clean"},
    )
    recovered_verdict = shell.evaluate()
    assert recovered_verdict.clear is True
    assert boundary.propose(intent=placeholder, verdict=recovered_verdict) is placeholder
    assert boundary.propose_order(order_intent=market, verdict=recovered_verdict) is market


# ---------------------------------------------------------------------------
# Invariant 10 — Distinct-but-equal verdict symmetry: identity-return depends
# on input, not on verdict identity
# ---------------------------------------------------------------------------


def test_distinct_but_equal_verdict_symmetry_identity_return_tracks_input_not_verdict() -> None:
    """Two structurally-equal clear SafetyVerdict instances both produce
    identity-return on both methods.
    """
    _heartbeat, _kill_switch, _reconciliation, shell = _build_clear_pipeline()
    verdict_a = shell.evaluate()
    assert verdict_a.clear is True
    # Construct an independent clear verdict equal in field-content but
    # not the same object as verdict_a using dataclasses.replace.
    verdict_b = replace(verdict_a)
    assert verdict_b is not verdict_a
    assert verdict_b.clear is True
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    placeholder = _placeholder_intent()
    market = _market_order()
    assert boundary.propose(intent=placeholder, verdict=verdict_a) is placeholder
    assert boundary.propose(intent=placeholder, verdict=verdict_b) is placeholder
    assert boundary.propose_order(order_intent=market, verdict=verdict_a) is market
    assert boundary.propose_order(order_intent=market, verdict=verdict_b) is market


# ---------------------------------------------------------------------------
# Invariant 11 — Inertness self-check: imports are bounded
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


def test_propose_symmetry_module_has_no_forbidden_runtime_imports() -> None:
    """The new test module does not import any forbidden runtime root."""
    imported = _collect_imported_modules()
    roots = {name.split(".", 1)[0] for name in imported}
    overlap = roots & _FORBIDDEN_IMPORT_ROOTS
    assert overlap == set(), f"forbidden import roots present in test module: {sorted(overlap)!r}"


def test_propose_symmetry_module_only_imports_from_authorized_prefixes() -> None:
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
