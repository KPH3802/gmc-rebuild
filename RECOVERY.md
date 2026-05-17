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
- `governance/authorizations/2026-05-16_ops-03.md` — authorization of record for the 2026-05-16 Seagate X10 Pro panic-history investigation recorded in §5.6.
- `governance/authorizations/2026-05-16_ops-04.md` — authorization of record for the OPS-04 memory-pressure baseline plan and OPS roadmap recorded in §13 and §14.
- `governance/authorizations/2026-05-17_ops-04b.md` — authorization of record for the 2026-05-17 OPS-04 memory-pressure measurement cycle recorded in §5.6 and reflected at §14.4.
- `governance/authorizations/2026-05-17_p5-01.md` — authorization of record for the P5-01 inert local simulation boundary skeleton (first Phase 5 implementation task; recorded in §13).
- `governance/authorizations/2026-05-17_gov-01.md` — authorization of record for the GOV-01 governance cleanup, risk register, and backup monitoring plan recorded in §15, §16, and §17, and reflected at §13.
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
- **OPS-04 — Memory-pressure baseline and OPS roadmap.** Status: **complete** (merged in PR #102 on 2026-05-16). Authorization of record: `governance/authorizations/2026-05-16_ops-04.md`. Scope: this §13 roadmap and the §14 memory-pressure baseline procedure (procedure definition only). Establishes the P5 gate at §14.4.
- **OPS-04B — Memory-pressure measurement record.** Status: **complete** (merged in PR #103 on 2026-05-17). Authorization of record: `governance/authorizations/2026-05-17_ops-04b.md`. Scope: dated §5.6 entry recording the 2026-05-17 OPS-04 measurement cycle and satisfying the §14.4 P5 gate.
- **P5-01 — Inert local simulation boundary skeleton.** Status: **complete** (merged in PR #104 on 2026-05-17; sibling Mode B monitoring packet merged in PR #105 first). Authorization of record: `governance/authorizations/2026-05-17_p5-01.md`. Scope: first Phase 5 implementation task — adds the `src/gmc_rebuild/simulation/` subpackage (closed `SimulationLane`, immutable `SimulatedIntent`, `SimulationBoundary` that gates intents on `SafetyVerdict.clear`) and the matching `tests/simulation/` test package. Inert: never submits, routes, executes, persists, schedules, or connects.
- **GOV-01 — Governance cleanup, risk register, and backup monitoring plan (this packet).** Status: **current / pending merge**. Authorization of record: `governance/authorizations/2026-05-17_gov-01.md`. Scope: (a) syncs the `MASTER_STATUS.md` §8 step 4a `allowed_p2_infra` bash gate to include `src/gmc_rebuild/runtime` (PR P4-06) and `src/gmc_rebuild/simulation` (PR P5-01) so the bash gate matches `tests/test_package_skeleton.py` and the actual authorized tree; (b) refreshes the stale `MASTER_STATUS.md` "Current work packet" header and the stale `plan/phase4_entry_plan.md` §4 closing paragraph; (c) introduces the §15 "No Chat-Only Risk Rule"; (d) adds the §16 "Risk Register / Future Controls" section covering OPS-05 / OPS-06 / OPS-07, repository and account hygiene, device and data security, secrets and credential policy, simulation scope creep controls, workflow and governance hardening, and release / tag policy; (e) defines the §17 "OPS-06 Backup Verification & Monitoring Plan" with read-only check set, escalation thresholds, escalation responses, cadence recommendations, and explicit non-authorizations. Implements no monitoring automation; defines plan and rules only.
- **OPS-05 — Seagate X10 Pro Layer 5 promotion decision.** Status: **future / not authorized**. No prior packet authorizes this. Scope (provisional, for sequencing visibility only; see also the §16.1 Risk Register entry): a separate, written, operator-authorized decision on whether to promote the X10 Pro to Layer 5 (offline / rotating cold copy), which will require resolving the four remaining gaps recorded in §5.6 / §10 (no SMART visibility through the USB enclosure, `Owners: Disabled`, FileVault not enabled, only 14 days of clean log evidence at the time of OPS-03) before promotion. OPS-05 is **not** authorized by any prior packet and continues to require its own separate written authorization from Kevin.
- **OPS-06 — Recurring backup verification cadence.** Status: **plan documented at §17 by GOV-01; cadence execution is operator-side and not yet authorized**. Authorization of record for the plan: `governance/authorizations/2026-05-17_gov-01.md`. Scope (per §17): a separate, written, operator-authorized cadence for recurring backup-health checks (GitHub reachability, Time Machine recency, Backblaze daemon state, Backblaze selected-volume visibility, Backblaze backlog and last-success thresholds, X10 Pro mount / storage / panic watch, and periodic byte-for-byte restore drills) with the escalation matrix defined at §17.3 and §17.4. Execution remains an operator-side action that requires its own separate written authorization at the time it is performed; this document defines the plan, not the schedule.
- **OPS-07 — Clean-directory or clean-machine disaster-recovery drill.** Status: **future / not authorized**. No prior packet authorizes this. Scope (provisional, for sequencing visibility only; see also the §16.1 Risk Register entry): a separate, written, operator-authorized end-to-end execution of the §5 "Fresh Clone From Cold" drill on a clean directory (and, optionally, on a clean machine), recorded as a dated entry under §5.5 / §5.6 with the artifacts and the pass / fail outcome. OPS-07 is **not** authorized by any prior packet and continues to require its own separate written authorization from Kevin.

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

---

## 15. No Chat-Only Risk Rule

This rule is doctrine. It exists because chat conversations are ephemeral and not part of the source of truth (§2): a risk that is only ever named in a chat transcript and never captured in the repository will eventually be lost. Lost risks are how preventable incidents happen.

**The rule.** Any material risk, deferred control, future gate, operational concern, or "remember this later" item identified by Kevin, by any AI collaborator (Codex, Perplexity Computer, Backup AI, or any other), or by any reviewer **must be captured in the repository before the next implementation packet begins**. "Captured in the repository" means at least one of the following:

- A new or updated entry in §16 "Risk Register / Future Controls" with status, trigger, rule, and (where applicable) owner.
- A new bullet in §10 "Unresolved Risks at This Checkpoint".
- A new dated entry in §5.5 "Recorded Restore Drills" or §5.6 "Recorded Investigations".
- A new top-level numbered section in this document, if the concern is large enough to merit one.
- A new ADR under `docs/decisions/` (per `AI_WORKFLOW.md` §7) when the concern is an architecture decision.
- A new authorization artifact under `governance/authorizations/` when the concern is the basis of a new bounded packet.

**What "before the next implementation packet" means.** "Implementation packet" is any PR that adds or modifies code under `src/**` or `tests/**`, or any PR that performs an operator-side action (a backup execution, a restore drill, a hardware change, a setting change). A docs/governance-only PR like this one is not itself an implementation packet, so a deferred risk surfaced during this PR's review may itself be captured as part of the same PR or as a sibling docs-only follow-up — but it must be captured before the next code or operator-side action lands.

**What this rule does not require.** This rule does not require that the risk be resolved before the next implementation packet; only that it be captured. Resolution may itself require its own separate written authorization (e.g., an OPS-05 X10 Layer 5 promotion decision is captured here as a Risk Register entry; closing it is a separate future packet that Kevin authorizes separately).

**What this rule does not authorize.** This rule does not authorize any new operator-side action, any setting change, any hardware change, any device touch, any Backblaze / Time Machine / drive / network change, any broker integration, any market-data ingestion, any order placement, any persistence, any scheduler, any daemon, any runtime activation, any tag, or any release. It is a discipline rule about capture, not an authorization for any specific successor action.

**How this rule fails safely.** If a risk is surfaced and the operator is not certain whether it merits a §16 entry, an §10 bullet, or some other capture form, the failsafe is to **capture it anyway** — preferably in §16 with status `unknown / needs triage` — rather than letting it live only in chat. A spurious or duplicate Risk Register entry is recoverable by a future docs-only cleanup packet; a forgotten one is not.

---

## 16. Risk Register / Future Controls

This section is a structured record of deferred controls, open operational concerns, and future gates that are not yet closed. Each entry has a **status** (the current state of the entry), a **trigger** (the event or condition that would activate or escalate the entry), a **rule** (what is required if and when the entry is acted on), and where applicable an **owner** (the role accountable for the entry — almost always Kevin as operator).

Entries here are records, not authorizations. Acting on any entry — closing it, escalating it, opening a successor packet — continues to require its own separate written authorization from Kevin per `AI_WORKFLOW.md` §7. New entries are added under the §15 No Chat-Only Risk Rule; closed entries are not deleted but are annotated as such with the closing packet's authorization artifact named.

### 16.1 Operational backup and recovery (OPS-05 through OPS-07)

- **OPS-05 — Seagate X10 Pro Layer 5 promotion decision.** Status: **open / future / not authorized**. Trigger: any decision to begin treating the X10 Pro as a rotated offline cold copy (Layer 5 in §3.5). Rule: Layer 5 promotion requires resolving the four remaining gaps recorded in §5.6 and §10 — (i) no SMART visibility through the USB enclosure, (ii) `Owners: Disabled` on the volume, (iii) FileVault not enabled on the volume, (iv) only the 14-day clean log window from OPS-03 — and requires Kevin's separate written authorization at the time of promotion. Until then, the X10 Pro remains a Backblaze-included online drive (§5.6, §9.4). Owner: Kevin.
- **OPS-06 — Recurring backup-verification and monitoring cadence.** Status: **plan documented as §17 below; cadence execution is operator-side and not yet authorized**. Trigger: any operator-side execution of the §17 checks. Rule: §17 defines the per-check thresholds and the escalation matrix. Execution remains an operator-side action that requires its own separate written authorization at the time it is performed; this document defines the plan, not the schedule. Owner: Kevin.
- **OPS-07 — Clean-directory or clean-machine disaster-recovery drill.** Status: **described as §5 "Fresh Clone From Cold" since OPS-01; never actually performed**. Trigger: any operator-side execution of §5.1 against a clean directory (and, optionally, a clean machine). Rule: the drill is recorded as a dated entry under §5.5 / §5.6 with the artifacts and pass / fail outcome, under its own separate written authorization. Owner: Kevin.

### 16.2 Repository and account hygiene

- **Branch and remote hygiene.** Status: **deferred / no policy yet**. Trigger: any stale feature branch, stale monitoring branch, or stale ops branch persisting on the remote after its PR has merged. Rule: a future docs/governance-only packet should define a per-branch cleanup cadence (likely "stale ≥ 14 days after merge is candidate for deletion under separate authorization") and the policy for `gh` versus web-UI deletion. No branch deletion is authorized by this register entry; per `AI_WORKFLOW.md` §6 rule 1 and the standing destructive-action discipline, branch deletion requires its own separate written authorization. Owner: Kevin.
- **Local quarantine folder disposition.** Status: **open / undefined**. Trigger: any local-only file the operator wants to keep but never commit (e.g., raw OPS-04 snapshots, restore-drill artifacts, screenshots, third-party SDK downloads, vendor research notes). Rule: a future docs/governance-only packet should define where on the operator's hardware such artifacts live (e.g., `~/gmc-quarantine/` outside the repo working tree), how long they are retained, when they are deleted, and how their contents are kept off this repository (consistent with §7 forbidden-artifact discipline and §14.2.4). No quarantine-folder action is authorized by this entry. Owner: Kevin.
- **GitHub access, 2FA, and recovery codes.** Status: **partial — 2FA per `RECOVERY.md` §3.1 enabled; no documented recovery procedure on file**. Trigger: any GitHub access disruption (lost device, lost 2FA factor, compromised account, vendor-side outage). Rule: a future docs/governance-only packet should record (without storing any secret in the repository) where recovery codes physically live, how the operator regains access, the order-of-operations for re-enabling 2FA on a new device, and how the operator would prove ownership of the `KPH3802` account during recovery. No secret, recovery code, token, or credential is ever stored in this repository; the entry is about pointers and procedures, not contents. Owner: Kevin.
- **Personal-access-token (PAT) and SSH key hygiene.** Status: **open / no documented rotation cadence**. Trigger: any PAT issuance, rotation, revocation, or compromise. Rule: a future docs/governance-only packet should document the PAT scope rules (least-privilege per task, rotation cadence, where the token lives operator-side, when it is revoked), the SSH key inventory (which keys can push to `KPH3802/gmc-rebuild`, where they live, rotation cadence), and the breach-response runbook. No token, key, or credential is ever stored in this repository. Owner: Kevin.

### 16.3 Device and data security

- **Device security and FileVault posture.** Status: **partial — Mac Studio FileVault status is operator's own state; LaCie is FileVault-enabled per §5.6 baseline; X10 Pro is FileVault-disabled per §5.6 baseline**. Trigger: any change in the Mac Studio's FileVault state, any change to LaCie's encryption posture, any decision to encrypt or change-ownership on the X10 Pro. Rule: a future docs/governance-only packet should record the desired posture per device, the rationale, and the recovery story (where each device's FileVault recovery key physically lives, never in the repository). Layer 5 promotion of the X10 Pro per OPS-05 may require FileVault enablement; that decision is part of OPS-05. Owner: Kevin.
- **Backup encryption posture.** Status: **Backblaze is encrypted in transit and at rest per the Backblaze account configuration the operator established at install time**. Trigger: any decision to change the Backblaze personal encryption key (PEK), or any Backblaze-side change to encryption posture. Rule: PEK changes require a recorded operator-side action and a re-baseline of Backblaze (a new restore drill per §5.5 to prove the new key can still restore). No PEK is ever stored in this repository. Owner: Kevin.

### 16.4 Secrets, credentials, and external integration

- **Secrets and credential policy.** Status: **strict — `.secrets.baseline`, the `detect-secrets` pre-commit hook, and `ADR-001_secrets_management.md` codify the no-real-secrets discipline**. Trigger: any proposed addition under `src/**`, `tests/**`, `monitoring/**`, or `governance/**` that would read `os.environ`, `os.getenv`, a `.env` file, a credential store, or any external secret source. Rule: any such addition requires its own separate written authorization from Kevin, an ADR follow-up if it changes the secrets posture, and a `detect-secrets` baseline update. The default posture is: secrets do not exist in this repository, and code in this repository does not read secrets. Owner: Kevin.
- **External API / network integration policy.** Status: **strict — every existing subpackage's inertness test explicitly forbids `socket`, `urllib`, `requests`, `http`, `ssl`, `smtplib`, `ftplib` imports and `time.sleep` / `asyncio.sleep` usage**. Trigger: any proposed addition that would import a network library, call an external API, perform a DNS lookup, open a socket, or schedule any timed external action. Rule: any such addition requires its own separate written authorization, an ADR follow-up, and an extension of the relevant subpackage's inertness test to either declare the new surface as authorized or to continue forbidding it. The default posture is: this repository performs no network call, no external API call, no DNS lookup, and runs no scheduler / daemon / background thread. Owner: Kevin.

### 16.5 Simulation scope (P5 controls)

- **Simulation scope creep control.** Status: **closed at the P5-01 skeleton scope per `governance/authorizations/2026-05-17_p5-01.md`**. Trigger: any proposed change to `src/gmc_rebuild/simulation/` beyond the merged `__init__.py` and `_boundary.py`, any new module under that subpackage, any new symbol re-exported, any new field on `SimulatedIntent`, or any change to `SimulationBoundary.propose` semantics. Rule: any such change requires its own separate written authorization that explicitly names the new surface, the inertness tests to extend, and the safety-gate behaviour to preserve. The default posture is: the simulation subpackage stays at the P5-01 skeleton scope. Owner: Kevin.
- **`SimulationLane` expansion requires written authorization.** Status: **closed at one member (`LOCAL_ONLY`) per `governance/authorizations/2026-05-17_p5-01.md`**. Trigger: any proposed addition of a new `SimulationLane` member (for example a paper-broker lane, a backtest lane, a live lane, or any other). Rule: any such addition requires its own separate written authorization that explicitly names the new lane, the gates that the new lane must satisfy (`SafetyVerdict.clear`, separate broker authorization if applicable, separate market-data authorization if applicable, separate persistence authorization if applicable), and the test tripwires that the new lane must respect. The `tests/simulation/test_simulation_boundary.py::test_simulation_lane_has_only_authorized_values` test currently asserts `members == {"local_only"}`; any unauthorized addition fails this test. Owner: Kevin.
- **Order-intent semantics before symbol / side / quantity / price / venue / account fields.** Status: **closed at the `SimulatedIntent` placeholder shape per `governance/authorizations/2026-05-17_p5-01.md` — fields are limited to `lane`, `intent_id`, `created_at`**. Trigger: any proposed addition of a symbol, side, quantity, price, venue, account, routing instruction, or other order-shaped field to `SimulatedIntent` or any successor class. Rule: any such addition requires its own separate written authorization that explicitly names the new field, the validation rules, the inertness consequences (a field carrying real order content escalates the package out of the "inert placeholder" class), and the test extensions. Adding any one of these fields is **not** authorized by being similar to other authorized fields; each field is its own decision. Owner: Kevin.
- **Paper and live execution remain blocked until separately authorized.** Status: **blocked / future / not authorized**. Trigger: any proposed change that would cause `SimulationBoundary.propose` (or any successor surface) to **act on** the supplied intent rather than return it unchanged — for example, by calling out to a paper broker, by writing the intent to disk, by emitting a market-data subscription, or by routing the intent to any execution venue (paper or live). Rule: any such change requires its own separate written authorization that explicitly names the broker (paper or live), the integration shape, the kill-switch behaviour, the reconciliation cadence, the audit-trail expectations, and the rollback procedure. The current `SimulationBoundary.propose` contract — "returns the supplied intent unchanged (by identity) if and only if the boundary's lane matches the intent's lane and the supplied `SafetyVerdict.clear` is `True`, otherwise raises `SimulationBoundaryError`" — must continue to hold for the `LOCAL_ONLY` lane regardless of any new lane added under separate authorization. Owner: Kevin.

### 16.6 Workflow and governance hardening

- **Manual approval gates before external actions.** Status: **enforced by `AI_WORKFLOW.md` §6 rule 1 ("One builder at a time"), §6 rule 3 ("One approver" — Kevin), and §7 (authorization of record)**. Trigger: any proposed external-facing action — a `git push --force`, a branch deletion, a tag, a release, a Backblaze setting change, a Time Machine setting change, a drive action, a broker integration, a market-data subscription, an order, a persistence write, a network call, an env-var read — initiated by Codex, by Perplexity Computer, by the Backup AI, or by any other AI collaborator without an explicit per-action written approval from Kevin. Rule: the existing `AI_WORKFLOW.md` rules already forbid this, and the existing per-PR authorization discipline already records every authorized action; this Risk Register entry exists to make the rule discoverable from this document and to flag it as a recurring hardening priority. No new authorization is granted; the entry is a pointer to the existing rule. Owner: Kevin.
- **Append-only audit-trail hardening before paper / live.** Status: **partial — `src/gmc_rebuild/logging/` (P2-04) exposes a structured `audit_event` helper writing to the standard logger only; no append-only file, no signed log, no tamper-evident persistence exists yet**. Trigger: any decision to open a paper or live execution path (per the §16.5 "Paper and live execution" entry). Rule: paper or live execution requires a hardened append-only audit trail under separate written authorization — at minimum (a) every order intent, order submission, fill, cancel, kill-switch trip, and reconciliation result is recorded with an ADR-004 `Z`-suffixed UTC timestamp before the network call completes, (b) the audit-trail storage is append-only (no in-place overwrite, no truncation), (c) the audit-trail storage survives unclean shutdowns (consistent with the §5.6 May 13 panic record), and (d) a separate operator-side procedure exists for reading the audit trail back. None of (a)–(d) is authorized by this entry; they are named as preconditions for any paper / live escalation. Owner: Kevin.
- **Incident response runbook.** Status: **open / not yet written**. Trigger: any incident — kernel panic (per §5.6 May 13), ungraceful reboot, suspected device compromise, suspected account compromise, suspected destructive `git` operation, suspected lost or stolen device, suspected Backblaze health failure, suspected Time Machine corruption, suspected X10 Pro failure. Rule: a future docs/governance-only packet should add an incident-response runbook section (likely §18 or a sibling document) covering: containment (which operator-side actions stop further damage), assessment (which read-only checks characterize the incident), recovery (which §5 / §9 procedures apply, in which order), recordation (which §5.5 / §5.6 entry captures the incident), and disclosure (when an external party — broker, exchange, tax authority — must be informed; not applicable today but pre-committed for paper / live). Until then, the §9 "Safe Next Actions" are the closest existing analogue. Owner: Kevin.
- **Change-freeze rules.** Status: **open / no formal freeze policy**. Trigger: any major external event (vendor outage, market event, account disruption, hardware failure) during which no new implementation work should land. Rule: a future docs/governance-only packet should define when Kevin declares a change freeze, which packets are still permitted during a freeze (typically: monitoring packets, governance / docs packets, incident-response packets), and how a freeze is lifted. No freeze is in effect today; the entry is a pointer for the future. Owner: Kevin.
- **Second-review policy (ChatGPT, Grok, or other independent review).** Status: **ad hoc — used at Kevin's discretion (e.g., the "ultrareview" command)**. Trigger: any high-risk architecture decision (per `AI_WORKFLOW.md` §4(2)), any phase gate (per §4(1)), any safety-critical decision (per §4(3)), or any docs/governance packet that materially extends Kevin's standing controls. Rule: a future docs/governance-only packet should formalize when a second review by an independent reviewer (a non-Codex, non-Perplexity Computer, non-Backup AI reviewer such as ChatGPT, Grok, or a human reviewer) is required versus optional, what the reviewer is given (read-only access to the repository plus the proposed diff), and how the reviewer's findings are recorded (PR-review text per `AI_WORKFLOW.md` §6 rule 5; never committed). The current ad-hoc practice is acceptable for today's scope; the entry flags the need for an explicit policy as scope grows. Owner: Kevin.
- **Dependency policy.** Status: **strict — `pyproject.toml` pins exact versions for every `[project.optional-dependencies] dev` entry (detect-secrets 1.5.0, mypy 1.20.2, pre-commit 4.6.0, pytest 9.0.3, pytest-cov 7.0.0, ruff 0.15.11); `[project] requires-python = ">=3.12"`**. Trigger: any proposed dependency addition, removal, version change, or constraint relaxation; any proposed new `[project] dependencies` (the runtime dependency set is currently empty by design). Rule: any such change requires its own separate written authorization, a matching `.pre-commit-config.yaml` update if the dependency is a hook, a `detect-secrets` baseline review, and a full `pre-commit run --all-files` proof. The default posture is: the runtime dependency set is empty; dev dependencies are exact-pinned. Owner: Kevin.
- **Release and tag policy.** Status: **explicit — no tag, no release, no version bump has ever been authorized**. Trigger: any proposed `git tag`, GitHub release, version bump in `pyproject.toml`, or change-log entry. Rule: any such change requires its own separate written authorization that explicitly names the tag / release / version, the rollback procedure, and the audit-trail expectations. The default posture is: there are no tags, no releases, and the version stays at `0.1.0` until Kevin separately authorizes a change. Owner: Kevin.

---

## 17. OPS-06 Backup Verification & Monitoring Plan

This section defines (in documentation only) the recurring backup-health and monitoring checks for `gmc-rebuild` and its operational dependencies. The plan is **read-only**; it defines what is checked, against what thresholds, and what escalation responses are appropriate. **It does not authorize any operator-side execution, any monitoring automation, any alerting system, any daemon, any scheduler, any setting change, any backup execution, any drive action, any Backblaze setting change, any Time Machine setting change, any network configuration change, or any successor packet.** Execution of any check named here remains an operator-side action that requires its own separate written authorization at the time it is performed.

### 17.1 Why this plan exists

§13 OPS Roadmap lists OPS-06 as "Recurring backup-verification cadence" — future / not authorized. The §16 Risk Register entry for OPS-06 (above) records the status, trigger, and rule but does not define the check set. This §17 defines the check set so the future OPS-06 execution packet has a concrete plan to authorize against. Per the §15 No Chat-Only Risk Rule, the plan is captured here in the repository rather than left in chat.

### 17.2 Read-only check set

Each check is operator-side and read-only. None of them changes any setting, kills any app, writes to any disk other than the operator's own working files outside this repository, or makes any external API call.

1. **GitHub reachability and `main` sync check.**
   - Confirm `gh auth status` reports an authenticated session and Kevin's `KPH3802` identity.
   - Confirm `git ls-remote origin main` returns a sha (DNS / TLS / `github.com` reachable).
   - Confirm `git fetch origin && git merge-base --is-ancestor 1f101fc origin/main` succeeds (current `origin/main` is a descendant of the accepted Phase 1 baseline `1f101fc`).
   - Confirm the local working tree's `main` branch is fast-forward-compatible with `origin/main` (no force-push has rewritten history out from under the operator).
2. **LaCie / Time Machine latest-backup recency check.**
   - Confirm `/Volumes/LaCie` is mounted (`diskutil info "/Volumes/LaCie"` returns `Mounted: Yes`).
   - Confirm `tmutil destinationinfo` reports the LaCie as the active Time Machine destination.
   - Confirm `tmutil latestbackup` (or the equivalent `tmutil listbackups | tail -1`) returns a timestamp newer than the threshold below.
   - Confirm the LaCie SMART status reports `Verified` via `diskutil info "/Volumes/LaCie"`.
   - Confirm at least one local APFS snapshot under `/Volumes/LaCie` matches a recent UTC date.
3. **Backblaze daemon / process state.**
   - Confirm `pgrep -af bzserv` returns the Backblaze main daemon PID (single instance expected).
   - Confirm `pgrep -af bzbmenu` returns the menubar app PID (single instance expected).
   - Confirm no `bztransmit` zombie or stuck process is present (transient `bztransmit` workers during a push are normal; multi-hour stuck workers are not).
4. **Backblaze selected-volume visibility.**
   - Confirm `/Library/Backblaze.bzpkg/bzdata/bzinfo.xml` `<mountpoints mountpoints_to_watch="…">` lists every volume the operator currently intends to back up.
   - Confirm `/Library/Backblaze.bzpkg/bzdata/bzvolumes.xml` enumerates the same volumes with non-zero `numBytesTotalOnVolume`.
   - Confirm no volume that should be excluded (e.g., `/Volumes/LaCie` Time Machine target) appears in the included list.
5. **Backblaze remaining-file backlog threshold.**
   - Read `/Library/Backblaze.bzpkg/bzdata/bzreports/bzstat_remainingbackup.xml` `remainingnumbytesforbackup`.
   - Read `/Library/Backblaze.bzpkg/bzdata/bzreports/bzstat_remainingbackup.xml` `remainingnumfilesforbackup`.
   - Compare against the per-check threshold below.
6. **Backblaze last-successful-backup threshold.**
   - Read `/Library/Backblaze.bzpkg/bzdata/bzreports/bzstat_lastbackupcompleted.xml` `localdatetime`.
   - Compare against the per-check threshold below.
7. **X10 Pro mounted / offline-intent status.**
   - Confirm whether `/Volumes/X10 Pro` is mounted (`diskutil info "/Volumes/X10 Pro"` returns `Mounted: Yes` or the mount-point is absent).
   - If mounted and OPS-05 has not yet promoted it to Layer 5: confirm the X10 Pro is in `mountpoints_to_watch` and `hard_drives_to_backup` per `bzinfo.xml` (the current OPS-03 / OPS-04 baseline state).
   - If unmounted intentionally (post-OPS-05 promotion): confirm the operator's offline-rotation log records the last mount timestamp.
8. **X10 Pro storage / panic / I/O error watch.**
   - Confirm no new `JetsamEvent-*.ips`, `*hang*.ips`, `*.panic`, or `Kernel_*` artifact has appeared in `/Library/Logs/DiagnosticReports` since the last check.
   - Confirm no new `loginwindow` `previousStartupWasAPanicOrHardRestart` entry has appeared (per the §5.6 OPS-03 method).
   - Confirm no new kernel-log entry mentioning `disk6`, `disk7`, `X10 Pro`, USB disconnect / reset / removal, APFS error, NVMe enclosure error, ScsiTask error, or media error has appeared since the last check (per the §5.6 OPS-03 method's `/usr/bin/log show` predicates).
9. **Periodic byte-for-byte restore drill.**
   - Per §5.5 cadence (currently single-file drills recorded 2026-05-16 under OPS-02 for `docs/decisions/ADR-004_utc_discipline.md`), pick one small non-sensitive project file per drill, restore it from the relevant layer to an off-repo location, verify byte-for-byte against the local working tree using `shasum -a 256` or equivalent, and record the result as a new dated entry under §5.5 / §5.6 under its own future written authorization. The drill is **not** authorized by this §17; it is named here so the future OPS-06 execution packet can authorize it.

### 17.3 Escalation thresholds

The thresholds below are intentionally generous so that a single missed window is noise, not signal. Recurring or simultaneous threshold breaches escalate per §17.4.

- **Time Machine (Layer 3) recency.**
  - **Green:** latest backup within the last 12 hours.
  - **Warning (yellow):** latest backup older than 24 hours.
  - **Investigate (red):** latest backup older than 48 hours, or `tmutil destinationinfo` reports no destination.
- **Backblaze (Layer 4) last-successful-backup.**
  - **Green:** last completed backup within the last 24 hours.
  - **Warning:** no successful backup in the last 48 hours.
  - **Investigate:** no successful backup in the last 72 hours, or `bzserv` is not running.
- **Backblaze remaining-file backlog.**
  - **Green:** backlog is decreasing across consecutive checks, **and** the absolute remaining bytes are within the operator's accepted ceiling (today: documented at ~148 GB during the OPS-01 / OPS-02 window; per-PR drift is normal).
  - **Warning:** backlog is stuck (within ±5% across three consecutive checks) **or** increasing across two consecutive checks **or** the absolute remaining bytes have grown beyond 1.5× the prior check's value.
  - **Investigate:** backlog is increasing across three consecutive checks **or** the absolute remaining bytes have grown beyond 2× the prior check's value.
- **Panic / ungraceful reboot.**
  - **Green:** no new `loginwindow` `previousStartupWasAPanicOrHardRestart` entry and no new `*.panic` / `Kernel_*` artifact since the last check.
  - **Investigate (red):** any new panic indicator. Open an OPS-03-shape investigation packet under separate written authorization before resuming any implementation work.
- **X10 Pro storage / I/O errors.**
  - **Green:** no new USB / APFS / NVMe / enclosure / ScsiTask / media-error kernel-log entry tied to `disk6` / `disk7` since the last check.
  - **Warning:** one new such entry. Increase observation cadence per §17.4.
  - **Demote (red):** two or more such entries in any rolling 7-day window. Treat the X10 Pro as suspect and do not promote to Layer 5 (per OPS-05 / §16.1) until reviewed.
- **GitHub reachability (Layer 1).**
  - **Green:** `gh auth status` authenticated **and** `git ls-remote origin main` returns a sha.
  - **Pause-coding (red):** either check fails. Pause any further implementation work until reachability is restored; per §9.1 and `RECOVERY.md` §6 step 4, working against a stale local tree is not safe.
- **Memory pressure (cross-link to §14.3).**
  - The OPS-04 §14.3 escalation criteria apply unchanged: any of recurring `JetsamEvent`, sustained swap pressure, sustained compressed-memory pressure, repeated non-storage UI hangs, or another ungraceful reboot escalates to an OPS-03-shape investigation packet.

### 17.4 Escalation response (alerting / notification expectations)

This §17 does **not** authorize any automated alerting system, any cron job, any launchd plist, any desktop notification, any email, any SMS, any push notification, any webhook, any third-party paging service, any chat-bot, any Slack / Discord / Telegram / Signal integration, or any other notification mechanism. Each of those would be its own separate operator-side action requiring its own separate written authorization.

What this §17 does define is what the operator should do when running the checks manually and observing one of the thresholds above:

- **Warning-grade signals** are recorded by the operator in a personal note (off-repo per §14.2.4 / §7) with a timestamp and a short observation; the next scheduled check confirms whether the warning escalated or cleared.
- **Investigate / red signals** trigger an immediate OPS-03-shape read-only investigation packet under separate written authorization. The investigation packet records findings as a new dated entry under §5.6.
- **Pause-coding signals** (GitHub unreachable) stop any further implementation packet from being opened until reachability is restored per §9.1.
- **Demote signals** (X10 Pro I/O errors) update the OPS-05 Risk Register entry to record the demote condition; OPS-05 promotion remains blocked.

The operator may choose, under separate written authorization, to add a future automated check runner (a cron job, a launchd plist, or a small operator-side script outside this repository) — but that is its own future packet, not this one. This §17 is the plan, not the schedule.

### 17.5 Cadence

The recommended cadence (operator-side, not authorized by this §17):

- **Daily (operator's own routine):** GitHub reachability + Time Machine recency + Backblaze last-success + panic / hang / I/O error scan since the last check.
- **Weekly:** Backblaze backlog trend (three-point comparison) + X10 Pro mount status + memory-pressure snapshot per §14.2.
- **Monthly:** Single-file byte-for-byte restore drill per §5.5 (cycling through Layer 3 Time Machine and Layer 4 Backblaze in alternation).
- **At every phase boundary:** §5 "Fresh Clone From Cold" disaster-recovery drill per OPS-07.
- **Immediately after any incident:** OPS-03-shape investigation packet (per §17.4).

### 17.6 What §17 does not do

- Does not authorize any operator-side execution of any check listed above.
- Does not authorize any monitoring automation, cron job, launchd plist, desktop notification, email / SMS / push / webhook / chat integration, or any other alerting mechanism.
- Does not authorize any backup execution, restore execution, drive action, Backblaze setting change, Time Machine setting change, network configuration change, system setting change, app installation, or hardware change.
- Does not authorize any successor packet (OPS-06 execution, OPS-07 disaster-recovery drill execution, monitoring automation packet, alerting packet, …). Each future packet continues to require its own separate written authorization from Kevin per `AI_WORKFLOW.md` §7.
- Does not change the merged P4-06 / P4-07 / P4-08 safety foundation, the merged P3-03 / P3-04 / P3-05 in-memory fakes, the merged P2-01..P2-05 packages, the merged OPS-01..OPS-04B operations records, or the merged P5-01 inert local simulation boundary.
- Does not modify the §16 Risk Register entries except via a future docs/governance-only packet that adds, updates, or closes specific entries under separate written authorization.
