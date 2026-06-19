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

    def test_codex_manifest_has_required_marketplace_metadata(self):
        codex = load_json(ROOT / ".codex-plugin" / "plugin.json")
        interface = codex["interface"]

        self.assertIsInstance(codex["author"], dict)
        self.assertEqual(codex["author"]["name"], "Project Forge Contributors")
        self.assertEqual(codex["homepage"], "https://github.com/Haozhenyu123/project-forge")
        self.assertEqual(codex["repository"], "https://github.com/Haozhenyu123/project-forge")
        self.assertIn("architecture", codex["keywords"])
        self.assertIn("harness", codex["keywords"])

        for field in (
            "shortDescription",
            "longDescription",
            "developerName",
            "category",
            "capabilities",
            "defaultPrompt",
        ):
            self.assertIn(field, interface)

        self.assertEqual(interface["developerName"], "Project Forge Contributors")
        self.assertEqual(interface["category"], "Developer Tools")
        self.assertIn("Interactive", interface["capabilities"])
        self.assertIn("Read", interface["capabilities"])
        self.assertIn("Write", interface["capabilities"])
        self.assertEqual(len(interface["defaultPrompt"]), 3)

    def test_repo_has_ci_and_reproducible_install_docs(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("python -m unittest tests/test_project_forge.py", workflow)
        self.assertIn("python scripts/evals/validate_scenarios.py evals/scenarios", workflow)
        self.assertIn("python -m compileall scripts", workflow)

        for section in (
            "## Codex local install",
            "## Claude Code local install",
            "## Verify the plugin",
            "## Update",
            "## Uninstall",
        ):
            self.assertIn(section, readme)

        self.assertIn("codex-marketplace.personal.json", readme)
        self.assertIn("/plugin install", readme)
        self.assertIn("python -m unittest tests/test_project_forge.py", readme)


class SkillTests(unittest.TestCase):
    def test_required_skills_have_valid_frontmatter_and_no_placeholders(self):
        expected = {
            "forge-intake",
            "forge-project",
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
        forge_project = (ROOT / "skills" / "forge-project" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("docs/research/<project-slug>/evidence.jsonl", architect)
        self.assertIn("docs/architecture/ADR-0001-stack.md", architect)
        self.assertIn("project-forge.yaml", harness)
        self.assertIn("docs/harness.md", harness)
        self.assertIn("scripts/forge_project.py", forge_project)
        self.assertIn("--evidence", forge_project)
        self.assertIn("scripts/harness/apply_template.py", forge_project)
        self.assertIn("docs/architecture/ADR-0001-stack.md", forge_project)


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
            self.assertTrue(all("evidence_id" in row for row in rows))
            self.assertTrue(all("relevance" in row for row in rows))
            self.assertTrue(all("provisional" in row for row in rows))

    def test_validate_evidence_rejects_incomplete_non_provisional_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / "evidence.jsonl"
            evidence.write_text(
                json.dumps({"source": "web", "title": "Missing URL", "summary": "No URL"})
                + "\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [PYTHON, "scripts/research/validate_evidence.py", str(evidence)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("url", proc.stderr.lower())

    def test_validate_evidence_accepts_normalized_provisional_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw"
            raw.mkdir()
            (raw / "web.jsonl").write_text(
                json.dumps(
                    {
                        "source": "host-web-tool",
                        "kind": "manual-search-required",
                        "query": "current framework evidence",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            normalized = Path(tmp) / "evidence.jsonl"
            self.run_script(
                "scripts/research/normalize_evidence.py",
                "--input",
                str(raw),
                "--out",
                str(normalized),
            )
            proc = self.run_script("scripts/research/validate_evidence.py", str(normalized))
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["provisional_count"], 1)

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

    def test_detect_stack_respects_package_manager_and_available_scripts(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "package.json").write_text(
                json.dumps(
                    {
                        "scripts": {
                            "dev": "vite --host 0.0.0.0",
                            "test": "vitest run",
                            "lint": "eslint .",
                            "typecheck": "tsc --noEmit",
                            "build": "vite build",
                            "smoke": "playwright test tests/smoke.spec.ts",
                        },
                        "devDependencies": {"typescript": "^5.0.0"},
                    }
                ),
                encoding="utf-8",
            )
            (project / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
            proc = self.run_script("scripts/harness/detect_stack.py", "--project", str(project), "--json")
            payload = json.loads(proc.stdout)

            self.assertEqual(payload["template"], "node-ts")
            self.assertEqual(payload["package_manager"], "pnpm")
            self.assertEqual(payload["commands"]["install"], "pnpm install")
            self.assertEqual(payload["commands"]["test"], "pnpm run test")
            self.assertEqual(payload["commands"]["run"], "pnpm run dev")

    def test_apply_template_creates_harness_artifacts_without_overwriting_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.run_script(
                "scripts/harness/apply_template.py",
                "--template",
                "node-ts",
                "--project",
                str(project),
            )
            expected_files = [
                "project-forge.yaml",
                "docs/harness.md",
                ".github/workflows/project-forge-ci.yml",
            ]
            for relative in expected_files:
                self.assertTrue((project / relative).exists(), relative)

            proc = subprocess.run(
                [
                    PYTHON,
                    "scripts/harness/apply_template.py",
                    "--template",
                    "node-ts",
                    "--project",
                    str(project),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("--force", proc.stderr)

    def test_forge_project_writes_research_adr_and_harness_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            evidence = project / "raw-evidence.jsonl"
            evidence.write_text(
                json.dumps(
                    {
                        "source": "github",
                        "title": "example/project",
                        "url": "https://github.com/example/project",
                        "summary": "Reference architecture example",
                        "score": 10,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            self.run_script(
                "scripts/forge_project.py",
                "--project",
                str(project),
                "--slug",
                "team-research",
                "--goal",
                "Help small teams turn research into architecture decisions",
                "--stack",
                "node-ts",
                "--evidence",
                str(evidence),
                "--force",
            )

            research = project / "docs/research/team-research/evidence.jsonl"
            adr = project / "docs/architecture/ADR-0001-stack.md"
            contract = project / "project-forge.yaml"
            harness = project / "docs/harness.md"
            ci = project / ".github/workflows/project-forge-ci.yml"

            for path in (research, adr, contract, harness, ci):
                self.assertTrue(path.exists(), str(path))

            self.assertIn("https://github.com/example/project", research.read_text(encoding="utf-8"))
            adr_text = adr.read_text(encoding="utf-8")
            self.assertIn("team-research", adr_text)
            self.assertIn("node-ts", adr_text)
            self.assertIn("Reference architecture example", adr_text)
            self.assertIn("[E1]", adr_text)
            self.assertIn("Help small teams", contract.read_text(encoding="utf-8"))

    def test_forge_project_rejects_slug_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            evidence = project / "evidence.jsonl"
            evidence.write_text(
                json.dumps({"source": "web", "title": "Example", "url": "https://example.com"})
                + "\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    PYTHON,
                    "scripts/forge_project.py",
                    "--project",
                    str(project),
                    "--slug",
                    "../escape",
                    "--goal",
                    "Keep generated files inside the project",
                    "--stack",
                    "generic",
                    "--evidence",
                    str(evidence),
                    "--force",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("slug", proc.stderr.lower())
            self.assertFalse((project.parent / "escape").exists())

    def test_forge_project_uses_detected_node_commands_in_contract_and_ci(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "package.json").write_text(
                json.dumps(
                    {
                        "scripts": {
                            "dev": "vite --host 0.0.0.0",
                            "test": "vitest run",
                            "lint": "eslint .",
                            "typecheck": "tsc --noEmit",
                            "build": "vite build",
                            "smoke": "playwright test tests/smoke.spec.ts",
                        },
                        "devDependencies": {"typescript": "^5.0.0"},
                    }
                ),
                encoding="utf-8",
            )
            (project / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
            evidence = project / "evidence.jsonl"
            evidence.write_text(
                json.dumps({"source": "github", "title": "Example", "url": "https://github.com/example/repo"})
                + "\n",
                encoding="utf-8",
            )

            self.run_script(
                "scripts/forge_project.py",
                "--project",
                str(project),
                "--slug",
                "pnpm-project",
                "--goal",
                "Use detected package manager commands",
                "--stack",
                "node-ts",
                "--evidence",
                str(evidence),
                "--force",
            )

            contract = (project / "project-forge.yaml").read_text(encoding="utf-8")
            ci = (project / ".github/workflows/project-forge-ci.yml").read_text(encoding="utf-8")
            self.assertIn("install: pnpm install", contract)
            self.assertIn("test: pnpm run test", contract)
            self.assertIn("run: pnpm run dev", contract)
            self.assertIn("pnpm install", ci)
            self.assertIn("pnpm run smoke", ci)


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

    def test_evaluation_scenarios_use_full_rubric_schema(self):
        for path in sorted((ROOT / "evals" / "scenarios").glob("*.json")):
            data = load_json(path)
            for field in ("name", "purpose", "setup", "steps", "expected", "evidence", "rubric"):
                self.assertIn(field, data, path.name)
            self.assertIsInstance(data["steps"], list)
            self.assertIsInstance(data["rubric"], dict)
            self.assertIn("evidence", data["rubric"])

    def test_run_scenarios_scores_response_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "results.json"
            proc = subprocess.run(
                [
                    PYTHON,
                    "scripts/evals/run_scenarios.py",
                    "--scenario-dir",
                    "evals/scenarios",
                    "--responses-dir",
                    "tests/fixtures/eval_responses",
                    "--out",
                    str(out),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = load_json(out)
            self.assertEqual(payload["scenario_count"], 6)
            self.assertEqual(payload["status"], "ok")
            self.assertTrue(all("score" in result for result in payload["results"]))

    def test_smoke_docs_and_example_project_exist(self):
        smoke = (ROOT / "docs" / "smoke-test.md").read_text(encoding="utf-8")
        example = ROOT / "examples" / "team-research"
        for relative in (
            "docs/research/team-research/evidence.jsonl",
            "docs/architecture/ADR-0001-stack.md",
            "project-forge.yaml",
            "docs/harness.md",
            "docs/superpowers-handoff.md",
        ):
            self.assertTrue((example / relative).exists(), relative)
        self.assertIn("python scripts/smoke_test.py", smoke)

    def test_smoke_test_script_validates_example_project(self):
        proc = subprocess.run(
            [PYTHON, "scripts/smoke_test.py", "--project", "examples/team-research", "--slug", "team-research"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "ok")

    def test_export_handoff_writes_superpowers_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "docs/research/team-research").mkdir(parents=True)
            (project / "docs/architecture").mkdir(parents=True)
            (project / "docs").mkdir(exist_ok=True)
            (project / "docs/research/team-research/evidence.jsonl").write_text(
                json.dumps(
                    {
                        "evidence_id": "E1",
                        "source": "github",
                        "title": "Example",
                        "url": "https://github.com/example/repo",
                        "summary": "Reference implementation",
                        "observed_at": "2026-06-19T00:00:00Z",
                        "relevance": "Shows project structure",
                        "provisional": False,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (project / "docs/architecture/ADR-0001-stack.md").write_text("# ADR\nUse node-ts.\n", encoding="utf-8")
            (project / "project-forge.yaml").write_text("project:\n  slug: team-research\ncommands:\n  test: npm run test\n", encoding="utf-8")
            (project / "docs/harness.md").write_text("# Harness\nRun npm run test.\n", encoding="utf-8")
            out = project / "docs/superpowers-handoff.md"
            proc = subprocess.run(
                [
                    PYTHON,
                    "scripts/export_handoff.py",
                    "--project",
                    str(project),
                    "--slug",
                    "team-research",
                    "--out",
                    str(out),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            text = out.read_text(encoding="utf-8")
            self.assertIn("Superpowers Handoff", text)
            self.assertIn("ADR-0001-stack.md", text)
            self.assertIn("npm run test", text)


if __name__ == "__main__":
    unittest.main()
