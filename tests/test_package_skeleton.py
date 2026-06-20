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
    - ``decision/`` — PR P6-03 (position/risk decision composer;
      third Phase 6 dry-run implementation packet; declares the
      closed two-member ``PositionDecisionOutcome`` enumeration
      (``WOULD_TRADE``, ``WOULD_SKIP``), the closed five-member
      ``PositionDecisionReason`` enumeration
      (``ELIGIBILITY_INELIGIBLE``, ``SAFETY_HEARTBEAT_STALE``,
      ``SAFETY_KILL_SWITCH_NOT_ARMED``,
      ``SAFETY_RECONCILIATION_NOT_CLEAN``,
      ``SAFETY_VERDICT_NOT_CLEAR``), the frozen, slotted
      ``PositionDecision`` five-field result enforcing the
      ``WOULD_TRADE iff reasons == ()`` biconditional, and a pure
      ``compose_position_decision`` function that consumes a P6-01
      ``SignalIntent``, a P6-02 ``EligibilityDecision``, and a P4-06
      ``SafetyVerdict`` and returns a ``PositionDecision``; no
      strategy logic, no broker integration, no market-data
      ingestion, no order placement, no external config loading, no
      network, no secrets, no scheduler, no persistence, no
      ``time.sleep``, no ``__main__``). See
      ``governance/authorizations/2026-05-20_p6-03.md``.
    - ``portfolio_state/`` — PR P6-05 (deterministic in-memory
      simulated portfolio state; fifth Phase 6 dry-run implementation
      packet; declares the frozen, slotted ``SimulatedPosition`` and
      ``SimulatedPortfolio`` value types and the pure
      ``apply_simulated_order_intent`` function that applies an accepted
      P6-03 ``PositionDecision`` with a P6-04 ``SimulatedOrderIntent``
      to a position book under a fixed, deterministic, fixture-only
      full-fill assumption, idempotent by the deterministic P6-04
      simulated order intent ID; frozen / value-typed replaceable
      snapshot model; no real position book, account, balances, P&L,
      cash ledger, valuation, broker, market data, orders, network,
      secrets, scheduler, persistence, ``time.sleep``, ``__main__``).
      The directory name carries the forbidden ``portfolio`` token and
      is allowlisted on the ``MASTER_STATUS.md`` §8 step 4a gate per the
      P6-01 ``signal_intake`` precedent. See
      ``governance/authorizations/2026-05-22_p6-05.md``.
    - ``reporting/`` — PR P6-06 (deterministic daily dry-run report;
      sixth Phase 6 dry-run implementation packet; declares the frozen,
      slotted ``DailyReport`` value object, the pure
      ``build_daily_report`` builder, and the pure
      ``render_daily_report_event`` renderer that summarizes a simulated
      cycle (P6-03 decisions, the P6-05 ``SimulatedPortfolio`` snapshot,
      the P2-05 / P3-05 ``ReconciliationStatus``, and caller-supplied
      tripped-invariant codes) and emits it only via the merged P2-04
      ``audit_event`` helper under the closed ``lifecycle`` category;
      caller-supplied timestamp only, no internal clock read, no
      ``AUDIT_CATEGORIES`` change, no external sink, no real position
      book, broker, market data, orders, network, secrets, scheduler,
      persistence, ``time.sleep``, or ``__main__``). See
      ``governance/authorizations/2026-05-23_p6-06.md``.
    - ``operator_view/`` — PR P6-07 (deterministic read-only operator
      view of dry-run engine state; seventh Phase 6 dry-run
      implementation packet; declares the frozen, slotted
      ``DryRunOperatorView`` value object and the pure
      ``build_dry_run_operator_view`` builder that project the cycle's
      P6-03 ``PositionDecision`` results, the cycle's P6-04
      ``SimulatedOrderIntent`` values, the end-of-cycle P6-05
      ``SimulatedPortfolio`` snapshot, and the P6-06 ``DailyReport``
      summary into an operator-facing value object plus a deterministic
      multi-line string render; ``SafetyVerdict`` is excluded from
      inputs and ``gmc_rebuild.runtime`` is not imported, so the merged
      P4-07 ``OperatorSafetyView`` is not composed with; no clock read
      (any date is echoed from ``DailyReport.report_date``); no
      ``audit_event`` emission, no ``gmc_rebuild.logging`` import, no
      external log sink, no real position book, broker, market data,
      orders, network, secrets, scheduler, persistence, ``time.sleep``,
      or ``__main__``). See
      ``governance/authorizations/2026-06-15_p6-07.md``.
    - ``dry_run/`` — PR P6-DRYRUN-ENTRYPOINT (runnable dry-run loop
      entrypoint; composes the merged P6-01..P6-07 surfaces into one
      watchable pipeline executed via ``python -m gmc_rebuild.dry_run``;
      adds no new engine logic; imports only public symbols from
      already-authorized merged modules; pure / deterministic /
      value-typed at the library boundary; caller-supplied (fixed
      inline) timestamps only, no internal clock read; the only side
      effect is a single ``print`` in the ``__main__`` module; no
      external log sink, no real position book, broker, market data,
      orders, network, secrets, scheduler, persistence, or
      ``time.sleep``). See
      ``governance/authorizations/2026-06-18_dry-run-entrypoint.md``.
    - ``insider_cluster_intake/`` — PR INSIDER-CLUSTER-INTAKE (insider-
      cluster signal intake adapter; reads ONE row from a caller-
      supplied ``backtest_results`` SQLite database in read-only URI
      mode and adapts it into a typed
      ``gmc_rebuild.signal_intake.SignalIntent``; adds no engine logic,
      modifies no engine module; read-only filesystem access via stdlib
      ``sqlite3`` with ``?mode=ro`` URI — cannot write; deterministic
      share-quantity derivation; no network, no broker, no real account,
      no credentials, no env-var read, no secrets, no scheduler, no
      daemon, no ``time.sleep``, no clock read, no ``__main__``; not
      re-exported from ``src/gmc_rebuild/__init__.py``). See
      ``governance/authorizations/2026-06-18_insider-cluster-intake.md``.
    - ``dry_run_reconciliation/`` — PR P6-09 (deterministic in-memory
      read-only dry-run position reconciliation; ninth Phase 6 dry-run
      implementation packet; declares the closed two-member
      ``DryRunReconciliationOutcome`` enumeration (``MATCH``,
      ``MISMATCH``), the frozen, slotted ``ExpectedPositions`` input value
      object with a ``from_simulated_portfolio`` convenience constructor,
      the frozen, slotted ``ReconciliationQuantityMismatch`` per-symbol
      record, the frozen, slotted six-field ``DryRunReconciliationResult``
      enforcing the ``MATCH`` iff no-differences biconditional, and a pure
      ``reconcile_dry_run_positions`` function that compares a P6-05
      ``SimulatedPortfolio`` snapshot against an ``ExpectedPositions``
      input and echoes the caller-supplied P2-05 ``ReconciliationStatus``
      verbatim; no ``render()`` method, no ``ReconciliationProtocol``
      implementation, no import or runtime use of
      ``gmc_rebuild.reconciliation`` (the P3-05 fixture), no
      ``gmc_rebuild.runtime`` import, no real position book, account,
      broker, market data, orders, network, secrets, scheduler,
      persistence, clock read, ``audit_event``, ``time.sleep``, or
      ``__main__``; not re-exported from
      ``src/gmc_rebuild/__init__.py``). The directory name carries no
      forbidden token, so the step 4 / step 4c scans stay clean. See
      ``governance/authorizations/2026-06-19_p6-09.md``.
    - ``dry_run_reconciliation_view/`` — PR P6-10 (deterministic read-only
      JSON projection of a merged P6-09 ``DryRunReconciliationResult`` into
      a JSON-serializable ``dict`` so the structured reconciliation outcome
      can be surfaced through the same operator-facing ``--emit-json`` lane
      PR #196 established for dry-run decisions; tenth Phase 6 dry-run
      implementation packet; declares the single pure
      ``build_dry_run_reconciliation_json_payload`` function and adds no new
      reconciliation logic, consuming the merged P6-09 public surface by
      value only; no clock read, no I/O, no file handle, no ``audit_event``
      emission, no ``gmc_rebuild.logging`` / ``gmc_rebuild.runtime`` /
      ``gmc_rebuild.reconciliation`` import, no real position book, account,
      broker, market data, orders, network, secrets, scheduler, persistence,
      ``time.sleep``, or ``__main__``; not re-exported from
      ``src/gmc_rebuild/__init__.py``). The directory name carries no
      forbidden token, so the step 4 / step 4c scans stay clean. See
      ``governance/authorizations/2026-06-20_p6-10.md``.

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
        "decision",
        "portfolio_state",
        "reporting",
        "operator_view",
        "dry_run",
        "insider_cluster_intake",
        "dry_run_reconciliation",
        "dry_run_reconciliation_view",
    }, f"unexpected package contents: {entries}"
