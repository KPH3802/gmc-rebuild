# ADR-001: Secrets Management Strategy

## Status

Accepted

## Date

2026-05-10 UTC

## Context / Problem

The rebuild will eventually need credentials for broker APIs, market data services, and operational tooling. Phase 1 must define how secrets are handled before any Phase 2 implementation starts. Secrets must not be committed, stored in plaintext project files, copied into review artifacts, or embedded in examples.

## Decision

Use HashiCorp Vault as the system of record for runtime secrets once Phase 2 begins. The repository may contain only fake example values and documentation placeholders. Local `.env` files, private keys, certificates, database files, and generated credential material are ignored by Git.

## Alternatives Considered

- Local `.env` files only: simple, but weak auditability and easy to leak.
- macOS Keychain only: useful locally, but less portable for daemon and deployment workflows.
- Cloud provider secret manager: viable later, but unnecessary for a local Phase 2 governance baseline.

## Consequences

- Positive: Centralized secret storage, rotation policy, and audit trail are available before live operations.
- Positive: Git history remains clean of runtime credentials.
- Negative: Vault adds local setup work at Phase 2 entry.
- Risk: If Vault is unavailable, runtime components must fail closed rather than trade with missing credentials.

## Implementation Notes

- Phase 1 contains no real secrets and no broker execution code.
- Phase 2 may add fake `config.example` material only if values are clearly non-sensitive.
- Runtime code must read secrets from Vault or injected test doubles, never from committed files.
- Secret scanning is enforced through pre-commit.

## Follow-up Actions

- Install and initialize Vault during Phase 2 setup.
- Document Vault paths for each required credential before credentials are loaded.
- Add tests proving missing secrets fail closed when runtime code exists.

## Related ADRs

- ADR-007: Minimal CI Strategy
