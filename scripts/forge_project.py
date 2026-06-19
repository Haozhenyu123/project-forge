#!/usr/bin/env python3
"""Coordinate Project Forge research, architecture, and harness artifacts."""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


GENERATED_FILES = (
    Path("docs") / "research" / "{slug}" / "evidence.jsonl",
    Path("docs") / "architecture" / "ADR-0001-stack.md",
    Path("project-forge.yaml"),
    Path("docs") / "harness.md",
    Path(".github") / "workflows" / "project-forge-ci.yml",
)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--stack", required=True)
    parser.add_argument("--secondary-stack", default="", help="Optional secondary stack for multi-stack projects")
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def repo_root():
    return Path(__file__).resolve().parents[1]


def import_copy_template():
    harness_dir = repo_root() / "scripts" / "harness"
    sys.path.insert(0, str(harness_dir))
    try:
        from apply_template import copy_template
    finally:
        try:
            sys.path.remove(str(harness_dir))
        except ValueError:
            pass
    return copy_template


def import_detect_helpers():
    harness_dir = repo_root() / "scripts" / "harness"
    sys.path.insert(0, str(harness_dir))
    try:
        from detect_stack import COMMANDS, node_commands
    finally:
        try:
            sys.path.remove(str(harness_dir))
        except ValueError:
            pass
    return COMMANDS, node_commands


def validate_slug(slug):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", slug):
        raise ValueError("Project slug must use lowercase letters, digits, and hyphens only.")
    if "--" in slug or slug.endswith("-"):
        raise ValueError("Project slug must not contain repeated or trailing hyphens.")
    return slug


def generated_targets(project, slug):
    for relative in GENERATED_FILES:
        yield project / Path(str(relative).format(slug=slug))


def refuse_existing(project, slug, force):
    existing = [path for path in generated_targets(project, slug) if path.exists()]
    if existing and not force:
        targets = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"Refusing to overwrite existing generated file(s): {targets}. Re-run with --force.")


def records_from_json(path):
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return payload["items"]
    if isinstance(payload, dict):
        return [payload]
    return []


def records_from_jsonl(path):
    rows = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def evidence_paths(evidence):
    if evidence.is_dir():
        return sorted(
            [
                path
                for path in evidence.iterdir()
                if path.is_file() and path.suffix.lower() in (".json", ".jsonl")
            ],
            key=lambda path: path.name,
        )
    return [evidence]


def iter_evidence_rows(evidence):
    for path in evidence_paths(evidence):
        suffix = path.suffix.lower()
        if suffix == ".jsonl":
            rows = records_from_jsonl(path)
        elif suffix == ".json":
            rows = records_from_json(path)
        else:
            raise ValueError(f"Evidence input must be .json, .jsonl, or a directory of those files: {path}")
        for row in rows:
            if isinstance(row, dict):
                yield row


def evidence_score(row):
    stars = row.get("stars")
    if stars is None:
        stars = row.get("stargazers_count")
    try:
        return int(stars)
    except (TypeError, ValueError):
        return 1


def is_provisional_evidence(row):
    if "provisional" in row:
        return bool(row["provisional"])
    return row.get("source") == "host-web-tool" or row.get("kind") == "manual-search-required"


def evidence_relevance(row):
    value = row.get("relevance") or row.get("summary") or row.get("description")
    if value:
        return str(value)
    if row.get("query"):
        return f"Manual research required for query: {row['query']}"
    return "Supports project research decision."


def normalize_evidence(rows, slug=""):
    normalized = []
    observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    for index, row in enumerate(rows, start=1):
        url = row.get("url") or row.get("html_url") or row.get("link")
        title = row.get("title") or row.get("name") or row.get("full_name")
        summary = row.get("summary") or row.get("description") or row.get("title") or ""
        item = dict(row)
        item["evidence_id"] = str(item.get("evidence_id") or f"E{index}")
        if url:
            item["url"] = url
        if title and "title" not in item:
            item["title"] = str(title)
        if summary:
            item["summary"] = str(summary)
        if slug and slug not in item.get("summary", ""):
            item['summary'] = f"{item.get('summary', '')} {slug}".strip()
        item["observed_at"] = str(item.get("observed_at") or observed_at)
        item["score"] = evidence_score(item)
        item["relevance"] = evidence_relevance(item)
        item["provisional"] = is_provisional_evidence(item)
        normalized.append(item)
    return normalized


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def adr_text(slug, stack, goal, evidence_rows, confidence_levels=None):
    lines = [
        "# ADR-0001: Project stack",
        "",
        "## Status",
        "",
        "Accepted",
        "",
        "## Context",
        "",
        f"- Project slug: `{slug}`",
        f"- Goal: {goal}",
        f"- Selected stack: `{stack}`",
        "",
    ]
    if evidence_rows:
        lines.append("## Evidence")
        lines.append("")
        for row in evidence_rows:
            evidence_id = str(row.get("evidence_id") or "E?")
            is_prov = " *(provisional)*" if row.get("provisional") else ""
            summary = str(row.get("summary") or row.get("title") or "Evidence item")
            url = row.get("url")
            if url:
                lines.append(f"- [{evidence_id}]{is_prov} {summary}: {url}")
            else:
                lines.append(f"- [{evidence_id}]{is_prov} {summary}")
        lines.append("")
    else:
        lines.append("## Evidence\n\n- No evidence rows were provided.\n")
    lines.extend([
        "## Decision",
        "",
        f"Use `{stack}` as the primary harness for `{slug}`.",
        "",
        "## Explicitly Rejected",
        "",
        '- run: `scripts/research/github_search.py --query "alternative keywords" --limit 5 --out docs/research/{slug}/alternatives.jsonl` to collect rejection evidence automatically.',
        "",
        "## Confidence Assessment",
        "",
    ])
    if confidence_levels:
        for decision_name, level, reason in confidence_levels:
            lines.append(f"- **{decision_name}**: {level} confidence -- {reason}")
    else:
        lines.append('- run: `python scripts/research/validate_evidence.py docs/research/{slug}/evidence.jsonl` to assess source quality, then assign High/Medium/Low per decision below.\n- **Stack choice**: Medium confidence (default) -- reassign after reviewing evidence.')
    lines.extend([
        "",
        "## Consequences",
        "",
        "- The repository receives a Project Forge harness contract and CI workflow.",
        "- Future architecture changes should cite updated research evidence.",
        "- Low-confidence decisions should be re-evaluated before expanding scope beyond MVP.",
        "",
        "## Risks and Revisit Triggers",
        "",
        "- If the project needs capabilities not covered by the current stack, revisit this ADR.",
        "- If a dependency becomes unmaintained or a better alternative emerges, schedule a re-evaluation.",
        "- If the chosen stack does not support a required Architecture Signal, escalate back to the architect.",
        "",
    ])
    return "\n".join(lines)


def yaml_scalar(value):
    text = str(value)
    return json.dumps(text)


def write_project_contract(path, slug, stack, goal, commands, secondary_stack=""):
    lines = [
        "project:",
        f"  slug: {yaml_scalar(slug)}",
        f"  goal: {yaml_scalar(goal)}",
        f"  stack: {yaml_scalar(stack)}",
    ]
    if secondary_stack:
        lines.append(f"  secondary_stack: {yaml_scalar(secondary_stack)}")
    lines.append("commands:")
    for name in ("install", "test", "lint", "typecheck", "build", "run", "smoke"):
        lines.append(f"  {name}: {commands.get(name, 'echo command not configured')}")
    if secondary_stack:
        lines.append("secondary_commands:")
        for name in ("install", "test", "lint", "typecheck", "build", "run", "smoke"):
            lines.append(f"  {name}: echo secondary stack command not configured")
    text = "\n".join(lines) + "\n"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def commands_for_project(project, stack):
    commands_by_template, node_commands_fn = import_detect_helpers()
    NODE_STACKS = {"node-ts", "nextjs", "electron", "cli", "chrome-extension"}
    if stack in NODE_STACKS:
        root = Path(project)
        if (root / "package.json").exists():
            _, commands = node_commands_fn(root)
            return commands
        return commands_by_template.get(stack, commands_by_template["node-ts"])
    return commands_by_template.get(stack, commands_by_template["generic"])


def write_ci_contract(path, stack, commands):
    verify_names = ("install", "test", "lint", "typecheck", "build", "smoke")
    NODE_STACKS = {"node-ts", "nextjs", "electron", "cli", "chrome-extension"}
    PYTHON_STACKS = {"python", "fastapi"}
    lines = [
        "name: Project Forge CI",
        "",
        "on:",
        "  push:",
        "  pull_request:",
        "",
        "jobs:",
        "  verify:",
        "    name: Project Forge CI",
        "    runs-on: ubuntu-latest",
        "    steps:",
        "      - uses: actions/checkout@v4",
    ]
    if stack in NODE_STACKS:
        lines.extend(
            [
                "      - uses: actions/setup-node@v4",
                "        with:",
                "          node-version: \"22\"",
                "      - run: corepack enable",
            ]
        )
    elif stack in PYTHON_STACKS:
        lines.extend(
            [
                "      - uses: actions/setup-python@v5",
                "        with:",
                "          python-version: \"3.12\"",
            ]
        )
    for name in verify_names:
        lines.append(f"      - run: {commands[name]}")
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")

def write_handoff_text(slug, stack, goal, evidence_rows, commands):
    """Generate superpowers-handoff.md from project artifacts."""
    evidence_list = []
    for row in evidence_rows[:5]:
        eid = row.get("evidence_id", "?")
        title = row.get("title", "Unknown")
        url = row.get("url", "")
        summary = row.get("summary", "")[:120]
        evidence_list.append(f"- [{eid}] {title}: {summary} ({url})")

    evidence_block = "\n".join(evidence_list) if evidence_list else "No evidence recorded."
    commands_block = "\n".join(f"- `{k}`: {v}" for k, v in commands.items())

    return f"""# Superpowers Handoff

## Brief

- Project slug: `{slug}`
- Goal: {goal}
- Stack signal: {stack}
- Assignment: consume this packet, preserve the evidence-backed architecture, and implement against the harness contract.

## Creative Direction

- Build the smallest coherent product experience that satisfies the goal and keeps future iteration easy.
- Keep user-facing choices aligned with the accepted ADR and the current harness constraints.
- When product direction is ambiguous, make the assumption explicit under Open Questions before expanding scope.

## Evidence

Source: `docs/research/{slug}/evidence.jsonl`

{evidence_block}

## Architecture Decision

See `docs/architecture/ADR-0001-stack.md` for the full decision record.

## Harness Contract

See `project-forge.yaml` and `docs/harness.md` for the full harness contract.

{commands_block}

## Open Questions

- Left blank intentionally; fill in as the implementation progresses.
"""


def main():
    args = parse_args()
    project = Path(args.project)
    slug = validate_slug(args.slug)
    evidence = Path(args.evidence)
    research_path = project / "docs" / "research" / slug / "evidence.jsonl"
    adr_path = project / "docs" / "architecture" / "ADR-0001-stack.md"
    contract_path = project / "project-forge.yaml"
    ci_path = project / ".github" / "workflows" / "project-forge-ci.yml"

    try:
        if not evidence.exists():
            raise FileNotFoundError(f"Evidence input does not exist: {evidence}")
        refuse_existing(project, slug, args.force)
        rows = normalize_evidence(iter_evidence_rows(evidence), slug)

        project.mkdir(parents=True, exist_ok=True)
        copy_template = import_copy_template()
        copy_template(args.stack, project, args.force)
        commands = commands_for_project(project, args.stack)

        write_jsonl(research_path, rows)
        adr_path.parent.mkdir(parents=True, exist_ok=True)
        with adr_path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(adr_text(slug, args.stack, args.goal, rows))

        write_project_contract(contract_path, slug, args.stack, args.goal, commands, args.secondary_stack)
        write_ci_contract(ci_path, args.stack, commands)
        handoff_path = project / "docs" / "superpowers-handoff.md"
        handoff_path.parent.mkdir(parents=True, exist_ok=True)
        with handoff_path.open("w", encoding="utf-8", newline="\n") as hf:
            hf.write(write_handoff_text(slug, args.stack, args.goal, rows, commands))
    except (FileExistsError, FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())




