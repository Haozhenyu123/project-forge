#!/usr/bin/env python3
"""Prepare a local Claude Code marketplace for Project Forge."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import InstallResult, copy_payload, manifest_version, update_json


def install_claude(source, marketplace_root):
    marketplace_root = Path(marketplace_root)
    plugin_dir = marketplace_root / "plugins" / "project-forge"
    copy_payload(Path(source), plugin_dir)
    marketplace = marketplace_root / "marketplace.json"

    def write(data):
        data.clear()
        data.update(
            {
                "name": "project-forge-local",
                "plugins": [
                    {
                        "name": "project-forge",
                        "version": verify_claude(plugin_dir),
                        "source": "./plugins/project-forge",
                    }
                ],
            }
        )

    update_json(marketplace, write)
    return InstallResult(plugin_dir=plugin_dir, marketplace_file=marketplace)


def verify_claude(plugin_dir):
    return manifest_version(plugin_dir, ".claude-plugin/plugin.json")
