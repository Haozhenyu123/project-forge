# Superpowers Handoff

## Brief

- Project slug: `team-research`
- Goal: Help small teams convert research evidence into architecture decisions and handoffs.
- Primary stack: `node-ts`
- Secondary stacks: none
- First task: Implement the smallest user-visible workflow from the accepted creative direction and prove it with the harness contract.

## Evidence

- [E1] team-research reference implementation discussion: Maintainers describe a lightweight team-research workflow that keeps source notes, architectural decisions, and verification commands in one repository so handoffs remain reviewable. (https://github.com/example/team-research/issues/42)
- [E2] Small-team research synthesis practices for team-research: The article recommends short evidence records, explicit decision logs, and repeatable smoke checks for small product teams turning research into implementation plans. (https://example.com/research/small-team-synthesis)

## Architecture Decision

Read `docs/architecture/ADR-0001-stack.md` before changing architecture.

```markdown
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
```

## Harness Commands

### node-ts (`node-ts` at `.`)

- `install`: `npm ci`
- `test`: `npm test`
- `lint`: `npm run lint`
- `typecheck`: `npm run typecheck`
- `build`: `npm run build`
- `run`: `npm start`
- `smoke`: `npm run smoke`

## Acceptance Criteria

- Preserve the accepted ADR unless new evidence is recorded.
- Run the relevant structured harness commands and explain remaining failures.
- Keep implementation scope inside the accepted creative direction.
- Return to Project Forge when direction, architecture, or harness assumptions become stale.

## Guardrails

- Project Forge does not replace TDD, debugging, code review, worktrees, or branch completion.
- Do not silently replace provisional evidence with unsupported claims.
- Do not execute commands that are absent from the harness contract.

## Readiness

- Status: `structurally_ready`
- Verification report: `not run`

## Machine-Readable Packet

Source: `docs/superpowers-handoff.json` (Schema v2).

## How Superpowers Should Consume This

1. Read this packet and the Markdown handoff.
2. Open the ADR, creative decision, inventory, and evidence only when more detail is needed.
3. Use Superpowers implementation workflows after accepting the packet.

## Harness Notes

```markdown
# Node TypeScript Harness
This harness defines the standard Project Forge command contract for Node.js and TypeScript projects.
## How to verify
Run the commands listed in `project-forge.yaml` from the project root. At minimum, verify `install`, `test`, `lint`, `typecheck`, `build`, and `smoke` before handing off the project.
```
