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

## Explicitly Rejected

- No alternative has enough evidence for a responsible rejection.
- Re-run architecture research before treating this choice as final.

## Confidence Assessment

- **Stack choice**: High confidence -- multiple current, independent sources support the decision.

## Consequences

- The repository receives a Project Forge harness contract and CI workflow.
- Future architecture changes should cite updated research evidence.
- Low-confidence decisions should be re-evaluated before expanding scope beyond MVP.

## Risks and Revisit Triggers

- The project needs capabilities not covered by the current stack.
- A critical dependency becomes unmaintained or changes licensing.
- A required Architecture Signal cannot be verified by the harness.
