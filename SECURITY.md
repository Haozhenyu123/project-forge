# Security Policy

Project Forge is a local plugin and scripting toolkit. It should not require paid APIs or secret credentials to run basic workflows.

Please report security issues privately to the repository owner. Include:

- affected version or commit;
- reproduction steps;
- expected and actual behavior;
- whether secrets, generated project files, or local plugin state are exposed.

Security expectations:

- scripts must not print tokens;
- missing API keys must degrade to provisional evidence;
- generated files must not overwrite user work without explicit `--force`;
- forced overwrites must create backups under `.project-forge/backups/`.
