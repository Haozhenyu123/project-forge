# Superpowers Handoff

## Brief

- Project slug: `cli-demo`
- Goal: A CLI tool that converts markdown files to HTML and PDF with syntax highlighting
- Stack signal: cli
- Assignment: Consume this packet, preserve the evidence-backed architecture, and implement against the harness contract.
- First task: Implement the smallest user-visible workflow that satisfies the brief, then prove it with the Project Forge harness commands.

## Creative Direction

- Build the smallest coherent product experience that satisfies the goal and keeps future iteration easy.
- Keep user-facing choices aligned with the accepted ADR and the current harness constraints.
- When product direction is ambiguous, make the assumption explicit under Open Questions before expanding scope.

## Evidence

Source: `docs/research/cli-demo/evidence.jsonl`

- [E1] vercel/pkg: Package your Node.js project into an executable cli-demo (https://github.com/vercel/pkg)
- [E2] Building CLI Tools with Node.js: Node.js has built-in support for command-line argument parsing and CLI tool development. cli-demo (https://nodejs.org/en/learn/command-line/how-to-parse-command-line-arguments)

## ADR

Read `docs/architecture/ADR-0001-stack.md` before changing architecture or dependencies.

```markdown
# ADR-0001: Project stack
## Status
Accepted
## Context
- Project slug: `cli-demo`
- Goal: A CLI tool that converts markdown files to HTML and PDF with syntax highlighting.
- Selected stack: `cli`
## Evidence
- [E1] Node packaging examples show how JavaScript CLI projects can expose executables.
- [E2] Node.js documentation covers command-line argument parsing and CLI tool development.
## Considered Options
- `cli` (score: 88): Directly matches a package with a command entrypoint and local smoke tests.
```

## Harness Commands

Source: `project-forge.yaml`

- `install`: `npm ci`
- `test`: `npm run test`
- `lint`: `npm run lint`
- `typecheck`: `npm run typecheck`
- `build`: `npm run build`
- `run`: `node dist/index.js`
- `smoke`: `npm run smoke`

Harness notes from `docs/harness.md`:

```markdown
# CLI Harness
This harness defines the standard Project Forge command contract for Node.js CLI tools with TypeScript.
## How to verify
Run the commands listed in `project-forge.yaml` from the project root. At minimum, verify `install`, `lint`, `typecheck`, `build`, `test`, and `smoke` before handing off the project. For CLI tools, also verify that `node dist/index.js --help` (or the equivalent entry point) produces usable output.
```

## Risks

- No handoff-specific risks were detected; still verify commands in the target project.

## Open Questions

- Which feature or workflow should Superpowers implement first if the brief does not name one?
- Are any provisional evidence rows strong enough to keep, or should they be replaced with verified sources?
- Do harness failures represent implementation defects, missing dependencies, or an outdated command contract?

## Acceptance Criteria

- The implementation keeps the accepted stack and ADR assumptions unless the ADR is updated with new evidence.
- The relevant commands in project-forge.yaml pass, or every remaining failure is explained with an owner.
- User-facing scope stays inside the creative direction and smallest useful version.
- The handoff is refreshed if implementation changes risks, commands, or architecture assumptions.

## Guardrails

- Do not treat Project Forge as the TDD, debugging, code-review, worktree, or branch-completion workflow.
- Escalate back to Project Forge if the product direction, architecture, or harness contract becomes stale.
- Do not silently replace provisional evidence with claims; cite updated sources first.

## Machine-Readable Packet

Source: `docs/superpowers-handoff.json`

## How Superpowers Should Consume This

1. Read this handoff first, then open `ADR-0001-stack.md`, the evidence JSONL, and harness docs only as needed.
2. Treat `project-forge.yaml` as the source of truth for verification commands such as `npm run test` when present.
3. Keep implementation changes scoped to the brief and update this handoff when risks, commands, or architecture assumptions change.

## Raw Command Contract

```yaml
project:
  slug: "cli-demo"
  goal: "A CLI tool that converts markdown files to HTML and PDF with syntax highlighting"
  stack: "cli"
commands:
  install: npm ci
  test: npm run test
  lint: npm run lint
  typecheck: npm run typecheck
  build: npm run build
  run: node dist/index.js
  smoke: npm run smoke
```
