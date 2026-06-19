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

## Consequences

- The repository receives a Project Forge harness contract and CI workflow.
- Future architecture changes should cite updated research evidence.
