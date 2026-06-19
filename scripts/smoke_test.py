#!/usr/bin/env python3
"""Validate the Project Forge smoke-test example project."""

import argparse
import json
import sys
from pathlib import Path


REQUIRED_FILES = (
    Path("docs") / "research" / "{slug}" / "evidence.jsonl",
    Path("docs") / "architecture" / "ADR-0001-stack.md",
    Path("project-forge.yaml"),
    Path("docs") / "harness.md",
    Path("docs") / "superpowers-handoff.md",
)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="Project directory to validate.")
    parser.add_argument("--slug", required=True, help="Expected project slug.")
    return parser.parse_args()


def required_paths(project, slug):
    for relative in REQUIRED_FILES:
        yield Path(str(relative).format(slug=slug)), project / Path(str(relative).format(slug=slug))


def validate_evidence(path, slug):
    required_keys = {
        "evidence_id",
        "source",
        "title",
        "url",
        "summary",
        "observed_at",
        "relevance",
        "provisional",
    }
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}: line {line_number} is not valid JSON: {exc}") from exc
            missing = sorted(required_keys - set(row))
            if missing and not row.get("provisional"):
                raise ValueError(f"{path}: line {line_number} missing keys: {', '.join(missing)}")
            rows.append(row)
    if not rows:
        raise ValueError(f"{path}: evidence.jsonl must contain at least one row")
    if not any(slug in json.dumps(row, sort_keys=True) for row in rows):
        raise ValueError(f"{path}: evidence rows do not contain slug {slug!r}")
    return len(rows)


def fail(message):
    print(json.dumps({"status": "error", "error": message}, sort_keys=True), file=sys.stderr)
    return 1


def main():
    args = parse_args()
    project = Path(args.project)
    slug = args.slug

    if not project.exists():
        return fail(f"Project directory does not exist: {project}")
    if not project.is_dir():
        return fail(f"Project path is not a directory: {project}")

    checked = []
    try:
        SLUG_REQUIRED = {"evidence.jsonl", "project-forge.yaml"}
        for relative, path in required_paths(project, slug):
            if not path.exists():
                return fail(f"Missing required file: {relative}")
            text = path.read_text(encoding="utf-8")
            if relative.name in SLUG_REQUIRED and slug not in text:
                return fail(f"Required file does not contain slug {slug!r}: {relative}")
            checked.append(str(relative).replace("\\", "/"))
        evidence_count = validate_evidence(
            project / "docs" / "research" / slug / "evidence.jsonl",
            slug,
        )
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return fail(str(exc))

    print(
        json.dumps(
            {
                "status": "ok",
                "project": str(project).replace("\\", "/"),
                "slug": slug,
                "checked": checked,
                "evidence_count": evidence_count,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())



