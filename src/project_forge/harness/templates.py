"""Structured command templates for supported harnesses."""

from copy import deepcopy

from project_forge.models import CommandSpec


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


def commands_for(template, root="."):
    if template not in TEMPLATES:
        raise ValueError(f"unknown harness template: {template}")
    return {
        name: CommandSpec(argv=deepcopy(argv), cwd=root, mutates=mutates)
        for name, (argv, mutates) in TEMPLATES[template].items()
    }
