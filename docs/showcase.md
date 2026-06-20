# Showcase

These examples demonstrate the full Project Forge boundary: vague direction, evidence-backed
architecture, harness contract, and Superpowers handoff. They are not complete applications.

| Example | Product angle | Stack signal | What to inspect |
|---|---|---|---|
| `examples/team-research` | Team research decisions and citations | `node-ts` | ADR, harness, handoff packet |
| `examples/fastapi-demo` | API-first project planning service | `fastapi` | Python commands and CI |
| `examples/chrome-extension-demo` | Browser workflow assistant | `chrome-extension` | MV3 harness and handoff |
| `examples/cli-demo` | Local-first AI planning CLI | `cli` | CLI package contract |
| `examples/nextjs-fastapi-demo` | Decision dashboard plus API service | `nextjs` + `fastapi` | Multi-stack contract, CI, and handoff |

Run the same confidence checks against any example:

```powershell
python scripts/smoke_test.py --project examples/team-research --slug team-research
python scripts/cli.py superpowers-ready --project examples/team-research --slug team-research
python scripts/cli.py superpowers-ready --project examples/nextjs-fastapi-demo --slug nextjs-fastapi-demo
```

Each example includes:

- `docs/creative-brief.md`
- `docs/research/<slug>/evidence.jsonl`
- `docs/architecture/ADR-0001-stack.md`
- `project-forge.yaml`
- `docs/harness.md`
- `docs/superpowers-handoff.md`
- `docs/superpowers-handoff.json`

When adding a showcase, prefer a realistic ambiguous idea over a toy task. The point is to show how
Project Forge turns uncertainty into a decision packet that a separate implementation workflow can
consume.
