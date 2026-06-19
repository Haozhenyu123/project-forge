---
name: forge-project
description: Use when Project Forge needs the end-to-end coordinator flow that turns intake, research, architecture, and harness setup into executable project artifacts.
---

# Forge Project

Use this skill as the coordinator for Project Forge. It connects intake, creative direction, evidence gathering, architecture, and harness setup into one repeatable workflow.

Run commands from the plugin root, using plugin-root-relative script paths. If the plugin is installed into another project, first identify the plugin root, then run the scripts from there while passing the target project with `--project`.

## Coordinator Flow

1. Confirm the project slug, goal, target project directory, and preferred stack if one is known.
2. Gather or normalize evidence for consequential choices.
3. Write the architecture decision record.
4. Apply the harness template and command contract.
5. Verify the generated artifacts and report the paths that changed.
6. Export the Superpowers handoff when the project is ready for implementation.

Prefer the coordinator script when the user wants the whole Forge flow:

`python scripts/forge_project.py --project <target-project> --slug <project-slug> --goal "<project goal>" --stack <template> --evidence <evidence-json-or-jsonl>`

Use `--evidence <path>` when evidence already exists. Use `--force` only when the user expects existing Forge artifacts to be refreshed.

## Script Map

- `scripts/forge_project.py`: orchestrates research ingestion, ADR creation, and harness generation.
- `scripts/export_handoff.py`: writes `docs/superpowers-handoff.md` from evidence, ADR, harness docs, and `project-forge.yaml`.
- `scripts/harness/apply_template.py`: applies a harness template directly when only the command contract is needed.
- `scripts/research/github_search.py`: collects GitHub repository evidence into JSONL.
- `scripts/research/web_search.py`: records web evidence or host-tool search instructions.
- `scripts/research/normalize_evidence.py`: merges raw JSON or JSONL evidence into normalized evidence rows.

When running research manually, write raw sources into a temporary evidence directory, then normalize them into:

`docs/research/<project-slug>/evidence.jsonl`

## Required Outputs

The completed coordinator flow should produce or update:

- `docs/research/<project-slug>/evidence.jsonl`
- `docs/architecture/ADR-0001-stack.md`
- `project-forge.yaml`
- `docs/harness.md`
- `docs/superpowers-handoff.md`

The harness template may also add CI files when supported by the selected stack. Create the handoff with:

`python scripts/export_handoff.py --project <target-project> --slug <project-slug> --out <target-project>/docs/superpowers-handoff.md`

## Worker Coordination

Use `ai-architect` for deeper stack judgment, evidence interpretation, and ADR quality. Use `harness-engineer` for command contracts, smoke checks, CI behavior, and troubleshooting docs.

When other workers are active, do not overwrite their edits casually. Inspect existing Forge artifacts first, preserve user or worker changes, and only use `--force` when replacement is intentional.

## Quality Bar

The target project should be left with evidence-backed architecture, a runnable command contract, and a Superpowers handoff. A future worker should be able to read the ADR, run the commands in `project-forge.yaml`, understand the verification path from `docs/harness.md`, and consume `docs/superpowers-handoff.md` as the implementation packet.
