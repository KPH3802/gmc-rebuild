"""P2-03 UTC time utility tests.

Verifies that the ``gmc_rebuild.time`` subpackage authorized by PR P2-03
(see ``governance/authorizations/2026-05-12_p2-03.md`` and
``plan/phase2_entry_plan.md`` §4):

- exposes a UTC-only ``now_utc``, ``ensure_utc``, ``format_utc``,
  ``parse_utc``, and ``NaiveDatetimeError`` API;
- always returns timezone-aware UTC values;
- rejects timezone-naive inputs at the API boundary per ADR-004;
- normalizes non-UTC aware inputs to UTC deterministically;
- introduces no forbidden submodules or runtime entry points.
"""

from __future__ import annotations

import importlib
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

from gmc_rebuild.time import (
    NaiveDatetimeError,
    ensure_utc,
    format_utc,
    now_utc,
    parse_utc,
)


def test_time_subpackage_imports() -> None:
    module = importlib.import_module("gmc_rebuild.time")
    assert module is not None
    assert getattr(module, "now_utc", None) is now_utc
    assert getattr(module, "ensure_utc", None) is ensure_utc
    assert getattr(module, "format_utc", None) is format_utc
    assert getattr(module, "parse_utc", None) is parse_utc
    assert getattr(module, "NaiveDatetimeError", None) is NaiveDatetimeError


def test_now_utc_returns_aware_utc_datetime() -> None:
    value = now_utc()
    assert isinstance(value, datetime)
    assert value.tzinfo is not None
    assert value.utcoffset() == timedelta(0)
    assert value.tzinfo is UTC


def test_now_utc_is_monotonic_across_calls() -> None:
    first = now_utc()
    second = now_utc()
    assert second >= first


def test_ensure_utc_passes_through_utc_aware() -> None:
    src = datetime(2026, 5, 12, 14, 23, 45, tzinfo=UTC)
    result = ensure_utc(src)
    assert result.tzinfo is UTC
    assert result == src


def test_ensure_utc_converts_non_utc_aware_to_utc() -> None:
    eastern = timezone(timedelta(hours=-5))
    src = datetime(2026, 5, 12, 9, 23, 45, tzinfo=eastern)
    result = ensure_utc(src)
    assert result.tzinfo is UTC
    assert result == datetime(2026, 5, 12, 14, 23, 45, tzinfo=UTC)


def test_ensure_utc_rejects_naive_datetime() -> None:
    naive = datetime(2026, 5, 12, 14, 23, 45)
    assert naive.tzinfo is None
    raised = False
    try:
        ensure_utc(naive)
    except NaiveDatetimeError as exc:
        raised = True
        assert "ADR-004" in str(exc)
    assert raised, "ensure_utc must reject timezone-naive datetimes"


def test_naive_datetime_error_is_value_error() -> None:
    assert issubclass(NaiveDatetimeError, ValueError)


def test_format_utc_uses_z_suffix_for_utc_aware() -> None:
    src = datetime(2026, 5, 12, 14, 23, 45, tzinfo=UTC)
    assert format_utc(src) == "2026-05-12T14:23:45Z"


def test_format_utc_preserves_microseconds() -> None:
    src = datetime(2026, 5, 12, 14, 23, 45, 123456, tzinfo=UTC)
    assert format_utc(src) == "2026-05-12T14:23:45.123456Z"


def test_format_utc_converts_non_utc_aware_before_formatting() -> None:
    eastern = timezone(timedelta(hours=-5))
    src = datetime(2026, 5, 12, 9, 23, 45, tzinfo=eastern)
    assert format_utc(src) == "2026-05-12T14:23:45Z"


def test_format_utc_rejects_naive_datetime() -> None:
    naive = datetime(2026, 5, 12, 14, 23, 45)
    raised = False
    try:
        format_utc(naive)
    except NaiveDatetimeError:
        raised = True
    assert raised, "format_utc must reject timezone-naive datetimes"


def test_parse_utc_accepts_z_suffix() -> None:
    parsed = parse_utc("2026-05-12T14:23:45Z")
    assert parsed == datetime(2026, 5, 12, 14, 23, 45, tzinfo=UTC)
    assert parsed.tzinfo is UTC


def test_parse_utc_accepts_lowercase_z_suffix() -> None:
    parsed = parse_utc("2026-05-12T14:23:45z")
    assert parsed == datetime(2026, 5, 12, 14, 23, 45, tzinfo=UTC)


def test_parse_utc_accepts_explicit_offset_and_normalizes_to_utc() -> None:
    parsed = parse_utc("2026-05-12T09:23:45-05:00")
    assert parsed.tzinfo is UTC
    assert parsed == datetime(2026, 5, 12, 14, 23, 45, tzinfo=UTC)


def test_parse_utc_accepts_explicit_zero_offset() -> None:
    parsed = parse_utc("2026-05-12T14:23:45+00:00")
    assert parsed == datetime(2026, 5, 12, 14, 23, 45, tzinfo=UTC)


def test_parse_utc_rejects_naive_string() -> None:
    raised = False
    try:
        parse_utc("2026-05-12T14:23:45")
    except NaiveDatetimeError:
        raised = True
    assert raised, "parse_utc must reject ISO strings with no offset"


def test_parse_utc_rejects_empty_string() -> None:
    raised = False
    try:
        parse_utc("")
    except ValueError:
        raised = True
    assert raised


def test_parse_utc_rejects_non_iso_garbage() -> None:
    raised = False
    try:
        parse_utc("not-a-date")
    except ValueError:
        raised = True
    assert raised


def test_parse_utc_rejects_non_string_input() -> None:
    raised = False
    try:
        parse_utc(12345)  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised


def test_format_parse_roundtrip_is_deterministic() -> None:
    src = datetime(2026, 5, 12, 14, 23, 45, 678901, tzinfo=UTC)
    formatted = format_utc(src)
    parsed = parse_utc(formatted)
    assert parsed == src
    assert format_utc(parsed) == formatted


def test_now_utc_is_deterministic_under_monkeypatch() -> None:
    """``now_utc`` must be replaceable so tests can pin time deterministically."""
    import gmc_rebuild.time as time_pkg
    import gmc_rebuild.time.utc as utc_mod

    fixed = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    original = utc_mod.now_utc

    def fake_now_utc() -> datetime:
        return fixed

    utc_mod.now_utc = fake_now_utc
    try:
        assert utc_mod.now_utc() == fixed
    finally:
        utc_mod.now_utc = original
    # Re-export through the package namespace still points at the original.
    assert time_pkg.now_utc is original


def test_time_subpackage_has_no_forbidden_submodules() -> None:
    """The P2-03 directory authorizes a single UTC utility module only."""
    time_root = Path(__file__).resolve().parents[1] / "src" / "gmc_rebuild" / "time"
    files = {p.name for p in time_root.iterdir() if p.is_file()}
    dirs = {p.name for p in time_root.iterdir() if p.is_dir() and p.name != "__pycache__"}
    assert files == {"__init__.py", "utc.py"}, (
        f"unexpected files under src/gmc_rebuild/time/: {files}"
    )
    assert not dirs, f"unexpected subdirectories under src/gmc_rebuild/time/: {dirs}"


def test_no_runtime_entrypoint_in_time_module() -> None:
    """P2-03 does not authorize any ``__main__`` entry point or daemon."""
    time_root = Path(__file__).resolve().parents[1] / "src" / "gmc_rebuild" / "time"
    for path in time_root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert '__name__ == "__main__"' not in text, f"{path} declares a __main__ entry point"
        assert "__name__ == '__main__'" not in text, f"{path} declares a __main__ entry point"


def test_no_env_var_loading_in_time_module() -> None:
    """Env-var loading is out of scope for P2-03."""
    time_root = Path(__file__).resolve().parents[1] / "src" / "gmc_rebuild" / "time"
    for path in time_root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "os.environ" not in text, f"{path} reads os.environ; P2-03 does not authorize it"
        assert "os.getenv" not in text, f"{path} calls os.getenv; P2-03 does not authorize it"


def test_time_module_does_not_call_naive_utcnow() -> None:
    """``datetime.utcnow`` is naive and explicitly forbidden by ADR-004."""
    time_root = Path(__file__).resolve().parents[1] / "src" / "gmc_rebuild" / "time"
    for path in time_root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "utcnow(" not in text, (
            f"{path} calls utcnow(); ADR-004 forbids naive UTC helpers"
        )
