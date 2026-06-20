#!/usr/bin/env python3
"""Claude Code plugin lifecycle compatibility API."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from project_forge.hosts import HostService, manifest_version


def service(source, marketplace_root):
    return HostService.claude(source, marketplace_root)


def install_claude(source, marketplace_root, cachebuster=None, dry_run=False):
    return service(source, marketplace_root).install(cachebuster, dry_run)


def update_claude(source, marketplace_root, cachebuster=None, dry_run=False):
    return service(source, marketplace_root).update(cachebuster, dry_run)


def verify_claude(plugin_dir):
    """Return the installed manifest version, preserving the v0.2 interface."""
    return manifest_version(plugin_dir, ".claude-plugin/plugin.json")


def verify_claude_install(source, marketplace_root):
    return service(source, marketplace_root).verify()


def uninstall_claude(source, marketplace_root, dry_run=False):
    return service(source, marketplace_root).uninstall(dry_run)


def restore_claude(source, marketplace_root, backup_dir, dry_run=False):
    return service(source, marketplace_root).restore(backup_dir, dry_run)
