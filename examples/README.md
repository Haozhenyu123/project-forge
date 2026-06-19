# Project Forge Examples

The examples are complete Project Forge packets, not full applications. They show what a receiving
implementation workflow should see before coding begins.

## Examples

| Directory | Slug | Stack | Purpose |
|---|---|---|---|
| `team-research` | `team-research` | `node-ts` | Research evidence and decision workspace |
| `fastapi-demo` | `fastapi-demo` | `fastapi` | API-first planning service |
| `chrome-extension-demo` | `chrome-extension` | `chrome-extension` | Browser workflow assistant |
| `cli-demo` | `cli-demo` | `cli` | Local-first planning command line tool |

## Verify

```powershell
python scripts/smoke_test.py --project examples/team-research --slug team-research
python scripts/cli.py superpowers-ready --json --slug team-research examples/team-research
```

Use `docs/showcase.md` for the full showcase policy.
