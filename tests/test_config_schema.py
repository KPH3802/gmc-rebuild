"""P2-02 minimal config schema tests.

Verifies that the ``gmc_rebuild.config`` subpackage authorized by PR P2-02
(see ``governance/authorizations/2026-05-11_p2-02.md`` and
``plan/phase2_entry_plan.md`` §4):

- imports cleanly and exposes a safe, immutable :class:`ProjectConfig`;
- defaults are safe / disabled / local-only;
- introduces no forbidden runtime submodules and no forbidden fields;
- does not silently widen the phase-boundary categories tracked in
  ``MASTER_STATUS.md`` §6 / §8.
"""

from __future__ import annotations

import dataclasses
import importlib
import re
from pathlib import Path, PurePosixPath

from gmc_rebuild.config import ProjectConfig, default_config


def test_config_subpackage_imports() -> None:
    module = importlib.import_module("gmc_rebuild.config")
    assert module is not None
    assert getattr(module, "ProjectConfig", None) is ProjectConfig
    assert getattr(module, "default_config", None) is default_config


def test_default_config_is_frozen_dataclass_instance() -> None:
    cfg = default_config()
    assert isinstance(cfg, ProjectConfig)
    assert dataclasses.is_dataclass(cfg)
    params = getattr(ProjectConfig, "__dataclass_params__", None)
    assert params is not None
    assert params.frozen is True

    # Frozen-instance write must raise FrozenInstanceError. Using a
    # try/except rather than pytest.raises keeps the mypy strict hook
    # free of a pytest-stub dependency in its isolated environment.
    raised = False
    try:
        cfg.project_name = "mutated"  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        raised = True
    assert raised, "ProjectConfig is not frozen as expected"


def test_defaults_are_safe_disabled_and_local_only() -> None:
    cfg = default_config()
    assert cfg.project_name == "gmc-rebuild"
    assert cfg.package_name == "gmc_rebuild"
    assert cfg.phase == "phase-2"
    assert cfg.phase_task == "P2-02"
    assert cfg.environment == "local"
    assert cfg.runtime_enabled is False
    assert isinstance(cfg.local_data_dir, PurePosixPath)
    assert isinstance(cfg.local_logs_dir, PurePosixPath)
    # Local-only paths only; no absolute paths, no external URLs.
    assert not cfg.local_data_dir.is_absolute()
    assert not cfg.local_logs_dir.is_absolute()


def test_replace_returns_new_instance_and_does_not_mutate() -> None:
    cfg = default_config()
    other = dataclasses.replace(cfg, environment="ci")
    assert other is not cfg
    assert cfg.environment == "local"
    assert other.environment == "ci"
    assert other.runtime_enabled is False  # still safe-default


def test_config_fields_are_minimal_and_named_safely() -> None:
    """The schema must not introduce forbidden field names or hidden runtime knobs.

    The set of expected field names is pinned so that adding new fields
    (which would require a separately authorized PR) trips this test.
    """
    expected = {
        "project_name",
        "package_name",
        "phase",
        "phase_task",
        "environment",
        "runtime_enabled",
        "local_data_dir",
        "local_logs_dir",
    }
    actual = {f.name for f in dataclasses.fields(ProjectConfig)}
    assert actual == expected, (
        "ProjectConfig fields drifted from the P2-02 authorized set; "
        "see governance/authorizations/2026-05-11_p2-02.md"
    )

    # Whole-word match on field-name tokens against the MASTER_STATUS
    # §8 step 4c forbidden token set. Substring matches like "data"
    # inside "local_data_dir" are acceptable: step 4c tokenizes path
    # components, not field names, and the field name itself is a
    # compound that does not match a forbidden token under whole-token
    # comparison.
    forbidden_tokens = {
        "strategy",
        "strategies",
        "signal",
        "signals",
        "scanner",
        "scanners",
        "model",
        "models",
        "portfolio",
        "backtest",
        "backtests",
        "broker",
        "brokers",
        "execution",
        "executions",
        "live",
        "paper",
        "daemon",
        "daemons",
        "market_data",
        "order",
        "orders",
        "secret",
        "secrets",
    }
    for name in actual:
        tokens = {t.lower() for t in re.split(r"[._-]+", name) if t}
        assert not tokens & forbidden_tokens, (
            f"ProjectConfig field {name!r} tokenises to a forbidden category"
        )


def test_config_subpackage_has_no_forbidden_submodules() -> None:
    """The P2-02 directory authorizes a single config schema module only."""
    config_root = Path(__file__).resolve().parents[1] / "src" / "gmc_rebuild" / "config"
    files = {p.name for p in config_root.iterdir() if p.is_file()}
    dirs = {p.name for p in config_root.iterdir() if p.is_dir()}
    assert files == {"__init__.py", "schema.py"}, (
        f"unexpected files under src/gmc_rebuild/config/: {files}"
    )
    # No subdirectories are authorized under config/ in P2-02.
    assert not {d for d in dirs if d != "__pycache__"}, (
        f"unexpected subdirectories under src/gmc_rebuild/config/: {dirs}"
    )


def test_no_env_var_loading_in_config_module() -> None:
    """Env-var loading is explicitly out of scope for P2-02.

    Static check: the config module sources must not import ``os.environ``
    or call ``os.getenv``. Future authorized PRs may revisit this.
    """
    config_root = Path(__file__).resolve().parents[1] / "src" / "gmc_rebuild" / "config"
    for path in config_root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "os.environ" not in text, (
            f"{path} reads os.environ; P2-02 does not authorize env-var loading"
        )
        assert "os.getenv" not in text, (
            f"{path} calls os.getenv; P2-02 does not authorize env-var loading"
        )


def test_no_runtime_entrypoint_in_config_module() -> None:
    """P2-02 does not authorize any ``__main__`` entry point or daemon."""
    config_root = Path(__file__).resolve().parents[1] / "src" / "gmc_rebuild" / "config"
    for path in config_root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert '__name__ == "__main__"' not in text, f"{path} declares a __main__ entry point"
        assert "__name__ == '__main__'" not in text, f"{path} declares a __main__ entry point"


def test_phase_boundary_forbidden_categories_absent_from_tree() -> None:
    """Re-assert that the MASTER_STATUS §8 step 4 always-forbidden categories
    are not present as top-level paths in the working tree.

    This guards against the P2-02 PR (or any descendant) accidentally
    introducing a forbidden category at the repo root. The forbidden
    list is intentionally hard-coded here so that loosening the §8 list
    cannot silently loosen this test.
    """
    repo_root = Path(__file__).resolve().parents[1]
    forbidden = [
        "strategy",
        "strategies",
        "signal",
        "signals",
        "scanner",
        "scanners",
        "model",
        "models",
        "portfolio",
        "backtest",
        "backtests",
        "broker",
        "execution",
        "live",
        "paper",
        "daemons",
        "data",
        "market_data",
        "orders",
        "secrets",
    ]
    present = [name for name in forbidden if (repo_root / name).exists()]
    assert not present, (
        f"forbidden top-level path(s) present: {present}; see MASTER_STATUS.md §6 / §8 step 4"
    )
