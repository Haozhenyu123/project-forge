# Superpowers Handoff

## Brief

- Project slug: `nextjs-fastapi-demo`
- Goal: Decision dashboard with a TypeScript frontend and Python REST API backend
- Primary stack: `nextjs`
- Secondary stacks: fastapi
- First task: Implement the smallest user-visible workflow from the accepted creative direction and prove it with the harness contract.

## Evidence

- [E1] Next.js documentation: Next.js supports TypeScript web applications and dashboard-style product surfaces. (https://nextjs.org/docs)
- [E2] FastAPI documentation: FastAPI supports Python REST APIs with OpenAPI contracts for separated backend services. (https://fastapi.tiangolo.com/)

## Architecture Decision

Read `docs/architecture/ADR-0001-stack.md` before changing architecture.

```markdown
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
```

## Harness Commands

### nextjs (`nextjs` at `.`)

- `install`: `npm ci`
- `test`: `npm run test`
- `lint`: `npm run lint`
- `typecheck`: `npm run typecheck`
- `build`: `npm run build`
- `run`: `npm run dev`
- `smoke`: `npm run smoke`

### fastapi (`fastapi` at `api`)

- `install`: `python -m pip install -r requirements.txt`
- `test`: `python -m pytest`
- `lint`: `python -m ruff check .`
- `typecheck`: `python -m mypy .`
- `build`: `python -m compileall app`
- `run`: `python -m uvicorn app.main:app --reload`
- `smoke`: `python -m pytest tests/smoke`

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
# Next.js Harness
This harness defines the standard Project Forge command contract for Next.js App Router projects with TypeScript.
## How to verify
Run the commands listed in `project-forge.yaml` from the project root. At minimum, verify `install`, `lint`, `typecheck`, `build`, `test`, and `smoke` before handing off the project. Pay special attention to `npm run build` -- a passing Next.js production build catches most integration issues early.
```
