# Contributing to Project Forge

## Setup

```powershell
git clone https://github.com/Haozhenyu123/project-forge.git
cd project-forge
python -m unittest tests/test_project_forge.py
```

No external Python dependencies are required. All scripts use Python 3.9+ stdlib only.

## Development Loop

1. Make changes in a branch off `main`.
2. Write or update tests in `tests/test_project_forge.py`.
3. Run the test suite:

```powershell
make test
```

4. Verify everything before committing:

```powershell
make verify
```

This runs unit tests, eval validation, smoke tests, and installation verification.

## Code Style

- Python: 4-space indent, no tabs. Follow PEP 8.
- Markdown: wrap at 100 characters. Use reference-style links for repeated URLs.
- YAML: 2-space indent.
- Skills (`skills/*/SKILL.md`): keep the YAML frontmatter tight. No TODO, TBD, or placeholders.
- Scripts: prefer argparse for CLI interfaces. Keep `scripts/` flat; only sub-packages for grouped logic (`harness/`, `research/`, `evals/`, `mcp/`).

See `.editorconfig` for automatic enforcement.

## Commit Messages

Use conventional commit prefixes: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`.

## Adding a New Harness Template

1. Create `templates/harness/<name>/` with `project-forge.yaml`, `docs/harness.md`, and `.github/workflows/project-forge-ci.yml`.
2. Add the template's default commands to `COMMANDS` in `scripts/harness/detect_stack.py`.
3. Update `detect_template()` to recognize the stack from project signals.
4. Add the template name to `TEMPLATES` in `scripts/cli.py` and `scripts/mcp/server.py`.
5. Add tests to `tests/test_project_forge.py` under `V2TemplateTests` and `ForgeProjectV2Tests`.
6. Run `make verify`.

## Adding a New Skill

1. Create `skills/<name>/SKILL.md` with YAML frontmatter (`name`, `description`).
2. A valid description starts with "Use when".
3. Follow the skill's handoff chain convention. If it produces an artifact, name the output path and the script that writes it.
4. Add the skill name to `REQUIRED_SKILLS` in `scripts/install_test.py`.
5. Add a test to `SkillTests` in `tests/test_project_forge.py`.

## Questions

Open an issue on GitHub.
