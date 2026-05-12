"""Structured audit-event conventions (P2-04).

Defines the canonical audit-event shape used by future Phase 2 / Phase 3
governance, configuration, and review code. The implementation is
intentionally minimal — conventions, an immutable record type, a builder,
and a deterministic JSON serializer — with no runtime side effects.

Design constraints, mirrored from
``governance/authorizations/2026-05-12_p2-04.md``:

- No trading, broker, order, market-data, persistence, scheduler, or
  daemon logic.
- No env-var reads, no filesystem I/O, no network calls, no external sinks.
- Output is plain data (an :class:`AuditEvent` record) and deterministic
  JSON text. Callers integrate with the standard Python ``logging``
  framework themselves; this module does not call ``logging.basicConfig``,
  install handlers, or otherwise mutate global state.
- Timestamps come from :mod:`gmc_rebuild.time` so ADR-004's UTC discipline
  is enforced at the audit boundary.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Final

from gmc_rebuild.time import ensure_utc, format_utc, now_utc

AuditCategory = str

AUDIT_CATEGORIES: Final[frozenset[AuditCategory]] = frozenset(
    {
        "governance",
        "config",
        "lifecycle",
    }
)

REDACTED_PLACEHOLDER: Final[str] = "[REDACTED]"

_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")

_REDACT_KEY_TOKENS: Final[frozenset[str]] = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "private_key",
        "credential",
        "credentials",
        "authorization",
        "auth",
    }
)


class AuditEventError(ValueError):
    """Raised when an audit-event construction violates the conventions.

    Subclass of ``ValueError`` so callers can catch it alongside other
    bad-input cases while still distinguishing audit-shape violations by
    type.
    """


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Immutable structured audit record.

    Fields:

    - ``timestamp``: ISO-8601 UTC string with the ``Z`` suffix (ADR-004).
    - ``category``: one of :data:`AUDIT_CATEGORIES`.
    - ``name``: dotted lowercase identifier (``category.action``), e.g.
      ``governance.authorization_granted``.
    - ``message``: short human-readable description; no secrets, no PII.
    - ``fields``: read-only mapping of structured key/value detail.
      Values must be JSON-serializable primitives (``str``, ``int``,
      ``float``, ``bool``, ``None``) or nested ``dict``/``list`` of the
      same. Keys whose lowercased name contains a redaction token are
      replaced with :data:`REDACTED_PLACEHOLDER`.
    """

    timestamp: str
    category: AuditCategory
    name: str
    message: str
    fields: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


def _validate_name(name: str) -> None:
    if not isinstance(name, str):
        raise AuditEventError(f"audit event name must be a str, got {type(name).__name__}")
    if not _NAME_PATTERN.fullmatch(name):
        raise AuditEventError(
            f"audit event name {name!r} must be a dotted lowercase identifier "
            "of the form '<category>.<action>' using [a-z0-9_] tokens"
        )


def _validate_category(category: AuditCategory, name: str) -> None:
    if category not in AUDIT_CATEGORIES:
        allowed = ", ".join(sorted(AUDIT_CATEGORIES))
        raise AuditEventError(f"audit event category {category!r} is not one of: {allowed}")
    prefix = name.split(".", 1)[0]
    if prefix != category:
        raise AuditEventError(
            f"audit event name {name!r} must start with the category "
            f"{category!r} (got prefix {prefix!r})"
        )


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in _REDACT_KEY_TOKENS)


def _normalize_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return _normalize_fields(value)
    if isinstance(value, (list, tuple)):
        return [_normalize_value(item) for item in value]
    raise AuditEventError(
        f"audit event field value of type {type(value).__name__!s} is not "
        "JSON-serializable; allowed: None, bool, int, float, str, dict, list"
    )


def _normalize_fields(fields: Mapping[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in fields.items():
        if not isinstance(key, str):
            raise AuditEventError(f"audit event field keys must be str, got {type(key).__name__}")
        if _is_sensitive_key(key):
            normalized[key] = REDACTED_PLACEHOLDER
            continue
        normalized[key] = _normalize_value(value)
    return normalized


def audit_event(
    category: AuditCategory,
    name: str,
    message: str,
    *,
    fields: Mapping[str, Any] | None = None,
    timestamp: datetime | None = None,
) -> AuditEvent:
    """Construct an :class:`AuditEvent` with validation and redaction.

    Validates ``category`` against :data:`AUDIT_CATEGORIES`, requires
    ``name`` to follow the ``<category>.<action>`` convention, copies
    ``fields`` into an immutable mapping with sensitive keys replaced by
    :data:`REDACTED_PLACEHOLDER`, and formats ``timestamp`` (or the
    current UTC time) via :mod:`gmc_rebuild.time`.

    All inputs are validated; invalid categories, names, field keys, or
    field-value types raise :class:`AuditEventError`. Naive datetimes
    propagate :class:`gmc_rebuild.time.NaiveDatetimeError` from
    :func:`gmc_rebuild.time.ensure_utc`.
    """
    if not isinstance(message, str):
        raise AuditEventError(f"audit event message must be a str, got {type(message).__name__}")
    _validate_name(name)
    _validate_category(category, name)
    when = ensure_utc(timestamp) if timestamp is not None else now_utc()
    normalized = _normalize_fields(fields) if fields is not None else {}
    return AuditEvent(
        timestamp=format_utc(when),
        category=category,
        name=name,
        message=message,
        fields=MappingProxyType(normalized),
    )


def serialize_event(event: AuditEvent) -> str:
    """Serialize an :class:`AuditEvent` to deterministic JSON.

    All mapping keys (top-level and nested) are emitted in sorted order
    using compact separators, so the same logical event always produces
    the same string — important for audit-log diffability and
    golden-file tests.
    """
    payload: dict[str, Any] = {
        "timestamp": event.timestamp,
        "category": event.category,
        "name": event.name,
        "message": event.message,
        "fields": _to_plain(event.fields),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _to_plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _to_plain(value[key]) for key in value}
    if isinstance(value, list):
        return [_to_plain(item) for item in value]
    return value
