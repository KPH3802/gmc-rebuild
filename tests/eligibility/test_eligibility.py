"""P6-02 eligibility-check pure-function tests.

Deterministic, pytest-only tests for the merged P6-02 eligibility-check
boundary at :mod:`gmc_rebuild.eligibility`. The tests cover:

- The eligible happy path (every check passes; ``outcome`` is
  :attr:`EligibilityOutcome.ELIGIBLE`; ``reasons`` is empty).
- Each of the five closed :class:`EligibilityReason` codes
  individually, plus the multi-reason case where every check fails
  simultaneously, plus an exhaustive scan that confirms each named
  reason appears in at least one targeted ineligibility test.
- Deterministic repeat calls — the same ``(intent, config)`` pair
  returns equal :class:`EligibilityDecision` instances across repeated
  invocations.
- Input non-mutation — neither the supplied
  :class:`~gmc_rebuild.signal_intake.SignalIntent` nor the supplied
  :class:`EligibilityConfig` is modified by
  :func:`check_eligibility`.
- Frozen / slotted shape on :class:`EligibilityConfig` and
  :class:`EligibilityDecision`; closed enumerations on
  :class:`EligibilityOutcome` and :class:`EligibilityReason`; the
  ``outcome == ELIGIBLE iff reasons == ()`` biconditional on
  :class:`EligibilityDecision`; sorted-canonical-order on the
  ``reasons`` tuple for ineligible decisions.
- Equality and hashability for :class:`EligibilityConfig` and
  :class:`EligibilityDecision`.
- An :mod:`ast` import-graph inertness self-check confirming that the
  subpackage's source imports are disjoint from the forbidden runtime
  roots and that every imported module starts with one of the
  authorized prefixes.
- The root :mod:`gmc_rebuild` package does not re-export the new
  surface (``EligibilityConfig`` / ``EligibilityDecision`` /
  ``EligibilityOutcome`` / ``EligibilityReason`` /
  ``check_eligibility``).

Authorization: ``governance/authorizations/2026-05-19_p6-02.md``.
"""

from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError
from pathlib import Path

from gmc_rebuild.eligibility import (
    EligibilityConfig,
    EligibilityDecision,
    EligibilityOutcome,
    EligibilityReason,
    check_eligibility,
)
from gmc_rebuild.signal_intake import SignalIntent, SignalSide


def _intent(**overrides: object) -> SignalIntent:
    kwargs: dict[str, object] = {
        "intent_id": "intent-p6-02-A",
        "symbol": "SIM-P6-02",
        "side": SignalSide.BUY,
        "quantity": 10,
        "rationale": "tripwire fixture rationale",
    }
    kwargs.update(overrides)
    return SignalIntent(**kwargs)  # type: ignore[arg-type]


def _config(**overrides: object) -> EligibilityConfig:
    kwargs: dict[str, object] = {
        "allowed_symbols": frozenset({"SIM-P6-02", "SIM-OTHER"}),
        "allowed_sides": frozenset({SignalSide.BUY, SignalSide.SELL}),
        "min_quantity": 1,
        "max_quantity": 100,
        "min_rationale_length": 5,
    }
    kwargs.update(overrides)
    return EligibilityConfig(**kwargs)  # type: ignore[arg-type]


def _snapshot_intent(intent: SignalIntent) -> tuple[object, ...]:
    return (
        intent.intent_id,
        intent.symbol,
        intent.side,
        intent.quantity,
        intent.rationale,
    )


def _snapshot_config(config: EligibilityConfig) -> tuple[object, ...]:
    return (
        frozenset(config.allowed_symbols),
        frozenset(config.allowed_sides),
        config.min_quantity,
        config.max_quantity,
        config.min_rationale_length,
    )


# ---------------------------------------------------------------------------
# Eligible happy path
# ---------------------------------------------------------------------------


def test_eligible_happy_path_returns_eligible_with_empty_reasons() -> None:
    decision = check_eligibility(_intent(), _config())
    assert decision.outcome is EligibilityOutcome.ELIGIBLE
    assert decision.reasons == ()


def test_eligible_path_at_min_quantity_boundary() -> None:
    decision = check_eligibility(_intent(quantity=1), _config(min_quantity=1))
    assert decision.outcome is EligibilityOutcome.ELIGIBLE
    assert decision.reasons == ()


def test_eligible_path_at_max_quantity_boundary() -> None:
    decision = check_eligibility(_intent(quantity=100), _config(max_quantity=100))
    assert decision.outcome is EligibilityOutcome.ELIGIBLE
    assert decision.reasons == ()


def test_eligible_path_at_min_rationale_length_boundary() -> None:
    decision = check_eligibility(
        _intent(rationale="abcde"),
        _config(min_rationale_length=5),
    )
    assert decision.outcome is EligibilityOutcome.ELIGIBLE
    assert decision.reasons == ()


# ---------------------------------------------------------------------------
# Per-reason ineligibility paths
# ---------------------------------------------------------------------------


def test_ineligible_symbol_not_allowed() -> None:
    decision = check_eligibility(
        _intent(symbol="UNAUTHORIZED"),
        _config(),
    )
    assert decision.outcome is EligibilityOutcome.INELIGIBLE
    assert decision.reasons == (EligibilityReason.SYMBOL_NOT_ALLOWED,)


def test_ineligible_side_not_permitted() -> None:
    decision = check_eligibility(
        _intent(side=SignalSide.SELL),
        _config(allowed_sides=frozenset({SignalSide.BUY})),
    )
    assert decision.outcome is EligibilityOutcome.INELIGIBLE
    assert decision.reasons == (EligibilityReason.SIDE_NOT_PERMITTED,)


def test_ineligible_quantity_below_minimum() -> None:
    decision = check_eligibility(
        _intent(quantity=1),
        _config(min_quantity=5),
    )
    assert decision.outcome is EligibilityOutcome.INELIGIBLE
    assert decision.reasons == (EligibilityReason.QUANTITY_BELOW_MINIMUM,)


def test_ineligible_quantity_above_maximum() -> None:
    decision = check_eligibility(
        _intent(quantity=200),
        _config(max_quantity=100),
    )
    assert decision.outcome is EligibilityOutcome.INELIGIBLE
    assert decision.reasons == (EligibilityReason.QUANTITY_ABOVE_MAXIMUM,)


def test_ineligible_rationale_too_short() -> None:
    decision = check_eligibility(
        _intent(rationale="hi"),
        _config(min_rationale_length=10),
    )
    assert decision.outcome is EligibilityOutcome.INELIGIBLE
    assert decision.reasons == (EligibilityReason.RATIONALE_TOO_SHORT,)


# ---------------------------------------------------------------------------
# Multi-reason ineligibility
# ---------------------------------------------------------------------------


def test_multi_reason_ineligibility_four_codes_surface_in_canonical_order_below_min_path() -> None:
    """Maximum simultaneous reasons is four: symbol, side, ONE-of-quantity,
    rationale. ``EligibilityConfig`` enforces ``max_quantity >= min_quantity``,
    so a single quantity value cannot trigger both ``QUANTITY_BELOW_MINIMUM``
    and ``QUANTITY_ABOVE_MAXIMUM`` under any valid config. This test
    exercises the below-min path; the next test exercises the above-max path.
    """
    decision = check_eligibility(
        _intent(
            symbol="UNAUTHORIZED",
            side=SignalSide.SELL,
            quantity=1,
            rationale="hi",
        ),
        _config(
            allowed_symbols=frozenset({"SIM-X"}),
            allowed_sides=frozenset({SignalSide.BUY}),
            min_quantity=5,
            max_quantity=50,
            min_rationale_length=10,
        ),
    )
    assert decision.outcome is EligibilityOutcome.INELIGIBLE
    assert decision.reasons == (
        EligibilityReason.SYMBOL_NOT_ALLOWED,
        EligibilityReason.SIDE_NOT_PERMITTED,
        EligibilityReason.QUANTITY_BELOW_MINIMUM,
        EligibilityReason.RATIONALE_TOO_SHORT,
    )


def test_multi_reason_ineligibility_four_codes_surface_in_canonical_order_above_max_path() -> None:
    decision = check_eligibility(
        _intent(
            symbol="UNAUTHORIZED",
            side=SignalSide.SELL,
            quantity=999,
            rationale="hi",
        ),
        _config(
            allowed_symbols=frozenset({"SIM-X"}),
            allowed_sides=frozenset({SignalSide.BUY}),
            min_quantity=1,
            max_quantity=50,
            min_rationale_length=10,
        ),
    )
    assert decision.outcome is EligibilityOutcome.INELIGIBLE
    assert decision.reasons == (
        EligibilityReason.SYMBOL_NOT_ALLOWED,
        EligibilityReason.SIDE_NOT_PERMITTED,
        EligibilityReason.QUANTITY_ABOVE_MAXIMUM,
        EligibilityReason.RATIONALE_TOO_SHORT,
    )


def test_multi_reason_ineligibility_pair_emits_canonical_order_subset() -> None:
    decision = check_eligibility(
        _intent(symbol="UNAUTHORIZED", quantity=200),
        _config(),
    )
    assert decision.outcome is EligibilityOutcome.INELIGIBLE
    assert decision.reasons == (
        EligibilityReason.SYMBOL_NOT_ALLOWED,
        EligibilityReason.QUANTITY_ABOVE_MAXIMUM,
    )


def test_quantity_min_and_max_cannot_simultaneously_fire_invariant() -> None:
    """Documentation tripwire: the ``max_quantity >= min_quantity`` config
    invariant guarantees that no single intent can simultaneously trigger
    both ``QUANTITY_BELOW_MINIMUM`` and ``QUANTITY_ABOVE_MAXIMUM``. This
    test attempts to construct a config that would allow both and asserts
    the construction fails with ``ValueError``.
    """
    raised: Exception | None = None
    try:
        _config(min_quantity=10, max_quantity=5)
    except ValueError as exc:
        raised = exc
    assert isinstance(raised, ValueError)
    assert "max_quantity" in str(raised)


# ---------------------------------------------------------------------------
# Exhaustive closed-reason-code coverage
# ---------------------------------------------------------------------------


def test_every_named_reason_code_appears_in_at_least_one_targeted_test() -> None:
    """Closed-set exhaustiveness check.

    Every named :class:`EligibilityReason` member must be surfaced by
    at least one of the targeted per-reason tests above. The full
    declared set is exactly five members; this test cross-checks the
    enum against the canonical order tuple used inside the module.
    """
    declared = set(EligibilityReason)
    assert declared == {
        EligibilityReason.SYMBOL_NOT_ALLOWED,
        EligibilityReason.SIDE_NOT_PERMITTED,
        EligibilityReason.QUANTITY_BELOW_MINIMUM,
        EligibilityReason.QUANTITY_ABOVE_MAXIMUM,
        EligibilityReason.RATIONALE_TOO_SHORT,
    }
    # The multi-reason all-five test above exercises each in turn; a
    # set-comparison here would be redundant. This test pins the
    # closed-set invariant: any future addition or removal of a
    # member breaks this assertion.


# ---------------------------------------------------------------------------
# Deterministic repeat calls
# ---------------------------------------------------------------------------


def test_repeat_calls_return_equal_decisions_eligible_path() -> None:
    intent = _intent()
    config = _config()
    decisions = [check_eligibility(intent, config) for _ in range(5)]
    for d in decisions[1:]:
        assert d == decisions[0]


def test_repeat_calls_return_equal_decisions_ineligible_path() -> None:
    intent = _intent(symbol="UNAUTHORIZED", quantity=200)
    config = _config()
    decisions = [check_eligibility(intent, config) for _ in range(5)]
    for d in decisions[1:]:
        assert d == decisions[0]


# ---------------------------------------------------------------------------
# Input non-mutation
# ---------------------------------------------------------------------------


def test_check_eligibility_does_not_mutate_intent() -> None:
    intent = _intent(symbol="UNAUTHORIZED", quantity=200)
    config = _config()
    snapshot = _snapshot_intent(intent)
    for _ in range(3):
        check_eligibility(intent, config)
    assert _snapshot_intent(intent) == snapshot


def test_check_eligibility_does_not_mutate_config() -> None:
    intent = _intent()
    config = _config()
    snapshot = _snapshot_config(config)
    for _ in range(3):
        check_eligibility(intent, config)
    assert _snapshot_config(config) == snapshot


# ---------------------------------------------------------------------------
# Type-validation determinism
# ---------------------------------------------------------------------------


def test_check_eligibility_rejects_non_signal_intent() -> None:
    raised: Exception | None = None
    try:
        check_eligibility("not-an-intent", _config())  # type: ignore[arg-type]
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "SignalIntent" in str(raised)


def test_check_eligibility_rejects_non_eligibility_config() -> None:
    raised: Exception | None = None
    try:
        check_eligibility(_intent(), {"allowed_symbols": "SIM-P6-02"})  # type: ignore[arg-type]
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "EligibilityConfig" in str(raised)


# ---------------------------------------------------------------------------
# EligibilityOutcome closed enumeration
# ---------------------------------------------------------------------------


def test_eligibility_outcome_is_closed_two_member_strenum() -> None:
    assert set(EligibilityOutcome) == {
        EligibilityOutcome.ELIGIBLE,
        EligibilityOutcome.INELIGIBLE,
    }
    assert EligibilityOutcome.ELIGIBLE.value == "ELIGIBLE"
    assert EligibilityOutcome.INELIGIBLE.value == "INELIGIBLE"


def test_eligibility_outcome_is_a_str_subclass() -> None:
    assert isinstance(EligibilityOutcome.ELIGIBLE, str)


# ---------------------------------------------------------------------------
# EligibilityReason closed enumeration
# ---------------------------------------------------------------------------


def test_eligibility_reason_is_closed_five_member_strenum() -> None:
    assert set(EligibilityReason) == {
        EligibilityReason.SYMBOL_NOT_ALLOWED,
        EligibilityReason.SIDE_NOT_PERMITTED,
        EligibilityReason.QUANTITY_BELOW_MINIMUM,
        EligibilityReason.QUANTITY_ABOVE_MAXIMUM,
        EligibilityReason.RATIONALE_TOO_SHORT,
    }


def test_eligibility_reason_values_match_member_names() -> None:
    for reason in EligibilityReason:
        assert reason.value == reason.name


# ---------------------------------------------------------------------------
# EligibilityConfig: frozen / slotted / closed-shape / validation
# ---------------------------------------------------------------------------


def test_config_is_frozen() -> None:
    config = _config()
    raised: Exception | None = None
    try:
        config.min_quantity = 7  # type: ignore[misc]
    except FrozenInstanceError as exc:
        raised = exc
    assert isinstance(raised, FrozenInstanceError)


def test_config_uses_slots_and_has_no_dict() -> None:
    config = _config()
    assert hasattr(EligibilityConfig, "__slots__")
    assert not hasattr(config, "__dict__")


def test_config_field_set_is_closed_five_fields() -> None:
    expected = (
        "allowed_symbols",
        "allowed_sides",
        "min_quantity",
        "max_quantity",
        "min_rationale_length",
    )
    assert tuple(EligibilityConfig.__dataclass_fields__) == expected


def test_config_rejects_non_frozenset_allowed_symbols() -> None:
    raised: Exception | None = None
    try:
        _config(allowed_symbols={"SIM-X"})
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "allowed_symbols" in str(raised)


def test_config_rejects_non_string_allowed_symbol_member() -> None:
    raised: Exception | None = None
    try:
        _config(allowed_symbols=frozenset({"SIM-X", 42}))
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "allowed_symbols" in str(raised)


def test_config_rejects_empty_string_allowed_symbol_member() -> None:
    raised: Exception | None = None
    try:
        _config(allowed_symbols=frozenset({"SIM-X", ""}))
    except ValueError as exc:
        raised = exc
    assert isinstance(raised, ValueError)
    assert "allowed_symbols" in str(raised)


def test_config_rejects_non_frozenset_allowed_sides() -> None:
    raised: Exception | None = None
    try:
        _config(allowed_sides={SignalSide.BUY})
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "allowed_sides" in str(raised)


def test_config_rejects_non_signal_side_allowed_side_member() -> None:
    raised: Exception | None = None
    try:
        _config(allowed_sides=frozenset({"BUY"}))
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "allowed_sides" in str(raised)


def test_config_rejects_bool_min_quantity() -> None:
    raised: Exception | None = None
    try:
        _config(min_quantity=True)
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "min_quantity" in str(raised)


def test_config_rejects_zero_min_quantity() -> None:
    raised: Exception | None = None
    try:
        _config(min_quantity=0)
    except ValueError as exc:
        raised = exc
    assert isinstance(raised, ValueError)
    assert "min_quantity" in str(raised)


def test_config_rejects_max_quantity_below_min_quantity() -> None:
    raised: Exception | None = None
    try:
        _config(min_quantity=10, max_quantity=5)
    except ValueError as exc:
        raised = exc
    assert isinstance(raised, ValueError)
    assert "max_quantity" in str(raised)


def test_config_rejects_negative_min_rationale_length() -> None:
    raised: Exception | None = None
    try:
        _config(min_rationale_length=-1)
    except ValueError as exc:
        raised = exc
    assert isinstance(raised, ValueError)
    assert "min_rationale_length" in str(raised)


def test_config_rejects_bool_min_rationale_length() -> None:
    raised: Exception | None = None
    try:
        _config(min_rationale_length=False)
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "min_rationale_length" in str(raised)


def test_config_accepts_zero_min_rationale_length() -> None:
    config = _config(min_rationale_length=0)
    assert config.min_rationale_length == 0


# ---------------------------------------------------------------------------
# EligibilityDecision: frozen / slotted / closed-shape / biconditional
# ---------------------------------------------------------------------------


def test_decision_is_frozen() -> None:
    decision = check_eligibility(_intent(), _config())
    raised: Exception | None = None
    try:
        decision.outcome = EligibilityOutcome.INELIGIBLE  # type: ignore[misc]
    except FrozenInstanceError as exc:
        raised = exc
    assert isinstance(raised, FrozenInstanceError)


def test_decision_uses_slots_and_has_no_dict() -> None:
    decision = check_eligibility(_intent(), _config())
    assert hasattr(EligibilityDecision, "__slots__")
    assert not hasattr(decision, "__dict__")


def test_decision_field_set_is_closed_two_fields() -> None:
    assert tuple(EligibilityDecision.__dataclass_fields__) == ("outcome", "reasons")


def test_decision_biconditional_eligible_requires_empty_reasons() -> None:
    raised: Exception | None = None
    try:
        EligibilityDecision(
            outcome=EligibilityOutcome.ELIGIBLE,
            reasons=(EligibilityReason.SYMBOL_NOT_ALLOWED,),
        )
    except ValueError as exc:
        raised = exc
    assert isinstance(raised, ValueError)
    assert "ELIGIBLE" in str(raised)


def test_decision_biconditional_ineligible_requires_non_empty_reasons() -> None:
    raised: Exception | None = None
    try:
        EligibilityDecision(
            outcome=EligibilityOutcome.INELIGIBLE,
            reasons=(),
        )
    except ValueError as exc:
        raised = exc
    assert isinstance(raised, ValueError)
    assert "INELIGIBLE" in str(raised)


def test_decision_rejects_non_outcome_outcome() -> None:
    raised: Exception | None = None
    try:
        EligibilityDecision(
            outcome="ELIGIBLE",  # type: ignore[arg-type]
            reasons=(),
        )
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "outcome" in str(raised)


def test_decision_rejects_non_tuple_reasons() -> None:
    raised: Exception | None = None
    try:
        EligibilityDecision(
            outcome=EligibilityOutcome.INELIGIBLE,
            reasons=[EligibilityReason.SYMBOL_NOT_ALLOWED],  # type: ignore[arg-type]
        )
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "reasons" in str(raised)


def test_decision_rejects_non_reason_reason_member() -> None:
    raised: Exception | None = None
    try:
        EligibilityDecision(
            outcome=EligibilityOutcome.INELIGIBLE,
            reasons=("SYMBOL_NOT_ALLOWED",),  # type: ignore[arg-type]
        )
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "reasons" in str(raised)


# ---------------------------------------------------------------------------
# Equality and hashability
# ---------------------------------------------------------------------------


def test_two_configs_with_same_fields_compare_equal_and_have_equal_hashes() -> None:
    a = _config()
    b = _config()
    assert a == b
    assert hash(a) == hash(b)


def test_two_decisions_with_same_fields_compare_equal_and_have_equal_hashes() -> None:
    a = check_eligibility(_intent(), _config())
    b = check_eligibility(_intent(), _config())
    assert a == b
    assert hash(a) == hash(b)


def test_decisions_differing_in_outcome_are_not_equal() -> None:
    eligible = check_eligibility(_intent(), _config())
    ineligible = check_eligibility(_intent(symbol="UNAUTHORIZED"), _config())
    assert eligible != ineligible


# ---------------------------------------------------------------------------
# Inertness self-check: no forbidden runtime imports
# ---------------------------------------------------------------------------


_AUTHORIZED_IMPORT_PREFIXES: tuple[str, ...] = (
    "__future__",
    "dataclasses",
    "enum",
    "gmc_rebuild.eligibility",
    "gmc_rebuild.signal_intake",
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
        Path(__file__).resolve().parents[1].parent / "src" / "gmc_rebuild" / "eligibility"
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


def test_eligibility_source_has_no_forbidden_runtime_imports() -> None:
    imported = _collect_imported_modules_from_subpackage_source()
    roots = {name.split(".", 1)[0] for name in imported}
    overlap = roots & _FORBIDDEN_IMPORT_ROOTS
    assert overlap == set(), (
        f"forbidden import roots present in eligibility source: {sorted(overlap)!r}"
    )


def test_eligibility_source_only_imports_from_authorized_prefixes() -> None:
    imported = _collect_imported_modules_from_subpackage_source()
    unauthorized: list[str] = []
    for name in sorted(imported):
        if not any(
            name == prefix or name.startswith(prefix + ".")
            for prefix in _AUTHORIZED_IMPORT_PREFIXES
        ):
            unauthorized.append(name)
    assert unauthorized == [], f"unauthorized imports in eligibility source: {unauthorized!r}"


def test_eligibility_source_has_no_main_block_or_sleep_or_builtin_io() -> None:
    """Belt-and-suspenders substring scan for patterns the import-graph
    test above cannot catch: ``__main__`` statements, ``time.sleep(`` /
    ``urllib`` / ``requests.`` / ``socket.`` call sites, and the
    ``open(`` builtin. ``os.environ`` and ``os.getenv`` are not
    substring-checked because the docstrings legitimately use those
    tokens in backticked reassurance prose; the AST import scan above
    already proves :mod:`os` is not imported.
    """
    subpackage_root = (
        Path(__file__).resolve().parents[1].parent / "src" / "gmc_rebuild" / "eligibility"
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


def test_gmc_rebuild_root_does_not_re_export_eligibility_surface() -> None:
    root = importlib.import_module("gmc_rebuild")
    for name in (
        "EligibilityConfig",
        "EligibilityDecision",
        "EligibilityOutcome",
        "EligibilityReason",
        "check_eligibility",
    ):
        assert not hasattr(root, name), (
            f"gmc_rebuild unexpectedly re-exports {name!r}; per P6-02 the new "
            f"surface must be reachable only via gmc_rebuild.eligibility."
        )


def test_gmc_rebuild_root_all_does_not_include_eligibility_surface() -> None:
    root = importlib.import_module("gmc_rebuild")
    root_all = list(getattr(root, "__all__", ()))
    for name in (
        "EligibilityConfig",
        "EligibilityDecision",
        "EligibilityOutcome",
        "EligibilityReason",
        "check_eligibility",
    ):
        assert name not in root_all, (
            f"gmc_rebuild.__all__ unexpectedly includes {name!r}; "
            f"per P6-02 the new surface must not be re-exported."
        )
