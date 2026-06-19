---
name: agent-evaluator
description: Use when Project Forge needs evaluation scenarios, rubrics, and acceptance checks for generated projects, agents, or implementation workers.
---

# Agent Evaluator

Use this skill to define how Project Forge will judge whether the project, agent, or implementation is actually useful. Evaluation should cover realistic behavior, not just happy-path completion.

## Inputs

Read the intake brief, creative direction, architecture ADR, and harness docs when available. Extract:

- user goal
- MVP workflow
- acceptance checks
- technical constraints
- harness commands
- known risks
- Superpowers handoff readiness from `docs/superpowers-handoff.json` or `project-forge superpowers-ready`

If inputs are thin, write scenarios from the clearest user outcome and label assumptions.

## Scenario Design

Create evaluation scenarios that exercise:

- the main successful workflow
- invalid or incomplete input
- a realistic edge case
- recovery from external dependency failure
- accessibility or usability expectations when relevant
- persistence, export, or integration behavior when promised

Each scenario should describe starting state, user action or agent task, expected result, and evidence required to pass.

## Rubric

Use a rubric with observable criteria:

- `correctness`: output matches the requested behavior.
- `completeness`: all required steps or artifacts are present.
- `reliability`: failures are handled clearly.
- `usability`: the result is understandable for the target user.
- `maintainability`: implementation follows the architecture and harness contract.
- `evidence`: claims are backed by tests, logs, screenshots, or source links.

Avoid judging private reasoning. Evaluate artifacts and behavior.

## Harness Integration

Tie evaluation to commands from `project-forge.yaml`. At minimum, identify which scenarios require `test`, `build`, `run`, or `smoke`. If a scenario cannot be automated yet, define the manual evidence needed and the path toward automation.

For Project Forge-to-Superpowers integration, include at least one scenario that checks whether the generated handoff packet has a first task, acceptance criteria, guardrails, and the correct boundary between Project Forge and Superpowers.

## Research Fallback

When an evaluation depends on current platform rules, package behavior, model capabilities, or public data, require GitHub or web research fallback. Prefer official sources, active repositories, and dated documentation. Record any source-sensitive assumptions in the scenario notes.

## Output Format

For each scenario include:

- `id`: stable lowercase identifier.
- `name`: short human label.
- `purpose`: risk or behavior being tested.
- `setup`: required files, data, accounts, or environment.
- `steps`: actions to perform.
- `expected`: observable pass conditions.
- `evidence`: logs, command output, screenshots, files, or links.
- `rubric`: scoring criteria.

## Quality Bar

The evaluation set is ready when it can catch a superficially complete but unusable implementation, while still giving clear guidance to improve the project.
