"""P6-05 deterministic in-memory simulated portfolio state tests.

Covers the contract authorized by
``governance/authorizations/2026-05-22_p6-05.md``:

- deterministic state transition under the fixture-only full-fill model;
- idempotent duplicate-intent handling keyed on the deterministic P6-04
  simulated order intent ID;
- non-mutation of the prior snapshot and of the supplied decision /
  order intent;
- frozen / slotted / canonical-shape, equality, hashability, and
  identity semantics on the snapshot value types;
- non-accepted (would-skip) and unsupported (wrong-type) input handling;
- composed local-pipeline integration across the P6-01 signal-intake,
  P6-02 eligibility, P6-03 decision, and P5-02 / P6-04 simulated order
  intent surfaces;
- :mod:`ast` import-graph and substring inertness self-checks proving no
  network, persistence, runtime activation, env-var, or secret behavior;
- root-package non-re-export of the new surface;
- §8 step 4a allowlist reconciliation evidence for ``portfolio_state``
  (whose name carries the forbidden ``portfolio`` token, allowlisted per
  the P6-01 ``signal_intake`` precedent).

Exception expectations use the in-repo ``_expect_error`` try/except
helper rather than ``pytest.raises``, matching the convention of the
merged P6-01 / P6-02 / P6-03 test modules (none of which imports
``pytest`` at module level).
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
    PositionDecisionOutcome,
    PositionDecisionReason,
    compose_position_decision,
)
from gmc_rebuild.eligibility import EligibilityConfig, check_eligibility
from gmc_rebuild.portfolio_state import (
    SimulatedPortfolio,
    SimulatedPosition,
    apply_simulated_order_intent,
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

_CREATED_AT = "2026-05-22T00:00:00Z"


def _expect_error(
    exc_type: type[BaseException],
    fn: Callable[..., object],
    *args: object,
    **kwargs: object,
) -> BaseException:
    """Call ``fn`` and assert it raises ``exc_type``; return the exception.

    In-repo equivalent of ``pytest.raises``; keeps this module free of a
    ``pytest`` import, matching the merged P6-NN test convention.
    """
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
        rationale="p6-05 portfolio-state fixture rationale",
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
    order_type: SimulatedOrderType = SimulatedOrderType.MARKET,
    limit_price: float | None = None,
    time_in_force: SimulatedOrderTimeInForce = SimulatedOrderTimeInForce.DAY,
    created_at: str = _CREATED_AT,
) -> SimulatedOrderIntent:
    """Build a SimulatedOrderIntent whose intent_id is the deterministic P6-04 ID."""
    intent_id = derive_simulated_order_intent_id(
        lane=SimulationLane.LOCAL_ONLY,
        symbol=symbol,
        side=side,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit_price,
        time_in_force=time_in_force,
        created_at=created_at,
    )
    return SimulatedOrderIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id=intent_id,
        created_at=created_at,
        symbol=symbol,
        side=side,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit_price,
        time_in_force=time_in_force,
    )


# ---------------------------------------------------------------------------
# SimulatedPosition value type
# ---------------------------------------------------------------------------


def test_position_is_frozen_and_slotted() -> None:
    position = SimulatedPosition(symbol="SIM-A", net_quantity=5)
    assert not hasattr(position, "__dict__")
    raised: Exception | None = None
    try:
        position.net_quantity = 9  # type: ignore[misc]
    except FrozenInstanceError as exc:
        raised = exc
    assert isinstance(raised, FrozenInstanceError)


def test_position_rejects_empty_symbol() -> None:
    exc = _expect_error(ValueError, SimulatedPosition, symbol="", net_quantity=5)
    assert "non-empty str" in str(exc)


def test_position_rejects_whitespace_symbol() -> None:
    exc = _expect_error(ValueError, SimulatedPosition, symbol="SIM A", net_quantity=5)
    assert "whitespace" in str(exc)


def test_position_rejects_zero_quantity() -> None:
    exc = _expect_error(ValueError, SimulatedPosition, symbol="SIM-A", net_quantity=0)
    assert "non-zero" in str(exc)


def test_position_rejects_bool_quantity() -> None:
    exc = _expect_error(TypeError, SimulatedPosition, symbol="SIM-A", net_quantity=True)
    assert "net_quantity must be an int" in str(exc)


def test_position_allows_negative_quantity() -> None:
    position = SimulatedPosition(symbol="SIM-A", net_quantity=-3)
    assert position.net_quantity == -3


# ---------------------------------------------------------------------------
# SimulatedPortfolio value type
# ---------------------------------------------------------------------------


def test_portfolio_is_frozen_and_slotted() -> None:
    portfolio = SimulatedPortfolio.empty()
    assert not hasattr(portfolio, "__dict__")
    raised: Exception | None = None
    try:
        portfolio.positions = ()  # type: ignore[misc]
    except FrozenInstanceError as exc:
        raised = exc
    assert isinstance(raised, FrozenInstanceError)


def test_empty_portfolio_has_no_positions_or_applied_ids() -> None:
    portfolio = SimulatedPortfolio.empty()
    assert portfolio.positions == ()
    assert portfolio.applied_intent_ids == ()
    assert portfolio.net_quantity("SIM-A") == 0
    assert portfolio.has_applied("anything") is False


def test_portfolio_rejects_duplicate_symbols() -> None:
    exc = _expect_error(
        ValueError,
        SimulatedPortfolio,
        positions=(
            SimulatedPosition(symbol="SIM-A", net_quantity=1),
            SimulatedPosition(symbol="SIM-A", net_quantity=2),
        ),
        applied_intent_ids=(),
    )
    assert "unique symbols" in str(exc)


def test_portfolio_rejects_unsorted_positions() -> None:
    exc = _expect_error(
        ValueError,
        SimulatedPortfolio,
        positions=(
            SimulatedPosition(symbol="SIM-B", net_quantity=1),
            SimulatedPosition(symbol="SIM-A", net_quantity=2),
        ),
        applied_intent_ids=(),
    )
    assert "sorted by symbol" in str(exc)


def test_portfolio_rejects_unsorted_applied_ids() -> None:
    exc = _expect_error(
        ValueError, SimulatedPortfolio, positions=(), applied_intent_ids=("b", "a")
    )
    assert "sorted ascending" in str(exc)


def test_portfolio_rejects_duplicate_applied_ids() -> None:
    exc = _expect_error(
        ValueError, SimulatedPortfolio, positions=(), applied_intent_ids=("a", "a")
    )
    assert "unique" in str(exc)


def test_portfolio_is_hashable() -> None:
    portfolio = apply_simulated_order_intent(
        SimulatedPortfolio.empty(),
        decision=_would_trade_decision(),
        order_intent=_order_intent(),
    )
    assert isinstance(hash(portfolio), int)


# ---------------------------------------------------------------------------
# Deterministic state transition
# ---------------------------------------------------------------------------


def test_buy_increases_net_quantity() -> None:
    result = apply_simulated_order_intent(
        SimulatedPortfolio.empty(),
        decision=_would_trade_decision(),
        order_intent=_order_intent(side=SimulatedOrderSide.BUY, quantity=10),
    )
    assert result.net_quantity("SIM-A") == 10


def test_sell_decreases_net_quantity() -> None:
    result = apply_simulated_order_intent(
        SimulatedPortfolio.empty(),
        decision=_would_trade_decision(),
        order_intent=_order_intent(side=SimulatedOrderSide.SELL, quantity=4),
    )
    assert result.net_quantity("SIM-A") == -4


def test_apply_is_deterministic_for_identical_inputs() -> None:
    decision = _would_trade_decision()
    order_intent = _order_intent()
    first = apply_simulated_order_intent(
        SimulatedPortfolio.empty(), decision=decision, order_intent=order_intent
    )
    second = apply_simulated_order_intent(
        SimulatedPortfolio.empty(), decision=decision, order_intent=order_intent
    )
    assert first == second


def test_position_netting_to_zero_drops_symbol() -> None:
    portfolio = apply_simulated_order_intent(
        SimulatedPortfolio.empty(),
        decision=_would_trade_decision(),
        order_intent=_order_intent(side=SimulatedOrderSide.BUY, quantity=10),
    )
    # A distinct intent (different created_at -> different deterministic ID)
    # that sells the full 10 nets the symbol to zero.
    flat = apply_simulated_order_intent(
        portfolio,
        decision=_would_trade_decision(),
        order_intent=_order_intent(
            side=SimulatedOrderSide.SELL,
            quantity=10,
            created_at="2026-05-22T01:00:00Z",
        ),
    )
    assert flat.net_quantity("SIM-A") == 0
    assert all(p.symbol != "SIM-A" for p in flat.positions)
    assert len(flat.applied_intent_ids) == 2


def test_multiple_symbols_are_kept_sorted() -> None:
    portfolio = SimulatedPortfolio.empty()
    portfolio = apply_simulated_order_intent(
        portfolio,
        decision=_would_trade_decision("SIM-B"),
        order_intent=_order_intent(symbol="SIM-B"),
    )
    portfolio = apply_simulated_order_intent(
        portfolio,
        decision=_would_trade_decision("SIM-A"),
        order_intent=_order_intent(symbol="SIM-A"),
    )
    assert [p.symbol for p in portfolio.positions] == ["SIM-A", "SIM-B"]


# ---------------------------------------------------------------------------
# Idempotent duplicate-intent handling
# ---------------------------------------------------------------------------


def test_duplicate_intent_id_is_not_double_applied() -> None:
    decision = _would_trade_decision()
    order_intent = _order_intent(quantity=10)
    once = apply_simulated_order_intent(
        SimulatedPortfolio.empty(), decision=decision, order_intent=order_intent
    )
    twice = apply_simulated_order_intent(once, decision=decision, order_intent=order_intent)
    assert twice.net_quantity("SIM-A") == 10
    assert twice.applied_intent_ids == once.applied_intent_ids


def test_duplicate_application_returns_prior_snapshot_by_identity() -> None:
    decision = _would_trade_decision()
    order_intent = _order_intent()
    once = apply_simulated_order_intent(
        SimulatedPortfolio.empty(), decision=decision, order_intent=order_intent
    )
    twice = apply_simulated_order_intent(once, decision=decision, order_intent=order_intent)
    assert twice is once


def test_idempotent_across_many_repeats() -> None:
    decision = _would_trade_decision()
    order_intent = _order_intent(quantity=7)
    portfolio = SimulatedPortfolio.empty()
    for _ in range(5):
        portfolio = apply_simulated_order_intent(
            portfolio, decision=decision, order_intent=order_intent
        )
    assert portfolio.net_quantity("SIM-A") == 7
    assert portfolio.applied_intent_ids == (order_intent.intent_id,)


# ---------------------------------------------------------------------------
# Non-mutation of prior state and inputs
# ---------------------------------------------------------------------------


def test_prior_snapshot_is_not_mutated() -> None:
    prior = SimulatedPortfolio.empty()
    apply_simulated_order_intent(
        prior, decision=_would_trade_decision(), order_intent=_order_intent()
    )
    assert prior == SimulatedPortfolio.empty()
    assert prior.positions == ()
    assert prior.applied_intent_ids == ()


def test_apply_returns_new_snapshot_on_change() -> None:
    prior = SimulatedPortfolio.empty()
    result = apply_simulated_order_intent(
        prior, decision=_would_trade_decision(), order_intent=_order_intent()
    )
    assert result is not prior


def test_inputs_are_not_mutated() -> None:
    decision = _would_trade_decision()
    order_intent = _order_intent()
    decision_before = (decision.outcome, decision.reasons, decision.intent_id)
    intent_before = (
        order_intent.intent_id,
        order_intent.symbol,
        order_intent.side,
        order_intent.quantity,
    )
    apply_simulated_order_intent(
        SimulatedPortfolio.empty(), decision=decision, order_intent=order_intent
    )
    assert (decision.outcome, decision.reasons, decision.intent_id) == decision_before
    assert (
        order_intent.intent_id,
        order_intent.symbol,
        order_intent.side,
        order_intent.quantity,
    ) == intent_before


# ---------------------------------------------------------------------------
# Equality / identity semantics
# ---------------------------------------------------------------------------


def test_structurally_equal_snapshots_compare_equal() -> None:
    decision = _would_trade_decision()
    order_intent = _order_intent()
    a = apply_simulated_order_intent(
        SimulatedPortfolio.empty(), decision=decision, order_intent=order_intent
    )
    b = apply_simulated_order_intent(
        SimulatedPortfolio.empty(), decision=decision, order_intent=order_intent
    )
    assert a == b
    assert a is not b


def test_distinct_snapshots_compare_unequal() -> None:
    buy = apply_simulated_order_intent(
        SimulatedPortfolio.empty(),
        decision=_would_trade_decision(),
        order_intent=_order_intent(side=SimulatedOrderSide.BUY, quantity=10),
    )
    sell = apply_simulated_order_intent(
        SimulatedPortfolio.empty(),
        decision=_would_trade_decision(),
        order_intent=_order_intent(side=SimulatedOrderSide.SELL, quantity=10),
    )
    assert buy != sell


# ---------------------------------------------------------------------------
# Non-accepted and unsupported input handling
# ---------------------------------------------------------------------------


def test_would_skip_decision_is_a_noop() -> None:
    prior = SimulatedPortfolio.empty()
    result = apply_simulated_order_intent(
        prior, decision=_would_skip_decision(), order_intent=_order_intent()
    )
    assert result is prior
    assert result.net_quantity("SIM-A") == 0
    assert result.applied_intent_ids == ()


def test_would_skip_does_not_record_intent_id() -> None:
    skip = _would_skip_decision()
    assert skip.outcome is PositionDecisionOutcome.WOULD_SKIP
    assert PositionDecisionReason.SAFETY_KILL_SWITCH_NOT_ARMED in skip.reasons
    result = apply_simulated_order_intent(
        SimulatedPortfolio.empty(), decision=skip, order_intent=_order_intent()
    )
    assert result.has_applied(_order_intent().intent_id) is False


def test_apply_rejects_non_portfolio() -> None:
    exc = _expect_error(
        TypeError,
        apply_simulated_order_intent,
        object(),
        decision=_would_trade_decision(),
        order_intent=_order_intent(),
    )
    assert "portfolio must be a SimulatedPortfolio" in str(exc)


def test_apply_rejects_non_decision() -> None:
    exc = _expect_error(
        TypeError,
        apply_simulated_order_intent,
        SimulatedPortfolio.empty(),
        decision=object(),
        order_intent=_order_intent(),
    )
    assert "decision must be a PositionDecision" in str(exc)


def test_apply_rejects_non_order_intent() -> None:
    exc = _expect_error(
        TypeError,
        apply_simulated_order_intent,
        SimulatedPortfolio.empty(),
        decision=_would_trade_decision(),
        order_intent=object(),
    )
    assert "order_intent must be a SimulatedOrderIntent" in str(exc)


# ---------------------------------------------------------------------------
# Composed local-pipeline integration (P6-01 / P6-02 / P6-03 / P6-04)
# ---------------------------------------------------------------------------


def test_composed_pipeline_would_trade_applies_position() -> None:
    # P6-01 signal -> P6-02 eligibility -> P4-06 verdict -> P6-03 decision
    signal = _signal("SIM-A")
    eligibility = check_eligibility(signal, _config())
    verdict = _clear_verdict()
    decision = compose_position_decision(signal, eligibility, verdict)
    assert decision.outcome is PositionDecisionOutcome.WOULD_TRADE

    # P6-04 order intent with its deterministic identity -> P6-05 apply
    order_intent = _order_intent(symbol="SIM-A", side=SimulatedOrderSide.BUY, quantity=25)
    portfolio = apply_simulated_order_intent(
        SimulatedPortfolio.empty(), decision=decision, order_intent=order_intent
    )
    assert portfolio.net_quantity("SIM-A") == 25
    assert portfolio.applied_intent_ids == (order_intent.intent_id,)


def test_composed_pipeline_would_skip_leaves_portfolio_flat() -> None:
    signal = _signal("SIM-A")
    eligibility = check_eligibility(signal, _config())
    decision = compose_position_decision(signal, eligibility, _blocked_verdict())
    assert decision.outcome is PositionDecisionOutcome.WOULD_SKIP

    order_intent = _order_intent(symbol="SIM-A")
    portfolio = apply_simulated_order_intent(
        SimulatedPortfolio.empty(), decision=decision, order_intent=order_intent
    )
    assert portfolio == SimulatedPortfolio.empty()


def test_composed_pipeline_ineligible_signal_skips() -> None:
    # Symbol not in the allowed set -> ineligible -> would-skip -> no-op.
    signal = _signal("UNAUTHORIZED")
    eligibility = check_eligibility(signal, _config())
    decision = compose_position_decision(signal, eligibility, _clear_verdict())
    assert decision.outcome is PositionDecisionOutcome.WOULD_SKIP
    assert PositionDecisionReason.ELIGIBILITY_INELIGIBLE in decision.reasons

    order_intent = _order_intent(symbol="UNAUTHORIZED")
    portfolio = apply_simulated_order_intent(
        SimulatedPortfolio.empty(), decision=decision, order_intent=order_intent
    )
    assert portfolio == SimulatedPortfolio.empty()


# ---------------------------------------------------------------------------
# Inertness self-check: no forbidden runtime imports / behavior
# ---------------------------------------------------------------------------


_AUTHORIZED_IMPORT_PREFIXES: tuple[str, ...] = (
    "__future__",
    "dataclasses",
    "gmc_rebuild.decision",
    "gmc_rebuild.portfolio_state",
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
    }
)


def _collect_imported_modules_from_subpackage_source() -> set[str]:
    subpackage_root = (
        Path(__file__).resolve().parents[1].parent / "src" / "gmc_rebuild" / "portfolio_state"
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


def test_portfolio_state_source_has_no_forbidden_runtime_imports() -> None:
    imported = _collect_imported_modules_from_subpackage_source()
    roots = {name.split(".", 1)[0] for name in imported}
    overlap = roots & _FORBIDDEN_IMPORT_ROOTS
    assert overlap == set(), (
        f"forbidden import roots present in portfolio_state source: {sorted(overlap)!r}"
    )


def test_portfolio_state_source_only_imports_from_authorized_prefixes() -> None:
    imported = _collect_imported_modules_from_subpackage_source()
    unauthorized: list[str] = []
    for name in sorted(imported):
        if not any(
            name == prefix or name.startswith(prefix + ".")
            for prefix in _AUTHORIZED_IMPORT_PREFIXES
        ):
            unauthorized.append(name)
    assert unauthorized == [], f"unauthorized imports in portfolio_state source: {unauthorized!r}"


def test_portfolio_state_source_has_no_main_block_or_sleep_or_builtin_io() -> None:
    """Belt-and-suspenders substring scan for runtime-activation / I/O
    patterns the import-graph test cannot catch. ``os.environ`` / ``os.getenv``
    are not substring-checked because the module docstring legitimately uses
    those tokens in backticked reassurance prose; the AST import scan above
    already proves :mod:`os` is not imported.
    """
    subpackage_root = (
        Path(__file__).resolve().parents[1].parent / "src" / "gmc_rebuild" / "portfolio_state"
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


def test_gmc_rebuild_root_does_not_re_export_portfolio_state_surface() -> None:
    root = importlib.import_module("gmc_rebuild")
    for name in ("SimulatedPortfolio", "SimulatedPosition", "apply_simulated_order_intent"):
        assert not hasattr(root, name), (
            f"gmc_rebuild unexpectedly re-exports {name!r}; per P6-05 the new "
            f"surface must be reachable only via gmc_rebuild.portfolio_state."
        )


def test_gmc_rebuild_root_all_does_not_include_portfolio_state_surface() -> None:
    root = importlib.import_module("gmc_rebuild")
    root_all = list(getattr(root, "__all__", ()))
    for name in ("SimulatedPortfolio", "SimulatedPosition", "apply_simulated_order_intent"):
        assert name not in root_all


# ---------------------------------------------------------------------------
# §8 step 4a allowlist reconciliation for the forbidden `portfolio` token
# ---------------------------------------------------------------------------


def test_master_status_allowlists_portfolio_state_path() -> None:
    """`portfolio_state` carries the forbidden `portfolio` token, so it must be
    on the MASTER_STATUS.md §8 step 4a allowlist (P6-01 `signal_intake`
    precedent). This guards the reconciliation in-tree against the actual
    ``allowed_p2_infra`` gate line, not merely prose mentions."""
    master_status = (
        Path(__file__).resolve().parents[1].parent / "MASTER_STATUS.md"
    ).read_text(encoding="utf-8")
    allowlist_lines = [
        line for line in master_status.splitlines() if line.startswith("allowed_p2_infra=")
    ]
    assert allowlist_lines, "MASTER_STATUS.md must declare the §8 step 4a allowed_p2_infra gate"
    assert all("src/gmc_rebuild/portfolio_state" in line for line in allowlist_lines), (
        "src/gmc_rebuild/portfolio_state must be added to the MASTER_STATUS.md "
        "§8 step 4a allowed_p2_infra allowlist in the same PR that introduces "
        "the directory (P6-01 signal_intake forbidden-token precedent)"
    )
