# ADR-0001: Project stack

## Status

Accepted

## Context

- Project slug: `team-research`
- Goal: Help small teams turn research notes into architecture decisions that can be verified by a repeatable harness.
- Selected stack: `node-ts`

## Evidence

- [E1] The reference implementation discussion keeps research, decisions, and verification commands together.
- [E2] Small-team synthesis guidance recommends short evidence records, explicit decision logs, and smoke checks.

## Considered Options

- `node-ts` (score: 86): Gives the example a familiar command surface for web-adjacent collaboration tools without forcing a full app scaffold.
- `python` (score: 70): Good for local analysis scripts, but weaker for a future collaborative dashboard.
- `generic` (score: 55): Safest fallback, but too vague to show a realistic harness contract.

## Decision

Use `node-ts` as the primary harness for `team-research`.

- Rationale: the example needs a clear install/test/lint/typecheck/build/run/smoke contract and a familiar implementation path if Superpowers later builds a small web experience.

## Explicitly Rejected

- `python`: rejected because the first likely implementation surface is a collaborative project workspace, not a data-processing script.
- `generic`: rejected because it would hide the command expectations that Project Forge is meant to make explicit.

## Confidence Assessment

- **Stack choice**: Medium confidence -- the example has enough evidence for a showcase packet, but production implementation should refresh framework evidence before coding.

## Consequences

- `project-forge.yaml` is the source of truth for verification commands.
- `docs/harness.md` explains how a worker should run and interpret those commands.
- `docs/research/team-research/evidence.jsonl` remains the cited research input for future ADR updates.

## Risks and Revisit Triggers

- Revisit if the product becomes primarily a local research CLI.
- Revisit if the first implementation needs a backend API or persistent multi-user database.
- Revisit if the node harness cannot run cleanly in the target implementation environment.
