#!/usr/bin/env python3
"""Shared local install helpers."""

import json
import shutil
from dataclasses import dataclass
from pathlib import Path


EXCLUDE_DIRS = {"__pycache__", ".git", ".pytest_cache", "dist"}


@dataclass
class InstallResult:
    plugin_dir: Path
    marketplace_file: Path = None


def package_files(source):
    package = json.loads((source / "package.json").read_text(encoding="utf-8"))
    files = package.get("files") or [
        ".codex-plugin",
        ".claude-plugin",
        "skills",
        "scripts",
        "templates",
        "docs",
        "install",
        "LICENSE",
        "README.md",
    ]
    return ["package.json", *[item for item in files if item != "package.json"]]


def should_skip(path):
    return any(part in EXCLUDE_DIRS for part in path.parts)


def copy_payload(source, target):
    source = Path(source)
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    for relative in package_files(source):
        src = source / relative
        dst = target / relative
        if not src.exists():
            continue
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            ignore = shutil.ignore_patterns(*EXCLUDE_DIRS)
            shutil.copytree(src, dst, ignore=ignore)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    for cache in target.rglob("__pycache__"):
        if cache.is_dir():
            shutil.rmtree(cache)


def manifest_version(plugin_dir, manifest):
    path = Path(plugin_dir) / manifest
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["version"]


def update_json(path, updater):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
    updater(data)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return data
