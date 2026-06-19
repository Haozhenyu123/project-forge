# ADR-0001: Project stack

## Status

Accepted

## Context

- Project slug: `cli-demo`
- Goal: A CLI tool that converts markdown files to HTML and PDF with syntax highlighting.
- Selected stack: `cli`

## Evidence

- [E1] Node packaging examples show how JavaScript CLI projects can expose executables.
- [E2] Node.js documentation covers command-line argument parsing and CLI tool development.

## Considered Options

- `cli` (score: 88): Directly matches a package with a command entrypoint and local smoke tests.
- `node-ts` (score: 74): Strong TypeScript baseline, but less explicit about executable packaging.
- `python` (score: 66): Viable for document conversion, but weaker fit for the existing Node-oriented evidence.

## Decision

Use `cli` as the primary harness for `cli-demo`.

- Rationale: the product is a command-line tool, so the harness should verify executable packaging, command invocation, and local smoke behavior.

## Explicitly Rejected

- `node-ts`: rejected because it does not make CLI packaging and invocation the primary contract.
- `python`: rejected because the evidence and package story are already oriented around Node CLI tooling.

## Confidence Assessment

- **Stack choice**: Medium confidence -- the CLI shape is clear, but production implementation should refresh packaging evidence before release.

## Consequences

- The repository receives a CLI-specific command contract and CI workflow.
- Future changes should preserve a fast smoke command that exercises the executable path.
- Superpowers can implement features without reselecting the delivery surface.

## Risks and Revisit Triggers

- Revisit if PDF generation requires native binaries that complicate Node packaging.
- Revisit if users need a single-file native binary with no Node runtime expectations.
- Revisit if the product becomes a hosted conversion service instead of a local CLI.
