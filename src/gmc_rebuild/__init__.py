"""gmc_rebuild package — Phase 2 infrastructure skeleton.

This package is intentionally empty of runtime behavior. It exists solely to
establish the importable ``src/`` layout authorized by PR P2-01 (see
``plan/phase2_entry_plan.md`` §4). No trading strategy, broker integration,
market data ingestion, runtime daemon, or other Phase 3+ behavior is
implemented here, and none is implied by the presence of this module.

The phase-boundary controls in ``MASTER_STATUS.md`` §6, §7, and §8 continue to
apply: forbidden categories remain forbidden regardless of where code is
placed.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
