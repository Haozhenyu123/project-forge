# Superpowers Handoff

## Brief

- Project slug: `fastapi-demo`
- Goal: Test
- Stack signal: fastapi
- Assignment: Consume this packet, preserve the evidence-backed architecture, and implement against the harness contract.
- First task: Implement the smallest user-visible workflow that satisfies the brief, then prove it with the Project Forge harness commands.

## Creative Direction

- Build the smallest coherent product experience that satisfies the goal and keeps future iteration easy.
- Keep user-facing choices aligned with the accepted ADR and the current harness constraints.
- When product direction is ambiguous, make the assumption explicit under Open Questions before expanding scope.

## Evidence

Source: `docs/research/fastapi-demo/evidence.jsonl`

- [E1] tiangolo/fastapi: FastAPI framework, high performance, easy to learn, fast to code, ready for production fastapi-demo (https://github.com/tiangolo/fastapi)
- [E2] FastAPI Official Docs: FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints. fastapi-demo (https://fastapi.tiangolo.com/)

## ADR

Read `docs/architecture/ADR-0001-stack.md` before changing architecture or dependencies.

```markdown
# ADR-0001: Project stack
## Status
Accepted
## Context
- Project slug: `fastapi-demo`
- Goal: Show an API-first planning service with typed endpoints and a Python verification harness.
- Selected stack: `fastapi`
## Evidence
- [E1] FastAPI framework repository demonstrates a maintained Python API framework with production usage.
- [E2] FastAPI documentation emphasizes standard Python type hints, OpenAPI generation, and fast local development.
## Considered Options
- `fastapi` (score: 89): Strong fit for typed APIs, generated docs, and simple Python CI.
```

## Harness Commands

Source: `project-forge.yaml`

- `install`: `pip install -r requirements.txt`
- `test`: `python -m pytest`
- `lint`: `python -m ruff check .`
- `typecheck`: `python -m mypy .`
- `build`: `echo FastAPI projects do not require a build step`
- `run`: `uvicorn app.main:app --reload`
- `smoke`: `python -m pytest tests/smoke/`

Harness notes from `docs/harness.md`:

```markdown
# FastAPI Harness
This harness defines the standard Project Forge command contract for FastAPI Python projects.
## How to verify
Run the commands listed in `project-forge.yaml` from the project root. At minimum, verify `install`, `lint`, `typecheck`, `test`, and `smoke` before handing off the project. FastAPI projects skip the build step by default; add a Docker build command if containerization is part of the delivery contract.
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
  slug: "fastapi-demo"
  goal: "Test"
  stack: "fastapi"
commands:
  install: pip install -r requirements.txt
  test: python -m pytest
  lint: python -m ruff check .
  typecheck: python -m mypy .
  build: echo FastAPI projects do not require a build step
  run: uvicorn app.main:app --reload
  smoke: python -m pytest tests/smoke/
```
