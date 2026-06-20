# ADR-0001: Project stack

## Status

Accepted

## Context

- Project slug: `fastapi-demo`
- Goal: API-first planning service for architecture decisions
- Selected stack: `fastapi`

## Evidence

- [E1] FastAPI framework, high performance, easy to learn, fast to code, ready for production fastapi-demo: https://github.com/tiangolo/fastapi
- [E2] FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints. fastapi-demo: https://fastapi.tiangolo.com/

## Considered Options

- `fastapi`: selected from the requested harness and available evidence.
- Additional alternatives were not scored; this decision remains provisional.

## Decision

Use `fastapi` as the primary harness for `fastapi-demo`.
- Rationale: This stack matches the current project goal and has an available harness contract.

## Explicitly Rejected

- No alternative has enough evidence for a responsible rejection.
- Re-run architecture research before treating this choice as final.

## Confidence Assessment

- **Stack choice**: High confidence -- multiple current, independent sources support the decision.

## Consequences

- The repository receives a Project Forge harness contract and CI workflow.
- Future architecture changes should cite updated research evidence.
- Low-confidence decisions should be re-evaluated before expanding scope beyond MVP.

## Risks and Revisit Triggers

- The project needs capabilities not covered by the current stack.
- A critical dependency becomes unmaintained or changes licensing.
- A required Architecture Signal cannot be verified by the harness.
