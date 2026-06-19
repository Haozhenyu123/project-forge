#!/usr/bin/env python3
"""Export a Superpowers implementation handoff from Project Forge artifacts."""

import argparse
import json
import sys
from pathlib import Path


COMMAND_ORDER = ("install", "test", "lint", "typecheck", "build", "run", "smoke")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--out", required=True)
    return parser.parse_args()


def read_jsonl(path):
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL in {path} on line {line_number}: {exc}") from exc
            if isinstance(value, dict):
                rows.append(value)
    return rows


def strip_quotes(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def parse_project_forge(text):
    commands = {}
    project = {}
    section = None
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith((" ", "\t")) and raw_line.rstrip().endswith(":"):
            section = raw_line.strip()[:-1]
            continue
        if section not in {"commands", "project"}:
            continue
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = strip_quotes(value)
        if section == "commands" and key:
            commands[key] = value
        elif section == "project" and key:
            project[key] = value
    return project, commands


def first_nonempty_lines(text, limit):
    return [line.rstrip() for line in text.splitlines() if line.strip()][:limit]


def markdown_list(items, empty):
    if not items:
        return [f"- {empty}"]
    return [f"- {item}" for item in items]


def evidence_lines(rows):
    lines = []
    for index, row in enumerate(rows[:8], start=1):
        evidence_id = row.get("evidence_id") or f"E{index}"
        title = row.get("title") or row.get("name") or row.get("source") or "Evidence item"
        summary = row.get("summary") or row.get("description") or row.get("relevance") or "No summary provided."
        url = row.get("url") or row.get("html_url") or row.get("link")
        provisional = " provisional" if row.get("provisional") else ""
        if url:
            lines.append(f"[{evidence_id}]{provisional} {title}: {summary} ({url})")
        else:
            lines.append(f"[{evidence_id}]{provisional} {title}: {summary}")
    return markdown_list(lines, "No evidence rows were found.")


def command_lines(commands):
    ordered = []
    for name in COMMAND_ORDER:
        if name in commands:
            ordered.append(f"`{name}`: `{commands[name]}`")
    for name in sorted(set(commands) - set(COMMAND_ORDER)):
        ordered.append(f"`{name}`: `{commands[name]}`")
    return markdown_list(ordered, "No commands were found in project-forge.yaml.")


def risk_lines(evidence_rows, commands):
    risks = []
    provisional = [row for row in evidence_rows if row.get("provisional")]
    if provisional:
        risks.append(f"{len(provisional)} evidence row(s) are provisional and need confirmation before major architecture changes.")
    missing = [name for name in COMMAND_ORDER if name not in commands]
    if missing:
        risks.append(f"Missing harness command(s): {', '.join(missing)}.")
    if not risks:
        risks.append("No handoff-specific risks were detected; still verify commands in the target project.")
    return markdown_list(risks, "No risks recorded.")


def render_handoff(slug, project_meta, evidence_rows, adr_text, forge_text, harness_text, commands):
    goal = project_meta.get("goal") or "Read the Forge artifacts and implement the next scoped feature."
    stack = project_meta.get("stack") or project_meta.get("chosen_stack") or "See ADR-0001-stack.md"
    adr_excerpt = first_nonempty_lines(adr_text, 12)
    harness_excerpt = first_nonempty_lines(harness_text, 12)

    lines = [
        "# Superpowers Handoff",
        "",
        "## Brief",
        "",
        f"- Project slug: `{slug}`",
        f"- Goal: {goal}",
        f"- Stack signal: {stack}",
        "- Assignment: consume this packet, preserve the evidence-backed architecture, and implement against the harness contract.",
        "",
        "## Creative Direction",
        "",
        "- Build the smallest coherent product experience that satisfies the goal and keeps future iteration easy.",
        "- Keep user-facing choices aligned with the accepted ADR and the current harness constraints.",
        "- When product direction is ambiguous, make the assumption explicit under Open Questions before expanding scope.",
        "",
        "## Evidence",
        "",
        f"Source: `docs/research/{slug}/evidence.jsonl`",
        "",
        *evidence_lines(evidence_rows),
        "",
        "## ADR",
        "",
        "Read `docs/architecture/ADR-0001-stack.md` before changing architecture or dependencies.",
        "",
        "```markdown",
        *adr_excerpt,
        "```",
        "",
        "## Harness Commands",
        "",
        "Source: `project-forge.yaml`",
        "",
        *command_lines(commands),
        "",
        "Harness notes from `docs/harness.md`:",
        "",
        "```markdown",
        *harness_excerpt,
        "```",
        "",
        "## Risks",
        "",
        *risk_lines(evidence_rows, commands),
        "",
        "## Open Questions",
        "",
        "- Which feature or workflow should Superpowers implement first if the brief does not name one?",
        "- Are any provisional evidence rows strong enough to keep, or should they be replaced with verified sources?",
        "- Do harness failures represent implementation defects, missing dependencies, or an outdated command contract?",
        "",
        "## How Superpowers Should Consume This",
        "",
        "1. Read this handoff first, then open `ADR-0001-stack.md`, the evidence JSONL, and harness docs only as needed.",
        "2. Treat `project-forge.yaml` as the source of truth for verification commands such as `npm run test` when present.",
        "3. Keep implementation changes scoped to the brief and update this handoff when risks, commands, or architecture assumptions change.",
        "",
        "## Raw Command Contract",
        "",
        "```yaml",
        forge_text.rstrip(),
        "```",
        "",
    ]
    return "\n".join(lines)


def export_handoff(project, slug, out):
    project = Path(project)
    paths = {
        "evidence": project / "docs" / "research" / slug / "evidence.jsonl",
        "adr": project / "docs" / "architecture" / "ADR-0001-stack.md",
        "forge": project / "project-forge.yaml",
        "harness": project / "docs" / "harness.md",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required handoff input(s): " + ", ".join(missing))

    evidence_rows = read_jsonl(paths["evidence"])
    adr_text = paths["adr"].read_text(encoding="utf-8")
    forge_text = paths["forge"].read_text(encoding="utf-8")
    harness_text = paths["harness"].read_text(encoding="utf-8")
    project_meta, commands = parse_project_forge(forge_text)

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_handoff(slug, project_meta, evidence_rows, adr_text, forge_text, harness_text, commands))


def main():
    args = parse_args()
    try:
        export_handoff(args.project, args.slug, args.out)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
