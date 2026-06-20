# Release Notes

## 0.3.0

Project Forge 0.3.0 upgrades the project from a working decision plugin into a maintainable, verifiable handoff system.

Highlights:

- domain package under `src/project_forge/` with thin compatibility scripts;
- Schema v2 multi-stack contracts and handoff packets;
- executable readiness reports via `superpowers-ready --execute`;
- read-only inventory inspection for existing projects;
- creative decision JSON with commercial reasoning and evidence confidence;
- versioned architecture catalog and evidence-aware scoring;
- Codex/Claude plugin lifecycle commands and host-specific release bundles;
- plan-only Superpowers compatibility evals and routing skill;
- migrated showcases plus a Next.js + FastAPI multi-stack example.

Scope note:

Project Forge still decides what to build, why, which architecture fits, and how to verify/handoff. Superpowers remains responsible for implementation planning, TDD, debugging, review, worktrees, and branch completion.

## 0.2.5

Project Forge 0.2.5 completes the Superpowers integration maturity pass while preserving the
boundary: Project Forge decides and packages; Superpowers implements.

Highlights:

- Markdown and JSON Superpowers handoff packets;
- `superpowers-ready` CLI/script/MCP checks for handoff completeness;
- smoke tests that validate the structured handoff contract;
- showcase examples with ready-checkable packets;
- marketplace copy, logo assets, issue/PR templates, and cleaner project docs;
- clean UTF-8 README with synchronized badges.

## 0.2.4

Project Forge 0.2.4 turns the V2 comparison work into a releaseable, safer closed loop.

Highlights:

- deterministic decision engine for creative directions, architecture options, stack choice, confidence, and revisit triggers;
- Codex and Claude Code runtime activation through SessionStart hooks and MCP registration;
- safer forge runs with dry-run, backups, restore, overwrite refusal, and run history;
- richer ADRs plus explicit Superpowers handoff documents;
- live-agent eval runner for vague ideas, trendy-framework bias, no-search fallback, and full forge flow scenarios;
- install, release, distribution, security, and community-maintenance tooling.

Scope note:

Project Forge still focuses on deciding what to build, why, which stack fits, and how to verify/handoff. It intentionally does not reimplement Superpowers-style TDD, debugging, code review, worktree, or branch execution workflows.

## 0.2.3

Project Forge focuses on deciding what to build, why it matters, which architecture fits, and how to hand off to Superpowers.

Highlights:

- safer Forge runs with dry-run, backups, and restore;
- deterministic decision engine for product directions and architecture candidates;
- runtime SessionStart context for Project Forge's decision boundary;
- MCP registration for Codex and Claude plugin manifests;
- local install helpers and release packaging tools;
- live-agent evaluation framework with explicit skip behavior when CLIs are unavailable.
