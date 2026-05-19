"""P2-01 package skeleton tests.

Verifies the importable ``gmc_rebuild`` package exists, exposes a version, and
contains no runtime behavior beyond the placeholder skeleton authorized by
``plan/phase2_entry_plan.md`` §4.
"""

from __future__ import annotations

import importlib
from pathlib import Path


def test_package_is_importable() -> None:
    module = importlib.import_module("gmc_rebuild")
    assert module is not None


def test_package_exposes_version() -> None:
    module = importlib.import_module("gmc_rebuild")
    version = getattr(module, "__version__", None)
    assert isinstance(version, str)
    assert version  # non-empty


def test_package_lives_under_src_layout() -> None:
    module = importlib.import_module("gmc_rebuild")
    module_file = getattr(module, "__file__", None)
    assert module_file is not None
    src_root = Path(__file__).resolve().parents[1] / "src" / "gmc_rebuild"
    assert Path(module_file).resolve().parent == src_root.resolve()


def test_package_has_py_typed_marker() -> None:
    src_root = Path(__file__).resolve().parents[1] / "src" / "gmc_rebuild"
    assert (src_root / "py.typed").is_file()


def test_package_contents_match_authorized_phase2_tasks() -> None:
    """The ``src/gmc_rebuild`` tree must only contain authorized entries.

    Authorized entries to date:

    - ``py.typed`` and ``__init__.py`` — PR P2-01 (package skeleton).
    - ``config/`` — PR P2-02 (minimal safe config schema). See
      ``governance/authorizations/2026-05-11_p2-02.md``.
    - ``time/`` — PR P2-03 (minimal UTC time utility). See
      ``governance/authorizations/2026-05-12_p2-03.md``.
    - ``logging/`` — PR P2-04 (structured logging and audit event
      conventions). See
      ``governance/authorizations/2026-05-12_p2-04.md``.
    - ``risk/`` — PR P2-05 (risk-control interfaces). See
      ``governance/authorizations/2026-05-12_p2-05.md``.
    - ``heartbeat/`` — PR P3-03 (HeartbeatProtocol in-memory test
      fixture; pure-Python in-memory fake only, no runtime activation).
      See ``governance/authorizations/2026-05-13_p3-03.md``.
    - ``kill_switch/`` — PR P3-04 (KillSwitchProtocol in-memory test
      fixture; pure-Python in-memory fake only, no runtime activation).
      See ``governance/authorizations/2026-05-14_p3-04.md``.
    - ``reconciliation/`` — PR P3-05 (ReconciliationProtocol in-memory
      test fixture; pure-Python in-memory fake only, no runtime
      activation). See
      ``governance/authorizations/2026-05-14_p3-05.md``.
    - ``runtime/`` — PR P4-06 (inert local runtime shell boundary;
      composes the abstract Protocol boundaries declared in
      ``gmc_rebuild.risk`` only, no runtime activation, no broker,
      no market data, no orders, no scheduler, no persistence, no
      network, no secrets, no ``time.sleep``). See
      ``governance/authorizations/2026-05-16_p4-06.md``.
    - ``simulation/`` — PR P5-01 (inert local simulation boundary
      skeleton; declares ``SimulationLane``, ``SimulatedIntent``, and
      a ``SimulationBoundary`` that gates a placeholder simulated
      progression on an already-clear
      ``gmc_rebuild.runtime.SafetyVerdict``; no broker, paper-broker,
      market data, real orders, network, secrets, scheduler,
      persistence, or ``time.sleep``). See
      ``governance/authorizations/2026-05-17_p5-01.md``.
    - ``signal_intake/`` — PR P6-01 (typed signal-intake boundary;
      first Phase 6 dry-run implementation packet; declares the closed
      ``SignalSide`` enumeration, the frozen, slotted ``SignalIntent``
      five-field dataclass, and a pure ``accept_signal_intent`` typed
      acceptance function; no strategy logic, no broker integration,
      no market-data ingestion, no order placement, no network, no
      secrets, no scheduler, no persistence, no ``time.sleep``, no
      ``__main__``). See
      ``governance/authorizations/2026-05-19_p6-01.md``.
    - ``eligibility/`` — PR P6-02 (eligibility-check pure functions;
      second Phase 6 dry-run implementation packet; declares the
      closed two-member ``EligibilityOutcome`` enumeration, the closed
      five-member ``EligibilityReason`` enumeration, the frozen,
      slotted ``EligibilityConfig`` five-field caller-supplied config
      slice, the frozen, slotted ``EligibilityDecision`` two-field
      result, and a pure ``check_eligibility`` function that compares
      a P6-01 ``SignalIntent`` against the supplied
      ``EligibilityConfig`` and returns an ``EligibilityDecision``;
      no strategy logic, no broker integration, no market-data
      ingestion, no order placement, no external config loading, no
      network, no secrets, no scheduler, no persistence, no
      ``time.sleep``, no ``__main__``). See
      ``governance/authorizations/2026-05-19_p6-02.md``.

    Any additional entry indicates a phase-expanding change without an
    authorization artifact and must be rejected at review.
    """
    src_root = Path(__file__).resolve().parents[1] / "src" / "gmc_rebuild"
    entries = {p.name for p in src_root.iterdir() if not p.name.startswith("__")}
    assert entries == {
        "py.typed",
        "config",
        "time",
        "logging",
        "risk",
        "heartbeat",
        "kill_switch",
        "reconciliation",
        "runtime",
        "simulation",
        "signal_intake",
        "eligibility",
    }, f"unexpected package contents: {entries}"
