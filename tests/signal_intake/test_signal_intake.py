"""P6-01 typed signal-intake boundary tests.

Deterministic, pytest-only tests for the merged P6-01 typed signal-intake
boundary at :mod:`gmc_rebuild.signal_intake`. The tests cover:

- Successful construction of :class:`SignalIntent` and identity-return
  from :func:`accept_signal_intent`.
- Frozen / immutable behavior on the dataclass.
- ``__slots__`` shape and exact five-field closed surface.
- Closed :class:`SignalSide` enumeration (``BUY`` and ``SELL`` only).
- Validation failures for invalid ``intent_id`` / ``symbol`` / ``side`` /
  ``quantity`` / ``rationale`` values, including the ``bool``-rejected-
  as-quantity edge case.
- Equality and hashability under value semantics.
- An :mod:`ast` import-graph inertness self-check confirming that the
  subpackage's source imports are disjoint from the forbidden runtime
  roots and that every imported module starts with one of the
  authorized prefixes.
- The root :mod:`gmc_rebuild` package does not re-export the new
  :class:`SignalIntent` / :class:`SignalSide` / :func:`accept_signal_intent`
  surface, preserving the P3 / P4 / P5 pattern that subpackage public
  surfaces are reachable only through ``from gmc_rebuild.<subpackage>``.

Authorization: ``governance/authorizations/2026-05-19_p6-01.md``.
"""

from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError
from pathlib import Path

from gmc_rebuild.signal_intake import SignalIntent, SignalSide, accept_signal_intent

_VALID_KWARGS: dict[str, object] = {
    "intent_id": "intent-p6-01-A",
    "symbol": "SIM-P6-01",
    "side": SignalSide.BUY,
    "quantity": 10,
    "rationale": "tripwire fixture rationale",
}


def _build(**overrides: object) -> SignalIntent:
    kwargs: dict[str, object] = dict(_VALID_KWARGS)
    kwargs.update(overrides)
    return SignalIntent(**kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Construction and identity-return
# ---------------------------------------------------------------------------


def test_construct_with_valid_fields_succeeds() -> None:
    intent = _build()
    assert intent.intent_id == "intent-p6-01-A"
    assert intent.symbol == "SIM-P6-01"
    assert intent.side is SignalSide.BUY
    assert intent.quantity == 10
    assert intent.rationale == "tripwire fixture rationale"


def test_accept_returns_supplied_intent_by_identity() -> None:
    intent = _build()
    returned = accept_signal_intent(intent)
    assert returned is intent


def test_accept_rejects_non_signal_intent_with_type_error() -> None:
    raised: Exception | None = None
    try:
        accept_signal_intent("not-an-intent")  # type: ignore[arg-type]
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "SignalIntent" in str(raised)


def test_accept_rejects_dict_with_type_error() -> None:
    raised: Exception | None = None
    try:
        accept_signal_intent(dict(_VALID_KWARGS))  # type: ignore[arg-type]
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "SignalIntent" in str(raised)


# ---------------------------------------------------------------------------
# Frozen / slotted / shape invariants
# ---------------------------------------------------------------------------


def test_intent_is_frozen() -> None:
    intent = _build()
    raised: Exception | None = None
    try:
        intent.symbol = "OTHER"  # type: ignore[misc]
    except FrozenInstanceError as exc:
        raised = exc
    assert isinstance(raised, FrozenInstanceError)


def test_intent_uses_slots_and_has_no_dict() -> None:
    intent = _build()
    assert hasattr(SignalIntent, "__slots__")
    assert not hasattr(intent, "__dict__")


def test_intent_field_set_is_closed_five_fields() -> None:
    expected = ("intent_id", "symbol", "side", "quantity", "rationale")
    assert tuple(SignalIntent.__dataclass_fields__) == expected


def test_intent_field_types_are_declared_as_expected() -> None:
    fields = SignalIntent.__dataclass_fields__
    assert fields["intent_id"].type == "str"
    assert fields["symbol"].type == "str"
    assert fields["side"].type == "SignalSide"
    assert fields["quantity"].type == "int"
    assert fields["rationale"].type == "str"


# ---------------------------------------------------------------------------
# SignalSide closed enumeration
# ---------------------------------------------------------------------------


def test_signal_side_is_closed_two_member_strenum() -> None:
    assert set(SignalSide) == {SignalSide.BUY, SignalSide.SELL}
    assert SignalSide.BUY.value == "BUY"
    assert SignalSide.SELL.value == "SELL"


def test_signal_side_is_a_str_subclass() -> None:
    assert isinstance(SignalSide.BUY, str)
    assert SignalSide.BUY == "BUY"


# ---------------------------------------------------------------------------
# Per-field validation: intent_id
# ---------------------------------------------------------------------------


def test_validation_rejects_non_string_intent_id() -> None:
    raised: Exception | None = None
    try:
        _build(intent_id=42)
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "intent_id" in str(raised)


def test_validation_rejects_empty_intent_id() -> None:
    raised: Exception | None = None
    try:
        _build(intent_id="")
    except ValueError as exc:
        raised = exc
    assert isinstance(raised, ValueError)
    assert "intent_id" in str(raised)


# ---------------------------------------------------------------------------
# Per-field validation: symbol
# ---------------------------------------------------------------------------


def test_validation_rejects_non_string_symbol() -> None:
    raised: Exception | None = None
    try:
        _build(symbol=42)
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "symbol" in str(raised)


def test_validation_rejects_empty_symbol() -> None:
    raised: Exception | None = None
    try:
        _build(symbol="")
    except ValueError as exc:
        raised = exc
    assert isinstance(raised, ValueError)
    assert "symbol" in str(raised)


# ---------------------------------------------------------------------------
# Per-field validation: side
# ---------------------------------------------------------------------------


def test_validation_rejects_string_side_even_if_value_matches() -> None:
    raised: Exception | None = None
    try:
        _build(side="BUY")
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "side" in str(raised)


def test_validation_rejects_none_side() -> None:
    raised: Exception | None = None
    try:
        _build(side=None)
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "side" in str(raised)


def test_validation_accepts_signal_side_sell() -> None:
    intent = _build(side=SignalSide.SELL)
    assert intent.side is SignalSide.SELL


# ---------------------------------------------------------------------------
# Per-field validation: quantity
# ---------------------------------------------------------------------------


def test_validation_rejects_float_quantity() -> None:
    raised: Exception | None = None
    try:
        _build(quantity=1.5)
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "quantity" in str(raised)


def test_validation_rejects_bool_quantity_true() -> None:
    raised: Exception | None = None
    try:
        _build(quantity=True)
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "quantity" in str(raised)


def test_validation_rejects_bool_quantity_false() -> None:
    raised: Exception | None = None
    try:
        _build(quantity=False)
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "quantity" in str(raised)


def test_validation_rejects_zero_quantity() -> None:
    raised: Exception | None = None
    try:
        _build(quantity=0)
    except ValueError as exc:
        raised = exc
    assert isinstance(raised, ValueError)
    assert "quantity" in str(raised)


def test_validation_rejects_negative_quantity() -> None:
    raised: Exception | None = None
    try:
        _build(quantity=-3)
    except ValueError as exc:
        raised = exc
    assert isinstance(raised, ValueError)
    assert "quantity" in str(raised)


# ---------------------------------------------------------------------------
# Per-field validation: rationale
# ---------------------------------------------------------------------------


def test_validation_rejects_non_string_rationale() -> None:
    raised: Exception | None = None
    try:
        _build(rationale=42)
    except TypeError as exc:
        raised = exc
    assert isinstance(raised, TypeError)
    assert "rationale" in str(raised)


def test_validation_rejects_empty_rationale() -> None:
    raised: Exception | None = None
    try:
        _build(rationale="")
    except ValueError as exc:
        raised = exc
    assert isinstance(raised, ValueError)
    assert "rationale" in str(raised)


# ---------------------------------------------------------------------------
# Equality and hashability
# ---------------------------------------------------------------------------


def test_two_intents_with_same_fields_compare_equal() -> None:
    a = _build()
    b = _build()
    assert a == b
    assert a is not b


def test_intents_differing_in_any_field_are_not_equal() -> None:
    base = _build()
    assert base != _build(intent_id="intent-other")
    assert base != _build(symbol="OTHER")
    assert base != _build(side=SignalSide.SELL)
    assert base != _build(quantity=11)
    assert base != _build(rationale="other rationale")


def test_intents_are_hashable_and_equal_hashes_match() -> None:
    a = _build()
    b = _build()
    assert hash(a) == hash(b)
    assert {a, b} == {a}


# ---------------------------------------------------------------------------
# Inertness self-check: no forbidden runtime imports
# ---------------------------------------------------------------------------


_AUTHORIZED_IMPORT_PREFIXES: tuple[str, ...] = (
    "__future__",
    "dataclasses",
    "enum",
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
        Path(__file__).resolve().parents[1].parent / "src" / "gmc_rebuild" / "signal_intake"
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


def test_signal_intake_source_has_no_forbidden_runtime_imports() -> None:
    imported = _collect_imported_modules_from_subpackage_source()
    roots = {name.split(".", 1)[0] for name in imported}
    overlap = roots & _FORBIDDEN_IMPORT_ROOTS
    assert overlap == set(), (
        f"forbidden import roots present in signal_intake source: {sorted(overlap)!r}"
    )


def test_signal_intake_source_only_imports_from_authorized_prefixes() -> None:
    imported = _collect_imported_modules_from_subpackage_source()
    unauthorized: list[str] = []
    for name in sorted(imported):
        if not any(
            name == prefix or name.startswith(prefix + ".")
            for prefix in _AUTHORIZED_IMPORT_PREFIXES
        ):
            unauthorized.append(name)
    assert unauthorized == [], f"unauthorized imports in signal_intake source: {unauthorized!r}"


def test_signal_intake_source_has_no_main_block_or_sleep_or_builtin_io() -> None:
    """Belt-and-suspenders substring scan for the patterns the import-graph
    test above cannot catch: ``__main__`` statements, ``time.sleep(`` /
    ``urllib`` / ``requests.`` / ``socket.`` call sites (the import-graph
    test catches the imports, but this restates the call-site shape for
    audit clarity), and the ``open(`` builtin (which needs no import).

    ``os.environ`` and ``os.getenv`` are deliberately not checked as
    substrings because the subpackage docstrings legitimately use those
    tokens in backticked reassurance language ("no ``os.environ`` reads")
    — the AST import-graph scan above already proves :mod:`os` is not
    imported, so neither attribute can be referenced from code.
    """
    subpackage_root = (
        Path(__file__).resolve().parents[1].parent / "src" / "gmc_rebuild" / "signal_intake"
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


def test_gmc_rebuild_root_does_not_re_export_signal_intake_surface() -> None:
    root = importlib.import_module("gmc_rebuild")
    for name in ("SignalIntent", "SignalSide", "accept_signal_intent"):
        assert not hasattr(root, name), (
            f"gmc_rebuild unexpectedly re-exports {name!r}; per P6-01 the new "
            f"surface must be reachable only via gmc_rebuild.signal_intake."
        )


def test_gmc_rebuild_root_all_does_not_include_signal_intake_surface() -> None:
    root = importlib.import_module("gmc_rebuild")
    root_all = list(getattr(root, "__all__", ()))
    for name in ("SignalIntent", "SignalSide", "accept_signal_intent"):
        assert name not in root_all, (
            f"gmc_rebuild.__all__ unexpectedly includes {name!r}; "
            f"per P6-01 the new surface must not be re-exported."
        )
