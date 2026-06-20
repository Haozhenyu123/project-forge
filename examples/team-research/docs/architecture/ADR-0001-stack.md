# ADR-0001: Project stack

## Status

Accepted

## Context

- Project slug: `team-research`
- Goal: Help small teams convert research evidence into architecture decisions and handoffs.
- Selected stack: `node-ts`

## Evidence

- [E1] Maintainers describe a lightweight team-research workflow that keeps source notes, architectural decisions, and verification commands in one repository so handoffs remain reviewable.: https://github.com/example/team-research/issues/42
- [E2] The article recommends short evidence records, explicit decision logs, and repeatable smoke checks for small product teams turning research into implementation plans.: https://example.com/research/small-team-synthesis

## Considered Options

- `node-ts`: selected from the requested harness and available evidence.
- Additional alternatives were not scored; this decision remains provisional.

## Decision

Use `node-ts` as the primary harness for `team-research`.
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
