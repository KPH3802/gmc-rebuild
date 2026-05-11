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


def test_package_has_no_runtime_submodules() -> None:
    """Phase 2 P2-01 is skeleton-only; no submodules are introduced yet."""
    src_root = Path(__file__).resolve().parents[1] / "src" / "gmc_rebuild"
    entries = {p.name for p in src_root.iterdir() if not p.name.startswith("__")}
    assert entries == {"py.typed"}, f"unexpected package contents: {entries}"
