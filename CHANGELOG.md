# Changelog

## [0.2.0] - 2026-06-19

### Added
- **CLI entry point** (`project-forge init`, `detect`, `research`, `handoff`, `smoke`, `validate-evidence`, `list-templates`)
- **MCP server** with 9 tools: `github_search`, `web_search`, `detect_stack`, `apply_template`, `forge_project`, `export_handoff`, `validate_evidence`, `list_templates`, `run_evals`
- **Five new harness templates**: `nextjs`, `fastapi`, `electron`, `cli`, `chrome-extension` (total: 8)
- **Skill auto-chaining**: `forge-intake` -> `creative-director` -> `ai-architect` -> `harness-engineer` -> `forge-project`
- **`creative-brief.md` artifact** produced by `scripts/creative_brief.py`
- **Real web search backend** via DuckDuckGo API (no key required), with custom provider fallback
- **Three new example projects**: `fastapi-demo`, `chrome-extension-demo`, `cli-demo` (total: 4)
- `docs/architecture.md` — internal architecture documentation
- `docs/quickstart.md` — 5-minute setup guide
- `Makefile` — `make test`, `make verify`, `make clean`, `make smoke`, `make evals`
- `.editorconfig` — consistent code style
- `scripts/clean.py` — remove `__pycache__` and build artifacts
- `scripts/install_test.py` — 12-point installation verification
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
