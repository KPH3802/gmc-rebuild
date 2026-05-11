# MASTER STATUS

**Read this document first at the start of every serious work session.** It is the canonical, single source of truth for the current state of `gmc-rebuild`. If anything in another document conflicts with this file, this file wins until it is updated.

**Last updated:** 2026-05-11 UTC
**Maintained by:** Perplexity Computer (supervisor / status keeper), approved by Kevin

---

## 1. Current Phase

**Phase 1 — Governance cleanup only.**

Phase 1 covers planning, architecture decisions, templates, project configuration, verification tooling, and the governance workflow itself. Phase 1 is documentation and tooling only. No runtime trading behavior exists in this repository.

Phase 2 has **not** started. Phase 2 may begin only after:

1. Phase 1 passes external verification.
2. Kevin explicitly authorizes Phase 2 in writing (commit message, PR comment, or governance entry).
3. The first Phase 2 task is infrastructure-only unless Kevin approves a narrower implementation plan.

---

## 2. Source of Truth

The authoritative artifacts, in priority order:

1. `MASTER_STATUS.md` — this file. Current phase, boundary, verification commands, allowed next decisions.
2. `AI_WORKFLOW.md` — separation of duties between Codex, Perplexity Computer, Kevin, and the optional backup AI.
3. `plan/rebuild_plan.md` — the canonical rebuild plan and the 12 governance invariants.
4. `README.md` — operating overview, setup, phase gates, safety rules.
5. `docs/decisions/ADR-*.md` — accepted architecture decision records.
6. `EXTERNAL_REVIEW_BRIEF.md` — scope and checklist for independent Phase 1 verification.

Anything not in this list is supporting material, not source of truth. If a conflict appears, escalate to Kevin before changing behavior.

---

## 3. Verified Baseline

**Verified baseline commit:** `ee3457f` (`docs: normalize governance template whitespace`).

This is the last commit verified to satisfy Phase 1 exit criteria as documented in `README.md` and `EXTERNAL_REVIEW_BRIEF.md`. Any work session should start from this commit or a descendant of it on the default branch. If `HEAD` is not a descendant of `ee3457f`, stop and reconcile before doing further work.

---

## 4. Machine Setup

The repository is worked on from two machines. Both must point at the same remote and the same default branch.

| Machine | Path |
| --- | --- |
| MacBook Pro | `~/gmc-rebuild` |
| Mac Studio | `/Users/kevinheaney/gmc-rebuild` |

Rules:

- Never work on both machines simultaneously on the same branch.
- Before starting a session, `git fetch` and confirm the local branch matches the remote.
- Never commit machine-local files, virtual environments, caches, secrets, local databases, logs, or generated data. `.gitignore` enforces this; do not bypass it.
- Python 3.12 is the required interpreter on both machines. If `python3.12` is not the default, install it and use the explicit executable.

---

## 5. What Phase 1 Contains

Phase 1 is intentionally narrow. The repository contains, and only contains:

- Governance documents (`MASTER_STATUS.md`, `AI_WORKFLOW.md`, `README.md`, `plan/rebuild_plan.md`, `EXTERNAL_REVIEW_BRIEF.md`).
- Accepted architecture decision records under `docs/decisions/ADR-*.md`.
- Templates for ADRs, deployment logs, daily monitoring reports, and review requests.
- Project configuration: `pyproject.toml`, `.pre-commit-config.yaml`, `.gitignore`, `.secrets.baseline`.
- Phase 1 governance placeholder tests under `tests/`.

---

## 6. What Is Explicitly Not Present

Phase 1 contains **none** of the following. If any of these appear in a diff, the change is out of scope and must be rejected at review.

- Trading strategy code (signals, scanners, models, portfolio rules, backtests).
- Broker execution code (order placement, position management, broker SDK integration).
- Live trading workflows or paper-trading workflows wired to a broker.
- Runtime daemons, schedulers, long-running services, or background workers.
- Market data ingestion code, data pipelines, or stored datasets.
- Phase 2 implementation of any kind.
- Secrets, private keys, certificates, `.env` files, local databases, or generated reports.

---

## 7. Phase 2 Boundary

The line between Phase 1 and Phase 2 is hard. Phase 2 begins only when **all** of the following are true:

1. Phase 1 external verification is complete and accepted by Kevin.
2. No unresolved blocker remains in ADRs, templates, README, tooling, or repo hygiene.
3. Kevin authorizes Phase 2 explicitly (commit message, PR comment, or governance entry, not a chat message).
4. The first Phase 2 change is infrastructure-only — interfaces, types, configuration, scaffolding — unless Kevin pre-approves a narrower implementation plan.

Until those conditions are met, any pull request that introduces strategy logic, broker integration, runtime daemons, or live trading behavior must be closed without merge.

---

## 8. Required Startup Verification Commands

Run these in order at the start of every serious work session. Do not skip steps. Stop at the first failure and resolve it before continuing.

```bash
# 1. Confirm working tree state
git status

# 2. Confirm branch and recent history
git log --oneline -10
git rev-parse HEAD

# 3. Confirm you are on or descended from the verified baseline
git merge-base --is-ancestor ee3457f HEAD && echo "OK: descended from ee3457f" || echo "STOP: not descended from ee3457f"

# 4. Confirm Phase 1 boundary is intact (no forbidden directories)
ls src/ strategies/ broker/ execution/ live/ daemons/ 2>/dev/null && echo "STOP: forbidden Phase 2 directories present" || echo "OK: no forbidden directories"

# 5. Confirm tooling is installed and matches committed versions
python --version          # expect Python 3.12.x
pre-commit --version

# 6. Run the full quality gate
pre-commit run --all-files

# 7. Run tests
pytest
```

If any step fails, document the failure in the session log and stop. Do not "fix" by widening scope.

---

## 9. Next Allowed Decisions

Only the following decisions are in scope right now. Any other change requires Kevin's explicit approval.

1. Editing or extending governance documentation: `MASTER_STATUS.md`, `AI_WORKFLOW.md`, `README.md`, `plan/rebuild_plan.md`, `EXTERNAL_REVIEW_BRIEF.md`.
2. Editing or extending ADRs and the four templates under `docs/` and adjacent directories, in line with the existing structure.
3. Fixing documented blockers raised by external verification, scoped to Phase 1 only.
4. Repository hygiene: `.gitignore`, `.pre-commit-config.yaml`, `pyproject.toml`, `.secrets.baseline`, where the change strictly preserves Phase 1 invariants.
5. Updating Phase 1 placeholder tests in `tests/` so they continue to verify governance artifacts, not behavior.
6. Recording Kevin's decision to open Phase 2 — and only then planning the first Phase 2 infrastructure-only change.

Decisions that are **not** allowed without a new approval from Kevin:

- Starting Phase 2 work.
- Adding any code path that touches market data, signals, orders, brokers, or accounts.
- Adding runtime services, schedulers, or long-running processes.
- Relaxing pre-commit, mypy strict mode, or detect-secrets.
- Loosening `.gitignore` to allow secrets, data, or generated state.
