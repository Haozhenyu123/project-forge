#!/usr/bin/env python3
"""Compatibility exports for the host lifecycle package."""

import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from project_forge.hosts import copy_payload, manifest_version, package_entries, update_json


@dataclass
class InstallResult:
    """Legacy result shape retained for callers importing this script."""

    plugin_dir: Path
    marketplace_file: Path = None


def package_files(source):
    return package_entries(source)


def should_skip(path):
    return any(part in {"__pycache__", ".git", ".pytest_cache", "dist"} for part in path.parts)


__all__ = [
    "InstallResult",
    "copy_payload",
    "manifest_version",
    "package_files",
    "should_skip",
    "update_json",
]
