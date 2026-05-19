# GMC Project Map

Last updated: 2026-05-19

## Purpose

Grist Mill Capital is being built as a professional-grade systematic trading operation, not as a casual one-person coding project. The goal is to combine Kevin Heaney's 20 years of experience as a Chicago Board of Trade and Chicago Mercantile Exchange trader and brokerage-firm owner with AI-assisted research, disciplined software engineering, and institutional-quality operating controls.

The first product objective is a trustworthy trading engine. Governance, safety controls, tests, documentation, and verification are required controls around that engine, but they are not the engine itself.

## North Star

Build a real operating hedge-fund-like platform that can:

- Generate and research trading ideas using AI-assisted deep research.
- Validate signals through disciplined testing, evidence review, and regime analysis.
- Convert approved signals into a controlled dry-run trading workflow.
- Progress from dry-run to paper/live readiness only through explicit gates.
- Maintain professional operational standards: auditability, risk control, monitoring, backups, incident response, and verified change management.

## Where We Have Been

Before the rebuild, GMC already had meaningful trading-system components:

- Signal work across PEAD, 8-K Item 1.01 shorts, SI squeeze, COT, CEL, 13F, Form 4, dividend initiations/cuts, options volume, and Congress trading.
- Interactive Brokers dry-run/autotrader infrastructure.
- Scanner jobs, PythonAnywhere tasks, dashboard work, local data stores, GitHub repos, backup systems, and a Mac Studio runtime machine.
- A broader fund structure: Bedrock, Event Alpha, and Digital Alpha.

The prior system got close to live operation, but gateway/login/runtime reliability exposed that the foundation was not solid enough. Claude ultimately identified that the system needed to be rebuilt from the ground up rather than patched further.

## Where We Are

The current `gmc-rebuild` effort is a foundation rebuild. The foundation work is valid, but it must stay tied to the trading-engine objective.

Current reality:

- The rebuild has created stronger governance, authorization, safety vocabulary, tests, review discipline, and phase gates.
- The project has also drifted toward status reconciliation, tripwires, and process artifacts.
- The missing piece is a visible path from the current foundation to an actual working dry-run trading engine.

The correct framing is:

> We are rebuilding the chassis, brakes, dashboard, inspection process, and operating manual before putting the engine back on the road. But the objective is still to build the engine.

## Where We Are Going

The roadmap should be understood as five layers.

### Layer 1: Professional Foundation

Purpose: create a reliable codebase and operating discipline that can safely support trading-system work.

Includes:

- Package structure.
- Configuration.
- UTC time discipline.
- Structured logging.
- Tests and pre-commit checks.
- Risk-control abstractions.
- Local-only safety boundaries.
- No accidental live broker, secret, order, scheduler, or money-moving path.

Success means the system is trustworthy enough to build on. It does not mean inventing endless safety ceremony.

### Layer 2: Dry-Run Trading Engine

Purpose: model the real trading loop without money movement.

Target capabilities:

- Signal intake.
- Eligibility checks.
- Position/risk checks.
- Simulated order intent.
- Simulated portfolio state.
- Operator view.
- Reconciliation.
- Daily report.
- Failure and exception handling.

This is the next major product layer. It is where the rebuild should begin feeling like a trading system again.

### Layer 3: Research and Alpha Pipeline

Purpose: use AI and Kevin's market experience to generate, test, and prioritize trading ideas.

Target capabilities:

- Research queue.
- Hypothesis generation.
- Academic/expert-work synthesis.
- Backtest/evidence review.
- Regime and conditional analysis.
- Signal promotion/demotion rules.
- Separation between "interesting idea" and "deployable edge."

This layer should not wait forever behind safety work. It can run in parallel as long as it does not create live-trading risk.

### Layer 4: Paper/Live Readiness

Purpose: prepare for broker-connected operation only after dry-run behavior is boringly reliable.

Target capabilities:

- Broker gateway integration.
- Paper trading.
- Live-account constraints.
- Kill switch.
- Exposure limits.
- Position reconciliation.
- Operator override.
- Incident response.

This layer requires hard gates and independent review.

### Layer 5: Operating Hedge-Fund Platform

Purpose: mature GMC into a complete operating platform.

Target capabilities:

- Trading engine.
- Dashboard.
- Morning and evening reports.
- Strategy research queue.
- Portfolio/risk book.
- Operational logs.
- Investor/employer-quality GitHub presence.
- Backup and disaster recovery.
- Compliance, legal, accounting, and reporting workflows when needed.

## Safety Philosophy

Safety is mandatory, but safety is not the product.

The standard is professional hedge-fund risk and change control:

- No reckless live trading.
- No hidden broker, secret, order, scheduler, or money-moving path.
- No undocumented material changes.
- No unverified claims.
- No sign-off based only on absence of errors.
- Every material change must be verified to work and checked against surrounding context.

At the same time:

- Low-risk local simulation work should not require excessive ceremony.
- Each phase should add or protect a visible trading-engine capability.
- Governance should accelerate trust, not become a substitute for progress.

## Working Standards

### Professional Fund Mindset

All planning, engineering, and review should assume GMC is being built as a professional hedge-fund operating system. Decisions should be made the way a serious fund would make them, not the way a casual one-person script project would make them.

This means:

- Prefer boring reliability over cleverness.
- Prefer explicit controls over implicit assumptions.
- Prefer auditability over memory.
- Prefer verified evidence over confidence.
- Prefer controlled progress over either reckless speed or endless process.

### FAA Closed-Loop Communication

Instructions are not considered heard and understood until they are repeated back and confirmed.

For important work:

1. Repeat back the instruction.
2. State the intended output.
3. Execute one bounded step.
4. Show verified result.
5. Wait for confirmation before moving to the next major step when appropriate.

### Verification Rule

Nothing is complete until both checks pass:

1. Verify the fix or change worked by reading back the actual file, output, state, or test result.
2. Verify the surrounding context did not break.

Absence of errors is not proof of success. Sign-off requires positive verification.

## AI Roles

### Claude Code

Primary local builder.

Best used for:

- Repo edits.
- Tests.
- Git workflows.
- Local implementation.
- Multi-step code changes.
- Working directly inside the Mac environment.

### Perplexity Computer

Strategic planner and independent verifier.

Best used for:

- Project map maintenance.
- Direction setting.
- Roadmap and phase planning.
- Reviewing whether work matches the larger trading-engine objective.
- Independent repo/status verification.
- Model-council orchestration at major gates.
- Guarding against drift between Master Status, code reality, and project purpose.

### Implementation Boundary

Claude Code should do the heavy lifting for local repo implementation by default.

Perplexity Computer should not become the default implementation agent. Its default role is to:

- Clarify the objective.
- Repeat back the intended work.
- Define the authorized task boundary.
- Prepare prompts or instructions for Claude Code.
- Verify Claude Code's claims against the actual repo state.
- Check whether the result matches the Project Map, Master Status, tests, and git state.
- Recommend when a second model or adversarial review is worth the spend.

Perplexity Computer may edit repo files only when Kevin explicitly authorizes that specific edit or when the edit is a narrow documentation/control update needed to preserve project truth. Even then, the change must be read back and verified before sign-off.

### Additional Models

Use multiple models selectively for high-leverage decisions, not routine work.

Good use cases:

- Major architecture decisions.
- Phase exit criteria.
- Go/no-go decisions.
- Broker/live/paper readiness.
- Risk reviews.
- Adversarial review of Claude's implementation direction.
- Strategic roadmap review.

Routine status, verification, and planning should normally be single-model and credit-conscious.

## Documentation Layers

The project should maintain three separate kinds of truth:

### Project Map

This document.

Purpose: strategic compass. It answers why the project exists, where it is going, what standards govern it, and how the AI workflow should operate.

### Master Status

Purpose: audit/status log. It records what happened, what is current, what is authorized, and what is not authorized.

Master Status should not be forced to carry the whole strategic vision.

### Git, Tests, and Runtime Evidence

Purpose: ground truth. Code, commits, tests, logs, and runtime outputs are the final evidence of what is actually true.

## Near-Term Objective

For the next 30 to 60 days, progress means completing the professional foundation and moving toward a working local dry-run trading loop skeleton.

The desired outcome is not merely a cleaner Master Status. The desired outcome is a codebase and operating workflow that can support:

- Local-only signal intake.
- Local-only simulated order intent.
- Risk and eligibility checks.
- Operator-visible state.
- Reconciliation and reporting.
- Clear barriers against accidental live trading.

## Current Key Question

The next major planning question is:

> What must be true before the foundation rebuild is considered complete enough to begin building the dry-run trading engine in earnest?

That question should drive the next roadmap discussion more than "what is the next status-doc patch?"
