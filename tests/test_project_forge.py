import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} is missing YAML frontmatter"
    _, raw, body = text.split("---", 2)
    frontmatter = {}
    for line in raw.strip().splitlines():
        if not line.strip():
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"')
    return frontmatter, body


class ManifestTests(unittest.TestCase):
    def test_codex_and_claude_manifests_are_installable_plugin_manifests(self):
        codex = load_json(ROOT / ".codex-plugin" / "plugin.json")
        claude = load_json(ROOT / ".claude-plugin" / "plugin.json")

        for manifest in (codex, claude):
            self.assertEqual(manifest["name"], "project-forge")
            self.assertEqual(manifest["version"], "0.1.0")
            self.assertEqual(manifest["license"], "MIT")
            self.assertEqual(manifest["skills"], "./skills/")
            self.assertIn("architect", manifest["description"].lower())
            self.assertIn("harness", manifest["description"].lower())

        self.assertEqual(claude["displayName"], "Project Forge")
        self.assertEqual(codex["interface"]["displayName"], "Project Forge")


class SkillTests(unittest.TestCase):
    def test_required_skills_have_valid_frontmatter_and_no_placeholders(self):
        expected = {
            "forge-intake",
            "creative-director",
            "ai-architect",
            "harness-engineer",
            "agent-evaluator",
        }
        found = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}
        self.assertEqual(found, expected)

        for skill_name in expected:
            path = ROOT / "skills" / skill_name / "SKILL.md"
            frontmatter, body = read_frontmatter(path)
            self.assertEqual(frontmatter["name"], skill_name)
            self.assertTrue(frontmatter["description"].startswith("Use when"))
            self.assertLess(len(frontmatter["description"]), 500)
            lowered = body.lower()
            self.assertNotIn("todo", lowered)
            self.assertNotIn("tbd", lowered)
            self.assertNotIn("[placeholder", lowered)
            self.assertLess(len(body.split()), 1200)

    def test_architect_and_harness_skills_name_their_output_contracts(self):
        architect = (ROOT / "skills" / "ai-architect" / "SKILL.md").read_text(encoding="utf-8")
        harness = (ROOT / "skills" / "harness-engineer" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("docs/research/<project-slug>/evidence.jsonl", architect)
        self.assertIn("docs/architecture/ADR-0001-stack.md", architect)
        self.assertIn("project-forge.yaml", harness)
        self.assertIn("docs/harness.md", harness)


class ScriptTests(unittest.TestCase):
    def run_script(self, *args, env=None):
        proc = subprocess.run(
            [PYTHON, *args],
            cwd=ROOT,
            env={**os.environ, **(env or {})},
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc

    def test_github_search_accepts_fixture_and_writes_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "github.jsonl"
            self.run_script(
                "scripts/research/github_search.py",
                "--query",
                "python web framework",
                "--limit",
                "2",
                "--out",
                str(out),
                "--fixture",
                "tests/fixtures/github_search_response.json",
            )
            rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["source"], "github")
            self.assertIn("stars", rows[0])
            self.assertTrue(rows[0]["url"].startswith("https://github.com/"))

    def test_web_search_without_provider_writes_host_tool_instruction(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "web.jsonl"
            self.run_script(
                "scripts/research/web_search.py",
                "--query",
                "best javascript framework 2026",
                "--limit",
                "3",
                "--out",
                str(out),
                env={"PROJECT_FORGE_WEB_SEARCH_URL": ""},
            )
            rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[0]["source"], "host-web-tool")
            self.assertEqual(rows[0]["kind"], "manual-search-required")
            self.assertIn("best javascript framework 2026", rows[0]["query"])

    def test_normalize_evidence_merges_json_and_jsonl_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            evidence_dir = tmp_path / "evidence"
            evidence_dir.mkdir()
            (evidence_dir / "github.jsonl").write_text(
                json.dumps(
                    {
                        "source": "github",
                        "title": "Example Repo",
                        "url": "https://github.com/example/repo",
                        "summary": "A useful repository",
                        "stars": 42,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (evidence_dir / "web.json").write_text(
                json.dumps(
                    [
                        {
                            "source": "web",
                            "title": "Framework Guide",
                            "url": "https://example.com/framework",
                            "summary": "A useful article",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            out = tmp_path / "normalized.jsonl"
            self.run_script(
                "scripts/research/normalize_evidence.py",
                "--input",
                str(evidence_dir),
                "--out",
                str(out),
            )
            rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["source"] for row in rows], ["github", "web"])
            self.assertTrue(all("observed_at" in row for row in rows))
            self.assertTrue(all("score" in row for row in rows))

    def test_detect_stack_identifies_node_python_and_generic_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            node = root / "node"
            python = root / "python"
            generic = root / "generic"
            node.mkdir()
            python.mkdir()
            generic.mkdir()
            (node / "package.json").write_text('{"scripts": {"test": "vitest"}}', encoding="utf-8")
            (python / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")

            for project, expected in ((node, "node-ts"), (python, "python"), (generic, "generic")):
                proc = self.run_script("scripts/harness/detect_stack.py", "--project", str(project), "--json")
                payload = json.loads(proc.stdout)
                self.assertEqual(payload["template"], expected)
                self.assertIn("commands", payload)


class TemplateAndEvalTests(unittest.TestCase):
    def test_harness_templates_define_command_contracts_and_ci(self):
        for template in ("node-ts", "python", "generic"):
            base = ROOT / "templates" / "harness" / template
            contract = (base / "project-forge.yaml").read_text(encoding="utf-8")
            docs = (base / "docs" / "harness.md").read_text(encoding="utf-8")
            ci = (base / ".github" / "workflows" / "project-forge-ci.yml").read_text(encoding="utf-8")
            for command in ("install", "test", "lint", "typecheck", "build", "run", "smoke"):
                self.assertIn(f"{command}:", contract)
            self.assertIn("How to verify", docs)
            self.assertIn("Project Forge CI", ci)

    def test_evaluation_scenarios_are_schema_valid(self):
        proc = subprocess.run(
            [PYTHON, "scripts/evals/validate_scenarios.py", "evals/scenarios"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["scenario_count"], 6)
        self.assertEqual(payload["status"], "ok")


if __name__ == "__main__":
    unittest.main()
