import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


version_tool = load_module("version_tool", ROOT / "scripts" / "release" / "version.py")
package_tool = load_module(
    "package_release_tool", ROOT / "scripts" / "release" / "package_release.py"
)


class VersionToolTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "package.json").write_text(
            json.dumps({"name": "fixture", "version": "1.2.3"}) + "\n",
            encoding="utf-8",
        )
        (self.root / "manifest.json").write_text(
            json.dumps({"version": "1.2.2"}) + "\n",
            encoding="utf-8",
        )
        (self.root / "runtime.py").write_text(
            'VERSION = "1.2.2"\n', encoding="utf-8"
        )
        (self.root / ".version-bump.json").write_text(
            json.dumps(
                {
                    "source": {"path": "package.json", "field": "version"},
                    "targets": [
                        {
                            "path": "manifest.json",
                            "type": "json",
                            "field": "version",
                        },
                        {
                            "path": "runtime.py",
                            "type": "regex",
                            "pattern": '^VERSION = "(?P<version>[^"]+)"$',
                        },
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_audit_reports_each_version_drift(self):
        result = version_tool.audit_versions(self.root)

        self.assertEqual(result.version, "1.2.3")
        self.assertEqual(
            [item.path for item in result.mismatches],
            ["manifest.json", "runtime.py"],
        )

    def test_sync_updates_json_and_regex_targets(self):
        changed = version_tool.sync_versions(self.root)

        manifest = json.loads((self.root / "manifest.json").read_text(encoding="utf-8"))
        runtime = (self.root / "runtime.py").read_text(encoding="utf-8")
        self.assertEqual(manifest["version"], "1.2.3")
        self.assertEqual(runtime, 'VERSION = "1.2.3"\n')
        self.assertEqual(changed, ["manifest.json", "runtime.py"])
        self.assertEqual(version_tool.audit_versions(self.root).mismatches, [])

    def test_bump_updates_source_and_targets(self):
        changed = version_tool.bump_version(self.root, "2.0.0-rc.1")

        package = json.loads((self.root / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package["version"], "2.0.0-rc.1")
        self.assertIn("package.json", changed)
        self.assertEqual(version_tool.audit_versions(self.root).mismatches, [])

    def test_rejects_non_semver_version(self):
        with self.assertRaisesRegex(ValueError, "semantic version"):
            version_tool.bump_version(self.root, "release-next")


class PackageReleaseTests(unittest.TestCase):
    def test_builds_versioned_archives_and_checksums(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "source"
            out = Path(temp) / "dist"
            (root / "skills" / "sample").mkdir(parents=True)
            (root / "skills" / "sample" / "SKILL.md").write_text(
                "# Sample\n", encoding="utf-8"
            )
            (root / "package.json").write_text(
                json.dumps(
                    {
                        "name": "project-forge",
                        "version": "1.2.3",
                        "files": ["skills"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            artifacts = package_tool.build_archives(root, out)

            self.assertEqual(
                {path.name for path in artifacts},
                {
                    "project-forge-1.2.3.zip",
                    "project-forge-1.2.3.tar.gz",
                    "SHA256SUMS",
                },
            )
            with zipfile.ZipFile(out / "project-forge-1.2.3.zip") as archive:
                names = set(archive.namelist())
            self.assertIn("project-forge-1.2.3/package.json", names)
            self.assertIn(
                "project-forge-1.2.3/skills/sample/SKILL.md",
                names,
            )
            checksums = (out / "SHA256SUMS").read_text(encoding="utf-8")
            self.assertIn("project-forge-1.2.3.zip", checksums)
            self.assertIn("project-forge-1.2.3.tar.gz", checksums)


if __name__ == "__main__":
    unittest.main()
