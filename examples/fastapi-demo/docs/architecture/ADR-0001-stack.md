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
- `python` (score: 72): Useful generic Python baseline, but lacks API-specific run and smoke commands.
- `node-ts` (score: 61): Good ecosystem, but adds a JavaScript runtime for an API-first Python example.

## Decision

Use `fastapi` as the primary harness for `fastapi-demo`.

- Rationale: the example is explicitly API-first, and FastAPI gives the clearest command contract for install, tests, linting, running Uvicorn, and smoke checks.

## Explicitly Rejected

- `python`: rejected because the generic Python template does not communicate the API server lifecycle clearly enough.
- `node-ts`: rejected because it would add an unnecessary runtime and weaken the typed Python API story.

## Confidence Assessment

- **Stack choice**: High confidence -- the evidence and product shape both point to a Python API service.

## Consequences

- The repository receives a Project Forge harness contract and Python CI workflow.
- Future architecture changes should cite updated research evidence.
- Superpowers can begin implementation from a typed API surface instead of reselecting the backend stack.

## Risks and Revisit Triggers

- Revisit if the product becomes a mostly static dashboard with little API logic.
- Revisit if deployment constraints require a platform that does not support Python services well.
- Revisit if the API needs realtime bidirectional collaboration as the primary workflow.
