# Distribution

Project Forge can be used directly from a Git clone or packaged as a local plugin bundle.

## Local Clone

```powershell
git clone https://github.com/Haozhenyu123/project-forge.git
python scripts/install_test.py
python scripts/cli.py doctor
```

## Codex Local Install

Use `scripts/install/codex.py` programmatically or copy `install/codex-marketplace.personal.json` into the Codex marketplace path.

## Claude Code Local Install

Use `scripts/install/claude.py` programmatically to generate a local marketplace directory, then install the generated marketplace in Claude Code.

## Release Package

```powershell
python scripts/release/version.py audit
python scripts/release/package_release.py
```

Release artifacts include zip, tar.gz, and SHA256 checksums. Project Forge packages only the decision, architecture, harness, runtime, and handoff assets. It does not package Superpowers implementation workflows.
