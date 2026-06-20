---
name: using-project-forge
description: Use when the user has a vague product idea, is starting a new project, needs an evidence-backed architecture choice, needs a project harness contract, or asks whether a handoff is Superpowers-ready. Do not use for ordinary implementation, debugging, TDD, code review, Git, worktree, or branch tasks.
triggers: ["new project", "start a project", "vague idea", "what should I build", "which stack", "which framework", "which architecture", "choose architecture", "what language", "project setup", "scaffold project", "harness", "superpowers-ready", "handoff", "architecture decision", "ADR", "evidence", "generate project", "create project", "init project", "forge", "project-forge"]
never_trigger: ["fix bug", "debug", "refactor", "add test", "code review", "merge", "branch", "commit", "pull request", "TDD", "implement feature", "add endpoint"]
---

# Using Project Forge — Hard Routing Contract

This skill forces a routing decision BEFORE any implementation work begins.

## MUST Route to Project Forge

Route the user request into the Project Forge workflow when ANY of these are true:

- The user is starting a **new project** or has a **vague product idea**.
- The user asks **"what should I build?"**, **"which stack/framework/architecture?"**, or **"what language?"**.
- The user wants to **scaffold**, **init**, or **generate** a project with evidence-backed decisions.
- The user mentions **harness**, **Superpowers-ready**, **handoff**, **architecture decision**, or **ADR**.
- The user asks for **evidence** or **research** to support a technical choice.

## MUST NOT Route to Project Forge

These are implementation tasks owned by Superpowers or general coding workflow:

- Fixing bugs, debugging, refactoring, adding tests.
- Code review, merging, branching, committing, pull requests.
- TDD cycles, implementing a feature endpoint, writing business logic.
- Any task where product direction, architecture, and harness are **already accepted**.

## Procedure When Routing

1. Pause and acknowledge that this falls inside the Project Forge boundary.
2. Read the relevant Project Forge skills (`forge-intake`, `creative-director`, `ai-architect`, `harness-engineer`, `forge-project`).
3. Execute the Project Forge workflow: intake → creative → architecture → harness → handoff.
4. Only hand off to Superpowers after the handoff packet is structurally ready.
