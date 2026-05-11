"""Minimal, safe-by-default project configuration object (P2-02).

The configuration here is intentionally boring. It exists so that future
authorized Phase 2 work has a typed place to read project-level metadata
from. It does **not** describe trading behavior, broker integration,
market data, accounts, secrets, or any runtime that touches money.

Design constraints, mirrored from
``governance/authorizations/2026-05-11_p2-02.md`` §2 and §3:

- The config object is an immutable frozen dataclass.
- Defaults are local-only and disabled where they could imply runtime
  behavior.
- No broker names, no account identifiers, no credentials, no real
  endpoints, no market symbols, no strategy parameters, no execution /
  live / paper mode toggles.
- No loading from environment variables. If env-var support is needed
  later, it requires a separately authorized PR.
- No I/O, no network, no filesystem mutation. Reading
  ``ProjectConfig()`` produces a plain in-memory object.

Callers that need a modified copy use :func:`dataclasses.replace`
directly. ``ProjectConfig`` deliberately does not expose its own
``with_overrides`` helper: the standard-library helper is already
typed correctly and adding a wrapper would either widen its types or
duplicate them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    """Immutable project/environment metadata.

    All fields default to safe, local-only, runtime-disabled values.
    The object is frozen; use :func:`dataclasses.replace` to construct
    a modified copy.
    """

    project_name: str = "gmc-rebuild"
    package_name: str = "gmc_rebuild"
    phase: str = "phase-2"
    phase_task: str = "P2-02"
    environment: str = "local"
    runtime_enabled: bool = False
    local_data_dir: PurePosixPath = field(default_factory=lambda: PurePosixPath("./data"))
    local_logs_dir: PurePosixPath = field(default_factory=lambda: PurePosixPath("./logs"))


def default_config() -> ProjectConfig:
    """Return the canonical safe-default :class:`ProjectConfig`.

    This is a thin convenience wrapper around ``ProjectConfig()`` so
    callers can express intent ("I want the project defaults") without
    relying on positional construction.
    """
    return ProjectConfig()
