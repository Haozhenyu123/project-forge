import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


common = load_module("install_common", ROOT / "scripts" / "install" / "common.py")
codex = load_module("install_codex", ROOT / "scripts" / "install" / "codex.py")
claude = load_module("install_claude", ROOT / "scripts" / "install" / "claude.py")


class InstallToolTests(unittest.TestCase):
    def make_source(self, parent):
        source = parent / "source"
        (source / ".codex-plugin").mkdir(parents=True)
        (source / ".claude-plugin").mkdir()
        (source / "skills" / "sample").mkdir(parents=True)
        (source / "scripts" / "nested" / "__pycache__").mkdir(parents=True)
        package = {
            "name": "project-forge",
            "version": "1.2.3",
            "files": [
                ".codex-plugin",
                ".claude-plugin",
                "skills",
                "scripts",
            ],
        }
        (source / "package.json").write_text(
            json.dumps(package) + "\n", encoding="utf-8"
        )
        manifest = {
            "name": "project-forge",
            "version": "1.2.3",
            "description": "Fixture plugin",
        }
        (source / ".codex-plugin" / "plugin.json").write_text(
            json.dumps(manifest) + "\n", encoding="utf-8"
        )
        (source / ".claude-plugin" / "plugin.json").write_text(
            json.dumps(manifest) + "\n", encoding="utf-8"
        )
        (source / "skills" / "sample" / "SKILL.md").write_text(
            "# Sample\n", encoding="utf-8"
        )
        (source / "scripts" / "tool.py").write_text(
            "print('ok')\n", encoding="utf-8"
        )
        (source / "scripts" / "nested" / "__pycache__" / "tool.pyc").write_bytes(
            b"cache"
        )
        return source

    def test_copy_payload_is_repeatable_and_excludes_cache_files(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            source = self.make_source(parent)
            target = parent / "target"

            common.copy_payload(source, target)
            common.copy_payload(source, target)

            self.assertTrue((target / "skills" / "sample" / "SKILL.md").is_file())
            self.assertTrue((target / "package.json").is_file())
            self.assertFalse((target / "scripts" / "nested" / "__pycache__").exists())

    def test_codex_install_merges_personal_marketplace(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            source = self.make_source(parent)
            codex_home = parent / "codex"
            agents_home = parent / "agents"
            marketplace = agents_home / "plugins" / "marketplace.json"
            marketplace.parent.mkdir(parents=True)
            marketplace.write_text(
                json.dumps(
                    {
                        "name": "personal",
                        "interface": {"displayName": "My Plugins"},
                        "plugins": [{"name": "existing"}],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = codex.install_codex(source, codex_home, agents_home)

            data = json.loads(marketplace.read_text(encoding="utf-8"))
            self.assertEqual(data["interface"]["displayName"], "My Plugins")
            self.assertEqual(
                [plugin["name"] for plugin in data["plugins"]],
                ["existing", "project-forge"],
            )
            self.assertEqual(result.plugin_dir, codex_home / "plugins" / "project-forge")
            self.assertEqual(codex.verify_codex(result.plugin_dir), "1.2.3")

    def test_codex_sync_uses_cachebuster_only_in_installed_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            source = self.make_source(parent)

            result = codex.install_codex(
                source,
                parent / "codex",
                parent / "agents",
                cachebuster="local-test",
            )

            installed = json.loads(
                (result.plugin_dir / ".codex-plugin" / "plugin.json").read_text(
                    encoding="utf-8"
                )
            )
            original = json.loads(
                (source / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
            )
            self.assertEqual(installed["version"], "1.2.3+codex.local-test")
            self.assertEqual(original["version"], "1.2.3")

    def test_claude_install_generates_local_marketplace(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            source = self.make_source(parent)
            marketplace_root = parent / "claude-marketplace"

            result = claude.install_claude(source, marketplace_root)

            data = json.loads(result.marketplace_file.read_text(encoding="utf-8"))
            self.assertEqual(data["name"], "project-forge-local")
            self.assertEqual(data["plugins"][0]["version"], "1.2.3")
            self.assertEqual(data["plugins"][0]["source"], "./plugins/project-forge")
            self.assertEqual(claude.verify_claude(result.plugin_dir), "1.2.3")


if __name__ == "__main__":
    unittest.main()
