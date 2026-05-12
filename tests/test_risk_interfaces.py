"""P2-05 risk-control interface tests.

Verifies that the ``gmc_rebuild.risk`` subpackage authorized by PR P2-05
(see ``governance/authorizations/2026-05-12_p2-05.md`` and
``plan/phase2_entry_plan.md`` §4):

- exposes the documented Protocols, dataclasses, status enums, and
  helpers;
- produces immutable records with validated fields;
- enforces ADR-002, ADR-003, and ADR-005 safety properties at the type
  boundary (safe defaults, no naive datetimes, no broker / order /
  market-data coupling);
- accepts test-only fakes that conform structurally to the Protocols;
- introduces no forbidden runtime entry points, env-var reads, or
  filesystem / network I/O.

The fakes defined below live entirely under ``tests/`` per the P2-05
authorization. They exist solely to exercise the interfaces; none of
them touches the network, the filesystem, a broker, or a real account.

Tests avoid ``pytest.raises`` / fixture-typed parameters so the mypy
strict pre-commit hook does not need a pytest-stub dependency. See
``tests/test_logging_audit.py`` and ``tests/test_time_utc.py`` for the
same pattern.
"""

from __future__ import annotations

import ast
import importlib
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

from gmc_rebuild.risk import (
    HeartbeatProtocol,
    HeartbeatRecord,
    HeartbeatStatus,
    KillSwitchDecision,
    KillSwitchProtocol,
    KillSwitchState,
    ReconciliationProtocol,
    ReconciliationReport,
    ReconciliationStatus,
    RiskControlError,
    to_utc_string,
)
from gmc_rebuild.time import NaiveDatetimeError


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


# ---------------------------------------------------------------------------
# Test-only fakes (test-scope only; not exported from the runtime package).
# ---------------------------------------------------------------------------


class FakeKillSwitch:
    """In-memory fake for :class:`KillSwitchProtocol`.

    Used solely to exercise the protocol shape in tests. Does not place
    orders, does not talk to a broker, does not touch a network or
    filesystem. ADR-002's "safe default is no trading" is preserved by
    having tripped state be sticky once set.
    """

    def __init__(self) -> None:
        self._tripped: KillSwitchDecision | None = None
        self._clock: datetime = datetime(2026, 5, 12, 14, 0, 0, tzinfo=UTC)

    def advance(self, seconds: int) -> None:
        self._clock = self._clock + timedelta(seconds=seconds)

    def current(self) -> KillSwitchDecision:
        if self._tripped is not None:
            return self._tripped
        return KillSwitchDecision(
            state=KillSwitchState.ARMED,
            observed_at=to_utc_string(self._clock),
            reason="",
            triggered_by="",
        )

    def trip(self, *, reason: str, triggered_by: str) -> KillSwitchDecision:
        decision = KillSwitchDecision(
            state=KillSwitchState.TRIPPED,
            observed_at=to_utc_string(self._clock),
            reason=reason,
            triggered_by=triggered_by,
        )
        self._tripped = decision
        return decision


class FakeReconciliation:
    """In-memory fake for :class:`ReconciliationProtocol`.

    Returns a fixed :class:`ReconciliationReport` constructed at init
    time. Pure data; no I/O.
    """

    def __init__(self, report: ReconciliationReport) -> None:
        self._report = report

    def reconcile(self) -> ReconciliationReport:
        return self._report


class FakeHeartbeat:
    """In-memory fake for :class:`HeartbeatProtocol`.

    Stores last-update timestamps per component and computes staleness
    against a fixed ``observed_at`` clock and 8-hour threshold (ADR-005).
    Unknown components report STALE, preserving ADR-005's safe-default
    property.
    """

    def __init__(self, observed_at: datetime, threshold_seconds: float = 8 * 3600) -> None:
        self._observed_at = observed_at
        self._threshold = threshold_seconds
        self._last_updates: dict[str, datetime] = {}

    def beat(self, component: str, when: datetime) -> None:
        self._last_updates[component] = when

    def status(self, component: str) -> HeartbeatRecord:
        last = self._last_updates.get(component)
        if last is None:
            return HeartbeatRecord(
                component=component,
                status=HeartbeatStatus.STALE,
                last_update=to_utc_string(self._observed_at - timedelta(days=365)),
                observed_at=to_utc_string(self._observed_at),
                age_seconds=float(self._threshold) + 1.0,
            )
        age = (self._observed_at - last).total_seconds()
        is_stale = age > self._threshold
        return HeartbeatRecord(
            component=component,
            status=HeartbeatStatus.STALE if is_stale else HeartbeatStatus.FRESH,
            last_update=to_utc_string(last),
            observed_at=to_utc_string(self._observed_at),
            age_seconds=max(0.0, age),
        )


# ---------------------------------------------------------------------------
# Package surface
# ---------------------------------------------------------------------------


def test_risk_subpackage_imports() -> None:
    module = importlib.import_module("gmc_rebuild.risk")
    assert module is not None
    for name in (
        "HeartbeatProtocol",
        "HeartbeatRecord",
        "HeartbeatStatus",
        "KillSwitchDecision",
        "KillSwitchProtocol",
        "KillSwitchState",
        "ReconciliationProtocol",
        "ReconciliationReport",
        "ReconciliationStatus",
        "RiskControlError",
        "to_utc_string",
    ):
        assert hasattr(module, name), f"gmc_rebuild.risk must export {name}"


def test_risk_control_error_is_value_error() -> None:
    assert issubclass(RiskControlError, ValueError)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


def test_kill_switch_state_values() -> None:
    assert {s.value for s in KillSwitchState} == {"armed", "tripped"}
    assert KillSwitchState.ARMED.value == "armed"
    assert KillSwitchState.TRIPPED.value == "tripped"


def test_reconciliation_status_values() -> None:
    assert {s.value for s in ReconciliationStatus} == {
        "clean",
        "warning",
        "failed",
        "unavailable",
    }


def test_heartbeat_status_values() -> None:
    assert {s.value for s in HeartbeatStatus} == {"fresh", "stale"}


# ---------------------------------------------------------------------------
# to_utc_string helper
# ---------------------------------------------------------------------------


def test_to_utc_string_formats_aware_utc() -> None:
    ts = datetime(2026, 5, 12, 14, 23, 45, tzinfo=UTC)
    assert to_utc_string(ts) == "2026-05-12T14:23:45Z"


def test_to_utc_string_normalizes_non_utc_aware() -> None:
    eastern = timezone(timedelta(hours=-5))
    ts = datetime(2026, 5, 12, 9, 23, 45, tzinfo=eastern)
    assert to_utc_string(ts) == "2026-05-12T14:23:45Z"


def test_to_utc_string_rejects_naive_datetime() -> None:
    naive = datetime(2026, 5, 12, 14, 23, 45)
    raised: Exception | None = None
    try:
        to_utc_string(naive)
    except NaiveDatetimeError as exc:
        raised = exc
    assert isinstance(raised, NaiveDatetimeError)


def test_to_utc_string_rejects_non_datetime() -> None:
    _expect_risk_error(
        lambda: to_utc_string("2026-05-12T14:23:45Z"),  # type: ignore[arg-type]
        "to_utc_string expects a datetime",
    )


# ---------------------------------------------------------------------------
# KillSwitchDecision
# ---------------------------------------------------------------------------


def test_kill_switch_decision_armed_shape() -> None:
    decision = KillSwitchDecision(
        state=KillSwitchState.ARMED,
        observed_at="2026-05-12T14:00:00Z",
        reason="",
        triggered_by="",
    )
    assert decision.state is KillSwitchState.ARMED
    assert decision.observed_at.endswith("Z")
    assert decision.reason == ""
    assert decision.triggered_by == ""


def test_kill_switch_decision_tripped_requires_reason_and_actor() -> None:
    decision = KillSwitchDecision(
        state=KillSwitchState.TRIPPED,
        observed_at="2026-05-12T14:00:00Z",
        reason="reconciliation failed",
        triggered_by="reconciliation",
    )
    assert decision.state is KillSwitchState.TRIPPED
    assert decision.reason == "reconciliation failed"
    assert decision.triggered_by == "reconciliation"


def test_kill_switch_decision_armed_rejects_reason() -> None:
    _expect_risk_error(
        lambda: KillSwitchDecision(
            state=KillSwitchState.ARMED,
            observed_at="2026-05-12T14:00:00Z",
            reason="should be empty",
            triggered_by="",
        ),
        "must be empty when armed",
    )


def test_kill_switch_decision_tripped_rejects_empty_reason() -> None:
    _expect_risk_error(
        lambda: KillSwitchDecision(
            state=KillSwitchState.TRIPPED,
            observed_at="2026-05-12T14:00:00Z",
            reason="",
            triggered_by="kevin",
        ),
        "reason must be non-empty when state is tripped",
    )


def test_kill_switch_decision_tripped_rejects_empty_actor() -> None:
    _expect_risk_error(
        lambda: KillSwitchDecision(
            state=KillSwitchState.TRIPPED,
            observed_at="2026-05-12T14:00:00Z",
            reason="x",
            triggered_by="",
        ),
        "triggered_by must be non-empty when state is tripped",
    )


def test_kill_switch_decision_rejects_non_enum_state() -> None:
    _expect_risk_error(
        lambda: KillSwitchDecision(
            state="armed",  # type: ignore[arg-type]
            observed_at="2026-05-12T14:00:00Z",
            reason="",
            triggered_by="",
        ),
        "must be a KillSwitchState",
    )


def test_kill_switch_decision_rejects_empty_timestamp() -> None:
    _expect_risk_error(
        lambda: KillSwitchDecision(
            state=KillSwitchState.ARMED,
            observed_at="",
            reason="",
            triggered_by="",
        ),
        "observed_at must be a non-empty str",
    )


def test_kill_switch_decision_is_immutable() -> None:
    decision = KillSwitchDecision(
        state=KillSwitchState.ARMED,
        observed_at="2026-05-12T14:00:00Z",
        reason="",
        triggered_by="",
    )
    raised: Exception | None = None
    try:
        decision.reason = "changed"  # type: ignore[misc]
    except (AttributeError, TypeError) as exc:
        raised = exc
    assert raised is not None, "KillSwitchDecision must be frozen"


# ---------------------------------------------------------------------------
# ReconciliationReport
# ---------------------------------------------------------------------------


def test_reconciliation_report_clean_shape() -> None:
    report = ReconciliationReport(
        status=ReconciliationStatus.CLEAN,
        checked_at="2026-05-12T14:00:00Z",
        tolerance=10.0,
        observed_delta=0.0,
        details={"source": "fake"},
    )
    assert report.status is ReconciliationStatus.CLEAN
    assert report.tolerance == 10.0
    assert report.observed_delta == 0.0
    assert report.details["source"] == "fake"


def test_reconciliation_report_details_is_read_only() -> None:
    report = ReconciliationReport(
        status=ReconciliationStatus.CLEAN,
        checked_at="2026-05-12T14:00:00Z",
        tolerance=10.0,
        observed_delta=0.0,
        details={"k": 1},
    )
    raised: Exception | None = None
    try:
        report.details["k"] = 2  # type: ignore[index]
    except TypeError as exc:
        raised = exc
    assert raised is not None, "ReconciliationReport.details must be read-only"


def test_reconciliation_report_rejects_non_enum_status() -> None:
    _expect_risk_error(
        lambda: ReconciliationReport(
            status="clean",  # type: ignore[arg-type]
            checked_at="2026-05-12T14:00:00Z",
            tolerance=10.0,
            observed_delta=0.0,
            details={},
        ),
        "must be a ReconciliationStatus",
    )


def test_reconciliation_report_rejects_negative_tolerance() -> None:
    _expect_risk_error(
        lambda: ReconciliationReport(
            status=ReconciliationStatus.CLEAN,
            checked_at="2026-05-12T14:00:00Z",
            tolerance=-1.0,
            observed_delta=0.0,
            details={},
        ),
        "tolerance must be non-negative",
    )


def test_reconciliation_report_rejects_negative_delta() -> None:
    _expect_risk_error(
        lambda: ReconciliationReport(
            status=ReconciliationStatus.WARNING,
            checked_at="2026-05-12T14:00:00Z",
            tolerance=10.0,
            observed_delta=-1.0,
            details={},
        ),
        "observed_delta must be non-negative",
    )


def test_reconciliation_report_rejects_bool_tolerance() -> None:
    _expect_risk_error(
        lambda: ReconciliationReport(
            status=ReconciliationStatus.CLEAN,
            checked_at="2026-05-12T14:00:00Z",
            tolerance=True,
            observed_delta=0.0,
            details={},
        ),
        "tolerance must be a number",
    )


def test_reconciliation_report_rejects_non_mapping_details() -> None:
    _expect_risk_error(
        lambda: ReconciliationReport(
            status=ReconciliationStatus.CLEAN,
            checked_at="2026-05-12T14:00:00Z",
            tolerance=10.0,
            observed_delta=0.0,
            details=[("k", 1)],  # type: ignore[arg-type]
        ),
        "details must be a Mapping",
    )


def test_reconciliation_report_distinguishes_unavailable_from_failed() -> None:
    """ADR-003: unavailable upstream is not the same as a confirmed mismatch."""
    unavailable = ReconciliationReport(
        status=ReconciliationStatus.UNAVAILABLE,
        checked_at="2026-05-12T14:00:00Z",
        tolerance=10.0,
        observed_delta=0.0,
        details={"reason": "upstream timeout"},
    )
    failed = ReconciliationReport(
        status=ReconciliationStatus.FAILED,
        checked_at="2026-05-12T14:00:00Z",
        tolerance=10.0,
        observed_delta=250.0,
        details={"symbol": "CASH"},
    )
    assert unavailable.status is not failed.status
    assert unavailable.observed_delta == 0.0
    assert failed.observed_delta > failed.tolerance


# ---------------------------------------------------------------------------
# HeartbeatRecord
# ---------------------------------------------------------------------------


def test_heartbeat_record_fresh_shape() -> None:
    record = HeartbeatRecord(
        component="operator",
        status=HeartbeatStatus.FRESH,
        last_update="2026-05-12T13:00:00Z",
        observed_at="2026-05-12T14:00:00Z",
        age_seconds=3600.0,
    )
    assert record.component == "operator"
    assert record.status is HeartbeatStatus.FRESH
    assert record.age_seconds == 3600.0


def test_heartbeat_record_rejects_empty_component() -> None:
    _expect_risk_error(
        lambda: HeartbeatRecord(
            component="",
            status=HeartbeatStatus.STALE,
            last_update="2026-05-12T13:00:00Z",
            observed_at="2026-05-12T14:00:00Z",
            age_seconds=0.0,
        ),
        "component must be a non-empty str",
    )


def test_heartbeat_record_rejects_whitespace_component() -> None:
    _expect_risk_error(
        lambda: HeartbeatRecord(
            component="op erator",
            status=HeartbeatStatus.STALE,
            last_update="2026-05-12T13:00:00Z",
            observed_at="2026-05-12T14:00:00Z",
            age_seconds=0.0,
        ),
        "must not contain whitespace",
    )


def test_heartbeat_record_rejects_negative_age() -> None:
    _expect_risk_error(
        lambda: HeartbeatRecord(
            component="operator",
            status=HeartbeatStatus.FRESH,
            last_update="2026-05-12T13:00:00Z",
            observed_at="2026-05-12T14:00:00Z",
            age_seconds=-1.0,
        ),
        "age_seconds must be non-negative",
    )


def test_heartbeat_record_is_immutable() -> None:
    record = HeartbeatRecord(
        component="operator",
        status=HeartbeatStatus.FRESH,
        last_update="2026-05-12T13:00:00Z",
        observed_at="2026-05-12T14:00:00Z",
        age_seconds=3600.0,
    )
    raised: Exception | None = None
    try:
        record.component = "x"  # type: ignore[misc]
    except (AttributeError, TypeError) as exc:
        raised = exc
    assert raised is not None, "HeartbeatRecord must be frozen"


# ---------------------------------------------------------------------------
# Protocol conformance via test-only fakes
# ---------------------------------------------------------------------------


def test_fake_kill_switch_conforms_to_protocol() -> None:
    fake = FakeKillSwitch()
    assert isinstance(fake, KillSwitchProtocol)


def test_fake_reconciliation_conforms_to_protocol() -> None:
    report = ReconciliationReport(
        status=ReconciliationStatus.CLEAN,
        checked_at="2026-05-12T14:00:00Z",
        tolerance=10.0,
        observed_delta=0.0,
        details={},
    )
    fake = FakeReconciliation(report)
    assert isinstance(fake, ReconciliationProtocol)


def test_fake_heartbeat_conforms_to_protocol() -> None:
    fake = FakeHeartbeat(observed_at=datetime(2026, 5, 12, 14, 0, 0, tzinfo=UTC))
    assert isinstance(fake, HeartbeatProtocol)


def test_fake_kill_switch_starts_armed() -> None:
    fake = FakeKillSwitch()
    decision = fake.current()
    assert decision.state is KillSwitchState.ARMED
    assert decision.reason == ""
    assert decision.triggered_by == ""


def test_fake_kill_switch_trip_is_sticky() -> None:
    """ADR-002: once tripped, the switch must stay tripped until reset."""
    fake = FakeKillSwitch()
    fake.trip(reason="reconciliation failed", triggered_by="reconciliation")
    fake.advance(60)
    later = fake.current()
    assert later.state is KillSwitchState.TRIPPED
    assert later.reason == "reconciliation failed"
    assert later.triggered_by == "reconciliation"


def test_fake_reconciliation_returns_report() -> None:
    report = ReconciliationReport(
        status=ReconciliationStatus.FAILED,
        checked_at="2026-05-12T14:00:00Z",
        tolerance=10.0,
        observed_delta=125.0,
        details={"symbol": "CASH"},
    )
    fake = FakeReconciliation(report)
    assert fake.reconcile() is report


def test_fake_heartbeat_unknown_component_is_stale() -> None:
    """ADR-005 safe default: a component the heartbeat has never seen is STALE."""
    fake = FakeHeartbeat(observed_at=datetime(2026, 5, 12, 14, 0, 0, tzinfo=UTC))
    record = fake.status("operator")
    assert record.component == "operator"
    assert record.status is HeartbeatStatus.STALE
    assert record.age_seconds > 8 * 3600


def test_fake_heartbeat_fresh_when_within_threshold() -> None:
    observed = datetime(2026, 5, 12, 14, 0, 0, tzinfo=UTC)
    fake = FakeHeartbeat(observed_at=observed)
    fake.beat("operator", observed - timedelta(hours=1))
    record = fake.status("operator")
    assert record.status is HeartbeatStatus.FRESH
    assert record.age_seconds == 3600.0
    assert record.last_update == "2026-05-12T13:00:00Z"
    assert record.observed_at == "2026-05-12T14:00:00Z"


def test_fake_heartbeat_stale_when_beyond_threshold() -> None:
    observed = datetime(2026, 5, 12, 14, 0, 0, tzinfo=UTC)
    fake = FakeHeartbeat(observed_at=observed)
    fake.beat("operator", observed - timedelta(hours=9))
    record = fake.status("operator")
    assert record.status is HeartbeatStatus.STALE
    assert record.age_seconds == 9 * 3600.0


# ---------------------------------------------------------------------------
# Boundary scans — risk submodule must not introduce forbidden runtime hooks
# ---------------------------------------------------------------------------


def test_risk_submodule_layout_has_no_forbidden_files() -> None:
    pkg_root = Path(__file__).resolve().parents[1] / "src" / "gmc_rebuild" / "risk"
    assert pkg_root.is_dir()
    allowed = {"__init__.py", "interfaces.py"}
    present = {p.name for p in pkg_root.iterdir() if p.is_file()}
    assert present <= allowed, f"unexpected files in risk submodule: {present - allowed}"
    dirs = {p.name for p in pkg_root.iterdir() if p.is_dir() and p.name != "__pycache__"}
    assert not dirs, f"unexpected subdirectories under src/gmc_rebuild/risk/: {dirs}"


def test_risk_submodule_has_no_runtime_entry_points() -> None:
    pkg_root = Path(__file__).resolve().parents[1] / "src" / "gmc_rebuild" / "risk"
    forbidden_imports = {"os", "socket", "subprocess", "threading", "asyncio", "sqlite3"}
    forbidden_attr_chains = {("os", "environ"), ("os", "getenv")}
    for python_file in pkg_root.rglob("*.py"):
        tree = ast.parse(python_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                test = node.test
                if (
                    isinstance(test, ast.Compare)
                    and isinstance(test.left, ast.Name)
                    and test.left.id == "__name__"
                ):
                    raise AssertionError(
                        f"{python_file} must not define an `if __name__` entry point"
                    )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in forbidden_imports, (
                        f"{python_file} must not import {alias.name}"
                    )
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                root = node.module.split(".", 1)[0]
                assert root not in forbidden_imports, (
                    f"{python_file} must not import from {node.module}"
                )
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                assert (node.value.id, node.attr) not in forbidden_attr_chains, (
                    f"{python_file} must not access {node.value.id}.{node.attr}"
                )
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id != "open", (
                    f"{python_file} must not call open() for filesystem I/O"
                )


def test_risk_module_does_not_call_naive_utcnow() -> None:
    pkg_root = Path(__file__).resolve().parents[1] / "src" / "gmc_rebuild" / "risk"
    for path in pkg_root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "utcnow(" not in text, f"{path} calls utcnow(); ADR-004 forbids naive UTC helpers"
