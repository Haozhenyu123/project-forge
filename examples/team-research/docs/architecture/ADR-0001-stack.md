# ADR-0001: Stack for team-research

## Status

Accepted

## Context

team-research helps small teams turn research notes into architecture decisions that can be verified by a repeatable harness. The example project needs artifacts that are legible to Project Forge workers and to downstream Superpowers handoff readers.

Evidence:

- [E1] The reference implementation discussion keeps research, decisions, and verification commands together.
- [E2] Small-team synthesis guidance recommends short evidence records, explicit decision logs, and smoke checks.

## Decision

Use the node-ts Project Forge harness contract for team-research while keeping this example implementation-neutral. The stack gives the project a familiar command surface for install, test, lint, typecheck, build, run, and smoke without requiring the smoke docs to install dependencies.

## Consequences

- The project contract in project-forge.yaml is the source of truth for verification commands.
- docs/harness.md explains how a worker should run and interpret those commands.
- docs/research/team-research/evidence.jsonl remains the cited research input for future ADR updates.
