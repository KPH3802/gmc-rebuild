"""P6-06 deterministic daily dry-run report tests.

Covers the contract authorized by
``governance/authorizations/2026-05-23_p6-06.md``:

- deterministic build and render (identical inputs + the same explicit
  timestamp produce byte-for-byte identical output);
- idempotence under repeated rendering;
- caller-supplied timestamp is required and used — no implicit clock
  fallback (``None`` is rejected) and no internal clock read;
- exact conformance to the merged P2-04 ``audit_event`` contract (closed
  ``lifecycle`` category, ``lifecycle.daily_report`` name, JSON-
  serializable fields);
- frozen / slotted / closed-shape invariants and field validation on
  :class:`DailyReport`;
- non-mutation of the supplied decisions / portfolio / status / invariant
  inputs;
- equality / identity semantics;
- composed local-pipeline integration across the P6-01..P6-05 surfaces,
  preserving the ``UNAVAILABLE`` vs ``FAILED`` reconciliation distinction;
- :mod:`ast` import-graph and substring inertness self-checks proving no
  network, persistence, runtime activation, env-var, secret, or clock
  behavior;
- root-package non-re-export of the new surface;
- §8 step 4a allowlist reconciliation evidence for ``reporting``.

Exception expectations use the in-repo ``_expect_error`` try/except helper
rather than ``pytest.raises``, matching the merged P6-NN test convention
(none of which imports ``pytest`` at module level).
"""

from __future__ import annotations

import ast
import importlib
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType

from gmc_rebuild.decision import (
    PositionDecision,
    compose_position_decision,
)
from gmc_rebuild.eligibility import EligibilityConfig, check_eligibility
from gmc_rebuild.logging import AUDIT_CATEGORIES, AuditEvent, serialize_event
from gmc_rebuild.portfolio_state import SimulatedPortfolio, apply_simulated_order_intent
from gmc_rebuild.reporting import (
    DailyReport,
    build_daily_report,
    render_daily_report_event,
)
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

_CREATED_AT = "2026-05-23T00:00:00Z"
_TS = datetime(2026, 5, 23, 12, 0, 0, tzinfo=UTC)
_REPORT_DATE = "2026-05-23"


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
        rationale="p6-06 reporting fixture rationale",
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


# ---------------------------------------------------------------------------
# DailyReport value type — shape and validation
# ---------------------------------------------------------------------------


def test_report_is_frozen_and_slotted() -> None:
    report = _sample_report()
    assert not hasattr(report, "__dict__")
    raised: Exception | None = None
    try:
        report.would_trade = 5  # type: ignore[misc]
    except FrozenInstanceError as exc:
        raised = exc
    assert isinstance(raised, FrozenInstanceError)


def test_report_has_exactly_eight_closed_fields() -> None:
    assert DailyReport.__dataclass_fields__.keys() == {
        "report_date",
        "decisions_total",
        "would_trade",
        "would_skip",
        "applied_intent_ids",
        "net_positions",
        "reconciliation_status",
        "tripped_invariants",
    }


def test_report_rejects_empty_report_date() -> None:
    exc = _expect_error(
        ValueError,
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
    assert "report_date" in str(exc)


def test_report_rejects_count_mismatch() -> None:
    exc = _expect_error(
        ValueError,
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
    assert "would_trade + would_skip" in str(exc)


def test_report_rejects_bool_count() -> None:
    exc = _expect_error(
        TypeError,
        DailyReport,
        report_date=_REPORT_DATE,
        decisions_total=True,
        would_trade=0,
        would_skip=0,
        applied_intent_ids=(),
        net_positions=(),
        reconciliation_status=ReconciliationStatus.CLEAN,
        tripped_invariants=(),
    )
    assert "decisions_total must be an int" in str(exc)


def test_report_rejects_unsorted_net_positions() -> None:
    exc = _expect_error(
        ValueError,
        DailyReport,
        report_date=_REPORT_DATE,
        decisions_total=0,
        would_trade=0,
        would_skip=0,
        applied_intent_ids=(),
        net_positions=(("SIM-B", 1), ("SIM-A", 2)),
        reconciliation_status=ReconciliationStatus.CLEAN,
        tripped_invariants=(),
    )
    assert "sorted by symbol" in str(exc)


def test_report_rejects_zero_quantity_position() -> None:
    exc = _expect_error(
        ValueError,
        DailyReport,
        report_date=_REPORT_DATE,
        decisions_total=0,
        would_trade=0,
        would_skip=0,
        applied_intent_ids=(),
        net_positions=(("SIM-A", 0),),
        reconciliation_status=ReconciliationStatus.CLEAN,
        tripped_invariants=(),
    )
    assert "non-zero" in str(exc)


def test_report_rejects_unsorted_applied_ids() -> None:
    exc = _expect_error(
        ValueError,
        DailyReport,
        report_date=_REPORT_DATE,
        decisions_total=0,
        would_trade=0,
        would_skip=0,
        applied_intent_ids=("b", "a"),
        net_positions=(),
        reconciliation_status=ReconciliationStatus.CLEAN,
        tripped_invariants=(),
    )
    assert "sorted ascending" in str(exc)


def test_report_rejects_non_reconciliation_status() -> None:
    exc = _expect_error(
        TypeError,
        DailyReport,
        report_date=_REPORT_DATE,
        decisions_total=0,
        would_trade=0,
        would_skip=0,
        applied_intent_ids=(),
        net_positions=(),
        reconciliation_status="clean",
        tripped_invariants=(),
    )
    assert "ReconciliationStatus" in str(exc)


def test_report_is_hashable() -> None:
    assert isinstance(hash(_sample_report()), int)


# ---------------------------------------------------------------------------
# build_daily_report — counting and snapshotting
# ---------------------------------------------------------------------------


def test_build_counts_decisions_by_outcome() -> None:
    decisions = (_would_trade_decision("SIM-A"), _would_skip_decision("SIM-B"))
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=decisions,
        portfolio=SimulatedPortfolio.empty(),
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    assert report.decisions_total == 2
    assert report.would_trade == 1
    assert report.would_skip == 1


def test_build_snapshots_portfolio_positions_and_ids() -> None:
    portfolio = apply_simulated_order_intent(
        SimulatedPortfolio.empty(),
        decision=_would_trade_decision("SIM-A"),
        order_intent=_order_intent(symbol="SIM-A", quantity=10),
    )
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(_would_trade_decision("SIM-A"),),
        portfolio=portfolio,
        reconciliation_status=ReconciliationStatus.WARNING,
    )
    assert report.net_positions == (("SIM-A", 10),)
    assert report.applied_intent_ids == portfolio.applied_intent_ids
    assert report.reconciliation_status is ReconciliationStatus.WARNING


def test_build_is_deterministic() -> None:
    decisions = (_would_trade_decision("SIM-A"),)
    portfolio = SimulatedPortfolio.empty()
    first = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=decisions,
        portfolio=portfolio,
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    second = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=decisions,
        portfolio=portfolio,
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    assert first == second


def test_build_rejects_non_tuple_decisions() -> None:
    exc = _expect_error(
        TypeError,
        build_daily_report,
        report_date=_REPORT_DATE,
        decisions=[_would_trade_decision()],
        portfolio=SimulatedPortfolio.empty(),
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    assert "decisions must be a tuple" in str(exc)


def test_build_rejects_non_portfolio() -> None:
    exc = _expect_error(
        TypeError,
        build_daily_report,
        report_date=_REPORT_DATE,
        decisions=(),
        portfolio=object(),
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    assert "portfolio must be a SimulatedPortfolio" in str(exc)


def test_build_does_not_mutate_inputs() -> None:
    decisions = (_would_trade_decision("SIM-A"), _would_skip_decision("SIM-B"))
    portfolio = apply_simulated_order_intent(
        SimulatedPortfolio.empty(),
        decision=_would_trade_decision("SIM-A"),
        order_intent=_order_intent(symbol="SIM-A"),
    )
    invariants = ("INV_NONE",)
    portfolio_before = portfolio
    build_daily_report(
        report_date=_REPORT_DATE,
        decisions=decisions,
        portfolio=portfolio,
        reconciliation_status=ReconciliationStatus.CLEAN,
        tripped_invariants=invariants,
    )
    assert portfolio == portfolio_before
    assert portfolio.positions == portfolio_before.positions
    assert invariants == ("INV_NONE",)
    assert len(decisions) == 2


# ---------------------------------------------------------------------------
# render_daily_report_event — audit-contract conformance and determinism
# ---------------------------------------------------------------------------


def test_render_uses_lifecycle_category_and_name() -> None:
    event = render_daily_report_event(_sample_report(), timestamp=_TS)
    assert isinstance(event, AuditEvent)
    assert event.category == "lifecycle"
    assert event.category in AUDIT_CATEGORIES
    assert event.name == "lifecycle.daily_report"


def test_render_fields_are_json_serializable_and_deterministic() -> None:
    event = render_daily_report_event(_sample_report(), timestamp=_TS)
    first = serialize_event(event)
    second = serialize_event(render_daily_report_event(_sample_report(), timestamp=_TS))
    assert first == second
    assert '"name":"lifecycle.daily_report"' in first


def test_render_carries_report_fields() -> None:
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(_would_trade_decision("SIM-A"), _would_skip_decision("SIM-B")),
        portfolio=apply_simulated_order_intent(
            SimulatedPortfolio.empty(),
            decision=_would_trade_decision("SIM-A"),
            order_intent=_order_intent(symbol="SIM-A", quantity=10),
        ),
        reconciliation_status=ReconciliationStatus.UNAVAILABLE,
        tripped_invariants=("INV_X",),
    )
    event = render_daily_report_event(report, timestamp=_TS)
    assert event.fields["would_trade"] == 1
    assert event.fields["would_skip"] == 1
    assert event.fields["net_positions"] == {"SIM-A": 10}
    assert event.fields["reconciliation_status"] == "unavailable"
    assert event.fields["tripped_invariants"] == ["INV_X"]


def test_render_uses_caller_supplied_timestamp() -> None:
    ts_a = datetime(2026, 5, 23, 8, 0, 0, tzinfo=UTC)
    ts_b = datetime(2026, 5, 23, 20, 30, 0, tzinfo=UTC)
    event_a = render_daily_report_event(_sample_report(), timestamp=ts_a)
    event_b = render_daily_report_event(_sample_report(), timestamp=ts_b)
    assert event_a.timestamp != event_b.timestamp
    # Same explicit timestamp -> identical rendered timestamp (deterministic).
    again = render_daily_report_event(_sample_report(), timestamp=ts_a)
    assert event_a.timestamp == again.timestamp


def test_render_rejects_none_timestamp() -> None:
    exc = _expect_error(ValueError, render_daily_report_event, _sample_report(), timestamp=None)
    assert "explicit caller-supplied timestamp" in str(exc)


def test_render_rejects_non_datetime_timestamp() -> None:
    exc = _expect_error(
        TypeError, render_daily_report_event, _sample_report(), timestamp="2026-05-23"
    )
    assert "timestamp must be a datetime" in str(exc)


def test_render_rejects_non_report() -> None:
    exc = _expect_error(TypeError, render_daily_report_event, object(), timestamp=_TS)
    assert "report must be a DailyReport" in str(exc)


def test_render_does_not_mutate_report() -> None:
    report = _sample_report()
    before = (report.report_date, report.would_trade, report.net_positions)
    render_daily_report_event(report, timestamp=_TS)
    assert (report.report_date, report.would_trade, report.net_positions) == before


# ---------------------------------------------------------------------------
# Equality / identity semantics
# ---------------------------------------------------------------------------


def test_structurally_equal_reports_compare_equal() -> None:
    assert _sample_report() == _sample_report()


def test_distinct_reports_compare_unequal() -> None:
    other = DailyReport(
        report_date=_REPORT_DATE,
        decisions_total=2,
        would_trade=2,
        would_skip=0,
        applied_intent_ids=("simoi-aaa",),
        net_positions=(("SIM-A", 10),),
        reconciliation_status=ReconciliationStatus.CLEAN,
        tripped_invariants=(),
    )
    assert _sample_report() != other


# ---------------------------------------------------------------------------
# Composed local-pipeline integration (P6-01 .. P6-05)
# ---------------------------------------------------------------------------


def test_composed_pipeline_summarizes_cycle() -> None:
    # Two decisions: one would-trade (applied) and one would-skip.
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
    assert report.would_trade == 1
    assert report.would_skip == 1
    assert report.net_positions == (("SIM-A", 25),)
    assert report.applied_intent_ids == (order_intent.intent_id,)

    event = render_daily_report_event(report, timestamp=_TS)
    assert event.fields["net_positions"] == {"SIM-A": 25}


def test_composed_pipeline_preserves_unavailable_vs_failed() -> None:
    decisions = (_would_trade_decision("SIM-A"),)
    portfolio = SimulatedPortfolio.empty()
    unavailable = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=decisions,
        portfolio=portfolio,
        reconciliation_status=ReconciliationStatus.UNAVAILABLE,
    )
    failed = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=decisions,
        portfolio=portfolio,
        reconciliation_status=ReconciliationStatus.FAILED,
    )
    assert unavailable.reconciliation_status is ReconciliationStatus.UNAVAILABLE
    assert failed.reconciliation_status is ReconciliationStatus.FAILED
    assert unavailable != failed


def test_empty_cycle_renders_clean_report() -> None:
    report = build_daily_report(
        report_date=_REPORT_DATE,
        decisions=(),
        portfolio=SimulatedPortfolio.empty(),
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    assert report.decisions_total == 0
    assert report.net_positions == ()
    event = render_daily_report_event(report, timestamp=_TS)
    assert event.fields["decisions_total"] == 0


# ---------------------------------------------------------------------------
# Inertness self-check: no forbidden runtime imports / behavior / clock read
# ---------------------------------------------------------------------------


_AUTHORIZED_IMPORT_PREFIXES: tuple[str, ...] = (
    "__future__",
    "dataclasses",
    "datetime",  # stdlib datetime type for the caller-supplied timestamp only
    "gmc_rebuild.decision",
    "gmc_rebuild.logging",
    "gmc_rebuild.portfolio_state",
    "gmc_rebuild.reporting",
    "gmc_rebuild.risk",
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
    }
)


def _collect_imported_modules_from_subpackage_source() -> set[str]:
    subpackage_root = (
        Path(__file__).resolve().parents[1].parent / "src" / "gmc_rebuild" / "reporting"
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


def test_reporting_source_has_no_forbidden_runtime_imports() -> None:
    imported = _collect_imported_modules_from_subpackage_source()
    roots = {name.split(".", 1)[0] for name in imported}
    overlap = roots & _FORBIDDEN_IMPORT_ROOTS
    assert overlap == set(), (
        f"forbidden import roots present in reporting source: {sorted(overlap)!r}"
    )


def test_reporting_source_only_imports_from_authorized_prefixes() -> None:
    imported = _collect_imported_modules_from_subpackage_source()
    unauthorized: list[str] = []
    for name in sorted(imported):
        if not any(
            name == prefix or name.startswith(prefix + ".")
            for prefix in _AUTHORIZED_IMPORT_PREFIXES
        ):
            unauthorized.append(name)
    assert unauthorized == [], f"unauthorized imports in reporting source: {unauthorized!r}"


def test_reporting_source_has_no_runtime_activation_or_external_io() -> None:
    """Belt-and-suspenders substring scan for runtime-activation and I/O
    patterns the import-graph test cannot catch.

    ``now_utc(``, ``datetime.now(``, and ``logging.basicConfig`` are *not*
    substring-checked because the module docstrings legitimately use those
    tokens in backticked reassurance prose (the same exception the merged
    P6-05 test makes for ``os.environ`` / ``os.getenv``). The
    caller-supplied-timestamp / no-clock-read contract is instead proven by
    two stronger checks: the AST import scan above shows neither
    :mod:`time` nor :mod:`gmc_rebuild.time` (the home of ``now_utc``) is
    imported, so ``now_utc`` is unreachable; and
    :func:`test_render_uses_caller_supplied_timestamp` proves behaviorally
    that the rendered event timestamp tracks the explicit caller timestamp
    rather than the wall clock.
    """
    subpackage_root = (
        Path(__file__).resolve().parents[1].parent / "src" / "gmc_rebuild" / "reporting"
    )
    for path in sorted(subpackage_root.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert 'if __name__ == "__main__"' not in source, path
        assert "time.sleep(" not in source, path
        assert "socket." not in source, path
        assert "urllib" not in source, path
        assert "requests." not in source, path
        assert "open(" not in source, path


# ---------------------------------------------------------------------------
# Root package does not re-export the new surface
# ---------------------------------------------------------------------------


def test_gmc_rebuild_root_does_not_re_export_reporting_surface() -> None:
    root = importlib.import_module("gmc_rebuild")
    for name in ("DailyReport", "build_daily_report", "render_daily_report_event"):
        assert not hasattr(root, name), (
            f"gmc_rebuild unexpectedly re-exports {name!r}; per P6-06 the new "
            f"surface must be reachable only via gmc_rebuild.reporting."
        )


def test_gmc_rebuild_root_all_does_not_include_reporting_surface() -> None:
    root = importlib.import_module("gmc_rebuild")
    root_all = list(getattr(root, "__all__", ()))
    for name in ("DailyReport", "build_daily_report", "render_daily_report_event"):
        assert name not in root_all


# ---------------------------------------------------------------------------
# §8 step 4a allowlist reconciliation for the new directory
# ---------------------------------------------------------------------------


def test_master_status_allowlists_reporting_path() -> None:
    """The new ``src/gmc_rebuild/reporting`` directory must be on the
    MASTER_STATUS.md §8 step 4a ``allowed_p2_infra`` allowlist, added in the
    same PR that introduces the directory (``MASTER_STATUS.md`` §8 step 4b)."""
    master_status = (Path(__file__).resolve().parents[1].parent / "MASTER_STATUS.md").read_text(
        encoding="utf-8"
    )
    allowlist_lines = [
        line for line in master_status.splitlines() if line.startswith("allowed_p2_infra=")
    ]
    assert allowlist_lines, "MASTER_STATUS.md must declare the §8 step 4a allowed_p2_infra gate"
    assert all("src/gmc_rebuild/reporting" in line for line in allowlist_lines), (
        "src/gmc_rebuild/reporting must be added to the MASTER_STATUS.md §8 step 4a "
        "allowed_p2_infra allowlist in the same PR that introduces the directory"
    )
