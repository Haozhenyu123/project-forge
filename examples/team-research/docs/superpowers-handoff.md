# Superpowers Handoff

## Brief

- Project slug: `team-research`
- Goal: Help small teams convert research evidence into architecture decisions and handoffs.
- Stack signal: node-ts
- Assignment: Consume this packet, preserve the evidence-backed architecture, and implement against the harness contract.
- First task: Implement the smallest user-visible workflow that satisfies the brief, then prove it with the Project Forge harness commands.

## Creative Direction

- Build the smallest coherent product experience that satisfies the goal and keeps future iteration easy.
- Keep user-facing choices aligned with the accepted ADR and the current harness constraints.
- When product direction is ambiguous, make the assumption explicit under Open Questions before expanding scope.

## Evidence

Source: `docs/research/team-research/evidence.jsonl`

- [E1] team-research reference implementation discussion: Maintainers describe a lightweight team-research workflow that keeps source notes, architectural decisions, and verification commands in one repository so handoffs remain reviewable. (https://github.com/example/team-research/issues/42)
- [E2] Small-team research synthesis practices for team-research: The article recommends short evidence records, explicit decision logs, and repeatable smoke checks for small product teams turning research into implementation plans. (https://example.com/research/small-team-synthesis)

## ADR

Read `docs/architecture/ADR-0001-stack.md` before changing architecture or dependencies.

```markdown
# ADR-0001: Project stack
## Status
Accepted
## Context
- Project slug: `team-research`
- Goal: Help small teams turn research notes into architecture decisions that can be verified by a repeatable harness.
- Selected stack: `node-ts`
## Evidence
- [E1] The reference implementation discussion keeps research, decisions, and verification commands together.
- [E2] Small-team synthesis guidance recommends short evidence records, explicit decision logs, and smoke checks.
## Considered Options
- `node-ts` (score: 86): Gives the example a familiar command surface for web-adjacent collaboration tools without forcing a full app scaffold.
```

## Harness Commands

Source: `project-forge.yaml`

- `install`: `npm ci`
- `test`: `npm test`
- `lint`: `npm run lint`
- `typecheck`: `npm run typecheck`
- `build`: `npm run build`
- `run`: `npm start`
- `smoke`: `python ../../scripts/smoke_test.py --project . --slug team-research`

Harness notes from `docs/harness.md`:

```markdown
# Harness
team-research follows the Project Forge command contract in project-forge.yaml.
## How to verify
Run commands from the team-research project root unless a command names a repository-relative path.
- install: npm ci
- test: npm test
- lint: npm run lint
- typecheck: npm run typecheck
- build: npm run build
- run: npm start
- smoke: python ../../scripts/smoke_test.py --project . --slug team-research
The smoke command validates that the research evidence, ADR, harness contract, harness guide, and Superpowers handoff all refer to team-research.
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
  slug: team-research
  goal: Help small teams convert research evidence into architecture decisions and handoffs.
  stack: node-ts
commands:
  install: npm ci
  test: npm test
  lint: npm run lint
  typecheck: npm run typecheck
  build: npm run build
  run: npm start
  smoke: python ../../scripts/smoke_test.py --project . --slug team-research
artifacts:
  evidence: docs/research/team-research/evidence.jsonl
  adr: docs/architecture/ADR-0001-stack.md
  harness: docs/harness.md
  handoff: docs/superpowers-handoff.md
```
