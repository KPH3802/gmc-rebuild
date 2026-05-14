"""P4-02 composed-fixture test.

Pure-Python, in-memory, pytest-only composed-fixture test exercising
:class:`gmc_rebuild.heartbeat.InMemoryHeartbeat`,
:class:`gmc_rebuild.kill_switch.InMemoryKillSwitch`, and
:class:`gmc_rebuild.reconciliation.InMemoryReconciliation` together
against their abstract :class:`typing.Protocol` boundaries declared in
:mod:`gmc_rebuild.risk` (``HeartbeatProtocol``, ``KillSwitchProtocol``,
``ReconciliationProtocol``).

Authorization: ``governance/authorizations/2026-05-14_p4-02.md``.

Design constraints — these are governance constraints, not stylistic
preferences:

- **No new ``src/**`` directory or file.** This test lives only under
  ``tests/p4_02_composed/``.
- **No modification of ``src/gmc_rebuild/risk/``.** The P2-05
  protocol boundary is preserved unchanged.
- **No re-export of any merged Phase 3 fixture from any runtime
  path.** Imports come from the merged Phase 3 fixture packages
  (`gmc_rebuild.heartbeat`, `gmc_rebuild.kill_switch`,
  `gmc_rebuild.reconciliation`) and from `gmc_rebuild.risk` only.
- **No runtime activation.** No ``__main__``, no daemon, no
  scheduler, no background thread, no long-running service.
- **No external I/O.** No filesystem write, no network, no broker
  SDK, no market-data feed, no ``time.sleep``, no ``asyncio.sleep``,
  no ``os.environ`` / ``os.getenv``, no real account / venue /
  endpoint / secret.
- **Composed, not new fake.** This module exercises the three
  already-merged in-memory fakes against their abstract Protocol
  boundaries. It does not introduce a new concrete protocol
  implementation, a new fake, or a new helper under ``src/**``.
- **Deterministic.** Uses only the in-memory ``advance(seconds)``
  helpers on the three fakes; no wall-clock read.

Tests avoid ``pytest.raises`` / fixture-typed parameters so the mypy
strict pre-commit hook does not need a pytest-stub dependency. See
``tests/heartbeat/test_heartbeat_fixture.py``,
``tests/kill_switch/test_kill_switch_fixture.py``, and
``tests/reconciliation/test_reconciliation_fixture.py`` for the same
pattern.
"""

from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from pathlib import Path

from gmc_rebuild.heartbeat import InMemoryHeartbeat
from gmc_rebuild.kill_switch import InMemoryKillSwitch
from gmc_rebuild.reconciliation import InMemoryReconciliation
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
)

_FIXED_CLOCK = datetime(2026, 5, 14, 14, 0, 0, tzinfo=UTC)


def _make_trio() -> tuple[InMemoryHeartbeat, InMemoryKillSwitch, InMemoryReconciliation]:
    """Construct the three in-memory fakes against a shared fixed clock.

    The fakes do not share state; they share only a starting moment so
    composed scenarios can advance their independent clocks in lock-step
    via the explicit ``advance(seconds)`` helpers each fake exposes.
    """
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    return heartbeat, kill_switch, reconciliation


# ---------------------------------------------------------------------------
# Composed Protocol conformance
# ---------------------------------------------------------------------------


def test_composed_fakes_all_conform_to_their_protocols() -> None:
    """Each of the three fakes conforms structurally to its Protocol.

    The composed-fixture test exists to exercise the three fakes
    *together* against the three abstract ``Protocol`` boundaries
    declared in ``src/gmc_rebuild/risk/`` (P2-05). This test asserts
    the structural-conformance precondition.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    assert isinstance(heartbeat, HeartbeatProtocol)
    assert isinstance(kill_switch, KillSwitchProtocol)
    assert isinstance(reconciliation, ReconciliationProtocol)


def test_composed_fakes_return_protocol_record_types() -> None:
    """Each fake's protocol method returns its declared record type."""
    heartbeat, kill_switch, reconciliation = _make_trio()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    hb_record = heartbeat.status("operator")
    ks_decision = kill_switch.current()
    rc_report = reconciliation.reconcile()
    assert isinstance(hb_record, HeartbeatRecord)
    assert isinstance(ks_decision, KillSwitchDecision)
    assert isinstance(rc_report, ReconciliationReport)


# ---------------------------------------------------------------------------
# Composed safe-default start state
# ---------------------------------------------------------------------------


def test_composed_start_state_is_safe_defaults_for_all_three_protocols() -> None:
    """Freshly composed trio reports the three ADR-mandated safe defaults.

    - ADR-005: an unknown heartbeat component is ``STALE`` (paused).
    - ADR-002: a freshly constructed kill switch is ``ARMED``.
    - ADR-003: a freshly constructed reconciliation is ``UNAVAILABLE``
      (not ``FAILED``); the ``UNAVAILABLE`` / ``FAILED`` distinction is
      preserved.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    hb_record = heartbeat.status("operator")
    ks_decision = kill_switch.current()
    rc_report = reconciliation.reconcile()
    assert hb_record.status is HeartbeatStatus.STALE
    assert ks_decision.state is KillSwitchState.ARMED
    assert rc_report.status is ReconciliationStatus.UNAVAILABLE
    # ADR-003 explicit distinction: UNAVAILABLE != FAILED.
    assert ReconciliationStatus.UNAVAILABLE.value == "unavailable"
    assert ReconciliationStatus.FAILED.value == "failed"


def test_composed_start_state_timestamps_are_z_suffixed_utc() -> None:
    """ADR-004 UTC discipline holds at every composed-fixture boundary."""
    heartbeat, kill_switch, reconciliation = _make_trio()
    hb_record = heartbeat.status("operator")
    ks_decision = kill_switch.current()
    rc_report = reconciliation.reconcile()
    assert hb_record.observed_at.endswith("Z")
    assert hb_record.last_update.endswith("Z")
    assert ks_decision.observed_at.endswith("Z")
    assert rc_report.checked_at.endswith("Z")
    assert hb_record.observed_at == "2026-05-14T14:00:00Z"
    assert ks_decision.observed_at == "2026-05-14T14:00:00Z"
    assert rc_report.checked_at == "2026-05-14T14:00:00Z"


# ---------------------------------------------------------------------------
# Composed "healthy" steady state
# ---------------------------------------------------------------------------


def test_composed_healthy_state_reports_fresh_armed_clean() -> None:
    """A composed healthy steady state: FRESH heartbeat + ARMED kill + CLEAN recon.

    Exercises all three fakes together: a recent operator heartbeat is
    ``FRESH``; the kill switch has never been tripped and is ``ARMED``;
    a staged ``CLEAN`` reconciliation outcome flows through.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=5))
    reconciliation.set_next(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"composed-fixture-scenario": "healthy"},
    )
    hb_record = heartbeat.status("operator")
    ks_decision = kill_switch.current()
    rc_report = reconciliation.reconcile()
    assert hb_record.status is HeartbeatStatus.FRESH
    assert ks_decision.state is KillSwitchState.ARMED
    assert rc_report.status is ReconciliationStatus.CLEAN
    assert rc_report.observed_delta == 0.0
    assert rc_report.tolerance == 10.0
    assert rc_report.details["composed-fixture-scenario"] == "healthy"


# ---------------------------------------------------------------------------
# Composed "ADR-003 mismatch → ADR-002 trip" scenario
# ---------------------------------------------------------------------------


def test_composed_failed_recon_then_explicit_kill_switch_trip() -> None:
    """Composed scenario: confirmed material mismatch → operator-initiated trip.

    ADR-003 names ``FAILED`` as a confirmed material mismatch; ADR-002
    names ``trip(reason, triggered_by)`` as the operator-side mechanism
    that records an active trip. This composed scenario asserts that
    when reconciliation reports ``FAILED``, an operator can trip the
    kill switch and the kill switch records the trip — exercised against
    the abstract Protocol boundaries (``ReconciliationProtocol`` and
    ``KillSwitchProtocol``). The fakes do not auto-trip; the connection
    between a ``FAILED`` report and a kill-switch trip is a future
    runtime concern that is **not** wired here.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=42.5,
        details={"composed-fixture-scenario": "material-mismatch"},
    )
    rc_report = reconciliation.reconcile()
    # Pre-trip: the kill switch is still ARMED.
    pre_trip = kill_switch.current()
    assert pre_trip.state is KillSwitchState.ARMED
    assert rc_report.status is ReconciliationStatus.FAILED
    assert rc_report.observed_delta == 42.5
    # Operator trips the kill switch in response.
    tripped = kill_switch.trip(
        reason="reconciliation FAILED in composed fixture scenario",
        triggered_by="operator",
    )
    assert tripped.state is KillSwitchState.TRIPPED
    # Subsequent calls continue to report TRIPPED.
    assert kill_switch.current().state is KillSwitchState.TRIPPED
    # Heartbeat is unaffected by the kill-switch trip.
    assert heartbeat.status("operator").status is HeartbeatStatus.FRESH


# ---------------------------------------------------------------------------
# Composed "ADR-005 heartbeat staleness" scenario
# ---------------------------------------------------------------------------


def test_composed_advance_makes_heartbeat_stale_independent_of_other_controls() -> None:
    """Composed scenario: advancing the heartbeat clock past ADR-005's threshold.

    Asserts that the three fakes maintain independent clocks (the
    composed-fixture test does not introduce a shared clock):
    advancing only the heartbeat's in-memory clock past the ADR-005
    8-hour threshold turns a previously ``FRESH`` heartbeat ``STALE``
    while leaving the kill-switch decision and reconciliation result
    untouched. This preserves ADR-005's "safe default is paused"
    property without coupling it to the other two controls.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    assert heartbeat.status("operator").status is HeartbeatStatus.FRESH
    # Advance only the heartbeat's clock past the ADR-005 threshold.
    heartbeat.advance(9 * 3600.0)
    assert heartbeat.status("operator").status is HeartbeatStatus.STALE
    # The other two controls are unaffected: their clocks did not advance.
    assert kill_switch.current().state is KillSwitchState.ARMED
    assert kill_switch.current().observed_at == "2026-05-14T14:00:00Z"
    assert reconciliation.reconcile().checked_at == "2026-05-14T14:00:00Z"


# ---------------------------------------------------------------------------
# Composed FIFO + UNAVAILABLE drain
# ---------------------------------------------------------------------------


def test_composed_reconciliation_fifo_drains_to_unavailable_under_armed_kill_switch() -> None:
    """Composed scenario: a FIFO of staged outcomes drains to UNAVAILABLE.

    The reconciliation fake exposes a FIFO queue of staged outcomes;
    once drained, ``reconcile()`` returns ``UNAVAILABLE`` (not
    ``FAILED``). The kill switch remains ``ARMED`` and the heartbeat
    remains ``FRESH`` throughout, since the queue drain is a
    reconciliation-side concern only.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    reconciliation.enqueue(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"composed-fixture-scenario": "drain-1-clean"},
    )
    reconciliation.enqueue(
        status=ReconciliationStatus.WARNING,
        tolerance=10.0,
        observed_delta=3.0,
        details={"composed-fixture-scenario": "drain-2-warning"},
    )
    first = reconciliation.reconcile()
    second = reconciliation.reconcile()
    third = reconciliation.reconcile()
    assert first.status is ReconciliationStatus.CLEAN
    assert second.status is ReconciliationStatus.WARNING
    # Queue drained — subsequent calls return UNAVAILABLE (not FAILED).
    assert third.status is ReconciliationStatus.UNAVAILABLE
    assert ReconciliationStatus.UNAVAILABLE.value == "unavailable"
    assert ReconciliationStatus.FAILED.value == "failed"
    # Kill switch and heartbeat are unaffected by the drain.
    assert kill_switch.current().state is KillSwitchState.ARMED
    assert heartbeat.status("operator").status is HeartbeatStatus.FRESH


# ---------------------------------------------------------------------------
# Composed multi-component heartbeat
# ---------------------------------------------------------------------------


def test_composed_multi_component_heartbeats_track_independently() -> None:
    """Composed scenario: multiple heartbeat components track independently.

    ADR-005 distinguishes per-component staleness; a stale
    ``local-machine`` heartbeat does not pull a fresh ``operator``
    heartbeat ``STALE``. The kill switch and reconciliation are unaware
    of which component is fresh; their states remain at safe defaults.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    heartbeat.beat("local-machine", _FIXED_CLOCK - timedelta(hours=10))
    assert heartbeat.status("operator").status is HeartbeatStatus.FRESH
    assert heartbeat.status("local-machine").status is HeartbeatStatus.STALE
    # Unknown components still report STALE per ADR-005's safe default.
    assert heartbeat.status("never-seen").status is HeartbeatStatus.STALE
    # Other controls remain at safe defaults.
    assert kill_switch.current().state is KillSwitchState.ARMED
    assert reconciliation.reconcile().status is ReconciliationStatus.UNAVAILABLE


# ---------------------------------------------------------------------------
# No forbidden tokens / imports in the composed-fixture test module itself
# ---------------------------------------------------------------------------


_THIS_PKG_ROOT = Path(__file__).resolve().parent


def _composed_source_files() -> list[Path]:
    return sorted(_THIS_PKG_ROOT.glob("*.py"))


def _strip_docstrings_and_comments(source: str) -> str:
    """Return ``source`` with module/class/function docstrings and ``#`` comments removed.

    Mirrors the same helper in the merged P3-03 / P3-04 / P3-05 fixture
    tests so the "no forbidden tokens" checks below match real code,
    not governance commentary in docstrings. Docstrings are
    intentionally verbose and reference forbidden token names by design
    (to assert what the module is *not*).
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


def _composed_code_text() -> str:
    return "\n".join(
        _strip_docstrings_and_comments(p.read_text()) for p in _composed_source_files()
    )


def test_composed_test_module_has_no_forbidden_runtime_imports() -> None:
    imported: set[str] = set()
    for path in _composed_source_files():
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
    assert not leaked, f"P4-02 composed-fixture test must not import {leaked}"


def test_composed_test_module_only_imports_from_authorized_sources() -> None:
    """The composed test imports from the three merged Phase 3 fixture packages
    and from :mod:`gmc_rebuild.risk` (P2-05 protocol boundary) only, plus the
    standard-library helpers ``ast``, ``datetime``, ``pathlib``.

    This asserts that the composed-fixture test does **not** reach into
    any concrete protocol implementation that does not exist, does
    **not** re-export any merged Phase 3 fixture from any runtime path,
    and does **not** introduce a new ``src/**`` import target.
    """
    imported_from: set[str] = set()
    for path in _composed_source_files():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_from.add(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported_from.add(alias.name)
    allowed_prefixes = (
        "gmc_rebuild.heartbeat",
        "gmc_rebuild.kill_switch",
        "gmc_rebuild.reconciliation",
        "gmc_rebuild.risk",
        "ast",
        "datetime",
        "pathlib",
        "__future__",
    )
    for mod in imported_from:
        assert mod.startswith(allowed_prefixes), (
            f"P4-02 composed-fixture test imported unauthorized module {mod!r}"
        )


def test_composed_test_module_does_not_modify_risk_subpackage() -> None:
    """Smoke check: the composed test imports from :mod:`gmc_rebuild.risk`
    but the package's source files are not touched by this test module.

    The structural prohibition ("may not modify ``src/gmc_rebuild/risk/``")
    is enforced by review and by the implementation PR's diff scope.
    This test merely confirms the composed module imports against the
    declared abstract Protocol boundaries.
    """
    code = _composed_code_text()
    assert "from gmc_rebuild.risk" in code
