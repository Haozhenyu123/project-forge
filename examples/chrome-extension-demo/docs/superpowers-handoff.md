# Superpowers Handoff

## Brief

- Project slug: `chrome-extension`
- Goal: A Chrome extension that summarizes selected text on any webpage using a configurable AI backend
- Stack signal: chrome-extension
- Assignment: consume this packet, preserve the evidence-backed architecture, and implement against the harness contract.

## Creative Direction

- Build the smallest coherent product experience that satisfies the goal and keeps future iteration easy.
- Keep user-facing choices aligned with the accepted ADR and the current harness constraints.
- When product direction is ambiguous, make the assumption explicit under Open Questions before expanding scope.

## Evidence

Source: `docs/research/chrome-extension/evidence.jsonl`

- [E1] GoogleChrome/chrome-extensions-samples: Official Chrome Extension samples repository with Manifest V3 examples (https://github.com/GoogleChrome/chrome-extensions-samples)
- [E2] Chrome Extension Manifest V3 Overview: Manifest V3 is the latest version of the Chrome Extensions platform with improved security and performance. (https://developer.chrome.com/docs/extensions/mv3/intro/)

## ADR

Read `docs/architecture/ADR-0001-stack.md` before changing architecture or dependencies.

```markdown
# ADR-0001: Project stack
## Status
Accepted
## Context
- Project slug: chrome-extension
- Goal: A Chrome extension that summarizes selected text on any webpage using a configurable AI backend
- Selected stack: chrome-extension
## Evidence
- [E1] Official Chrome Extension samples repository with Manifest V3 examples: https://github.com/GoogleChrome/chrome-extensions-samples
- [E2] Manifest V3 is the latest version of the Chrome Extensions platform with improved security and performance.: https://developer.chrome.com/docs/extensions/mv3/intro/
## Decision
Use the chrome-extension harness and architecture baseline for chrome-extension.
```

## Harness Commands

Source: `project-forge.yaml`

- `install`: `npm ci`
- `test`: `npm run test`
- `lint`: `npm run lint`
- `typecheck`: `npm run typecheck`
- `build`: `npm run build`
- `run`: `echo Load from chrome://extensions in developer mode`
- `smoke`: `npm run smoke`

Harness notes from `docs/harness.md`:

```markdown
# Chrome Extension Harness
This harness defines the standard Project Forge command contract for Chrome Extension (Manifest V3) projects with TypeScript.
## How to verify
Run the commands listed in `project-forge.yaml` from the project root. At minimum, verify `install`, `lint`, `typecheck`, `build`, `test`, and `smoke` before handing off the project. Chrome Extensions require manual loading from `chrome://extensions` in developer mode; the `run` command documents this step rather than opening a browser automatically.
```

## Risks

- No handoff-specific risks were detected; still verify commands in the target project.

## Open Questions

- Which feature or workflow should Superpowers implement first if the brief does not name one?
- Are any provisional evidence rows strong enough to keep, or should they be replaced with verified sources?
- Do harness failures represent implementation defects, missing dependencies, or an outdated command contract?

## How Superpowers Should Consume This

1. Read this handoff first, then open `ADR-0001-stack.md`, the evidence JSONL, and harness docs only as needed.
2. Treat `project-forge.yaml` as the source of truth for verification commands such as `npm run test` when present.
3. Keep implementation changes scoped to the brief and update this handoff when risks, commands, or architecture assumptions change.

## Raw Command Contract

```yaml
project:
  slug: "chrome-extension"
  goal: "A Chrome extension that summarizes selected text on any webpage using a configurable AI backend"
  stack: "chrome-extension"
commands:
  install: npm ci
  test: npm run test
  lint: npm run lint
  typecheck: npm run typecheck
  build: npm run build
  run: echo Load from chrome://extensions in developer mode
  smoke: npm run smoke
```
