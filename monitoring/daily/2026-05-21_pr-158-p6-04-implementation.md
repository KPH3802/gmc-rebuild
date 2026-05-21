# Daily Monitoring Report: 2026-05-21 UTC (PR #158 — P6-04 Direction A simulated order intent extension implementation)

## Report Metadata

**Environment**: Local (governance-only repository; no runtime, no broker, no live or paper trading wired to a real broker, no market data ingestion).
**Operator**: Backup AI authors the packet text under ADR-008 Mode B (Continuous Governance Monitor) per `AI_WORKFLOW.md` §1.4; the default builder commits per `AI_WORKFLOW.md` §6 rule 1 ("One builder at a time"); Perplexity Computer verifies and oversees per `AI_WORKFLOW.md` §1.2 (Supervisor / Verifier / Status Keeper) — Perplexity Computer is not the Mode B author. Per the GOV-02 execution-environment workflow rule (merged via PR #132 / reconciled via PR #134), default-builder work on `gmc-rebuild` is by default carried out via Kevin's local Claude Code / Claude Max subscription; this packet is built in compliance with that rule.
**Report Window**: 2026-05-21T00:00:00Z to 2026-05-21T23:59:59Z (first 2026-05-21 active-workday event, the P6-04 Direction A implementation, following the merged P6-04 planning / enumeration packet (PR #156 at `14ff8d3`, sibling Mode B PR #157 at `8e88d67`) on 2026-05-20).
**Authored**: approx. 2026-05-21T18:00Z (authored timestamp; not a completed-at timestamp).
**Overall Status**: Green at packet authoring (the P6-04 implementation PR #158 is **open / awaiting Kevin's review**, not merged; this packet is required by ADR-008 §D3 / §D5 to be committed and merged to `main` **before** PR #158 merges; `main` head at time of authoring is `14ff8d3`, the merged P6-04 planning packet).
**Monitor Mode**: ADR-008 Mode B — Continuous Governance Monitor.
**Trigger**: ADR-008 §D3 / §D5. The P6-04 Direction A implementation (branch `p6-04-direction-a-2026-05-21`, implementation commit `625ed91b275e5502a698f4efb3c5d7620db779d4` awaiting review) was prepared on 2026-05-21 against `main` at `14ff8d3`, making 2026-05-21 an active-workday event under ADR-008 §D3 (the first `src/**` / `tests/**` PR after the merged P6-04 planning packet).

**Naming note (ADR-008 §D4 / §D5):** This is the **first** Mode B sibling packet for 2026-05-21, covering the P6-04 Direction A implementation PR (expected PR #158). Per ADR-008 §D5, the PR that commits this Mode B packet (expected PR #159) must merge to `main` **before** the P6-04 implementation PR #158 merges. PR numbers #158 / #159 are the expected assignments at PR-open time (the prior pair was PR #156 planning / PR #157 monitoring); the maintainer confirms the actual numbers when the PRs are opened.

---

## Activity Summary

UTC date 2026-05-21 has an active-workday event under ADR-008 §D3: the P6-04 Direction A simulated order intent extension implementation (branch `p6-04-direction-a-2026-05-21`, implementation commit `625ed91b275e5502a698f4efb3c5d7620db779d4`, base `main` at `14ff8d3`) is prepared and **awaiting Kevin's review**, selecting **Direction A** of the two planning-level candidate directions recorded in the merged P6-04 planning packet (`governance/authorizations/2026-05-20_p6-04-planning.md`). At the time this packet is authored, **the P6-04 implementation PR #158 is open / awaiting review and has not merged**; this packet must be committed and merged to `main` before PR #158 merges per ADR-008 §D5.

**P6-04 implementation PR #158 metadata.**

- **URL:** https://github.com/KPH3802/gmc-rebuild/pull/158 (expected PR number; assigned at PR-open time)
- **Title:** `feat: add P6-04 Direction A simulated order intent extension`
- **Branch:** `p6-04-direction-a-2026-05-21`
- **Implementation commit awaiting review:** `625ed91b275e5502a698f4efb3c5d7620db779d4`
- **Base:** `main` at `14ff8d3`
- **State:** open / awaiting Kevin's review (not merged)
- **Classification:** Bounded `src/**` / `tests/**` **P6-04 Direction A implementation** packet authorized by Kevin in writing on 2026-05-21 per `governance/authorizations/2026-05-21_p6-04.md`. **PR #158 extends the existing local-only simulated-order-intent surface in place inside `src/gmc_rebuild/simulation/`; it adds no new top-level source package, adds no new `src/**` directory, leaves the `MASTER_STATUS.md` §8 step 4a `allowed_p2_infra` allowlist unchanged, introduces no broker / account / venue / market-data / order-routing / order-placement / strategy / live-trading / paper-trading / network / persistence / scheduler / daemon / `__main__` / env-var / secrets behavior, and changes no quality-gate / tag / release surface.**

**Authorization of record for PR #158.** Kevin's verbatim written authorization on 2026-05-21 is reproduced in full in `governance/authorizations/2026-05-21_p6-04.md` §Authorization (two verbatim blocks: the Direction A implementation directive, and the explicit ninth-field disambiguation). The authorization selects **Direction A** — extend the existing simulated-order-intent surface in place — and **does not** open Direction B (a separately named composed record class in a new sibling subpackage). It is the separate written implementation authorization required by the P6-04 planning packet (`governance/authorizations/2026-05-20_p6-04-planning.md` §Required Implementation Authorization (Future)) and by the merged P5-02 / P5-03 guard-rail tripwires that explicitly named `time_in_force` as a ninth-field example requiring its own explicit authorization line.

**The explicit ninth-field decision.** Kevin explicitly authorized `time_in_force` becoming a **real ninth field** on `SimulatedOrderIntent`. The merged P5-02 / P5-03 / P5-04 guard-rail tripwires asserted an eight-field shape and explicitly named `time_in_force` as a "future ninth field" that must "fail this assertion before it lands"; Kevin's verbatim disambiguation confirms this is "an intentional P6-04 guardrail update, not a guardrail failure" and directs that "the tests that previously expected `time_in_force` to be a future field" be updated "so they now assert the P6-04 nine-field shape." The prior eight-field invariant was correct for P5; P6-04 is the explicit authorization to evolve that shape in place. The new field is **optional and defaulted** (`SimulatedOrderTimeInForce.DAY`) so existing eight-argument `SimulatedOrderIntent` construction across the merged P5-02..P5-07 surface is preserved unchanged.

**PR #158 scope (as reported on the implementation branch).**

| File | Change | Notes |
|---|---|---|
| `governance/authorizations/2026-05-21_p6-04.md` | new | P6-04 Direction A implementation authorization of record (Kevin's two verbatim blocks, allowed scope, authorized contract, required tests, explicitly-not-authorized list, required sequencing, required validation, review basis). |
| `src/gmc_rebuild/simulation/_boundary.py` | modified | Adds the closed `SimulatedOrderTimeInForce` `StrEnum` (`DAY`, `GOOD_TILL_CANCEL`, `IMMEDIATE_OR_CANCEL`, `FILL_OR_KILL`); adds `time_in_force` as the ninth `SimulatedOrderIntent` field (default `DAY`) with `__post_init__` validation and a matching defaulted `build()` parameter; adds the deterministic, pure `derive_simulated_order_intent_id` helper (a `simoi-`-prefixed SHA-256 content fingerprint over a closed content subset). Only new import is `hashlib` (stdlib). Updated `__all__` and the module docstring. |
| `src/gmc_rebuild/simulation/__init__.py` | modified | Re-exports the new `SimulatedOrderTimeInForce` enum and the `derive_simulated_order_intent_id` helper; updates `__all__` and the docstring constraints (closed time-in-force enumeration; deterministic order-intent identity; the order-intent record now carries a time-in-force duration tag). |
| `tests/simulation/test_p6_04_order_intent_extension.py` | new | 28 focused deterministic tests covering the closed TIF enum, the deterministic identity helper (determinism / idempotence / field-sensitivity / input validation / usability as `intent_id`), the nine-field shape, immutability with the new field, the defaulted `time_in_force`, `build()` parity, equality/hash including the new field, and the preserved local-only `propose_order` gate. |
| `tests/simulation/test_simulated_order_intent.py` | modified | Updated the eight-field structural tripwire to assert the P6-04 nine-field shape; updated the surrounding docstring (the record no longer omits a time-in-force tag). |
| `tests/simulation/test_simulated_order_intent_invariants.py` | modified | Renamed/updated the eight-field invariant tripwire to assert the nine-field shape; added a `differs_by_time_in_force` equality/hash case; updated the distinct-classes field tuple and the section docstrings. |
| `tests/simulation/test_simulation_boundary.py` | modified | Extended the public-surface `__all__` assertion to include the two new P6-04 symbols. |
| `tests/simulation/test_composed_safety_foundation.py` | modified | Updated the field-introspection tripwire to assert the nine-field shape. |
| `MASTER_STATUS.md` | modified | Added a conservative §1 P6-04 implementation status reflection scoped to the open P6-04 implementation PR. The §8 step 4a `allowed_p2_infra` allowlist is **unchanged**. |

Nine files changed on PR #158 (2 new under `governance/` and `tests/simulation/`, 7 modified). PR #158 is a **bounded P6-04 Direction A implementation** authorized by `governance/authorizations/2026-05-21_p6-04.md`. It explicitly does **not**:

- Create any new top-level source package or any new `src/**` directory. Direction A stays entirely inside the already-allowlisted `src/gmc_rebuild/simulation/` subpackage. The `MASTER_STATUS.md` §8 step 4a `allowed_p2_infra` allowlist is preserved exactly at the thirteen entries on `main` after the merged P6-03 implementation (`src`, `src/gmc_rebuild/config`, `src/gmc_rebuild/time`, `src/gmc_rebuild/logging`, `src/gmc_rebuild/risk`, `src/gmc_rebuild/heartbeat`, `src/gmc_rebuild/kill_switch`, `src/gmc_rebuild/reconciliation`, `src/gmc_rebuild/runtime`, `src/gmc_rebuild/simulation`, `src/gmc_rebuild/signal_intake`, `src/gmc_rebuild/eligibility`, `src/gmc_rebuild/decision`).
- Open Direction B. No separately named composed record class, no `DecidedOrderIntent` / `ComposedOrderIntent`, no new sibling subpackage. Direction B remains future / not authorized.
- Change the merged `SimulationBoundary.propose` (P5-01) or `SimulationBoundary.propose_order` (P5-02) identity-return semantics, the `SafetyVerdict.clear` precondition, the lane-mismatch rejection, or the blocked-verdict rejection behavior. These are preserved byte-for-byte semantically; the merged P5-03..P5-07 tripwire suites that pin them are preserved.
- Expand any other merged closed shape. No additional `SimulationLane` member beyond `LOCAL_ONLY`; no additional `SimulatedOrderSide` member beyond `BUY` / `SELL`; no additional `SimulatedOrderType` member beyond `MARKET` / `LIMIT`; no tenth `SimulatedOrderIntent` field; no additional `SimulatedOrderTimeInForce` member beyond the four authorized; no additional method on `SimulationBoundary`.
- Expand any merged P6-01 / P6-02 / P6-03 surface. No change to `SignalIntent` / `SignalSide`, `EligibilityOutcome` / `EligibilityReason` / `EligibilityConfig` / `EligibilityDecision`, or `PositionDecisionOutcome` / `PositionDecisionReason` / `PositionDecision`, or the merged `accept_signal_intent` / `check_eligibility` / `compose_position_decision` signatures.
- Re-export the new surface from `src/gmc_rebuild/__init__.py`. The new `SimulatedOrderTimeInForce` and `derive_simulated_order_intent_id` are reachable only via `from gmc_rebuild.simulation import ...`, mirroring the merged non-re-export precedent.
- Introduce any broker integration (real or paper), broker SDK, broker account identifier, broker session, broker handshake, or broker credential.
- Introduce any live / delayed / paper market data, market-data feed, vendor SDK, real symbol universe, or real venue identifier.
- Introduce any real or paper order placement, order routing, order management, order book, fill, execution, position, P&L, trade report, OMS, EMS, routing instruction, post-only / IOC / FOK execution modifier wired to any router, FIX session, REST client, or WebSocket client. The `time_in_force` field is a pure order-duration data tag; it triggers no broker action and is not wired to any execution surface.
- Introduce any account identifier, venue identifier, secrets, credentials, API keys, `.env` reads, `os.environ` / `os.getenv` reads, or any other credential / env surface.
- Introduce any external API call, network call, `socket`, `urllib`, `requests`, `http`, `ssl`, `smtplib`, `ftplib`, or DNS lookup.
- Introduce any scheduler, daemon, background thread, long-running service, `__main__` entry point, `if __name__` block, `time.sleep`, `asyncio.sleep`, cron job, or launchd plist.
- Introduce any persistence, database, SQLite, pickle, shelve, filesystem write, on-disk snapshot, log sink, or file artifact. The deterministic identity helper opens no file and holds no state.
- Introduce any strategy, scanner, model, portfolio, backtest, live trading, or paper trading wired to a real broker.
- Reinterpret or relax the GOV-02 execution-environment workflow rule.
- Relax any quality gate, hook, mypy strictness, ruff rule, or `detect-secrets` baseline; create any tag, release, or version bump; or open any successor P6-05+ packet.

**Validation reported on the P6-04 implementation branch (`p6-04-direction-a-2026-05-21`, commit `625ed91`).**

- `.venv/bin/pre-commit run --all-files` → **Passed** with every hook green (ruff legacy alias, ruff format, mypy strict, trim trailing whitespace, fix end-of-files, check yaml, check json (skipped — no files), check python ast, check for added large files, check for merge conflicts, mixed line ending, detect-secrets, pytest); no second-pass `files were modified by this hook` message.
- `.venv/bin/python -m pytest -q` → **578 passed** (the post-P6-03 baseline of 550 tests plus 28 new P6-04 tests; no test removed, the two field-count tripwires intentionally evolved 8→9).
- `git diff --stat main..HEAD` → nine files changed, 891 insertions / 40 deletions, confined to `governance/authorizations/2026-05-21_p6-04.md` (new), `src/gmc_rebuild/simulation/_boundary.py`, `src/gmc_rebuild/simulation/__init__.py`, `tests/simulation/test_p6_04_order_intent_extension.py` (new), `tests/simulation/test_simulated_order_intent.py`, `tests/simulation/test_simulated_order_intent_invariants.py`, `tests/simulation/test_simulation_boundary.py`, `tests/simulation/test_composed_safety_foundation.py`, and `MASTER_STATUS.md`.
- §8 step 4 always-forbidden top-level scan → OK; §8 step 4a allowlist → unchanged thirteen entries with no new directory; §8 step 4c recursive name audit → the only `order` token hits are the pre-existing, accepted P5-02 / P5-03 `*_order_intent*` simulation-test naming convention (and the new `test_p6_04_order_intent_extension.py` following that same accepted convention), referring to the simulated-order-intent data shape, not order placement / routing. Root `gmc_rebuild` does not re-export the new surface (verified).

**Monitoring sequencing (Mode B, ADR-008 §D3 / §D5).** The P6-04 implementation is a 2026-05-21 active-workday event. Per ADR-008 §D5, per `governance/authorizations/2026-05-21_p6-04.md` §Required Sequencing, and per the established 2026-05-13 through 2026-05-20 precedents (every prior active-workday `src/**` / `tests/**` PR has been preceded by a sibling Mode B packet PR that merged first), this packet must be committed and merged to `main` in a **separate monitoring PR** (expected PR #159) before the P6-04 implementation PR #158 merges. The P6-04 implementation PR does not bundle the monitoring packet, per `AI_WORKFLOW.md` §6 rule 1. The monitoring branch (`monitoring/2026-05-21-pr-158-p6-04-implementation`) is based on **current `main` head `14ff8d3`**, **not** on the P6-04 implementation branch.

---

## Mode A Context (PR #158)

The P6-04 implementation PR modifies a merged `src/**` surface and **intentionally evolves a merged guard-rail invariant** (the eight-field `SimulatedOrderIntent` shape → nine fields). Per `governance/authorizations/2026-05-21_p6-04.md` §Required Sequencing and `AI_WORKFLOW.md` §4, Mode A adversarial review is **recommended as PR-review text** before merge, mirroring the P5-01 / P6-01 / P6-02 / P6-03 first-implementation precedents for `src/**` control-surface changes. Per `AI_WORKFLOW.md` §6 rule 5, Mode A output is recorded as PR-review text on PR #158 only and **is not committed to the repository**.

**Important: This monitoring PR does not itself authorize any new Phase 6 work, open any successor packet, open any new authorization artifact, change the authorization or status of PR #158 beyond serving as monitoring evidence, or change any phase-boundary control.** It records that PR #158 is a bounded `src/**` / `tests/**` P6-04 Direction A implementation that extends the existing simulated-order-intent surface in place with a deterministic, side-effect-free, mutation-free, local-only time-in-force tag and identity helper, with the merged P5-01..P5-07 simulation surface, the merged P6-01 / P6-02 / P6-03 surfaces, the safety foundation (P4-06 / P4-07 / P4-08), the in-memory fakes (P3-03 / P3-04 / P3-05), the operations records (OPS-01..OPS-04B / OPS-06), the canonical allowlists, the merged GOV-01 / GOV-02 governance packets, and the merged Phase 6 entry plan all preserved unchanged.

---

## Known Review Focus (for Kevin / Mode A)

This packet records the specific review focus the maintainer flagged for the P6-04 implementation. The reviewer should confirm, on the implementation branch, that:

1. **Local-only.** The new time-in-force tag and the deterministic identity helper introduce no broker, no account identifier, no venue identifier, no order routing, no order placement, no live trading, and no paper trading wired to a real broker. `time_in_force` is a pure order-duration label; `derive_simulated_order_intent_id` is a pure content fingerprint. Neither is wired to any execution surface. The merged `SimulationLane` remains closed at `LOCAL_ONLY`.
2. **Deterministic.** `derive_simulated_order_intent_id` returns the byte-for-byte identical identifier for identical inputs across repeated calls, with no randomness, no clock read (the `created_at` value is caller-supplied, not read from a wall clock), no counter, and no hidden state. Distinct content produces distinct identifiers. The implementation tests assert determinism, idempotence, and field-sensitivity.
3. **Immutable.** `SimulatedOrderIntent` remains a frozen, slotted dataclass with the new ninth field; assignment to `time_in_force` raises `FrozenInstanceError`; the record has no `__dict__`; equality and hash include the new field. The deterministic identity helper mutates no input.
4. **No broker / order-routing / live-trading concepts.** The new `SimulatedOrderTimeInForce` members (`DAY`, `GOOD_TILL_CANCEL`, `IMMEDIATE_OR_CANCEL`, `FILL_OR_KILL`) are data tags only; they do not imply any connection to a venue, broker, or matching engine, and they carry no post-only / IOC / FOK execution-routing behavior. The `RECOVERY.md` §16.5 order-intent-semantics boundary remains respected: no venue / account / broker credential / routing field is added.
5. **Guard-rail evolution is intentional and authorized.** The two merged eight-field tripwires (which explicitly named `time_in_force`) were updated to the nine-field shape per Kevin's explicit ninth-field authorization; this is an intentional, separately-authorized P6-04 guard-rail update, not a guard-rail failure. The reviewer should confirm the tripwires now assert the nine-field shape and that no other merged invariant was weakened.

---

## Risks Considered (PR #158)

1. **Risk: the implementation drifts into a forbidden category (broker / order routing / live or paper trading / market data / network / persistence / scheduler).** Mitigation: `git diff --stat main..HEAD` confines the change to the simulation subpackage, its tests, the authorization artifact, and a one-paragraph `MASTER_STATUS.md` reflection. The only new source import is `hashlib` (stdlib). The existing source-inertness tests (which glob every `*.py` under `src/gmc_rebuild/simulation/`) pass, confirming no forbidden runtime import, no `time.sleep`, no `os.environ` / `os.getenv`, no `open(`, no `socket.` / `urllib.` / `requests.`, and no `__main__`. The `time_in_force` enum and the identity helper are pure data / pure functions with no execution wiring.
2. **Risk: the ninth-field addition silently breaks merged P5 behavior.** Mitigation: `time_in_force` is optional and defaulted to `DAY`, so existing eight-argument `SimulatedOrderIntent` construction across the merged P5-02..P5-07 tripwires continues to work unchanged; the 578-test suite passes with no test removed. Only the two explicit field-count tripwires and a small number of field-introspection / public-surface assertions were intentionally updated to the nine-field shape per Kevin's authorization.
3. **Risk: the deterministic identity helper is non-deterministic or leaks entropy / clock.** Mitigation: the helper uses `hashlib.sha256` over a canonical delimiter-joined serialization of a closed content subset; it reads no wall clock (the `created_at` value is caller-supplied), draws no randomness, holds no counter, and imports neither `uuid`, `random`, nor `time`. The implementation tests assert determinism across repeated calls, idempotence, field-sensitivity, and that the output is a valid whitespace-free `intent_id`.
4. **Risk: the §8 step 4a allowlist is silently extended or a new top-level package is added.** Mitigation: Direction A stays inside the already-allowlisted `src/gmc_rebuild/simulation/` entry; the allowlist is preserved exactly at thirteen entries; `git ls-files src/gmc_rebuild/*` confirms exactly twelve source subpackages with no new directory.
5. **Risk: monitoring-packet drift if this Mode B sibling does not merge before PR #158.** Mitigation: ADR-008 §D5, the P6-04 implementation authorization §Required Sequencing, and the established precedents all require merge of this packet first; the maintainer sequences the two merges accordingly.
6. **Risk: the new surface is mistaken for authorization of Direction B or any successor packet.** Mitigation: PR #158 implements only Direction A; the authorization artifact explicitly records that Direction B and all P6-05+ packets remain future / not authorized. No composed record class and no new sibling subpackage is introduced.
7. **Risk: the new surface is re-exported from the package root.** Mitigation: the implementation tests assert that `gmc_rebuild` does not expose `SimulatedOrderTimeInForce` or `derive_simulated_order_intent_id`; the new surface is reachable only via `gmc_rebuild.simulation`.
8. **Risk: confusion about whether `time_in_force` is an execution instruction.** Mitigation: the field is documented and reviewed as a pure order-duration data tag, not a routing / execution modifier; no venue, broker, account, or routing field is added; the `RECOVERY.md` §16.5 order-intent-semantics boundary is respected.

---

## Conditions to be Confirmed Before PR #158 Merges

1. **The narrow diff on PR #158** — exactly the nine files listed in the scope table above (2 new, 7 modified), with no new `src/**` directory, no new top-level source package, no §8 step 4a allowlist change, and no other `governance/authorizations/*` modification beyond the new P6-04 implementation authorization.
2. **Mode A critique** recorded against PR #158 itself in PR-review text — per ADR-008 §D7, `AI_WORKFLOW.md` §4 / §6 rule 5, and the P6-04 implementation authorization §Required Sequencing — and **not committed as a file**. Mode A is recommended because PR #158 modifies a merged `src/**` control surface and evolves a merged guard-rail invariant.
3. **Mode B monitoring packet (this packet)** authored under ADR-008 Mode B, filed in a separate monitoring PR (expected PR #159) per ADR-008 §D5, and merged to `main` **before** PR #158 merges.
4. **PR #158 validation** as reported on the implementation branch: `.venv/bin/pre-commit run --all-files` exits 0 with every hook passing; `.venv/bin/python -m pytest -q` returns 578 passed; `git diff --stat main..HEAD` shows the nine-file diff; the §8 step 4 / 4a / 4c boundary scans confirm no new forbidden top-level category, no allowlist change, and only the accepted simulated-order-intent `order` naming convention.
5. **Known review focus** (local-only, deterministic, immutable, no broker / order-routing / live-trading concepts) confirmed by the reviewer per the section above.

---

## Diff Scope Verification (this monitoring PR)

This monitoring PR adds exactly **one** new file: `monitoring/daily/2026-05-21_pr-158-p6-04-implementation.md`. **No other file is modified, added, or deleted by this monitoring PR; this monitoring PR changes no code, no implementation source, no tests, and no canonical docs on the monitoring branch — only this single monitoring file.** The monitoring branch (`monitoring/2026-05-21-pr-158-p6-04-implementation`) is based on **current `main` head `14ff8d3`**, not on the P6-04 implementation branch. The §8 step 4a `allowed_p2_infra` allowlist on `main` is preserved exactly at the thirteen entries after the merged P6-03 implementation. This monitoring PR introduces no new `src/**` directory, so §8 step 4b's same-PR allowlist-update rule does not trigger.

---

## Non-Goals (this monitoring PR and PR #158)

Neither this monitoring PR nor PR #158 does any of the following:

- Open Direction B, any P6-05 or later P6-0N task, or any successor packet. Each future packet continues to require its own separate written authorization from Kevin per `AI_WORKFLOW.md` §7.
- Add or authorize any new top-level source package or any new `src/**` directory.
- Add or authorize any third `SimulationLane` / third `SimulatedOrderSide` / third `SimulatedOrderType` member, any fifth `SimulatedOrderTimeInForce` member, any tenth `SimulatedOrderIntent` field, or any additional `SimulationBoundary` method.
- Change the merged `propose` / `propose_order` identity-return semantics or the `SafetyVerdict.clear` precondition.
- Authorize any broker integration (real or paper), live / delayed / paper market data, real or paper order placement, order routing, execution adapter, venue / account / broker credential field, secrets / env loading, network / API call, scheduler / daemon, persistence / filesystem write, strategy / scanner / model / portfolio / backtest / live trading / production execution, `time.sleep`, or concrete protocol implementation.
- Modify the merged P5-01..P5-07 simulation surface beyond the authorized Direction A in-place extension; the merged P6-01 / P6-02 / P6-03 surfaces; the merged P4-06 / P4-07 / P4-08 safety surfaces; the P3-03 / P3-04 / P3-05 fakes; the P2-01..P2-05 packages; the OPS-01..OPS-04B / OPS-06 records; or the GOV-01 / GOV-02 packets. All are preserved unchanged.
- Modify any file under `src/**` or `tests/**` on this monitoring branch (this monitoring PR's `src/**` and `tests/**` diffs are empty).
- Modify `MASTER_STATUS.md`, `README.md`, `RECOVERY.md`, `plan/**`, any ADR, `AI_WORKFLOW.md`, any existing `governance/authorizations/*` file, `pyproject.toml`, `.pre-commit-config.yaml`, `.secrets.baseline`, `.gitignore`, or any other `monitoring/**` file beyond this new packet itself.
- Modify the `MASTER_STATUS.md` §8 step 4a allowlist, the §8 step 4 always-forbidden scan, the §8 step 4c forbidden-token bash gate, or the §8 step 8 canonical-doc staleness check.
- Promote X10 Layer 5, automate backup-monitoring, execute any DR drill, or open OPS-05 / OPS-07.
- Relax any quality gate; create any tag, release, or version bump.
- Substitute for any Mode A adversarial review of PR #158 — Mode A and Mode B are independent dual artifacts per ADR-008 §D7.

---

## Required Merge Order

Per ADR-008 §D3 / §D5 and per `governance/authorizations/2026-05-21_p6-04.md` §Required Sequencing: **this monitoring PR (expected PR #159) must merge to `main` before the P6-04 implementation PR #158 merges.** The maintainer is responsible for sequencing the two merges accordingly; this packet does not itself authorize any merge.

---

## Closing

This packet records the Mode B governance-monitor evidence for the P6-04 Direction A simulated order intent extension implementation (branch `p6-04-direction-a-2026-05-21`, implementation commit `625ed91b275e5502a698f4efb3c5d7620db779d4` awaiting Kevin's review, expected PR #158). The implementation extends the existing local-only simulated-order-intent surface in place inside `src/gmc_rebuild/simulation/` with a closed `SimulatedOrderTimeInForce` enum carried as a real ninth `SimulatedOrderIntent` field (defaulting to `DAY`) and a deterministic, pure `derive_simulated_order_intent_id` identity helper, under Kevin's verbatim written authorization on 2026-05-21 (`governance/authorizations/2026-05-21_p6-04.md`), including the explicit ninth-field decision and the intentional evolution of the merged P5 eight-field guard-rail tripwires to the P6-04 nine-field shape. PR #158 adds no new top-level source package, leaves the §8 step 4a allowlist unchanged, introduces no broker / account / venue / market-data / order-routing / order-placement / strategy / live-trading / paper-trading / network / persistence / scheduler / daemon / `__main__` / env-var / secrets behavior, and reports `.venv/bin/pre-commit run --all-files` passing and `.venv/bin/python -m pytest -q` passing with 578 tests. The known review focus is that the new intent identity and time-in-force semantics remain local-only, deterministic, immutable, and free of broker / order-routing / live-trading concepts. Per ADR-008 §D5, this packet must merge to `main` **before** the P6-04 implementation PR #158 merges. Nothing is merged by this packet; the P6-04 implementation awaits Kevin's review.
