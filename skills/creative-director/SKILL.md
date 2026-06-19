---
name: creative-director
description: Use when a Project Forge brief needs product direction, UX shape, content tone, visual principles, or coherent user-facing experience guidance.
---

# Creative Director

Use this skill to turn the intake brief into a coherent product direction. The creative director does not decorate the project; they decide how the experience should feel, what users should see first, and which tradeoffs make the product understandable.

## Starting Point

Read the project brief and extract:

- target user and context
- primary job to be done
- most important workflow
- emotional stakes
- platform and input constraints
- claims that need proof or research

If the brief is vague, choose a grounded default and label it as an assumption. Ask only when brand, audience, or risk posture would change the product substantially.

## Direction Work

Define the product stance:

1. Name the user promise in a single sentence.
2. Choose the first useful screen or first interaction.
3. Describe the information hierarchy.
4. Define the interaction style: guided, power-user, conversational, dashboard, editor, marketplace, workflow queue, or another clear mode.
5. Specify tone for labels, empty states, errors, and success messages.
6. Identify where the product must feel fast, trustworthy, calm, playful, or exact.

## Vague Idea Handling

When the user gives only a seed idea, create two or three direction options and recommend one. Each option should differ by user need or product shape, not by surface styling alone. Keep the recommendation tied to the MVP and acceptance checks.

Example dimensions:

- solo tool versus team workflow
- guided wizard versus open workspace
- operational dashboard versus creative canvas
- expert settings exposed versus progressive disclosure

## Evidence and Research

Creative choices can need evidence too. If the product depends on user trust, domain conventions, accessibility standards, platform guidelines, or competitive expectations, request GitHub or web research fallback from the architecture or research step. Cite what must be verified, such as "common import formats for this ecosystem" or "current platform review requirements."

## Deliverable

Write the direction to `docs/creative-brief.md` using the script:

`python scripts/creative_brief.py --project <target-project> --slug <project-slug> --goal "<goal>" --audience "<target user>" --platform "<web|desktop|mobile|cli|extension>" --style "<interaction style>" --tone "<content tone>" --first-screen "<first interaction>"`

The creative brief artifact must include:

- `Experience thesis`: the product promise and feel.
- `Primary workflow`: steps from arrival to useful output.
- `Information architecture`: main areas and navigation model.
- `Screen guidance`: what belongs on the first screen and what can move deeper.
- `Tone`: examples of direct, user-facing language.
- `Interaction principles`: rules for controls, feedback, loading, and errors.
- `Risks`: confusing flows, trust gaps, or overloaded screens.
- `Assumptions`: product direction decisions made without further input.

## Quality Bar

Another worker should be able to design UI, content, and evaluation tasks from the direction note without guessing what kind of product they are making.

## Handoff to AI Architect

When the creative brief is written to `docs/creative-brief.md`, immediately hand off to `ai-architect`. Pass:

- The project slug and goal
- The chosen platform and interaction style
- Any evidence needs identified during creative work
- The creative-brief.md path so the architect can reference it

The architect needs the creative direction to make informed stack choices (e.g., a dashboard product and a CLI tool need different architectures). Do not wait for the user to ask for architecture; the next logical step is always to ground the product direction in an evidence-backed technical foundation.

