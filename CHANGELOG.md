# Changelog

## [1.0.0] — 2026-06-25

### Major

- **Persona-driven pipeline**: Every step has a strong professional identity — Senior Product Requirements Analyst (Intake), Senior AI Prompt Engineer + Product Architect (Creative Director), Senior AI Prompt Engineer + Technical Architect (AI Architect), Senior AI Prompt Engineer + DevOps Engineer (Harness Engineer). Each role writes a structured system prompt for the next.
- **Domain classification with probing axes**: 10 domains (medical, finance, legal, education, gaming, ecommerce, enterprise, content, iot, general) with domain-specific probing dimensions. Creative Director interviews the user along these axes to determine product depth.
- **29 stack templates**: Added mini-programs (uni-app, Taro, native), mobile (React Native, Flutter), AI/ML (RAG, Graph RAG, LangChain), games (Unity, Godot), IoT embedded, data pipelines, Tauri, SvelteKit, Supabase.
- **Plugin auto-discovery**: Codex skill descriptions rewritten for semantic matching — no manual skill invocation needed.
- **One-line installer**: `irm .../install-codex.ps1 | iex` — no git, no Python required.
- **Multi-ADR support**: Beyond stack selection (ADR-0001), the architect now generates ADR-0002 (database), ADR-0003 (authentication), ADR-0004 (deployment) as triggered by project needs.
- **Conditional pipeline routing**: `forge-intake` determines route_mode (full_pipeline, stack_given, existing_project, multi_stack, architecture_only) and only invokes relevant skills.
- **Evidence source expansion**: Added DockerHub provider (image pull counts) and enhanced StackOverflow provider.
- **Team preference weights**: `--weights security=2.0,speed=0.8` with alias mapping.
- **Token estimation**: New `estimate` CLI command — estimates pipeline token consumption before running.

### Changed

- Domain profiles shifted from answer templates (architecture_patterns, key_libraries) to constraint cards (domain_profile, probing_axes, compliance).
- Decision engine scoring now serves as verification, not primary driver — architect reasons first, engine confirms.
- CLI `--stack` argument dynamically loads from live catalog instead of hardcoded list.
- CLI error messages use Levenshtein fuzzy matching for misspelled template names.
- `init` command shows step-by-step progress (`[1/6]` through `[6/6]`).

### Added

- `project-forge adr new --type database|auth|deployment` — create sub-ADRs with bilingual templates.
- `project-forge adr list` — list existing ADRs.
- `project-forge estimate --goal "..." --lang en` — estimate pipeline token consumption.
- `--lang zh|en` parameter for bilingual creative briefs and ADRs.
- `--interactive` mode enhanced with product depth and platform probing.
- `DockerHubProvider` evidence source.
- `PRODUCT_DIRECTION_CHALLENGE` signal type in loop engine.
- Security test suite (9 tests) for harness executor: cwd escape, legacy_shell block, timeout, fuzzing.

### Fixed

- CLI hardcoded template list eliminated.
- Hooks adapted for Codex runtime (removed Claude-specific env vars).
- Duplicate StackOverflowProvider resolved.
- Catalog template coverage check relaxed from exact match to minimum-required.

---

## [0.4.0] — 2026-06-20

### Added

- Decision Loop Engine: 8-state finite state machine for continuous architecture revision.
- Loop signal ingestion, deduplication, routing, revision, and human decision packet generation.
- `project-forge loop ingest/run/status/resume` CLI commands.
- Inventory Scanner: project structure analysis with JSON/Mermaid output.
- Readiness Checker: harness command execution with structured reporting.
- Hosts Manager: Codex/Claude Code plugin lifecycle (install/verify/update/uninstall/restore).
- MCP Server for project-forge tool exposure.
- Comprehensive test suite (132 tests passing).

---

## [0.3.0] — 2026-06-15

### Added

- Creative Director: product direction generation with scoring.
- AI Architect: evidence-backed stack selection with 9-dimension scoring.
- Harness Engineer: 7-command contract generation with CI templates.
- 8 stack templates: node-ts, nextjs, fastapi, electron, cli, chrome-extension, python, generic.
- Evidence Pipeline: GitHub, npm, PyPI, OSV providers.
- Handoff Service: Superpowers-compatible Markdown + JSON export.
- Superpowers-ready verification.
- Codex and Claude Code plugin manifests.
