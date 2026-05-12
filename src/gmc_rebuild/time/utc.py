"""UTC-only time utilities (P2-03).

ADR-004 requires strict UTC throughout the repository. This module is the
single in-tree implementation of that discipline: it produces only
timezone-aware UTC ``datetime`` objects, formats them with the trailing
``Z`` suffix the ADR documents, and rejects timezone-naive inputs at the
API boundary.

Design constraints, mirrored from
``governance/authorizations/2026-05-12_p2-03.md``:

- No trading, broker, order, market-data, persistence, scheduler, or
  daemon logic. This module contains only pure, deterministic helpers
  built on ``datetime``.
- No environment-variable reads, no filesystem I/O, no network calls.
- The only source of non-determinism is :func:`now_utc`, which delegates
  to :meth:`datetime.datetime.now` with an explicit UTC tzinfo so test
  callers can monkeypatch it or use ``freezegun``-style fakes.
"""

from __future__ import annotations

from datetime import UTC, datetime


class NaiveDatetimeError(ValueError):
    """Raised when a timezone-naive ``datetime`` is given at the API boundary.

    ADR-004 forbids naive datetimes. This exception is a ``ValueError`` so
    callers can catch it with the same handler they use for other bad-input
    cases, while still distinguishing the UTC-discipline violation by type.
    """


def now_utc() -> datetime:
    """Return the current time as a timezone-aware UTC ``datetime``.

    The returned object has ``tzinfo == datetime.UTC`` and ``utcoffset()``
    equal to ``timedelta(0)``. Callers must never call
    :meth:`datetime.datetime.utcnow`; it is naive and is the exact failure
    mode ADR-004 exists to prevent.
    """
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    """Return ``value`` normalized to UTC, rejecting naive datetimes.

    A timezone-aware non-UTC datetime is converted to UTC via
    :meth:`datetime.datetime.astimezone`. A timezone-naive datetime raises
    :class:`NaiveDatetimeError`: ADR-004 forbids guessing the intended
    zone, and silently assuming UTC would defeat the discipline.
    """
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise NaiveDatetimeError(
            "timezone-naive datetime is not accepted; ADR-004 requires UTC-aware values"
        )
    return value.astimezone(UTC)


def format_utc(value: datetime) -> str:
    """Format a timezone-aware datetime as an ISO-8601 UTC string with ``Z``.

    Examples: ``2026-05-12T14:23:45Z``, ``2026-05-12T14:23:45.123456Z``.
    Equivalent to ``ensure_utc(value).isoformat()`` with ``+00:00``
    rewritten to ``Z`` per ADR-004's documented format.
    """
    iso = ensure_utc(value).isoformat()
    suffix = "+00:00"
    if iso.endswith(suffix):
        return iso[: -len(suffix)] + "Z"
    return iso


def parse_utc(value: str) -> datetime:
    """Parse an ISO-8601 string into a timezone-aware UTC ``datetime``.

    Accepts either an explicit offset (``+00:00``, ``-05:00``) or the
    ``Z`` suffix. Strings without any offset are rejected with
    :class:`NaiveDatetimeError`: ADR-004 forbids guessing the intended
    zone. The returned datetime is normalized to UTC regardless of the
    input offset.
    """
    if not isinstance(value, str):
        raise TypeError(f"parse_utc expects a str, got {type(value).__name__}")
    normalized = value.strip()
    if not normalized:
        raise ValueError("parse_utc received an empty string")
    if normalized.endswith("Z") or normalized.endswith("z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"could not parse {value!r} as ISO-8601: {exc}") from exc
    return ensure_utc(parsed)
