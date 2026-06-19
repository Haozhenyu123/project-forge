---
name: Bug report
about: Report a Project Forge workflow, artifact, or packaging issue
title: "[Bug]: "
labels: bug
assignees: ""
---

## What happened?

## Expected behavior

## Project Forge artifacts involved

- [ ] `docs/creative-brief.md`
- [ ] `docs/research/<slug>/evidence.jsonl`
- [ ] `docs/architecture/ADR-0001-stack.md`
- [ ] `project-forge.yaml`
- [ ] `docs/harness.md`
- [ ] `docs/superpowers-handoff.md`
- [ ] `docs/superpowers-handoff.json`

## Verification

Paste the output from:

```text
python scripts/cli.py doctor
python scripts/cli.py superpowers-ready --slug <slug> --json <project>
```
