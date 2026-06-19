#!/usr/bin/env python3
"""Apply a Project Forge harness template to a project."""

import argparse
import shutil
import sys
from pathlib import Path


TEMPLATE_FILES = (
    Path("project-forge.yaml"),
    Path("docs") / "harness.md",
    Path(".github") / "workflows" / "project-forge-ci.yml",
)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def repo_root():
    return Path(__file__).resolve().parents[2]


def copy_template(template, project, force):
    template_root = repo_root() / "templates" / "harness" / template
    if not template_root.is_dir():
        raise ValueError(f"Unknown harness template: {template}")

    project_root = Path(project)
    copies = [(template_root / relative, project_root / relative) for relative in TEMPLATE_FILES]
    missing_sources = [source for source, _ in copies if not source.is_file()]
    if missing_sources:
        missing = ", ".join(str(path) for path in missing_sources)
        raise FileNotFoundError(f"Template {template} is missing required file(s): {missing}")

    existing_targets = [target for _, target in copies if target.exists()]
    if existing_targets and not force:
        existing = ", ".join(str(path) for path in existing_targets)
        raise FileExistsError(f"Refusing to overwrite existing file(s): {existing}. Re-run with --force.")

    for source, target in copies:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def main():
    args = parse_args()
    try:
        copy_template(args.template, args.project, args.force)
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
