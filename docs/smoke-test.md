# Project Forge Smoke Test

Use this smoke test when you need a fast confidence check that a generated Project Forge project still carries the expected research, architecture, harness, and handoff artifacts.

## Command

```bash
python scripts/smoke_test.py --project examples/team-research --slug team-research
```

The script checks that the example project contains its normalized research evidence, ADR, harness contract, harness guide, and Superpowers handoff. It also verifies that each artifact names the requested slug so a stale or copied project is caught early.

## Expected output

```json
{"status": "ok", "project": "examples/team-research", "slug": "team-research"}
```

Run this before publishing docs or packaging a release candidate.
