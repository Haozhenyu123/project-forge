#!/usr/bin/env python3
"""Install Project Forge into a local Codex plugin directory."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import InstallResult, copy_payload, manifest_version, update_json


def install_codex(source, codex_home, agents_home, cachebuster=None):
    source = Path(source)
    plugin_dir = Path(codex_home) / "plugins" / "project-forge"
    copy_payload(source, plugin_dir)
    if cachebuster:
        manifest_path = plugin_dir / ".codex-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["version"] = f"{manifest['version']}+codex.{cachebuster}"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    marketplace = Path(agents_home) / "plugins" / "marketplace.json"

    def merge(data):
        data.setdefault("name", "personal")
        data.setdefault("interface", {"displayName": "Personal Plugins"})
        plugins = data.setdefault("plugins", [])
        plugins[:] = [plugin for plugin in plugins if plugin.get("name") != "project-forge"]
        plugins.append(
            {
                "name": "project-forge",
                "path": str(plugin_dir),
                "version": verify_codex(plugin_dir),
            }
        )

    update_json(marketplace, merge)
    return InstallResult(plugin_dir=plugin_dir, marketplace_file=marketplace)


def verify_codex(plugin_dir):
    return manifest_version(plugin_dir, ".codex-plugin/plugin.json")
