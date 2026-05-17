# RECOVERY — Project Resilience Plan (`gmc-rebuild`)

**Status:** Documentation only. Captures the no-single-point-of-failure standard for the `gmc-rebuild` project. Authorized as the OPS-01 project resilience checkpoint on 2026-05-16 per `governance/authorizations/2026-05-16_ops-01.md`. Extended on 2026-05-16 by the OPS-02 Backblaze restore-drill record per `governance/authorizations/2026-05-16_ops-02.md` (see §5.5).

**Maintained by:** Kevin Heaney (operator). The repository contains no agents, daemons, or schedulers; every operational action described here is performed by the human operator on his own hardware. This file describes the standard. It does **not** execute it.

**Scope:** This document is operations doctrine for the `gmc-rebuild` source tree itself — the code, governance, tests, and documents that make up the repository. It is not a recovery plan for any trading runtime, broker connection, market-data feed, or order pipeline. None of those exist in this repository at the current `main` checkpoint, and none are authorized by this document.

**Out of scope:** Secrets, credentials, broker accounts, market data, order history, fills, positions, P&L, tax records, and any other data that has nothing to do with this source tree. If and when such data ever exists, it requires its own separate recovery plan with its own separate written authorization from Kevin.

---

## 1. Resilience Principle — No Single Point of Failure

The project must survive the loss of any single device, any single account, any single network, and any single human action, without losing more than a bounded, recoverable amount of work.

The standard is a 3-2-1-1-0 style model adapted to a one-person, hedge-fund-grade engineering workflow:

| Number | Meaning in this project |
| --- | --- |
| **3** copies of every load-bearing artifact | GitHub `main` + local Mac Studio working tree + at least one independent backup layer (Time Machine on LaCie **and** Backblaze offsite). |
| **2** different storage media | Spinning / SSD local media (Mac internal, LaCie, X10 Pro) **and** independent offsite cloud (Backblaze). GitHub itself is a third, vendor-managed medium. |
| **1** copy offsite | Backblaze (continuous, encrypted offsite cloud) and GitHub (vendor-managed offsite). |
| **1** copy offline | Seagate X10 Pro, used as a rotating offline / cold copy. Only enabled after the live backup layers are verified healthy. |
| **0** restore failures tolerated | Every backup layer must be exercised by a periodic recovery drill (§5). A backup that has never been restored is not yet a backup. |

The repository's authoritative state lives in **one** place: the `KPH3802/gmc-rebuild` GitHub repository, `main` branch. Every other copy is a recoverable mirror or a working tree on top of `main`.

---

## 2. Source of Truth

- **Authoritative remote:** `https://github.com/KPH3802/gmc-rebuild`, branch `main`.
- **Authoritative governance:** every authorization of record lives under `governance/authorizations/` on `main`. The verbatim written authorization captured in each artifact is the authorization of record per `AI_WORKFLOW.md` §7.
- **Authoritative status:** `MASTER_STATUS.md` on `main`, maintained by Perplexity Computer per `AI_WORKFLOW.md` §1.2 and §6 rule 2 ("One status keeper").
- **Authoritative decisions:** `docs/decisions/ADR-*.md` on `main`.
- **Authoritative plan:** `plan/phase4_entry_plan.md` (current phase) and prior `plan/phase*_entry_plan.md` files on `main`.

If any local copy disagrees with `main`, `main` wins. The recovery drill in §5 always starts from `main`.

---

## 3. Backup Layers

The four backup layers, in priority order. Each layer is independent of the others; the failure of any one layer must not compromise any other.

### 3.1 Layer 1 — GitHub (authoritative remote)

- **Role:** Source of truth. Vendor-managed offsite copy of every commit, branch, tag, PR, review, issue, and authorization artifact that has been pushed.
- **Owned by:** Kevin Heaney (GitHub account `KPH3802`).
- **Failure modes covered:** Local hardware loss (Mac Studio dies, LaCie dies, X10 Pro dies), local-network loss, accidental local deletion of files that have already been pushed.
- **Failure modes NOT covered:** Account compromise, vendor outage, force-push to `main` that overwrites history, repository deletion, branch deletion, and any in-flight local work that has not yet been pushed.
- **Operator-side discipline:**
  - 2FA enabled on the GitHub account.
  - Branch protection on `main`: PR review required; force-push to `main` not permitted.
  - Push at least once per work session and before powering down the Mac Studio.
  - Never rely on a feature branch as the only copy of important work; merged `main` is the only durable layer.

### 3.2 Layer 2 — Mac Studio working tree (local working copy)

- **Role:** The active working tree. Where code is edited, where pre-commit runs, where PRs are prepared.
- **Failure modes covered:** Short network outages, GitHub vendor outage of bounded duration (work can continue locally and be pushed when reachability returns).
- **Failure modes NOT covered:** Disk failure of the Mac Studio, accidental local deletion of unpushed work, accidental destructive git operations on local branches.
- **Operator-side discipline:**
  - Treat the Mac Studio working tree as **ephemeral**. Anything that is not pushed is not yet safe.
  - Run `git status` and `git fetch` at the start of every session. If the local checkout is behind `main`, sync **before** starting new work (§6).
  - Never store secrets, credentials, broker keys, market data, or any other forbidden artifact (see §7) inside the working tree, even temporarily.

### 3.3 Layer 3 — LaCie + Time Machine (local recovery)

- **Role:** Local point-in-time recovery for the Mac Studio. Restores the working tree (and the rest of the Mac filesystem) to an earlier state if a destructive local action damages files that have not yet been pushed.
- **Failure modes covered:** Local destructive action (accidental `rm -rf`, accidental discard of an uncommitted change), local filesystem corruption.
- **Failure modes NOT covered:** Loss of both the Mac Studio and the LaCie (fire, theft, flood, power surge), loss of the LaCie alone (then Layer 4 takes over). Time Machine does not protect against a destructive operation performed inside GitHub.
- **Observed state at 2026-05-16:** Time Machine is **active** on the LaCie. No setting change is authorized by this packet.

### 3.4 Layer 4 — Backblaze (offsite cloud)

- **Role:** Continuous, encrypted offsite cloud backup. Independent of GitHub, the Mac Studio, the LaCie, and the X10 Pro.
- **Failure modes covered:** Loss of all local hardware (fire, theft, flood, power surge), prolonged GitHub vendor outage, account-side issues that affect GitHub but not Backblaze.
- **Failure modes NOT covered:** Operator-side account compromise of Backblaze itself, undiscovered backup-health failure (a backup that silently stopped working). Both are addressed by the recovery drill in §5.
- **Observed state at 2026-05-16:** Backblaze is **installed** and, as of 2026-05-16, **restore-proven for one non-sensitive project file** (see §5.5 for the recorded drill and `governance/authorizations/2026-05-16_ops-02.md` for the authorization of record). The Seagate X10 Pro is mounted and selected in Backblaze. A single successful restore for one file is the minimum bar described in §9.3; Backblaze health is treated as verified at that scope as of 2026-05-16, and any broader claim (multiple files, larger artifacts, rotation across time) requires its own separate operator-side drill on its own date.

### 3.5 Layer 5 — Seagate X10 Pro (offline / rotating cold copy)

- **Role:** Offline rotating cold copy. Enabled only **after** Layer 4 (Backblaze) is proven healthy. Protects against an active threat (ransomware, account compromise, accidental synchronized destruction across live layers) that the always-online layers cannot survive.
- **Failure modes covered:** Synchronized destruction across live layers (e.g., an action that propagates to GitHub, Time Machine, and Backblaze before it is noticed), prolonged outage of every live layer.
- **Failure modes NOT covered:** Physical loss of the X10 Pro itself; this is acceptable because the X10 Pro is the deepest layer, not the only layer.
- **Observed state at 2026-05-16:** The X10 Pro is **mounted** and **selected in Backblaze**. It is not yet rotated as an offline cold copy. Establishing a rotation cadence (connect → snapshot → disconnect and store offline → rotate) is an operator-side action that is **not authorized** by this packet; it is named here only as the next safe action **after** Layer 4 is proven healthy.

---

## 4. Device Roles Summary

| Device / Account | Role | Authoritative? | Always online? | Owned by |
| --- | --- | --- | --- | --- |
| GitHub `KPH3802/gmc-rebuild` `main` | Source of truth | **Yes** | Yes | Kevin (vendor-managed) |
| Mac Studio working tree | Working copy | No | When powered on | Kevin |
| LaCie (Time Machine target) | Local recovery | No | When connected | Kevin |
| Backblaze | Offsite cloud backup | No | Yes (continuous) | Kevin (vendor-managed) |
| Seagate X10 Pro | Offline / rotating cold copy | No | **No** (rotated offline) | Kevin |

No device other than GitHub is authoritative. If a layer disagrees with `main`, `main` is correct and the layer is the one to repair.

---

## 5. Recovery Drill — "Fresh Clone From Cold"

The recovery drill is the periodic exercise that proves the project can be rebuilt from the source of truth alone. A backup layer that has never been exercised is not yet a backup.

The drill is **operator-side**, performed by Kevin on a clean directory. It does **not** require any other device, any local backup, or any prior state.

### 5.1 Steps

1. **Clean directory.** Choose a directory that does not already contain a `gmc-rebuild` checkout. Confirm it is empty.
2. **Fresh clone.** Clone the authoritative remote:
   ```
   gh repo clone KPH3802/gmc-rebuild
   cd gmc-rebuild
   ```
   (Equivalent: `git clone https://github.com/KPH3802/gmc-rebuild.git`.)
3. **Confirm baseline.** `git status` reports a clean working tree. `git log -1 --oneline` shows the current `main` head.
4. **Python environment.** Create an isolated virtual environment that uses Python 3.12 (per `pyproject.toml`):
   ```
   python3.12 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -e ".[dev]"
   ```
5. **Validate.** Run the full pre-commit gate exactly as the project requires for every implementation PR:
   ```
   python3 -m pre_commit run --all-files
   ```
   The expected result is a clean baseline: every hook passes, no test failures, no formatter changes, no detect-secrets findings beyond the committed baseline.
6. **Confirm safety state.** Optional spot check: `pytest tests/runtime/` and `pytest tests/p4_02_composed/` exercise the merged P4-06 / P4-07 / P4-08 safety surfaces and the merged composed-fixture / invariants / edge-cases / failure-modes suites. Both must pass.
7. **Tear down.** Deactivate the virtual environment. Optionally delete the clean directory. The drill leaves no trace.

### 5.2 What the drill proves

- The repository on `main` is self-sufficient: the source of truth alone is enough to rebuild a green, validated working tree.
- The pre-commit gate, the pinned tool versions in `pyproject.toml`, and the merged tests together form the project's verifiable baseline.
- Any deviation (a hook fails on a fresh clone, a test fails on a fresh clone, a dependency cannot be installed) is a real defect on `main` that must be repaired before further work is authorized.

### 5.3 What the drill does NOT do

- It does not exercise Backblaze (that is a separate operator-side action: restore a recent file from Backblaze to a known-good location and verify byte-for-byte).
- It does not exercise the X10 Pro offline rotation (that is a separate operator-side action and is only authorized after Backblaze is proven healthy).
- It does not restore any secret, credential, broker artifact, or market-data artifact — by §7, no such artifact is ever in the repository, so there is nothing to restore.
- It does not authorize any successor work. The drill is a check, not a change.

### 5.4 Cadence

- **At least once per phase boundary** (e.g., before opening Phase 5, before any local/paper simulation boundary planning is authorized).
- **At least once per quarter** as a calendar discipline.
- **Immediately after any incident** (lost device, suspected compromise, suspected destructive action, suspected Backblaze health failure).

### 5.5 Recorded Restore Drills

This section records each operator-side restore drill that has actually been performed, in date order. Each entry is a one-time record of a real drill that succeeded; it is not a standing claim of layer health beyond the scope of the drill it describes.

#### 2026-05-16 — Backblaze (Layer 4), single-file restore

- **Layer exercised:** Backblaze (Layer 4 in §3.4).
- **File chosen:** `docs/decisions/ADR-004_utc_discipline.md`. The file is an existing non-sensitive project file already on `main` at the time of the drill. It contains no secrets, credentials, broker data, market data, order data, or trading runtime content (consistent with §7 forbidden-artifact discipline; the file would not exist in this repository if it did).
- **Operator action:** Kevin Heaney restored the file from Backblaze to a known-good location on his own hardware and verified it byte-for-byte against the copy on `main`. The restore drill itself was an operator-side action performed outside this repository, per §9.3.
- **Restored file size:** 2,288 bytes.
- **Restored file SHA-256:** `e9b335b77fb0ee520a47fa2d2e413fcb176355a6e71df619c4d392d3f4f93535`.
- **Verification outcome:** The restored file matched the original byte-for-byte. The hash above was computed against the restored copy and is the value that the repository's copy of `docs/decisions/ADR-004_utc_discipline.md` on `main` must continue to match for this record to remain meaningful; any future change to that file by an authorized packet will leave this dated record unchanged, because the record describes the state restored on 2026-05-16, not the perpetual state of the file.
- **Authorization of record:** `governance/authorizations/2026-05-16_ops-02.md`.
- **What this entry proves:** Backblaze (Layer 4) successfully returned a real, recent, non-sensitive project file end-to-end on 2026-05-16. The "0 restore failures tolerated" half of the §1 standard is satisfied for Backblaze for this one file on this date.
- **What this entry does not prove:** It does not prove Backblaze health for larger files, for binary files, for files outside the working tree, for older or deleted-then-recovered files, or for any future point in time. Those are separate drills that require their own separate operator-side actions and their own separate written authorizations from Kevin. It does not prove the health of any other layer (Time Machine, X10 Pro, GitHub reachability from the Mac Studio); those remain governed by their own §3 entries and §9 safe-next-actions.

### 5.6 Recorded Investigations

This section records each operator-side investigation that has actually been performed, in date order. Each entry is a one-time record of a real read-only investigation; it is not a standing claim of layer health beyond the scope of the investigation it describes.

#### 2026-05-16 — Seagate X10 Pro (Layer 5), panic-history investigation

- **Layer / device examined:** Seagate X10 Pro (Layer 5 in §3.5).
- **Trigger:** A `loginwindow` `previousStartupWasAPanicOrHardRestart` flag was set at 2026-05-13 19:44 CDT, and prior operator recall associated past Mac Studio crashes with the X10 Pro. Operator wanted the 2026-05-13 reboot trigger characterized before any future Layer 5 promotion.
- **Method:** Read-only inspection only. No setting change, no repair, no eject / unmount, no First Aid, no formatting, no Backblaze or Time Machine setting change. Tools: `diskutil list`, `diskutil info`, `df -h`, `pmset -g log`, `/usr/bin/log show` (14-day window, narrow predicates), `last reboot`, and direct inspection of `/Library/Logs/DiagnosticReports`, `~/Library/Logs/DiagnosticReports`, and (absent) `/var/db/CrashReporter`.
- **Findings:**
  - **The 2026-05-13 19:43 CDT reboot was ungraceful.** `last` records a `reboot` entry with no paired `shutdown` entry, in contrast to every other reboot in the file.
  - **No kernel-panic dump exists.** No `*.panic`, `*.kernel`, or `Kernel_*` artifact in any diagnostic-report directory; zero `"panic"`-keyword matches in the unified log over the past 14 days other than self-referential `loginwindow` entries. The `loginwindow` flag name itself (`previousStartupWasAPanicOrHardRestart`) does not distinguish a kernel panic from a hard restart.
  - **Memory-pressure cluster on the same day.** Twelve `JetsamEvent-2026-05-13-*.ips` artifacts between 10:21 and 17:04 CDT.
  - **UI hang immediately preceding the reboot.** `NotificationsSettings_2026-05-13-194248_Kevins-Mac-Studio.hang` reports a 28-second hang ending 19:42:30 CDT; the hang stack is generic UI plumbing (`NSApplication` / `ViewBridge` / `HIRunLoop` / `mach_msg`) and contains no storage, APFS, USB, or kernel-storage code path.
  - **Post-reboot APFS work was benign.** `apfsd_2026-05-13-204001_Kevins-Mac-Studio.cpu_resource.diag` shows `apfsd` performing a `fts_read` / `getattrlistbulk` filesystem walk shortly after the new boot — the expected dirty-shutdown reconciliation, not a fault signature.
  - **No storage-stack incrimination of the X10 Pro.** Zero USB disconnect / reset / removal / error events tied to `disk6` / `disk7` (the X10 Pro container and volume) in the 14-day kernel record. No genuine APFS driver-level error, fault, failure, or corruption event in 14 days (a 60-hit search for "apfs error" matched only `peopled` / `sharingd` CoreData app errors whose payload happens to contain the string "apfs"). No NVMe, enclosure, ScsiTask, or media-error keyword hit in 14 days.
  - **Current X10 Pro state.** Mounted, APFS, USB SSD, 4 TB, 705.6 GB used / 3.3 TB free (≈18%); container `disk6` → `disk7` → `disk7s1` at `/Volumes/X10 Pro`. SMART status not exposed through the USB enclosure. `Owners: Disabled`. FileVault disabled. Backblaze continues to include the volume in its selection set with 0 remaining files at the time of the investigation.
- **Conclusion:** The 2026-05-13 19:43 CDT reboot was ungraceful. By the available 14-day read-only evidence, it is **not directly tied to the X10 Pro**; the stronger evidence pattern points to **memory pressure plus a UI hang followed by a hard restart**. This finding does not exonerate the X10 Pro; it only fails to incriminate it within the scope and time window of the investigation.
- **Resulting layer state:** **X10 Pro remains acceptable in its current Backblaze-included online role.** It is **not promoted** to Layer 5 (offline / rotating cold copy) by this investigation. Four independent X10 Pro gaps remain and together block Layer 5 promotion: (i) no SMART visibility through the USB enclosure, (ii) `Owners: Disabled` on the volume, (iii) FileVault not enabled on the volume, and (iv) only 14 days of clean log evidence on hand.
- **Recommended next gates before any future Layer 5 promotion** (each is operator-side, requires its own separate written authorization from Kevin at the time it is performed, and is **not authorized** by this packet):
  - **30-day clean observation window.** No new `previousStartupWasAPanicOrHardRestart` flag, no new USB / APFS / NVMe / enclosure kernel error tied to `disk6` / `disk7`, and no ungraceful reboot during a continuous 30-day window beginning at or after 2026-05-16.
  - **SMART-visibility decision.** Either accept the SMART gap with a written rationale, or move the drive to an enclosure that surfaces SMART through to macOS.
  - **Encryption / ownership decision.** Decide whether `Owners: Disabled` and the absence of FileVault are acceptable for a Layer 5 cold copy; if not, enable both before promotion.
  - **Cold restore drill.** At least one operator-side mount → snapshot → unmount → re-mount → verify cycle on the X10 Pro before treating it as a recovery layer, recorded in §5.5 / §5.6.
- **Authorization of record:** `governance/authorizations/2026-05-16_ops-03.md`.
- **What this entry proves:** Within the scope and 14-day window of the read-only investigation, no storage-layer evidence ties the 2026-05-13 ungraceful reboot to the X10 Pro, and the stronger evidence pattern points to system-wide memory pressure plus a UI hang. The X10 Pro is acceptable in its current Backblaze-included online role on this basis.
- **What this entry does not prove:** It does not prove the X10 Pro is free of latent faults, does not extend conclusions beyond the 14-day window, does not authorize Layer 5 promotion, and does not authorize any setting change, repair, eject, formatting, Backblaze setting change, Time Machine setting change, or rotation discipline on any device.

#### 2026-05-17 — Mac Studio (Layer 2), OPS-04 memory-pressure measurement cycle

- **Layer / device examined:** Mac Studio (Layer 2 in §3.2) — the operator's primary working machine.
- **Trigger:** The OPS-04 procedure at §14, authorized by `governance/authorizations/2026-05-16_ops-04.md`, requires at least one before-heavy-work snapshot and at least one during-heavy-work snapshot per §14.2 before the §14.4 P5 gate can be satisfied as completed. The OPS-03 investigation recorded earlier in this section had surfaced a stronger evidence pattern of memory pressure plus a UI hang than of any X10 Pro storage fault for the 2026-05-13 ungraceful reboot.
- **Method:** Read-only inspection only. No setting change, no app killing, no cleanup tool, no OS tuning, no swap / sleep change, no Backblaze / Time Machine / drive / network change. Tools per §14.2: `uptime`, `memory_pressure`, `vm_stat`, `sysctl vm.swapusage`, `top -l 1 -n 15 -o mem`, `last reboot`, and a 24-hour incident scan of `/Library/Logs/DiagnosticReports`. The validation workload was the repository's normal pre-commit gate (`python -m pre_commit run --all-files` from the project's pinned Python 3.12 `.venv`). Raw snapshot output, process lists, and screenshots were stored locally on the operator's hardware and are deliberately **not** committed to this repository, consistent with §14.2.4 and §7.
- **Findings (summary statistics only; raw snapshots not committed per §14.2.4 / §7):**
  - **Boot session:** continuous since 2026-05-13 19:43 CDT (the post-panic boot). Uptime at BEFORE snapshot: 3 days 8 hours 38 minutes. No ungraceful reboot during the cycle.
  - **Swap stayed at 0 MB across BEFORE, DURING_PEAK, and AFTER.** `sysctl vm.swapusage` reported `total=0M used=0M free=0M` at all three samples. The lifetime `Swapins / Swapouts` counters stayed at `0 / 0` throughout.
  - **Compressor decreased across the cycle.** BEFORE: 8,719 MB occupied. DURING_PEAK: 7,931 MB. AFTER: **5,737 MB**. Net release of approximately 2,982 MB of compressed memory across the cycle. Pages-stored-in-compressor fell from 1,155,124 (BEFORE) to 927,610 (AFTER). The lifetime compressions counter rose by approximately 41,571 pages (≈ 650 MB) during the workload and then **stopped** during the AFTER window; the decompressions counter rose by approximately 148,928 pages (≈ 2.3 GB) during the AFTER window, indicating the kernel was actively pulling compressed pages back into active RAM during recovery.
  - **Physical memory headroom grew during the workload.** BEFORE unused: 1,357 MB. DURING_PEAK unused: 5,052 MB. AFTER unused: 4,953 MB. The kernel responded elastically to the workload by reclaiming inactive / purgeable memory.
  - **CPU briefly loaded.** BEFORE idle: 68%. DURING_PEAK idle: **8.5%** (caught mid-run, with thirteen `detect-secrets-hook` Python workers each at ~55–65% CPU). AFTER idle: 73%. The full workload (`pre-commit run --all-files`) completed in approximately 3 seconds wall-clock against the repository's pre-warmed `~/.cache/pre-commit/` cache; the brief CPU spike did not translate into memory pressure.
  - **No new incident signals in the last 24 hours.** Zero new `JetsamEvent-*.ips`, zero new `*hang*.ips` / `*.hang`, zero new `*panic*` / `Kernel_*` artifacts in `/Library/Logs/DiagnosticReports`. The most recent isolated `JetsamEvent` (2026-05-15 17:35 CDT) remains noise per §14.3 ("A single isolated `JetsamEvent` is noise; recurrence is a signal"). The most recent hang (`NotificationsSettings_2026-05-13-194248`) is the pre-panic May 13 event already recorded.
- **§14.3 escalation check** (each criterion evaluated against the snapshot evidence):
  - Recurring `JetsamEvent` artifacts (≥ 2 in any 7-day window since baseline): **not tripped** — zero in the last 24 hours.
  - Sustained swap pressure: **not tripped** — swap at 0 MB and zero swap activity across all three snapshots.
  - Sustained compressed-memory pressure: **not tripped** — compressor decreased materially across the cycle.
  - Repeated non-storage UI hangs: **not tripped** — zero new hang reports in the last 24 hours.
  - Another ungraceful reboot: **not tripped** — continuous boot session since 2026-05-13 19:43 CDT.
- **Conclusion:** The Mac Studio handled the validation workload elastically. None of the five §14.3 escalation signals are tripped at the time of the measurement. Running the pre-commit gate produced a brief CPU spike but **reduced** the kernel's compressor pressure rather than increasing it.
- **Resulting state:** The OPS-04 §14.4 P5 gate is **satisfied as of 2026-05-17** by this dated §5.6 entry. The baseline established here is a point-in-time record; per §14.2.5 it must be re-established after any material change in routinely-running apps, after any macOS major upgrade, after any new external device connection, or after any future ungraceful reboot. Satisfying §14.4 alone does not authorize P5 — every other §10 unresolved risk and every other authorization required by `AI_WORKFLOW.md` §7 continues to apply.
- **Authorization of record:** `governance/authorizations/2026-05-17_ops-04b.md`.
- **What this entry proves:** Within the scope of one measurement cycle on 2026-05-17, no §14.3 escalation signal is tripped and the OPS-04 §14.4 P5 gate is procedurally satisfied as completed.
- **What this entry does not prove:** It does not prove memory health beyond this single dated cycle, does not exempt future operator sessions from re-baselining per §14.2.5, does not authorize P5, does not authorize any setting change, app killing, cleanup tool, OS tuning, hardware decision, Backblaze / Time Machine / drive / network change, or any successor packet. It does not extend or close any other §10 unresolved risk.

---

## 6. Mac Studio Sync Procedure

The Mac Studio working tree is the most frequent point of operator interaction. It is also the layer most likely to drift from `main`. The following procedure keeps it safe.

1. **At the start of every session:**
   - `git fetch origin`
   - `git status` — confirm clean tree, confirm current branch.
   - If on `main`: `git pull --ff-only origin main`. If the pull is not a fast-forward, **stop** and investigate; do not force.
   - If on a feature branch: confirm the branch is intentional and rebase or merge from `main` only with explicit operator intent.
2. **Before starting new work:**
   - Confirm `main` is current (per step 1).
   - Create a fresh feature branch from `main` with a clear dated or scope-named slug.
3. **Before powering down:**
   - Commit or stash every meaningful local change.
   - Push every commit on every branch that contains unpushed work.
   - `git status` reports clean. `git log origin/<branch>..HEAD` reports empty for every active branch.
4. **If the Mac checkout is behind current `main`** (as observed on 2026-05-16):
   - Do **not** start new work on the stale checkout.
   - Sync first, per step 1. If GitHub reachability fails (also observed on 2026-05-16), repair reachability first (§9) — do not begin work against a stale tree.
5. **If a destructive local action is suspected:**
   - Stop immediately. Do not `git push`. Do not `git reset --hard`.
   - Recover from Time Machine (Layer 3) to the most recent known-good state, then resume from §5 if needed.

---

## 7. Local-Only Forbidden Artifacts

The repository's safety posture requires that certain categories of artifact **never** appear in the working tree, **never** be committed, and **never** be backed up via repository layers. They have no place in the project, regardless of which device is being used.

Forbidden categories (consistent with the merged P2-01..P2-05 / P3-03..P3-05 / P4-06..P4-08 authorizations):

- **Secrets and credentials.** API keys, broker keys, session tokens, OAuth tokens, SSH keys, `.env` files containing live credentials, anything matching the patterns in `.secrets.baseline` and the `detect-secrets` pre-commit hook.
- **Broker artifacts.** Broker SDKs, broker account identifiers, order objects, fills, positions, executions, trade reports, order books.
- **Market data.** Quotes, bars, ticks, symbol universes, vendor feeds, vendor-licensed datasets.
- **Live or paper trading runtime.** Any `__main__`, daemon, scheduler, background thread, long-running service, persistent storage, env-var or secrets loading, network call, `time.sleep`, or `asyncio.sleep`.
- **Strategy / scanner / model / portfolio / backtest content.** Any concrete implementation of a strategy, scanner, model, portfolio, or backtest beyond the merged inert pytest-only surfaces.
- **Concrete protocol implementations** of `HeartbeatProtocol`, `KillSwitchProtocol`, or `ReconciliationProtocol` outside the merged P3-03 / P3-04 / P3-05 in-memory fakes.

If any forbidden artifact is ever observed locally:
- Do **not** commit. Do **not** push.
- Remove the artifact from the working tree.
- If it has already been committed (it should not have been, given the pre-commit gate), treat it as an incident, halt further work, and consult the relevant authorization process before any remediation that touches `main`.

---

## 8. Observed Local Facts — 2026-05-16

These facts are recorded from the read-only Mac Studio check that motivated this OPS-01 packet. They are a snapshot, not a standing claim.

- **Mac Studio checkout is behind current GitHub `main`.** The local working tree on the Mac Studio is not at the current `main` head. Action: sync per §6 step 1 before starting new work.
- **Time Machine is active on the LaCie.** Layer 3 is operating. No setting change is authorized by this packet.
- **Seagate X10 Pro is mounted and selected in Backblaze.** The X10 Pro is currently behaving as a Backblaze-included drive rather than as an offline rotating cold copy. This is acceptable as a transitional state; the eventual Layer 5 role (offline rotation) is a future operator-side action.
- **Seagate X10 Pro panic-history investigation completed and recorded.** A read-only investigation on 2026-05-16 (see §5.6) characterized the 2026-05-13 19:43 CDT ungraceful reboot. By the available 14-day evidence, the reboot is **not directly tied** to the X10 Pro; the stronger evidence pattern points to memory pressure plus a UI hang followed by a hard restart. The X10 Pro remains acceptable in its current Backblaze-included online role and is **not** promoted to Layer 5 by that investigation; the remaining gaps (no SMART visibility through the USB enclosure, `Owners: Disabled`, FileVault not enabled, and only 14 days of clean log evidence) are recorded in §5.6 and §10.
- **Backblaze is installed and, as of 2026-05-16, restore-proven for one non-sensitive project file.** Layer 4 was exercised by a real restore of `docs/decisions/ADR-004_utc_discipline.md` (2,288 bytes; SHA-256 `e9b335b77fb0ee520a47fa2d2e413fcb176355a6e71df619c4d392d3f4f93535`) that matched the original byte-for-byte; see §5.5 for the recorded drill and `governance/authorizations/2026-05-16_ops-02.md` for the authorization of record. Broader Backblaze claims (multiple files, larger artifacts, rotation across time) remain unverified at this scope.
- **Mac DNS / GitHub reachability failed during the check.** Layer 1 was unreachable from the Mac Studio at the time of the check. Action: repair reachability (§9) before any work that requires `git fetch`, `git push`, or `gh` operations.

None of these observed conditions are emergencies. All are addressable by the safe next actions in §9.

---

## 9. Safe Next Actions (Operator-Side, Not Authorized by This Packet)

These actions are named for clarity. They are **operator-side actions** that Kevin performs on his own hardware. They are **not** authorized by this packet and are **not** executed by any agent. Each requires the operator's own judgment at the time of execution; nothing here authorizes a destructive operation, a setting change, or a successor work packet.

### 9.1 GitHub reachability (Layer 1)

- Confirm the Mac Studio has working DNS resolution for `github.com`.
- Confirm `ssh -T git@github.com` (or the HTTPS equivalent via `gh auth status`) reports a working credentialed connection.
- If reachability remains broken, escalate to network repair before resuming any push / pull work.

### 9.2 LaCie Time Machine (Layer 3)

- Confirm Time Machine is still active and that the most recent successful backup timestamp is recent.
- No setting change is authorized.

### 9.3 Backblaze (Layer 4)

- The single-file restore drill described here was performed on 2026-05-16 and succeeded; see §5.5 for the recorded drill and `governance/authorizations/2026-05-16_ops-02.md` for the authorization of record. Layer 4 is **restore-proven for one non-sensitive project file as of 2026-05-16**.
- Recurring or broader drills (different files, larger artifacts, older snapshots, drills on later dates) are operator-side actions that each remain **not authorized** by any prior packet; each requires its own separate written authorization from Kevin at the time it is performed.
- No setting change is authorized.

### 9.4 Seagate X10 Pro (Layer 5)

- Only after Layer 4 is proven healthy: establish an offline rotation discipline (connect → snapshot → disconnect → store offline → rotate). Document the cadence in a future operations note.
- Until Layer 4 is proven healthy, treat the X10 Pro as a Backblaze-included drive (its current observed state).
- A read-only X10 Pro panic-history investigation was performed on 2026-05-16 and is recorded at §5.6. By the available 14-day evidence, the 2026-05-13 ungraceful reboot is not directly tied to the X10 Pro; the X10 Pro remains acceptable in its current Backblaze-included online role and is **not** promoted to Layer 5 by that investigation. The recommended next gates before any future Layer 5 promotion (30-day clean observation window, SMART-visibility decision, encryption / ownership decision, and a cold restore drill) are listed in §5.6 and each remains an operator-side action that requires its own separate written authorization from Kevin.
- No formatting, repartitioning, or repair action is authorized.

### 9.5 Mac Studio working tree

- Sync to current `main` per §6 step 1 before resuming work.
- If a destructive local action is suspected, recover from Time Machine (§3.3) before any further git operation.

---

## 10. Unresolved Risks at This Checkpoint

- **Backblaze health is proven only for a single non-sensitive file as of 2026-05-16.** The §5.5 restore drill resolves the "Backblaze not yet proven healthy" risk recorded at the OPS-01 checkpoint at the scope of one file on that date. Broader Backblaze health (multiple files, larger artifacts, rotation across time) remains unverified at this scope; each broader drill is a separate operator-side action with its own separate written authorization.
- **The X10 Pro is not yet acting as an offline rotating cold copy.** Layer 5 is therefore not yet contributing. Layer 4 is now restore-proven at the §5.5 scope, and the 2026-05-16 X10 Pro panic-history investigation recorded at §5.6 finds no storage-layer evidence tying the 2026-05-13 ungraceful reboot to the X10 Pro by the available 14-day record (the stronger evidence pattern points to memory pressure plus a UI hang followed by a hard restart). The X10 Pro nevertheless remains **not yet promoted** to Layer 5 because four independent gaps remain: (i) no SMART visibility through the USB enclosure, (ii) `Owners: Disabled` on the volume, (iii) FileVault not enabled on the volume, and (iv) only 14 days of clean log evidence on hand. Establishing a Layer 5 offline rotation discipline remains an operator-side action that is **not authorized** by this packet and requires its own separate written authorization from Kevin.
- **GitHub reachability was failing from the Mac Studio at the time of the read-only check.** Until reachability is repaired, the Mac Studio cannot benefit from Layer 1.
- **The Mac checkout was behind current `main` at the time of the read-only check.** Until it is synced, any local work risks being authored against stale governance.
- **The recovery drill (§5) has not yet been performed against this RECOVERY.md.** The drill is described and required, but is itself a future operator-side action.
- **Mac Studio memory-pressure baseline established on 2026-05-17.** The OPS-04 §14.2 measurement cycle was performed on 2026-05-17 and is recorded as a dated entry at §5.6. None of the five §14.3 escalation signals were tripped at the time of the measurement (swap stayed at 0 MB across BEFORE / DURING_PEAK / AFTER snapshots; compressor occupancy decreased ~2,982 MB across the cycle; no new `JetsamEvent`, hang, or panic artifacts in the prior 24 hours); the OPS-04 §14.4 P5 gate is procedurally satisfied as completed as of 2026-05-17. Per §14.2.5 the baseline is a point-in-time record and must be re-established after any material change in routinely-running apps, after any macOS major upgrade, after any new external device connection, or after any future ungraceful reboot. The baseline being established does not, on its own, authorize P5; the §14.4 gate becoming satisfied only removes one procedural blocker.

None of these risks individually breach the no-single-point-of-failure standard, because the source of truth (Layer 1) is intact and at least one local recovery layer (Layer 3, Time Machine on LaCie) is active. Together, however, they are why this checkpoint exists: each risk has a named safe next action in §9, and each will be addressed in its own time outside the scope of this docs-only packet.

---

## 11. What This Document Does Not Do

This document is doctrine. It does not, by being merged:

- Open or authorize any P5 work, including local/paper simulation boundary planning.
- Open or authorize any successor Phase 4 work (P4-09 or later).
- Execute any backup, restore, drill, formatting, repair, or setting change on any device.
- Modify any file under `src/**` or change any test behavior.
- Extend the `MASTER_STATUS.md` §8 step 4a `allowed_p2_infra` allowlist.
- Change the safety foundation closure recorded by P4-08.

Any change to those items requires its own separate written authorization from Kevin per `AI_WORKFLOW.md` §7.

---

## 12. References

- `governance/authorizations/2026-05-16_ops-01.md` — authorization of record for the OPS-01 project resilience checkpoint that established this document.
- `governance/authorizations/2026-05-16_ops-02.md` — authorization of record for the 2026-05-16 Backblaze single-file restore drill recorded in §5.5.
- `governance/authorizations/2026-05-16_ops-04.md` — authorization of record for the OPS-04 memory-pressure baseline plan and OPS roadmap recorded in §13 and §14.
- `governance/authorizations/2026-05-17_ops-04b.md` — authorization of record for the 2026-05-17 OPS-04 memory-pressure measurement cycle recorded in §5.6 and reflected at §14.4.
- `governance/authorizations/2026-05-16_p4-08.md` — safety foundation closure (preserved unchanged).
- `AI_WORKFLOW.md` §7 (authorization of record), §4 (Mode A scope), §1.4 / §6 rule 2 (status keeper).
- `docs/decisions/ADR-001_secrets_management.md`, `ADR-002_kill_switch.md`, `ADR-003_reconciliation.md`, `ADR-004_utc_discipline.md`, `ADR-005_heartbeat.md`, `ADR-006_deployment_logs.md`, `ADR-007_minimal_ci.md`, `ADR-008_monitoring_cadence_and_ai_monitor_role.md`, `ADR-009_runtime_monitoring_cadence.md`.
- `MASTER_STATUS.md` (current phase state).
- `pyproject.toml` (pinned Python 3.12 toolchain and dev dependencies used in the §5 drill).
- `.pre-commit-config.yaml` (the validation gate referenced in the §5 drill).

---

## 13. OPS Roadmap

This section makes the operational-resilience packet sequence explicit so that no OPS item is implicit, lost, or assumed. Each item is dated, scoped, and either complete (with the merging PR named), current/pending (this packet), or future / not authorized. Future items are listed for sequencing visibility only; each future item continues to require its own separate written authorization from Kevin at the time it is initiated.

- **OPS-01 — Project resilience checkpoint.** Status: **complete** (merged in PR #99 on 2026-05-16). Authorization of record: `governance/authorizations/2026-05-16_ops-01.md`. Scope: established this `RECOVERY.md` document, the 3-2-1-1-0 layer model, the recovery drill, the Mac Studio sync procedure, the local-only forbidden-artifact discipline, the observed local facts, and the original unresolved-risk list.
- **OPS-02 — Backblaze single-file restore drill.** Status: **complete** (merged in PR #100 on 2026-05-16). Authorization of record: `governance/authorizations/2026-05-16_ops-02.md`. Scope: recorded the 2026-05-16 single-file restore of `docs/decisions/ADR-004_utc_discipline.md` from Backblaze with byte-for-byte verification; resolved the "Backblaze not yet proven healthy" risk at the §5.5 single-file scope. Recorded at §5.5.
- **OPS-03 — Seagate X10 Pro panic-history investigation.** Status: **complete** (merged in PR #101 on 2026-05-16). Authorization of record: `governance/authorizations/2026-05-16_ops-03.md`. Scope: recorded the 2026-05-16 read-only investigation of the 2026-05-13 19:43 CDT ungraceful reboot; found no direct evidence tying the X10 Pro to the reboot within the 14-day window; recorded the four remaining gaps blocking Layer 5 promotion. Recorded at §5.6.
- **OPS-04 — Memory-pressure baseline and OPS roadmap (this packet).** Status: **current / pending**. Authorization of record: `governance/authorizations/2026-05-16_ops-04.md`. Scope: this §13 roadmap and the §14 memory-pressure baseline procedure (procedure definition only; the baseline measurement itself is an operator-side action that is **not authorized** by this packet). Establishes the P5 gate at §14.4.
- **OPS-05 — Seagate X10 Pro Layer 5 promotion decision.** Status: **future / not authorized**. No prior packet authorizes this. Scope (provisional, for sequencing visibility only): a separate, written, operator-authorized decision on whether to promote the X10 Pro to Layer 5 (offline / rotating cold copy), which will require resolving the four remaining gaps recorded in §5.6 / §10 (no SMART visibility through the USB enclosure, `Owners: Disabled`, FileVault not enabled, only 14 days of clean log evidence at the time of OPS-03) before promotion. OPS-05 is **not** authorized by any prior packet and continues to require its own separate written authorization from Kevin.
- **OPS-06 — Recurring backup verification cadence.** Status: **future / not authorized**. No prior packet authorizes this. Scope (provisional, for sequencing visibility only): a separate, written, operator-authorized cadence for recurring restore drills across the Backblaze layer (different files, larger artifacts, older snapshots, drills on later dates) and the Time Machine layer, expressed as calendar discipline consistent with the §5.4 cadence. OPS-06 is **not** authorized by any prior packet and continues to require its own separate written authorization from Kevin.
- **OPS-07 — Clean-directory or clean-machine disaster-recovery drill.** Status: **future / not authorized**. No prior packet authorizes this. Scope (provisional, for sequencing visibility only): a separate, written, operator-authorized end-to-end execution of the §5 "Fresh Clone From Cold" drill on a clean directory (and, optionally, on a clean machine), recorded as a dated entry under §5.5 / §5.6 with the artifacts and the pass / fail outcome. OPS-07 is **not** authorized by any prior packet and continues to require its own separate written authorization from Kevin.

This roadmap is a sequence, not a schedule. No date commitment is implied for any future OPS item. OPS items may be reordered, expanded, contracted, retitled, or withdrawn by a separate, written, operator-authorized packet at any time. P4-09, P5-01, local/paper simulation boundary planning, broker integration, market-data ingestion, strategy/scanner/model/portfolio/backtest content, and any trading runtime remain future / not authorized by every OPS packet listed here.

---

## 14. OPS-04 Memory-Pressure Baseline Procedure

This section defines (in documentation only) the operator-side procedure for establishing a Mac Studio memory-pressure baseline before P5 simulation work begins. The procedure is read-only; it makes no setting change, kills no app, runs no cleanup automation, tunes no OS parameter, and makes no hardware decision. The procedure is **not** executed by this document and is **not** authorized to be performed automatically by any agent.

### 14.1 Why this baseline exists

The 2026-05-13 19:43 CDT ungraceful reboot recorded at §5.6 had a stronger evidence pattern for **memory pressure plus a UI hang** than for any X10 Pro storage fault. Twelve `JetsamEvent-2026-05-13-*.ips` artifacts between 10:21 and 17:04 CDT on that day record macOS forcibly killing processes for memory; a 28-second `NotificationsSettings` UI hang ended 19:42:30 CDT (immediately before the ungraceful reboot at 19:43); and no storage-stack evidence implicating the X10 Pro was found in the 14-day kernel record.

The Mac Studio is the operator's primary working machine for `gmc-rebuild`. P5 work (local/paper simulation, when authorized) will plausibly increase memory load on this machine. Before P5 begins, the operator should know what "normal" memory pressure looks like on the Mac Studio during everyday work and during heavy work, so that future drift toward jetsam-prone conditions can be recognized early — before another ungraceful reboot. The OPS-04 baseline exists for exactly that purpose: it does **not** prevent a memory event, it makes the precondition for one observable.

### 14.2 Read-only baseline procedure

This procedure is an **operator-side action** that Kevin performs on his own hardware. It is described here only so that it is reproducible and so the pass / fail / escalation criteria at §14.3 are anchored to a real measurement.

1. **Before-heavy-work snapshot.** With the operator's usual idle-session set of apps running but no deliberately heavy task (no test suite, no build, no large file scan, no large model load, no batch download / upload), capture and save (locally, outside this repository) a snapshot of:
   - `vm_stat` (one sample is enough).
   - `memory_pressure` (one sample is enough).
   - `top -l 1 -o mem -n 30` (top 30 processes by resident memory; one sample is enough).
   - Activity Monitor → "Memory" tab screenshot or a copy of the visible columns (memory used, swap used, memory pressure indicator, top memory consumers).
   - The current uptime (`uptime`) and the current `last reboot | head -3` output to anchor the snapshot to a specific boot session.
2. **During-heavy-work snapshot.** With a deliberately heavy task running (for example, `python -m pre_commit run --all-files` in this repository on a freshly cloned working tree, or any other heavy task the operator would realistically run during a working session), capture and save the same five items as above. Take the snapshot while the heavy task is still running, not afterward.
3. **After-heavy-work snapshot (optional).** A third snapshot taken five to ten minutes after the heavy task has completed and the system has been allowed to settle. This makes recovery vs. residual pressure observable.
4. **Storage.** Snapshots are stored on the operator's own hardware, **outside** this repository (consistent with §7 — no operator-side measurement artifact, screenshot, or log dump is ever committed to this repository). The snapshots are records for the operator's own use; they are not governance artifacts.
5. **Re-baseline cadence.** A baseline is a point-in-time record. Re-baseline whenever the apps the operator routinely runs change materially, after any macOS major version upgrade, after any new external device is connected, or after another ungraceful reboot. Each re-baseline is itself an operator-side action governed by this §14.2 procedure.

This procedure explicitly does **not** include: changing any system setting, killing any app, running any memory-cleanup or "memory cleaner" tool, tuning any OS parameter, changing swap configuration, changing any Backblaze or Time Machine setting, ejecting / mounting / unmounting any drive, or making any hardware-buy / hardware-replace decision from a single baseline sample. Each of those is its own operator-side action that requires its own separate written authorization from Kevin and is **not** covered by this packet.

### 14.3 Escalation criteria

A single snapshot establishes a baseline. It is not enough to make a hardware decision and is not enough to revise the §10 risk list. Escalation begins only when the operator observes one or more of the following signals **after** the baseline has been established and **across more than one observation**:

- **Recurring `JetsamEvent` artifacts.** Two or more new `JetsamEvent-*.ips` files in `/Library/Logs/DiagnosticReports` within any rolling seven-day window after the baseline is taken. (A single isolated `JetsamEvent` is noise; recurrence is a signal.)
- **Sustained swap pressure.** `vm_stat` consistently reporting non-trivial swap-in / swap-out rates during idle work, or Activity Monitor's swap-used figure trending materially higher across multiple observations than the baseline showed during equivalent work.
- **Sustained compressed-memory pressure.** `vm_stat` page-compression / decompression counters or Activity Monitor's "Compressed" figure trending materially higher than baseline across multiple observations under equivalent work.
- **Repeated UI hangs.** Two or more new `*hang*.ips` (or `_Kevins-Mac-Studio.hang`) reports in `/Library/Logs/DiagnosticReports` within any rolling seven-day window after the baseline is taken whose hang stack does **not** clearly originate in storage code (a storage-rooted hang escalates separately under §9.4 / §5.6).
- **Another ungraceful reboot.** A new `last` entry showing a `reboot` time without a paired `shutdown` time, or a new `loginwindow` `previousStartupWasAPanicOrHardRestart` flag.

When any escalation signal triggers, the next step is a separate, written, operator-authorized investigation packet in the OPS-03 shape (a read-only investigation that characterizes the trigger before any decision). That follow-up is **not** authorized by this packet and is **not** assumed to happen on any schedule.

### 14.4 P5 gate

Phase 5 (local/paper simulation, when authorized) **may proceed only after** OPS-04 is either:

- **Completed**, meaning the operator has taken at least one before-heavy-work snapshot and at least one during-heavy-work snapshot per §14.2 and has stored them locally outside this repository, with the result recorded as a dated note in §5.6 (Recorded Investigations) under its own future written authorization (OPS-05 / OPS-06 / OPS-07 or a separately numbered packet); **or**
- **Explicitly waived** by Kevin in a separate, written, dated authorization that names this §14.4 gate and accepts the residual memory-pressure risk.

**Status as of 2026-05-17:** The "Completed" condition is **satisfied** by the dated §5.6 entry "2026-05-17 — Mac Studio (Layer 2), OPS-04 memory-pressure measurement cycle" recorded under `governance/authorizations/2026-05-17_ops-04b.md`. The §14.4 procedural blocker is therefore removed as of 2026-05-17. Per §14.2.5 the baseline is a point-in-time record; if material conditions change (apps, macOS upgrade, new external device, ungraceful reboot), §14.4 must be re-satisfied by a new measurement cycle and a new dated §5.6 entry under its own separate written authorization.

Until one of those two conditions holds, P5 remains future / not authorized regardless of any other gate's state. This gate is additive to — not a replacement for — every other §10 unresolved risk and every other authorization required by `AI_WORKFLOW.md` §7. Satisfying §14.4 alone does not authorize P5; it only stops being a blocker.
