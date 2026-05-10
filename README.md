# gmc-rebuild

Disciplined rebuild of Grist Mill Capital's event-driven equity autotrader.

## Phase: Governance Setup

Plan-first, code-later. Rebuild plan established; governance controls being made enforceable before trading logic.

## Key Decisions

1. Secrets: HashiCorp Vault
2. Kill Switch: SQLite database
3. Reconciliation: Hourly auto-daemon
4. Timestamps: Strict UTC only
5. Operator Availability: Database heartbeat
6. Deployment: Template-based logs
7. CI: Pre-commit MVP (Phase 2), GitHub Actions (Phase 3+)

See docs/decisions/ADR-*.md for details.

## License

MIT
