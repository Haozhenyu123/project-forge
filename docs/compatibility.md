# Superpowers Compatibility

Project Forge tests the boundary between its decision packet and Superpowers planning. It does not
copy or evaluate Superpowers implementation internals.

## Contract

The compatibility runner gives Superpowers an isolated Project Forge project and asks for a plan
only. A passing run must:

- cite the accepted ADR, harness contract, and first task;
- keep the selected architecture rather than reopening the decision;
- declare that implementation has not started;
- leave every project file unchanged.

The versioned matrix is `compatibility/superpowers-matrix.json`. A version is listed only after its
handoff contract has offline coverage. Live results add runtime evidence but do not rewrite the
matrix automatically.

## Run

```powershell
python scripts/evals/superpowers_compat.py `
  --host codex `
  --project examples/team-research `
  --superpowers-dir ../superpowers `
  --superpowers-version 5.1.3
```

The runner uses a temporary HOME and project copy. Codex runs with a read-only sandbox; Claude Code
runs in plan permission mode. Results and raw logs are written under
`.project-forge/compatibility/`.

Result status is strict:

- `pass`: the host returned a compliant plan and did not change the project;
- `fail`: the host ran but violated the contract or failed;
- `not_run`: the CLI, credentials, Superpowers source, or matrix entry was unavailable.

`not_run` exits successfully for scheduled workflows but is never reported as a pass. The weekly
and manual workflow stores each host result as a GitHub Actions artifact.

## Host Bundles

Build general archives plus host-specific submission bundles:

```powershell
python scripts/release/package_release.py --host-bundles --out dist
```

Each host zip includes only its own manifest. The generated submission JSON records host, version,
manifest path, archive name, and SHA-256. `HOST-SHA256SUMS` covers both archives.

