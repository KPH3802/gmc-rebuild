# GMC Rebuild Plan

**Status:** v0.3 — no-patches-later clause added to Section 1; new Section 3 (Engineering Standards) inserted; downstream sections renumbered
**Created:** 2026-05-08
**Last Updated:** 2026-05-08
**Location:** `~/gmc-rebuild/plan/rebuild_plan.md`
**Repo:** `gmc-rebuild` (local; GitHub hosting decision pending)

---

## 1. Purpose

This plan governs the structured rebuild of Grist Mill Capital's systematic trading infrastructure, undertaken May 2026 after a series of audit findings revealed that the existing project's signal foundation, audit trails, and documentation-based enforcement had drifted below the standard required for live capital deployment. The rebuild follows a strict seven-step sequence — data, validation, backtest, stress test, execution, safety stress test, execute — with no step proceeding until the previous step is verifiably complete. Every constraint that can become runtime enforcement becomes runtime enforcement; documentation governs only what genuinely cannot be encoded. Independent AI review gates designated artifacts before they advance. Work follows test-driven, build-it-correctly-from-the-start discipline; patching holes after the fact is explicitly out of bounds — if a defect surfaces, the affected work returns to the appropriate step and is rebuilt to standard, not patched in place. Existing components from the prior project — code, signals, infrastructure — may be carried forward into the rebuild only after passing the same audit bar new work is held to; nothing is grandfathered. The existing project remains in dry-run, unchanged, until the rebuild produces a replacement of equivalent or higher rigor; the live crypto autotrader continues running independently and is itself subject to re-audit before being designated part of the rebuilt system. This plan is the canonical artifact — when scope, sequence, or acceptance criteria change, this plan changes, and the change is committed with a reasoned message.

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

[Each step's definition and exit criteria filled in Section 7.]

---

## 3. Engineering Standards

The continuous baseline discipline that applies to every artifact produced by this rebuild, regardless of which of the seven steps it belongs to. Engineering standards are the floor; review gates (Section 4) and audit standard (Section 5) are additional bars on top of this floor for designated artifacts.

The no-patches-later principle from Section 1 binds here: when a defect surfaces, work returns to the appropriate step and is rebuilt to standard. Tests catch the bugs we know how to test for; review gates catch the design errors and reasoning failures we don't know to test for; the audit standard is the explicit pass/fail bar. All three layers operate together.

[Section will define: test-driven development as default practice (failing test first, code to pass, refactor); no-untested-code rule with coverage thresholds; pre-commit hooks enforcing linting, type checking, formatting; reproducibility tests required for every numerical claim; migration and rollback tests required for every schema change; specific tooling choices (test framework, coverage tool, hook framework); the explicit "what good looks like" examples to prevent drift.]

---

## 4. External Review Gates

Independent AI review is required for designated artifacts before they can be merged or acted on. Reviews are git-tracked artifacts under `~/gmc-rebuild/reviews/`, not conversations.

[Section will define: which artifacts require review, at which points in the sequence, the format of the review request, the format of the review response, how disagreements are adjudicated. To be drafted before Step 1 begins.]

---

## 5. Audit Standard

The concrete specification of the bar every component — newly built or carried forward from the prior project — must clear before being designated part of the rebuilt system. The audit standard is what makes "the same bar new work is held to" (Section 1) a measurable test rather than a phrase.

[Section will define: required artifacts (e.g., backtest script, raw output, methodology document, reproducibility test, test coverage), traceability requirements (every claimed number maps to a specific output), runtime requirements (e.g., schema fields populated, startup checks pass), engineering standard requirements (linked to Section 3), review requirements (which gates from Section 4 apply), and the explicit pass/fail criteria. Carried-forward components and new components are evaluated identically.]

---

## 6. Current State Assessment

Honest read of where each of the seven steps actually stands today, component by component and signal by signal. Distinguishes verified facts from unverified claims. Every entry marked (verified) or (claim, needs verification) with the verification step or claim source named explicitly.

[To be filled. Will draw on the May 8 audit findings, the existing project's git history, and per-signal verification of backtest provenance.]

---

## 7. Step-by-Step Plan

For each of the seven steps in Section 2:

- What "done" looks like (acceptance criteria)
- The work it requires (sub-tasks)
- Dependencies on prior steps
- Engineering standards requirements (linked to Section 3)
- External review requirements (linked to Section 4)
- Audit standard requirements (linked to Section 5)
- Estimated scope (rough order of magnitude only — not a deadline)

[Filled step by step, in order, after Sections 1-6 are complete.]

---

## 8. Order of Work

Sequencing within and across the seven steps, including:

- Critical-path identification
- Parallel tracks where they exist
- Stop-points where the rebuild explicitly pauses for review or decision

[Filled after Section 7.]

---

## 9. Out of Scope

Explicit list of items this rebuild is NOT doing, to prevent scope creep. Items move out of scope by deliberate decision, recorded with rationale.

[Filled progressively as scope decisions are made.]

---

## 10. Open Questions

Items not yet known that need to be resolved before specific phases can begin. Each open question has an owner (Kevin or Claude) and a target resolution point in the sequence.

[Filled progressively.]

---

*v0.3 — Section 1 amended with no-patches-later clause; Section 3 (Engineering Standards) inserted; downstream sections renumbered. Sections 3, 4, 5 are next priority for filling, in that order, before Section 6.*
