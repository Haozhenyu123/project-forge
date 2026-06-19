# Superpowers Handoff

## Project

- Slug: team-research
- Goal: Help small teams convert research evidence into architecture decisions and handoffs.
- Stack: node-ts

## Key artifacts

- Research evidence: docs/research/team-research/evidence.jsonl
- Architecture decision: docs/architecture/ADR-0001-stack.md
- Harness contract: project-forge.yaml
- Harness guide: docs/harness.md

## Evidence trail

- E1: team-research reference implementation discussion
- E2: Small-team research synthesis practices for team-research

## Verification

Run the smoke check before handoff:

```bash
python ../../scripts/smoke_test.py --project . --slug team-research
```

The broader harness commands are listed in project-forge.yaml. For this documentation example, the smoke check is the release gate.
