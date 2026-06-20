---
name: using-project-forge
description: Use when the user has a vague product idea, is starting a new project, needs an evidence-backed architecture choice, needs a project harness contract, or asks whether a handoff is Superpowers-ready. Do not use for ordinary implementation, debugging, TDD, code review, Git, worktree, or branch tasks.
---

# Using Project Forge

Classify the request before using implementation tools.

1. For a vague idea or new project, invoke `forge-intake`; use `creative-director` when the product
   direction is still unclear.
2. For architecture or stack selection, invoke `ai-architect` and require current evidence.
3. For install/test/lint/typecheck/build/run/smoke contracts, invoke `harness-engineer`.
4. For a handoff check, invoke `forge-project` and run the Superpowers-ready validation.

Keep Project Forge at its boundary: decide what to build, why, which architecture to accept, and how
the project will be verified. Hand accepted work to Superpowers for implementation planning and its
own TDD, debugging, review, and Git workflows.

Do not trigger this route for a scoped implementation request whose product direction,
architecture, and harness are already accepted. Continue with the implementation workflow instead.
