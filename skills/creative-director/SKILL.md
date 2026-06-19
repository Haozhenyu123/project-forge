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
3. Describe the information hierarchy and primary workflow.
4. Define the interaction style: guided, power-user, conversational, dashboard, editor, marketplace, workflow queue, or another clear mode.
5. Specify tone for labels, empty states, errors, and success messages.
6. Identify where the product must feel fast, trustworthy, calm, playful, or exact.

## Competitive Context

Before finalizing direction, identify what already exists in this space:

1. Name 2-3 competing products, approaches, or common workflows the user already uses.
2. Identify the gap: what do existing solutions not do well for the target user?
3. State whether the project replaces, augments, or sits alongside those alternatives.
4. If no direct competitor exists, explain why (new problem, underserved audience, or novel technology).

This analysis is not about building a business case; it prevents the team from building something that already exists and gives the architect a concrete user need to design around.

## Differentiation Strategy

Define what makes this product distinct:

1. What is the one thing this product does that alternatives cannot match?
2. Is the advantage in simplicity, speed, integration, data ownership, price, or domain specificity?
3. What trade-off does the differentiation force? (e.g., "simpler than X but less customizable")
4. Can the differentiation be sustained, or is it easy for competitors to copy?

A weak or missing differentiation means the product competes on features alone, which is nearly always a losing strategy for small teams.

## Architecture Signals

Creative decisions directly constrain technical choices. Record explicit signals for the architect:

- **Real-time**: does the product need live updates, collaboration, or streaming?
- **Offline-first**: must the product work without a network connection?
- **Data sensitivity**: does the product handle PII, health data, financial records, or credentials?
- **Multi-device**: must state sync across devices? If so, what is the conflict resolution strategy?
- **Scale ceiling**: what is the realistic upper bound for users, data volume, or request rate in the first year?
- **Integration surface**: which external services, APIs, or file formats must be supported?
- **Accessibility**: any specific regulatory or inclusive-design requirements?

Each signal limits or opens specific architecture choices. If a signal is unknown, label it as an open question for the architect to investigate.

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

Write the direction to `docs/creative-brief.md`.

**Preferred: freeform mode.** Write a rich Markdown brief with all required sections, then use the script to validate and commit it:

`python scripts/creative_brief.py --project <target-project> --slug <project-slug> --goal "<goal>" --body "<markdown content>"`

**Fallback: structured mode.** Use CLI flags for quick scaffolding:

`python scripts/creative_brief.py --project <target-project> --slug <project-slug> --goal "<goal>" --audience "<target user>" --platform "<web|desktop|mobile|cli|extension>" --style "<interaction style>" --tone "<content tone>" --first-screen "<first interaction>" --competitors "<competitor analysis>" --differentiation "<what makes this different>" --architecture-signals "<signals for the architect>"`

The creative brief artifact must include these sections:

- `Experience Thesis`: the product promise and feel.
- `Target User`: who uses it and in what context.
- `Primary Workflow`: steps from arrival to useful output.
- `Information Architecture`: main areas and navigation model.
- `First Interaction`: what the user sees first and why.
- `Interaction Style`: the interaction mode (dashboard, editor, guided, etc.).
- `Content Tone`: examples of direct, user-facing language.
- `Platform`: target platform and any constraints it imposes.
- `Competitive Context`: what already exists and where the gap is.
- `Differentiation`: what makes this product uniquely valuable.
- `Architecture Signals`: creative choices that constrain technical decisions.
- `Assumptions`: product direction decisions made without further input.
- `Risks`: confusing flows, trust gaps, overloaded screens, competitive threats.

## Quality Bar

Another worker should be able to design UI, content, and evaluation tasks from the direction note without guessing what kind of product they are making. The architect should be able to read Architecture Signals and immediately narrow the stack search space.

## Escalation (Feedback to Intake)

If the intake brief lacks information needed to make creative decisions (no target user, no platform, no workflow), escalate back to `forge-intake` before proceeding. Do not fabricate a user or platform that would change the product fundamentally without asking.

## Handoff to AI Architect

When the creative brief is written to `docs/creative-brief.md`, immediately hand off to `ai-architect`. Pass:

- The project slug and goal
- The chosen platform and interaction style
- The Architecture Signals section (critical for stack selection)
- Any evidence needs identified during creative work
- The creative-brief.md path so the architect can reference it

The architect needs the creative direction to make informed stack choices (e.g., a dashboard product and a CLI tool need different architectures). Do not wait for the user to ask for architecture; the next logical step is always to ground the product direction in an evidence-backed technical foundation.





