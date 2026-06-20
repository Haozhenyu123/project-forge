#!/usr/bin/env python3
"""Detect a project stack and emit a Project Forge harness command contract.

Uses template manifests for detection signals and commands.
"""

import argparse
import json
import re
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
from project_forge.harness.templates import (
    load_manifests,
    MANIFEST_REGISTRY,
    TemplateManifest,
)

MANIFESTS = {}


def _ensure_manifests():
    global MANIFESTS
    if not MANIFESTS:
        MANIFESTS = load_manifests()


def detect_by_manifest(project: Path) -> str:
    _ensure_manifests()
    pkg_json = project / "package.json"
    manifest_json = project / "manifest.json"

    # Chrome extension: manifest.json in project root
    if manifest_json.exists():
        try:
            payload = json.loads(manifest_json.read_text(encoding="utf-8"))
            if "manifest_version" in payload:
                return "chrome-extension"
        except (OSError, json.JSONDecodeError):
            pass

    # Node-based projects
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pkg = {}
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

        # Check each manifest for dependency matches
        # Order matters: specific frameworks first
        ordered = ["nextjs", "electron", "cli", "node-ts"]
        for kind in ordered:
            m = MANIFESTS.get(kind)
            if not m or not m.detection:
                continue
            req_deps = m.detection.get("dependencies", [])
            excl_deps = m.detection.get("exclude_dependencies", [])
            has_bin = m.detection.get("has_bin", False)

            if req_deps and any(d in deps for d in req_deps):
                return kind
            if excl_deps and any(d in deps for d in excl_deps):
                continue
            if has_bin and "bin" in pkg and isinstance(pkg["bin"], (str, dict)):
                return kind

        return "node-ts"

    # Python-based projects
    if (project / "pyproject.toml").exists() or (project / "requirements.txt").exists():
        if (project / "main.py").exists():
            main_text = (project / "main.py").read_text(encoding="utf-8")
            if "fastapi" in main_text.lower() or "FastAPI" in main_text:
                return "fastapi"
        return "python"

    # Standalone main.py (no requirements.txt/pyproject.toml)
    if (project / "main.py").exists():
        main_text = (project / "main.py").read_text(encoding="utf-8")
        if "fastapi" in main_text.lower() or "FastAPI" in main_text:
            return "fastapi"
        return "python"

    # Fallback: read stack from existing project-forge.yaml
    forge_yaml = project / "project-forge.yaml"
    if forge_yaml.exists():
        yaml_text = forge_yaml.read_text(encoding="utf-8")
        match = re.search(r'^\s*stack:\s*"?([^"\s]+)"?\s*$', yaml_text, re.MULTILINE)
        if match:
            known = match.group(1).strip('"')
            if known in MANIFESTS:
                return known

    return "generic"


def detect_package_manager(root):
    for lockfile, pm in (
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "yarn"),
        ("package-lock.json", "npm"),
    ):
        if (root / lockfile).exists():
            return pm
    return "npm"


def load_package_scripts(root):
    package_json = root / "package.json"
    try:
        payload = json.loads(package_json.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    scripts = payload.get("scripts", {})
    if not isinstance(scripts, dict):
        return {}
    return {name for name, command in scripts.items() if isinstance(name, str) and command}


def node_commands(root):
    pm = detect_package_manager(root)
    scripts = load_package_scripts(root)
    cmds = {"install": f"{pm} install"}
    for name in ("test", "lint", "typecheck", "build", "smoke"):
        cmds[name] = f"{pm} run {name}" if name in scripts else f"node -e \"console.error('No script: {name}'); process.exit(1)\""
    cmds["run"] = f"{pm} run dev" if "dev" in scripts else (f"{pm} start" if "start" in scripts else "node -e \"console.error('No dev/start'); process.exit(1)\"")
    return pm, cmds


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project", required=True)
    p.add_argument("--json", action="store_true")
    return p.parse_args()



# Backward-compatible exports for forge_project.py
# Eagerly load manifests for module-level COMMANDS
_ensure_manifests()
COMMANDS = {}
for _k, _m in MANIFESTS.items():
    COMMANDS[_k] = {}
    for _cmd, _argv in _m.commands.items():
        COMMANDS[_k][_cmd] = ' '.join(_argv)

NODE_TEMPLATES = {'node-ts', 'nextjs', 'electron', 'cli', 'chrome-extension'}

def node_commands(root):
    """Return (package_manager, commands_dict) for a Node project."""
    pm = detect_package_manager(root)
    scripts = load_package_scripts(root)
    cmds = {'install': f'{pm} install'}
    for name in ('test', 'lint', 'typecheck', 'build', 'smoke'):
        cmds[name] = f'{pm} run {name}' if name in scripts else 'echo No script configured'
    cmds['run'] = f'{pm} run dev' if 'dev' in scripts else (f'{pm} start' if 'start' in scripts else 'echo No run command')
    return pm, cmds

def main():
    args = parse_args()
    root = Path(args.project)
    template = detect_by_manifest(root)
    pm = None
    if template in ("node-ts", "nextjs", "electron", "cli"):
        pm, cmds = node_commands(root)
    else:
        _ensure_manifests()
        m = MANIFESTS.get(template)
        cmds = {k: " ".join(v) for k, v in m.commands.items()} if m else {}
    payload = {"template": template, "package_manager": pm, "commands": cmds}
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(template)
    return 0


if __name__ == "__main__":
    sys.exit(main())
