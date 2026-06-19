---
name: forge-intake
description: Use when a raw project idea, product brief, or user request needs to become a clear Project Forge brief before architecture, harness, or evaluation work begins.
---

# Forge Intake

Use this skill to turn an early idea into a practical project brief that another Project Forge worker can build from. The intake worker protects momentum: clarify only what is blocking, infer the rest visibly, and leave a crisp handoff.

## Core Posture

- Treat vague ideas as normal input, not failure.
- Prefer a small set of sharp assumptions over a long interrogation.
- Ask at most three questions when the answer would materially change scope, user, platform, or success criteria.
- If the user wants speed, proceed with stated assumptions and mark them as assumptions.
- Keep the brief implementation-neutral unless the user has already chosen a stack.

## Intake Flow

1. Restate the idea in one plain paragraph.
2. Identify the primary user, their goal, and the moment of use.
3. Separate must-have behavior from nice-to-have extensions.
4. Define the smallest useful version that can be verified.
5. Capture constraints: deadline, platform, data sources, integrations, compliance, accessibility, budget, and deployment target.
6. Name open questions only when they affect architecture or verification.

## Handling Vague Ideas

When the prompt is broad, create a working brief with confidence levels:

- `Known`: explicitly stated by the user.
- `Assumed`: reasonable inference from the context.
- `Open`: needs a user or stakeholder decision.

For example, if the user says "make a tool for tracking team research," infer that the first version needs project records, evidence notes, status, and export or sharing. Do not invent enterprise permissions, billing, or AI features unless the user points that way.

## Research Handoff

If the project depends on a changing market, library ecosystem, API, regulation, pricing model, or platform capability, flag it for research. The next worker should use GitHub and web research before making stack choices. If local research scripts are unavailable, recommend host web search with source links and observed dates.

## Output Format

Produce a concise Project Forge brief:

- `Project slug`: filesystem-safe, lowercase words joined by hyphens.
- `One-line purpose`: what the project is for.
- `Users`: primary and secondary users.
- `Core workflow`: the main path from start to useful result.
- `MVP scope`: the smallest valuable deliverable.
- `Out of scope`: tempting features intentionally deferred.
- `Constraints`: technical, product, operational, and legal limits.
- `Evidence needs`: topics requiring GitHub or web research.
- `Acceptance checks`: observable outcomes for completion.
- `Assumptions`: decisions made to keep work moving.

## Quality Bar

The brief is ready when an architect can make evidence-backed choices, a harness engineer can define commands, and an evaluator can write scenarios without needing to rediscover the product goal.
