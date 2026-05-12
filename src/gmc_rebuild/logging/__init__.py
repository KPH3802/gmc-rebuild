"""gmc_rebuild.logging — structured logging and audit event conventions (P2-04).

This subpackage is authorized by PR P2-04 (see
``governance/authorizations/2026-05-12_p2-04.md`` and
``plan/phase2_entry_plan.md`` §4). It defines the canonical structured
log-record shape and the ``audit_event`` helper that produces deterministic,
redaction-aware audit records.

P2-04 deliberately does **not** introduce:

- broker, account, order, or execution logic,
- strategy, signal, scanner, or model code,
- market-data ingestion,
- persistence, database writes, or on-disk audit log files,
- schedulers, background jobs, daemons, or any ``__main__`` entry point,
- env-var or secrets loading inside this submodule,
- external log sinks (syslog, journald, cloud, HTTP, message brokers),
- expansion into P2-05 or later Phase 2 items.

See ``MASTER_STATUS.md`` §6, §7, and §8 for the phase-boundary controls
that continue to apply.
"""

from __future__ import annotations

from gmc_rebuild.logging.audit import (
    AUDIT_CATEGORIES,
    REDACTED_PLACEHOLDER,
    AuditCategory,
    AuditEvent,
    AuditEventError,
    audit_event,
    serialize_event,
)

__all__ = [
    "AUDIT_CATEGORIES",
    "REDACTED_PLACEHOLDER",
    "AuditCategory",
    "AuditEvent",
    "AuditEventError",
    "audit_event",
    "serialize_event",
]
