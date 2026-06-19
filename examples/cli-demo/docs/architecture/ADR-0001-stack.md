# ADR-0001: Project stack

## Status

Accepted

## Context

- Project slug: cli-demo
- Goal: A CLI tool that converts markdown files to HTML and PDF with syntax highlighting
- Selected stack: cli

## Evidence

- [E1] Package your Node.js project into an executable: https://github.com/vercel/pkg
- [E2] Node.js has built-in support for command-line argument parsing and CLI tool development.: https://nodejs.org/en/learn/command-line/how-to-parse-command-line-arguments

## Decision

Use the cli harness and architecture baseline for cli-demo.

## Consequences

- The repository receives a Project Forge harness contract and CI workflow.
- Future architecture changes should cite updated research evidence.
