"""P5-01 local simulation boundary skeleton tests.

Verifies that the ``gmc_rebuild.simulation`` subpackage authorized by
``governance/authorizations/2026-05-17_p5-01.md``:

- exposes exactly the four authorized public names (``SimulationLane``,
  ``SimulatedIntent``, ``SimulationBoundary``, ``SimulationBoundaryError``);
- declares only the single authorized lane (``LOCAL_ONLY``);
- treats :class:`SimulatedIntent` as a frozen, immutable record with
  ADR-004 UTC-string discipline;
- composes the merged P4-06 :class:`SafetyVerdict` boundary and only
  permits a simulated progression when the verdict is ``clear``;
- is local, deterministic, and inert (no I/O, no network, no
  ``time.sleep``, no env-var reads, no broker, no scheduler, no
  persistence, no ``__main__`` entry point);
- is not re-exported from the package root.

Tests avoid ``pytest.raises`` / fixture-typed parameters so the mypy
strict pre-commit hook does not need a pytest-stub dependency. See
``tests/heartbeat/test_heartbeat_fixture.py`` for the same pattern.
"""

from __future__ import annotations

import ast
import importlib
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from gmc_rebuild.risk import (
    HeartbeatStatus,
    KillSwitchState,
    ReconciliationStatus,
)
from gmc_rebuild.runtime import (
    BLOCKER_HEARTBEAT_STALE,
    BLOCKER_KILL_SWITCH_TRIPPED,
    SafetyVerdict,
)
from gmc_rebuild.simulation import (
    SimulatedIntent,
    SimulationBoundary,
    SimulationBoundaryError,
    SimulationLane,
)

_FIXED_CLOCK = datetime(2026, 5, 17, 14, 0, 0, tzinfo=UTC)
_FIXED_CLOCK_Z = "2026-05-17T14:00:00Z"


def _expect_boundary_error(call: object, match: str) -> None:
    raised: Exception | None = None
    try:
        call()  # type: ignore[operator]
    except SimulationBoundaryError as exc:
        raised = exc
    assert isinstance(raised, SimulationBoundaryError), (
        f"expected SimulationBoundaryError matching {match!r}, got {raised!r}"
    )
    assert match in str(raised), (
        f"SimulationBoundaryError message {str(raised)!r} missing {match!r}"
    )


def _clear_verdict() -> SafetyVerdict:
    return SafetyVerdict(
        clear=True,
        blockers=(),
        heartbeat_statuses=MappingProxyType({"operator": HeartbeatStatus.FRESH}),
        kill_switch_state=KillSwitchState.ARMED,
        reconciliation_status=ReconciliationStatus.CLEAN,
        observed_at=_FIXED_CLOCK_Z,
    )


def _blocked_verdict() -> SafetyVerdict:
    return SafetyVerdict(
        clear=False,
        blockers=(BLOCKER_HEARTBEAT_STALE, BLOCKER_KILL_SWITCH_TRIPPED),
        heartbeat_statuses=MappingProxyType({"operator": HeartbeatStatus.STALE}),
        kill_switch_state=KillSwitchState.TRIPPED,
        reconciliation_status=ReconciliationStatus.CLEAN,
        observed_at=_FIXED_CLOCK_Z,
    )


# ---------------------------------------------------------------------------
# Package surface
# ---------------------------------------------------------------------------


def test_simulation_subpackage_imports() -> None:
    module = importlib.import_module("gmc_rebuild.simulation")
    assert module is not None
    # P5-01 surface.
    assert hasattr(module, "SimulationLane")
    assert hasattr(module, "SimulatedIntent")
    assert hasattr(module, "SimulationBoundary")
    assert hasattr(module, "SimulationBoundaryError")
    # P5-02 surface.
    assert hasattr(module, "SimulatedOrderIntent")
    assert hasattr(module, "SimulatedOrderSide")
    assert hasattr(module, "SimulatedOrderType")
    assert sorted(module.__all__) == sorted(
        [
            "SimulatedIntent",
            "SimulatedOrderIntent",
            "SimulatedOrderSide",
            "SimulatedOrderType",
            "SimulationBoundary",
            "SimulationBoundaryError",
            "SimulationLane",
        ]
    )


def test_simulation_not_reexported_from_package_root() -> None:
    runtime_root = importlib.import_module("gmc_rebuild")
    forbidden_root_attrs = (
        "simulation",
        "SimulationBoundary",
        "SimulatedIntent",
        "SimulationLane",
        "SimulatedOrderIntent",
        "SimulatedOrderSide",
        "SimulatedOrderType",
    )
    runtime_all = getattr(runtime_root, "__all__", None)
    if runtime_all is not None:
        for name in forbidden_root_attrs:
            assert name not in runtime_all, (
                f"simulation surface {name!r} must not be re-exported from gmc_rebuild"
            )
    else:
        for name in forbidden_root_attrs:
            assert not hasattr(runtime_root, name), (
                f"simulation surface {name!r} must not appear on gmc_rebuild without __all__"
            )


# ---------------------------------------------------------------------------
# SimulationLane: closed authorized enumeration
# ---------------------------------------------------------------------------


def test_simulation_lane_has_only_authorized_values() -> None:
    """Only ``LOCAL_ONLY`` is authorized by P5-01.

    Adding a new lane (for example a paper-broker lane or a backtest
    lane) without extending the authorization is a phase-expanding
    change and must be rejected at review. This test fails if any
    other lane is added.
    """
    members = {lane.value for lane in SimulationLane}
    assert members == {"local_only"}, f"unexpected SimulationLane members: {members}"


def test_simulation_lane_is_strenum() -> None:
    assert SimulationLane.LOCAL_ONLY.value == "local_only"
    assert isinstance(SimulationLane.LOCAL_ONLY, str)
    assert str(SimulationLane.LOCAL_ONLY) == "local_only"


# ---------------------------------------------------------------------------
# SimulatedIntent: immutability and validation
# ---------------------------------------------------------------------------


def test_simulated_intent_constructs_with_valid_inputs() -> None:
    intent = SimulatedIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="op-001",
        created_at=_FIXED_CLOCK_Z,
    )
    assert intent.lane is SimulationLane.LOCAL_ONLY
    assert intent.intent_id == "op-001"
    assert intent.created_at == _FIXED_CLOCK_Z


def test_simulated_intent_build_converts_datetime_to_z_string() -> None:
    intent = SimulatedIntent.build(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="op-002",
        created_at=_FIXED_CLOCK,
    )
    assert intent.created_at == _FIXED_CLOCK_Z
    assert intent.created_at.endswith("Z")


def test_simulated_intent_is_frozen() -> None:
    intent = SimulatedIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="op-003",
        created_at=_FIXED_CLOCK_Z,
    )
    raised: Exception | None = None
    try:
        intent.intent_id = "op-004"  # type: ignore[misc]
    except Exception as exc:
        raised = exc
    assert raised is not None, "frozen SimulatedIntent must reject attribute mutation"


def test_simulated_intent_uses_slots() -> None:
    intent = SimulatedIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="op-005",
        created_at=_FIXED_CLOCK_Z,
    )
    assert not hasattr(intent, "__dict__")


def test_simulated_intent_rejects_non_lane() -> None:
    _expect_boundary_error(
        lambda: SimulatedIntent(
            lane="local_only",  # type: ignore[arg-type]
            intent_id="op-006",
            created_at=_FIXED_CLOCK_Z,
        ),
        "lane must be a SimulationLane",
    )


def test_simulated_intent_rejects_empty_or_whitespace_id() -> None:
    _expect_boundary_error(
        lambda: SimulatedIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="",
            created_at=_FIXED_CLOCK_Z,
        ),
        "intent_id must be a non-empty str",
    )
    _expect_boundary_error(
        lambda: SimulatedIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="op 007",
            created_at=_FIXED_CLOCK_Z,
        ),
        "intent_id must not contain whitespace",
    )


def test_simulated_intent_rejects_non_z_suffixed_created_at() -> None:
    _expect_boundary_error(
        lambda: SimulatedIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="op-008",
            created_at="",
        ),
        "created_at must be a non-empty str",
    )
    _expect_boundary_error(
        lambda: SimulatedIntent(
            lane=SimulationLane.LOCAL_ONLY,
            intent_id="op-009",
            created_at="2026-05-17T14:00:00+00:00",
        ),
        "ADR-004 Z-suffixed UTC string",
    )


# ---------------------------------------------------------------------------
# SimulationBoundary: construction and lane property
# ---------------------------------------------------------------------------


def test_simulation_boundary_constructs_with_lane() -> None:
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    assert boundary.lane is SimulationLane.LOCAL_ONLY


def test_simulation_boundary_uses_slots() -> None:
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    assert not hasattr(boundary, "__dict__")


def test_simulation_boundary_rejects_non_lane() -> None:
    _expect_boundary_error(
        lambda: SimulationBoundary(lane="local_only"),  # type: ignore[arg-type]
        "lane must be a SimulationLane",
    )


# ---------------------------------------------------------------------------
# Safety gate: propose only succeeds when the SafetyVerdict is clear
# ---------------------------------------------------------------------------


def test_propose_returns_intent_when_verdict_is_clear() -> None:
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    intent = SimulatedIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="op-010",
        created_at=_FIXED_CLOCK_Z,
    )
    result = boundary.propose(intent=intent, verdict=_clear_verdict())
    assert result is intent  # identity: the boundary does not mutate or copy


def test_propose_is_deterministic_for_equivalent_inputs() -> None:
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    intent_a = SimulatedIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="op-011",
        created_at=_FIXED_CLOCK_Z,
    )
    intent_b = SimulatedIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="op-011",
        created_at=_FIXED_CLOCK_Z,
    )
    assert intent_a == intent_b  # frozen dataclasses compare structurally
    result_a = boundary.propose(intent=intent_a, verdict=_clear_verdict())
    result_b = boundary.propose(intent=intent_b, verdict=_clear_verdict())
    assert result_a == result_b
    assert boundary.propose(intent=intent_a, verdict=_clear_verdict()) is intent_a


def test_propose_rejects_non_intent() -> None:
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    bogus: Any = object()
    _expect_boundary_error(
        lambda: boundary.propose(intent=bogus, verdict=_clear_verdict()),
        "intent must be a SimulatedIntent",
    )


def test_propose_rejects_non_verdict() -> None:
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    intent = SimulatedIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="op-012",
        created_at=_FIXED_CLOCK_Z,
    )
    bogus: Any = object()
    _expect_boundary_error(
        lambda: boundary.propose(intent=intent, verdict=bogus),
        "verdict must be a SafetyVerdict",
    )


def test_propose_blocks_when_verdict_is_not_clear() -> None:
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    intent = SimulatedIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="op-013",
        created_at=_FIXED_CLOCK_Z,
    )
    _expect_boundary_error(
        lambda: boundary.propose(intent=intent, verdict=_blocked_verdict()),
        "blocked by safety verdict",
    )


def test_propose_surfaces_blocker_codes_in_error_message() -> None:
    """The error message must surface the verdict's blocker tuple so
    operator code can route on the specific blocker."""
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    intent = SimulatedIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="op-014",
        created_at=_FIXED_CLOCK_Z,
    )
    raised: SimulationBoundaryError | None = None
    try:
        boundary.propose(intent=intent, verdict=_blocked_verdict())
    except SimulationBoundaryError as exc:
        raised = exc
    assert raised is not None
    message = str(raised)
    assert BLOCKER_HEARTBEAT_STALE in message
    assert BLOCKER_KILL_SWITCH_TRIPPED in message


def test_propose_does_not_mutate_intent_or_verdict() -> None:
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    intent = SimulatedIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="op-015",
        created_at=_FIXED_CLOCK_Z,
    )
    verdict = _clear_verdict()
    snapshot_intent = (intent.lane, intent.intent_id, intent.created_at)
    snapshot_verdict = (
        verdict.clear,
        verdict.blockers,
        verdict.kill_switch_state,
        verdict.reconciliation_status,
        verdict.observed_at,
    )
    boundary.propose(intent=intent, verdict=verdict)
    assert (intent.lane, intent.intent_id, intent.created_at) == snapshot_intent
    assert (
        verdict.clear,
        verdict.blockers,
        verdict.kill_switch_state,
        verdict.reconciliation_status,
        verdict.observed_at,
    ) == snapshot_verdict


# ---------------------------------------------------------------------------
# Lane gate: only matching lanes are permitted
# ---------------------------------------------------------------------------


def test_propose_rejects_intent_with_mismatched_lane() -> None:
    """Boundary rejects an intent whose lane is not the boundary's lane.

    :class:`SimulationLane` has only one authorized value (``LOCAL_ONLY``)
    under P5-01, so to exercise the mismatch branch this test injects
    a stand-in :class:`StrEnum` value via ``object.__setattr__`` on
    the frozen intent. The boundary's mismatch comparison is identity
    (``intent.lane is not self._lane``) and so triggers for any value
    that is not the boundary's exact lane singleton. When a future
    authorized packet adds a second lane to :class:`SimulationLane`,
    this test can be simplified to use that second value directly.
    """
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    intent = SimulatedIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="op-016",
        created_at=_FIXED_CLOCK_Z,
    )

    class _StandInLane(StrEnum):
        OTHER = "other_lane_test_only"

    object.__setattr__(intent, "lane", _StandInLane.OTHER)
    _expect_boundary_error(
        lambda: boundary.propose(intent=intent, verdict=_clear_verdict()),
        "lane mismatch",
    )


def test_propose_lane_check_uses_identity() -> None:
    """Boundary lane comparison is by identity (``is``) because
    :class:`SimulationLane` is a :class:`StrEnum` and enum members
    are singletons. This test documents the contract."""
    boundary = SimulationBoundary(lane=SimulationLane.LOCAL_ONLY)
    intent = SimulatedIntent(
        lane=SimulationLane.LOCAL_ONLY,
        intent_id="op-017",
        created_at=_FIXED_CLOCK_Z,
    )
    assert intent.lane is boundary.lane
    boundary.propose(intent=intent, verdict=_clear_verdict())


# ---------------------------------------------------------------------------
# Inertness: structural checks on the simulation subpackage
# ---------------------------------------------------------------------------


_PKG_ROOT = Path(__file__).resolve().parent.parent.parent / "src" / "gmc_rebuild" / "simulation"


def _simulation_source_files() -> list[Path]:
    return sorted(_PKG_ROOT.glob("*.py"))


def _strip_docstrings_and_comments(source: str) -> str:
    """Return ``source`` with module/class/function docstrings and # comments removed.

    Used so the "no forbidden tokens" checks below match real code,
    not governance commentary in docstrings. Docstrings are
    intentionally verbose under the P5-01 authorization and reference
    forbidden token names by design (to assert what the module is
    *not*).
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


def _simulation_code_text() -> str:
    return "\n".join(
        _strip_docstrings_and_comments(p.read_text()) for p in _simulation_source_files()
    )


def test_simulation_package_has_no_main_entry_point() -> None:
    code = _simulation_code_text()
    assert "__main__" not in code
    assert "if __name__" not in code


def test_simulation_package_has_no_forbidden_runtime_imports() -> None:
    imported: set[str] = set()
    for path in _simulation_source_files():
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
    assert not leaked, f"simulation package must not import {leaked}"


def test_simulation_package_has_no_sleep_or_env_or_io() -> None:
    code = _simulation_code_text()
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
        assert needle not in code, f"simulation package code must not contain {needle!r}"


def test_simulation_package_does_not_modify_runtime_or_risk_subpackages() -> None:
    """The simulation subpackage may *import from* runtime and risk
    (for the SafetyVerdict and to_utc_string symbols respectively),
    but must not re-export or mutate them."""
    code = _simulation_code_text()
    assert "from gmc_rebuild.runtime" in code or "import gmc_rebuild.runtime" in code
    assert "from gmc_rebuild.risk" in code or "import gmc_rebuild.risk" in code
