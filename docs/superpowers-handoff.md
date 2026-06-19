# Superpowers Handoff

Project Forge hands work to Superpowers as a compact implementation packet, not as a blank prompt. The packet should let Superpowers understand the product direction, the evidence behind the stack, the accepted architecture decision, and the exact harness commands that define success.

## Protocol

Create or refresh the handoff after research, ADR, and harness setup are complete:

`python scripts/export_handoff.py --project <target-project> --slug <project-slug> --out <target-project>/docs/superpowers-handoff.md`

The exporter reads:

- `docs/research/<project-slug>/evidence.jsonl`
- `docs/architecture/ADR-0001-stack.md`
- `project-forge.yaml`
- `docs/harness.md`

## Handoff Contents

The handoff should include:

- Brief: the project slug, goal, and the immediate implementation assignment.
- Creative direction: the user experience, product tone, and constraints from intake or creative review.
- Evidence: the strongest research rows, especially cited URLs, summaries, relevance notes, and provisional status.
- ADR: a pointer to `ADR-0001-stack.md` plus the accepted decision and consequences.
- Harness commands: install, test, lint, typecheck, build, run, and smoke commands from `project-forge.yaml`, with supporting notes from `docs/harness.md`.
- Risks: assumptions, provisional evidence, fragile dependencies, and any command that has not been verified.
- Open questions: decisions that Superpowers should resolve before broad implementation.

## How Superpowers Should Consume It

Superpowers should read the handoff first, then open the linked ADR, evidence, and harness files only when more detail is needed. Treat `project-forge.yaml` as the command contract: implementation is not complete until the relevant harness commands pass or the remaining failures are clearly explained. Preserve evidence citations when changing stack or architecture choices, and update the handoff when implementation changes the risk profile or verification path.
