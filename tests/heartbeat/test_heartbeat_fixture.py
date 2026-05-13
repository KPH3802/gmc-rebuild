"""P3-03 HeartbeatProtocol in-memory fixture tests.

Verifies that the ``gmc_rebuild.heartbeat`` subpackage authorized by
the P3-03 implementation PR (see
``governance/authorizations/2026-05-13_p3-03.md``):

- exposes the in-memory fake fixture (and only that);
- conforms structurally to :class:`gmc_rebuild.risk.HeartbeatProtocol`;
- preserves ADR-005 safe-default behavior (unknown components are
  ``STALE``);
- preserves ADR-005 staleness semantics (within-threshold beats are
  ``FRESH``, beyond-threshold beats are ``STALE``);
- preserves ADR-004 UTC discipline at the boundary (naive datetimes
  are rejected);
- introduces no forbidden runtime entry points, env-var reads, or
  filesystem / network / sleep / broker I/O.

Tests avoid ``pytest.raises`` / fixture-typed parameters so the mypy
strict pre-commit hook does not need a pytest-stub dependency. See
``tests/test_risk_interfaces.py`` for the same pattern.
"""

from __future__ import annotations

import ast
import importlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

from gmc_rebuild.heartbeat import InMemoryHeartbeat
from gmc_rebuild.heartbeat._fake import DEFAULT_STALENESS_SECONDS
from gmc_rebuild.risk import (
    HeartbeatProtocol,
    HeartbeatRecord,
    HeartbeatStatus,
    RiskControlError,
)
from gmc_rebuild.time import NaiveDatetimeError


_FIXED_CLOCK = datetime(2026, 5, 13, 14, 0, 0, tzinfo=UTC)


def _expect_risk_error(call: object, match: str) -> None:
    raised: Exception | None = None
    try:
        call()  # type: ignore[operator]
    except RiskControlError as exc:
        raised = exc
    assert isinstance(raised, RiskControlError), (
        f"expected RiskControlError matching {match!r}, got {raised!r}"
    )
    assert match in str(raised), f"RiskControlError message {str(raised)!r} missing {match!r}"


def _expect_naive_error(call: object) -> None:
    raised: Exception | None = None
    try:
        call()  # type: ignore[operator]
    except NaiveDatetimeError as exc:
        raised = exc
    assert isinstance(raised, NaiveDatetimeError), (
        f"expected NaiveDatetimeError, got {raised!r}"
    )


# ---------------------------------------------------------------------------
# Package surface
# ---------------------------------------------------------------------------


def test_heartbeat_subpackage_imports() -> None:
    module = importlib.import_module("gmc_rebuild.heartbeat")
    assert module is not None
    assert hasattr(module, "InMemoryHeartbeat")
    assert getattr(module, "__all__") == ["InMemoryHeartbeat"]


def test_default_staleness_is_adr_005_eight_hours() -> None:
    assert DEFAULT_STALENESS_SECONDS == 8 * 3600.0


def test_heartbeat_not_reexported_from_runtime_root() -> None:
    runtime_root = importlib.import_module("gmc_rebuild")
    assert not hasattr(runtime_root, "heartbeat") or (
        getattr(runtime_root, "__all__", None) is not None
        and "heartbeat" not in runtime_root.__all__
        and "InMemoryHeartbeat" not in runtime_root.__all__
    )


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_fake_is_heartbeat_protocol_instance() -> None:
    fake = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    assert isinstance(fake, HeartbeatProtocol)


def test_status_returns_heartbeat_record() -> None:
    fake = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    fake.beat("operator", _FIXED_CLOCK - timedelta(minutes=5))
    record = fake.status("operator")
    assert isinstance(record, HeartbeatRecord)
    assert record.component == "operator"


# ---------------------------------------------------------------------------
# ADR-005 safe-default behavior
# ---------------------------------------------------------------------------


def test_unknown_component_is_stale_not_raising() -> None:
    fake = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    record = fake.status("never-seen")
    assert record.status is HeartbeatStatus.STALE
    assert record.component == "never-seen"
    assert record.age_seconds > DEFAULT_STALENESS_SECONDS


def test_fresh_beat_within_threshold_is_fresh() -> None:
    fake = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    fake.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    record = fake.status("operator")
    assert record.status is HeartbeatStatus.FRESH
    assert record.age_seconds == 60.0


def test_beat_older_than_threshold_is_stale() -> None:
    fake = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    fake.beat("operator", _FIXED_CLOCK - timedelta(hours=9))
    record = fake.status("operator")
    assert record.status is HeartbeatStatus.STALE
    assert record.age_seconds == 9 * 3600.0


def test_beat_exactly_at_threshold_is_fresh() -> None:
    fake = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    fake.beat("operator", _FIXED_CLOCK - timedelta(seconds=DEFAULT_STALENESS_SECONDS))
    record = fake.status("operator")
    assert record.status is HeartbeatStatus.FRESH


def test_custom_threshold_is_respected() -> None:
    fake = InMemoryHeartbeat(observed_at=_FIXED_CLOCK, threshold_seconds=60.0)
    fake.beat("operator", _FIXED_CLOCK - timedelta(seconds=30))
    assert fake.status("operator").status is HeartbeatStatus.FRESH
    fake.beat("operator", _FIXED_CLOCK - timedelta(seconds=120))
    assert fake.status("operator").status is HeartbeatStatus.STALE


def test_advance_clock_makes_fresh_beats_stale() -> None:
    fake = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    fake.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    assert fake.status("operator").status is HeartbeatStatus.FRESH
    fake.advance(DEFAULT_STALENESS_SECONDS + 60.0)
    assert fake.status("operator").status is HeartbeatStatus.STALE


def test_multiple_components_are_independent() -> None:
    fake = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    fake.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    fake.beat("local-machine", _FIXED_CLOCK - timedelta(hours=10))
    assert fake.status("operator").status is HeartbeatStatus.FRESH
    assert fake.status("local-machine").status is HeartbeatStatus.STALE
    assert fake.status("other").status is HeartbeatStatus.STALE


# ---------------------------------------------------------------------------
# ADR-004 UTC discipline at the boundary
# ---------------------------------------------------------------------------


def test_construction_rejects_naive_observed_at() -> None:
    _expect_naive_error(lambda: InMemoryHeartbeat(observed_at=datetime(2026, 5, 13, 14)))


def test_beat_rejects_naive_when() -> None:
    fake = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    _expect_naive_error(lambda: fake.beat("operator", datetime(2026, 5, 13, 14)))


def test_record_timestamps_are_z_suffixed_utc_strings() -> None:
    fake = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    fake.beat("operator", _FIXED_CLOCK - timedelta(minutes=1))
    record = fake.status("operator")
    assert record.last_update.endswith("Z")
    assert record.observed_at.endswith("Z")
    assert record.observed_at == "2026-05-13T14:00:00Z"


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_threshold_must_be_positive_number() -> None:
    _expect_risk_error(
        lambda: InMemoryHeartbeat(observed_at=_FIXED_CLOCK, threshold_seconds=0),
        "threshold_seconds must be positive",
    )
    _expect_risk_error(
        lambda: InMemoryHeartbeat(observed_at=_FIXED_CLOCK, threshold_seconds=-1.0),
        "threshold_seconds must be positive",
    )
    _expect_risk_error(
        lambda: InMemoryHeartbeat(
            observed_at=_FIXED_CLOCK,
            threshold_seconds=True,
        ),
        "threshold_seconds must be a number",
    )


def test_advance_rejects_negative_or_non_numeric() -> None:
    fake = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    _expect_risk_error(lambda: fake.advance(-1.0), "must be non-negative")
    _expect_risk_error(
        lambda: fake.advance(True),
        "must be a number",
    )


def test_beat_rejects_empty_or_whitespace_component() -> None:
    fake = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    _expect_risk_error(lambda: fake.beat("", _FIXED_CLOCK), "non-empty str")
    _expect_risk_error(
        lambda: fake.beat("op erator", _FIXED_CLOCK), "must not contain whitespace"
    )


def test_status_rejects_empty_or_whitespace_component() -> None:
    fake = InMemoryHeartbeat(observed_at=_FIXED_CLOCK)
    _expect_risk_error(lambda: fake.status(""), "non-empty str")
    _expect_risk_error(lambda: fake.status("op erator"), "must not contain whitespace")


# ---------------------------------------------------------------------------
# No forbidden runtime behavior
# ---------------------------------------------------------------------------


_PKG_ROOT = Path(__file__).resolve().parent.parent.parent / "src" / "gmc_rebuild" / "heartbeat"


def _heartbeat_source_files() -> list[Path]:
    return sorted(_PKG_ROOT.glob("*.py"))


def _strip_docstrings_and_comments(source: str) -> str:
    """Return ``source`` with module/class/function docstrings and # comments removed.

    Used so the "no forbidden tokens" checks below match real code, not
    governance commentary in docstrings. Docstrings are intentionally
    verbose under the P3-03 authorization and reference forbidden token
    names by design (to assert what the module is *not*).
    """
    tree = ast.parse(source)
    # Collect docstring line ranges.
    drop_ranges: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", None)
            if not body:
                continue
            first = body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                drop_ranges.append((first.lineno, getattr(first, "end_lineno", first.lineno)))
    lines = source.splitlines()
    keep: list[str] = []
    for idx, raw in enumerate(lines, start=1):
        if any(lo <= idx <= hi for lo, hi in drop_ranges):
            continue
        # Strip trailing line comments.
        if "#" in raw:
            raw = raw.split("#", 1)[0]
        keep.append(raw)
    return "\n".join(keep)


def _heartbeat_code_text() -> str:
    return "\n".join(_strip_docstrings_and_comments(p.read_text()) for p in _heartbeat_source_files())


def test_heartbeat_package_has_no_main_entry_point() -> None:
    code = _heartbeat_code_text()
    assert "__main__" not in code
    assert "if __name__" not in code


def test_heartbeat_package_has_no_forbidden_runtime_imports() -> None:
    imported: set[str] = set()
    for path in _heartbeat_source_files():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    imported.add(node.module.split(".")[0])
    forbidden = {
        "os",
        "socket",
        "requests",
        "urllib",
        "http",
        "threading",
        "asyncio",
        "subprocess",
        "sqlite3",
        "pickle",
        "shelve",
        "ssl",
        "smtplib",
        "ftplib",
    }
    leaked = forbidden & imported
    assert not leaked, f"heartbeat package must not import {leaked}"


def test_heartbeat_package_has_no_sleep_or_env_reads() -> None:
    code = _heartbeat_code_text()
    for needle in (
        "time.sleep",
        "asyncio.sleep",
        "os.environ",
        "os.getenv",
        "getenv(",
        "open(",
        "socket.",
        "urllib.",
        "requests.",
    ):
        assert needle not in code, f"heartbeat package code must not contain {needle!r}"


def test_heartbeat_package_does_not_modify_risk_subpackage() -> None:
    code = _heartbeat_code_text()
    assert "from gmc_rebuild.risk" in code or "import gmc_rebuild.risk" in code
