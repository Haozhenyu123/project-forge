# Quickstart

Get Project Forge running in five minutes.

## 1. Verify the plugin

```powershell
python -m unittest tests/test_project_forge.py
python scripts/install_test.py
```

Both should report all checks passed.

## 2. Try the CLI

```powershell
python scripts/cli.py list-templates
python scripts/cli.py --version
```

## 3. Detect your project stack

```powershell
python scripts/cli.py detect /path/to/your-project --json
```

Project Forge auto-detects: Node.js, Next.js, Electron, CLI tools, Chrome Extensions, Python, and FastAPI.

## 4. Forge a new project from scratch

```powershell
python scripts/cli.py init my-new-project --stack node-ts --goal "A team dashboard for sprint metrics"
```

This runs the full pipeline: research -> evidence -> ADR -> harness -> handoff.

## 5. Forge an existing project

If you already have a project with code but no harness:

```powershell
$slug = "my-project"
$goal = "Describe what the project does"

python scripts/research/github_search.py --query "similar to $goal" --limit 5 --out evidence/github.jsonl
python scripts/research/web_search.py --query "best architecture for $goal" --limit 5 --out evidence/web.jsonl
python scripts/research/normalize_evidence.py --input evidence --out evidence/normalized.jsonl

python scripts/cli.py detect . --json

python scripts/forge_project.py --project . --slug $slug --goal $goal --stack node-ts --evidence evidence/normalized.jsonl --force
```

## 6. What you get

After forging, your project will have:

| File | Purpose |
|------|---------|
| `project-forge.yaml` | Install/test/lint/typecheck/build/run/smoke commands |
| `docs/creative-brief.md` | Product direction and UX stance |
| `docs/research/<slug>/evidence.jsonl` | Research evidence with sources |
| `docs/architecture/ADR-0001-stack.md` | Architecture decision record |
| `docs/harness.md` | How to verify the project |
| `docs/superpowers-handoff.md` | Implementation packet for Superpowers |
| `.github/workflows/project-forge-ci.yml` | CI workflow |

## 7. Run the MCP server (optional)

```powershell
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}' | python scripts/mcp/server.py
```

## Next

Read `docs/architecture.md` for the internal design and `docs/superpowers-handoff.md` for the handoff protocol.
