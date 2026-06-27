# Open Gaps & Follow-Ups

**Purpose:** A single tracked list of identified gaps, missing sources, and deferred work items that are not blocking current operations but must be resolved before promotion gates (paper-live, live). This is the authoritative checklist — if it's not here, it's not tracked.

**Last updated:** 2026-06-27 — initial creation during methodology synthesis sprint.

---

## Methodology — Missing Source Papers

These gaps left `[PROPOSED]` placeholders in the committed methodology docs in `gmc_engine/research/methodology/`. Each blocks the corresponding doc from being fully sourced.

### 1. Carver Ch 9 "Volatility Targeting" (HIGH PRIORITY)

- **Book:** *Systematic Trading* by Robert Carver, Harriman House (2015), ISBN 9780857195005.
- **Why it matters:** Contains the canonical ~25% annualized portfolio volatility target — the single most load-bearing number in the risk framework. Without it, the master vol dial is `[PROPOSED 10-15%]` rather than sourced.
- **Affected doc:** `gmc_engine/research/methodology/risk_guardrails.md` (commit `1137d41`), §5 and Open Question #1.
- **What we have:** Carver Ch 7, 8, 10, 11, 12, 13 — Ch 9 specifically is missing.
- **Legitimate sources to try:**
  - Kindle / Amazon hardcover purchase (~$15-25)
  - St. Louis County Library interlibrary loan
  - Carver's blog `qoppac.blogspot.com` — he discusses the 25% vol target in free posts
  - Google Books / Amazon "Look Inside" preview
  - `pysystemtrade` GitHub repo — production code defaults reference the number
- **What did NOT work:** Harriman House publisher preview EPUB (`preview-9780857195005`) only contains front matter, no chapter content.

### 2. Pedersen *Efficiently Inefficient* Ch 3 (MEDIUM PRIORITY)

- **Book:** *Efficiently Inefficient: How Smart Money Invests and Market Prices Are Determined* by Lasse Heje Pedersen, Princeton University Press.
- **Chapter needed:** Chapter 3, "Finding and Backtesting Strategies: Profiting in Efficiently Inefficient Markets" (pp. 39-53 per the verified TOC).
- **Why it matters:** Pedersen's framework for evaluation, backtesting, and survivorship bias. Complements Bailey/López de Prado's PBO and López de Prado's purged k-fold.
- **Affected doc:** `gmc_engine/research/methodology/return_predictability.md` — NOT YET CREATED.
- **What did NOT work:**
  - `Efficiently_Inefficient.pdf` originally in inbox was a "Bookey" third-party app summary (paraphrase, not Pedersen). Deleted.
  - `https-nbgarleanu.github.io-EfficientlyInefficient.pdf` was Gârleanu & Pedersen's 2016 academic paper "Efficiently Inefficient Markets for Assets and Asset Management" — same authors, similar title, different work. Deleted.
  - `DE0028AE5094129E9AD5AC125800D002FCDB0.pdf` was just the book's front matter / TOC, no chapter content. Deleted.
- **Legitimate sources to try:**
  - Kindle / Amazon hardcover (~$30-40)
  - St. Louis County Library interlibrary loan
  - Princeton University Press chapter preview
  - Google Books preview
- **Priority rationale:** Marginal — Carver + G&K + López de Prado already cover most of the same ground. Evaluate whether the book purchase justifies itself before committing.

### 3. PBO Companion Papers (LOW PRIORITY, EASY TO RESOLVE)

- **Affected doc:** `gmc_engine/research/methodology/pbo_gate.md` (commit `f32d0e9`)
- **Missing:**
  - Bailey, Borwein, López de Prado, Zhu, "Pseudo-mathematics and financial charlatanism," AMS Notices, 2014 — contains the MinBTL formula derivation
  - Bailey & López de Prado, "The Deflated Sharpe Ratio," Journal of Portfolio Management, 2014 — contains the DSR derivation
- **Both are freely available academic papers.** Both authors and SSRN typically host free preprints. Easy lift.

### 4. G&K Ch 12 "Information Analysis" (LOW PRIORITY)

- **Book:** *Active Portfolio Management*, 2nd ed., Grinold & Kahn.
- **Chapter needed:** Ch 12 "Information Analysis" — the dedicated IC-estimation chapter.
- **Affected doc:** `gmc_engine/research/methodology/information_ratio.md` (commit `b3164b4`), §6 and §9.
- **What we have:** G&K Ch 5, 6, 13 — Ch 12 specifically is missing.
- **Status:** Full G&K book PDF was in the inbox during synthesis but flagged as questionable source. Need a legitimate copy.

---

## Methodology — Lessons & Process Improvements

### Chapter-to-topic mapping errors in overnight prompts (RECURRING)

During the 2026-06-27 synthesis sprint, two prompts I (Perplexity Computer) wrote contained wrong chapter-to-topic mappings:

- **Carver risk guardrails prompt:** I said Ch 7-8 = position sizing / vol targeting. Actually Ch 7 = Forecasts, Ch 8 = Combined Forecasts, Ch 9 = Vol Targeting, Ch 10 = Position Sizing. Claude Code self-corrected and cited what it actually read.
- **G&K Information Ratio prompt:** I said Ch 5 = Fundamental Law. Actually Ch 5 = Information Ratio, Ch 6 = Fundamental Law. Claude Code self-corrected and noted the correction at the top of the doc.

**Implication:** Claude Code's discipline saved both syntheses, but a less rigorous agent would have synthesized confidently from the wrong chapters and produced authoritative-looking but mis-sourced docs. The fix belongs in the eventual overnight prompt template: **prompts should NOT pre-bind specific chapter numbers to topics. Instead, instruct the agent to read the TOC first, then identify which chapters cover the required topics.** This shifts the chapter-mapping work from the (less reliable) prompt author to the (more reliable) reading agent.

### Overnight prompt template — pending creation

The pre-flight + fallback pattern proved its value on both syntheses today (caught the Pedersen-Bookey issue, caught missing pypdf on MBP, both via the verification steps). When time permits, codify this as `docs/overnight_prompt_template.md` so future overnight prompts inherit:

1. Verify environment access before synthesis
2. Verify source legitimacy before synthesis (TOC + author cross-check)
3. Explicit "do not stop and ask" authorizations for `brew install`, `pip install`, etc.
4. Read TOC first, do NOT pre-bind chapters to topics in the prompt
5. Document deviations from prompt assumptions at top of output doc
6. Cross-reference, don't re-synthesize (avoid drift across parallel sessions)
7. Commit + push pattern with rebase fallback for parallel-session conflicts

---

## Operations — Open Gates for Paper-Live & Live Promotion

These came out of the launchd healthcheck monitor build on 2026-06-26. They are NOT blockers for Monday's paper-monitor operation but ARE gates for promotion to higher modes.

### Paper-live promotion gates
- Risk guardrails formally adopted (PM redline of `risk_guardrails.md` complete)
- Information Ratio evaluation framework formally adopted (PM redline of `information_ratio.md` complete)
- Strategy passes both PBO ≤ 0.05 (`pbo_gate.md`) and purged k-fold validation (`walk_forward.md`)

### Live promotion gates (in addition to paper-live gates)
- ≥4 weeks unattended paper operation with no incidents
- Second alert channel beyond Pushover (e.g., SMS via Twilio, or PagerDuty)
- Stateful debounce on alert generation (avoid repeated alerts for same incident)
- Sleep / host-reliability validation (currently dead-man's switch is the only safety net)
- Methodology codification complete (no `[PROPOSED]` items remaining in adopted docs)
- 2FA recovery procedure documented and tested

### Other open items (housekeeping, not gates)
- TWS port 7462 cleanup (legacy CP port, currently inert)
- `gateway_version=176` baseline detects API-protocol changes, NOT all Gateway build bumps (potential silent miss on UI-only updates)
- Pushover secrets rotation: keys exposed in chat 2026-06-26, scheduled rotation Sunday 2026-06-28 20:00 CT

---

## How to use this doc

- Review on every "what's left" session-opening sweep.
- Items marked HIGH PRIORITY must be resolved before paper-live promotion.
- Items marked MEDIUM/LOW PRIORITY should be resolved opportunistically.
- When an item is resolved, remove it from this doc and reference the resolving commit/PR in the affected target doc.
- New gaps discovered in any session should land here, not in chat-only notes.


---

## Sourcing Policy (added 2026-06-27)

**Decision:** Going forward, source all copyrighted methodology books and papers through legitimate channels only. No more pirated PDFs.

**Why this is logged:** During the 2026-06-27 methodology synthesis sprint, the Carver chapter PDFs in `gmc_engine/research/papers_inbox/` were discovered (via PDF metadata embedded by Preview on macOS 2026-04-16) to have originated from `quant-wiki.com` — a pirate site hosting copyrighted finance textbooks without authorization. This affected:

- `Chap7_Carver.pdf`, `Chap8_Carver.pdf`, `Chap10_Carver.pdf`, `Chap11_Carver.pdf`, `Chap12_Carver.pdf`, `Chap13_Grinold_&_Kahn_The_Information_Horizon.pdf`, and the full Carver book PDF (`https:asset.quant-wiki.com:...`)
- These were the sources used to synthesize `risk_guardrails.md` (`1137d41`), `information_ratio.md` (`b3164b4`), and portions of `walk_forward.md` (`037cfe6`) and `pbo_gate.md` (`f32d0e9`).
- Perplexity Computer (and Claude Code) did not flag the source provenance at the time of synthesis. The PDFs read cleanly via pypdf and looked like standard chapter PDFs.

**Going-forward policy:**

1. **For all new methodology sources:** purchase through legitimate channels (Amazon Kindle, publisher direct, academic library access, or interlibrary loan). Open-access preprints (SSRN, NBER, author personal sites) are fine when they exist.
2. **For Carver's *Systematic Trading* specifically:** Carver publishes the same volatility-targeting methodology free on his blog and in his open-source `pysystemtrade` repo. Citing his own free writing is legitimate. Key Carver-authored open sources:
   - [qoppac.blogspot.com/2020/03/how-much-risk-should-we-take.html](https://qoppac.blogspot.com/2020/03/how-much-risk-should-we-take.html) — derivation of 25% vol target via Kelly + half-Kelly
   - [qoppac.blogspot.com/2020/10/should-i-run-my-trading-system-at-fixed.html](https://qoppac.blogspot.com/2020/10/should-i-run-my-trading-system-at-fixed.html) — 25% is a long-run average, not a daily fixed target
   - [github.com/robcarver17/pysystemtrade/blob/master/systems/provided/rob_system/config.yaml](https://github.com/robcarver17/pysystemtrade/blob/master/systems/provided/rob_system/config.yaml) — Carver's production config showing `percentage_vol_target: 25.0`
   - [github.com/robcarver17/pysystemtrade/blob/master/docs/introduction.md](https://github.com/robcarver17/pysystemtrade/blob/master/docs/introduction.md) — Carver's documentation referencing book Ch 9 and Ch 10
3. **For Pedersen *Efficiently Inefficient* Ch 3:** purchase Kindle (~$30-40) or library access. No legitimate free-online substitute exists for the specific chapter content.
4. **For G&K *Active Portfolio Management* 2nd ed.:** purchase Kindle (~$50) or library access. Most-used finance text in this project; ownership is justified.

**Open question for PM review:** What to do about the four methodology docs already on `gmc_engine/origin/main` that were synthesized partly from quant-wiki sources?

Options:
- (a) Leave as-is; the citations are accurate transcriptions of Carver's and G&K's actual words and equations, and the resulting framework is intellectually sound. Treat as "internal draft" until re-sourced.
- (b) Re-synthesize after purchasing the books legitimately. High effort; verifies provenance end-to-end.
- (c) Hybrid: leave the docs in place but add a sourcing note at the top of each, then incrementally replace citations with legitimate-source citations as those sources are acquired.

PM call required before any of these docs influence a live-trading decision. Not a blocker for Monday paper-monitor operation.

**Recommended path (Perplexity Computer):** Option (c). The methodology content is correct (verified by Claude Code's transcription discipline). Re-synthesizing from scratch costs days and produces the same content. Adding a provenance note + incremental replacement preserves the work while making the sourcing trail honest.
