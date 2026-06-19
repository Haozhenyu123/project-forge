#!/usr/bin/env python3
"""Detect a project stack and emit a Project Forge harness command contract."""

import argparse
import json
import sys
from pathlib import Path


COMMANDS = {
    "node-ts": {
        "install": "npm install",
        "test": "npm test",
        "lint": "npm run lint",
        "typecheck": "npm run typecheck",
        "build": "npm run build",
        "run": "npm start",
        "smoke": "npm test",
    },
    "python": {
        "install": "python -m pip install -r requirements.txt",
        "test": "python -m pytest",
        "lint": "python -m ruff check .",
        "typecheck": "python -m mypy .",
        "build": "python -m build",
        "run": "python -m app",
        "smoke": "python -m pytest",
    },
    "generic": {
        "install": "echo no install command configured",
        "test": "echo no test command configured",
        "lint": "echo no lint command configured",
        "typecheck": "echo no typecheck command configured",
        "build": "echo no build command configured",
        "run": "echo no run command configured",
        "smoke": "echo no smoke command configured",
    },
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def detect_template(project):
    root = Path(project)
    if (root / "package.json").exists():
        return "node-ts"
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
        return "python"
    return "generic"


def main():
    args = parse_args()
    template = detect_template(args.project)
    payload = {"template": template, "commands": COMMANDS[template]}
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(template)
    return 0


if __name__ == "__main__":
    sys.exit(main())
