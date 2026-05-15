"""P4-04 composed-edge-cases test.

Pure-Python, in-memory, pytest-only composed-edge-cases test extending
the merged P4-02 composed-fixture coverage at
``tests/p4_02_composed/test_composed_fixture.py`` and the merged P4-03
composed-invariants coverage at
``tests/p4_02_composed/test_composed_invariants.py``. Asserts boundary
and edge-case behaviour at the composed level — properties at threshold
boundaries, idempotency under repeated operations, FIFO-vs-clock
interleaving, and `__slots__` immutability of the three already-merged
in-memory fakes — exercised against their abstract :class:`typing.Protocol`
boundaries declared in :mod:`gmc_rebuild.risk` (``HeartbeatProtocol``,
``KillSwitchProtocol``, ``ReconciliationProtocol``).

Authorization: ``governance/authorizations/2026-05-15_p4-04.md``.

Design constraints — these are governance constraints, not stylistic
preferences:

- **No new ``src/**`` directory or file.** This test lives only as
  one new file in the existing ``tests/p4_02_composed/`` directory.
- **No modification of existing test files.** The merged
  ``tests/p4_02_composed/__init__.py``,
  ``tests/p4_02_composed/test_composed_fixture.py``, and
  ``tests/p4_02_composed/test_composed_invariants.py`` are preserved
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
``tests/reconciliation/test_reconciliation_fixture.py``,
``tests/p4_02_composed/test_composed_fixture.py``, and
``tests/p4_02_composed/test_composed_invariants.py`` for the same
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
    HeartbeatStatus,
    KillSwitchState,
    ReconciliationStatus,
)

_FIXED_CLOCK = datetime(2026, 5, 15, 14, 0, 0, tzinfo=UTC)


def _make_trio() -> tuple[InMemoryHeartbeat, InMemoryKillSwitch, InMemoryReconciliation]:
    """Construct the three in-memory fakes against a shared fixed clock.

    Mirrors the ``_make_trio`` helper in
    ``tests/p4_02_composed/test_composed_fixture.py`` and
    ``tests/p4_02_composed/test_composed_invariants.py``; the helper is
    re-implemented here (rather than imported across test modules) so
    the new module remains self-contained and the existing P4-02 / P4-03
    test files are not modified.
    """
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    return heartbeat, kill_switch, reconciliation


# ---------------------------------------------------------------------------
# Edge case: ADR-005 staleness boundary
# ---------------------------------------------------------------------------


def test_edge_heartbeat_status_exactly_at_default_threshold_is_fresh() -> None:
    """At exactly the ADR-005 default 8-hour boundary, status is still FRESH.

    The fake's threshold check is ``age > threshold``, not ``age >=``,
    so a heartbeat whose age is exactly equal to the threshold remains
    ``FRESH``. The composed scenario asserts that the boundary is
    inclusive of FRESH and exclusive of STALE, in line with the fake's
    documented behaviour, while the kill switch and reconciliation
    remain at their safe defaults.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    eight_hours_ago = _FIXED_CLOCK - timedelta(hours=8)
    heartbeat.beat("operator", eight_hours_ago)
    record = heartbeat.status("operator")
    assert record.status is HeartbeatStatus.FRESH
    assert record.age_seconds == 8 * 3600.0
    # Other controls untouched.
    assert kill_switch.current().state is KillSwitchState.ARMED
    assert reconciliation.reconcile().status is ReconciliationStatus.UNAVAILABLE


def test_edge_heartbeat_status_just_past_default_threshold_is_stale() -> None:
    """One second past the ADR-005 default 8-hour boundary, status is STALE.

    Complements the boundary-FRESH test above: ``age = threshold + 1``
    crosses into ``STALE``. The other two controls remain at safe
    defaults because their clocks did not advance.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    just_past = _FIXED_CLOCK - timedelta(hours=8, seconds=1)
    heartbeat.beat("operator", just_past)
    record = heartbeat.status("operator")
    assert record.status is HeartbeatStatus.STALE
    assert record.age_seconds == 8 * 3600.0 + 1.0
    assert kill_switch.current().state is KillSwitchState.ARMED
    assert reconciliation.reconcile().status is ReconciliationStatus.UNAVAILABLE


def test_edge_heartbeat_custom_threshold_independent_of_default() -> None:
    """A custom ``threshold_seconds`` is honoured at the composed boundary.

    Constructs a heartbeat with a 60-second threshold against the shared
    fixed clock, records a beat 59 seconds ago (FRESH), then records a
    new beat 61 seconds ago (STALE). Demonstrates that ``threshold_seconds``
    is the only knob driving the FRESH / STALE decision; the kill switch
    and reconciliation remain unaffected.
    """
    heartbeat_custom = InMemoryHeartbeat(observed_at=_FIXED_CLOCK, threshold_seconds=60.0)
    _, kill_switch, reconciliation = _make_trio()
    heartbeat_custom.beat("operator", _FIXED_CLOCK - timedelta(seconds=59))
    assert heartbeat_custom.status("operator").status is HeartbeatStatus.FRESH
    heartbeat_custom.beat("operator", _FIXED_CLOCK - timedelta(seconds=61))
    assert heartbeat_custom.status("operator").status is HeartbeatStatus.STALE
    # Other controls untouched (separate trio fakes — independent clocks).
    assert kill_switch.current().state is KillSwitchState.ARMED
    assert reconciliation.reconcile().status is ReconciliationStatus.UNAVAILABLE


# ---------------------------------------------------------------------------
# Edge case: ADR-002 trip idempotency / repeat-trip semantics
# ---------------------------------------------------------------------------


def test_edge_kill_switch_repeat_trip_overwrites_reason_and_actor() -> None:
    """A second ``trip(...)`` call records the new reason and triggered_by.

    ADR-002 names trip as recording an active trip; the fake's
    documented behaviour is "stores at most one active trip" — a
    second trip overwrites the first. The composed assertion is that
    subsequent ``current()`` calls reflect the most recent trip's
    reason and actor, the state remains ``TRIPPED``, and the heartbeat
    and reconciliation are unaffected.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    first = kill_switch.trip(reason="first trip", triggered_by="operator-1")
    assert first.state is KillSwitchState.TRIPPED
    assert first.reason == "first trip"
    assert first.triggered_by == "operator-1"
    # Sticky between trips: still TRIPPED with first-trip metadata.
    mid = kill_switch.current()
    assert mid.state is KillSwitchState.TRIPPED
    assert mid.reason == "first trip"
    assert mid.triggered_by == "operator-1"
    # Second trip overwrites recorded metadata.
    second = kill_switch.trip(reason="second trip", triggered_by="operator-2")
    assert second.state is KillSwitchState.TRIPPED
    assert second.reason == "second trip"
    assert second.triggered_by == "operator-2"
    after = kill_switch.current()
    assert after.state is KillSwitchState.TRIPPED
    assert after.reason == "second trip"
    assert after.triggered_by == "operator-2"
    # Heartbeat and reconciliation unaffected by trip overwrite.
    assert heartbeat.status("operator").status is HeartbeatStatus.FRESH
    assert reconciliation.reconcile().status is ReconciliationStatus.UNAVAILABLE


def test_edge_kill_switch_advance_does_not_alter_recorded_trip_metadata() -> None:
    """Advancing the kill switch clock after a trip preserves trip metadata.

    The trip's ``reason`` and ``triggered_by`` are recorded once and do
    not change when the in-memory clock advances; only ``observed_at``
    on subsequent ``current()`` decisions reflects the advanced clock.
    The heartbeat and reconciliation are unaffected because their clocks
    are independent.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    pre = kill_switch.trip(reason="initial trip", triggered_by="operator")
    assert pre.observed_at == "2026-05-15T14:00:00Z"
    kill_switch.advance(3600.0)
    post = kill_switch.current()
    assert post.state is KillSwitchState.TRIPPED
    assert post.reason == "initial trip"
    assert post.triggered_by == "operator"
    assert post.observed_at == "2026-05-15T15:00:00Z"
    # Heartbeat / reconciliation clocks did not advance.
    assert heartbeat.status("operator").observed_at == "2026-05-15T14:00:00Z"
    assert reconciliation.reconcile().checked_at == "2026-05-15T14:00:00Z"


# ---------------------------------------------------------------------------
# Edge case: ADR-005 per-component last-write-wins
# ---------------------------------------------------------------------------


def test_edge_heartbeat_repeated_beat_is_last_write_wins_per_component() -> None:
    """Multiple ``beat`` calls for the same component keep only the latest.

    ADR-005's "fresh" / "stale" question is answered against the most
    recent ``beat`` for the named component. The composed assertion is
    that an old beat followed by a recent beat reports ``FRESH``, and
    that a recent beat followed by a very-old beat reports ``STALE``.
    The kill switch and reconciliation are unaffected.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    # Stale-then-fresh: last write is fresh → FRESH.
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(hours=10))
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    assert heartbeat.status("operator").status is HeartbeatStatus.FRESH
    # Fresh-then-stale: last write is stale → STALE.
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(hours=10))
    assert heartbeat.status("operator").status is HeartbeatStatus.STALE
    assert kill_switch.current().state is KillSwitchState.ARMED
    assert reconciliation.reconcile().status is ReconciliationStatus.UNAVAILABLE


# ---------------------------------------------------------------------------
# Edge case: ADR-003 FIFO ordering interleaved with advance / clock
# ---------------------------------------------------------------------------


def test_edge_reconciliation_fifo_preserved_across_clock_advance() -> None:
    """FIFO order of staged outcomes is preserved when the clock advances.

    ``advance`` only changes ``checked_at`` on subsequent
    :class:`ReconciliationReport` values; it does not reorder, drop, or
    duplicate queued outcomes. The composed scenario stages three
    outcomes, advances the clock between drains, and asserts the FIFO
    order plus the moving ``checked_at`` timestamp.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    reconciliation.enqueue(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"composed-edge-scenario": "fifo-1-clean"},
    )
    reconciliation.enqueue(
        status=ReconciliationStatus.WARNING,
        tolerance=10.0,
        observed_delta=3.0,
        details={"composed-edge-scenario": "fifo-2-warning"},
    )
    reconciliation.enqueue(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=42.0,
        details={"composed-edge-scenario": "fifo-3-failed"},
    )
    first = reconciliation.reconcile()
    assert first.status is ReconciliationStatus.CLEAN
    assert first.checked_at == "2026-05-15T14:00:00Z"
    reconciliation.advance(60.0)
    second = reconciliation.reconcile()
    assert second.status is ReconciliationStatus.WARNING
    assert second.checked_at == "2026-05-15T14:01:00Z"
    reconciliation.advance(120.0)
    third = reconciliation.reconcile()
    assert third.status is ReconciliationStatus.FAILED
    assert third.checked_at == "2026-05-15T14:03:00Z"
    # Drained → UNAVAILABLE, not FAILED.
    drained = reconciliation.reconcile()
    assert drained.status is ReconciliationStatus.UNAVAILABLE
    # Heartbeat / kill switch unaffected.
    assert heartbeat.status("operator").status is HeartbeatStatus.STALE
    assert kill_switch.current().state is KillSwitchState.ARMED


def test_edge_reconciliation_set_next_clears_queue_then_enqueues_one() -> None:
    """``set_next`` discards every previously-staged outcome before enqueuing one.

    The fake's documented contract is "Replace any queued outcomes with
    exactly one new outcome." The composed scenario stages two outcomes,
    calls ``set_next`` with a third, drains it (the only outcome that
    survives the clear), and confirms the next call reports ``UNAVAILABLE``
    because the queue is empty again.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    reconciliation.enqueue(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"composed-edge-scenario": "set-next-discarded-1"},
    )
    reconciliation.enqueue(
        status=ReconciliationStatus.WARNING,
        tolerance=10.0,
        observed_delta=2.0,
        details={"composed-edge-scenario": "set-next-discarded-2"},
    )
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=99.0,
        details={"composed-edge-scenario": "set-next-survives"},
    )
    survivor = reconciliation.reconcile()
    assert survivor.status is ReconciliationStatus.FAILED
    assert survivor.observed_delta == 99.0
    assert survivor.details["composed-edge-scenario"] == "set-next-survives"
    drained = reconciliation.reconcile()
    assert drained.status is ReconciliationStatus.UNAVAILABLE
    # Heartbeat / kill switch unaffected.
    assert heartbeat.status("operator").status is HeartbeatStatus.STALE
    assert kill_switch.current().state is KillSwitchState.ARMED


# ---------------------------------------------------------------------------
# Edge case: ADR-003 / ADR-005 zero-second advance is a no-op
# ---------------------------------------------------------------------------


def test_edge_advance_zero_seconds_is_no_op_across_all_three_fakes() -> None:
    """``advance(0)`` leaves every observable timestamp unchanged.

    The fakes accept ``0`` as a non-negative advance and the composed
    assertion is that none of the three fakes' next-emitted timestamps
    change after a zero-second advance.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    before_hb = heartbeat.status("operator").observed_at
    before_ks = kill_switch.current().observed_at
    before_rc = reconciliation.reconcile().checked_at
    heartbeat.advance(0.0)
    kill_switch.advance(0.0)
    reconciliation.advance(0.0)
    after_hb = heartbeat.status("operator").observed_at
    after_ks = kill_switch.current().observed_at
    after_rc = reconciliation.reconcile().checked_at
    assert before_hb == after_hb
    assert before_ks == after_ks
    assert before_rc == after_rc


# ---------------------------------------------------------------------------
# Edge case: __slots__ immutability across the composed trio
# ---------------------------------------------------------------------------


def test_edge_composed_fakes_reject_unknown_attribute_writes() -> None:
    """Each in-memory fake uses ``__slots__`` and rejects unknown attribute writes.

    The three fakes declare ``__slots__`` for their internal state. Any
    attempt to set an attribute outside that slot list raises
    ``AttributeError``. This composed scenario asserts the property
    against the trio without relying on ``pytest.raises`` (the same
    pytest-stub-free pattern P3-03 / P3-04 / P3-05 / P4-02 / P4-03 use).
    The attribute name is held in a local variable so ``setattr`` is
    invoked dynamically — the test exercises the runtime
    ``__slots__`` check, not a compile-time attribute check, and is
    therefore compatible with the mypy-strict pre-commit hook.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    raised: list[str] = []
    unknown = "unknown_attr"
    sentinel = "should-not-stick"
    try:
        setattr(heartbeat, unknown, sentinel)
    except AttributeError:
        raised.append("heartbeat")
    try:
        setattr(kill_switch, unknown, sentinel)
    except AttributeError:
        raised.append("kill_switch")
    try:
        setattr(reconciliation, unknown, sentinel)
    except AttributeError:
        raised.append("reconciliation")
    assert raised == ["heartbeat", "kill_switch", "reconciliation"]


# ---------------------------------------------------------------------------
# Edge case: unknown-component synthetic ``last_update`` is always older
# ---------------------------------------------------------------------------


def test_edge_unknown_component_synthetic_last_update_is_strictly_older() -> None:
    """The synthetic ``last_update`` for an unknown component sits past the threshold.

    The fake reports ``STALE`` for unknown components and constructs a
    synthetic ``last_update`` that is ``threshold + 1`` seconds older
    than ``observed_at``. The composed assertion is that this synthetic
    timestamp is strictly less than ``observed_at`` and that the
    reported ``age_seconds`` is exactly ``threshold + 1``, independent
    of the kill switch and reconciliation state.
    """
    heartbeat, kill_switch, reconciliation = _make_trio()
    kill_switch.trip(reason="composed edge trip", triggered_by="operator")
    reconciliation.set_next(
        status=ReconciliationStatus.FAILED,
        tolerance=10.0,
        observed_delta=42.0,
        details={"composed-edge-scenario": "unknown-component"},
    )
    reconciliation.reconcile()
    record = heartbeat.status("never-seen")
    assert record.status is HeartbeatStatus.STALE
    assert record.age_seconds == 8 * 3600.0 + 1.0
    # Last-update string is strictly older than observed_at; compare via parsed UTC.
    last_update = datetime.fromisoformat(record.last_update.replace("Z", "+00:00"))
    observed_at = datetime.fromisoformat(record.observed_at.replace("Z", "+00:00"))
    assert last_update < observed_at
    # Other controls reflect their composed-edge state, not the heartbeat's.
    assert kill_switch.current().state is KillSwitchState.TRIPPED


# ---------------------------------------------------------------------------
# No forbidden tokens / imports in the composed-edge-cases test module itself
# ---------------------------------------------------------------------------


_THIS_FILE = Path(__file__).resolve()


def test_composed_edge_cases_module_has_no_forbidden_runtime_imports() -> None:
    """The composed-edge-cases test module imports no runtime-coupling modules."""
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
    assert not leaked, f"P4-04 composed-edge-cases test must not import {leaked}"


def test_composed_edge_cases_module_only_imports_from_authorized_sources() -> None:
    """The composed-edge-cases test imports from the three merged Phase 3 fixture
    packages and from :mod:`gmc_rebuild.risk` (P2-05 protocol boundary) only,
    plus the standard-library helpers ``ast``, ``datetime``, ``pathlib``.

    This asserts that the composed-edge-cases test does **not** reach
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
            f"P4-04 composed-edge-cases test imported unauthorized module {mod!r}"
        )


def test_composed_edge_cases_module_imports_match_p4_02_pattern() -> None:
    """The composed-edge-cases module's actual code imports exactly the
    three merged Phase 3 fixture packages, ``gmc_rebuild.risk``, and the
    standard-library helpers ``ast``, ``datetime``, ``pathlib``,
    ``__future__`` — matching the P4-02 ``test_composed_fixture.py`` and
    P4-03 ``test_composed_invariants.py`` import shape.

    Mirrors the P4-02 / P4-03 modules' import-shape invariant. Asserts
    the actual top-level imports against the closed authorized set, so
    any accidental new import (a runtime coupling, a new fake, a
    concrete protocol implementation) would be detected.
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
        f"P4-04 composed-edge-cases module imports drift: {top_level} != {expected}"
    )
