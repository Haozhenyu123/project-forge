---
name: ai-architect
description: Use when Project Forge needs evidence-backed technical architecture, stack decisions, ADRs, and research synthesis before implementation.
---

# AI Architect

Use this skill to choose a practical architecture for a Project Forge project. The architect must connect decisions to evidence, user needs, harness reality, and the `forge-project` coordinator flow.

## Inputs

Start from the intake brief and creative direction when available. Extract:

- project slug
- MVP scope and constraints
- expected users and traffic shape
- data model and integrations
- deployment target
- verification needs
- evidence needs

If the brief is incomplete, make the smallest safe assumption and record it. Ask only when a missing answer would change the stack, data boundary, security model, or delivery path.

## Evidence First

Before making stack decisions, gather evidence for unstable or consequential choices. Run local research scripts from the plugin root with plugin-root-relative paths, such as `scripts/research/github_search.py`, `scripts/research/web_search.py`, and `scripts/research/normalize_evidence.py`. If scripts are unavailable, fall back to GitHub search and web research using the host tools. Prefer primary sources: official documentation, release notes, reputable benchmarks, package repositories, and active issue trackers.

Write normalized research to:

`docs/research/<project-slug>/evidence.jsonl`

Each evidence row should include source, title, URL, short summary, observed date when possible, and why it matters. Do not treat popularity as proof by itself; weigh maintenance, ecosystem fit, complexity, and operational cost.

## Architecture Decisions

Create an ADR at:

`docs/architecture/ADR-0001-stack.md`

The ADR should include:

- context from the project brief
- considered options
- selected stack and reasoning
- evidence references
- rejected alternatives
- consequences and risks
- verification strategy

Keep the stack boring unless the project specifically needs a specialized tool. Favor technologies with clear local setup, testability, active maintenance, and simple deployment.

## Decision Heuristics

- Pick the simplest architecture that satisfies the MVP and foreseeable near-term growth.
- Avoid adding queues, microservices, vector stores, model orchestration, or realtime infrastructure without a concrete workflow need.
- Make data ownership explicit: local file, database, external service, or user-provided account.
- Define integration boundaries and failure behavior.
- Align choices with the harness engineer's command contract.

## Handoff

Provide a compact architecture handoff:

- stack summary
- major components
- data flow
- key dependencies
- environment variables
- commands expected from the harness
- risks and mitigations
- open questions

When the full coordinator is appropriate, hand the chosen stack and evidence path to `scripts/forge_project.py` from the plugin root so it can create the ADR and harness artifacts together.

## Quality Bar

Every major choice should be traceable to the brief, a constraint, or a cited piece of evidence. A future worker should be able to implement without re-litigating the foundation.

## Handoff to Harness Engineer

When the ADR is written and evidence is normalized, immediately hand off to `harness-engineer`. Pass:

- The project slug and chosen stack
- The ADR path (`docs/architecture/ADR-0001-stack.md`)
- The evidence path (`docs/research/<slug>/evidence.jsonl`)
- The creative brief path (`docs/creative-brief.md`) if available
- Any environment variables or runtime requirements identified during architecture

The harness engineer needs the stack decision to apply the correct template. Do not wait for the user to ask for harness setup; the next logical step is always to make the architecture verifiable.

