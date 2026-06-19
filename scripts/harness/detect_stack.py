#!/usr/bin/env python3
"""Detect a project stack and emit a Project Forge harness command contract."""

import argparse
import json
import sys
from pathlib import Path


COMMANDS = {
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

NODE_SCRIPT_COMMANDS = ("test", "lint", "typecheck", "build", "smoke")


def failing_node_command(script_name):
    return (
        "node -e \"console.error('No package.json script named "
        + script_name
        + " configured'); process.exit(1)\""
    )


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


def detect_package_manager(root):
    for lockfile, package_manager in (
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "yarn"),
        ("package-lock.json", "npm"),
    ):
        if (root / lockfile).exists():
            return package_manager
    return "npm"


def load_package_scripts(root):
    package_json = root / "package.json"
    try:
        payload = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    scripts = payload.get("scripts", {})
    if not isinstance(scripts, dict):
        return {}
    return {name for name, command in scripts.items() if isinstance(name, str) and command}


def node_commands(root):
    package_manager = detect_package_manager(root)
    scripts = load_package_scripts(root)
    commands = {"install": f"{package_manager} install"}

    for script_name in NODE_SCRIPT_COMMANDS:
        if script_name in scripts:
            commands[script_name] = f"{package_manager} run {script_name}"
        else:
            commands[script_name] = failing_node_command(script_name)

    if "dev" in scripts:
        commands["run"] = f"{package_manager} run dev"
    elif "start" in scripts:
        commands["run"] = f"{package_manager} start"
    else:
        commands["run"] = failing_node_command("dev or start")

    return package_manager, commands


def main():
    args = parse_args()
    root = Path(args.project)
    template = detect_template(root)
    package_manager = None
    if template == "node-ts":
        package_manager, commands = node_commands(root)
    else:
        commands = COMMANDS[template]
    payload = {
        "template": template,
        "package_manager": package_manager,
        "commands": commands,
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(template)
    return 0


if __name__ == "__main__":
    sys.exit(main())
