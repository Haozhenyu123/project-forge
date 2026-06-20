# Superpowers Handoff

## Brief

- Project slug: `fastapi-demo`
- Goal: API-first planning service for architecture decisions
- Primary stack: `fastapi`
- Secondary stacks: none
- First task: Implement the smallest user-visible workflow from the accepted creative direction and prove it with the harness contract.

## Evidence

- [E1] tiangolo/fastapi: FastAPI framework, high performance, easy to learn, fast to code, ready for production fastapi-demo (https://github.com/tiangolo/fastapi)
- [E2] FastAPI Official Docs: FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints. fastapi-demo (https://fastapi.tiangolo.com/)

## Architecture Decision

Read `docs/architecture/ADR-0001-stack.md` before changing architecture.

```markdown
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
```

## Harness Commands

### fastapi (`fastapi` at `.`)

- `install`: `pip install -r requirements.txt`
- `test`: `python -m pytest`
- `lint`: `python -m ruff check .`
- `typecheck`: `python -m mypy .`
- `build`: `echo FastAPI projects do not require a build step`
- `run`: `uvicorn app.main:app --reload`
- `smoke`: `python -m pytest tests/smoke/`

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
# FastAPI Harness
This harness defines the standard Project Forge command contract for FastAPI Python projects.
## How to verify
Run the commands listed in `project-forge.yaml` from the project root. At minimum, verify `install`, `lint`, `typecheck`, `test`, and `smoke` before handing off the project. FastAPI projects skip the build step by default; add a Docker build command if containerization is part of the delivery contract.
```
