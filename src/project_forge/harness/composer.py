"""Compose one or more harness templates into a Schema v2 contract."""

import re
import shlex
from pathlib import Path, PurePosixPath

from project_forge.models import ProjectContract, ProjectMeta, StackContract

from .templates import TEMPLATES, commands_for


STACK_SPEC = re.compile(r"^(?P<template>[a-z0-9-]+)(?::(?P<root>.+))?$")


def normalize_root(value):
    root = str(PurePosixPath(str(value or ".").replace("\\", "/")))
    if root.startswith("/") or ".." in root.split("/"):
        raise ValueError(f"stack root must be project-relative: {value}")
    return root


def parse_stack_spec(value):
    match = STACK_SPEC.fullmatch(str(value).strip())
    if not match:
        raise ValueError(f"invalid stack spec: {value}; expected TEMPLATE[:PATH]")
    template = match.group("template")
    if template not in TEMPLATES:
        raise ValueError(f"unknown harness template: {template}")
    return template, normalize_root(match.group("root") or ".")


def stack_id(template, root, used):
    base = template if root == "." else re.sub(r"[^a-z0-9]+", "-", root.lower()).strip("-")
    candidate = base or template
    suffix = 2
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def compose_contract(slug, goal, primary, secondary=(), services=(), project_root=None):
    primary_template, primary_root = parse_stack_spec(primary)
    specs = [(primary_template, primary_root), *[parse_stack_spec(item) for item in secondary]]
    used = set()
    stacks = []
    for template, root in specs:
        if project_root and root != ".":
            candidate = Path(project_root) / root
            if not candidate.is_dir():
                raise ValueError(f"stack root does not exist: {root}")
        identifier = stack_id(template, root, used)
        used.add(identifier)
        stacks.append(
            StackContract(
                id=identifier,
                template=template,
                root=root,
                commands=commands_for(template, root),
            )
        )
    contract = ProjectContract(
        project=ProjectMeta(slug=slug, goal=goal),
        primary=stacks[0],
        secondary=stacks[1:],
        services=list(services),
    )
    contract.validate()
    return contract


def command_specs_from_strings(commands, root="."):
    structured = {}
    for name, value in commands.items():
        text = str(value)
        if any(token in text for token in ("&&", "||", "|", ">", "<")) or text.strip().lower().startswith("echo "):
            from project_forge.models import CommandSpec
            structured[name] = CommandSpec(legacy_shell=text, cwd=root, mutates=name in {"install", "build", "run"})
        else:
            from project_forge.models import CommandSpec
            structured[name] = CommandSpec(argv=shlex.split(text), cwd=root, mutates=name in {"install", "build", "run"})
    return structured
