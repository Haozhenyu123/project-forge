---
name: ai-architect
description: Use when Project Forge needs evidence-backed technical architecture, stack decisions, ADRs, and research synthesis before implementation.
---

# AI Architect

Use this skill to choose a practical architecture for a Project Forge project. The architect must connect decisions to evidence, user needs, harness reality, and the `forge-project` coordinator flow.

## Inputs

Start from the intake brief and creative direction when available. Extract:

- project slug and goal
- MVP scope and constraints
- expected users and traffic shape
- data model and integrations
- deployment target
- Architecture Signals from the creative brief (real-time, offline-first, data sensitivity, multi-device, scale ceiling, integration surface, accessibility)
- verification needs
- evidence needs

If the brief is incomplete, make the smallest safe assumption and record it. Ask only when a missing answer would change the stack, data boundary, security model, or delivery path.

## Decision Confidence

Not every decision needs the same level of evidence. Classify each major choice:

- **High confidence**: supported by multiple current sources, official docs, and measurable benchmarks. Can proceed.
- **Medium confidence**: supported by one source, community consensus, or inference from similar projects. Record as provisional; revisit if the architecture shifts.
- **Low confidence**: based on assumptions, extrapolation, or stale data. Must be flagged in the ADR as a risk. Schedule a re-evaluation checkpoint.

Confidence is not the same as correctness. A high-confidence decision can still be wrong; it just means the evidence supports it at this moment.

## Domain Pattern Matching

Before running research from scratch, match the creative direction against known domain patterns. These heuristics narrow the search space:

| If the brief says... | Consider these stacks... | Key evidence to gather |
|---|---|---|
| Dashboard (data-heavy, real-time optional) | Next.js, React + GraphQL, SvelteKit | Bundle size, charting libs, data-fetching patterns |
| Real-time collaboration | Elixir/Phoenix, Node.js + WebSocket, CRDT libraries | Latency benchmarks, conflict-resolution maturity |
| Offline-first | PWA (Workbox), SQLite (local), CRDT or event-sourcing | Sync-protocol docs, storage limits, platform support |
| REST API backend | FastAPI, Express, Go + chi, Rust + Axum | Throughput benchmarks, OpenAPI tooling, auth ecosystem |
| CLI tool | Node.js + Commander, Python + Click, Rust + Clap | Binary size, startup time, cross-platform packaging |
| Chrome Extension | Vanilla TS, React + Plasmo, Svelte | Manifest V3 limitations, CSP constraints, storage APIs |
| Content-heavy / CMS | Next.js + MDX, Astro, Hugo | Build times, content-preview workflows, i18n support |
| ML/AI integration | Python + FastAPI, Node.js + LangChain, self-hosted vs API | Model latency, cost-per-query, GPU requirements, privacy |

This is not a prescriptive list; it is a starting point. The architect must still verify with evidence. But matching the pattern first prevents searching the entire possibility space from scratch.

## Multi-Stack Projects

Many real projects need more than one stack. If the creative brief describes both a frontend and a backend, or a web app and a CLI, record:

- **Primary stack**: the main harness template for the dominant part of the project.
- **Secondary stack(s)**: additional templates for supporting parts. Each secondary stack gets its own command contract section in `project-forge.yaml`.

Example: a Next.js dashboard with a FastAPI backend should produce a primary `node-ts` harness and a secondary `fastapi` harness. The ADR should explain why both are needed and how they communicate.

## Evidence First

Before making stack decisions, gather evidence for unstable or consequential choices. Run local research scripts from the plugin root with plugin-root-relative paths, such as `scripts/research/github_search.py`, `scripts/research/web_search.py`, and `scripts/research/normalize_evidence.py`. If scripts are unavailable, fall back to GitHub search and web research using the host tools. Prefer primary sources: official documentation, release notes, reputable benchmarks, package repositories, and active issue trackers.

Write normalized research to:

`docs/research/<project-slug>/evidence.jsonl`

Each evidence row should include source, title, URL, short summary, observed date when possible, and why it matters. Do not treat popularity as proof by itself; weigh maintenance, ecosystem fit, complexity, and operational cost.

## Architecture Decisions

Create an ADR at:

`docs/architecture/ADR-0001-stack.md`

The ADR must include:

- **Context**: from the project brief and Architecture Signals
- **Considered options**: 2-4 candidate stacks with evidence for each, including the option ultimately rejected
- **Selected stack**: the chosen primary stack with reasoning grounded in evidence
- **Explicitly rejected**: what was NOT chosen and why. This is as important as the selection itself. Record the specific reason: too immature, wrong ecosystem fit, excessive complexity, poor local dev experience, missing critical feature, or unsustainable maintenance burden
- **Confidence assessment**: label each major decision High/Medium/Low confidence with a one-sentence justification
- **Evidence references**: pointers to evidence rows, docs, benchmarks
- **Consequences**: what becomes easier, what becomes harder
- **Risks**: what could make this decision wrong, and when to revisit it
- **Secondary stacks** (if applicable): additional templates for separate concerns like backend API, CLI tooling, or mobile companion
- **Verification strategy**: how to confirm the stack works before implementation proceeds

Keep the stack boring unless the project specifically needs a specialized tool. Favor technologies with clear local setup, testability, active maintenance, and simple deployment.

## Decision Heuristics

- Pick the simplest architecture that satisfies the MVP and foreseeable near-term growth.
- Avoid adding queues, microservices, vector stores, model orchestration, or realtime infrastructure without a concrete workflow need.
- Make data ownership explicit: local file, database, external service, or user-provided account.
- Define integration boundaries and failure behavior.
- Align choices with the harness engineer's command contract.

## Handoff

Provide a compact architecture handoff:

- stack summary
- major components
- data flow
- key dependencies
- environment variables
- commands expected from the harness
- risks and mitigations
- open questions

When the full coordinator is appropriate, hand the chosen stack and evidence path to `scripts/forge_project.py` from the plugin root so it can create the ADR and harness artifacts together.

## Quality Bar

Every major choice should be traceable to the brief, a constraint, or a cited piece of evidence. A future worker should be able to implement without re-litigating the foundation.

## Escalation (Feedback to Creative Director)

If the creative direction imposes constraints that are technically infeasible at reasonable cost, escalate back to `creative-director` before proceeding. Examples:

- "Offline-first" on a platform with no reliable local storage API
- "Real-time collaboration" without a clear conflict-resolution model at the planned scale
- A platform choice that excludes the primary target user group
- Architecture Signals that contradict each other (e.g., offline-first AND real-time sync with no conflict strategy)

When escalating, state the specific signal, the technical constraint it hits, and one or two alternative directions that would be feasible.

## Handoff to Harness Engineer

When the ADR is written and evidence is normalized, immediately hand off to `harness-engineer`. Pass:

- The project slug and chosen stack (primary + any secondary)
- The ADR path (`docs/architecture/ADR-0001-stack.md`)
- The evidence path (`docs/research/<slug>/evidence.jsonl`)
- The creative brief path (`docs/creative-brief.md`) if available
- Any environment variables or runtime requirements identified during architecture
- Any low-confidence decisions that need harness-level safeguards

The harness engineer needs the stack decision to apply the correct template. Do not wait for the user to ask for harness setup; the next logical step is always to make the architecture verifiable.



