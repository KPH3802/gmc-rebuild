"""P6-10 deterministic read-only dry-run reconciliation JSON projection tests.

Covers the invariant matrix authorized by
``governance/authorizations/2026-06-20_p6-10.md``: determinism / idempotence,
read-only non-mutation of the P6-09 input, JSON-serializability (every leaf a
``str`` or ``int``; ``json.dumps`` round-trips), schema correctness for MATCH and
MISMATCH results, canonical order preservation, ``ReconciliationStatus`` echo for
all four statuses (preserving the ADR-003 ``UNAVAILABLE`` vs ``FAILED``
distinction), type-validation of the single input, AST / substring inertness
self-checks (no clock read, no I/O, no ``audit_event``, no ``__main__``),
root-package non-re-export, and the §8 allowlist + package-skeleton extension.

All assertions are deterministic and value-typed. The module imports only the
closed authorized surface; it activates no runtime, reads no clock, and performs
no I/O beyond reading the merged P6-10 source for the AST / substring self-checks.
"""

from __future__ import annotations

import ast
import copy
import importlib
import json
from collections.abc import Callable
from pathlib import Path

from gmc_rebuild.dry_run_reconciliation import (
    DryRunReconciliationResult,
    ExpectedPositions,
    reconcile_dry_run_positions,
)
from gmc_rebuild.dry_run_reconciliation_view import (
    build_dry_run_reconciliation_json_payload,
)
from gmc_rebuild.portfolio_state import SimulatedPortfolio, SimulatedPosition
from gmc_rebuild.risk import ReconciliationStatus


def _expect_error(error_type: type[BaseException], call: Callable[[], object]) -> None:
    """In-repo replacement for ``pytest.raises`` (matches the P6-NN convention)."""
    try:
        call()
    except error_type:
        return
    except BaseException as exc:
        raise AssertionError(f"expected {error_type.__name__}, got {type(exc).__name__}") from exc
    raise AssertionError(f"expected {error_type.__name__}, but no error was raised")


def _portfolio(*pairs: tuple[str, int]) -> SimulatedPortfolio:
    positions = tuple(
        SimulatedPosition(symbol=symbol, net_quantity=quantity) for symbol, quantity in pairs
    )
    return SimulatedPortfolio(
        positions=tuple(sorted(positions, key=lambda p: p.symbol)),
        applied_intent_ids=(),
    )


def _match_result(
    status: ReconciliationStatus = ReconciliationStatus.CLEAN,
) -> DryRunReconciliationResult:
    simulated = _portfolio(("AAA", 3), ("BBB", -2))
    expected = ExpectedPositions.from_simulated_portfolio(simulated)
    return reconcile_dry_run_positions(
        simulated=simulated, expected=expected, reconciliation_status=status
    )


def _mismatch_result(
    status: ReconciliationStatus = ReconciliationStatus.FAILED,
) -> DryRunReconciliationResult:
    # AAA quantity differs, CCC only-in-simulated, DDD only-in-expected, BBB matches.
    simulated = _portfolio(("AAA", 3), ("BBB", -2), ("CCC", 5))
    expected = ExpectedPositions(positions=(("AAA", 4), ("BBB", -2), ("DDD", 7)))
    return reconcile_dry_run_positions(
        simulated=simulated, expected=expected, reconciliation_status=status
    )


# ---------------------------------------------------------------------------
# Schema correctness
# ---------------------------------------------------------------------------


def test_match_payload_schema() -> None:
    payload = build_dry_run_reconciliation_json_payload(_match_result())
    assert payload == {
        "outcome": "MATCH",
        "reconciliation_status": "clean",
        "matches": [
            {"symbol": "AAA", "quantity": 3},
            {"symbol": "BBB", "quantity": -2},
        ],
        "quantity_mismatches": [],
        "only_in_simulated": [],
        "only_in_expected": [],
        "summary": {
            "matches": 2,
            "quantity_mismatches": 0,
            "only_in_simulated": 0,
            "only_in_expected": 0,
        },
    }


def test_mismatch_payload_schema() -> None:
    payload = build_dry_run_reconciliation_json_payload(_mismatch_result())
    assert payload == {
        "outcome": "MISMATCH",
        "reconciliation_status": "failed",
        "matches": [{"symbol": "BBB", "quantity": -2}],
        "quantity_mismatches": [
            {"symbol": "AAA", "simulated_quantity": 3, "expected_quantity": 4},
        ],
        "only_in_simulated": [{"symbol": "CCC", "quantity": 5}],
        "only_in_expected": [{"symbol": "DDD", "quantity": 7}],
        "summary": {
            "matches": 1,
            "quantity_mismatches": 1,
            "only_in_simulated": 1,
            "only_in_expected": 1,
        },
    }


def test_payload_canonical_order_preserved() -> None:
    # Two only-in-simulated symbols must appear in symbol-ascending order,
    # mirroring the canonical order the P6-09 result already enforces.
    simulated = _portfolio(("ZZZ", 1), ("AAA", 1))
    expected = ExpectedPositions(positions=())
    result = reconcile_dry_run_positions(
        simulated=simulated,
        expected=expected,
        reconciliation_status=ReconciliationStatus.FAILED,
    )
    payload = build_dry_run_reconciliation_json_payload(result)
    symbols = [record["symbol"] for record in payload["only_in_simulated"]]
    assert symbols == ["AAA", "ZZZ"]


# ---------------------------------------------------------------------------
# JSON-serializability
# ---------------------------------------------------------------------------


def test_payload_is_json_serializable_and_round_trips() -> None:
    payload = build_dry_run_reconciliation_json_payload(_mismatch_result())
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    assert json.loads(rendered) == payload


def test_payload_leaves_are_only_str_or_int() -> None:
    payload = build_dry_run_reconciliation_json_payload(_mismatch_result())

    def _check(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                assert isinstance(key, str)
                _check(value)
        elif isinstance(node, list):
            for item in node:
                _check(item)
        else:
            assert isinstance(node, str) or (
                isinstance(node, int) and not isinstance(node, bool)
            ), f"unexpected leaf type {type(node).__name__}"

    _check(payload)


# ---------------------------------------------------------------------------
# Determinism and read-only behavior
# ---------------------------------------------------------------------------


def test_payload_is_deterministic() -> None:
    first = build_dry_run_reconciliation_json_payload(_mismatch_result())
    second = build_dry_run_reconciliation_json_payload(_mismatch_result())
    assert first == second


def test_builder_does_not_mutate_input() -> None:
    result = _mismatch_result()
    before = copy.deepcopy(result)
    build_dry_run_reconciliation_json_payload(result)
    assert result == before


def test_status_echoed_verbatim_for_all_statuses() -> None:
    for status in ReconciliationStatus:
        result = _match_result(status)
        payload = build_dry_run_reconciliation_json_payload(result)
        assert payload["reconciliation_status"] == status.value


# ---------------------------------------------------------------------------
# Type validation
# ---------------------------------------------------------------------------


def test_builder_rejects_non_result_input() -> None:
    _expect_error(TypeError, lambda: build_dry_run_reconciliation_json_payload(object()))  # type: ignore[arg-type]
    _expect_error(TypeError, lambda: build_dry_run_reconciliation_json_payload(None))  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Closed public surface and non-re-export
# ---------------------------------------------------------------------------


_PUBLIC_NAMES = ("build_dry_run_reconciliation_json_payload",)


def test_subpackage_all_is_exactly_the_one_public_symbol() -> None:
    module = importlib.import_module("gmc_rebuild.dry_run_reconciliation_view")
    assert sorted(module.__all__) == sorted(_PUBLIC_NAMES)


def test_gmc_rebuild_root_does_not_re_export_dry_run_reconciliation_view_surface() -> None:
    root = importlib.import_module("gmc_rebuild")
    for name in _PUBLIC_NAMES:
        assert not hasattr(root, name), (
            f"gmc_rebuild unexpectedly re-exports {name!r}; per P6-10 the new "
            f"surface must be reachable only via gmc_rebuild.dry_run_reconciliation_view."
        )


def test_gmc_rebuild_root_all_does_not_include_dry_run_reconciliation_view_surface() -> None:
    root = importlib.import_module("gmc_rebuild")
    root_all = list(getattr(root, "__all__", ()))
    for name in _PUBLIC_NAMES:
        assert name not in root_all


# ---------------------------------------------------------------------------
# AST / substring inertness self-checks
# ---------------------------------------------------------------------------


def _payload_source() -> str:
    module = importlib.import_module("gmc_rebuild.dry_run_reconciliation_view._payload")
    return Path(module.__file__).read_text(encoding="utf-8")  # type: ignore[arg-type]


def test_source_imports_only_authorized_modules() -> None:
    tree = ast.parse(_payload_source())
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
    forbidden = {
        "os",
        "sys",
        "socket",
        "subprocess",
        "threading",
        "asyncio",
        "sqlite3",
        "time",
        "datetime",
        "random",
        "gmc_rebuild.logging",
        "gmc_rebuild.runtime",
        "gmc_rebuild.reconciliation",
        "gmc_rebuild.time",
    }
    assert not (imported & forbidden), f"forbidden import(s): {sorted(imported & forbidden)}"


def _source_without_docstrings() -> str:
    """Return the P6-10 source with module/function docstrings stripped.

    The inertness substring scan targets *code*, not prose: the docstrings
    legitimately name the very tokens the code must avoid (``now_utc``,
    ``__main__``, ...) when documenting that they are not used.
    """
    tree = ast.parse(_payload_source())
    docstrings: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None:
                docstrings.add(doc)
    source = _payload_source()
    for doc in docstrings:
        source = source.replace(doc, "")
    return source


def test_source_has_no_side_effecting_tokens() -> None:
    source = _source_without_docstrings()
    for token in (
        "open(",
        "now_utc",
        "datetime.now",
        "time.sleep",
        "audit_event",
        "__main__",
        ".write_text",
        "Path(",
    ):
        assert token not in source, f"unexpected token in P6-10 code: {token!r}"


# ---------------------------------------------------------------------------
# §8 step 4a allowlist + package-skeleton extension
# ---------------------------------------------------------------------------


def test_master_status_allowlists_dry_run_reconciliation_view_path() -> None:
    master_status = (Path(__file__).resolve().parents[1].parent / "MASTER_STATUS.md").read_text(
        encoding="utf-8"
    )
    allowlist_lines = [
        line for line in master_status.splitlines() if line.startswith("allowed_p2_infra=")
    ]
    assert allowlist_lines, "MASTER_STATUS.md must declare the §8 step 4a allowed_p2_infra gate"
    assert "src/gmc_rebuild/dry_run_reconciliation_view" in allowlist_lines[0], (
        "src/gmc_rebuild/dry_run_reconciliation_view must be on the §8 step 4a allowlist"
    )


def test_package_skeleton_includes_dry_run_reconciliation_view() -> None:
    src_root = Path(__file__).resolve().parents[1].parent / "src" / "gmc_rebuild"
    entries = {p.name for p in src_root.iterdir() if not p.name.startswith("__")}
    assert "dry_run_reconciliation_view" in entries
