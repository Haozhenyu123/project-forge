# Marketplace Preparation

Project Forge is packaged as a dual-harness plugin for Codex and Claude Code. The marketplace copy
should emphasize that it complements Superpowers instead of copying it.

## Short Copy

AI project architect for Codex and Claude Code: turn vague ideas into product direction,
evidence-backed architecture, runnable harness contracts, and Superpowers-ready handoffs.

## Long Copy

Project Forge adds a Creative Design Director, AI Architect, Harness Engineer, and evaluator to the
front of an AI coding workflow. It researches current evidence, compares architecture options,
records an ADR, generates command contracts and CI, and exports both Markdown and JSON handoff
packets for Superpowers or another implementation workflow.

Project Forge owns what to build, why, which stack fits, and how readiness is verified.
Superpowers owns implementation disciplines such as planning, TDD, debugging, code review, worktree
isolation, and branch completion.

## Suggested Tags

- `codex`
- `claude-code`
- `superpowers`
- `ai-architect`
- `creative-director`
- `architecture`
- `harness`
- `adr`
- `mcp`
- `agent-evaluation`

## Release Checklist

- Version audit passes: `python scripts/release/version.py audit`
- Install smoke passes: `python scripts/install_test.py`
- Example smoke passes for every showcase.
- `superpowers-ready` passes for every showcase.
- README badges match `package.json`.
- Marketplace copy matches the plugin manifests.
