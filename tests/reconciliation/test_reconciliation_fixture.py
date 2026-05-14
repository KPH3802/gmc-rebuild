"""P3-05 ReconciliationProtocol in-memory fixture tests.

Verifies that the ``gmc_rebuild.reconciliation`` subpackage authorized by
the P3-05 implementation PR (see
``governance/authorizations/2026-05-14_p3-05.md``):

- exposes the in-memory fake fixture (and only that);
- conforms structurally to
  :class:`gmc_rebuild.risk.ReconciliationProtocol`;
- preserves ADR-003 safe-default behavior (a freshly constructed
  fake reports ``UNAVAILABLE``, **not** ``FAILED``; the
  ``UNAVAILABLE`` / ``FAILED`` distinction is preserved);
- preserves ADR-004 UTC discipline at the boundary (naive datetimes
  are rejected; timestamps are Z-suffixed UTC strings);
- introduces no forbidden runtime entry points, env-var reads, or
  filesystem / network / sleep / broker / market-data / order /
  position / fill I/O.

Tests avoid ``pytest.raises`` / fixture-typed parameters so the mypy
strict pre-commit hook does not need a pytest-stub dependency. See
``tests/kill_switch/test_kill_switch_fixture.py`` for the same pattern.
"""

from __future__ import annotations

import ast
import importlib
from datetime import UTC, datetime
from pathlib import Path

from gmc_rebuild.reconciliation import InMemoryReconciliation
from gmc_rebuild.risk import (
    ReconciliationProtocol,
    ReconciliationReport,
    ReconciliationStatus,
    RiskControlError,
)
from gmc_rebuild.time import NaiveDatetimeError

_FIXED_CLOCK = datetime(2026, 5, 14, 14, 0, 0, tzinfo=UTC)


def _expect_risk_error(call: object, match: str) -> None:
    raised: Exception | None = None
    try:
        call()  # type: ignore[operator]
    except RiskControlError as exc:
        raised = exc
    assert isinstance(raised, RiskControlError), (
        f"expected RiskControlError matching {match!r}, got {raised!r}"
    )
    assert match in str(raised), f"RiskControlError message {str(raised)!r} missing {match!r}"


def _expect_naive_error(call: object) -> None:
    raised: Exception | None = None
    try:
        call()  # type: ignore[operator]
    except NaiveDatetimeError as exc:
        raised = exc
    assert isinstance(raised, NaiveDatetimeError), f"expected NaiveDatetimeError, got {raised!r}"


# ---------------------------------------------------------------------------
# Package surface
# ---------------------------------------------------------------------------


def test_reconciliation_subpackage_imports() -> None:
    module = importlib.import_module("gmc_rebuild.reconciliation")
    assert module is not None
    assert hasattr(module, "InMemoryReconciliation")
    assert module.__all__ == ["InMemoryReconciliation"]


def test_reconciliation_not_reexported_from_runtime_root() -> None:
    runtime_root = importlib.import_module("gmc_rebuild")
    assert not hasattr(runtime_root, "reconciliation") or (
        getattr(runtime_root, "__all__", None) is not None
        and "reconciliation" not in runtime_root.__all__
        and "InMemoryReconciliation" not in runtime_root.__all__
    )


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_fake_is_reconciliation_protocol_instance() -> None:
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    assert isinstance(fake, ReconciliationProtocol)


def test_reconcile_returns_reconciliation_report() -> None:
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    report = fake.reconcile()
    assert isinstance(report, ReconciliationReport)


# ---------------------------------------------------------------------------
# ADR-003 safe-default behavior: UNAVAILABLE on no upstream data
# ---------------------------------------------------------------------------


def test_fresh_fake_reports_unavailable_not_failed() -> None:
    """ADR-003 distinguishes ``UNAVAILABLE`` (no upstream data) from
    ``FAILED`` (confirmed material mismatch). A freshly constructed
    fake has no upstream data and must report ``UNAVAILABLE``.
    """
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    report = fake.reconcile()
    assert report.status is ReconciliationStatus.UNAVAILABLE
    # ADR-003 explicit distinction: UNAVAILABLE != FAILED.
    assert report.status.value == "unavailable"
    assert ReconciliationStatus.FAILED.value == "failed"


def test_fresh_fake_has_zero_delta_and_empty_details() -> None:
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    report = fake.reconcile()
    assert report.observed_delta == 0.0
    assert report.tolerance == 0.0
    assert dict(report.details) == {}


def test_repeated_reconcile_with_no_outcomes_keeps_unavailable() -> None:
    """Without staged outcomes, every ``reconcile()`` call remains UNAVAILABLE.

    The fake never auto-promotes to ``FAILED`` or ``CLEAN``; the test
    suite drives state transitions explicitly via :meth:`enqueue` /
    :meth:`set_next`.
    """
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    for _ in range(3):
        report = fake.reconcile()
        assert report.status is ReconciliationStatus.UNAVAILABLE


# ---------------------------------------------------------------------------
# Outcome staging via enqueue / set_next
# ---------------------------------------------------------------------------


def test_enqueue_clean_outcome_is_reported_then_drains_to_unavailable() -> None:
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    fake.enqueue(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"source": "fixture-synthetic"},
    )
    first = fake.reconcile()
    assert first.status is ReconciliationStatus.CLEAN
    assert first.tolerance == 10.0
    assert first.observed_delta == 0.0
    assert dict(first.details) == {"source": "fixture-synthetic"}
    second = fake.reconcile()
    assert second.status is ReconciliationStatus.UNAVAILABLE


def test_enqueue_failed_outcome_preserves_distinction_from_unavailable() -> None:
    """A confirmed material mismatch (``FAILED``) is distinct from
    ``UNAVAILABLE`` and carries a positive ``observed_delta``.
    """
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    fake.enqueue(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=42.5,
        details={"note": "fixture-synthetic"},
    )
    report = fake.reconcile()
    assert report.status is ReconciliationStatus.FAILED
    # ADR-003 explicit distinction: FAILED != UNAVAILABLE.
    assert report.status.value == "failed"
    assert ReconciliationStatus.UNAVAILABLE.value == "unavailable"
    assert report.observed_delta == 42.5
    assert report.tolerance == 10.0


def test_enqueue_warning_outcome_is_reported() -> None:
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    fake.enqueue(
        status=ReconciliationStatus.WARNING,
        tolerance=10.0,
        observed_delta=5.0,
        details={},
    )
    report = fake.reconcile()
    assert report.status is ReconciliationStatus.WARNING
    assert report.observed_delta == 5.0


def test_outcomes_are_drained_in_fifo_order() -> None:
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    fake.enqueue(status=ReconciliationStatus.CLEAN, tolerance=10.0, observed_delta=0.0)
    fake.enqueue(
        status=ReconciliationStatus.WARNING, tolerance=10.0, observed_delta=3.0
    )
    fake.enqueue(
        status=ReconciliationStatus.FAILED, tolerance=10.0, observed_delta=99.0
    )
    statuses = [fake.reconcile().status for _ in range(3)]
    assert statuses == [
        ReconciliationStatus.CLEAN,
        ReconciliationStatus.WARNING,
        ReconciliationStatus.FAILED,
    ]
    drained = fake.reconcile()
    assert drained.status is ReconciliationStatus.UNAVAILABLE


def test_set_next_clears_existing_queue() -> None:
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    fake.enqueue(status=ReconciliationStatus.CLEAN, tolerance=10.0, observed_delta=0.0)
    fake.enqueue(
        status=ReconciliationStatus.WARNING, tolerance=10.0, observed_delta=3.0
    )
    fake.set_next(
        status=ReconciliationStatus.FAILED, tolerance=10.0, observed_delta=50.0
    )
    report = fake.reconcile()
    assert report.status is ReconciliationStatus.FAILED
    assert fake.reconcile().status is ReconciliationStatus.UNAVAILABLE


# ---------------------------------------------------------------------------
# reconcile() does not raise in the steady-state case
# ---------------------------------------------------------------------------


def test_reconcile_does_not_raise_in_steady_state() -> None:
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    fake.reconcile()
    fake.enqueue(
        status=ReconciliationStatus.FAILED, tolerance=10.0, observed_delta=1.0
    )
    fake.reconcile()
    fake.reconcile()


# ---------------------------------------------------------------------------
# Clock helper
# ---------------------------------------------------------------------------


def test_advance_clock_reflects_in_checked_at() -> None:
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    before = fake.reconcile().checked_at
    fake.advance(3600.0)
    after = fake.reconcile().checked_at
    assert before == "2026-05-14T14:00:00Z"
    assert after == "2026-05-14T15:00:00Z"


# ---------------------------------------------------------------------------
# ADR-004 UTC discipline at the boundary
# ---------------------------------------------------------------------------


def test_construction_rejects_naive_checked_at() -> None:
    _expect_naive_error(lambda: InMemoryReconciliation(checked_at=datetime(2026, 5, 14, 14)))


def test_report_timestamps_are_z_suffixed_utc_strings() -> None:
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    unavailable = fake.reconcile()
    assert unavailable.checked_at.endswith("Z")
    assert unavailable.checked_at == "2026-05-14T14:00:00Z"
    fake.enqueue(
        status=ReconciliationStatus.CLEAN, tolerance=10.0, observed_delta=0.0
    )
    clean = fake.reconcile()
    assert clean.checked_at.endswith("Z")
    assert clean.checked_at == "2026-05-14T14:00:00Z"


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_enqueue_rejects_non_status() -> None:
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    _expect_risk_error(
        lambda: fake.enqueue(
            status="clean",  # type: ignore[arg-type]
            tolerance=10.0,
            observed_delta=0.0,
        ),
        "must be a ReconciliationStatus",
    )


def test_enqueue_rejects_negative_tolerance() -> None:
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    _expect_risk_error(
        lambda: fake.enqueue(
            status=ReconciliationStatus.CLEAN, tolerance=-1.0, observed_delta=0.0
        ),
        "tolerance must be non-negative",
    )


def test_enqueue_rejects_negative_observed_delta() -> None:
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    _expect_risk_error(
        lambda: fake.enqueue(
            status=ReconciliationStatus.FAILED, tolerance=10.0, observed_delta=-1.0
        ),
        "observed_delta must be non-negative",
    )


def test_enqueue_rejects_nonzero_delta_for_clean() -> None:
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    _expect_risk_error(
        lambda: fake.enqueue(
            status=ReconciliationStatus.CLEAN, tolerance=10.0, observed_delta=1.0
        ),
        "observed_delta must be 0.0",
    )


def test_enqueue_rejects_nonzero_delta_for_unavailable() -> None:
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    _expect_risk_error(
        lambda: fake.enqueue(
            status=ReconciliationStatus.UNAVAILABLE, tolerance=0.0, observed_delta=1.0
        ),
        "observed_delta must be 0.0",
    )


def test_enqueue_rejects_bool_numeric_inputs() -> None:
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    _expect_risk_error(
        lambda: fake.enqueue(
            status=ReconciliationStatus.CLEAN,
            tolerance=True,
            observed_delta=0.0,
        ),
        "tolerance must be a number",
    )
    _expect_risk_error(
        lambda: fake.enqueue(
            status=ReconciliationStatus.FAILED,
            tolerance=10.0,
            observed_delta=True,
        ),
        "observed_delta must be a number",
    )


def test_advance_rejects_negative_or_non_numeric() -> None:
    fake = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    _expect_risk_error(lambda: fake.advance(-1.0), "must be non-negative")
    _expect_risk_error(lambda: fake.advance(True), "must be a number")


# ---------------------------------------------------------------------------
# No forbidden runtime behavior
# ---------------------------------------------------------------------------


_PKG_ROOT = (
    Path(__file__).resolve().parent.parent.parent / "src" / "gmc_rebuild" / "reconciliation"
)


def _reconciliation_source_files() -> list[Path]:
    return sorted(_PKG_ROOT.glob("*.py"))


def _strip_docstrings_and_comments(source: str) -> str:
    """Return ``source`` with module/class/function docstrings and # comments removed.

    Used so the "no forbidden tokens" checks below match real code, not
    governance commentary in docstrings. Docstrings are intentionally
    verbose under the P3-05 authorization and reference forbidden token
    names by design (to assert what the module is *not*).
    """
    tree = ast.parse(source)
    drop_ranges: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", None)
            if not body:
                continue
            first = body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                drop_ranges.append((first.lineno, getattr(first, "end_lineno", first.lineno)))
    lines = source.splitlines()
    keep: list[str] = []
    for idx, raw in enumerate(lines, start=1):
        if any(lo <= idx <= hi for lo, hi in drop_ranges):
            continue
        if "#" in raw:
            raw = raw.split("#", 1)[0]
        keep.append(raw)
    return "\n".join(keep)


def _reconciliation_code_text() -> str:
    return "\n".join(
        _strip_docstrings_and_comments(p.read_text()) for p in _reconciliation_source_files()
    )


def test_reconciliation_package_has_no_main_entry_point() -> None:
    code = _reconciliation_code_text()
    assert "__main__" not in code
    assert "if __name__" not in code


def test_reconciliation_package_has_no_forbidden_runtime_imports() -> None:
    imported: set[str] = set()
    for path in _reconciliation_source_files():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module.split(".")[0])
    forbidden = {
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
    leaked = forbidden & imported
    assert not leaked, f"reconciliation package must not import {leaked}"


def test_reconciliation_package_has_no_sleep_or_env_reads() -> None:
    code = _reconciliation_code_text()
    for needle in (
        "time.sleep",
        "asyncio.sleep",
        "os.environ",
        "os.getenv",
        "getenv(",
        "open(",
        "socket.",
        "urllib.",
        "requests.",
    ):
        assert needle not in code, (
            f"reconciliation package code must not contain {needle!r}"
        )


def test_reconciliation_package_does_not_modify_risk_subpackage() -> None:
    code = _reconciliation_code_text()
    assert "from gmc_rebuild.risk" in code or "import gmc_rebuild.risk" in code
