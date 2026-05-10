# ADR-001: Secrets Management Strategy

**Status**: Accepted

**Date**: 2026-05-10 (UTC)

**Participants**: Kevin Heaney

---

## Problem Statement

Credentials for Interactive Brokers (IB API token), Coinbase Advanced Trade API, and Vault server itself must be loaded at runtime without being committed to Git or stored in plaintext on disk.

---

## Decision

**Use HashiCorp Vault** as the secrets management system for all credentials (IB token, Coinbase keys, Vault auth token).

---

## Implementation Details

Vault runs on Mac Studio with auth via GitHub token. Credentials stored under `/secret/ib/token`, `/secret/coinbase/key`, etc. Rotation policy: Every 90 days, auto-rotates and alerts Kevin.

### Dry-Run Mode (Phase 2)
- `gmc-rebuild/config_example.py` includes fake credentials
- Dry-run uses local config; doesn't connect to Vault
- Tests can mock Vault client

### Live Mode (Phase 3)
- Vault required; must be running before trading starts
- If Vault unavailable > 30 sec, system auto-stops (kill switch triggers)

---

## Rationale

Chosen Vault because:
1. Audit trail: Essential for post-incident forensics
2. Rotation built-in: Removes manual credential refresh
3. Free open-source: No cost, professional-grade
4. Local or cloud-hosted: Can run on Mac Studio

---

## Follow-Up Actions

| Action | Timeline |
|--------|----------|
| Vault installation & init | Phase 2 start |
| GitHub auth method setup | Phase 2 start |
| Credential migration (IB, CB) | Phase 2 start |
| Daily Vault health check | Phase 2+ |

---

## Approval

**Decision Made By**: Kevin Heaney (2026-05-10)  
**Status**: Accepted  
**Implementation**: Phase 2
