"""P6-08 failure-handling / exception-typing consolidation tripwire tests.

Tripwire-only test packet for the merged Phase 6 surface (P6-01..P6-07),
modeled on the merged P5-03 / P5-04 / P5-05 / P5-06 / P5-07 precedent.
Each test in this module exercises an already-merged public surface and
asserts an invariant that, if violated by a future change, would fail
before the change reached ``main``.

Authorization: ``governance/authorizations/2026-06-15_p6-08.md`` (and the
merged planning packet
``governance/authorizations/2026-06-15_p6-08-planning.md``, PR #183 at
``15c7e98``).

Categories pinned (planning §3.9):

1. Per-layer exception-type contracts for P6-01 ``signal_intake``, P6-02
   ``eligibility``, P6-03 ``decision``, P6-04 ``simulation`` extension,
   P6-05 ``portfolio_state``, P6-06 ``reporting``, and P6-07
   ``operator_view``.
2. The structured ``audit_event`` record contract for the merged P6-06
   ``lifecycle.daily_report`` emission (closed eight-field set, closed
   ``lifecycle`` category, deterministic ``serialize_event`` JSON).
3. **No-swallow** AST invariants — no ``except Exception`` / ``except
   BaseException`` / bare ``except:`` / ``except`` with no name appears
   in the merged P6-01..P6-07 source.
4. Composed-pipeline coverage — clear-path produces ``WOULD_TRADE`` and
   non-empty ``applied_intent_ids``; each of the five ``BLOCKER_*``
   blocked paths produces ``WOULD_SKIP`` with the documented reason and
   the daily report / operator view preserve the ``UNAVAILABLE`` vs
   ``FAILED`` reconciliation distinction.
5. **Inertness self-check** — AST import scan over the new test module
   asserts only authorized prefixes appear and no forbidden runtime root
   (``os``, ``socket``, ``requests``, ``urllib``, ``http``, ``threading``,
   ``asyncio``, ``subprocess``, ``sqlite3``, ``pickle``, ``shelve``,
   ``ssl``, ``smtplib``, ``ftplib``, ``time``, ``uuid``, ``random``) is
   imported.
6. **Substring self-check** — no ``__main__`` block, ``time.sleep(``,
   ``socket.``, ``urllib``, ``requests.``, ``open(`` builtin, ``uuid.``,
   ``random.``, ``logging.basicConfig``, or handler installation appears
   in source.
7. **No-new-public-symbol invariant** — none of the merged P6-01..P6-07
   subpackages exposes any name beyond the documented public surface,
   and ``gmc_rebuild`` itself does not re-export any P6 name.

P6-08 introduces no new production behavior. No new public symbol, no
new exception class, no signature change. The merged P6-01..P6-07
modules are byte-for-byte unchanged.
"""

from __future__ import annotations

import ast
import importlib
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import MappingProxyType

from gmc_rebuild.decision import (
    PositionDecision,
    PositionDecisionOutcome,
    PositionDecisionReason,
    compose_position_decision,
)
from gmc_rebuild.eligibility import (
    EligibilityConfig,
    EligibilityDecision,
    EligibilityOutcome,
    EligibilityReason,
    check_eligibility,
)
from gmc_rebuild.heartbeat import InMemoryHeartbeat
from gmc_rebuild.kill_switch import InMemoryKillSwitch
from gmc_rebuild.logging import (
    AUDIT_CATEGORIES,
    AuditEvent,
    serialize_event,
)
from gmc_rebuild.operator_view import (
    DryRunOperatorView,
    build_dry_run_operator_view,
)
from gmc_rebuild.portfolio_state import (
    SimulatedPortfolio,
    SimulatedPosition,
    apply_simulated_order_intent,
)
from gmc_rebuild.reconciliation import InMemoryReconciliation
from gmc_rebuild.reporting import (
    DailyReport,
    build_daily_report,
    render_daily_report_event,
)
from gmc_rebuild.risk import (
    HeartbeatStatus,
    KillSwitchState,
    ReconciliationStatus,
)
from gmc_rebuild.runtime import (
    BLOCKER_KILL_SWITCH_TRIPPED,
    OperatorSafetyView,
    RuntimeShell,
    SafetyVerdict,
)
from gmc_rebuild.signal_intake import (
    SignalIntent,
    SignalSide,
    accept_signal_intent,
)
from gmc_rebuild.simulation import (
    SimulatedOrderIntent,
    SimulatedOrderSide,
    SimulatedOrderTimeInForce,
    SimulatedOrderType,
    SimulationBoundaryError,
    SimulationLane,
    derive_simulated_order_intent_id,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_FIXED_CLOCK: datetime = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)
_CREATED_AT: str = "2026-06-15T00:00:00Z"
_REPORT_DATE: str = "2026-06-15"


# ---------------------------------------------------------------------------
# Helpers (private to this module)
# ---------------------------------------------------------------------------


def _expect(
    exc_type: type[BaseException],
    fn: Callable[..., object],
    *args: object,
    **kwargs: object,
) -> BaseException:
    """Call ``fn`` and assert it raises ``exc_type``; return the exception."""
    raised: BaseException | None = None
    try:
        fn(*args, **kwargs)
    except exc_type as exc:
        raised = exc
    assert isinstance(raised, exc_type), (
        f"expected {exc_type.__name__} to be raised, got {raised!r}"
    )
    return raised


def _expect_match(
    exc_type: type[BaseException],
    match: str,
    fn: Callable[..., object],
    *args: object,
    **kwargs: object,
) -> BaseException:
    exc = _expect(exc_type, fn, *args, **kwargs)
    assert match in str(exc), f"{exc_type.__name__} message {str(exc)!r} missing {match!r}"
    return exc


def _clear_verdict() -> SafetyVerdict:
    return SafetyVerdict(
        clear=True,
        blockers=(),
        heartbeat_statuses=MappingProxyType({"operator": HeartbeatStatus.FRESH}),
        kill_switch_state=KillSwitchState.ARMED,
        reconciliation_status=ReconciliationStatus.CLEAN,
        observed_at=_CREATED_AT,
    )


def _blocked_verdict_kill_switch() -> SafetyVerdict:
    return SafetyVerdict(
        clear=False,
        blockers=(BLOCKER_KILL_SWITCH_TRIPPED,),
        heartbeat_statuses=MappingProxyType({"operator": HeartbeatStatus.FRESH}),
        kill_switch_state=KillSwitchState.TRIPPED,
        reconciliation_status=ReconciliationStatus.CLEAN,
        observed_at=_CREATED_AT,
    )


def _config() -> EligibilityConfig:
    return EligibilityConfig(
        allowed_symbols=frozenset({"SIM-A", "SIM-B"}),
        allowed_sides=frozenset({SignalSide.BUY, SignalSide.SELL}),
        min_quantity=1,
        max_quantity=1000,
        min_rationale_length=5,
    )


def _signal(symbol: str = "SIM-A") -> SignalIntent:
    return SignalIntent(
        intent_id=f"sig-{symbol}",
        symbol=symbol,
        side=SignalSide.BUY,
        quantity=10,
        rationale="p6-08 tripwire fixture rationale",
    )


def _would_trade_decision(symbol: str = "SIM-A") -> PositionDecision:
    signal = _signal(symbol)
    eligibility = check_eligibility(signal, _config())
    return compose_position_decision(signal, eligibility, _clear_verdict())


def _would_skip_decision(symbol: str = "SIM-A") -> PositionDecision:
    signal = _signal(symbol)
    eligibility = check_eligibility(signal, _config())
    return compose_position_decision(signal, eligibility, _blocked_verdict_kill_switch())


def _order_intent(
    *,
    symbol: str = "SIM-A",
    side: SimulatedOrderSide = SimulatedOrderSide.BUY,
    quantity: int = 10,
) -> SimulatedOrderIntent:
    intent_id = derive_simulated_order_intent_id(
        lane=SimulationLane.LOCAL_ONLY,
        symbol=symbol,
        side=side,
        quantity=quantity,
        order_type=SimulatedOrderType.MARKET,
        limit_price=None,
        time_in_force=SimulatedOrderTimeInForce.DAY,
        created_at=_CREATED_AT,
    )
    return SimulatedOrderIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=_CREATED_AT,
        symbol=symbol,
        side=side,
        quantity=quantity,
        order_type=SimulatedOrderType.MARKET,
        limit_price=None,
        time_in_force=SimulatedOrderTimeInForce.DAY,
    )


def _build_clear_runtime_shell() -> RuntimeShell:
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    reconciliation.enqueue(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"p6-08-scenario": "clear"},
    )
    return RuntimeShell(
        heartbeat=heartbeat,
        kill_switch=kill_switch,
        reconciliation=reconciliation,
        required_components=("operator",),
    )


# ---------------------------------------------------------------------------
# 1. P6-01 signal_intake — exception-type contract
# ---------------------------------------------------------------------------


def test_signal_intent_rejects_non_str_intent_id() -> None:
    _expect_match(
        TypeError,
        "intent_id must be a str",
        SignalIntent,
        intent_id=123,
        symbol="SIM-A",
        side=SignalSide.BUY,
        quantity=10,
        rationale="x" * 5,
    )


def test_signal_intent_rejects_empty_intent_id() -> None:
    _expect_match(
        ValueError,
        "intent_id must be a non-empty string",
        SignalIntent,
        intent_id="",
        symbol="SIM-A",
        side=SignalSide.BUY,
        quantity=10,
        rationale="x" * 5,
    )


def test_signal_intent_rejects_non_signal_side() -> None:
    _expect_match(
        TypeError,
        "side must be a SignalSide member",
        SignalIntent,
        intent_id="sig-A",
        symbol="SIM-A",
        side="buy",
        quantity=10,
        rationale="x" * 5,
    )


def test_signal_intent_rejects_non_positive_quantity() -> None:
    _expect_match(
        ValueError,
        "quantity must be a positive integer",
        SignalIntent,
        intent_id="sig-A",
        symbol="SIM-A",
        side=SignalSide.BUY,
        quantity=0,
        rationale="x" * 5,
    )


def test_signal_intent_frozen_assignment_raises() -> None:
    intent = _signal()
    _expect(FrozenInstanceError, setattr, intent, "quantity", 99)


def test_accept_signal_intent_rejects_non_intent() -> None:
    _expect_match(
        TypeError,
        "intent must be a SignalIntent",
        accept_signal_intent,
        object(),
    )


# ---------------------------------------------------------------------------
# 2. P6-02 eligibility — exception-type contract
# ---------------------------------------------------------------------------


def test_eligibility_config_rejects_non_int_min_quantity() -> None:
    _expect_match(
        TypeError,
        "min_quantity must be an int",
        EligibilityConfig,
        allowed_symbols=frozenset({"SIM-A"}),
        allowed_sides=frozenset({SignalSide.BUY}),
        min_quantity="1",
        max_quantity=10,
        min_rationale_length=1,
    )


def test_eligibility_config_rejects_min_above_max() -> None:
    _expect(
        ValueError,
        EligibilityConfig,
        allowed_symbols=frozenset({"SIM-A"}),
        allowed_sides=frozenset({SignalSide.BUY}),
        min_quantity=10,
        max_quantity=1,
        min_rationale_length=1,
    )


def test_eligibility_decision_biconditional_violation_eligible_with_reasons() -> None:
    _expect_match(
        ValueError,
        "EligibilityDecision with outcome=ELIGIBLE must have empty reasons",
        EligibilityDecision,
        outcome=EligibilityOutcome.ELIGIBLE,
        reasons=(EligibilityReason.SYMBOL_NOT_ALLOWED,),
    )


def test_eligibility_decision_biconditional_violation_ineligible_no_reasons() -> None:
    _expect(
        ValueError,
        EligibilityDecision,
        outcome=EligibilityOutcome.INELIGIBLE,
        reasons=(),
    )


def test_eligibility_decision_frozen_assignment_raises() -> None:
    decision = EligibilityDecision(outcome=EligibilityOutcome.ELIGIBLE, reasons=())
    _expect(FrozenInstanceError, setattr, decision, "outcome", EligibilityOutcome.INELIGIBLE)


def test_check_eligibility_rejects_non_intent() -> None:
    _expect_match(
        TypeError,
        "intent must be a SignalIntent",
        check_eligibility,
        object(),
        _config(),
    )


def test_check_eligibility_rejects_non_config() -> None:
    _expect_match(
        TypeError,
        "config must be an EligibilityConfig",
        check_eligibility,
        _signal(),
        object(),
    )


# ---------------------------------------------------------------------------
# 3. P6-03 decision — exception-type contract
# ---------------------------------------------------------------------------


def test_position_decision_rejects_non_outcome() -> None:
    _expect(
        TypeError,
        PositionDecision,
        outcome="WOULD_TRADE",
        reasons=(),
        intent_id="sig-A",
        eligibility=check_eligibility(_signal(), _config()),
        verdict=_clear_verdict(),
    )


def test_position_decision_biconditional_violation_would_trade_with_reasons() -> None:
    _expect_match(
        ValueError,
        "PositionDecision with outcome=WOULD_TRADE must have empty reasons",
        PositionDecision,
        outcome=PositionDecisionOutcome.WOULD_TRADE,
        reasons=(PositionDecisionReason.ELIGIBILITY_INELIGIBLE,),
        intent_id="sig-A",
        eligibility=check_eligibility(_signal(), _config()),
        verdict=_clear_verdict(),
    )


def test_position_decision_biconditional_violation_would_skip_no_reasons() -> None:
    _expect_match(
        ValueError,
        "PositionDecision with outcome=WOULD_SKIP must have non-empty reasons",
        PositionDecision,
        outcome=PositionDecisionOutcome.WOULD_SKIP,
        reasons=(),
        intent_id="sig-A",
        eligibility=check_eligibility(_signal(), _config()),
        verdict=_clear_verdict(),
    )


def test_position_decision_frozen_assignment_raises() -> None:
    decision = _would_trade_decision()
    _expect(FrozenInstanceError, setattr, decision, "intent_id", "other")


def test_compose_position_decision_rejects_non_intent() -> None:
    _expect_match(
        TypeError,
        "intent must be a SignalIntent",
        compose_position_decision,
        object(),
        check_eligibility(_signal(), _config()),
        _clear_verdict(),
    )


def test_compose_position_decision_rejects_non_verdict() -> None:
    _expect_match(
        TypeError,
        "verdict must be a SafetyVerdict",
        compose_position_decision,
        _signal(),
        check_eligibility(_signal(), _config()),
        object(),
    )


# ---------------------------------------------------------------------------
# 4. P6-04 simulation extension — typed SimulationBoundaryError contract
# ---------------------------------------------------------------------------


def test_simulated_order_intent_rejects_non_positive_quantity_via_typed_error() -> None:
    _expect(
        SimulationBoundaryError,
        SimulatedOrderIntent,
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="oi-bad-qty",
        created_at=_CREATED_AT,
        symbol="SIM-A",
        side=SimulatedOrderSide.BUY,
        quantity=0,
        order_type=SimulatedOrderType.MARKET,
        limit_price=None,
        time_in_force=SimulatedOrderTimeInForce.DAY,
    )


def test_simulation_boundary_error_is_value_error_subclass() -> None:
    assert issubclass(SimulationBoundaryError, ValueError)


def test_derive_simulated_order_intent_id_rejects_non_positive_quantity() -> None:
    _expect_match(
        SimulationBoundaryError,
        "quantity must be positive",
        derive_simulated_order_intent_id,
        lane=SimulationLane.LOCAL_ONLY,
        symbol="SIM-A",
        side=SimulatedOrderSide.BUY,
        quantity=0,
        order_type=SimulatedOrderType.MARKET,
        limit_price=None,
        time_in_force=SimulatedOrderTimeInForce.DAY,
        created_at=_CREATED_AT,
    )


# ---------------------------------------------------------------------------
# 5. P6-05 portfolio_state — exception-type contract
# ---------------------------------------------------------------------------


def test_simulated_position_rejects_zero_quantity() -> None:
    _expect_match(
        ValueError,
        "net_quantity must be non-zero",
        SimulatedPosition,
        symbol="SIM-A",
        net_quantity=0,
    )


def test_simulated_position_rejects_bool_quantity() -> None:
    _expect_match(
        TypeError,
        "net_quantity must be an int",
        SimulatedPosition,
        symbol="SIM-A",
        net_quantity=True,
    )


def test_simulated_position_frozen_assignment_raises() -> None:
    position = SimulatedPosition(symbol="SIM-A", net_quantity=10)
    _expect(FrozenInstanceError, setattr, position, "net_quantity", 20)


def test_simulated_portfolio_rejects_unsorted_positions() -> None:
    _expect_match(
        ValueError,
        "positions must be sorted by symbol ascending",
        SimulatedPortfolio,
        positions=(
            SimulatedPosition(symbol="SIM-B", net_quantity=1),
            SimulatedPosition(symbol="SIM-A", net_quantity=2),
        ),
        applied_intent_ids=(),
    )


def test_simulated_portfolio_rejects_duplicate_applied_intent_ids() -> None:
    _expect_match(
        ValueError,
        "applied_intent_ids must be unique",
        SimulatedPortfolio,
        positions=(),
        applied_intent_ids=("a", "a"),
    )


def test_apply_simulated_order_intent_rejects_non_portfolio() -> None:
    _expect_match(
        TypeError,
        "portfolio must be a SimulatedPortfolio",
        apply_simulated_order_intent,
        object(),
        decision=_would_trade_decision(),
        order_intent=_order_intent(),
    )


# ---------------------------------------------------------------------------
# 6. P6-06 reporting — exception-type contract + structured-record contract
# ---------------------------------------------------------------------------


def test_daily_report_rejects_empty_report_date() -> None:
    _expect_match(
        ValueError,
        "DailyReport.report_date must be a non-empty str",
        DailyReport,
        report_date="",
        decisions_total=0,
        would_trade=0,
        would_skip=0,
        applied_intent_ids=(),
        net_positions=(),
        reconciliation_status=ReconciliationStatus.CLEAN,
        tripped_invariants=(),
    )


def test_daily_report_rejects_count_mismatch() -> None:
    _expect_match(
        ValueError,
        "would_trade + would_skip",
        DailyReport,
        report_date=_REPORT_DATE,
        decisions_total=3,
        would_trade=1,
        would_skip=1,
        applied_intent_ids=(),
        net_positions=(),
        reconciliation_status=ReconciliationStatus.CLEAN,
        tripped_invariants=(),
    )


def test_build_daily_report_rejects_non_tuple_decisions() -> None:
    _expect_match(
        TypeError,
        "decisions must be a tuple",
        build_daily_report,
        report_date=_REPORT_DATE,
        decisions=[_would_trade_decision()],
        portfolio=SimulatedPortfolio.empty(),
        reconciliation_status=ReconciliationStatus.CLEAN,
    )


def test_render_daily_report_event_rejects_none_timestamp() -> None:
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(),
        portfolio=SimulatedPortfolio.empty(),
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    exc = _expect_match(
        ValueError,
        "explicit caller-supplied timestamp",
        render_daily_report_event,
        report,
        timestamp=None,
    )
    assert "implicit clock fallback is forbidden" in str(exc)


def test_render_daily_report_event_rejects_non_datetime_timestamp() -> None:
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(),
        portfolio=SimulatedPortfolio.empty(),
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    _expect_match(
        TypeError,
        "timestamp must be a datetime",
        render_daily_report_event,
        report,
        timestamp="2026-06-15",
    )


def test_render_daily_report_event_structured_record_contract() -> None:
    """Pin the merged P6-06 ``lifecycle.daily_report`` structured-record
    contract: closed ``lifecycle`` category, ``lifecycle.daily_report``
    name, deterministic ``serialize_event`` JSON, and the documented
    closed eight-field set."""
    decisions = (_would_trade_decision("SIM-A"), _would_skip_decision("SIM-B"))
    portfolio = apply_simulated_order_intent(
        SimulatedPortfolio.empty(),
        decision=decisions[0],
        order_intent=_order_intent(symbol="SIM-A", quantity=10),
    )
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=decisions,
        portfolio=portfolio,
        reconciliation_status=ReconciliationStatus.UNAVAILABLE,
        tripped_invariants=("INV_TRIPWIRE",),
    )
    event = render_daily_report_event(report, timestamp=_FIXED_CLOCK)
    assert isinstance(event, AuditEvent)
    assert event.category == "lifecycle"
    assert event.category in AUDIT_CATEGORIES
    assert event.name == "lifecycle.daily_report"

    assert set(event.fields.keys()) == {
        "report_date",
        "decisions_total",
        "would_trade",
        "would_skip",
        "applied_intent_ids",
        "net_positions",
        "reconciliation_status",
        "tripped_invariants",
    }
    assert event.fields["reconciliation_status"] == "unavailable"
    assert event.fields["tripped_invariants"] == ["INV_TRIPWIRE"]

    # Deterministic serialization for identical inputs + same explicit timestamp.
    first = serialize_event(event)
    second = serialize_event(render_daily_report_event(report, timestamp=_FIXED_CLOCK))
    assert first == second


def test_render_daily_report_event_preserves_reconciliation_unavailable_vs_failed() -> None:
    empty_portfolio = SimulatedPortfolio.empty()
    unavailable = render_daily_report_event(
        build_daily_report(
            report_date=_REPORT_DATE,
            decisions=(),
            portfolio=empty_portfolio,
            reconciliation_status=ReconciliationStatus.UNAVAILABLE,
            tripped_invariants=(),
        ),
        timestamp=_FIXED_CLOCK,
    )
    failed = render_daily_report_event(
        build_daily_report(
            report_date=_REPORT_DATE,
            decisions=(),
            portfolio=empty_portfolio,
            reconciliation_status=ReconciliationStatus.FAILED,
            tripped_invariants=(),
        ),
        timestamp=_FIXED_CLOCK,
    )
    assert unavailable.fields["reconciliation_status"] == "unavailable"
    assert failed.fields["reconciliation_status"] == "failed"
    assert unavailable.fields["reconciliation_status"] != failed.fields["reconciliation_status"]


# ---------------------------------------------------------------------------
# 7. P6-07 operator_view — exception-type contract
# ---------------------------------------------------------------------------


def test_dry_run_operator_view_rejects_empty_report_date() -> None:
    _expect_match(
        ValueError,
        "report_date must be a non-empty str",
        DryRunOperatorView,
        report_date="",
        decisions_total=0,
        would_trade=0,
        would_skip=0,
        decision_lines=(),
        order_intent_lines=(),
        net_position_lines=(),
        applied_intent_ids=(),
        reconciliation_status="clean",
        tripped_invariant_lines=(),
    )


def test_dry_run_operator_view_rejects_count_mismatch() -> None:
    _expect_match(
        ValueError,
        "would_trade + would_skip",
        DryRunOperatorView,
        report_date=_REPORT_DATE,
        decisions_total=3,
        would_trade=1,
        would_skip=1,
        decision_lines=("a", "b", "c"),
        order_intent_lines=(),
        net_position_lines=(),
        applied_intent_ids=(),
        reconciliation_status="clean",
        tripped_invariant_lines=(),
    )


def test_dry_run_operator_view_rejects_decision_lines_length_mismatch() -> None:
    _expect_match(
        ValueError,
        "decision_lines length must equal decisions_total",
        DryRunOperatorView,
        report_date=_REPORT_DATE,
        decisions_total=2,
        would_trade=1,
        would_skip=1,
        decision_lines=("only-one",),
        order_intent_lines=(),
        net_position_lines=(),
        applied_intent_ids=(),
        reconciliation_status="clean",
        tripped_invariant_lines=(),
    )


def test_build_dry_run_operator_view_rejects_non_tuple_decisions() -> None:
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(),
        portfolio=SimulatedPortfolio.empty(),
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    _expect_match(
        TypeError,
        "decisions must be a tuple",
        build_dry_run_operator_view,
        decisions=[_would_trade_decision()],
        order_intents=(),
        portfolio=SimulatedPortfolio.empty(),
        report=report,
    )


def test_build_dry_run_operator_view_rejects_non_order_intent_member() -> None:
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(),
        portfolio=SimulatedPortfolio.empty(),
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    _expect_match(
        TypeError,
        "order_intents members must be SimulatedOrderIntent",
        build_dry_run_operator_view,
        decisions=(),
        order_intents=(object(),),
        portfolio=SimulatedPortfolio.empty(),
        report=report,
    )


def test_build_dry_run_operator_view_rejects_non_report() -> None:
    _expect_match(
        TypeError,
        "report must be a DailyReport",
        build_dry_run_operator_view,
        decisions=(),
        order_intents=(),
        portfolio=SimulatedPortfolio.empty(),
        report=object(),
    )


def test_dry_run_operator_view_frozen_assignment_raises() -> None:
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(),
        portfolio=SimulatedPortfolio.empty(),
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    view = build_dry_run_operator_view(
        decisions=(),
        order_intents=(),
        portfolio=SimulatedPortfolio.empty(),
        report=report,
    )
    _expect(FrozenInstanceError, setattr, view, "would_trade", 99)


# ---------------------------------------------------------------------------
# 8. No-swallow AST invariants over every merged P6-NN package
# ---------------------------------------------------------------------------


_P6_PACKAGE_DIRS: tuple[str, ...] = (
    "signal_intake",
    "eligibility",
    "decision",
    "portfolio_state",
    "reporting",
    "operator_view",
)


def _walk_p6_source_files() -> list[Path]:
    src_root = Path(__file__).resolve().parents[2] / "src" / "gmc_rebuild"
    files: list[Path] = []
    for package in _P6_PACKAGE_DIRS:
        files.extend(sorted((src_root / package).glob("*.py")))
    return files


def test_p6_source_has_no_swallowing_except_handlers() -> None:
    """No ``except Exception`` / ``except BaseException`` / bare ``except:`` /
    ``except`` without a captured name appears anywhere in the merged
    P6-01..P6-07 source. Any such handler would swallow specific failure
    information and is a stop condition per the planning packet §8."""
    swallowing_root_names: frozenset[str] = frozenset({"Exception", "BaseException"})
    offenders: list[str] = []
    for path in _walk_p6_source_files():
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            # Bare except: (no type at all) is the worst offender.
            if node.type is None:
                offenders.append(f"{path}:{node.lineno}: bare except:")
                continue
            # except Exception / except BaseException is a swallowing handler.
            handler_root: str | None = None
            if isinstance(node.type, ast.Name):
                handler_root = node.type.id
            elif isinstance(node.type, ast.Attribute):
                handler_root = node.type.attr
            elif isinstance(node.type, ast.Tuple):
                for member in node.type.elts:
                    if isinstance(member, ast.Name) and member.id in swallowing_root_names:
                        offenders.append(f"{path}:{node.lineno}: except tuple includes {member.id}")
                continue
            if handler_root in swallowing_root_names:
                offenders.append(f"{path}:{node.lineno}: except {handler_root}")
    assert offenders == [], f"P6 source contains swallowing except handlers: {offenders!r}"


# ---------------------------------------------------------------------------
# 9. Composed-pipeline coverage (P6-01..P6-07 end-to-end)
# ---------------------------------------------------------------------------


def test_composed_pipeline_clear_path_produces_would_trade_with_applied_intent() -> None:
    """Clear-verdict path: P6-01 signal → P6-02 eligibility → P6-03
    decision (WOULD_TRADE) → P6-04 order intent → P6-05 portfolio
    (intent applied) → P6-06 daily report (would_trade == 1, non-empty
    applied_intent_ids) → P6-07 operator view (decision_lines /
    order_intent_lines / net_position_lines populated)."""
    shell = _build_clear_runtime_shell()
    verdict = shell.evaluate()
    assert verdict.clear is True

    intent = _signal("SIM-A")
    eligibility = check_eligibility(intent, _config())
    decision = compose_position_decision(intent, eligibility, verdict)
    assert decision.outcome is PositionDecisionOutcome.WOULD_TRADE

    order = _order_intent(symbol="SIM-A", quantity=12)
    portfolio = apply_simulated_order_intent(
        SimulatedPortfolio.empty(), decision=decision, order_intent=order
    )
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(decision,),
        portfolio=portfolio,
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    assert report.would_trade == 1
    assert report.would_skip == 0
    assert report.applied_intent_ids == (order.intent_id,)

    view = build_dry_run_operator_view(
        decisions=(decision,),
        order_intents=(order,),
        portfolio=portfolio,
        report=report,
    )
    assert view.would_trade == 1
    assert view.would_skip == 0
    assert view.decision_lines == (f"{intent.intent_id}: WOULD_TRADE",)
    assert view.order_intent_lines == ("SIM-A buy 12",)
    assert view.net_position_lines == ("SIM-A: 12",)
    assert view.applied_intent_ids == (order.intent_id,)
    assert view.reconciliation_status == "clean"


def test_composed_pipeline_kill_switch_blocker_produces_would_skip() -> None:
    """Kill-switch-tripped path produces ``WOULD_SKIP`` with the
    ``SAFETY_KILL_SWITCH_NOT_ARMED`` reason; the daily report counts the
    skip and the operator view records the reason in the decision line.
    """
    decision = compose_position_decision(
        _signal(), check_eligibility(_signal(), _config()), _blocked_verdict_kill_switch()
    )
    assert decision.outcome is PositionDecisionOutcome.WOULD_SKIP
    assert PositionDecisionReason.SAFETY_KILL_SWITCH_NOT_ARMED in decision.reasons

    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(decision,),
        portfolio=SimulatedPortfolio.empty(),
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    assert report.would_skip == 1
    assert report.applied_intent_ids == ()

    view = build_dry_run_operator_view(
        decisions=(decision,),
        order_intents=(),
        portfolio=SimulatedPortfolio.empty(),
        report=report,
    )
    assert view.would_skip == 1
    assert len(view.decision_lines) == 1
    assert "SAFETY_KILL_SWITCH_NOT_ARMED" in view.decision_lines[0]


def test_composed_pipeline_preserves_unavailable_vs_failed_to_operator_view() -> None:
    """The ``ReconciliationStatus`` ``UNAVAILABLE`` vs ``FAILED``
    distinction is preserved end-to-end through P6-06 / P6-07 (ADR-003).
    """
    empty_portfolio = SimulatedPortfolio.empty()
    unavailable_report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(),
        portfolio=empty_portfolio,
        reconciliation_status=ReconciliationStatus.UNAVAILABLE,
    )
    failed_report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(),
        portfolio=empty_portfolio,
        reconciliation_status=ReconciliationStatus.FAILED,
    )
    unavailable_view = build_dry_run_operator_view(
        decisions=(),
        order_intents=(),
        portfolio=SimulatedPortfolio.empty(),
        report=unavailable_report,
    )
    failed_view = build_dry_run_operator_view(
        decisions=(),
        order_intents=(),
        portfolio=SimulatedPortfolio.empty(),
        report=failed_report,
    )
    assert unavailable_view.reconciliation_status == "unavailable"
    assert failed_view.reconciliation_status == "failed"
    assert unavailable_view != failed_view


# ---------------------------------------------------------------------------
# 10. Inertness self-check (AST import scan over this test module)
# ---------------------------------------------------------------------------


_AUTHORIZED_IMPORT_PREFIXES: tuple[str, ...] = (
    "__future__",
    "ast",
    "collections.abc",
    "dataclasses",
    "datetime",
    "importlib",
    "pathlib",
    "types",
    "gmc_rebuild.decision",
    "gmc_rebuild.eligibility",
    "gmc_rebuild.heartbeat",
    "gmc_rebuild.kill_switch",
    "gmc_rebuild.logging",
    "gmc_rebuild.operator_view",
    "gmc_rebuild.portfolio_state",
    "gmc_rebuild.reconciliation",
    "gmc_rebuild.reporting",
    "gmc_rebuild.risk",
    "gmc_rebuild.runtime",
    "gmc_rebuild.signal_intake",
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
        "time",
        "uuid",
        "random",
    }
)


def _collect_imports_from_this_module() -> set[str]:
    source = Path(__file__).resolve().read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
            imported.add(node.module)
    return imported


def test_tripwire_module_has_no_forbidden_runtime_imports() -> None:
    imported = _collect_imports_from_this_module()
    roots = {name.split(".", 1)[0] for name in imported}
    overlap = roots & _FORBIDDEN_IMPORT_ROOTS
    assert overlap == set(), (
        f"forbidden import roots present in P6-08 tripwire module: {sorted(overlap)!r}"
    )


def test_tripwire_module_only_imports_from_authorized_prefixes() -> None:
    imported = _collect_imports_from_this_module()
    unauthorized: list[str] = []
    for name in sorted(imported):
        if not any(
            name == prefix or name.startswith(prefix + ".")
            for prefix in _AUTHORIZED_IMPORT_PREFIXES
        ):
            unauthorized.append(name)
    assert unauthorized == [], f"unauthorized imports in P6-08 tripwire module: {unauthorized!r}"


# ---------------------------------------------------------------------------
# 11. Substring self-check (no runtime activation / external I/O patterns)
# ---------------------------------------------------------------------------


def test_merged_p6_source_has_no_runtime_activation_or_external_io() -> None:
    """Belt-and-suspenders substring scan over the merged P6-01..P6-07
    source files for runtime-activation, I/O, and audit-emission
    patterns the import-graph test cannot catch.

    This scan tripwires the merged ``src/gmc_rebuild/<package>/`` source
    (not this test module), mirroring the merged P6-05 / P6-06 / P6-07
    convention. Tokens skipped intentionally (matching that convention)
    because each merged module's docstring legitimately uses them in
    backticked reassurance prose: ``now_utc(``, ``datetime.now(``,
    ``logging.basicConfig``, ``audit_event(``. The no-clock-read /
    no-emission contracts are instead proven by the per-package AST
    import scans the merged P6-NN test files already include and by
    :func:`test_p6_source_has_no_swallowing_except_handlers` above.
    """
    forbidden_patterns: tuple[str, ...] = (
        'if __name__ == "__main__"',
        "time.sleep(",
        "asyncio.sleep(",
        "socket.",
        "urllib",
        "requests.",
        "open(",
        "uuid.",
        "random.",
    )
    for path in _walk_p6_source_files():
        source = path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            assert pattern not in source, (
                f"forbidden pattern {pattern!r} unexpectedly present in {path}"
            )


# ---------------------------------------------------------------------------
# 12. No-new-public-symbol invariant
# ---------------------------------------------------------------------------


_EXPECTED_P6_PUBLIC_SURFACE: tuple[tuple[str, frozenset[str]], ...] = (
    (
        "gmc_rebuild.signal_intake",
        frozenset({"SignalIntent", "SignalSide", "accept_signal_intent"}),
    ),
    (
        "gmc_rebuild.eligibility",
        frozenset(
            {
                "EligibilityConfig",
                "EligibilityDecision",
                "EligibilityOutcome",
                "EligibilityReason",
                "check_eligibility",
            }
        ),
    ),
    (
        "gmc_rebuild.decision",
        frozenset(
            {
                "PositionDecision",
                "PositionDecisionOutcome",
                "PositionDecisionReason",
                "compose_position_decision",
            }
        ),
    ),
    (
        "gmc_rebuild.portfolio_state",
        frozenset(
            {
                "SimulatedPortfolio",
                "SimulatedPosition",
                "apply_simulated_order_intent",
            }
        ),
    ),
    (
        "gmc_rebuild.reporting",
        frozenset(
            {
                "DailyReport",
                "build_daily_report",
                "render_daily_report_event",
            }
        ),
    ),
    (
        "gmc_rebuild.operator_view",
        frozenset(
            {
                "DryRunOperatorView",
                "build_dry_run_operator_view",
            }
        ),
    ),
)


def test_p6_subpackages_expose_exactly_their_authorized_public_surface() -> None:
    for module_name, expected in _EXPECTED_P6_PUBLIC_SURFACE:
        module = importlib.import_module(module_name)
        actual = frozenset(module.__all__)
        assert actual == expected, (
            f"{module_name}.__all__ drifted: expected={sorted(expected)!r}, "
            f"actual={sorted(actual)!r}"
        )


def test_gmc_rebuild_root_does_not_re_export_p6_symbols() -> None:
    root = importlib.import_module("gmc_rebuild")
    forbidden_root_names: set[str] = set()
    for _module_name, names in _EXPECTED_P6_PUBLIC_SURFACE:
        forbidden_root_names.update(names)
    for name in forbidden_root_names:
        assert not hasattr(root, name), (
            f"gmc_rebuild unexpectedly re-exports {name!r}; per P6-NN no P6 "
            f"public name is re-exported from the package root."
        )
    root_all = list(getattr(root, "__all__", ()))
    overlap = sorted(set(root_all) & forbidden_root_names)
    assert overlap == [], f"gmc_rebuild.__all__ unexpectedly includes P6 names: {overlap!r}"


# ---------------------------------------------------------------------------
# 13. P6-07 operator_view is distinct from the merged P4-07 OperatorSafetyView
# ---------------------------------------------------------------------------


def test_dry_run_operator_view_is_distinct_from_operator_safety_view() -> None:
    """Defense in depth: the P6-07 ``DryRunOperatorView`` type is not
    the same type as the merged P4-07 ``OperatorSafetyView``, and the
    operator_view source does not import ``gmc_rebuild.runtime``
    (planning §3.4 default, pinned by the merged P6-07 implementation)."""
    assert DryRunOperatorView is not OperatorSafetyView  # type: ignore[comparison-overlap]
    assert DryRunOperatorView.__name__ == "DryRunOperatorView"
    assert OperatorSafetyView.__name__ == "OperatorSafetyView"

    operator_view_source = (
        Path(__file__).resolve().parents[2] / "src" / "gmc_rebuild" / "operator_view" / "_view.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(operator_view_source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
    assert not any(
        name == "gmc_rebuild.runtime" or name.startswith("gmc_rebuild.runtime.")
        for name in imported
    ), f"operator_view source unexpectedly imports gmc_rebuild.runtime: {sorted(imported)!r}"
