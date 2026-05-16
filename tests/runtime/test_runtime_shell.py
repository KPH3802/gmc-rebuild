"""P4-06 inert local runtime shell boundary tests.

Pure-Python, in-memory, pytest-only tests for the inert local runtime
shell boundary introduced by :mod:`gmc_rebuild.runtime`. The tests
prove the boundary is:

- **local** — composes only the three already-merged in-memory
  fixtures via the abstract Protocol boundaries declared in
  :mod:`gmc_rebuild.risk`; no broker, no market-data feed, no network,
  no persistence, no scheduler, no daemon, no ``__main__``, no
  ``time.sleep``, no env-var read;
- **inert** — never trades, never places orders, never authorizes
  progression by itself; the read-only :meth:`RuntimeShell.evaluate`
  call is the shell's entire surface;
- **safety-gated** — a verdict is ``clear`` only when every required
  heartbeat is ``FRESH``, the kill switch is ``ARMED``, and
  reconciliation is ``CLEAN``; every other observed state produces a
  blocking verdict listing the specific blockers.

Authorization: ``governance/authorizations/2026-05-16_p4-06.md``.

Tests avoid ``pytest.raises`` / fixture-typed parameters so the mypy
strict pre-commit hook does not need a pytest-stub dependency, matching
the pattern used by ``tests/p4_02_composed/``.
"""

from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from pathlib import Path

from gmc_rebuild.heartbeat import InMemoryHeartbeat
from gmc_rebuild.kill_switch import InMemoryKillSwitch
from gmc_rebuild.reconciliation import InMemoryReconciliation
from gmc_rebuild.risk import (
    HeartbeatStatus,
    KillSwitchState,
    ReconciliationStatus,
)
from gmc_rebuild.runtime import (
    BLOCKER_HEARTBEAT_STALE,
    BLOCKER_KILL_SWITCH_TRIPPED,
    BLOCKER_RECONCILIATION_FAILED,
    BLOCKER_RECONCILIATION_UNAVAILABLE,
    BLOCKER_RECONCILIATION_WARNING,
    RuntimeShell,
    RuntimeShellError,
    SafetyVerdict,
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
    """Build a shell composed of the three in-memory fakes against a fixed clock.

    The fakes are constructed inline; no network, no I/O, no scheduler,
    no broker SDK, no env-var read. The shell receives the three
    protocol-typed instances by keyword via dependency injection.
    """
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


def _make_healthy_state(
    heartbeat: InMemoryHeartbeat,
    reconciliation: InMemoryReconciliation,
) -> None:
    """Stage a fully-healthy steady state across the three fakes."""
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=5))
    reconciliation.set_next(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"runtime-shell-scenario": "healthy"},
    )


# ---------------------------------------------------------------------------
# Safe default: a freshly-composed shell blocks
# ---------------------------------------------------------------------------


def test_freshly_composed_shell_blocks_with_safe_defaults() -> None:
    """A freshly composed shell is never ``clear``.

    ADR-002 / ADR-003 / ADR-005 prescribe safe defaults: an unknown
    heartbeat component is ``STALE``, a fresh kill switch is ``ARMED``,
    a fresh reconciliation is ``UNAVAILABLE``. The composed shell must
    report a blocking verdict listing the heartbeat staleness and the
    reconciliation unavailability.
    """
    shell, _, _, _ = _make_shell()
    verdict = shell.evaluate()
    assert isinstance(verdict, SafetyVerdict)
    assert verdict.clear is False
    assert BLOCKER_HEARTBEAT_STALE in verdict.blockers
    assert BLOCKER_RECONCILIATION_UNAVAILABLE in verdict.blockers
    assert BLOCKER_KILL_SWITCH_TRIPPED not in verdict.blockers
    assert verdict.kill_switch_state is KillSwitchState.ARMED
    assert verdict.reconciliation_status is ReconciliationStatus.UNAVAILABLE
    assert verdict.heartbeat_statuses["operator"] is HeartbeatStatus.STALE
    assert verdict.observed_at == "2026-05-16T15:00:00Z"


# ---------------------------------------------------------------------------
# Clear path: every control healthy
# ---------------------------------------------------------------------------


def test_shell_is_clear_only_when_all_three_controls_are_healthy() -> None:
    """``clear`` requires FRESH heartbeat + ARMED kill switch + CLEAN reconciliation."""
    shell, heartbeat, _, reconciliation = _make_shell()
    _make_healthy_state(heartbeat, reconciliation)
    verdict = shell.evaluate()
    assert verdict.clear is True
    assert verdict.blockers == ()
    assert verdict.heartbeat_statuses["operator"] is HeartbeatStatus.FRESH
    assert verdict.kill_switch_state is KillSwitchState.ARMED
    assert verdict.reconciliation_status is ReconciliationStatus.CLEAN


# ---------------------------------------------------------------------------
# Each individual blocker is reported
# ---------------------------------------------------------------------------


def test_heartbeat_stale_alone_blocks_progression() -> None:
    """STALE heartbeat alone blocks even when kill switch is ARMED and recon CLEAN."""
    shell, heartbeat, _, reconciliation = _make_shell()
    _make_healthy_state(heartbeat, reconciliation)
    # ADR-005 default staleness threshold is 8 hours; advance past it.
    heartbeat.advance(8 * 3600 + 1)
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert BLOCKER_HEARTBEAT_STALE in verdict.blockers
    assert BLOCKER_KILL_SWITCH_TRIPPED not in verdict.blockers
    assert BLOCKER_RECONCILIATION_FAILED not in verdict.blockers


def test_kill_switch_trip_alone_blocks_progression() -> None:
    """TRIPPED kill switch alone blocks even when heartbeat FRESH and recon CLEAN."""
    shell, heartbeat, kill_switch, reconciliation = _make_shell()
    _make_healthy_state(heartbeat, reconciliation)
    kill_switch.trip(reason="operator-test-trip", triggered_by="test-operator")
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert verdict.blockers == (BLOCKER_KILL_SWITCH_TRIPPED,)
    assert verdict.kill_switch_state is KillSwitchState.TRIPPED


def test_reconciliation_failed_alone_blocks_progression() -> None:
    """FAILED reconciliation alone blocks even when heartbeat FRESH and kill ARMED."""
    shell, heartbeat, _, reconciliation = _make_shell()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=5))
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=42.5,
        details={"runtime-shell-scenario": "material-mismatch"},
    )
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert verdict.blockers == (BLOCKER_RECONCILIATION_FAILED,)
    assert verdict.reconciliation_status is ReconciliationStatus.FAILED


def test_reconciliation_unavailable_alone_blocks_progression() -> None:
    """UNAVAILABLE reconciliation alone blocks; explicitly distinct from FAILED."""
    shell, heartbeat, _, _ = _make_shell()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=5))
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert verdict.blockers == (BLOCKER_RECONCILIATION_UNAVAILABLE,)
    assert verdict.reconciliation_status is ReconciliationStatus.UNAVAILABLE
    assert BLOCKER_RECONCILIATION_FAILED not in verdict.blockers


def test_reconciliation_warning_blocks_as_advisory_grade_blocker() -> None:
    """WARNING reconciliation surfaces as a distinct advisory blocker.

    The shell never authorizes progression on anything other than CLEAN;
    WARNING is reported as its own code so callers can distinguish it
    from FAILED and UNAVAILABLE without the shell making a trading
    decision.
    """
    shell, heartbeat, _, reconciliation = _make_shell()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=5))
    reconciliation.set_next(
        status=ReconciliationStatus.WARNING,
        tolerance=10.0,
        observed_delta=5.0,
        details={"runtime-shell-scenario": "advisory-band"},
    )
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert verdict.blockers == (BLOCKER_RECONCILIATION_WARNING,)
    assert verdict.reconciliation_status is ReconciliationStatus.WARNING


# ---------------------------------------------------------------------------
# Composed blockers: multiple simultaneous, deterministic ordering
# ---------------------------------------------------------------------------


def test_simultaneous_blockers_are_all_reported_in_documented_order() -> None:
    """All active blockers are listed in (heartbeat, kill, reconciliation) order."""
    shell, _, kill_switch, reconciliation = _make_shell()
    # heartbeat: never beat → STALE
    kill_switch.trip(reason="composed-test-trip", triggered_by="test-operator")
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=99.0,
        details={"runtime-shell-scenario": "composed"},
    )
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert verdict.blockers == (
        BLOCKER_HEARTBEAT_STALE,
        BLOCKER_KILL_SWITCH_TRIPPED,
        BLOCKER_RECONCILIATION_FAILED,
    )


def test_multiple_required_heartbeat_components_any_stale_blocks() -> None:
    """If *any* required heartbeat component is STALE, the shell blocks."""
    shell, heartbeat, _, reconciliation = _make_shell(
        components=("operator", "local_machine"),
    )
    # only one of the two required components has a recent beat
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=5))
    reconciliation.set_next(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"runtime-shell-scenario": "partial-heartbeats"},
    )
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert BLOCKER_HEARTBEAT_STALE in verdict.blockers
    assert verdict.heartbeat_statuses["operator"] is HeartbeatStatus.FRESH
    assert verdict.heartbeat_statuses["local_machine"] is HeartbeatStatus.STALE


# ---------------------------------------------------------------------------
# Inert / read-only properties
# ---------------------------------------------------------------------------


def test_evaluate_is_idempotent_when_underlying_state_is_unchanged() -> None:
    """Repeated evaluate() calls return the same verdict when state is unchanged.

    Asserts the shell does not mutate the kill switch or heartbeat on
    read. The reconciliation fake is consumed-on-read by design, so it
    is re-staged between calls to keep the comparison meaningful.
    """
    shell, heartbeat, _, reconciliation = _make_shell()
    _make_healthy_state(heartbeat, reconciliation)
    first = shell.evaluate()
    reconciliation.set_next(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"runtime-shell-scenario": "healthy"},
    )
    second = shell.evaluate()
    assert first.clear is True
    assert second.clear is True
    assert first.blockers == second.blockers
    assert first.heartbeat_statuses == second.heartbeat_statuses
    assert first.kill_switch_state is second.kill_switch_state
    assert first.reconciliation_status is second.reconciliation_status


def test_evaluate_does_not_trip_kill_switch_or_mutate_heartbeat() -> None:
    """Calling evaluate() must not mutate the underlying protocol instances."""
    shell, heartbeat, kill_switch, reconciliation = _make_shell()
    _make_healthy_state(heartbeat, reconciliation)
    pre_kill = kill_switch.current()
    pre_hb = heartbeat.status("operator")
    shell.evaluate()
    post_kill = kill_switch.current()
    post_hb = heartbeat.status("operator")
    assert pre_kill.state is KillSwitchState.ARMED
    assert post_kill.state is KillSwitchState.ARMED
    assert pre_hb.status is HeartbeatStatus.FRESH
    assert post_hb.status is HeartbeatStatus.FRESH


def test_verdict_is_frozen_immutable_dataclass() -> None:
    """The verdict is frozen; attribute assignment must raise."""
    shell, heartbeat, _, reconciliation = _make_shell()
    _make_healthy_state(heartbeat, reconciliation)
    verdict = shell.evaluate()
    try:
        verdict.clear = False  # type: ignore[misc]
    except Exception as exc:
        assert isinstance(exc, (AttributeError, TypeError))
    else:
        raise AssertionError("SafetyVerdict.clear must not be mutable")


def test_required_components_is_read_only_tuple() -> None:
    """The configured required-components surface is an immutable tuple."""
    shell, _, _, _ = _make_shell(components=("operator", "local_machine"))
    components = shell.required_components
    assert isinstance(components, tuple)
    assert tuple(components) == ("operator", "local_machine")


# ---------------------------------------------------------------------------
# Constructor input validation
# ---------------------------------------------------------------------------


def test_constructor_rejects_non_protocol_instances() -> None:
    """Each injected dependency must conform to its abstract Protocol."""
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    try:
        RuntimeShell(
            heartbeat=object(),  # type: ignore[arg-type]
            kill_switch=kill_switch,
            reconciliation=reconciliation,
            required_components=("operator",),
        )
    except RuntimeShellError:
        pass
    else:
        raise AssertionError("non-Protocol heartbeat must be rejected")
    try:
        RuntimeShell(
            heartbeat=heartbeat,
            kill_switch=object(),  # type: ignore[arg-type]
            reconciliation=reconciliation,
            required_components=("operator",),
        )
    except RuntimeShellError:
        pass
    else:
        raise AssertionError("non-Protocol kill_switch must be rejected")
    try:
        RuntimeShell(
            heartbeat=heartbeat,
            kill_switch=kill_switch,
            reconciliation=object(),  # type: ignore[arg-type]
            required_components=("operator",),
        )
    except RuntimeShellError:
        pass
    else:
        raise AssertionError("non-Protocol reconciliation must be rejected")


def test_constructor_rejects_empty_required_components() -> None:
    """At least one required component must be supplied."""
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    try:
        RuntimeShell(
            heartbeat=heartbeat,
            kill_switch=kill_switch,
            reconciliation=reconciliation,
            required_components=(),
        )
    except RuntimeShellError:
        pass
    else:
        raise AssertionError("empty required_components must be rejected")


def test_constructor_rejects_duplicate_or_whitespace_component_names() -> None:
    """Required-component names are unique, non-empty, whitespace-free strings."""
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    for bad in (("",), ("ok", ""), ("dup", "dup"), ("has space",)):
        try:
            RuntimeShell(
                heartbeat=heartbeat,
                kill_switch=kill_switch,
                reconciliation=reconciliation,
                required_components=bad,
            )
        except RuntimeShellError:
            continue
        raise AssertionError(f"required_components={bad!r} must be rejected")


# ---------------------------------------------------------------------------
# Inertness via AST: no forbidden surfaces
# ---------------------------------------------------------------------------


def _runtime_source_files() -> list[Path]:
    src_root = Path(__file__).resolve().parents[2] / "src" / "gmc_rebuild" / "runtime"
    return sorted(src_root.rglob("*.py"))


def test_runtime_package_exists_under_authorized_path() -> None:
    """The new runtime package lives under the exact authorized path."""
    files = _runtime_source_files()
    assert files, "src/gmc_rebuild/runtime/ must contain at least one .py file"
    for path in files:
        assert path.suffix == ".py"


def test_runtime_package_has_no_main_entry_point() -> None:
    """No ``__main__`` entry point may exist anywhere in the runtime package."""
    src_root = Path(__file__).resolve().parents[2] / "src" / "gmc_rebuild" / "runtime"
    assert not (src_root / "__main__.py").exists()
    for path in _runtime_source_files():
        source = path.read_text(encoding="utf-8")
        assert '__name__ == "__main__"' not in source
        assert "__name__ == '__main__'" not in source


def test_runtime_package_imports_are_within_inert_allowlist() -> None:
    """The runtime package imports only inert, already-authorized modules.

    Verifies via AST that no ``import`` or ``from ... import`` statement
    in ``src/gmc_rebuild/runtime/`` reaches into broker SDKs, network
    libraries, scheduler libraries, persistence libraries, secrets
    handling, ``time.sleep`` /``asyncio.sleep`` carriers, env-var
    access, or any concrete fixture under
    :mod:`gmc_rebuild.heartbeat` / :mod:`gmc_rebuild.kill_switch` /
    :mod:`gmc_rebuild.reconciliation`. The shell composes the abstract
    Protocol boundaries declared in :mod:`gmc_rebuild.risk` only.
    """
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
    for path in _runtime_source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    _assert_import_is_inert(
                        name,
                        path,
                        forbidden_prefixes,
                        forbidden_exact,
                        allowed_prefixes,
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                _assert_import_is_inert(
                    module,
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
        f"{path}: import {name!r} is not allowed for the inert runtime shell"
    )
    for prefix in forbidden_prefixes:
        assert not (name == prefix or name.startswith(prefix + ".")), (
            f"{path}: import {name!r} reaches into forbidden surface {prefix!r}"
        )
    if name and not any(name == ap or name.startswith(ap + ".") for ap in allowed_prefixes):
        raise AssertionError(
            f"{path}: import {name!r} is not in the inert-runtime allowlist {allowed_prefixes!r}"
        )


def test_runtime_package_executable_code_has_no_forbidden_attribute_access() -> None:
    """No executable attribute access in the runtime source reaches a forbidden surface.

    Belt-and-braces AST scan: walks every :class:`ast.Attribute` and
    :class:`ast.Call` node in ``src/gmc_rebuild/runtime/`` and asserts
    that no executable expression names ``time.sleep``, ``asyncio.sleep``,
    ``os.environ``, ``os.getenv``, ``subprocess.*``, ``socket.*``,
    ``urllib.*``, ``requests.*``, ``httpx.*``, ``aiohttp.*``, ``sqlite3.*``,
    ``open(...)``, or any of the named broker SDKs. Docstrings and
    comments are deliberately excluded — they may mention forbidden
    surfaces only to document that the surface is forbidden.

    The AST import test above is the primary guarantee; this scan
    catches any dynamic-attribute / runtime-shadowed bypass.
    """
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

    for path in _runtime_source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                flat = _flatten_attribute(node)
                if flat is None:
                    continue
                assert flat[:2] not in forbidden_attr_paths, (
                    f"{path}: forbidden attribute access {'.'.join(flat)} in inert runtime source"
                )
                assert flat[0] not in forbidden_attr_roots, (
                    f"{path}: forbidden attribute root {flat[0]!r} in inert runtime source"
                )
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_callables, (
                    f"{path}: forbidden builtin call {node.func.id!r} in inert runtime source"
                )
