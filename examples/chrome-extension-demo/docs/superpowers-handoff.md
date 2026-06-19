# Superpowers Handoff

## Brief

- Project slug: `chrome-extension`
- Goal: A Chrome extension that summarizes selected text on any webpage using a configurable AI backend
- Stack signal: chrome-extension
- Assignment: Consume this packet, preserve the evidence-backed architecture, and implement against the harness contract.
- First task: Implement the smallest user-visible workflow that satisfies the brief, then prove it with the Project Forge harness commands.

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
- Project slug: `chrome-extension`
- Goal: A Chrome extension that summarizes selected text on webpages using a configurable AI backend.
- Selected stack: `chrome-extension`
## Evidence
- [E1] Official Chrome Extension samples repository provides Manifest V3 examples and project structure references.
- [E2] Chrome Extensions documentation positions Manifest V3 as the current security and performance baseline.
## Considered Options
- `chrome-extension` (score: 91): Directly matches the browser-extension delivery target and Manifest V3 constraints.
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

## Acceptance Criteria

- The implementation keeps the accepted stack and ADR assumptions unless the ADR is updated with new evidence.
- The relevant commands in project-forge.yaml pass, or every remaining failure is explained with an owner.
- User-facing scope stays inside the creative direction and smallest useful version.
- The handoff is refreshed if implementation changes risks, commands, or architecture assumptions.

## Guardrails

- Do not treat Project Forge as the TDD, debugging, code-review, worktree, or branch-completion workflow.
- Escalate back to Project Forge if the product direction, architecture, or harness contract becomes stale.
- Do not silently replace provisional evidence with claims; cite updated sources first.

## Machine-Readable Packet

Source: `docs/superpowers-handoff.json`

## How Superpowers Should Consume This

1. Read this handoff first, then open `ADR-0001-stack.md`, the evidence JSONL, and harness docs only as needed.
2. Treat `project-forge.yaml` as the source of truth for verification commands such as `npm run test` when present.
3. Keep implementation changes scoped to the brief and update this handoff when risks, commands, or architecture assumptions change.

## Raw Command Contract

```yaml
project:
  slug: "chrome-extension-demo"
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
