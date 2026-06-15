"""P6-07 deterministic read-only operator view tests.

Covers the contract authorized by
``governance/authorizations/2026-06-15_p6-07.md`` and enumerated by the
merged planning packet
``governance/authorizations/2026-06-15_p6-07-planning.md``:

- frozen / slotted / closed-shape invariants on :class:`DryRunOperatorView`
  (planning §3.9 item 5);
- deterministic build and render — identical inputs produce byte-for-byte
  identical value object and string render (planning §3.9 items 1 and 2);
- non-mutation of the supplied decisions / order intents / portfolio /
  daily report inputs (planning §3.9 item 4);
- equality / identity semantics (planning §3.9 item 6);
- render-content correctness, preserving the ``UNAVAILABLE`` vs ``FAILED``
  reconciliation distinction (planning §3.9 item 7);
- composed local-pipeline integration across the P6-01..P6-06 surfaces
  (planning §3.9 item 8);
- distinct-from-``OperatorSafetyView`` and no ``gmc_rebuild.runtime``
  import (planning §3.9 item 9);
- :mod:`ast` import-graph and substring inertness self-checks proving no
  network, persistence, runtime activation, env-var, secret,
  ``audit_event`` emission, or clock behavior (planning §3.9 items 3, 10,
  11);
- root-package non-re-export of the new surface (planning §3.9 item 12);
- §8 step 4a allowlist reconciliation evidence for ``operator_view``.

Exception expectations use the in-repo ``_expect_error`` try/except helper
rather than ``pytest.raises``, matching the merged P6-NN test convention
(none of which imports ``pytest`` at module level).
"""

from __future__ import annotations

import ast
import importlib
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import MappingProxyType

from gmc_rebuild.decision import (
    PositionDecision,
    compose_position_decision,
)
from gmc_rebuild.eligibility import EligibilityConfig, check_eligibility
from gmc_rebuild.operator_view import (
    DryRunOperatorView,
    build_dry_run_operator_view,
)
from gmc_rebuild.portfolio_state import SimulatedPortfolio, apply_simulated_order_intent
from gmc_rebuild.reporting import DailyReport, build_daily_report
from gmc_rebuild.risk import HeartbeatStatus, KillSwitchState, ReconciliationStatus
from gmc_rebuild.runtime import BLOCKER_KILL_SWITCH_TRIPPED, SafetyVerdict
from gmc_rebuild.signal_intake import SignalIntent, SignalSide
from gmc_rebuild.simulation import (
    SimulatedOrderIntent,
    SimulatedOrderSide,
    SimulatedOrderTimeInForce,
    SimulatedOrderType,
    SimulationLane,
    derive_simulated_order_intent_id,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CREATED_AT = "2026-06-15T00:00:00Z"
_REPORT_DATE = "2026-06-15"


def _expect_error(
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
    assert isinstance(raised, exc_type), f"expected {exc_type.__name__} to be raised"
    return raised


def _clear_verdict() -> SafetyVerdict:
    return SafetyVerdict(
        clear=True,
        blockers=(),
        heartbeat_statuses=MappingProxyType({"operator": HeartbeatStatus.FRESH}),
        kill_switch_state=KillSwitchState.ARMED,
        reconciliation_status=ReconciliationStatus.CLEAN,
        observed_at=_CREATED_AT,
    )


def _blocked_verdict() -> SafetyVerdict:
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
        rationale="p6-07 operator-view fixture rationale",
    )


def _would_trade_decision(symbol: str = "SIM-A") -> PositionDecision:
    signal = _signal(symbol)
    eligibility = check_eligibility(signal, _config())
    return compose_position_decision(signal, eligibility, _clear_verdict())


def _would_skip_decision(symbol: str = "SIM-A") -> PositionDecision:
    signal = _signal(symbol)
    eligibility = check_eligibility(signal, _config())
    return compose_position_decision(signal, eligibility, _blocked_verdict())


def _order_intent(
    *,
    symbol: str = "SIM-A",
    side: SimulatedOrderSide = SimulatedOrderSide.BUY,
    quantity: int = 10,
    created_at: str = _CREATED_AT,
) -> SimulatedOrderIntent:
    intent_id = derive_simulated_order_intent_id(
        lane=SimulationLane.LOCAL_ONLY,
        symbol=symbol,
        side=side,
        quantity=quantity,
        order_type=SimulatedOrderType.MARKET,
        limit_price=None,
        time_in_force=SimulatedOrderTimeInForce.DAY,
        created_at=created_at,
    )
    return SimulatedOrderIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=created_at,
        symbol=symbol,
        side=side,
        quantity=quantity,
        order_type=SimulatedOrderType.MARKET,
        limit_price=None,
        time_in_force=SimulatedOrderTimeInForce.DAY,
    )


def _sample_report() -> DailyReport:
    return DailyReport(
        report_date=_REPORT_DATE,
        decisions_total=2,
        would_trade=1,
        would_skip=1,
        applied_intent_ids=("simoi-aaa",),
        net_positions=(("SIM-A", 10),),
        reconciliation_status=ReconciliationStatus.CLEAN,
        tripped_invariants=(),
    )


def _sample_view() -> DryRunOperatorView:
    return DryRunOperatorView(
        report_date=_REPORT_DATE,
        decisions_total=2,
        would_trade=1,
        would_skip=1,
        decision_lines=(
            "sig-SIM-A: WOULD_TRADE",
            "sig-SIM-B: WOULD_SKIP [SAFETY_KILL_SWITCH_NOT_ARMED]",
        ),
        order_intent_lines=("SIM-A BUY 10",),
        net_position_lines=("SIM-A: 10",),
        applied_intent_ids=("simoi-aaa",),
        reconciliation_status="clean",
        tripped_invariant_lines=(),
    )


# ---------------------------------------------------------------------------
# DryRunOperatorView value type — shape and validation
# ---------------------------------------------------------------------------


def test_view_is_frozen_and_slotted() -> None:
    view = _sample_view()
    assert not hasattr(view, "__dict__")
    raised: Exception | None = None
    try:
        view.would_trade = 5  # type: ignore[misc]
    except FrozenInstanceError as exc:
        raised = exc
    assert isinstance(raised, FrozenInstanceError)


def test_view_has_exactly_ten_closed_fields() -> None:
    assert DryRunOperatorView.__dataclass_fields__.keys() == {
        "report_date",
        "decisions_total",
        "would_trade",
        "would_skip",
        "decision_lines",
        "order_intent_lines",
        "net_position_lines",
        "applied_intent_ids",
        "reconciliation_status",
        "tripped_invariant_lines",
    }


def test_view_rejects_empty_report_date() -> None:
    exc = _expect_error(
        ValueError,
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
    assert "report_date" in str(exc)


def test_view_rejects_count_mismatch() -> None:
    exc = _expect_error(
        ValueError,
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
    assert "would_trade + would_skip" in str(exc)


def test_view_rejects_bool_count() -> None:
    exc = _expect_error(
        TypeError,
        DryRunOperatorView,
        report_date=_REPORT_DATE,
        decisions_total=True,
        would_trade=0,
        would_skip=0,
        decision_lines=(),
        order_intent_lines=(),
        net_position_lines=(),
        applied_intent_ids=(),
        reconciliation_status="clean",
        tripped_invariant_lines=(),
    )
    assert "decisions_total must be an int" in str(exc)


def test_view_rejects_negative_count() -> None:
    exc = _expect_error(
        ValueError,
        DryRunOperatorView,
        report_date=_REPORT_DATE,
        decisions_total=-1,
        would_trade=0,
        would_skip=0,
        decision_lines=(),
        order_intent_lines=(),
        net_position_lines=(),
        applied_intent_ids=(),
        reconciliation_status="clean",
        tripped_invariant_lines=(),
    )
    assert "decisions_total" in str(exc)


def test_view_rejects_non_tuple_lines() -> None:
    exc = _expect_error(
        TypeError,
        DryRunOperatorView,
        report_date=_REPORT_DATE,
        decisions_total=0,
        would_trade=0,
        would_skip=0,
        decision_lines=[],
        order_intent_lines=(),
        net_position_lines=(),
        applied_intent_ids=(),
        reconciliation_status="clean",
        tripped_invariant_lines=(),
    )
    assert "decision_lines must be a tuple" in str(exc)


def test_view_rejects_empty_line_entry() -> None:
    exc = _expect_error(
        ValueError,
        DryRunOperatorView,
        report_date=_REPORT_DATE,
        decisions_total=1,
        would_trade=1,
        would_skip=0,
        decision_lines=("",),
        order_intent_lines=(),
        net_position_lines=(),
        applied_intent_ids=(),
        reconciliation_status="clean",
        tripped_invariant_lines=(),
    )
    assert "decision_lines members must be non-empty str" in str(exc)


def test_view_rejects_decision_lines_length_mismatch() -> None:
    exc = _expect_error(
        ValueError,
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
    assert "decision_lines length must equal decisions_total" in str(exc)


def test_view_rejects_empty_reconciliation_status() -> None:
    exc = _expect_error(
        ValueError,
        DryRunOperatorView,
        report_date=_REPORT_DATE,
        decisions_total=0,
        would_trade=0,
        would_skip=0,
        decision_lines=(),
        order_intent_lines=(),
        net_position_lines=(),
        applied_intent_ids=(),
        reconciliation_status="",
        tripped_invariant_lines=(),
    )
    assert "reconciliation_status" in str(exc)


def test_view_is_hashable() -> None:
    assert isinstance(hash(_sample_view()), int)


# ---------------------------------------------------------------------------
# build_dry_run_operator_view — echoing and snapshotting
# ---------------------------------------------------------------------------


def _empty_report() -> DailyReport:
    return build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(),
        portfolio=SimulatedPortfolio.empty(),
        reconciliation_status=ReconciliationStatus.CLEAN,
    )


def test_build_echoes_counts_and_date_from_report() -> None:
    trade = _would_trade_decision("SIM-A")
    skip = _would_skip_decision("SIM-B")
    intent = _order_intent(symbol="SIM-A", quantity=10)
    portfolio = apply_simulated_order_intent(
        SimulatedPortfolio.empty(), decision=trade, order_intent=intent
    )
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(trade, skip),
        portfolio=portfolio,
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    view = build_dry_run_operator_view(
        decisions=(trade, skip),
        order_intents=(intent,),
        portfolio=portfolio,
        report=report,
    )
    assert view.report_date == _REPORT_DATE
    assert view.decisions_total == 2
    assert view.would_trade == 1
    assert view.would_skip == 1
    assert view.applied_intent_ids == portfolio.applied_intent_ids
    assert view.reconciliation_status == "clean"


def test_build_summarizes_order_intents_in_input_order() -> None:
    intent_a = _order_intent(symbol="SIM-A", quantity=10)
    intent_b = _order_intent(symbol="SIM-B", side=SimulatedOrderSide.SELL, quantity=3)
    report = _empty_report()
    view = build_dry_run_operator_view(
        decisions=(),
        order_intents=(intent_a, intent_b),
        portfolio=SimulatedPortfolio.empty(),
        report=report,
    )
    assert view.order_intent_lines == ("SIM-A buy 10", "SIM-B sell 3")


def test_build_renders_net_positions_in_canonical_order() -> None:
    trade_a = _would_trade_decision("SIM-A")
    trade_b = _would_trade_decision("SIM-B")
    intent_a = _order_intent(symbol="SIM-A", quantity=10)
    intent_b = _order_intent(symbol="SIM-B", quantity=7)
    portfolio = apply_simulated_order_intent(
        SimulatedPortfolio.empty(), decision=trade_a, order_intent=intent_a
    )
    portfolio = apply_simulated_order_intent(portfolio, decision=trade_b, order_intent=intent_b)
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(trade_a, trade_b),
        portfolio=portfolio,
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    view = build_dry_run_operator_view(
        decisions=(trade_a, trade_b),
        order_intents=(intent_a, intent_b),
        portfolio=portfolio,
        report=report,
    )
    assert view.net_position_lines == ("SIM-A: 10", "SIM-B: 7")


def test_build_summarizes_would_skip_reasons() -> None:
    skip = _would_skip_decision("SIM-A")
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(skip,),
        portfolio=SimulatedPortfolio.empty(),
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    view = build_dry_run_operator_view(
        decisions=(skip,),
        order_intents=(),
        portfolio=SimulatedPortfolio.empty(),
        report=report,
    )
    assert len(view.decision_lines) == 1
    line = view.decision_lines[0]
    assert line.startswith(f"{skip.intent_id}: WOULD_SKIP [")
    assert "SAFETY_KILL_SWITCH_NOT_ARMED" in line


def test_build_summarizes_would_trade_without_reasons() -> None:
    trade = _would_trade_decision("SIM-A")
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(trade,),
        portfolio=SimulatedPortfolio.empty(),
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    view = build_dry_run_operator_view(
        decisions=(trade,),
        order_intents=(),
        portfolio=SimulatedPortfolio.empty(),
        report=report,
    )
    assert view.decision_lines == (f"{trade.intent_id}: WOULD_TRADE",)


def test_build_echoes_tripped_invariants_in_input_order() -> None:
    invariants = ("INV_A", "INV_B")
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(),
        portfolio=SimulatedPortfolio.empty(),
        reconciliation_status=ReconciliationStatus.CLEAN,
        tripped_invariants=invariants,
    )
    view = build_dry_run_operator_view(
        decisions=(),
        order_intents=(),
        portfolio=SimulatedPortfolio.empty(),
        report=report,
    )
    assert view.tripped_invariant_lines == invariants


def test_build_is_deterministic() -> None:
    trade = _would_trade_decision("SIM-A")
    intent = _order_intent(symbol="SIM-A", quantity=10)
    portfolio = apply_simulated_order_intent(
        SimulatedPortfolio.empty(), decision=trade, order_intent=intent
    )
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(trade,),
        portfolio=portfolio,
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    first = build_dry_run_operator_view(
        decisions=(trade,),
        order_intents=(intent,),
        portfolio=portfolio,
        report=report,
    )
    second = build_dry_run_operator_view(
        decisions=(trade,),
        order_intents=(intent,),
        portfolio=portfolio,
        report=report,
    )
    assert first == second
    assert first.render() == second.render()


def test_build_rejects_non_tuple_decisions() -> None:
    exc = _expect_error(
        TypeError,
        build_dry_run_operator_view,
        decisions=[_would_trade_decision()],
        order_intents=(),
        portfolio=SimulatedPortfolio.empty(),
        report=_empty_report(),
    )
    assert "decisions must be a tuple" in str(exc)


def test_build_rejects_non_position_decision_member() -> None:
    exc = _expect_error(
        TypeError,
        build_dry_run_operator_view,
        decisions=(object(),),
        order_intents=(),
        portfolio=SimulatedPortfolio.empty(),
        report=_empty_report(),
    )
    assert "decisions members must be PositionDecision" in str(exc)


def test_build_rejects_non_tuple_order_intents() -> None:
    exc = _expect_error(
        TypeError,
        build_dry_run_operator_view,
        decisions=(),
        order_intents=[_order_intent()],
        portfolio=SimulatedPortfolio.empty(),
        report=_empty_report(),
    )
    assert "order_intents must be a tuple" in str(exc)


def test_build_rejects_non_order_intent_member() -> None:
    exc = _expect_error(
        TypeError,
        build_dry_run_operator_view,
        decisions=(),
        order_intents=(object(),),
        portfolio=SimulatedPortfolio.empty(),
        report=_empty_report(),
    )
    assert "order_intents members must be SimulatedOrderIntent" in str(exc)


def test_build_rejects_non_portfolio() -> None:
    exc = _expect_error(
        TypeError,
        build_dry_run_operator_view,
        decisions=(),
        order_intents=(),
        portfolio=object(),
        report=_empty_report(),
    )
    assert "portfolio must be a SimulatedPortfolio" in str(exc)


def test_build_rejects_non_report() -> None:
    exc = _expect_error(
        TypeError,
        build_dry_run_operator_view,
        decisions=(),
        order_intents=(),
        portfolio=SimulatedPortfolio.empty(),
        report=object(),
    )
    assert "report must be a DailyReport" in str(exc)


def test_build_does_not_mutate_inputs() -> None:
    trade = _would_trade_decision("SIM-A")
    skip = _would_skip_decision("SIM-B")
    intent = _order_intent(symbol="SIM-A", quantity=10)
    portfolio = apply_simulated_order_intent(
        SimulatedPortfolio.empty(), decision=trade, order_intent=intent
    )
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(trade, skip),
        portfolio=portfolio,
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    portfolio_before = portfolio
    report_before = report
    decisions_tuple = (trade, skip)
    intents_tuple = (intent,)

    build_dry_run_operator_view(
        decisions=decisions_tuple,
        order_intents=intents_tuple,
        portfolio=portfolio,
        report=report,
    )

    assert portfolio == portfolio_before
    assert portfolio.positions == portfolio_before.positions
    assert portfolio.applied_intent_ids == portfolio_before.applied_intent_ids
    assert report == report_before
    assert decisions_tuple == (trade, skip)
    assert intents_tuple == (intent,)
    assert trade.intent_id and skip.intent_id and intent.intent_id


# ---------------------------------------------------------------------------
# render — deterministic string content
# ---------------------------------------------------------------------------


def test_render_is_deterministic_and_idempotent() -> None:
    view = _sample_view()
    first = view.render()
    second = view.render()
    third = _sample_view().render()
    assert first == second == third


def test_render_includes_summary_lines() -> None:
    view = _sample_view()
    rendered = view.render()
    assert rendered.startswith(f"dry_run: {_REPORT_DATE}\n")
    assert "decisions: 2 total, 1 would-trade, 1 would-skip" in rendered
    assert "reconciliation: clean" in rendered
    assert "order_intents:" in rendered
    assert "  - SIM-A BUY 10" in rendered
    assert "net_positions:" in rendered
    assert "  - SIM-A: 10" in rendered
    assert "applied_intent_ids:" in rendered
    assert "  - simoi-aaa" in rendered
    assert "decisions_detail:" in rendered
    assert "  - sig-SIM-A: WOULD_TRADE" in rendered
    assert "  - sig-SIM-B: WOULD_SKIP [SAFETY_KILL_SWITCH_NOT_ARMED]" in rendered


def test_render_omits_tripped_invariants_section_when_empty() -> None:
    rendered = _sample_view().render()
    assert "tripped_invariants" not in rendered


def test_render_includes_tripped_invariants_section_when_present() -> None:
    view = DryRunOperatorView(
        report_date=_REPORT_DATE,
        decisions_total=0,
        would_trade=0,
        would_skip=0,
        decision_lines=(),
        order_intent_lines=(),
        net_position_lines=(),
        applied_intent_ids=(),
        reconciliation_status="clean",
        tripped_invariant_lines=("INV_A", "INV_B"),
    )
    rendered = view.render()
    assert "tripped_invariants:" in rendered
    assert "  - INV_A" in rendered
    assert "  - INV_B" in rendered


def test_render_uses_none_marker_for_empty_sections() -> None:
    empty_view = build_dry_run_operator_view(
        decisions=(),
        order_intents=(),
        portfolio=SimulatedPortfolio.empty(),
        report=_empty_report(),
    )
    rendered = empty_view.render()
    assert "order_intents:\n  (none)" in rendered
    assert "net_positions:\n  (none)" in rendered
    assert "applied_intent_ids:\n  (none)" in rendered
    assert "decisions_detail:\n  (none)" in rendered


# ---------------------------------------------------------------------------
# Equality semantics
# ---------------------------------------------------------------------------


def test_structurally_equal_views_compare_equal() -> None:
    assert _sample_view() == _sample_view()


def test_distinct_views_compare_unequal() -> None:
    other = DryRunOperatorView(
        report_date=_REPORT_DATE,
        decisions_total=2,
        would_trade=2,
        would_skip=0,
        decision_lines=("a", "b"),
        order_intent_lines=("SIM-A BUY 10",),
        net_position_lines=("SIM-A: 10",),
        applied_intent_ids=("simoi-aaa",),
        reconciliation_status="clean",
        tripped_invariant_lines=(),
    )
    assert _sample_view() != other


# ---------------------------------------------------------------------------
# Composed local-pipeline integration (P6-01 .. P6-06)
# ---------------------------------------------------------------------------


def test_composed_pipeline_summarizes_cycle() -> None:
    trade_decision = _would_trade_decision("SIM-A")
    skip_decision = _would_skip_decision("SIM-B")
    order_intent = _order_intent(symbol="SIM-A", side=SimulatedOrderSide.BUY, quantity=25)
    portfolio = apply_simulated_order_intent(
        SimulatedPortfolio.empty(), decision=trade_decision, order_intent=order_intent
    )
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(trade_decision, skip_decision),
        portfolio=portfolio,
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    view = build_dry_run_operator_view(
        decisions=(trade_decision, skip_decision),
        order_intents=(order_intent,),
        portfolio=portfolio,
        report=report,
    )
    assert view.would_trade == 1
    assert view.would_skip == 1
    assert view.net_position_lines == ("SIM-A: 25",)
    assert view.applied_intent_ids == (order_intent.intent_id,)
    assert view.order_intent_lines == ("SIM-A buy 25",)
    assert view.decision_lines[0].startswith(f"{trade_decision.intent_id}: WOULD_TRADE")
    assert view.decision_lines[1].startswith(f"{skip_decision.intent_id}: WOULD_SKIP")


def test_composed_pipeline_preserves_unavailable_vs_failed() -> None:
    decisions = (_would_trade_decision("SIM-A"),)
    portfolio = SimulatedPortfolio.empty()
    unavailable_report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=decisions,
        portfolio=portfolio,
        reconciliation_status=ReconciliationStatus.UNAVAILABLE,
    )
    failed_report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=decisions,
        portfolio=portfolio,
        reconciliation_status=ReconciliationStatus.FAILED,
    )
    unavailable_view = build_dry_run_operator_view(
        decisions=decisions,
        order_intents=(),
        portfolio=portfolio,
        report=unavailable_report,
    )
    failed_view = build_dry_run_operator_view(
        decisions=decisions,
        order_intents=(),
        portfolio=portfolio,
        report=failed_report,
    )
    assert unavailable_view.reconciliation_status == "unavailable"
    assert failed_view.reconciliation_status == "failed"
    assert unavailable_view != failed_view


def test_empty_cycle_renders_clean_view() -> None:
    view = build_dry_run_operator_view(
        decisions=(),
        order_intents=(),
        portfolio=SimulatedPortfolio.empty(),
        report=_empty_report(),
    )
    assert view.decisions_total == 0
    assert view.decision_lines == ()
    assert view.order_intent_lines == ()
    assert view.net_position_lines == ()
    assert view.applied_intent_ids == ()
    assert view.tripped_invariant_lines == ()


# ---------------------------------------------------------------------------
# Distinct from the merged P4-07 OperatorSafetyView
# ---------------------------------------------------------------------------


def test_view_type_is_distinct_from_operator_safety_view() -> None:
    from gmc_rebuild.runtime import OperatorSafetyView

    # Identity inequality is by construction (different types) — the value of
    # this assertion is the documented intent.
    assert DryRunOperatorView is not OperatorSafetyView  # type: ignore[comparison-overlap]
    assert DryRunOperatorView.__name__ != OperatorSafetyView.__name__
    assert DryRunOperatorView.__name__ == "DryRunOperatorView"
    assert OperatorSafetyView.__name__ == "OperatorSafetyView"


def test_operator_view_source_does_not_import_runtime() -> None:
    """Per planning §3.4 the operator-view module must not import
    ``gmc_rebuild.runtime`` (no accidental composition with the merged P4-07
    safety view absent the future implementation-time authorization).
    """
    imported = _collect_imported_modules_from_subpackage_source()
    assert not any(
        name == "gmc_rebuild.runtime" or name.startswith("gmc_rebuild.runtime.")
        for name in imported
    ), f"operator_view source unexpectedly imports gmc_rebuild.runtime: {sorted(imported)!r}"


# ---------------------------------------------------------------------------
# Inertness self-check: no forbidden runtime imports / behavior / clock read
# ---------------------------------------------------------------------------


_AUTHORIZED_IMPORT_PREFIXES: tuple[str, ...] = (
    "__future__",
    "dataclasses",
    "gmc_rebuild.decision",
    "gmc_rebuild.operator_view",
    "gmc_rebuild.portfolio_state",
    "gmc_rebuild.reporting",
    "gmc_rebuild.risk",
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


def _collect_imported_modules_from_subpackage_source() -> set[str]:
    subpackage_root = (
        Path(__file__).resolve().parents[1].parent / "src" / "gmc_rebuild" / "operator_view"
    )
    imported: set[str] = set()
    for path in sorted(subpackage_root.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
                imported.add(node.module)
    return imported


def test_operator_view_source_has_no_forbidden_runtime_imports() -> None:
    imported = _collect_imported_modules_from_subpackage_source()
    roots = {name.split(".", 1)[0] for name in imported}
    overlap = roots & _FORBIDDEN_IMPORT_ROOTS
    assert overlap == set(), (
        f"forbidden import roots present in operator_view source: {sorted(overlap)!r}"
    )


def test_operator_view_source_only_imports_from_authorized_prefixes() -> None:
    imported = _collect_imported_modules_from_subpackage_source()
    unauthorized: list[str] = []
    for name in sorted(imported):
        if not any(
            name == prefix or name.startswith(prefix + ".")
            for prefix in _AUTHORIZED_IMPORT_PREFIXES
        ):
            unauthorized.append(name)
    assert unauthorized == [], f"unauthorized imports in operator_view source: {unauthorized!r}"


def test_operator_view_source_has_no_runtime_activation_or_external_io() -> None:
    """Belt-and-suspenders substring scan for runtime-activation, I/O, and
    audit-emission patterns the import-graph test cannot catch.

    ``now_utc(``, ``datetime.now(``, ``logging.basicConfig``, and
    ``audit_event(`` are *not* substring-checked because the module
    docstrings legitimately use those tokens in backticked reassurance prose
    (matching the merged P6-05 / P6-06 test convention). The
    no-clock-read / no-audit-emission contract is instead proven by two
    stronger checks: the AST import scan above shows neither :mod:`time`,
    :mod:`gmc_rebuild.time` (the home of ``now_utc``), nor
    :mod:`gmc_rebuild.logging` (the home of ``audit_event``) is imported,
    so those callables are unreachable; and the deterministic-render tests
    confirm behaviorally that the rendered view depends only on its inputs.
    """
    subpackage_root = (
        Path(__file__).resolve().parents[1].parent / "src" / "gmc_rebuild" / "operator_view"
    )
    for path in sorted(subpackage_root.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert 'if __name__ == "__main__"' not in source, path
        assert "time.sleep(" not in source, path
        assert "asyncio.sleep(" not in source, path
        assert "socket." not in source, path
        assert "urllib" not in source, path
        assert "requests." not in source, path
        assert "open(" not in source, path
        assert "uuid." not in source, path
        assert "random." not in source, path


# ---------------------------------------------------------------------------
# Root package does not re-export the new surface
# ---------------------------------------------------------------------------


def test_gmc_rebuild_root_does_not_re_export_operator_view_surface() -> None:
    root = importlib.import_module("gmc_rebuild")
    for name in ("DryRunOperatorView", "build_dry_run_operator_view"):
        assert not hasattr(root, name), (
            f"gmc_rebuild unexpectedly re-exports {name!r}; per P6-07 the new "
            f"surface must be reachable only via gmc_rebuild.operator_view."
        )


def test_gmc_rebuild_root_all_does_not_include_operator_view_surface() -> None:
    root = importlib.import_module("gmc_rebuild")
    root_all = list(getattr(root, "__all__", ()))
    for name in ("DryRunOperatorView", "build_dry_run_operator_view"):
        assert name not in root_all


# ---------------------------------------------------------------------------
# §8 step 4a allowlist reconciliation for the new directory
# ---------------------------------------------------------------------------


def test_master_status_allowlists_operator_view_path() -> None:
    """The new ``src/gmc_rebuild/operator_view`` directory must be on the
    MASTER_STATUS.md §8 step 4a ``allowed_p2_infra`` allowlist, added in the
    same PR that introduces the directory (``MASTER_STATUS.md`` §8 step 4b)."""
    master_status = (Path(__file__).resolve().parents[1].parent / "MASTER_STATUS.md").read_text(
        encoding="utf-8"
    )
    allowlist_lines = [
        line for line in master_status.splitlines() if line.startswith("allowed_p2_infra=")
    ]
    assert allowlist_lines, "MASTER_STATUS.md must declare the §8 step 4a allowed_p2_infra gate"
    assert all("src/gmc_rebuild/operator_view" in line for line in allowlist_lines), (
        "src/gmc_rebuild/operator_view must be added to the MASTER_STATUS.md §8 step 4a "
        "allowed_p2_infra allowlist in the same PR that introduces the directory"
    )
