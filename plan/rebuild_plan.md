# GMC Rebuild Plan

**Status:** v0.2 — Section 1 filled, Section 4 (Audit Standard) inserted
**Created:** 2026-05-08
**Last Updated:** 2026-05-08
**Location:** `~/gmc-rebuild/plan/rebuild_plan.md`
**Repo:** `gmc-rebuild` (local; GitHub hosting decision pending)

---

## 1. Purpose

This plan governs the structured rebuild of Grist Mill Capital's systematic trading infrastructure, undertaken May 2026 after a series of audit findings revealed that the existing project's signal foundation, audit trails, and documentation-based enforcement had drifted below the standard required for live capital deployment. The rebuild follows a strict seven-step sequence — data, validation, backtest, stress test, execution, safety stress test, execute — with no step proceeding until the previous step is verifiably complete. Every constraint that can become runtime enforcement becomes runtime enforcement; documentation governs only what genuinely cannot be encoded. Independent AI review gates designated artifacts before they advance. Existing components from the prior project — code, signals, infrastructure — may be carried forward into the rebuild only after passing the same audit bar new work is held to; nothing is grandfathered. The existing project remains in dry-run, unchanged, until the rebuild produces a replacement of equivalent or higher rigor; the live crypto autotrader continues running independently and is itself subject to re-audit before being designated part of the rebuilt system. This plan is the canonical artifact — when scope, sequence, or acceptance criteria change, this plan changes, and the change is committed with a reasoned message.

---

## 2. Principles — The Seven Steps

The rebuild follows a strict sequence. No step proceeds until the previous step is verifiably complete.

1. Get data
2. Verify the data is clean and correct
3. Backtest the data
4. Stress test the findings
5. Build execution
6. Stress test the execution and safety monitors
7. Execute

[Each step's definition and exit criteria filled in Section 6.]

---

## 3. External Review Gates

Independent AI review is required for designated artifacts before they can be merged or acted on. Reviews are git-tracked artifacts under `~/gmc-rebuild/reviews/`, not conversations.

[Section will define: which artifacts require review, at which points in the sequence, the format of the review request, the format of the review response, how disagreements are adjudicated. To be drafted before Step 1 begins.]

---

## 4. Audit Standard

The concrete specification of the bar every component — newly built or carried forward from the prior project — must clear before being designated part of the rebuilt system. The audit standard is what makes "the same bar new work is held to" (Section 1) a measurable test rather than a phrase.

[Section will define: required artifacts (e.g., backtest script, raw output, methodology document, reproducibility test), traceability requirements (every claimed number maps to a specific output), runtime requirements (e.g., schema fields populated, startup checks pass), review requirements (which gates from Section 3 apply), and the explicit pass/fail criteria. Carried-forward components and new components are evaluated identically.]

---

## 5. Current State Assessment

Honest read of where each of the seven steps actually stands today, component by component and signal by signal. Distinguishes verified facts from unverified claims. Every entry marked (verified) or (claim, needs verification) with the verification step or claim source named explicitly.

[To be filled. Will draw on the May 8 audit findings, the existing project's git history, and per-signal verification of backtest provenance.]

---

## 6. Step-by-Step Plan

For each of the seven steps in Section 2:

- What "done" looks like (acceptance criteria)
- The work it requires (sub-tasks)
- Dependencies on prior steps
- External review requirements (linked to Section 3)
- Audit standard requirements (linked to Section 4)
- Estimated scope (rough order of magnitude only — not a deadline)

[Filled step by step, in order, after Sections 1-5 are complete.]

---

## 7. Order of Work

Sequencing within and across the seven steps, including:

- Critical-path identification
- Parallel tracks where they exist
- Stop-points where the rebuild explicitly pauses for review or decision

[Filled after Section 6.]

---

## 8. Out of Scope

Explicit list of items this rebuild is NOT doing, to prevent scope creep. Items move out of scope by deliberate decision, recorded with rationale.

[Filled progressively as scope decisions are made.]

---

## 9. Open Questions

Items not yet known that need to be resolved before specific phases can begin. Each open question has an owner (Kevin or Claude) and a target resolution point in the sequence.

[Filled progressively.]

---

*v0.2 — Section 1 filled (Purpose, with carry-forward and re-audit clauses); Section 4 (Audit Standard) inserted. Sections 3 and 4 are next priority for filling, in that order, before Section 5.*
