# Creative Brief

- Project slug: `fastapi-demo`
- Goal: API-first planning service for architecture decisions
- Selected direction: `Evidence Dashboard`
- Created: 2026-06-20T06:32:02.792566Z

## Experience Thesis

Make options, evidence, confidence, and next actions visible.

## Target User

teams that need shared confidence before implementation

## Primary Workflow

Guide the user from an initial idea to an accepted product direction, then to architecture and harness readiness.

## First Interaction

Present three concrete angles, choose a default, and ask only for corrections that would change the decision.

## Interaction Style

Opinionated, evidence-aware, and concise; make the next decision obvious.

## Content Tone

Clear, commercially grounded, and calm.

## Platform

Host-agent workflow with repository artifacts; no SaaS backend required for V1.

## Competitive Context

Compare direct competitors, substitute workflows, and manual decision processes when evidence is available.

## Differentiation

commercially strongest when stakeholders must compare options and justify tradeoffs

## Architecture Signals

- auditability
- evidence-store
- multi-view-comparison

## Assumptions

- Commercial reasoning is directional until user interviews, traffic, or payment intent are measured.
- Architecture choices must stay aligned with the accepted creative direction.

## Risks

- Direction is provisional when evidence confidence is low.
- Architecture must be revisited if the accepted creative direction changes.
- Product claims need validation before they become implementation scope.

## Next Steps

1. Feed the accepted direction into architecture scoring.
2. Record evidence gaps as provisional instead of inventing confidence.
3. Generate harness and handoff only after the direction is explicit.
