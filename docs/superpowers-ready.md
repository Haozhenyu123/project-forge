# Superpowers Ready Check

`project-forge superpowers-ready` verifies that a generated project can be handed to
Superpowers as an implementation packet.

Project Forge still stops at direction, evidence, architecture, harness, and handoff. This check
does not execute TDD, debugging, code review, worktree, or branch workflows. It only proves that the
packet has enough structure for Superpowers to begin its own implementation discipline.

## Command

```powershell
python scripts/cli.py superpowers-ready --slug <project-slug> <target-project>
python scripts/cli.py superpowers-ready --slug <project-slug> --json <target-project>
```

Use `--strict` when warnings, such as all-provisional evidence, should block the handoff.

## Checked Artifacts

- `docs/research/<project-slug>/evidence.jsonl`
- `docs/architecture/ADR-0001-stack.md`
- `project-forge.yaml`
- `docs/harness.md`
- `docs/superpowers-handoff.md`
- `docs/superpowers-handoff.json`

## Readiness Rules

The checker expects:

- evidence rows with at least one source;
- an ADR with considered options, rejected options, confidence, and revisit triggers;
- a complete harness command contract for install, test, lint, typecheck, build, run, and smoke;
- a Markdown handoff with brief, evidence, harness commands, acceptance criteria, guardrails, and
  Superpowers consumption steps;
- a structured JSON handoff that makes the same packet machine-readable.

Statuses:

- `ready`: no failures or warnings;
- `attention`: no failures, but warnings should be reviewed before broad implementation;
- `blocked`: missing or invalid artifacts.
