"""gmc_rebuild.config — minimal safe configuration foundation (P2-02).

This subpackage is authorized by PR P2-02 (see
``governance/authorizations/2026-05-11_p2-02.md`` and
``plan/phase2_entry_plan.md`` §4). It provides a small, immutable
project/environment metadata object with safe defaults and no runtime
behavior.

P2-02 deliberately does **not** introduce:

- broker names, account identifiers, credentials, or endpoints,
- market symbols, strategy parameters, signals, or scanners,
- live or paper trading toggles wired to any real venue,
- environment-variable loading (deferred to a future, separately
  authorized PR),
- daemons, schedulers, or any ``__main__`` entry point.

See ``MASTER_STATUS.md`` §6, §7, and §8 for the phase-boundary controls
that continue to apply.
"""

from __future__ import annotations

from gmc_rebuild.config.schema import ProjectConfig, default_config

__all__ = ["ProjectConfig", "default_config"]
