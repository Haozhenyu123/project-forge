#!/usr/bin/env python3
"""Check whether Project Forge artifacts are ready for Superpowers consumption."""

import argparse
import json
import sys
from pathlib import Path


COMMAND_ORDER = ("install", "test", "lint", "typecheck", "build", "run", "smoke")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="Project directory to validate.")
    parser.add_argument("--slug", required=True, help="Expected project slug.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    return parser.parse_args()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path):
    rows = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}: line {line_number} is invalid JSON: {exc}") from exc
    return rows


def add(checks, check_id, status, message, path=None):
    item = {"id": check_id, "status": status, "message": message}
    if path:
        item["path"] = str(path).replace("\\", "/")
    checks.append(item)


def required_artifacts(project, slug):
    return {
        "evidence": project / "docs" / "research" / slug / "evidence.jsonl",
        "adr": project / "docs" / "architecture" / "ADR-0001-stack.md",
        "contract": project / "project-forge.yaml",
        "harness": project / "docs" / "harness.md",
        "handoff_markdown": project / "docs" / "superpowers-handoff.md",
        "handoff_json": project / "docs" / "superpowers-handoff.json",
    }


def validate_artifacts(checks, paths):
    missing = []
    for name, path in paths.items():
        if path.is_file():
            add(checks, f"artifact.{name}", "pass", f"Found {name}.", path)
        else:
            missing.append(name)
            add(checks, f"artifact.{name}", "fail", f"Missing {name}.", path)
    return missing


def validate_evidence(checks, path, slug):
    try:
        rows = read_jsonl(path)
    except (OSError, ValueError) as exc:
        add(checks, "evidence.readable", "fail", str(exc), path)
        return []
    if not rows:
        add(checks, "evidence.rows", "fail", "Evidence file has no rows.", path)
        return rows
    add(checks, "evidence.rows", "pass", f"Evidence has {len(rows)} row(s).", path)
    if any(slug in json.dumps(row, sort_keys=True) for row in rows):
        add(checks, "evidence.slug", "pass", "Evidence references the expected slug.", path)
    else:
        add(checks, "evidence.slug", "warn", "Evidence does not mention the expected slug.", path)
    provisional = [row for row in rows if row.get("provisional")]
    if len(provisional) == len(rows):
        add(checks, "evidence.verified", "warn", "All evidence rows are provisional.", path)
    else:
        add(checks, "evidence.verified", "pass", "At least one evidence row is non-provisional.", path)
    return rows


def validate_adr(checks, path):
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        add(checks, "adr.readable", "fail", str(exc), path)
        return
    required = (
        "## Considered Options",
        "## Decision",
        "## Explicitly Rejected",
        "## Confidence Assessment",
        "## Risks and Revisit Triggers",
    )
    missing = [section for section in required if section not in text]
    if missing:
        add(checks, "adr.sections", "fail", "ADR missing section(s): " + ", ".join(missing), path)
    else:
        add(checks, "adr.sections", "pass", "ADR contains decision-quality sections.", path)


def validate_markdown_handoff(checks, path):
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        add(checks, "handoff.markdown", "fail", str(exc), path)
        return
    required = (
        "## Brief",
        "## Evidence",
        "## Harness Commands",
        "## Acceptance Criteria",
        "## Guardrails",
        "## How Superpowers Should Consume This",
    )
    missing = [section for section in required if section not in text]
    if missing:
        add(checks, "handoff.markdown", "fail", "Markdown handoff missing section(s): " + ", ".join(missing), path)
    else:
        add(checks, "handoff.markdown", "pass", "Markdown handoff contains Superpowers consumption sections.", path)


def validate_json_handoff(checks, path, slug):
    try:
        packet = read_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        add(checks, "handoff.json", "fail", f"Cannot read handoff JSON: {exc}", path)
        return {}
    if packet.get("schema_version") != 1:
        add(checks, "handoff.schema", "fail", "Expected schema_version 1.", path)
    else:
        add(checks, "handoff.schema", "pass", "Structured handoff schema version is supported.", path)
    if packet.get("kind") != "project-forge.superpowers-handoff":
        add(checks, "handoff.kind", "fail", "Unexpected handoff kind.", path)
    else:
        add(checks, "handoff.kind", "pass", "Structured handoff kind is correct.", path)
    project_slug = (packet.get("project") or {}).get("slug")
    if project_slug == slug:
        add(checks, "handoff.slug", "pass", "Structured handoff slug matches.", path)
    else:
        add(checks, "handoff.slug", "fail", f"Expected slug {slug!r}, got {project_slug!r}.", path)
    commands = ((packet.get("harness") or {}).get("commands") or {})
    missing_commands = [name for name in COMMAND_ORDER if name not in commands]
    if missing_commands:
        add(checks, "handoff.commands", "fail", "Missing command(s): " + ", ".join(missing_commands), path)
    else:
        add(checks, "handoff.commands", "pass", "Structured handoff contains all required harness commands.", path)
    superpowers = packet.get("superpowers") or {}
    for key in ("assignment", "first_task", "acceptance_criteria", "guardrails", "consume_steps"):
        value = superpowers.get(key)
        if value:
            add(checks, f"handoff.superpowers.{key}", "pass", f"Structured handoff has {key}.", path)
        else:
            add(checks, f"handoff.superpowers.{key}", "fail", f"Structured handoff missing {key}.", path)
    boundary = packet.get("boundary") or {}
    if boundary.get("project_forge_owns") and boundary.get("superpowers_owns"):
        add(checks, "handoff.boundary", "pass", "Boundary between Project Forge and Superpowers is explicit.", path)
    else:
        add(checks, "handoff.boundary", "fail", "Boundary section is incomplete.", path)
    return packet


def summarize(checks, strict=False):
    failures = [check for check in checks if check["status"] == "fail"]
    warnings = [check for check in checks if check["status"] == "warn"]
    passed = [check for check in checks if check["status"] == "pass"]
    score = int(round(100 * len(passed) / max(1, len(checks))))
    if failures or (strict and warnings):
        status = "blocked"
    elif warnings:
        status = "attention"
    else:
        status = "ready"
    next_actions = []
    if failures:
        next_actions.append("Fix failed checks, then rerun project-forge superpowers-ready.")
    if warnings:
        next_actions.append("Review warnings before handing broad implementation work to Superpowers.")
    if not next_actions:
        next_actions.append("Hand this packet to Superpowers for implementation planning and execution.")
    return {
        "status": status,
        "score": score,
        "passed": len(passed),
        "warnings": len(warnings),
        "failures": len(failures),
        "checks": checks,
        "next_actions": next_actions,
    }


def run(project, slug, strict=False):
    project = Path(project)
    checks = []
    if project.is_dir():
        add(checks, "project.directory", "pass", "Project directory exists.", project)
    else:
        add(checks, "project.directory", "fail", "Project directory is missing.", project)
        return summarize(checks, strict)
    paths = required_artifacts(project, slug)
    missing = validate_artifacts(checks, paths)
    if "evidence" not in missing:
        validate_evidence(checks, paths["evidence"], slug)
    if "adr" not in missing:
        validate_adr(checks, paths["adr"])
    if "handoff_markdown" not in missing:
        validate_markdown_handoff(checks, paths["handoff_markdown"])
    if "handoff_json" not in missing:
        validate_json_handoff(checks, paths["handoff_json"], slug)
    return summarize(checks, strict)


def print_human(payload, project, slug):
    print(f"Project Forge Superpowers readiness: {payload['status']} ({payload['score']}%)")
    print(f"Project: {project}")
    print(f"Slug: {slug}")
    for check in payload["checks"]:
        marker = {"pass": "OK", "warn": "WARN", "fail": "FAIL"}[check["status"]]
        print(f"  [{marker}] {check['id']}: {check['message']}")
    print("Next:")
    for action in payload["next_actions"]:
        print(f"  - {action}")


def main():
    args = parse_args()
    payload = run(args.project, args.slug, args.strict)
    payload["project"] = str(Path(args.project)).replace("\\", "/")
    payload["slug"] = args.slug
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_human(payload, args.project, args.slug)
    if payload["status"] == "blocked":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
