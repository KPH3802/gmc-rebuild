# GMC Rebuild Plan

**Status:** v0.1 — skeleton (structure only, no content yet)
**Created:** 2026-05-08
**Last Updated:** 2026-05-08
**Location:** `~/gmc-rebuild/plan/rebuild_plan.md`
**Repo:** `gmc-rebuild` (local; GitHub hosting decision pending)

---

## 1. Purpose

[One paragraph stating what this plan is and isn't. To be drafted jointly with Kevin before any other section is filled.]

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

[Each step's definition and exit criteria filled in Section 5.]

---

## 3. External Review Gates

Independent AI review is required for designated artifacts before they can be merged or acted on. Reviews are git-tracked artifacts under `~/gmc-rebuild/reviews/`, not conversations.

[Section will define: which artifacts require review, at which points in the sequence, the format of the review request, the format of the review response, how disagreements are adjudicated. To be drafted before Step 1 begins.]

---

## 4. Current State Assessment

Honest read of where each of the seven steps actually stands today, component by component and signal by signal. Distinguishes verified facts from unverified claims. Every entry marked (verified) or (claim, needs verification) with the verification step or claim source named explicitly.

[To be filled. Will draw on the May 8 audit findings, the existing project's git history, and per-signal verification of backtest provenance.]

---

## 5. Step-by-Step Plan

For each of the seven steps in Section 2:

- What "done" looks like (acceptance criteria)
- The work it requires (sub-tasks)
- Dependencies on prior steps
- External review requirements (linked to Section 3)
- Estimated scope (rough order of magnitude only — not a deadline)

[Filled step by step, in order, after Sections 1-4 are complete.]

---

## 6. Order of Work

Sequencing within and across the seven steps, including:

- Critical-path identification
- Parallel tracks where they exist
- Stop-points where the rebuild explicitly pauses for review or decision

[Filled after Section 5.]

---

## 7. Out of Scope

Explicit list of items this rebuild is NOT doing, to prevent scope creep. Items move out of scope by deliberate decision, recorded with rationale.

[Filled progressively as scope decisions are made.]

---

## 8. Open Questions

Items not yet known that need to be resolved before specific phases can begin. Each open question has an owner (Kevin or Claude) and a target resolution point in the sequence.

[Filled progressively.]

---

*End of skeleton. v0.1 — structure only. Sections 1, 2, 3 are top priority for filling first.*
