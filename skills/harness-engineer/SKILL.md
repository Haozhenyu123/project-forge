---
name: harness-engineer
description: Use when Project Forge needs reproducible install, verify, run, smoke, CI, and documentation contracts for a generated or existing project.
---

# Harness Engineer

Use this skill to make a project easy to install, verify, run, and evaluate. The harness is the contract between implementation workers, CI, and future maintainers.

## Required Artifacts

Create or update:

- `project-forge.yaml`
- `docs/harness.md`

The contract file defines commands. The documentation explains how humans use them, what they prove, and how to troubleshoot common failures.

## Command Contract

Define these commands whenever the project type can support them:

- `install`: prepare dependencies.
- `test`: run automated tests.
- `lint`: run style or static checks.
- `typecheck`: verify types or schema contracts.
- `build`: produce the deployable or packaged artifact.
- `run`: start the app or main workflow locally.
- `smoke`: perform a lightweight end-to-end confidence check.

If a command does not apply, map it to a harmless explicit command that explains why, or document the reason in `docs/harness.md`. Prefer commands that work on a clean machine.

## Harness Principles

- Commands must be deterministic and safe to run repeatedly.
- Commands should exit nonzero when their contract fails.
- Avoid hidden global dependencies.
- Put required environment variables in the docs with example names, not secrets.
- Keep install separate from verification.
- Make smoke tests fast and representative of the user's main path.

## Stack Detection

Use the architecture handoff and repository files to select the harness style. Common signals include `package.json`, `pyproject.toml`, lockfiles, Dockerfiles, and existing CI. Preserve existing project conventions when they are coherent.

If stack evidence is missing, provide a generic harness with concrete fallback commands: use commands that inspect files, print guidance, or run available checks.

## GitHub and Web Fallback

If command behavior depends on a current framework, package manager, cloud provider, or CI platform, verify with official docs or GitHub examples. When local scripts are missing, use web research fallback and record sources in the architecture or research notes.

## docs/harness.md Content

Include:

- project type and assumed runtime
- command table with purpose and expected success signal
- local setup steps
- environment variables
- CI behavior
- smoke test description
- troubleshooting notes

## Quality Bar

A new contributor should be able to clone the project, run `install`, run verification, start the app, and understand failures without asking which command matters.
