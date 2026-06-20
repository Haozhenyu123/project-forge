# ADR-0001: Project stack

## Status

Accepted

## Context

- Project slug: `nextjs-fastapi-demo`
- Goal: Decision dashboard with a TypeScript frontend and Python REST API backend
- Selected stack: `nextjs`

## Evidence

- [E1] Next.js supports TypeScript web applications and dashboard-style product surfaces.: https://nextjs.org/docs
- [E2] FastAPI supports Python REST APIs with OpenAPI contracts for separated backend services.: https://fastapi.tiangolo.com/

## Considered Options

- `nextjs`: selected from the requested harness and available evidence.
- Additional alternatives were not scored; this decision remains provisional.

## Decision

Use `nextjs` as the primary harness for `nextjs-fastapi-demo`.
- Rationale: This stack matches the current project goal and has an available harness contract.

## Explicitly Rejected

- No alternative has enough evidence for a responsible rejection.
- Re-run architecture research before treating this choice as final.

## Confidence Assessment

- **Stack choice**: Medium confidence -- current evidence exists, but source diversity is limited.

## Consequences

- The repository receives a Project Forge harness contract and CI workflow.
- Future architecture changes should cite updated research evidence.
- Low-confidence decisions should be re-evaluated before expanding scope beyond MVP.

## Risks and Revisit Triggers

- The project needs capabilities not covered by the current stack.
- A critical dependency becomes unmaintained or changes licensing.
- A required Architecture Signal cannot be verified by the harness.
