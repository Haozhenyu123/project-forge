# Static Architecture Inventory

Project Forge can inspect an existing repository before making an architecture decision. The
scanner reads bounded project metadata and source text; it does not import target code, run package
managers, start services, or execute project commands.

```powershell
python scripts/inspect_project.py path/to/project
python scripts/inspect_project.py path/to/project --json
python scripts/inspect_project.py path/to/project --json --no-write
```

By default it writes:

- `docs/architecture/inventory.json` for agents and handoff tooling.
- `docs/architecture/inventory.md` for human review, including a Mermaid topology.

Use `--out-dir PATH` to choose a different artifact directory. `--no-write` performs inspection
without creating artifacts; combine it with `--json` to receive the result on stdout.

## Detected Signals

- JavaScript package workspaces, pnpm workspaces, and Lerna package roots.
- Node and Python services, conventional entrypoints, languages, and common frameworks.
- Databases, queues, and third-party integrations declared as dependencies or container images.
- Dockerfiles, Compose, CI workflows, Kubernetes, and common deployment configuration files.
- Statically visible ports and environment variable names.

Results are evidence for architecture review, not proof that a service is healthy or deployable.
Unknown or dynamic topology should be confirmed by the AI Architect before it changes an ADR.

## Secret Safety

The scanner never opens `.env`, `.env.local`, `.env.production`, or similar runtime environment
files. It may read committed `.env.example`, `.env.sample`, and `.env.template` files, but records
only variable names. Source and CI references are likewise reduced to names such as
`DATABASE_URL`; values and secret expressions are never included in either artifact.

Large files, dependency directories, VCS metadata, virtual environments, caches, and generated
build outputs are skipped. The scanner is intentionally static and has no command-execution API.

## Output Contract

`inventory.json` contains a versioned top-level record with workspaces, services, infrastructure,
resources, environment variable names, inferred relationships, and warnings. Paths are relative to
the inspected project so artifacts remain portable. A relationship is emitted only for a statically
detected dependency; the report does not invent service-to-service calls.
