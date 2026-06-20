# Superpowers Handoff

## Brief

- Project slug: `chrome-extension`
- Goal: Chrome extension that summarizes selected text with a configurable AI backend
- Primary stack: `chrome-extension`
- Secondary stacks: none
- First task: Implement the smallest user-visible workflow from the accepted creative direction and prove it with the harness contract.

## Evidence

- [E1] GoogleChrome/chrome-extensions-samples: Official Chrome Extension samples repository with Manifest V3 examples (https://github.com/GoogleChrome/chrome-extensions-samples)
- [E2] Chrome Extension Manifest V3 Overview: Manifest V3 is the latest version of the Chrome Extensions platform with improved security and performance. (https://developer.chrome.com/docs/extensions/mv3/intro/)

## Architecture Decision

Read `docs/architecture/ADR-0001-stack.md` before changing architecture.

```markdown
# ADR-0001: Project stack
## Status
Accepted
## Context
- Project slug: `chrome-extension`
- Goal: Chrome extension that summarizes selected text with a configurable AI backend
- Selected stack: `chrome-extension`
## Evidence
- [E1] Official Chrome Extension samples repository with Manifest V3 examples: https://github.com/GoogleChrome/chrome-extensions-samples
- [E2] Manifest V3 is the latest version of the Chrome Extensions platform with improved security and performance.: https://developer.chrome.com/docs/extensions/mv3/intro/
## Considered Options
- `chrome-extension`: selected from the requested harness and available evidence.
- Additional alternatives were not scored; this decision remains provisional.
## Decision
Use `chrome-extension` as the primary harness for `chrome-extension`.
- Rationale: This stack matches the current project goal and has an available harness contract.
```

## Harness Commands

### chrome-extension (`chrome-extension` at `.`)

- `install`: `npm ci`
- `test`: `npm run test`
- `lint`: `npm run lint`
- `typecheck`: `npm run typecheck`
- `build`: `npm run build`
- `run`: `echo Load from chrome://extensions in developer mode`
- `smoke`: `npm run smoke`

## Acceptance Criteria

- Preserve the accepted ADR unless new evidence is recorded.
- Run the relevant structured harness commands and explain remaining failures.
- Keep implementation scope inside the accepted creative direction.
- Return to Project Forge when direction, architecture, or harness assumptions become stale.

## Guardrails

- Project Forge does not replace TDD, debugging, code review, worktrees, or branch completion.
- Do not silently replace provisional evidence with unsupported claims.
- Do not execute commands that are absent from the harness contract.

## Readiness

- Status: `structurally_ready`
- Verification report: `not run`

## Machine-Readable Packet

Source: `docs/superpowers-handoff.json` (Schema v2).

## How Superpowers Should Consume This

1. Read this packet and the Markdown handoff.
2. Open the ADR, creative decision, inventory, and evidence only when more detail is needed.
3. Use Superpowers implementation workflows after accepting the packet.

## Harness Notes

```markdown
# Chrome Extension Harness
This harness defines the standard Project Forge command contract for Chrome Extension (Manifest V3) projects with TypeScript.
## How to verify
Run the commands listed in `project-forge.yaml` from the project root. At minimum, verify `install`, `lint`, `typecheck`, `build`, `test`, and `smoke` before handing off the project. Chrome Extensions require manual loading from `chrome://extensions` in developer mode; the `run` command documents this step rather than opening a browser automatically.
```
