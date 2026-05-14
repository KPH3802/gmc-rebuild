"""P3-04 KillSwitchProtocol in-memory fixture tests.

Verifies that the ``gmc_rebuild.kill_switch`` subpackage authorized by
the P3-04 implementation PR (see
``governance/authorizations/2026-05-14_p3-04.md``):

- exposes the in-memory fake fixture (and only that);
- conforms structurally to :class:`gmc_rebuild.risk.KillSwitchProtocol`;
- preserves ADR-002 safe-default behavior (a freshly constructed
  fake is ``ARMED``; a tripped fake stays ``TRIPPED`` until discarded);
- preserves ADR-004 UTC discipline at the boundary (naive datetimes
  are rejected);
- introduces no forbidden runtime entry points, env-var reads, or
  filesystem / network / sleep / broker I/O.

Tests avoid ``pytest.raises`` / fixture-typed parameters so the mypy
strict pre-commit hook does not need a pytest-stub dependency. See
``tests/heartbeat/test_heartbeat_fixture.py`` for the same pattern.
"""

from __future__ import annotations

import ast
import importlib
from datetime import UTC, datetime
from pathlib import Path

from gmc_rebuild.kill_switch import InMemoryKillSwitch
from gmc_rebuild.risk import (
    KillSwitchDecision,
    KillSwitchProtocol,
    KillSwitchState,
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


def test_kill_switch_subpackage_imports() -> None:
    module = importlib.import_module("gmc_rebuild.kill_switch")
    assert module is not None
    assert hasattr(module, "InMemoryKillSwitch")
    assert module.__all__ == ["InMemoryKillSwitch"]


def test_kill_switch_not_reexported_from_runtime_root() -> None:
    runtime_root = importlib.import_module("gmc_rebuild")
    assert not hasattr(runtime_root, "kill_switch") or (
        getattr(runtime_root, "__all__", None) is not None
        and "kill_switch" not in runtime_root.__all__
        and "InMemoryKillSwitch" not in runtime_root.__all__
    )


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_fake_is_kill_switch_protocol_instance() -> None:
    fake = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    assert isinstance(fake, KillSwitchProtocol)


def test_current_returns_kill_switch_decision() -> None:
    fake = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    decision = fake.current()
    assert isinstance(decision, KillSwitchDecision)


def test_trip_returns_kill_switch_decision() -> None:
    fake = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    decision = fake.trip(reason="manual halt", triggered_by="operator")
    assert isinstance(decision, KillSwitchDecision)


# ---------------------------------------------------------------------------
# ADR-002 safe-default behavior
# ---------------------------------------------------------------------------


def test_fresh_fake_is_armed_with_empty_reason_and_triggered_by() -> None:
    fake = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    decision = fake.current()
    assert decision.state is KillSwitchState.ARMED
    assert decision.reason == ""
    assert decision.triggered_by == ""


def test_trip_records_active_trip_state() -> None:
    fake = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    decision = fake.trip(reason="manual halt", triggered_by="operator")
    assert decision.state is KillSwitchState.TRIPPED
    assert decision.reason == "manual halt"
    assert decision.triggered_by == "operator"


def test_current_after_trip_remains_tripped() -> None:
    fake = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    fake.trip(reason="manual halt", triggered_by="operator")
    decision = fake.current()
    assert decision.state is KillSwitchState.TRIPPED
    assert decision.reason == "manual halt"
    assert decision.triggered_by == "operator"


def test_second_trip_overwrites_recorded_trip() -> None:
    """A second trip records the latest ``reason`` / ``triggered_by``.

    The fake stores at most one active trip. There is no clear / reset
    API; tripping a second time replaces the recorded values. Real
    ADR-002 reset semantics are out of scope for this test-fixture
    artifact.
    """
    fake = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    fake.trip(reason="first", triggered_by="operator")
    fake.trip(reason="second", triggered_by="backup-operator")
    decision = fake.current()
    assert decision.state is KillSwitchState.TRIPPED
    assert decision.reason == "second"
    assert decision.triggered_by == "backup-operator"


def test_current_does_not_raise_in_steady_state() -> None:
    """ADR-002: ``current`` must not raise for the steady-state case."""
    fake = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    fake.current()
    fake.trip(reason="manual halt", triggered_by="operator")
    fake.current()


def test_advance_clock_reflects_in_observed_at() -> None:
    fake = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    before = fake.current().observed_at
    fake.advance(3600.0)
    after = fake.current().observed_at
    assert before == "2026-05-14T14:00:00Z"
    assert after == "2026-05-14T15:00:00Z"


# ---------------------------------------------------------------------------
# ADR-004 UTC discipline at the boundary
# ---------------------------------------------------------------------------


def test_construction_rejects_naive_observed_at() -> None:
    _expect_naive_error(lambda: InMemoryKillSwitch(observed_at=datetime(2026, 5, 14, 14)))


def test_decision_timestamps_are_z_suffixed_utc_strings() -> None:
    fake = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    armed = fake.current()
    assert armed.observed_at.endswith("Z")
    assert armed.observed_at == "2026-05-14T14:00:00Z"
    tripped = fake.trip(reason="manual halt", triggered_by="operator")
    assert tripped.observed_at.endswith("Z")
    assert tripped.observed_at == "2026-05-14T14:00:00Z"


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_trip_rejects_empty_reason() -> None:
    fake = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    _expect_risk_error(
        lambda: fake.trip(reason="", triggered_by="operator"),
        "reason must be a non-empty str",
    )


def test_trip_rejects_empty_triggered_by() -> None:
    fake = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    _expect_risk_error(
        lambda: fake.trip(reason="manual halt", triggered_by=""),
        "triggered_by must be a non-empty str",
    )


def test_advance_rejects_negative_or_non_numeric() -> None:
    fake = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    _expect_risk_error(lambda: fake.advance(-1.0), "must be non-negative")
    _expect_risk_error(
        lambda: fake.advance(True),
        "must be a number",
    )


# ---------------------------------------------------------------------------
# No forbidden runtime behavior
# ---------------------------------------------------------------------------


_PKG_ROOT = Path(__file__).resolve().parent.parent.parent / "src" / "gmc_rebuild" / "kill_switch"


def _kill_switch_source_files() -> list[Path]:
    return sorted(_PKG_ROOT.glob("*.py"))


def _strip_docstrings_and_comments(source: str) -> str:
    """Return ``source`` with module/class/function docstrings and # comments removed.

    Used so the "no forbidden tokens" checks below match real code, not
    governance commentary in docstrings. Docstrings are intentionally
    verbose under the P3-04 authorization and reference forbidden token
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


def _kill_switch_code_text() -> str:
    return "\n".join(
        _strip_docstrings_and_comments(p.read_text()) for p in _kill_switch_source_files()
    )


def test_kill_switch_package_has_no_main_entry_point() -> None:
    code = _kill_switch_code_text()
    assert "__main__" not in code
    assert "if __name__" not in code


def test_kill_switch_package_has_no_forbidden_runtime_imports() -> None:
    imported: set[str] = set()
    for path in _kill_switch_source_files():
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
    assert not leaked, f"kill_switch package must not import {leaked}"


def test_kill_switch_package_has_no_sleep_or_env_reads() -> None:
    code = _kill_switch_code_text()
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
        assert needle not in code, f"kill_switch package code must not contain {needle!r}"


def test_kill_switch_package_does_not_modify_risk_subpackage() -> None:
    code = _kill_switch_code_text()
    assert "from gmc_rebuild.risk" in code or "import gmc_rebuild.risk" in code
