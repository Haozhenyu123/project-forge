# ADR-0001: Project stack

## Status

Accepted

## Context

- Project slug: `cli-demo`
- Goal: CLI tool that converts markdown planning packets to HTML and PDF
- Selected stack: `cli`

## Evidence

- [E1] Package your Node.js project into an executable cli-demo: https://github.com/vercel/pkg
- [E2] Node.js has built-in support for command-line argument parsing and CLI tool development. cli-demo: https://nodejs.org/en/learn/command-line/how-to-parse-command-line-arguments

## Considered Options

- `cli`: selected from the requested harness and available evidence.
- Additional alternatives were not scored; this decision remains provisional.

## Decision

Use `cli` as the primary harness for `cli-demo`.
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
