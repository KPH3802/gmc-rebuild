# MASTER STATUS

**Read this document first at the start of every serious work session.** It is the canonical, single source of truth for the current state of `gmc-rebuild`. If anything in another document conflicts with this file, this file wins until it is updated.

**Last updated:** 2026-05-11 UTC (P2-01 package skeleton authorized)
**Maintained by:** Perplexity Computer (supervisor / status keeper), approved by Kevin

---

## 1. Current Phase

**Phase 2 — Infrastructure foundation, narrowly opened at P2-01.**

Phase 1 (governance cleanup) was accepted per `1f101fc` (see §3). Phase 2 is **partially open**: Kevin has authorized PR P2-01 (package skeleton and test harness), which creates the importable `src/gmc_rebuild/` layout with no runtime behavior. See `plan/phase2_entry_plan.md` §4 for the full P2-01..P2-05 sequence; only P2-01 is open. P2-02 and beyond require separate written authorization.

The repository still contains no trading strategy code, no broker execution code, no live trading workflow, no runtime daemon, no market data ingestion, and no real secrets or account identifiers. Each future Phase 2 PR is authorized individually and must satisfy the proof bundle in `plan/phase2_entry_plan.md` §6.

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

## 3. Baseline

**Accepted Phase 1 baseline:** `1f101fc` (`docs: fix Phase 1 verification blockers`).

The accepted Phase 1 baseline is `1f101fc`, established by Kevin's written acceptance note on PR #3. That note is itself the audit-visible record (GitHub PR-comment history); it supersedes earlier candidate baselines. Any session on the default branch should start from `1f101fc` or a descendant of it. The current `main` head is a descendant of `1f101fc` (see §8 step 3 for the verification command).

This section deliberately does not require `MASTER_STATUS.md` to name the merge commit that lands a given PR as a "new baseline" — that recursion is unnecessary. The accepted Phase 1 baseline (`1f101fc`) is fixed; subsequent work lives as descendants of it.

### Candidate-baseline history

- **`ee3457f`** — earlier candidate during Phase 1 cleanup. Superseded.
- **`b39d036`** — candidate baseline proposed for external verification per `EXTERNAL_REVIEW_BRIEF.md` and `docs/decisions/PHASE_1_COMPLETION_SUMMARY.md`. Superseded by `1f101fc` when Kevin accepted Phase 1 on PR #3; not the accepted baseline.
- **`1f101fc`** — accepted Phase 1 baseline (current).

`EXTERNAL_REVIEW_BRIEF.md` and `docs/decisions/PHASE_1_COMPLETION_SUMMARY.md` still reference `b39d036` because they are point-in-time review artifacts from the Phase 1 verification request, not live state. They should not be read as overriding this section.

### P2-01 authorization is separate from the baseline

Kevin's written authorization for PR P2-01 (package skeleton and test harness, see `plan/phase2_entry_plan.md` §4) is recorded in §1, §5, §7, and §8. P2-01 does not change the accepted Phase 1 baseline; it opens Phase 2 implementation narrowly on top of that baseline. Any future change to the accepted Phase 1 baseline must be recorded audit-visibly — in this section and in the PR that lands it — and must not silently substitute a different baseline (`AI_WORKFLOW.md` §3 covers the proof-bundle requirements that make this enforceable).

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

## 5. What Phase 1 (and the P2-01 Skeleton) Contains

The repository contains, and only contains:

- Governance documents (`MASTER_STATUS.md`, `AI_WORKFLOW.md`, `README.md`, `plan/rebuild_plan.md`).
- Verification-facing documents: `EXTERNAL_REVIEW_BRIEF.md` (the request) and `docs/decisions/PHASE_1_COMPLETION_SUMMARY.md` (the submission).
- Accepted architecture decision records under `docs/decisions/ADR-*.md`.
- Templates for ADRs, deployment logs, daily monitoring reports, and review requests.
- Project configuration: `pyproject.toml`, `.pre-commit-config.yaml`, `.gitignore`, `.secrets.baseline`.
- Phase 1 governance placeholder tests and the P2-01 skeleton tests under `tests/`.
- The P2-01 package skeleton at `src/gmc_rebuild/`: an empty importable package with `__init__.py`, a `__version__` string, and a `py.typed` marker. No submodules, no runtime behavior.

---

## 6. What Is Explicitly Not Present

The repository contains **none** of the following. If any of these appear in a diff, the change is out of scope and must be rejected at review.

Always-forbidden (no current authorization, regardless of phase):

- Trading strategy code (signals, scanners, models, portfolio rules, backtests).
- Broker execution code (order placement, position management, broker SDK integration).
- Live trading workflows or paper-trading workflows wired to a real broker.
- Runtime daemons, schedulers, long-running services, or background workers that touch accounts, markets, or money.
- Market data ingestion code, real data pipelines, or stored datasets.
- Secrets, private keys, certificates, `.env` files, local databases, or generated reports.

Phase 2 implementation is forbidden **except** for tasks named in an accepted Phase 2 PR and recorded on the §8 step 4a allowlist. At the time of writing, the only authorized Phase 2 implementation task is:

- **PR P2-01 — package skeleton and test harness.** Authorizes the importable `src/gmc_rebuild/` layout, the corresponding pytest fixtures under `tests/`, and the minimal `pyproject.toml` package-discovery wiring. Does not authorize submodules, runtime behavior, or any of the always-forbidden categories above.

P2-02..P2-05 in `plan/phase2_entry_plan.md` §4 are **not** authorized and remain forbidden until Kevin records explicit written authorization per `MASTER_STATUS.md` §7 and `AI_WORKFLOW.md` §6 rule 3 ("One approver") / rule 7 ("No phase drift"). A PR that introduces work outside the §8 step 4a allowlist must be rejected at review.

---

## 7. Phase 2 Boundary

Phase 1 was accepted by Kevin in writing on PR #3 against `1f101fc` (see §3). Phase 2 implementation is **partially open** under the following conditions, which have already been recorded:

1. Accepted Phase 1 baseline established at `1f101fc` and recorded in §3.
2. `plan/phase2_entry_plan.md` merged on `main` (commit `04faaa1`) and referenced from `README.md`.
3. `MASTER_STATUS.md` §8 reconciled to distinguish always-forbidden categories (step 4) from a per-PR Phase 2 infrastructure allowlist (step 4a). The reconciliation landed in commit `5c84d85` ("docs: reconcile MASTER_STATUS startup checks").
4. Kevin's explicit written authorization for PR P2-01 (package skeleton and test harness, per `plan/phase2_entry_plan.md` §4). P2-01 is the only Phase 2 implementation task authorized at this time.

What this means in practice:

- The §8 step 4a allowlist currently contains exactly `src/`, authorizing P2-01's importable `src/gmc_rebuild/` skeleton and nothing else.
- P2-02..P2-05 in `plan/phase2_entry_plan.md` §4 are **not** authorized. Each requires its own written authorization from Kevin per `AI_WORKFLOW.md` §6 rule 3 ("One approver") and rule 7 ("No phase drift"), and a corresponding update to the §8 step 4a allowlist in the PR that introduces the directory.
- The always-forbidden categories in §6 and `plan/phase2_entry_plan.md` §2 remain forbidden regardless of mode. Authorizing P2-01 does not authorize any Phase 3+ behavior.
- Any pull request that introduces strategy logic, broker integration, live or paper trading wired to a real broker, runtime daemons affecting accounts, real market data ingestion, order placement, or real secrets must be closed without merge, even if it is presented as "Phase 2 infrastructure."

The proof bundle required for every Phase 2 PR is defined in `plan/phase2_entry_plan.md` §6.

---

## 8. Required Startup Verification Commands

Run these in order at the start of every serious work session. Do not skip steps. Stop at the first failure and resolve it before continuing.

The boundary check in step 4 distinguishes two modes. Phase 2 implementation is **partially open** at the time of writing: Kevin has authorized PR P2-01 (package skeleton and test harness) per `plan/phase2_entry_plan.md` §4, which names `src/` as the authorized Phase 2 infrastructure directory. Step 4a below therefore runs in Phase 2 implementation mode restricted to that allowlist. The Phase 2 implementation mode applies only to directories named in an accepted Phase 2 task or PR; any other Phase 2 infrastructure path is STOP. Switching modes does not silently relax controls: forbidden categories (strategy, broker execution, live or paper trading wired to a real broker, runtime daemons affecting accounts, real market data ingestion, order placement, secrets) remain STOP unless and until a later gate specifically authorizes them.

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

# 4a. Phase 2 implementation mode — restricted to directories authorized by an
#     accepted Phase 2 task or PR. The allowlist below is exactly the set of
#     Phase 2 infrastructure paths Kevin has authorized in writing:
#       - src/  → authorized by PR P2-01 (package skeleton and test harness),
#                 see plan/phase2_entry_plan.md §4.
#     A Phase 2 infrastructure path present but not on this allowlist is STOP;
#     reconcile before continuing. The always-forbidden categories in step 4
#     still apply unchanged in this mode.
allowed_p2_infra="src"
unset p2_infra_found
for path in src; do
  if [ -e "$path" ]; then
    case " $allowed_p2_infra " in
      *" $path "*)
        echo "OK: Phase 2 infrastructure present and authorized: $path (PR P2-01)"
        ;;
      *)
        echo "STOP: Phase 2 infrastructure present but not authorized: $path (see plan/phase2_entry_plan.md)"
        p2_infra_found=1
        ;;
    esac
  fi
done
[ "${p2_infra_found:-0}" -eq 0 ] && echo "OK: Phase 2 infrastructure paths conform to P2-01 allowlist"

# 4b. Phase 2 implementation mode is operating under the P2-01 allowlist in
#     step 4a. To extend the allowlist for a future Phase 2 PR (e.g. P2-02,
#     P2-03, …), update the `allowed_p2_infra` variable above in the same PR
#     that adds the new directory, and reference the authorizing PR number in
#     the comment block. Step 4 (always-forbidden categories) still applies in
#     this mode; switching modes never relaxes those categories.

# 5. Confirm tooling is installed and matches committed versions
python --version          # expect Python 3.12.x
pre-commit --version

# 6. Run the full quality gate
pre-commit run --all-files

# 7. Run tests
pytest
```

If any step fails, document the failure in the session log and stop. Do not "fix" by widening scope. In particular, do not extend the `allowed_p2_infra` allowlist in step 4a without Kevin's explicit written authorization per §7 and a specific accepted Phase 2 task or PR that names the directory; per `AI_WORKFLOW.md` §6 rule 3 ("One approver") and rule 7 ("No phase drift"), the phase boundary cannot be moved by Codex or Perplexity Computer alone, and per rule 8, tooling hooks (pre-commit, mypy strict, detect-secrets) may not be weakened to make a failure go away. The only directory currently on the allowlist is `src/` under PR P2-01 — see `plan/phase2_entry_plan.md` for the full P2-01..P2-05 sequence and the Phase 2 entry criteria.

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
