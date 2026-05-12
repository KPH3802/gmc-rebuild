"""P2-04 structured-logging / audit-event tests.

Verifies that the ``gmc_rebuild.logging`` subpackage authorized by PR
P2-04 (see ``governance/authorizations/2026-05-12_p2-04.md`` and
``plan/phase2_entry_plan.md`` §4):

- exposes the ``audit_event``, ``serialize_event``, ``AuditEvent``,
  ``AuditEventError``, ``AUDIT_CATEGORIES``, and ``REDACTED_PLACEHOLDER``
  API;
- produces immutable records with a fixed structured shape;
- integrates with the P2-03 UTC time discipline (ADR-004);
- serializes deterministically;
- rejects invalid categories, names, and field-value types;
- redacts sensitive field keys without leaking values;
- introduces no forbidden runtime entry points.

Tests avoid ``pytest.raises`` / fixture-typed parameters so the mypy
strict pre-commit hook does not need a pytest-stub dependency. See
``tests/test_config_schema.py`` for the same pattern.
"""

from __future__ import annotations

import ast
import importlib
import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

from gmc_rebuild.logging import (
    AUDIT_CATEGORIES,
    REDACTED_PLACEHOLDER,
    AuditEvent,
    AuditEventError,
    audit_event,
    serialize_event,
)
from gmc_rebuild.time import NaiveDatetimeError


def _expect_audit_event_error(call: object, match: str) -> None:
    raised: Exception | None = None
    try:
        call()  # type: ignore[operator]
    except AuditEventError as exc:
        raised = exc
    assert isinstance(raised, AuditEventError), (
        f"expected AuditEventError matching {match!r}, got {raised!r}"
    )
    assert match in str(raised), f"AuditEventError message {str(raised)!r} missing {match!r}"


def test_logging_subpackage_imports() -> None:
    module = importlib.import_module("gmc_rebuild.logging")
    assert module is not None
    assert getattr(module, "audit_event", None) is audit_event
    assert getattr(module, "serialize_event", None) is serialize_event
    assert getattr(module, "AuditEvent", None) is AuditEvent
    assert getattr(module, "AuditEventError", None) is AuditEventError
    assert getattr(module, "AUDIT_CATEGORIES", None) is AUDIT_CATEGORIES
    assert getattr(module, "REDACTED_PLACEHOLDER", None) is REDACTED_PLACEHOLDER


def test_audit_categories_are_finite_and_lowercased() -> None:
    assert isinstance(AUDIT_CATEGORIES, frozenset)
    assert frozenset({"governance", "config", "lifecycle"}) == AUDIT_CATEGORIES
    for category in AUDIT_CATEGORIES:
        assert category.islower()
        assert category.isidentifier()


def test_audit_event_basic_shape() -> None:
    event = audit_event(
        "governance",
        "governance.authorization_granted",
        "P2-04 authorization recorded",
    )
    assert isinstance(event, AuditEvent)
    assert event.category == "governance"
    assert event.name == "governance.authorization_granted"
    assert event.message == "P2-04 authorization recorded"
    assert event.fields == {}
    assert event.timestamp.endswith("Z")


def test_audit_event_uses_supplied_utc_timestamp() -> None:
    ts = datetime(2026, 5, 12, 14, 23, 45, tzinfo=UTC)
    event = audit_event(
        "config",
        "config.loaded",
        "default config built",
        timestamp=ts,
    )
    assert event.timestamp == "2026-05-12T14:23:45Z"


def test_audit_event_normalizes_non_utc_timezones() -> None:
    eastern = timezone(timedelta(hours=-5))
    ts = datetime(2026, 5, 12, 9, 23, 45, tzinfo=eastern)
    event = audit_event(
        "lifecycle",
        "lifecycle.session_started",
        "session began",
        timestamp=ts,
    )
    assert event.timestamp == "2026-05-12T14:23:45Z"


def test_audit_event_rejects_naive_timestamp() -> None:
    naive = datetime(2026, 5, 12, 14, 23, 45)
    raised: Exception | None = None
    try:
        audit_event(
            "governance",
            "governance.authorization_granted",
            "x",
            timestamp=naive,
        )
    except NaiveDatetimeError as exc:
        raised = exc
    assert isinstance(raised, NaiveDatetimeError)


def test_audit_event_now_utc_timestamp_is_utc_z() -> None:
    """``now_utc`` must be substitutable so tests can pin time deterministically."""
    audit_mod = importlib.import_module("gmc_rebuild.logging.audit")
    module_globals = vars(audit_mod)

    fixed = datetime(2026, 5, 12, 14, 23, 45, tzinfo=UTC)
    original = module_globals["now_utc"]
    module_globals["now_utc"] = lambda: fixed
    try:
        event = audit_event("governance", "governance.granted", "x")
        assert event.timestamp == "2026-05-12T14:23:45Z"
    finally:
        module_globals["now_utc"] = original


def test_audit_event_rejects_unknown_category() -> None:
    _expect_audit_event_error(
        lambda: audit_event("strategy", "strategy.signal", "no"),
        "not one of",
    )


def test_audit_event_rejects_name_not_matching_category() -> None:
    _expect_audit_event_error(
        lambda: audit_event("governance", "config.loaded", "no"),
        "must start with the category",
    )


def test_audit_event_rejects_bare_name_without_dot() -> None:
    _expect_audit_event_error(
        lambda: audit_event("governance", "governance", "no"),
        "dotted lowercase identifier",
    )


def test_audit_event_rejects_uppercase_name() -> None:
    _expect_audit_event_error(
        lambda: audit_event("governance", "Governance.Granted", "no"),
        "dotted lowercase identifier",
    )


def test_audit_event_rejects_non_string_message() -> None:
    _expect_audit_event_error(
        lambda: audit_event("governance", "governance.granted", 123),  # type: ignore[arg-type]
        "message must be a str",
    )


def test_audit_event_rejects_non_string_field_key() -> None:
    _expect_audit_event_error(
        lambda: audit_event(
            "governance",
            "governance.granted",
            "x",
            fields={1: "v"},  # type: ignore[dict-item]
        ),
        "field keys must be str",
    )


def test_audit_event_rejects_unserializable_value() -> None:
    _expect_audit_event_error(
        lambda: audit_event(
            "governance",
            "governance.granted",
            "x",
            fields={"obj": object()},
        ),
        "JSON-serializable",
    )


def test_audit_event_accepts_nested_dict_and_list() -> None:
    event = audit_event(
        "config",
        "config.loaded",
        "x",
        fields={
            "paths": ["a", "b"],
            "nested": {"k": 1, "deep": {"v": True}},
            "n": 42,
            "missing": None,
        },
    )
    assert event.fields["paths"] == ["a", "b"]
    assert event.fields["nested"] == {"k": 1, "deep": {"v": True}}
    assert event.fields["n"] == 42
    assert event.fields["missing"] is None


def test_audit_event_redacts_sensitive_keys() -> None:
    redacted_value = "do-not-log"  # pragma: allowlist secret
    event = audit_event(
        "config",
        "config.loaded",
        "x",
        fields={
            "username": "kevin",
            "password": redacted_value,  # pragma: allowlist secret
            "API_KEY": "abc",  # pragma: allowlist secret
            "broker_token": "xyz",  # pragma: allowlist secret
            "private_key": "----",  # pragma: allowlist secret
            "credentials": {"u": "k", "p": "v"},  # pragma: allowlist secret
        },
    )
    assert event.fields["username"] == "kevin"
    assert event.fields["password"] == REDACTED_PLACEHOLDER
    assert event.fields["API_KEY"] == REDACTED_PLACEHOLDER
    assert event.fields["broker_token"] == REDACTED_PLACEHOLDER
    assert event.fields["private_key"] == REDACTED_PLACEHOLDER
    assert event.fields["credentials"] == REDACTED_PLACEHOLDER


def test_audit_event_is_immutable() -> None:
    event = audit_event("governance", "governance.granted", "x", fields={"k": 1})
    raised: Exception | None = None
    try:
        event.message = "changed"  # type: ignore[misc]
    except (AttributeError, TypeError) as exc:
        raised = exc
    assert raised is not None, "AuditEvent.message must be read-only"

    raised = None
    try:
        event.fields["k"] = 2  # type: ignore[index]
    except TypeError as exc:
        raised = exc
    assert raised is not None, "AuditEvent.fields must be a read-only mapping"


def test_serialize_event_is_deterministic_and_sorted() -> None:
    ts = datetime(2026, 5, 12, 14, 23, 45, tzinfo=UTC)
    event = audit_event(
        "config",
        "config.loaded",
        "default",
        fields={"b": 2, "a": 1, "nested": {"y": 2, "x": 1}},
        timestamp=ts,
    )
    serialized = serialize_event(event)
    assert serialized == (
        '{"category":"config",'
        '"fields":{"a":1,"b":2,"nested":{"x":1,"y":2}},'
        '"message":"default",'
        '"name":"config.loaded",'
        '"timestamp":"2026-05-12T14:23:45Z"}'
    )
    parsed = json.loads(serialized)
    assert parsed["timestamp"] == "2026-05-12T14:23:45Z"
    assert parsed["category"] == "config"
    assert parsed["name"] == "config.loaded"
    assert parsed["fields"] == {"a": 1, "b": 2, "nested": {"x": 1, "y": 2}}


def test_serialize_event_roundtrip_is_stable() -> None:
    ts = datetime(2026, 5, 12, 14, 23, 45, tzinfo=UTC)
    first = audit_event(
        "governance",
        "governance.granted",
        "x",
        fields={"who": "kevin", "secret": "redact-me"},  # pragma: allowlist secret
        timestamp=ts,
    )
    second = audit_event(
        "governance",
        "governance.granted",
        "x",
        fields={"secret": "redact-me", "who": "kevin"},  # pragma: allowlist secret
        timestamp=ts,
    )
    assert serialize_event(first) == serialize_event(second)
    payload = json.loads(serialize_event(first))
    assert payload["fields"]["secret"] == REDACTED_PLACEHOLDER


def test_logging_submodule_has_no_runtime_entry_points() -> None:
    pkg_root = Path(__file__).resolve().parents[1] / "src" / "gmc_rebuild" / "logging"
    assert pkg_root.is_dir()
    forbidden_imports = {"os", "socket", "subprocess", "threading", "asyncio"}
    forbidden_attr_chains = {("os", "environ"), ("os", "getenv")}
    for python_file in pkg_root.rglob("*.py"):
        tree = ast.parse(python_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                test = node.test
                if (
                    isinstance(test, ast.Compare)
                    and isinstance(test.left, ast.Name)
                    and test.left.id == "__name__"
                ):
                    raise AssertionError(
                        f"{python_file} must not define an `if __name__` entry point"
                    )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in forbidden_imports, (
                        f"{python_file} must not import {alias.name}"
                    )
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                root = node.module.split(".", 1)[0]
                assert root not in forbidden_imports, (
                    f"{python_file} must not import from {node.module}"
                )
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                assert (node.value.id, node.attr) not in forbidden_attr_chains, (
                    f"{python_file} must not access {node.value.id}.{node.attr}"
                )
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id != "open", (
                    f"{python_file} must not call open() for filesystem I/O"
                )


def test_logging_submodule_layout_has_no_forbidden_files() -> None:
    pkg_root = Path(__file__).resolve().parents[1] / "src" / "gmc_rebuild" / "logging"
    allowed = {"__init__.py", "audit.py"}
    present = {p.name for p in pkg_root.iterdir() if p.is_file()}
    assert present <= allowed, f"unexpected files in logging submodule: {present - allowed}"
