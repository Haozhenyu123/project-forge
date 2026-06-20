#!/usr/bin/env python3
"""Codex plugin lifecycle compatibility API."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from project_forge.hosts import HostService, manifest_version


def service(source, codex_home, agents_home):
    return HostService.codex(source, codex_home, agents_home)


def install_codex(source, codex_home, agents_home, cachebuster=None, dry_run=False):
    return service(source, codex_home, agents_home).install(cachebuster, dry_run)


def update_codex(source, codex_home, agents_home, cachebuster=None, dry_run=False):
    return service(source, codex_home, agents_home).update(cachebuster, dry_run)


def verify_codex(plugin_dir):
    """Return the installed manifest version, preserving the v0.2 interface."""
    return manifest_version(plugin_dir, ".codex-plugin/plugin.json")


def verify_codex_install(source, codex_home, agents_home):
    return service(source, codex_home, agents_home).verify()


def uninstall_codex(source, codex_home, agents_home, dry_run=False):
    return service(source, codex_home, agents_home).uninstall(dry_run)


def restore_codex(source, codex_home, agents_home, backup_dir, dry_run=False):
    return service(source, codex_home, agents_home).restore(backup_dir, dry_run)
