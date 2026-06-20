import json
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from project_forge.models import CommandSpec


@dataclass
class TemplateManifest:
    name: str
    kind: str
    aliases: List[str] = field(default_factory=list)
    detection: Dict[str, Any] = field(default_factory=dict)
    commands: Dict[str, List[str]] = field(default_factory=dict)
    ci: Dict[str, Any] = field(default_factory=dict)

    def argv_for(self, command: str) -> List[str]:
        return list(self.commands.get(command, []))


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_manifest(template_dir: Path) -> Optional[TemplateManifest]:
    manifest_path = template_dir / "manifest.json"
    if not manifest_path.is_file():
        return None
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return TemplateManifest(
        name=str(payload.get("name", "")),
        kind=str(payload.get("kind", "")),
        aliases=[str(s) for s in payload.get("aliases", [])],
        detection=dict(payload.get("detection", {})),
        commands={k: [str(a) for a in v] for k, v in payload.get("commands", {}).items()},
        ci=dict(payload.get("ci", {})),
    )


def load_manifests(repo_root: Optional[Path] = None) -> Dict[str, TemplateManifest]:
    root = repo_root or _repo_root()
    harness_dir = root / "templates" / "harness"
    if not harness_dir.is_dir():
        return {}
    manifests: Dict[str, TemplateManifest] = {}
    for child in sorted(harness_dir.iterdir()):
        if not child.is_dir():
            continue
        manifest = _load_manifest(child)
        if manifest:
            manifests[manifest.kind] = manifest
    return manifests


MANIFEST_REGISTRY: Dict[str, TemplateManifest] = {}


TEMPLATES = {
    "node-ts": {
        "install": (["npm", "ci"], True),
        "test": (["npm", "test"], False),
        "lint": (["npm", "run", "lint"], False),
        "typecheck": (["npm", "run", "typecheck"], False),
        "build": (["npm", "run", "build"], True),
        "run": (["npm", "start"], True),
        "smoke": (["npm", "run", "smoke"], False),
    },
    "nextjs": {
        "install": (["npm", "ci"], True),
        "test": (["npm", "run", "test"], False),
        "lint": (["npm", "run", "lint"], False),
        "typecheck": (["npm", "run", "typecheck"], False),
        "build": (["npm", "run", "build"], True),
        "run": (["npm", "run", "dev"], True),
        "smoke": (["npm", "run", "smoke"], False),
    },
    "electron": {
        "install": (["npm", "ci"], True),
        "test": (["npm", "run", "test"], False),
        "lint": (["npm", "run", "lint"], False),
        "typecheck": (["npm", "run", "typecheck"], False),
        "build": (["npm", "run", "build"], True),
        "run": (["npm", "start"], True),
        "smoke": (["npm", "run", "smoke"], False),
    },
    "cli": {
        "install": (["npm", "ci"], True),
        "test": (["npm", "run", "test"], False),
        "lint": (["npm", "run", "lint"], False),
        "typecheck": (["npm", "run", "typecheck"], False),
        "build": (["npm", "run", "build"], True),
        "run": (["node", "dist/index.js"], True),
        "smoke": (["npm", "run", "smoke"], False),
    },
    "chrome-extension": {
        "install": (["npm", "ci"], True),
        "test": (["npm", "run", "test"], False),
        "lint": (["npm", "run", "lint"], False),
        "typecheck": (["npm", "run", "typecheck"], False),
        "build": (["npm", "run", "build"], True),
        "run": (["python", "-c", "print('Load the extension from chrome://extensions')"], False),
        "smoke": (["npm", "run", "smoke"], False),
    },
    "python": {
        "install": (["python", "-m", "pip", "install", "-r", "requirements.txt"], True),
        "test": (["python", "-m", "pytest"], False),
        "lint": (["python", "-m", "ruff", "check", "."], False),
        "typecheck": (["python", "-m", "mypy", "."], False),
        "build": (["python", "-m", "build"], True),
        "run": (["python", "-m", "app"], True),
        "smoke": (["python", "-m", "pytest", "-m", "smoke"], False),
    },
    "fastapi": {
        "install": (["python", "-m", "pip", "install", "-r", "requirements.txt"], True),
        "test": (["python", "-m", "pytest"], False),
        "lint": (["python", "-m", "ruff", "check", "."], False),
        "typecheck": (["python", "-m", "mypy", "."], False),
        "build": (["python", "-m", "compileall", "app"], True),
        "run": (["python", "-m", "uvicorn", "app.main:app", "--reload"], True),
        "smoke": (["python", "-m", "pytest", "tests/smoke"], False),
    },
    "generic": {
        "install": (["python", "-c", "print('No install command configured')"], False),
        "test": (["python", "-c", "print('No test command configured')"], False),
        "lint": (["python", "-c", "print('No lint command configured')"], False),
        "typecheck": (["python", "-c", "print('No typecheck command configured')"], False),
        "build": (["python", "-c", "print('No build command configured')"], False),
        "run": (["python", "-c", "print('No run command configured')"], False),
        "smoke": (["python", "-c", "print('No smoke command configured')"], False),
    },
}


def _ensure_registry():
    global MANIFEST_REGISTRY
    if not MANIFEST_REGISTRY:
        MANIFEST_REGISTRY = load_manifests()


def commands_for(template, root="."):
    if template not in TEMPLATES:
        raise ValueError(f"unknown harness template: {template}")
    return {
        name: CommandSpec(argv=deepcopy(argv), cwd=root, mutates=mutates)
        for name, (argv, mutates) in TEMPLATES[template].items()
    }


def manifest_commands_for(template: str, root: str = ".") -> Dict[str, CommandSpec]:
    _ensure_registry()
    manifest = MANIFEST_REGISTRY.get(template)
    if not manifest:
        return commands_for(template, root)
    return {name: CommandSpec(argv=deepcopy(argv), cwd=root, mutates=name in ("install","build")) for name, argv in manifest.commands.items()}


def available_templates() -> List[str]:
    _ensure_registry()
    from_manifests = list(MANIFEST_REGISTRY.keys())
    return sorted(set(from_manifests) | set(TEMPLATES.keys()))


def template_commands_for(template: str) -> Dict[str, List[str]]:
    _ensure_registry()
    manifest = MANIFEST_REGISTRY.get(template)
    if manifest:
        return dict(manifest.commands)
    if template in TEMPLATES:
        return {name: list(argv) for name, (argv, _) in TEMPLATES[template].items()}
    return {}

#
