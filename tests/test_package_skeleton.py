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

    Any additional entry indicates a phase-expanding change without an
    authorization artifact and must be rejected at review.
    """
    src_root = Path(__file__).resolve().parents[1] / "src" / "gmc_rebuild"
    entries = {p.name for p in src_root.iterdir() if not p.name.startswith("__")}
    assert entries == {"py.typed", "config"}, f"unexpected package contents: {entries}"
