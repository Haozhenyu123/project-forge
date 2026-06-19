# Changelog

## [0.2.5] - 2026-06-20

### Added
- Structured `docs/superpowers-handoff.json` packets alongside Markdown handoffs.
- `scripts/superpowers_ready.py` and `project-forge superpowers-ready` for handoff readiness checks.
- MCP `superpowers_ready` tool for host-driven handoff validation.
- JSON schema for Superpowers handoff packets.
- Showcase docs, examples index, marketplace preparation copy, logo/card assets, and issue/PR templates.

### Changed
- Forge runs now generate both Markdown and JSON Superpowers handoff artifacts.
- Smoke tests now validate the structured handoff packet.
- Runtime context now routes vague ideas, new projects, stack decisions, and handoff readiness through Project Forge.
- README, docs, skills, CI, and install smoke checks now describe the Project Forge-to-Superpowers boundary and readiness flow.

### Fixed
- Restored clean UTF-8 Chinese README content and synchronized the README version badge.

## [0.2.4] - 2026-06-19

### Added
- Deterministic decision engine for creative directions, stack ranking, rejected options, confidence, and revisit triggers.
- Runtime activation assets for Codex and Claude Code: SessionStart hooks plus MCP registration in both plugin manifests.
- Safer forge runs with dry-run support, overwrite refusal by default, backups, restore, and run history.
- Superpowers handoff document generation that preserves Project Forge's boundary: decision, evidence, architecture, harness, and handoff.
- Live-agent evaluation runner with CLI isolation, skip behavior when agent CLIs are unavailable, and scenario assertions.
- Install helpers for Codex and Claude Code plugin locations.
- Release packaging, version audit, version bump tooling, release workflow, distribution docs, security policy, and code of conduct.

### Changed
- `forge_project.py` now writes richer ADRs with considered options, rejected options, confidence, and revisit triggers.
- `cli.py` now captures subprocess output correctly, supports `doctor`, `backups`, `restore`, `--dry-run`, `--force`, and decision files.
- Research scripts now produce higher quality fallback evidence, source quality markers, observed timestamps, and safer missing-token behavior.
- CI now covers cross-platform unit checks plus focused runtime, decision, agent, install, and release test jobs.
- README was rewritten in clean UTF-8 with a clearer Project Forge vs Superpowers boundary.

### Fixed
- Removed stale stack-detection fallback duplication.
- Hardened BOM handling for evidence inputs.
- Removed mojibake from project documentation.

## [0.2.0] - 2026-06-19

### Added
- **CLI entry point** (`project-forge init`, `detect`, `research`, `handoff`, `smoke`, `validate-evidence`, `list-templates`)
- **MCP server** with 9 tools: `github_search`, `web_search`, `detect_stack`, `apply_template`, `forge_project`, `export_handoff`, `validate_evidence`, `list_templates`, `run_evals`
- **Five new harness templates**: `nextjs`, `fastapi`, `electron`, `cli`, `chrome-extension` (total: 8)
- **Skill auto-chaining**: `forge-intake` -> `creative-director` -> `ai-architect` -> `harness-engineer` -> `forge-project`
- **`creative-brief.md` artifact** produced by `scripts/creative_brief.py`
- **Real web search backend** via DuckDuckGo API (no key required), with custom provider fallback
- **Three new example projects**: `fastapi-demo`, `chrome-extension-demo`, `cli-demo` (total: 4)
- `docs/architecture.md` - internal architecture documentation
- `docs/quickstart.md` - 5-minute setup guide
- `Makefile` - `make test`, `make verify`, `make clean`, `make smoke`, `make evals`
- `.editorconfig` - consistent code style
- `scripts/clean.py` - remove `__pycache__` and build artifacts
- `scripts/install_test.py` - 12-point installation verification
- Integration test class (5 tests) covering full pipeline, creative brief, DuckDuckGo search
- Smart stack detection for Next.js, Electron, CLI tools, Chrome Extensions, FastAPI

### Changed
- `detect_stack.py` now recognizes 8 project types from package deps, `manifest.json`, and `main.py` imports
- `forge_project.py` CI generation handles all 8 stacks with correct Node/Python setup actions
- `web_search.py` gains DuckDuckGo fallback between custom provider and host-tool instruction
- All 5 skills updated with explicit handoff instructions to the next worker
- `smoke_test.py` relaxed slug check to only evidence and contract files
- `test_project_forge.py` grew from 23 to 61 tests
- Cached `__pycache__` directories cleaned from workspace

### Fixed
- BOM (byte-order mark) stripped from all source files; `utf-8-sig` encoding used where needed
- `install_test.py` marketplace check fixed for object-format marketplace configs

## [0.1.0] - 2025

### Added
- Initial release with 6 skills, 3 harness templates, research scripts, eval framework
- `scripts/forge_project.py` coordinator
- `scripts/export_handoff.py` Superpowers handoff export
- `examples/team-research` example project
- 23 unit tests covering manifests, skills, scripts, templates, evals
- CI workflow in `.github/workflows/ci.yml`
- MIT license
