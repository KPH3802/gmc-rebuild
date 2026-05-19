"""Eligibility-check pure functions (P6-02).

This subpackage provides the second Phase 6 dry-run engine capability:
a pure-function eligibility check that accepts a P6-01
:class:`~gmc_rebuild.signal_intake.SignalIntent` plus a caller-supplied
:class:`EligibilityConfig` slice and returns a structured
:class:`EligibilityDecision` (``ELIGIBLE`` / ``INELIGIBLE`` with
closed-set reason codes). It is downstream of the P6-01 signal-intake
boundary and upstream of any later position / risk decision or
order-intent capability.

Authorization: ``governance/authorizations/2026-05-19_p6-02.md``.

Design constraints — these are governance constraints, not stylistic
preferences:

- **No runtime activation.** The package has no ``__main__`` entry
  point, no daemon, no scheduler, no background thread, no
  long-running service.
- **No external I/O.** No filesystem, no network, no broker SDK, no
  ``time.sleep``, no ``os.environ`` / ``os.getenv`` reads, no real
  external symbol allow/deny list. Every input — the
  :class:`~gmc_rebuild.signal_intake.SignalIntent` and every field of
  :class:`EligibilityConfig` — is supplied explicitly by the caller.
- **No external config loading.** This subpackage does not import
  :mod:`gmc_rebuild.config` or any other configuration source; the
  caller constructs the :class:`EligibilityConfig` slice and passes
  it in.
- **No real-runtime consumer.** This subpackage is not re-exported by
  :mod:`gmc_rebuild` as part of any runtime API. Its public surface
  is reachable only via ``from gmc_rebuild.eligibility import ...``.
- **No strategy / scanner / model / portfolio / backtest logic.**
  Eligibility is a structural pre-filter that compares the supplied
  intent against the supplied config slice. It does not generate
  signals, scan markets, fetch data, score candidates, or rank
  alternatives.
- **No order placement / broker integration / market data.** The
  decision returned here is informational; downstream packets (P6-03
  and beyond) decide what to do with it. This packet emits no order,
  contacts no broker, and reads no market data.
- **No mutation of inputs.** :func:`check_eligibility` does not
  modify the supplied :class:`SignalIntent` or
  :class:`EligibilityConfig`.
- **Closed enumerations.** :class:`EligibilityOutcome` has exactly
  two members (``ELIGIBLE``, ``INELIGIBLE``).
  :class:`EligibilityReason` has exactly five members enumerating
  the structural checks (``SYMBOL_NOT_ALLOWED``,
  ``SIDE_NOT_PERMITTED``, ``QUANTITY_BELOW_MINIMUM``,
  ``QUANTITY_ABOVE_MAXIMUM``, ``RATIONALE_TOO_SHORT``). Any expansion
  of either requires a separate written authorization per
  ``AI_WORKFLOW.md`` §7.
- **Closed dataclass shapes.** :class:`EligibilityConfig` has exactly
  five fields. :class:`EligibilityDecision` has exactly two fields.
  Both are frozen and slotted.
"""

from __future__ import annotations

from gmc_rebuild.eligibility._check import (
    EligibilityConfig,
    EligibilityDecision,
    EligibilityOutcome,
    EligibilityReason,
    check_eligibility,
)

__all__ = [
    "EligibilityConfig",
    "EligibilityDecision",
    "EligibilityOutcome",
    "EligibilityReason",
    "check_eligibility",
]
