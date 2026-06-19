"""P6-09 deterministic in-memory read-only dry-run position reconciliation tests.

Covers the invariant matrix authorized by
``governance/authorizations/2026-06-19_p6-09.md`` §Required Tests / Invariants:
determinism / idempotence, read-only non-mutation, frozen / slotted /
closed-shape, canonical sorted / unique / non-zero validation, quantity-mismatch
validation, the MATCH/MISMATCH biconditional, comparison correctness
(only-in-simulated / only-in-expected / quantity mismatch), ReconciliationStatus
echo for all four statuses, the ``ExpectedPositions.from_simulated_portfolio``
self-comparison sanity check, AST / substring inertness self-checks (including
that ``gmc_rebuild.runtime`` and ``gmc_rebuild.reconciliation`` are not
imported), root-package non-re-export, and the package-skeleton extension.

All assertions are deterministic and value-typed. The module imports only the
closed authorized surface; it activates no runtime, reads no clock, and performs
no I/O beyond reading the merged P6-09 source files for the AST / substring
self-checks.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
from collections.abc import Callable
from pathlib import Path

from gmc_rebuild.dry_run_reconciliation import (
    DryRunReconciliationOutcome,
    DryRunReconciliationResult,
    ExpectedPositions,
    ReconciliationQuantityMismatch,
    reconcile_dry_run_positions,
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


# ---------------------------------------------------------------------------
# ExpectedPositions construction and validation
# ---------------------------------------------------------------------------


def test_expected_positions_accepts_canonical_tuple() -> None:
    expected = ExpectedPositions(positions=(("AAA", 3), ("BBB", -2)))
    assert expected.positions == (("AAA", 3), ("BBB", -2))


def test_expected_positions_is_frozen_and_slotted() -> None:
    expected = ExpectedPositions(positions=(("AAA", 1),))
    assert not hasattr(expected, "__dict__")
    _expect_error(
        dataclasses.FrozenInstanceError,
        lambda: setattr(expected, "positions", (("ZZZ", 9),)),
    )


def test_expected_positions_rejects_unsorted() -> None:
    _expect_error(ValueError, lambda: ExpectedPositions(positions=(("BBB", 1), ("AAA", 1))))


def test_expected_positions_rejects_duplicate_symbol() -> None:
    _expect_error(ValueError, lambda: ExpectedPositions(positions=(("AAA", 1), ("AAA", 2))))


def test_expected_positions_rejects_zero_quantity() -> None:
    _expect_error(ValueError, lambda: ExpectedPositions(positions=(("AAA", 0),)))


def test_expected_positions_rejects_bool_quantity() -> None:
    _expect_error(TypeError, lambda: ExpectedPositions(positions=(("AAA", True),)))


def test_expected_positions_rejects_empty_symbol() -> None:
    _expect_error(ValueError, lambda: ExpectedPositions(positions=(("", 1),)))


def test_expected_positions_rejects_non_tuple() -> None:
    _expect_error(TypeError, lambda: ExpectedPositions(positions=[("AAA", 1)]))  # type: ignore[arg-type]


def test_expected_positions_rejects_malformed_pair() -> None:
    _expect_error(TypeError, lambda: ExpectedPositions(positions=(("AAA", 1, 2),)))  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# ExpectedPositions.from_simulated_portfolio
# ---------------------------------------------------------------------------


def test_from_simulated_portfolio_derives_canonical_positions() -> None:
    snapshot = _portfolio(("AAA", 5), ("BBB", -3))
    expected = ExpectedPositions.from_simulated_portfolio(snapshot)
    assert expected.positions == (("AAA", 5), ("BBB", -3))


def test_from_simulated_portfolio_on_empty_snapshot() -> None:
    expected = ExpectedPositions.from_simulated_portfolio(SimulatedPortfolio.empty())
    assert expected.positions == ()


def test_from_simulated_portfolio_rejects_non_snapshot() -> None:
    _expect_error(TypeError, lambda: ExpectedPositions.from_simulated_portfolio(object()))  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# ReconciliationQuantityMismatch validation
# ---------------------------------------------------------------------------


def test_quantity_mismatch_accepts_differing_quantities() -> None:
    mismatch = ReconciliationQuantityMismatch(
        symbol="AAA", simulated_quantity=3, expected_quantity=5
    )
    assert mismatch.symbol == "AAA"
    assert mismatch.simulated_quantity == 3
    assert mismatch.expected_quantity == 5


def test_quantity_mismatch_rejects_equal_quantities() -> None:
    _expect_error(
        ValueError,
        lambda: ReconciliationQuantityMismatch(
            symbol="AAA", simulated_quantity=4, expected_quantity=4
        ),
    )


def test_quantity_mismatch_rejects_bool_quantity() -> None:
    _expect_error(
        TypeError,
        lambda: ReconciliationQuantityMismatch(
            symbol="AAA", simulated_quantity=True, expected_quantity=2
        ),
    )


def test_quantity_mismatch_rejects_empty_symbol() -> None:
    _expect_error(
        ValueError,
        lambda: ReconciliationQuantityMismatch(
            symbol="", simulated_quantity=1, expected_quantity=2
        ),
    )


def test_quantity_mismatch_is_frozen_and_slotted() -> None:
    mismatch = ReconciliationQuantityMismatch(
        symbol="AAA", simulated_quantity=1, expected_quantity=2
    )
    assert not hasattr(mismatch, "__dict__")
    _expect_error(
        dataclasses.FrozenInstanceError,
        lambda: setattr(mismatch, "symbol", "ZZZ"),
    )


# ---------------------------------------------------------------------------
# DryRunReconciliationOutcome closed enum
# ---------------------------------------------------------------------------


def test_outcome_enum_is_closed_to_two_members() -> None:
    assert {member.name for member in DryRunReconciliationOutcome} == {"MATCH", "MISMATCH"}
    assert DryRunReconciliationOutcome.MATCH.value == "MATCH"
    assert DryRunReconciliationOutcome.MISMATCH.value == "MISMATCH"


# ---------------------------------------------------------------------------
# Comparison correctness
# ---------------------------------------------------------------------------


def test_reconcile_all_match() -> None:
    snapshot = _portfolio(("AAA", 3), ("BBB", -2))
    expected = ExpectedPositions(positions=(("AAA", 3), ("BBB", -2)))
    result = reconcile_dry_run_positions(
        simulated=snapshot, expected=expected, reconciliation_status=ReconciliationStatus.CLEAN
    )
    assert result.outcome is DryRunReconciliationOutcome.MATCH
    assert result.matches == (("AAA", 3), ("BBB", -2))
    assert result.quantity_mismatches == ()
    assert result.only_in_simulated == ()
    assert result.only_in_expected == ()


def test_reconcile_quantity_mismatch() -> None:
    snapshot = _portfolio(("AAA", 3))
    expected = ExpectedPositions(positions=(("AAA", 5),))
    result = reconcile_dry_run_positions(
        simulated=snapshot, expected=expected, reconciliation_status=ReconciliationStatus.WARNING
    )
    assert result.outcome is DryRunReconciliationOutcome.MISMATCH
    assert result.matches == ()
    assert result.quantity_mismatches == (
        ReconciliationQuantityMismatch(symbol="AAA", simulated_quantity=3, expected_quantity=5),
    )
    assert result.only_in_simulated == ()
    assert result.only_in_expected == ()


def test_reconcile_only_in_simulated() -> None:
    snapshot = _portfolio(("AAA", 3), ("BBB", 4))
    expected = ExpectedPositions(positions=(("AAA", 3),))
    result = reconcile_dry_run_positions(
        simulated=snapshot, expected=expected, reconciliation_status=ReconciliationStatus.FAILED
    )
    assert result.outcome is DryRunReconciliationOutcome.MISMATCH
    assert result.matches == (("AAA", 3),)
    assert result.only_in_simulated == (("BBB", 4),)
    assert result.only_in_expected == ()


def test_reconcile_only_in_expected() -> None:
    snapshot = _portfolio(("AAA", 3))
    expected = ExpectedPositions(positions=(("AAA", 3), ("CCC", -7)))
    result = reconcile_dry_run_positions(
        simulated=snapshot, expected=expected, reconciliation_status=ReconciliationStatus.CLEAN
    )
    assert result.outcome is DryRunReconciliationOutcome.MISMATCH
    assert result.matches == (("AAA", 3),)
    assert result.only_in_simulated == ()
    assert result.only_in_expected == (("CCC", -7),)


def test_reconcile_mixed_buckets_are_canonically_sorted() -> None:
    snapshot = _portfolio(("DDD", 1), ("BBB", 2), ("AAA", 9))
    expected = ExpectedPositions(positions=(("AAA", 9), ("BBB", 5), ("CCC", -1)))
    result = reconcile_dry_run_positions(
        simulated=snapshot, expected=expected, reconciliation_status=ReconciliationStatus.WARNING
    )
    assert result.outcome is DryRunReconciliationOutcome.MISMATCH
    assert result.matches == (("AAA", 9),)
    assert result.quantity_mismatches == (
        ReconciliationQuantityMismatch(symbol="BBB", simulated_quantity=2, expected_quantity=5),
    )
    assert result.only_in_simulated == (("DDD", 1),)
    assert result.only_in_expected == (("CCC", -1),)


def test_reconcile_two_empty_inputs_match() -> None:
    result = reconcile_dry_run_positions(
        simulated=SimulatedPortfolio.empty(),
        expected=ExpectedPositions(positions=()),
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    assert result.outcome is DryRunReconciliationOutcome.MATCH
    assert result.matches == ()


# ---------------------------------------------------------------------------
# ReconciliationStatus echo for all four statuses
# ---------------------------------------------------------------------------


def test_reconciliation_status_echoed_verbatim_for_all_statuses() -> None:
    snapshot = _portfolio(("AAA", 1))
    expected = ExpectedPositions(positions=(("AAA", 1),))
    for status in (
        ReconciliationStatus.CLEAN,
        ReconciliationStatus.WARNING,
        ReconciliationStatus.UNAVAILABLE,
        ReconciliationStatus.FAILED,
    ):
        result = reconcile_dry_run_positions(
            simulated=snapshot, expected=expected, reconciliation_status=status
        )
        assert result.reconciliation_status is status


# ---------------------------------------------------------------------------
# Determinism / idempotence
# ---------------------------------------------------------------------------


def test_reconcile_is_deterministic_and_idempotent() -> None:
    snapshot = _portfolio(("AAA", 3), ("BBB", -2))
    expected = ExpectedPositions(positions=(("AAA", 4), ("CCC", 1)))
    first = reconcile_dry_run_positions(
        simulated=snapshot, expected=expected, reconciliation_status=ReconciliationStatus.WARNING
    )
    second = reconcile_dry_run_positions(
        simulated=snapshot, expected=expected, reconciliation_status=ReconciliationStatus.WARNING
    )
    assert first == second


# ---------------------------------------------------------------------------
# Read-only non-mutation of inputs
# ---------------------------------------------------------------------------


def test_reconcile_does_not_mutate_inputs() -> None:
    snapshot = _portfolio(("AAA", 3), ("BBB", -2))
    expected = ExpectedPositions(positions=(("AAA", 4),))
    snapshot_before = (snapshot.positions, snapshot.applied_intent_ids)
    expected_before = expected.positions
    reconcile_dry_run_positions(
        simulated=snapshot, expected=expected, reconciliation_status=ReconciliationStatus.CLEAN
    )
    assert (snapshot.positions, snapshot.applied_intent_ids) == snapshot_before
    assert expected.positions == expected_before


# ---------------------------------------------------------------------------
# Argument type validation
# ---------------------------------------------------------------------------


def test_reconcile_rejects_non_portfolio_simulated() -> None:
    _expect_error(
        TypeError,
        lambda: reconcile_dry_run_positions(
            simulated=object(),  # type: ignore[arg-type]
            expected=ExpectedPositions(positions=()),
            reconciliation_status=ReconciliationStatus.CLEAN,
        ),
    )


def test_reconcile_rejects_non_expected_positions() -> None:
    _expect_error(
        TypeError,
        lambda: reconcile_dry_run_positions(
            simulated=SimulatedPortfolio.empty(),
            expected=object(),  # type: ignore[arg-type]
            reconciliation_status=ReconciliationStatus.CLEAN,
        ),
    )


def test_reconcile_rejects_non_reconciliation_status() -> None:
    _expect_error(
        TypeError,
        lambda: reconcile_dry_run_positions(
            simulated=SimulatedPortfolio.empty(),
            expected=ExpectedPositions(positions=()),
            reconciliation_status="clean",  # type: ignore[arg-type]
        ),
    )


# ---------------------------------------------------------------------------
# DryRunReconciliationResult shape, biconditional, equality / hashability
# ---------------------------------------------------------------------------


def test_result_is_frozen_and_slotted_with_six_fields() -> None:
    result = reconcile_dry_run_positions(
        simulated=SimulatedPortfolio.empty(),
        expected=ExpectedPositions(positions=()),
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    assert not hasattr(result, "__dict__")
    assert [f.name for f in dataclasses.fields(result)] == [
        "outcome",
        "matches",
        "quantity_mismatches",
        "only_in_simulated",
        "only_in_expected",
        "reconciliation_status",
    ]
    _expect_error(
        dataclasses.FrozenInstanceError,
        lambda: setattr(result, "outcome", DryRunReconciliationOutcome.MISMATCH),
    )


def test_result_biconditional_rejects_match_with_differences() -> None:
    _expect_error(
        ValueError,
        lambda: DryRunReconciliationResult(
            outcome=DryRunReconciliationOutcome.MATCH,
            matches=(),
            quantity_mismatches=(),
            only_in_simulated=(("AAA", 1),),
            only_in_expected=(),
            reconciliation_status=ReconciliationStatus.CLEAN,
        ),
    )


def test_result_biconditional_rejects_mismatch_without_differences() -> None:
    _expect_error(
        ValueError,
        lambda: DryRunReconciliationResult(
            outcome=DryRunReconciliationOutcome.MISMATCH,
            matches=(("AAA", 1),),
            quantity_mismatches=(),
            only_in_simulated=(),
            only_in_expected=(),
            reconciliation_status=ReconciliationStatus.CLEAN,
        ),
    )


def test_result_rejects_unsorted_quantity_mismatches() -> None:
    _expect_error(
        ValueError,
        lambda: DryRunReconciliationResult(
            outcome=DryRunReconciliationOutcome.MISMATCH,
            matches=(),
            quantity_mismatches=(
                ReconciliationQuantityMismatch(
                    symbol="BBB", simulated_quantity=1, expected_quantity=2
                ),
                ReconciliationQuantityMismatch(
                    symbol="AAA", simulated_quantity=1, expected_quantity=2
                ),
            ),
            only_in_simulated=(),
            only_in_expected=(),
            reconciliation_status=ReconciliationStatus.WARNING,
        ),
    )


def test_result_equality_and_hashability() -> None:
    snapshot = _portfolio(("AAA", 3))
    expected = ExpectedPositions(positions=(("AAA", 3),))
    first = reconcile_dry_run_positions(
        simulated=snapshot, expected=expected, reconciliation_status=ReconciliationStatus.CLEAN
    )
    second = reconcile_dry_run_positions(
        simulated=snapshot, expected=expected, reconciliation_status=ReconciliationStatus.CLEAN
    )
    different = reconcile_dry_run_positions(
        simulated=snapshot, expected=expected, reconciliation_status=ReconciliationStatus.WARNING
    )
    assert first == second
    assert first != different
    assert hash(first) == hash(second)
    assert len({first, second, different}) == 2


def test_self_comparison_is_match() -> None:
    snapshot = _portfolio(("AAA", 3), ("BBB", -2), ("CCC", 7))
    result = reconcile_dry_run_positions(
        simulated=snapshot,
        expected=ExpectedPositions.from_simulated_portfolio(snapshot),
        reconciliation_status=ReconciliationStatus.CLEAN,
    )
    assert result.outcome is DryRunReconciliationOutcome.MATCH
    assert result.quantity_mismatches == ()
    assert result.only_in_simulated == ()
    assert result.only_in_expected == ()


# ---------------------------------------------------------------------------
# Inertness self-check: no forbidden runtime imports / behavior
# ---------------------------------------------------------------------------


_AUTHORIZED_IMPORT_PREFIXES: tuple[str, ...] = (
    "__future__",
    "dataclasses",
    "enum",
    "collections.abc",
    "typing",
    "gmc_rebuild.dry_run_reconciliation",
    "gmc_rebuild.portfolio_state",
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
        "uuid",
        "random",
    }
)


def _subpackage_root() -> Path:
    return (
        Path(__file__).resolve().parents[1].parent
        / "src"
        / "gmc_rebuild"
        / "dry_run_reconciliation"
    )


def _collect_imported_modules_from_subpackage_source() -> set[str]:
    imported: set[str] = set()
    for path in sorted(_subpackage_root().glob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
                imported.add(node.module)
    return imported


def test_dry_run_reconciliation_source_has_no_forbidden_runtime_imports() -> None:
    imported = _collect_imported_modules_from_subpackage_source()
    roots = {name.split(".", 1)[0] for name in imported}
    overlap = roots & _FORBIDDEN_IMPORT_ROOTS
    assert overlap == set(), (
        f"forbidden import roots present in dry_run_reconciliation source: {sorted(overlap)!r}"
    )


def test_dry_run_reconciliation_source_only_imports_from_authorized_prefixes() -> None:
    imported = _collect_imported_modules_from_subpackage_source()
    unauthorized = [
        name
        for name in sorted(imported)
        if not any(
            name == prefix or name.startswith(prefix + ".")
            for prefix in _AUTHORIZED_IMPORT_PREFIXES
        )
    ]
    assert unauthorized == [], (
        f"unauthorized imports in dry_run_reconciliation source: {unauthorized!r}"
    )


def test_dry_run_reconciliation_does_not_import_runtime_or_reconciliation() -> None:
    """Pin the isolation contract from both directions: P6-09 must not import
    ``gmc_rebuild.runtime`` (no P4-07 composition) nor
    ``gmc_rebuild.reconciliation`` (no runtime use of the P3-05 fixture)."""
    imported = _collect_imported_modules_from_subpackage_source()
    for forbidden in ("gmc_rebuild.runtime", "gmc_rebuild.reconciliation"):
        assert not any(
            name == forbidden or name.startswith(forbidden + ".") for name in imported
        ), f"dry_run_reconciliation must not import {forbidden!r}"


def test_dry_run_reconciliation_source_has_no_main_block_or_io_or_audit() -> None:
    """Belt-and-suspenders substring scan for runtime-activation / I/O / audit
    patterns the import-graph test cannot catch."""
    for path in sorted(_subpackage_root().glob("*.py")):
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
        assert "logging.basicConfig" not in source, path
        assert "audit_event(" not in source, path


# ---------------------------------------------------------------------------
# Root package does not re-export the new surface
# ---------------------------------------------------------------------------


_PUBLIC_NAMES = (
    "DryRunReconciliationOutcome",
    "DryRunReconciliationResult",
    "ExpectedPositions",
    "ReconciliationQuantityMismatch",
    "reconcile_dry_run_positions",
)


def test_subpackage_all_is_exactly_the_five_public_symbols() -> None:
    module = importlib.import_module("gmc_rebuild.dry_run_reconciliation")
    assert sorted(module.__all__) == sorted(_PUBLIC_NAMES)


def test_gmc_rebuild_root_does_not_re_export_dry_run_reconciliation_surface() -> None:
    root = importlib.import_module("gmc_rebuild")
    for name in _PUBLIC_NAMES:
        assert not hasattr(root, name), (
            f"gmc_rebuild unexpectedly re-exports {name!r}; per P6-09 the new "
            f"surface must be reachable only via gmc_rebuild.dry_run_reconciliation."
        )


def test_gmc_rebuild_root_all_does_not_include_dry_run_reconciliation_surface() -> None:
    root = importlib.import_module("gmc_rebuild")
    root_all = list(getattr(root, "__all__", ()))
    for name in _PUBLIC_NAMES:
        assert name not in root_all


# ---------------------------------------------------------------------------
# §8 step 4a allowlist + package-skeleton extension
# ---------------------------------------------------------------------------


def test_master_status_allowlists_dry_run_reconciliation_path() -> None:
    master_status = (Path(__file__).resolve().parents[1].parent / "MASTER_STATUS.md").read_text(
        encoding="utf-8"
    )
    allowlist_lines = [
        line for line in master_status.splitlines() if line.startswith("allowed_p2_infra=")
    ]
    assert allowlist_lines, "MASTER_STATUS.md must declare the §8 step 4a allowed_p2_infra gate"
    assert "src/gmc_rebuild/dry_run_reconciliation" in allowlist_lines[0], (
        "src/gmc_rebuild/dry_run_reconciliation must be on the §8 step 4a allowlist"
    )


def test_package_skeleton_includes_dry_run_reconciliation() -> None:
    src_root = Path(__file__).resolve().parents[1].parent / "src" / "gmc_rebuild"
    entries = {p.name for p in src_root.iterdir() if not p.name.startswith("__")}
    assert "dry_run_reconciliation" in entries
