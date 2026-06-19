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
- `node-ts` (score: 68): Useful for TypeScript tooling, but not specific enough for manifest, permissions, and extension packaging.
- `nextjs` (score: 45): Good for web apps, but wrong runtime surface for selected-text browser workflows.

## Decision

Use `chrome-extension` as the primary harness for `chrome-extension`.

- Rationale: the product lives inside the browser, so the architecture must make Manifest V3, permissions, content scripts, and extension packaging first-class.

## Explicitly Rejected

- `node-ts`: rejected because a generic Node harness would not force extension-specific smoke checks.
- `nextjs`: rejected because a standalone web app would miss the selected-text and page-context workflow.

## Confidence Assessment

- **Stack choice**: High confidence -- the platform constraint is explicit and the evidence points to Manifest V3.

## Consequences

- The repository receives an extension-specific Project Forge harness and CI workflow.
- Future architecture changes must preserve browser permission and CSP constraints.
- Superpowers can implement against the extension contract without re-deciding the platform.

## Risks and Revisit Triggers

- Revisit if the browser target expands beyond Chromium-compatible extensions.
- Revisit if the AI backend requires privileged network flows that conflict with extension policies.
- Revisit if the product becomes a web dashboard with a small companion extension.
