# Superpowers Handoff

## Brief

- Project slug: `cli-demo`
- Goal: CLI tool that converts markdown planning packets to HTML and PDF
- Primary stack: `cli`
- Secondary stacks: none
- First task: Implement the smallest user-visible workflow from the accepted creative direction and prove it with the harness contract.

## Evidence

- [E1] vercel/pkg: Package your Node.js project into an executable cli-demo (https://github.com/vercel/pkg)
- [E2] Building CLI Tools with Node.js: Node.js has built-in support for command-line argument parsing and CLI tool development. cli-demo (https://nodejs.org/en/learn/command-line/how-to-parse-command-line-arguments)

## Architecture Decision

Read `docs/architecture/ADR-0001-stack.md` before changing architecture.

```markdown
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
```

## Harness Commands

### cli (`cli` at `.`)

- `install`: `npm ci`
- `test`: `npm run test`
- `lint`: `npm run lint`
- `typecheck`: `npm run typecheck`
- `build`: `npm run build`
- `run`: `node dist/index.js`
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
# CLI Harness
This harness defines the standard Project Forge command contract for Node.js CLI tools with TypeScript.
## How to verify
Run the commands listed in `project-forge.yaml` from the project root. At minimum, verify `install`, `lint`, `typecheck`, `build`, `test`, and `smoke` before handing off the project. For CLI tools, also verify that `node dist/index.js --help` (or the equivalent entry point) produces usable output.
```
