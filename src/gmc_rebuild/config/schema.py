"""Minimal, safe-by-default project configuration object (P2-02).

The configuration here is intentionally boring. It exists so that future
authorized Phase 2 work has a typed place to read project-level metadata
from. It does **not** describe trading behavior, broker integration,
market data, accounts, secrets, or any runtime that touches money.

Design constraints, mirrored from
``governance/authorizations/2026-05-11_p2-02.md`` §2 and §3:

- The config object is an immutable frozen dataclass.
- Defaults are local-only.
- No broker names, no account identifiers, no credentials, no real
  endpoints, no market symbols, no strategy parameters, no execution /
  live / paper mode toggles, and **no runtime-behavior boolean flags**
  (even disabled ones — a future PR cannot wire what does not exist).
- No loading from environment variables. If env-var support is needed
  later, it requires a separately authorized PR.
- No I/O, no network, no filesystem mutation. Constructing
  :class:`ProjectConfig` produces a plain in-memory object; no
  directory is created and no file is opened by this module.

Callers that need a modified copy use :func:`dataclasses.replace`
directly. ``ProjectConfig`` deliberately does not expose its own
``with_overrides`` helper: the standard-library helper is already
typed correctly and adding a wrapper would either widen its types or
duplicate them.

Path-default safety note. ``local_data_dir`` defaults to
``PurePosixPath("./gmc_data")`` rather than ``./data`` because the
top-level path ``data`` is on the ``MASTER_STATUS.md`` §8 step 4
always-forbidden list and would trip the startup gate if it were
ever materialised at the repo root. ``gmc_data/`` is already
gitignored at the repository root (see ``.gitignore``). The default
is metadata only; nothing in this module reads or creates the path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    """Immutable project/environment metadata.

    All fields default to safe, local-only values. The object is
    frozen; use :func:`dataclasses.replace` to construct a modified
    copy.

    Fields are deliberately limited to descriptive metadata. No
    runtime-behavior toggles are included: there is no runtime in
    this PR for a toggle to gate, and adding a disabled toggle now
    would create exactly the kind of phase-expanding hook the
    governance rules in ``MASTER_STATUS.md`` §6 / §7 forbid.
    """

    project_name: str = "gmc-rebuild"
    package_name: str = "gmc_rebuild"
    phase: str = "phase-2"
    environment: str = "local"
    local_data_dir: PurePosixPath = field(default_factory=lambda: PurePosixPath("./gmc_data"))
    local_logs_dir: PurePosixPath = field(default_factory=lambda: PurePosixPath("./logs"))


def default_config() -> ProjectConfig:
    """Return the canonical safe-default :class:`ProjectConfig`.

    Thin wrapper over ``ProjectConfig()`` so callers can express
    intent ("the project defaults"). Authorized explicitly in
    ``governance/authorizations/2026-05-11_p2-02.md`` §2 alongside
    :class:`ProjectConfig` itself.
    """
    return ProjectConfig()
