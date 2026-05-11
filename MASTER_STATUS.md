# MASTER STATUS

**Read this document first at the start of every serious work session.** It is the canonical, single source of truth for the current state of `gmc-rebuild`. If anything in another document conflicts with this file, this file wins until it is updated.

**Last updated:** 2026-05-11 UTC
**Maintained by:** Perplexity Computer (supervisor / status keeper), approved by Kevin

---

## 1. Current Phase

**Phase 1 — Governance cleanup only.**

Phase 1 covers planning, architecture decisions, templates, project configuration, verification tooling, and the governance workflow itself. Phase 1 is documentation and tooling only. No runtime trading behavior exists in this repository.

Phase 2 has **not** started, and Phase 1 has **not** yet been externally verified. Phase 2 may begin only after:

1. Phase 1 is externally verified against the candidate baseline (see §3) and Kevin accepts the verification report in writing.
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
6. `EXTERNAL_REVIEW_BRIEF.md` — scope and checklist for independent Phase 1 verification (the request side of the gate).
7. `docs/decisions/PHASE_1_COMPLETION_SUMMARY.md` — Phase 1 cleanup summary listing the artifacts presented for review (the submission side of the gate).

Anything not in this list is supporting material, not source of truth. If a conflict appears, escalate to Kevin before changing behavior.

---

## 3. Candidate Baseline

**Candidate Phase 1 baseline:** `b39d036` (`docs: add AI governance control docs`).

This is the commit currently proposed for external verification per `EXTERNAL_REVIEW_BRIEF.md` and summarized in `docs/decisions/PHASE_1_COMPLETION_SUMMARY.md`. It is the current `main` head after the governance documents (`MASTER_STATUS.md` and `AI_WORKFLOW.md`) landed, and it supersedes the prior candidate `ee3457f` because those two governance documents are now part of the artifact set under review. Recording the promotion from `ee3457f` to `b39d036` in this file is what makes the change auditable; per `AI_WORKFLOW.md` §3.1 and §6 rule 2, the candidate baseline may not be silently substituted, and any future change of the candidate baseline must be recorded the same way (in this section and in the PR that lands it).

`b39d036` has passed local quality gates (`pre-commit run --all-files` and `pytest`) and is the basis for the verification request, but it is **not** yet externally verified and has not yet been accepted by Kevin against an external verification report.

The Phase 1 status today is "Ready for external verification," not "verified." `b39d036` becomes the **accepted Phase 1 baseline** only after:

1. An external verification report is produced against this exact commit hash, and
2. Kevin records acceptance of that report in writing (commit message, PR comment, or governance entry).

Until those two conditions are met, `b39d036` is a *candidate* / *locally verified candidate* baseline only. The term "verified baseline" is reserved for use after Kevin has accepted an external verification report in writing; it is not applied to any commit before that point.

Any work session should start from `b39d036` or a descendant of it on the default branch. If `HEAD` is not a descendant of `b39d036`, stop and reconcile before doing further work.

---

## 4. Machine Setup

The repository is worked on from two machines. These are the current known checkout paths; the canonical reference is "the home-directory checkout on each machine," and the literal paths below are recorded for convenience, not as a constraint. If a machine's path changes, update this section.

| Machine | Current known checkout path |
| --- | --- |
| MacBook Pro | `~/gmc-rebuild` |
| Mac Studio | `~/gmc-rebuild` (i.e. `/Users/<kevin's user>/gmc-rebuild`) |

Rules:

- Never work on both machines simultaneously on the same branch.
- Before starting a session, `git fetch` and confirm the local branch matches the remote.
- Never commit machine-local files, virtual environments, caches, secrets, local databases, logs, or generated data. `.gitignore` enforces this; do not bypass it.
- Python 3.12 is the required interpreter on both machines. If `python3.12` is not the default, install it and use the explicit executable.

---

## 5. What Phase 1 Contains

Phase 1 is intentionally narrow. The repository contains, and only contains:

- Governance documents (`MASTER_STATUS.md`, `AI_WORKFLOW.md`, `README.md`, `plan/rebuild_plan.md`).
- Verification-facing documents: `EXTERNAL_REVIEW_BRIEF.md` (the request) and `docs/decisions/PHASE_1_COMPLETION_SUMMARY.md` (the submission).
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

The line between Phase 1 and Phase 2 is hard. Phase 1 external verification has **not** yet occurred — the repository is in the "Ready for external verification" state per `EXTERNAL_REVIEW_BRIEF.md` and `docs/decisions/PHASE_1_COMPLETION_SUMMARY.md`. Phase 2 begins only when **all** of the following future events have occurred:

1. An external verification report is produced against the candidate baseline (§3) and accepted by Kevin in writing.
2. No unresolved blocker remains in ADRs, templates, README, tooling, or repo hygiene.
3. Kevin authorizes Phase 2 explicitly (commit message, PR comment, or governance entry, not a chat message).
4. The first Phase 2 change is infrastructure-only — interfaces, types, configuration, scaffolding — unless Kevin pre-approves a narrower implementation plan.

Until those conditions are met, any pull request that introduces strategy logic, broker integration, runtime daemons, or live trading behavior must be closed without merge.

---

## 8. Required Startup Verification Commands

Run these in order at the start of every serious work session. Do not skip steps. Stop at the first failure and resolve it before continuing.

The boundary check in step 4 distinguishes two modes. Phase 2 implementation is **not yet open** at the time of writing — see `plan/phase2_entry_plan.md` §1, §5 for the criteria — so the default mode is Phase 1 / pre-Phase-2-implementation. The Phase 2 implementation mode applies only after Kevin has authorized Phase 2 in writing per §7 and the specific infrastructure directory has been named in an accepted Phase 2 task or PR. Switching modes does not silently relax controls: forbidden categories (strategy, broker execution, live or paper trading wired to a real broker, runtime daemons affecting accounts, real market data ingestion, order placement, secrets) remain STOP in both modes unless and until a later gate specifically authorizes them.

```bash
# 1. Confirm working tree state
git status

# 2. Confirm branch and recent history
git log --oneline -10
git rev-parse HEAD

# 3. Confirm you are on or descended from the accepted Phase 1 baseline
#    Accepted Phase 1 baseline: 1f101fc (per Kevin's written acceptance on PR #3;
#    supersedes the candidate b39d036 noted in §3). Current main descendant at
#    time of writing: 04faaa1 (plan: add Phase 2 entry plan).
git merge-base --is-ancestor 1f101fc HEAD && echo "OK: descended from 1f101fc" || echo "STOP: not descended from accepted Phase 1 baseline 1f101fc"

# 4. Confirm the Phase 1 / Phase 2 boundary is intact.
#    Always-forbidden categories (STOP in both modes unless a later, specific
#    gate authorizes them): strategy, signals, scanners, models, portfolio,
#    backtests, broker, execution, live, paper trading wired to a real broker,
#    runtime daemons affecting accounts, real market data ingestion, order
#    placement, secrets. These names are illustrative; the categories apply
#    regardless of where the code is placed. The loop below reports each
#    forbidden path individually and matches both files and directories, so a
#    single forbidden entry (e.g. an `orders/` directory or a `secrets` file)
#    cannot hide behind sibling missing paths the way it could with a
#    multi-arg `ls`.
unset found
for path in strategy strategies signal signals scanner scanners model models \
            portfolio backtest backtests broker execution live paper daemons \
            data market_data orders secrets; do
  if [ -e "$path" ]; then
    echo "STOP: always-forbidden category present: $path"
    found=1
  fi
done
[ "${found:-0}" -eq 0 ] && echo "OK: no always-forbidden category paths"

# 4a. Phase 1 / pre-Phase-2-implementation mode (current default).
#     In this mode, Phase 2 infrastructure directories such as src/ are also
#     STOP, because Phase 2 implementation is not yet open. See
#     plan/phase2_entry_plan.md §1, §4 (P2-01), §5 for the future sequence.
#     Same per-path style as step 4 for consistency.
unset p2_infra_found
for path in src; do
  if [ -e "$path" ]; then
    echo "STOP: Phase 2 infrastructure present but Phase 2 implementation is not open: $path (see plan/phase2_entry_plan.md)"
    p2_infra_found=1
  fi
done
[ "${p2_infra_found:-0}" -eq 0 ] && echo "OK: no Phase 2 infrastructure paths (pre-Phase-2-implementation mode)"

# 4b. Phase 2 implementation mode (only after Kevin's explicit written
#     authorization per §7 and a specific accepted Phase 2 task/PR that names
#     the directory). In this mode, step 4a is replaced by a check that any
#     Phase 2 infrastructure directory present is documented in an accepted
#     Phase 2 task or PR (e.g. src/ under PR P2-01 per
#     plan/phase2_entry_plan.md §4). If a directory exists that is not
#     documented in such a task or PR, treat it as STOP and reconcile before
#     continuing. Step 4 (always-forbidden categories) still applies in this
#     mode; switching modes never relaxes those categories.

# 5. Confirm tooling is installed and matches committed versions
python --version          # expect Python 3.12.x
pre-commit --version

# 6. Run the full quality gate
pre-commit run --all-files

# 7. Run tests
pytest
```

If any step fails, document the failure in the session log and stop. Do not "fix" by widening scope. In particular, do not switch from Phase 1 / pre-Phase-2-implementation mode (step 4a) to Phase 2 implementation mode (step 4b) without Kevin's explicit written authorization per §7 and a specific accepted Phase 2 task or PR that names the directory; per `AI_WORKFLOW.md` §6 rule 8, controls may not be silently relaxed. Phase 2 implementation is not open at the time of writing — see `plan/phase2_entry_plan.md` for the P2-01 sequence and the Phase 2 entry criteria.

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
