# Project Forge

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.0-brightgreen)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-61%20passed-brightgreen)](.)

Project Forge is a dual-harness plugin for Codex and Claude Code. It helps agents turn a rough project idea into a researched architecture, an implementation-ready harness, and repeatable verification steps.

## What It Provides

- AI Creative Design Director: shapes ambiguous product intent into a coherent creative and user experience direction before implementation starts.
- AI Architect: researches comparable projects, records evidence, chooses a stack, and writes architecture decisions with clear trade-offs.
- Harness Engineering: defines install, test, lint, typecheck, build, run, and smoke commands so the project can be verified consistently.
- Research scripts: collect and normalize GitHub and web evidence for stack decisions and implementation planning.
- Templates: provide starter harness contracts, documentation, and CI workflows for common project shapes.
- Evals: validate Project Forge scenarios and keep the plugin behavior measurable as the system evolves.

## Codex local install

From Windows PowerShell, copy or clone this repository to the local Codex plugin path:

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\plugins" | Out-Null
Copy-Item -Recurse -Force -Path "C:\path\to\project-forge" -Destination "$env:USERPROFILE\plugins\project-forge"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\plugins" | Out-Null
Copy-Item -Force -Path "$env:USERPROFILE\plugins\project-forge\install\codex-marketplace.personal.json" -Destination "$env:USERPROFILE\.agents\plugins\marketplace.json"
```

If you prefer Git, clone directly to `$env:USERPROFILE\plugins\project-forge` instead of using `Copy-Item`. The source marketplace file is `install\codex-marketplace.personal.json`.

## Claude Code local install

Install the local plugin from Claude Code:

```text
/plugin install <path-to-project-forge>
/plugin list
```

Use the official local plugin path format supported by your Claude Code version for `<path-to-project-forge>`; the `/plugin install` command is the primary local install path. Confirm `Project Forge` appears in `/plugin list`.

## Verify the plugin

Run the repository verification checks from the project root:

```powershell
python -m unittest tests/test_project_forge.py
python scripts/evals/validate_scenarios.py evals/scenarios
python -m compileall scripts
```

## Update

Pull or copy the latest repository contents into `$env:USERPROFILE\plugins\project-forge`. For Codex, refresh the personal marketplace metadata after updates:

```powershell
Copy-Item -Force -Path "$env:USERPROFILE\plugins\project-forge\install\codex-marketplace.personal.json" -Destination "$env:USERPROFILE\.agents\plugins\marketplace.json"
```

For Claude Code, reinstall the updated local path if your version does not refresh local plugins automatically:

```text
/plugin install <path-to-project-forge>
```

## Uninstall

Remove the local plugin copy and marketplace metadata:

```powershell
Remove-Item -Recurse -Force -Path "$env:USERPROFILE\plugins\project-forge"
Remove-Item -Force -Path "$env:USERPROFILE\.agents\plugins\marketplace.json"
```

In Claude Code, remove or disable `Project Forge` using the plugin management command supported by your installed version.

## Install And Use

Typical usage:

1. Start with the forge intake skill to capture the project goal and constraints.
2. Use the creative director and architect skills to refine direction, collect evidence, and choose a stack.
3. Use the harness engineer skill to write `project-forge.yaml`, harness docs, and verification commands.
4. Run the research scripts, templates, and evals as needed to check that the project remains grounded and testable.

## V1.2 executable workflow

V1.2 turns a rough idea into a reproducible project package. Start by collecting GitHub and web evidence for the idea, normalize that evidence into `docs/research/<slug>/evidence.jsonl`, then run the forge script to write the stack ADR, harness contract, harness guide, and CI workflow. The expected generated outputs are `docs/research/<slug>/evidence.jsonl`, `docs/architecture/ADR-0001-stack.md`, `project-forge.yaml`, `docs/harness.md`, and `.github/workflows/project-forge-ci.yml`.

Example end-to-end commands:

```powershell
$slug = "team-research"
$goal = "Help small teams turn research into architecture decisions"

python scripts/research/github_search.py --query "team research architecture decision tool" --limit 10 --out "docs/research/$slug/github.jsonl"
python scripts/research/web_search.py --query "team research architecture decision tool" --limit 10 --out "docs/research/$slug/web.jsonl"
python scripts/research/normalize_evidence.py --input "docs/research/$slug" --out "docs/research/$slug/evidence.jsonl"

python scripts/harness/apply_template.py --template node-ts --project . --force
python scripts/forge_project.py --project . --slug $slug --goal $goal --stack node-ts --evidence "docs/research/$slug/evidence.jsonl" --force
```

After generation, review `docs/architecture/ADR-0001-stack.md` for the stack decision and trade-offs, then run the commands recorded in `project-forge.yaml` and `docs/harness.md`. CI should execute the same install, test, lint, typecheck, build, and smoke contract so local verification and pull-request verification stay aligned.

## Quickstart in Chinese (中文快速开始)

1. 在 Codex 或 Claude Code 中安装或链接这个插件仓库。
2. 确认插件名称显示为 `Project Forge`。
3. 先使用 intake 流程说明项目目标、约束和成功标准。
4. 让 AI Architect 基于 GitHub 和 Web 证据选择技术栈，并写下取舍理由。
5. 让 Harness Engineer 生成 `project-forge.yaml` 和验证命令，再运行 install/test/lint/typecheck/build/run/smoke 检查项目。

## V2: CLI, MCP Server, and Expanded Templates

V2 adds a unified command-line interface, an MCP server for tool-provider integration, expanded harness templates, and automated install verification.

### CLI (`project-forge init`)

A single command runs the full Forge workflow:

```powershell
python scripts/cli.py init my-project --stack nextjs --goal "Build a team dashboard"
```

Available subcommands:
- `init [PROJECT]` -- full workflow: research, ADR, harness, handoff
- `detect [PROJECT]` -- detect project stack and print command contract
- `research --query Q` -- gather GitHub and web evidence
- `handoff --slug S` -- export Superpowers handoff
- `smoke --slug S` -- validate existing project artifacts
- `validate-evidence FILE` -- validate an evidence JSONL file
- `list-templates` -- show all eight available harness templates

Or use the batch wrapper from the repo root:

```powershell
.\project-forge.bat init my-project --stack fastapi
```

### MCP Server

The Project Forge MCP server exposes nine tools via the Model Context Protocol for any MCP-compatible host:

```powershell
python scripts/mcp/server.py
```

Tools provided: `github_search`, `web_search`, `detect_stack`, `apply_template`, `forge_project`, `export_handoff`, `validate_evidence`, `list_templates`, `run_evals`.

### Expanded Templates (8 total)

V1 had three templates. V2 adds five more:

| Template | Stack | Key Commands |
|----------|-------|--------------|
| `node-ts` | Node.js + TypeScript | npm ci, npm test, npm run lint |
| `python` | Python | pip install, pytest, ruff, mypy |
| `generic` | Any stack | Placeholder commands to customize |
| `nextjs` | Next.js App Router | npm run dev, npm run build |
| `fastapi` | FastAPI Python | uvicorn, pytest, ruff, mypy |
| `electron` | Electron Desktop | npm start, npm run build |
| `cli` | Node.js CLI tool | node dist/index.js, npm run build |
| `chrome-extension` | Chrome Extension MV3 | npm run build, manual load |

Auto-detection recognizes `next`, `electron`, `fastapi` in dependencies, `bin` in package.json for CLI tools, and `manifest.json` for Chrome extensions.

### Installation Verification

```powershell
python scripts/install_test.py
```

Validates: Codex manifest, Claude Code manifest, all six skills, all eight templates, all thirteen scripts, Python syntax, marketplace config, and README completeness.

## Sample Contract

The root `project-forge.yaml` is a compact sample output contract. Project templates may provide more specific versions for Node, Python, or generic stacks.

## License

MIT



