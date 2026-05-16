"""P4-08 safety policy hardening tests.

Pure-Python, in-memory, pytest-only tests that harden the merged P4-06
runtime safety policy and the merged P4-07 read-only operator view by
proving, exhaustively across the cross-product of observable
heartbeat / kill-switch / reconciliation states, that:

- :attr:`SafetyVerdict.clear` is ``True`` **if and only if** every
  required heartbeat component is :attr:`HeartbeatStatus.FRESH`, the
  kill switch is :attr:`KillSwitchState.ARMED`, and reconciliation is
  :attr:`ReconciliationStatus.CLEAN`. Any other observed combination is
  blocked (or advisory-blocked, in the case of
  :attr:`ReconciliationStatus.WARNING`) and reports a non-empty,
  documented set of blocker codes.
- The read-only operator view (:class:`OperatorSafetyView` /
  :func:`format_safety_verdict`) preserves the policy end-to-end: a
  blocked verdict can never be rendered as :data:`VERDICT_CLEAR`, and a
  cleared verdict can never be rendered as :data:`VERDICT_BLOCKED`.
- The blocker-code vocabulary is exactly the five documented codes
  (:data:`BLOCKER_HEARTBEAT_STALE`, :data:`BLOCKER_KILL_SWITCH_TRIPPED`,
  :data:`BLOCKER_RECONCILIATION_FAILED`,
  :data:`BLOCKER_RECONCILIATION_UNAVAILABLE`,
  :data:`BLOCKER_RECONCILIATION_WARNING`) — the policy cannot be
  weakened by silently widening the blocker set.
- Calling :meth:`RuntimeShell.evaluate` and formatting the resulting
  verdict do not mutate the injected fakes, so the policy cannot be
  weakened by accidental side effects on the underlying controls.

The tests do not introduce any new runtime surface; they exercise the
already-merged P4-06 / P4-07 surfaces through the merged P3-03 / P3-04 /
P3-05 in-memory fakes. They are pure-Python, in-memory, deterministic,
and do not perform any I/O.

Authorization: ``governance/authorizations/2026-05-16_p4-08.md``.

Tests avoid ``pytest.raises`` / fixture-typed parameters so the mypy
strict pre-commit hook does not need a pytest-stub dependency, matching
the pattern used by ``tests/runtime/test_runtime_shell.py`` and
``tests/runtime/test_operator_view.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from itertools import product

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
    RuntimeShell,
    SafetyVerdict,
    format_safety_verdict,
)

_FIXED_CLOCK = datetime(2026, 5, 16, 15, 0, 0, tzinfo=UTC)
_REQUIRED_COMPONENT = "operator"

_DOCUMENTED_BLOCKER_CODES: frozenset[str] = frozenset(
    {
        BLOCKER_HEARTBEAT_STALE,
        BLOCKER_KILL_SWITCH_TRIPPED,
        BLOCKER_RECONCILIATION_FAILED,
        BLOCKER_RECONCILIATION_UNAVAILABLE,
        BLOCKER_RECONCILIATION_WARNING,
    }
)


def _build_shell_in_state(
    *,
    heartbeat_status: HeartbeatStatus,
    kill_state: KillSwitchState,
    recon_status: ReconciliationStatus,
) -> tuple[RuntimeShell, InMemoryHeartbeat, InMemoryKillSwitch, InMemoryReconciliation]:
    """Stage three in-memory fakes in the requested observable state."""
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)

    if heartbeat_status is HeartbeatStatus.FRESH:
        heartbeat.beat(_REQUIRED_COMPONENT, _FIXED_CLOCK - timedelta(minutes=5))
    # STALE is the safe default for an unknown component; no beat needed.

    if kill_state is KillSwitchState.TRIPPED:
        kill_switch.trip(
            reason="p4-08-hardening-trip",
            triggered_by="p4-08-hardening-test",
        )

    if recon_status is ReconciliationStatus.CLEAN:
        reconciliation.set_next(
            status=ReconciliationStatus.CLEAN,
            tolerance=10.0,
            observed_delta=0.0,
            details={"p4-08-scenario": "clean"},
        )
    elif recon_status is ReconciliationStatus.WARNING:
        reconciliation.set_next(
            status=ReconciliationStatus.WARNING,
            tolerance=10.0,
            observed_delta=5.0,
            details={"p4-08-scenario": "warning"},
        )
    elif recon_status is ReconciliationStatus.FAILED:
        reconciliation.set_next(
            status=ReconciliationStatus.FAILED,
            tolerance=10.0,
            observed_delta=42.5,
            details={"p4-08-scenario": "failed"},
        )
    # UNAVAILABLE is the safe default; no staging needed.

    shell = RuntimeShell(
        heartbeat=heartbeat,
        kill_switch=kill_switch,
        reconciliation=reconciliation,
        required_components=(_REQUIRED_COMPONENT,),
    )
    return shell, heartbeat, kill_switch, reconciliation


def _expected_blockers(
    *,
    heartbeat_status: HeartbeatStatus,
    kill_state: KillSwitchState,
    recon_status: ReconciliationStatus,
) -> tuple[str, ...]:
    """Compute the documented blocker tuple for the requested state.

    The ordering mirrors :meth:`RuntimeShell.evaluate`:
    ``(heartbeat_*, kill_switch_*, reconciliation_*)``.
    """
    blockers: list[str] = []
    if heartbeat_status is HeartbeatStatus.STALE:
        blockers.append(BLOCKER_HEARTBEAT_STALE)
    if kill_state is KillSwitchState.TRIPPED:
        blockers.append(BLOCKER_KILL_SWITCH_TRIPPED)
    if recon_status is ReconciliationStatus.FAILED:
        blockers.append(BLOCKER_RECONCILIATION_FAILED)
    elif recon_status is ReconciliationStatus.UNAVAILABLE:
        blockers.append(BLOCKER_RECONCILIATION_UNAVAILABLE)
    elif recon_status is ReconciliationStatus.WARNING:
        blockers.append(BLOCKER_RECONCILIATION_WARNING)
    return tuple(blockers)


# ---------------------------------------------------------------------------
# Exhaustive cross-product: clear iff FRESH + ARMED + CLEAN
# ---------------------------------------------------------------------------


def test_clear_iff_fresh_armed_clean_across_full_cross_product() -> None:
    """Across every observable combination, ``clear`` matches FRESH+ARMED+CLEAN.

    Iterates the full cross-product of :class:`HeartbeatStatus`,
    :class:`KillSwitchState`, and :class:`ReconciliationStatus` and
    asserts that :attr:`SafetyVerdict.clear` is ``True`` if and only if
    the state tuple is exactly ``(FRESH, ARMED, CLEAN)``. The blockers
    tuple is also checked against the documented ordering so the policy
    cannot be weakened by quietly dropping a code.
    """
    seen_clear_states: list[tuple[HeartbeatStatus, KillSwitchState, ReconciliationStatus]] = []
    for hb, ks, rc in product(HeartbeatStatus, KillSwitchState, ReconciliationStatus):
        shell, _, _, _ = _build_shell_in_state(
            heartbeat_status=hb,
            kill_state=ks,
            recon_status=rc,
        )
        verdict = shell.evaluate()
        assert isinstance(verdict, SafetyVerdict)
        expected_clear = (
            hb is HeartbeatStatus.FRESH
            and ks is KillSwitchState.ARMED
            and rc is ReconciliationStatus.CLEAN
        )
        assert verdict.clear is expected_clear, (
            f"clear must be {expected_clear} for state ({hb}, {ks}, {rc}); "
            f"got clear={verdict.clear}, blockers={verdict.blockers}"
        )
        expected_blockers = _expected_blockers(
            heartbeat_status=hb, kill_state=ks, recon_status=rc
        )
        assert verdict.blockers == expected_blockers, (
            f"blocker tuple drifted for state ({hb}, {ks}, {rc}): "
            f"expected {expected_blockers}, got {verdict.blockers}"
        )
        if expected_clear:
            seen_clear_states.append((hb, ks, rc))

    assert seen_clear_states == [
        (HeartbeatStatus.FRESH, KillSwitchState.ARMED, ReconciliationStatus.CLEAN)
    ], (
        "exactly one (heartbeat, kill_switch, reconciliation) combination "
        "must yield clear=True; safety policy weakened if more or fewer appear"
    )


# ---------------------------------------------------------------------------
# Blocker vocabulary is closed: cannot be widened accidentally
# ---------------------------------------------------------------------------


def test_blocker_vocabulary_is_exactly_the_documented_set() -> None:
    """The set of blocker codes emitted across every state is the documented five.

    Guards against accidental widening of the blocker vocabulary — for
    example, an unfiltered enum value sneaking into the blockers tuple
    or a stringification bug producing a novel code. The vocabulary
    must be exactly the five documented codes; nothing more, nothing
    less.
    """
    observed: set[str] = set()
    for hb, ks, rc in product(HeartbeatStatus, KillSwitchState, ReconciliationStatus):
        shell, _, _, _ = _build_shell_in_state(
            heartbeat_status=hb,
            kill_state=ks,
            recon_status=rc,
        )
        verdict = shell.evaluate()
        observed.update(verdict.blockers)
    assert observed == _DOCUMENTED_BLOCKER_CODES, (
        "observed blocker vocabulary drifted from the documented set: "
        f"expected {_DOCUMENTED_BLOCKER_CODES}, got {observed}"
    )


# ---------------------------------------------------------------------------
# Each non-CLEAN reconciliation status remains visible (no silent collapse)
# ---------------------------------------------------------------------------


def test_each_non_clean_recon_status_emits_its_own_distinct_blocker() -> None:
    """``FAILED``, ``UNAVAILABLE``, and ``WARNING`` each emit their own blocker code.

    Prevents a regression that would collapse two reconciliation states
    onto a single blocker code (e.g. treating ``WARNING`` as ``FAILED``
    or merging ``UNAVAILABLE`` into ``FAILED``). The three non-``CLEAN``
    states must remain individually visible so the operator view can
    distinguish them.
    """
    expectations = {
        ReconciliationStatus.FAILED: BLOCKER_RECONCILIATION_FAILED,
        ReconciliationStatus.UNAVAILABLE: BLOCKER_RECONCILIATION_UNAVAILABLE,
        ReconciliationStatus.WARNING: BLOCKER_RECONCILIATION_WARNING,
    }
    for status, expected_code in expectations.items():
        shell, _, _, _ = _build_shell_in_state(
            heartbeat_status=HeartbeatStatus.FRESH,
            kill_state=KillSwitchState.ARMED,
            recon_status=status,
        )
        verdict = shell.evaluate()
        assert verdict.clear is False
        assert verdict.reconciliation_status is status
        assert verdict.blockers == (expected_code,), (
            f"reconciliation status {status} must emit exactly {expected_code!r}; "
            f"got {verdict.blockers}"
        )


# ---------------------------------------------------------------------------
# Operator view preserves the policy end-to-end
# ---------------------------------------------------------------------------


def test_operator_view_status_tracks_verdict_clear_across_cross_product() -> None:
    """The operator view's status mirrors ``SafetyVerdict.clear`` exactly.

    For every observable combination, :func:`format_safety_verdict` must
    label the view :data:`VERDICT_CLEAR` if and only if the verdict is
    ``clear``. A regression that rendered a blocked verdict as
    ``CLEAR`` — or vice versa — would silently weaken the safety
    foundation by hiding a blocker from the operator.
    """
    for hb, ks, rc in product(HeartbeatStatus, KillSwitchState, ReconciliationStatus):
        shell, _, _, _ = _build_shell_in_state(
            heartbeat_status=hb,
            kill_state=ks,
            recon_status=rc,
        )
        verdict = shell.evaluate()
        view = format_safety_verdict(verdict)
        if verdict.clear:
            assert view.status == VERDICT_CLEAR
            assert view.blocker_lines == ()
        else:
            assert view.status == VERDICT_BLOCKED
            assert view.blocker_lines, (
                f"blocked verdict for state ({hb}, {ks}, {rc}) must surface "
                f"at least one blocker line in the operator view"
            )
            rendered = view.render()
            assert f"safety: {VERDICT_BLOCKED}" in rendered
            assert f"safety: {VERDICT_CLEAR}" not in rendered


def test_operator_view_render_never_drops_a_blocker() -> None:
    """Every blocker code in the verdict surfaces in the rendered text.

    The rendered operator view is the read-only surface most likely to
    be consulted by a human; dropping a blocker from the rendering would
    weaken the safety foundation even if the underlying verdict was
    correct. This test asserts that every blocker in the verdict has a
    corresponding line in the rendered output across the full
    cross-product.
    """
    for hb, ks, rc in product(HeartbeatStatus, KillSwitchState, ReconciliationStatus):
        shell, _, _, _ = _build_shell_in_state(
            heartbeat_status=hb,
            kill_state=ks,
            recon_status=rc,
        )
        verdict = shell.evaluate()
        if verdict.clear:
            continue
        view = format_safety_verdict(verdict)
        rendered = view.render()
        assert len(view.blocker_lines) == len(verdict.blockers), (
            f"blocker line count diverged from verdict.blockers for state "
            f"({hb}, {ks}, {rc}): lines={view.blocker_lines}, "
            f"blockers={verdict.blockers}"
        )
        for blocker_line in view.blocker_lines:
            assert blocker_line in rendered


# ---------------------------------------------------------------------------
# Inert: evaluation and formatting do not mutate underlying fakes
# ---------------------------------------------------------------------------


def test_evaluate_and_format_do_not_mutate_underlying_controls() -> None:
    """Repeated evaluate + format calls must not change kill-switch or heartbeat state.

    The safety policy could be weakened in practice by an evaluator that
    silently re-armed a tripped kill switch or refreshed a stale
    heartbeat as a side effect of reading them. This test stages a
    fully-blocked state, evaluates and formats twice, and asserts that
    the kill switch remains TRIPPED and the heartbeat remains STALE.
    """
    shell, heartbeat, kill_switch, _ = _build_shell_in_state(
        heartbeat_status=HeartbeatStatus.STALE,
        kill_state=KillSwitchState.TRIPPED,
        recon_status=ReconciliationStatus.FAILED,
    )
    first = shell.evaluate()
    _ = format_safety_verdict(first)
    assert kill_switch.current().state is KillSwitchState.TRIPPED
    assert heartbeat.status(_REQUIRED_COMPONENT).status is HeartbeatStatus.STALE
    assert first.clear is False
    assert BLOCKER_HEARTBEAT_STALE in first.blockers
    assert BLOCKER_KILL_SWITCH_TRIPPED in first.blockers


# ---------------------------------------------------------------------------
# Multi-component policy: any STALE component blocks
# ---------------------------------------------------------------------------


def test_multi_component_heartbeat_any_stale_blocks_even_with_armed_clean() -> None:
    """With ARMED + CLEAN, a single STALE component still blocks the verdict.

    Hardens the multi-component heartbeat policy: even when the kill
    switch is ARMED and reconciliation is CLEAN, a single STALE
    component out of N must produce a blocked verdict and a
    ``BLOCKER_HEARTBEAT_STALE`` code visible to the operator view. The
    safety policy must not silently treat "most components FRESH" as
    "clear".
    """
    heartbeat = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    kill_switch = InMemoryKillSwitch(observed_at=_FIXED_CLOCK)
    reconciliation = InMemoryReconciliation(checked_at=_FIXED_CLOCK)
    heartbeat.beat("operator", _FIXED_CLOCK - timedelta(minutes=5))
    # "local_machine" is intentionally never beat → STALE
    reconciliation.set_next(
        status=ReconciliationStatus.CLEAN,
        tolerance=10.0,
        observed_delta=0.0,
        details={"p4-08-scenario": "multi-component"},
    )
    shell = RuntimeShell(
        heartbeat=heartbeat,
        kill_switch=kill_switch,
        reconciliation=reconciliation,
        required_components=("operator", "local_machine"),
    )
    verdict = shell.evaluate()
    assert verdict.clear is False
    assert BLOCKER_HEARTBEAT_STALE in verdict.blockers
    assert verdict.heartbeat_statuses["operator"] is HeartbeatStatus.FRESH
    assert verdict.heartbeat_statuses["local_machine"] is HeartbeatStatus.STALE
    view = format_safety_verdict(verdict)
    assert view.status == VERDICT_BLOCKED
    rendered = view.render()
    assert (
        f"heartbeat[local_machine]: {HeartbeatStatus.STALE.value}" in rendered
    )
    assert f"heartbeat[operator]: {HeartbeatStatus.FRESH.value}" in rendered


# ---------------------------------------------------------------------------
# Cleared verdict is the only path to VERDICT_CLEAR
# ---------------------------------------------------------------------------


def test_no_blocked_verdict_can_be_rendered_as_clear() -> None:
    """No combination of non-(FRESH, ARMED, CLEAN) states renders as ``CLEAR``.

    Stronger inverse of
    :func:`test_operator_view_status_tracks_verdict_clear_across_cross_product`:
    enumerates every non-(FRESH, ARMED, CLEAN) combination, formats each
    verdict, and asserts the rendered status is :data:`VERDICT_BLOCKED`.
    This is the end-to-end statement of the safety foundation: the only
    way to surface ``CLEAR`` to an operator is via a verdict whose three
    underlying controls are simultaneously FRESH + ARMED + CLEAN.
    """
    for hb, ks, rc in product(HeartbeatStatus, KillSwitchState, ReconciliationStatus):
        if (
            hb is HeartbeatStatus.FRESH
            and ks is KillSwitchState.ARMED
            and rc is ReconciliationStatus.CLEAN
        ):
            continue
        shell, _, _, _ = _build_shell_in_state(
            heartbeat_status=hb,
            kill_state=ks,
            recon_status=rc,
        )
        verdict = shell.evaluate()
        view = format_safety_verdict(verdict)
        assert view.status == VERDICT_BLOCKED, (
            f"state ({hb}, {ks}, {rc}) rendered as {view.status!r}; "
            f"only (FRESH, ARMED, CLEAN) may render as {VERDICT_CLEAR!r}"
        )
