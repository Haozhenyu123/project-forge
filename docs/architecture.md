# Project Forge Architecture

## Overview

Project Forge is a dual-harness plugin for Codex and Claude Code. It helps AI agents decide what to build and why before they start coding. It provides six skills, a stdlib Python script layer, eight harness templates, and a coordinator flow that chains them together.

## Component Map

```
User idea
    |
    v
forge-intake (skill)        -- clarifies goal, scope, constraints
    |
    v
creative-director (skill)   -- chooses product direction, writes creative-brief.md
    |
    v
ai-architect (skill)        -- gathers GitHub/web evidence, chooses stack, writes ADR
    |
    v
harness-engineer (skill)    -- applies template, writes project-forge.yaml, CI, docs/harness.md
    |
    v
forge-project (skill)       -- runs scripts/forge_project.py coordinator
    |
    v
Superpowers handoff         -- export_handoff.py writes Markdown and JSON packets
    |
    v
Superpowers-ready check     -- superpowers_ready.py validates the packet
```

## Skill Chaining

Each skill names its successor explicitly in its SKILL.md. When one skill completes its output, it instructs the agent to hand off to the next skill. The chain is:

`forge-intake -> creative-director -> ai-architect -> harness-engineer -> forge-project`

No runtime scheduler is needed; the skills tell the host agent which worker to call next.

## Script Layer

All scripts live under `scripts/` and are plain Python 3.9+ with no external dependencies.

| Directory | Purpose |
|-----------|---------|
| `scripts/harness/` | `detect_stack.py` (auto-detect project type), `apply_template.py` (copy template files) |
| `scripts/research/` | `github_search.py`, `web_search.py`, `normalize_evidence.py`, `validate_evidence.py` |
| `scripts/evals/` | `validate_scenarios.py`, `run_scenarios.py` |
| `scripts/mcp/` | `server.py` (MCP tool provider) |
| `scripts/` root | `cli.py` (unified CLI), `forge_project.py` (coordinator), `smoke_test.py`, `superpowers_ready.py`, `export_handoff.py`, `install_test.py`, `clean.py`, `creative_brief.py` |

## Data Flow

1. Raw evidence enters as `.json` or `.jsonl` files in a staging directory.
2. `normalize_evidence.py` merges and normalizes them into `docs/research/<slug>/evidence.jsonl`.
3. `forge_project.py` reads the normalized evidence, generates `docs/architecture/ADR-0001-stack.md` and `project-forge.yaml`.
4. `apply_template.py` copies `docs/harness.md` and `.github/workflows/project-forge-ci.yml` from templates.
5. `export_handoff.py` bundles everything into `docs/superpowers-handoff.md` and `docs/superpowers-handoff.json`.
6. `superpowers_ready.py` verifies the packet before it is handed to Superpowers.

## Templates

Eight harness templates live under `templates/harness/`. Each is a self-contained directory with:

- `project-forge.yaml` -- command contract
- `docs/harness.md` -- human-readable verification guide
- `.github/workflows/project-forge-ci.yml` -- CI workflow

The auto-detection in `detect_stack.py` recognizes project type from signals like `package.json` dependencies, `manifest.json`, `pyproject.toml`, and `main.py` imports.

## Evals

Six JSON scenario files under `evals/scenarios/` define pressure tests for the skills. Each scenario has a `name`, `purpose`, `setup`, `steps`, `expected` outcome, `evidence` requirements, and a `rubric` with scoring criteria. Response fixtures in `tests/fixtures/eval_responses/` simulate agent outputs for automated scoring.

## MCP Server

`scripts/mcp/server.py` implements the Model Context Protocol over stdin/stdout. It exposes fourteen tools: `github_search`, `web_search`, `detect_stack`, `apply_template`, `forge_project`, `export_handoff`, `superpowers_ready`, `inspect_project`, `harness_compose`, `migrate_schema`, `plugin_manage`, `validate_evidence`, `list_templates`, `run_evals`. Any MCP-compatible host can connect to it.
