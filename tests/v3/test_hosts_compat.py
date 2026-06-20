import json
import sys
import tempfile
import textwrap
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from project_forge.evals import EvalStatus, load_matrix, run_compatibility
from project_forge.hosts import HostService, build_host_bundles


def make_source(root):
    source = root / "source"
    for manifest in (".codex-plugin", ".claude-plugin"):
        (source / manifest).mkdir(parents=True)
        (source / manifest / "plugin.json").write_text(
            json.dumps({"name": "project-forge", "version": "0.3.0"}) + "\n",
            encoding="utf-8",
        )
    (source / "skills" / "forge-intake").mkdir(parents=True)
    (source / "skills" / "forge-intake" / "SKILL.md").write_text("# Forge\n", encoding="utf-8")
    (source / "src" / "project_forge").mkdir(parents=True)
    (source / "src" / "project_forge" / "__init__.py").write_text("", encoding="utf-8")
    (source / "package.json").write_text(
        json.dumps(
            {
                "name": "project-forge",
                "version": "0.3.0",
                "files": [".codex-plugin", ".claude-plugin", "skills"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return source


def make_matrix(root):
    path = root / "matrix.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "versions": [
                    {
                        "superpowers": "5.1.3",
                        "hosts": ["codex", "claude"],
                        "status": "contract-tested",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def make_project(root):
    project = root / "project"
    (project / "docs").mkdir(parents=True)
    handoff = {
        "schema_version": 2,
        "kind": "project-forge.superpowers-handoff",
        "artifacts": {
            "adr": "docs/architecture/ADR-0001-stack.md",
            "contract": "project-forge.yaml",
        },
        "superpowers": {"first_task": "Build the smallest accepted workflow."},
    }
    (project / "docs" / "superpowers-handoff.json").write_text(
        json.dumps(handoff), encoding="utf-8"
    )
    (project / "project-forge.yaml").write_text("schema_version: 2\n", encoding="utf-8")
    return project


def make_superpowers(root):
    source = root / "superpowers"
    (source / "skills" / "writing-plans").mkdir(parents=True)
    (source / "skills" / "writing-plans" / "SKILL.md").write_text(
        "# Writing Plans\n", encoding="utf-8"
    )
    return source


def fake_cli(root, mutate=False):
    path = root / ("fake-mutate.py" if mutate else "fake-plan.py")
    mutation = "Path('implemented.txt').write_text('bad', encoding='utf-8')" if mutate else ""
    path.write_text(
        textwrap.dedent(
            f"""
            import json
            import sys
            from pathlib import Path
            if "--version" in sys.argv:
                print("fake 1.0")
                raise SystemExit(0)
            {mutation}
            result = "\\n".join([
                "Architecture basis: docs/architecture/ADR-0001-stack.md",
                "Harness basis: project-forge.yaml",
                "First task: Build the smallest accepted workflow.",
                "Implementation status: not started",
                "1. Prepare the implementation plan.",
            ])
            print(json.dumps({{"result": result}}))
            """
        ),
        encoding="utf-8",
    )
    return [sys.executable, str(path)]


class HostLifecycleTests(unittest.TestCase):
    def test_dry_run_does_not_create_host_files(self):
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            service = HostService.codex(make_source(root), root / "codex", root / "agents")
            result = service.install(cachebuster="test", dry_run=True)
            self.assertEqual(result.status, "planned")
            self.assertTrue(result.dry_run)
            self.assertFalse(result.plugin_dir.exists())
            self.assertFalse(result.marketplace_file.exists())

    def test_codex_update_backs_up_and_cachebuster_never_changes_source(self):
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            source = make_source(root)
            service = HostService.codex(
                source,
                root / "codex",
                root / "agents",
                clock=lambda: datetime(2026, 1, 2, tzinfo=timezone.utc),
            )
            self.assertEqual(service.install().status, "installed")
            result = service.update(cachebuster="local-2")
            self.assertEqual(result.status, "updated")
            self.assertTrue(result.backup_dir.is_dir())
            self.assertEqual(service.verify().status, "verified")
            installed = json.loads((service.plugin_dir / service.manifest).read_text(encoding="utf-8"))
            original = json.loads((source / service.manifest).read_text(encoding="utf-8"))
            self.assertEqual(installed["version"], "0.3.0+codex.local-2")
            self.assertEqual(original["version"], "0.3.0")

    def test_uninstall_backup_can_be_restored(self):
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            service = HostService.claude(make_source(root), root / "marketplace")
            service.install(cachebuster="one")
            removed = service.uninstall()
            self.assertEqual(removed.status, "uninstalled")
            self.assertFalse(service.plugin_dir.exists())
            restored = service.restore(removed.backup_dir)
            self.assertEqual(restored.status, "restored")
            self.assertEqual(service.verify().status, "verified")

    def test_update_requires_an_existing_install(self):
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            service = HostService.claude(make_source(root), root / "marketplace")
            result = service.update()
            self.assertEqual(result.status, "not_installed")
            self.assertFalse(result.ok)

    def test_unsafe_cachebuster_is_rejected_without_writes(self):
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            service = HostService.codex(make_source(root), root / "codex", root / "agents")
            result = service.install(cachebuster="bad value; exit")
            self.assertEqual(result.status, "failed")
            self.assertFalse(service.plugin_dir.exists())

    def test_host_bundles_contain_only_their_manifest(self):
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            source = make_source(root)
            artifacts = build_host_bundles(source, root / "dist")
            codex = next(path for path in artifacts if path.name.endswith("codex-0.3.0.zip"))
            claude = next(path for path in artifacts if path.name.endswith("claude-0.3.0.zip"))
            with zipfile.ZipFile(codex) as archive:
                codex_names = "\n".join(archive.namelist())
            with zipfile.ZipFile(claude) as archive:
                claude_names = "\n".join(archive.namelist())
            self.assertIn(".codex-plugin/plugin.json", codex_names)
            self.assertNotIn(".claude-plugin/plugin.json", codex_names)
            self.assertIn(".claude-plugin/plugin.json", claude_names)
            self.assertNotIn(".codex-plugin/plugin.json", claude_names)


class SuperpowersCompatibilityTests(unittest.TestCase):
    def run_case(self, root, command, env=None):
        return run_compatibility(
            host="codex",
            project=make_project(root),
            plugin_root=make_source(root),
            superpowers_dir=make_superpowers(root),
            superpowers_version="5.1.3",
            matrix_path=make_matrix(root),
            log_root=root / "logs",
            command_override=command,
            env=env or {"OPENAI_API_KEY": "fixture"},
        )

    def test_missing_credentials_is_not_run(self):
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            result = run_compatibility(
                "codex",
                make_project(root),
                make_source(root),
                make_superpowers(root),
                "5.1.3",
                make_matrix(root),
                root / "logs",
                command_override=["missing-cli"],
                env={},
            )
            self.assertEqual(result.status, EvalStatus.NOT_RUN)
            self.assertIn("credentials", result.reason)

    def test_missing_cli_is_not_run(self):
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            result = self.run_case(root, ["definitely-missing-project-forge-cli"])
            self.assertEqual(result.status, EvalStatus.NOT_RUN)
            self.assertIn("CLI unavailable", result.reason)

    def test_compliant_plan_passes_without_touching_project(self):
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            result = self.run_case(root, fake_cli(root))
            self.assertEqual(result.status, EvalStatus.PASS, result.to_dict())
            self.assertTrue(result.assertions["project_unchanged"])
            self.assertTrue(Path(result.log_dir, "prompt.txt").is_file())

    def test_file_mutation_fails_plan_only_contract(self):
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            result = self.run_case(root, fake_cli(root, mutate=True))
            self.assertEqual(result.status, EvalStatus.FAIL)
            self.assertFalse(result.assertions["project_unchanged"])

    def test_repository_matrix_is_well_formed(self):
        matrix = load_matrix(ROOT / "compatibility" / "superpowers-matrix.json")
        self.assertEqual(matrix["schema_version"], 1)
        self.assertEqual(matrix["versions"][0]["mode"], "plan-only")


if __name__ == "__main__":
    unittest.main()
