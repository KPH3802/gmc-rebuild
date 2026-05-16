"""P4-07 read-only operator view tests.

Pure-Python, in-memory, pytest-only tests for the read-only operator
view added by :mod:`gmc_rebuild.runtime._operator_view`. The tests prove
the view is:

- **read-only / inert** — :func:`format_safety_verdict` takes an
  already-built :class:`SafetyVerdict` by value and does not call any
  protocol method; the underlying :class:`InMemoryHeartbeat`,
  :class:`InMemoryKillSwitch`, and :class:`InMemoryReconciliation`
  fixtures are never mutated by the view;
- **deterministic** — the same verdict always produces the same view
  and the same rendered text, and the heartbeat lines are emitted in
  sorted component-name order;
- **local** — pure Python; no broker, no market data, no order, no
  scheduler, no daemon, no network, no persistence, no env-var, no
  secrets, no ``time.sleep``, no ``__main__``;
- **safety-preserving** — a blocked verdict is always rendered as
  ``BLOCKED`` listing every blocker; a ``clear`` verdict is rendered as
  ``CLEAR`` with no blocker lines; the view cannot widen the verdict.

Authorization: ``governance/authorizations/2026-05-16_p4-07.md``.

Tests avoid ``pytest.raises`` / fixture-typed parameters so the mypy
strict pre-commit hook does not need a pytest-stub dependency, matching
the pattern used by ``tests/runtime/test_runtime_shell.py``.
"""

from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from pathlib import Path

from gmc_rebuild.heartbeat import InMemoryHeartbeat
from gmc_rebuild.kill_switch import InMemoryKillSwitch
from gmc_rebuild.reconciliation import InMemoryReconciliation
from gmc_rebuild.risk import HeartbeatStatus, KillSwitchState, ReconciliationStatus
from gmc_rebuild.runtime import (
    BLOCKER_HEARTBEAT_STALE,
    BLOCKER_KILL_SWITCH_TRIPPED,
    BLOCKER_RECONCILIATION_FAILED,
    BLOCKER_RECONCILIATION_UNAVAILABLE,
    BLOCKER_RECONCILIATION_WARNING,
    VERDICT_BLOCKED,
    VERDICT_CLEAR,
    OperatorSafetyView,
    RuntimeShell,
    SafetyVerdict,
    format_safety_verdict,
)

_FIXED_CLOCK = datetime(2026, 5, 16, 15, 0, 0, tzinfo=UTC)
_REQUIRED_COMPONENTS: tuple[str, ...] = ("operator",)


def _make_shell(
    *,
    components: tuple[str, ...] = _REQUIRED_COMPONENTS,
) -> tuple[
    RuntimeShell,
    InMemoryHeartbeat,
    InMemoryKillSwitch,
    InMemoryReconciliation,
]:
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    shell = RuntimeShell(
        heartbeat=heartbeat,
        kill_switch=kill_switch,
        reconciliation=reconciliation,
        required_components=components,
    )
    return shell, heartbeat, kill_switch, reconciliation


def _stage_healthy(
    heartbeat: InMemoryHeartbeat,
    reconciliation: InMemoryReconciliation,
    *,
    components: tuple[str, ...] = _REQUIRED_COMPONENTS,
) -> None:
    for component in components:
        heartbeat.beat(component, _FIXED_CLOCK - timedelta(minutes=5))
    reconciliation.set_next(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"operator-view-scenario": "healthy"},
    )


# ---------------------------------------------------------------------------
# Clear verdict rendering
# ---------------------------------------------------------------------------


def test_clear_verdict_renders_as_clear_with_no_blocker_lines() -> None:
    shell, heartbeat, _, reconciliation = _make_shell()
    _stage_healthy(heartbeat, reconciliation)
    verdict = shell.evaluate()
    view = format_safety_verdict(verdict)
    assert isinstance(view, OperatorSafetyView)
    assert view.status == VERDICT_CLEAR
    assert view.blocker_lines == ()
    assert view.kill_switch_line == f"kill_switch: {KillSwitchState.ARMED.value}"
    assert view.reconciliation_line == f"reconciliation: {ReconciliationStatus.CLEAN.value}"
    assert view.heartbeat_lines == (f"heartbeat[operator]: {HeartbeatStatus.FRESH.value}",)
    assert view.observed_at == verdict.observed_at


def test_clear_verdict_render_includes_clear_label_and_no_blockers_section() -> None:
    shell, heartbeat, _, reconciliation = _make_shell()
    _stage_healthy(heartbeat, reconciliation)
    verdict = shell.evaluate()
    rendered = format_safety_verdict(verdict).render()
    assert "safety: CLEAR" in rendered
    assert "blockers:" not in rendered
    assert "observed_at: 2026-05-16T15:00:00Z" in rendered


# ---------------------------------------------------------------------------
# Blocked verdict rendering — every blocker reaches the operator view
# ---------------------------------------------------------------------------


def test_blocked_verdict_renders_as_blocked_with_every_blocker_line() -> None:
    shell, _, kill_switch, reconciliation = _make_shell()
    kill_switch.trip(reason="operator-view-test", triggered_by="test-operator")
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=99.0,
        details={"operator-view-scenario": "composed"},
    )
    verdict = shell.evaluate()
    view = format_safety_verdict(verdict)
    assert view.status == VERDICT_BLOCKED
    assert len(view.blocker_lines) == len(verdict.blockers)
    rendered = view.render()
    assert "safety: BLOCKED" in rendered
    assert "blockers:" in rendered
    assert "heartbeat stale" in rendered
    assert "kill switch tripped" in rendered
    assert "reconciliation failed" in rendered


def test_unavailable_reconciliation_blocker_is_distinct_from_failed() -> None:
    shell, heartbeat, _, _ = _make_shell()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=5))
    verdict = shell.evaluate()
    view = format_safety_verdict(verdict)
    assert view.status == VERDICT_BLOCKED
    assert verdict.blockers == (BLOCKER_RECONCILIATION_UNAVAILABLE,)
    assert any("unavailable" in line for line in view.blocker_lines)
    assert not any("failed" in line for line in view.blocker_lines)


def test_warning_reconciliation_is_advisory_blocker_line() -> None:
    shell, heartbeat, _, reconciliation = _make_shell()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=5))
    reconciliation.set_next(
        status=ReconciliationStatus.WARNING,
        tolerance=10.0,
        observed_delta=5.0,
        details={"operator-view-scenario": "advisory"},
    )
    verdict = shell.evaluate()
    view = format_safety_verdict(verdict)
    assert view.status == VERDICT_BLOCKED
    assert verdict.blockers == (BLOCKER_RECONCILIATION_WARNING,)
    assert any("advisory" in line for line in view.blocker_lines)


def test_blocker_line_order_matches_verdict_blocker_order() -> None:
    shell, _, kill_switch, reconciliation = _make_shell()
    kill_switch.trip(reason="order-test", triggered_by="test-operator")
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=42.0,
        details={"operator-view-scenario": "ordering"},
    )
    verdict = shell.evaluate()
    view = format_safety_verdict(verdict)
    assert verdict.blockers == (
        BLOCKER_HEARTBEAT_STALE,
        BLOCKER_KILL_SWITCH_TRIPPED,
        BLOCKER_RECONCILIATION_FAILED,
    )
    assert "heartbeat" in view.blocker_lines[0]
    assert "kill switch" in view.blocker_lines[1]
    assert "reconciliation failed" in view.blocker_lines[2]


# ---------------------------------------------------------------------------
# Read-only / inert: the view never mutates the underlying fixtures
# ---------------------------------------------------------------------------


def test_format_does_not_mutate_underlying_protocol_instances() -> None:
    shell, heartbeat, kill_switch, reconciliation = _make_shell()
    _stage_healthy(heartbeat, reconciliation)
    verdict = shell.evaluate()
    pre_kill = kill_switch.current()
    pre_hb = heartbeat.status("operator")
    format_safety_verdict(verdict)
    format_safety_verdict(verdict)
    format_safety_verdict(verdict)
    post_kill = kill_switch.current()
    post_hb = heartbeat.status("operator")
    assert pre_kill.state is KillSwitchState.ARMED
    assert post_kill.state is KillSwitchState.ARMED
    assert pre_hb.status is HeartbeatStatus.FRESH
    assert post_hb.status is HeartbeatStatus.FRESH


def test_format_is_deterministic_for_same_verdict() -> None:
    shell, heartbeat, _, reconciliation = _make_shell()
    _stage_healthy(heartbeat, reconciliation)
    verdict = shell.evaluate()
    first = format_safety_verdict(verdict)
    second = format_safety_verdict(verdict)
    assert first == second
    assert first.render() == second.render()


def test_view_is_frozen_immutable_dataclass() -> None:
    shell, heartbeat, _, reconciliation = _make_shell()
    _stage_healthy(heartbeat, reconciliation)
    view = format_safety_verdict(shell.evaluate())
    try:
        view.status = VERDICT_BLOCKED  # type: ignore[misc]
    except Exception as exc:
        assert isinstance(exc, (AttributeError, TypeError))
    else:
        raise AssertionError("OperatorSafetyView.status must not be mutable")


# ---------------------------------------------------------------------------
# Safety-preserving: the view cannot widen the verdict
# ---------------------------------------------------------------------------


def test_blocked_verdict_cannot_be_rendered_as_clear() -> None:
    shell, _, _, _ = _make_shell()
    verdict = shell.evaluate()
    assert verdict.clear is False
    view = format_safety_verdict(verdict)
    assert view.status != VERDICT_CLEAR
    assert view.status == VERDICT_BLOCKED
    assert view.blocker_lines  # non-empty


def test_clear_status_only_when_verdict_is_clear() -> None:
    shell, heartbeat, _, reconciliation = _make_shell()
    _stage_healthy(heartbeat, reconciliation)
    clear_verdict = shell.evaluate()
    clear_view = format_safety_verdict(clear_verdict)
    assert clear_view.status == VERDICT_CLEAR
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=77.0,
        details={"operator-view-scenario": "flip"},
    )
    blocked_verdict = shell.evaluate()
    blocked_view = format_safety_verdict(blocked_verdict)
    assert blocked_view.status == VERDICT_BLOCKED


# ---------------------------------------------------------------------------
# Multi-component heartbeat lines are sorted deterministically
# ---------------------------------------------------------------------------


def test_heartbeat_lines_are_emitted_in_sorted_component_order() -> None:
    components = ("z_component", "a_component", "m_component")
    shell, heartbeat, _, reconciliation = _make_shell(components=components)
    _stage_healthy(heartbeat, reconciliation, components=components)
    view = format_safety_verdict(shell.evaluate())
    component_names = [line.split("[", 1)[1].split("]", 1)[0] for line in view.heartbeat_lines]
    assert component_names == sorted(components)


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_format_rejects_non_verdict_input() -> None:
    try:
        format_safety_verdict(object())  # type: ignore[arg-type]
    except TypeError:
        return
    raise AssertionError("format_safety_verdict must reject non-SafetyVerdict input")


# ---------------------------------------------------------------------------
# Inertness via AST: the operator-view source itself touches no forbidden surface
# ---------------------------------------------------------------------------


def _operator_view_source_file() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "src"
        / "gmc_rebuild"
        / "runtime"
        / "_operator_view.py"
    )


def test_operator_view_source_exists_under_authorized_path() -> None:
    path = _operator_view_source_file()
    assert path.is_file()
    assert path.suffix == ".py"


def test_operator_view_source_has_no_main_entry_point() -> None:
    source = _operator_view_source_file().read_text(encoding="utf-8")
    assert '__name__ == "__main__"' not in source
    assert "__name__ == '__main__'" not in source


def test_operator_view_source_imports_are_within_inert_allowlist() -> None:
    """The operator view imports only inert, already-authorized modules."""
    forbidden_prefixes = (
        "socket",
        "ssl",
        "http",
        "urllib",
        "requests",
        "aiohttp",
        "httpx",
        "asyncio",
        "threading",
        "multiprocessing",
        "subprocess",
        "sched",
        "signal",
        "sqlite3",
        "pickle",
        "shelve",
        "tempfile",
        "pathlib",
        "os",
        "os.path",
        "time",
        "secrets",
        "hmac",
        "hashlib",
        "ibapi",
        "ib_insync",
        "alpaca",
        "polygon",
        "yfinance",
    )
    forbidden_exact = {
        "gmc_rebuild.heartbeat",
        "gmc_rebuild.kill_switch",
        "gmc_rebuild.reconciliation",
    }
    allowed_prefixes = (
        "__future__",
        "collections",
        "collections.abc",
        "dataclasses",
        "types",
        "typing",
        "gmc_rebuild.risk",
        "gmc_rebuild.runtime",
    )
    path = _operator_view_source_file()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _assert_import_is_inert(
                    alias.name,
                    path,
                    forbidden_prefixes,
                    forbidden_exact,
                    allowed_prefixes,
                )
        elif isinstance(node, ast.ImportFrom):
            _assert_import_is_inert(
                node.module or "",
                path,
                forbidden_prefixes,
                forbidden_exact,
                allowed_prefixes,
            )


def _assert_import_is_inert(
    name: str,
    path: Path,
    forbidden_prefixes: tuple[str, ...],
    forbidden_exact: set[str],
    allowed_prefixes: tuple[str, ...],
) -> None:
    assert name not in forbidden_exact, (
        f"{path}: import {name!r} is not allowed for the inert operator view"
    )
    for prefix in forbidden_prefixes:
        assert not (name == prefix or name.startswith(prefix + ".")), (
            f"{path}: import {name!r} reaches into forbidden surface {prefix!r}"
        )
    if name and not any(name == ap or name.startswith(ap + ".") for ap in allowed_prefixes):
        raise AssertionError(
            f"{path}: import {name!r} is not in the inert-runtime allowlist {allowed_prefixes!r}"
        )


def test_operator_view_source_has_no_forbidden_attribute_access() -> None:
    """No executable attribute access in the operator-view source reaches a forbidden surface."""
    forbidden_attr_paths: set[tuple[str, ...]] = {
        ("time", "sleep"),
        ("asyncio", "sleep"),
        ("os", "environ"),
        ("os", "getenv"),
    }
    forbidden_attr_roots: set[str] = {
        "subprocess",
        "socket",
        "urllib",
        "requests",
        "httpx",
        "aiohttp",
        "sqlite3",
        "ibapi",
        "ib_insync",
        "alpaca",
        "polygon",
        "yfinance",
    }
    forbidden_callables: set[str] = {"open", "exec", "eval", "compile"}

    def _flatten_attribute(node: ast.Attribute) -> tuple[str, ...] | None:
        parts: list[str] = [node.attr]
        current: ast.expr = node.value
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
            return tuple(reversed(parts))
        return None

    path = _operator_view_source_file()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            flat = _flatten_attribute(node)
            if flat is None:
                continue
            assert flat[:2] not in forbidden_attr_paths, (
                f"{path}: forbidden attribute access {'.'.join(flat)} in inert operator view"
            )
            assert flat[0] not in forbidden_attr_roots, (
                f"{path}: forbidden attribute root {flat[0]!r} in inert operator view"
            )
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_callables, (
                f"{path}: forbidden builtin call {node.func.id!r} in inert operator view"
            )


# ---------------------------------------------------------------------------
# Surface check: the operator view exposes nothing that authorizes trading
# ---------------------------------------------------------------------------


def test_operator_view_surface_does_not_expose_trading_or_mutation_methods() -> None:
    """The OperatorSafetyView surface is fields + a pure ``render`` method only."""
    shell, heartbeat, _, reconciliation = _make_shell()
    _stage_healthy(heartbeat, reconciliation)
    view = format_safety_verdict(shell.evaluate())
    public_attrs = {name for name in dir(view) if not name.startswith("_")}
    expected = {
        "status",
        "blocker_lines",
        "heartbeat_lines",
        "kill_switch_line",
        "reconciliation_line",
        "observed_at",
        "render",
    }
    assert public_attrs == expected, f"unexpected operator-view surface: {public_attrs}"


def test_operator_view_does_not_carry_protocol_instances() -> None:
    """The view holds plain strings/tuples — no live protocol instances escape into it."""
    shell, heartbeat, _, reconciliation = _make_shell()
    _stage_healthy(heartbeat, reconciliation)
    view = format_safety_verdict(shell.evaluate())
    assert isinstance(view.status, str)
    assert isinstance(view.blocker_lines, tuple)
    assert isinstance(view.heartbeat_lines, tuple)
    assert isinstance(view.kill_switch_line, str)
    assert isinstance(view.reconciliation_line, str)
    assert isinstance(view.observed_at, str)
    for line in view.heartbeat_lines:
        assert isinstance(line, str)
    for line in view.blocker_lines:
        assert isinstance(line, str)


# Touch the SafetyVerdict import so it is exercised by at least one assertion.
def test_safety_verdict_type_is_re_exported_from_runtime_package() -> None:
    assert SafetyVerdict.__module__.startswith("gmc_rebuild.runtime")
