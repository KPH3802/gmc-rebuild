"""P4-03 composed-invariants test.

Pure-Python, in-memory, pytest-only composed-invariants test extending
the merged P4-02 composed-fixture coverage at
``tests/p4_02_composed/test_composed_fixture.py``. Asserts properties
that hold *across* multiple composed scenarios (rather than scenario-
by-scenario as the P4-02 module does), exercising the same three
already-merged in-memory fakes — :class:`gmc_rebuild.heartbeat.InMemoryHeartbeat`,
:class:`gmc_rebuild.kill_switch.InMemoryKillSwitch`,
:class:`gmc_rebuild.reconciliation.InMemoryReconciliation` — against
their abstract :class:`typing.Protocol` boundaries declared in
:mod:`gmc_rebuild.risk` (``HeartbeatProtocol``, ``KillSwitchProtocol``,
``ReconciliationProtocol``).

Authorization: ``governance/authorizations/2026-05-15_p4-03.md``.

Design constraints — these are governance constraints, not stylistic
preferences:

- **No new ``src/**`` directory or file.** This test lives only as
  one new file in the existing ``tests/p4_02_composed/`` directory.
- **No modification of existing test files.** The merged
  ``tests/p4_02_composed/__init__.py`` and
  ``tests/p4_02_composed/test_composed_fixture.py`` are preserved
  exactly.
- **No new test directories.** The single new test file lives in the
  existing ``tests/p4_02_composed/`` package.
- **No ``conftest.py``.** No shared fixture export is added.
- **No new fakes / helpers.** This module exercises the three
  already-merged in-memory fakes against their abstract Protocol
  boundaries. It does not introduce a new concrete protocol
  implementation, a new fake, or a new helper under ``src/**``.
- **No re-export of any merged Phase 3 fixture from any runtime
  path.** Imports come from the merged Phase 3 fixture packages
  (``gmc_rebuild.heartbeat``, ``gmc_rebuild.kill_switch``,
  ``gmc_rebuild.reconciliation``) and from ``gmc_rebuild.risk`` only.
- **No runtime activation.** No ``__main__``, no daemon, no
  scheduler, no background thread, no long-running service.
- **No external I/O.** No filesystem write, no network, no broker
  SDK, no market-data feed, no ``time.sleep``, no ``asyncio.sleep``,
  no ``os.environ`` / ``os.getenv``, no real account / venue /
  endpoint / secret.
- **Composed, not new fake.** This module exercises the three
  already-merged in-memory fakes against their abstract Protocol
  boundaries.
- **Deterministic.** Uses only the in-memory ``advance(seconds)``
  helpers on the three fakes; no wall-clock read.

Tests avoid ``pytest.raises`` / fixture-typed parameters so the mypy
strict pre-commit hook does not need a pytest-stub dependency. See
``tests/heartbeat/test_heartbeat_fixture.py``,
``tests/kill_switch/test_kill_switch_fixture.py``,
``tests/reconciliation/test_reconciliation_fixture.py``, and
``tests/p4_02_composed/test_composed_fixture.py`` for the same
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
    HeartbeatStatus,
    KillSwitchProtocol,
    KillSwitchState,
    ReconciliationProtocol,
    ReconciliationStatus,
)

_FIXED_CLOCK = datetime(2026, 5, 15, 14, 0, 0, tzinfo=UTC)


def _make_trio() -> tuple[InMemoryHeartbeat, InMemoryKillSwitch, InMemoryReconciliation]:
    """Construct the three in-memory fakes against a shared fixed clock.

    Mirrors the ``_make_trio`` helper in
    ``tests/p4_02_composed/test_composed_fixture.py``; the helper is
    re-implemented here (rather than imported across test modules) so
    the new module remains self-contained and the existing P4-02 test
    file is not modified.
    """
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    return heartbeat, kill_switch, reconciliation


# ---------------------------------------------------------------------------
# Invariant: ADR-002 trip stickiness across composed scenarios
# ---------------------------------------------------------------------------


def test_invariant_kill_switch_trip_is_sticky_across_all_other_state() -> None:
    """Once tripped, the kill switch reports ``TRIPPED`` regardless of
    heartbeat freshness or reconciliation outcome.

    ADR-002 mandates that a kill-switch trip is monotonic and sticky:
    no other observed state (a fresh operator heartbeat, a clean
    reconciliation report, time advancing) may flip ``TRIPPED`` back to
    ``ARMED``. This invariant is exercised across a small matrix of
    composed scenarios.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    kill_switch.trip(reason="invariant test trip", triggered_by="operator")
    # Vary heartbeat freshness, reconciliation outcomes, and clock
    # advances; the kill switch must remain TRIPPED in every case.
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    assert kill_switch.current().state is KillSwitchState.TRIPPED
    reconciliation.set_next(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"composed-invariants-scenario": "trip-sticky-clean"},
    )
    assert reconciliation.reconcile().status is ReconciliationStatus.CLEAN
    assert kill_switch.current().state is KillSwitchState.TRIPPED
    heartbeat.advance(9 * 3600.0)
    assert heartbeat.status("operator").status is HeartbeatStatus.STALE
    assert kill_switch.current().state is KillSwitchState.TRIPPED
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=99.0,
        details={"composed-invariants-scenario": "trip-sticky-failed"},
    )
    assert reconciliation.reconcile().status is ReconciliationStatus.FAILED
    assert kill_switch.current().state is KillSwitchState.TRIPPED


# ---------------------------------------------------------------------------
# Invariant: ADR-005 heartbeat staleness is independent of other controls
# ---------------------------------------------------------------------------


def test_invariant_heartbeat_status_is_independent_of_kill_switch_and_reconciliation() -> None:
    """Heartbeat status depends only on the heartbeat's own clock and
    the per-component ``beat`` history.

    A kill-switch trip and a ``FAILED`` reconciliation report must not
    change the heartbeat status reported by the heartbeat fake, nor the
    safe-default ``STALE`` for unknown components.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    baseline = heartbeat.status("operator").status
    assert baseline is HeartbeatStatus.FRESH
    kill_switch.trip(reason="invariant test", triggered_by="operator")
    assert heartbeat.status("operator").status is HeartbeatStatus.FRESH
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=42.0,
        details={"composed-invariants-scenario": "heartbeat-independence"},
    )
    assert reconciliation.reconcile().status is ReconciliationStatus.FAILED
    assert heartbeat.status("operator").status is HeartbeatStatus.FRESH
    # Unknown components remain STALE regardless of other controls.
    assert heartbeat.status("never-seen").status is HeartbeatStatus.STALE


# ---------------------------------------------------------------------------
# Invariant: ADR-003 UNAVAILABLE != FAILED across composed scenarios
# ---------------------------------------------------------------------------


def test_invariant_reconciliation_unavailable_distinct_from_failed_in_every_scenario() -> None:
    """``UNAVAILABLE`` and ``FAILED`` remain distinct values across composed scenarios.

    ADR-003 explicitly distinguishes ``UNAVAILABLE`` ("we could not
    determine the answer") from ``FAILED`` ("we determined a
    confirmed material mismatch"). This invariant asserts that the
    distinction is preserved across kill-switch trips, heartbeat
    staleness, queue drains, and explicitly staged outcomes.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    # Fresh-start: empty queue → UNAVAILABLE (not FAILED).
    assert reconciliation.reconcile().status is ReconciliationStatus.UNAVAILABLE
    assert ReconciliationStatus.UNAVAILABLE.value == "unavailable"
    assert ReconciliationStatus.FAILED.value == "failed"
    # Kill switch trip does not flip UNAVAILABLE to FAILED.
    kill_switch.trip(reason="invariant test", triggered_by="operator")
    assert reconciliation.reconcile().status is ReconciliationStatus.UNAVAILABLE
    # Heartbeat staleness does not flip UNAVAILABLE to FAILED.
    heartbeat.advance(9 * 3600.0)
    assert reconciliation.reconcile().status is ReconciliationStatus.UNAVAILABLE
    # Staged FAILED is FAILED, not UNAVAILABLE.
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=42.0,
        details={"composed-invariants-scenario": "explicit-failed"},
    )
    assert reconciliation.reconcile().status is ReconciliationStatus.FAILED
    # Drained again → UNAVAILABLE, not FAILED.
    assert reconciliation.reconcile().status is ReconciliationStatus.UNAVAILABLE


# ---------------------------------------------------------------------------
# Invariant: ADR-004 Z-suffixed UTC timestamps at every composed boundary
# ---------------------------------------------------------------------------


def test_invariant_all_timestamps_are_z_suffixed_utc_across_advances() -> None:
    """ADR-004 UTC discipline holds at every composed-fixture boundary,
    including after the heartbeat clock has been advanced.

    Each fake exposes timestamps as Z-suffixed UTC ISO-8601 strings;
    advancing one fake's clock must not produce a non-Z-suffixed
    timestamp on any of the three fakes.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    # Pre-advance: every timestamp Z-suffixed.
    hb_record = heartbeat.status("operator")
    ks_decision = kill_switch.current()
    rc_report = reconciliation.reconcile()
    assert hb_record.observed_at.endswith("Z")
    assert hb_record.last_update.endswith("Z")
    assert ks_decision.observed_at.endswith("Z")
    assert rc_report.checked_at.endswith("Z")
    # Advance only the heartbeat's clock; every timestamp still Z-suffixed.
    heartbeat.advance(9 * 3600.0)
    hb_record_after = heartbeat.status("operator")
    ks_decision_after = kill_switch.current()
    rc_report_after = reconciliation.reconcile()
    assert hb_record_after.observed_at.endswith("Z")
    assert hb_record_after.last_update.endswith("Z")
    assert ks_decision_after.observed_at.endswith("Z")
    assert rc_report_after.checked_at.endswith("Z")
    # Trip the kill switch; its observed_at must remain Z-suffixed.
    tripped = kill_switch.trip(reason="invariant test", triggered_by="operator")
    assert tripped.observed_at.endswith("Z")
    assert kill_switch.current().observed_at.endswith("Z")


# ---------------------------------------------------------------------------
# Invariant: composed safe defaults hold for a freshly composed trio
# ---------------------------------------------------------------------------


def test_invariant_safe_defaults_hold_across_repeated_construction() -> None:
    """Repeatedly constructing a fresh trio yields the same safe defaults.

    The three ADR-mandated safe defaults — ``STALE`` heartbeat for an
    unknown component, ``ARMED`` kill switch, ``UNAVAILABLE``
    reconciliation — must hold for every freshly constructed trio,
    independent of any prior trio's state.
    """
    for _ in range(3):
        heartbeat, kill_switch, reconciliation = _make_trio()
        assert heartbeat.status("operator").status is HeartbeatStatus.STALE
        assert kill_switch.current().state is KillSwitchState.ARMED
        assert reconciliation.reconcile().status is ReconciliationStatus.UNAVAILABLE


# ---------------------------------------------------------------------------
# Invariant: structural Protocol conformance is composed-scenario-stable
# ---------------------------------------------------------------------------


def test_invariant_protocol_conformance_is_stable_across_state_transitions() -> None:
    """Each fake conforms to its Protocol both before and after state transitions.

    Structural ``isinstance`` checks against the three
    ``runtime_checkable`` Protocols must succeed regardless of whether
    a fake has been advanced, tripped, or staged with outcomes.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    assert isinstance(heartbeat, HeartbeatProtocol)
    assert isinstance(kill_switch, KillSwitchProtocol)
    assert isinstance(reconciliation, ReconciliationProtocol)
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    kill_switch.trip(reason="invariant test", triggered_by="operator")
    reconciliation.set_next(
        status=ReconciliationStatus.WARNING,
        tolerance=10.0,
        observed_delta=3.0,
        details={"composed-invariants-scenario": "post-transition-conformance"},
    )
    reconciliation.reconcile()
    heartbeat.advance(9 * 3600.0)
    # Post-transition: still conforming.
    assert isinstance(heartbeat, HeartbeatProtocol)
    assert isinstance(kill_switch, KillSwitchProtocol)
    assert isinstance(reconciliation, ReconciliationProtocol)


# ---------------------------------------------------------------------------
# Invariant: per-component heartbeat independence under composed transitions
# ---------------------------------------------------------------------------


def test_invariant_per_component_heartbeats_remain_independent_under_composed_transitions() -> None:
    """ADR-005 per-component independence holds across composed transitions.

    A stale ``local-machine`` heartbeat does not pull a fresh
    ``operator`` heartbeat ``STALE``, even after the kill switch has
    been tripped and the reconciliation queue has been drained.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    heartbeat.beat("local-machine", _FIXED_CLOCK - timedelta(hours=10))
    # Compose: trip + drain.
    kill_switch.trip(reason="invariant test", triggered_by="operator")
    reconciliation.reconcile()  # empty queue → UNAVAILABLE
    # Per-component independence preserved.
    assert heartbeat.status("operator").status is HeartbeatStatus.FRESH
    assert heartbeat.status("local-machine").status is HeartbeatStatus.STALE
    assert heartbeat.status("never-seen").status is HeartbeatStatus.STALE


# ---------------------------------------------------------------------------
# No forbidden tokens / imports in the composed-invariants test module itself
# ---------------------------------------------------------------------------


_THIS_FILE = Path(__file__).resolve()


def test_composed_invariants_module_has_no_forbidden_runtime_imports() -> None:
    """The composed-invariants test module imports no runtime-coupling modules."""
    imported: set[str] = set()
    tree = ast.parse(_THIS_FILE.read_text())
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
    assert not leaked, f"P4-03 composed-invariants test must not import {leaked}"


def test_composed_invariants_module_only_imports_from_authorized_sources() -> None:
    """The composed-invariants test imports from the three merged Phase 3 fixture
    packages and from :mod:`gmc_rebuild.risk` (P2-05 protocol boundary) only,
    plus the standard-library helpers ``ast``, ``datetime``, ``pathlib``.

    This asserts that the composed-invariants test does **not** reach
    into any concrete protocol implementation that does not exist, does
    **not** re-export any merged Phase 3 fixture from any runtime path,
    and does **not** introduce a new ``src/**`` import target.
    """
    imported_from: set[str] = set()
    tree = ast.parse(_THIS_FILE.read_text())
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
            f"P4-03 composed-invariants test imported unauthorized module {mod!r}"
        )


def test_composed_invariants_module_imports_match_p4_02_pattern() -> None:
    """The composed-invariants module's actual code imports exactly the
    three merged Phase 3 fixture packages, ``gmc_rebuild.risk``, and the
    standard-library helpers ``ast``, ``datetime``, ``pathlib``,
    ``__future__`` — matching the P4-02 ``test_composed_fixture.py``
    import shape.

    Mirrors the P4-02 module's import-shape invariant. Asserts the
    actual top-level imports against the closed authorized set, so any
    accidental new import (a runtime coupling, a new fake, a concrete
    protocol implementation) would be detected.
    """
    tree = ast.parse(_THIS_FILE.read_text())
    top_level: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_level.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            top_level.add(node.module)
    expected = {
        "__future__",
        "ast",
        "datetime",
        "pathlib",
        "gmc_rebuild.heartbeat",
        "gmc_rebuild.kill_switch",
        "gmc_rebuild.reconciliation",
        "gmc_rebuild.risk",
    }
    assert top_level == expected, (
        f"P4-03 composed-invariants module imports drift: {top_level} != {expected}"
    )
