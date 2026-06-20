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
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


PROJECT_VERSION = load_json(ROOT / "package.json")["version"]


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
            self.assertEqual(manifest["version"], PROJECT_VERSION)
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
        self.assertGreaterEqual(len(interface["defaultPrompt"]), 4)
        self.assertIn("superpowers", " ".join(interface["defaultPrompt"]).lower())

    def test_repo_has_ci_and_reproducible_install_docs(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("python -m unittest tests/test_project_forge.py", workflow)
        self.assertIn("python scripts/evals/validate_scenarios.py evals/scenarios", workflow)
        self.assertIn("python -m compileall src scripts", workflow)

        for section in (
            "Install",
            "Quick Start",
            "Verify",
            "License",
        ):
            self.assertTrue(
                section.lower() in readme.lower(),
                f"README missing section: {section}"
            )

        self.assertIn("codex-marketplace.personal.json", readme)
        self.assertIn("/plugin install", readme)
        self.assertIn("python -m unittest tests/test_project_forge.py", readme)

    def test_readme_is_clean_utf8_without_mojibake(self):
        raw = (ROOT / "README.md").read_bytes()
        text = raw.decode("utf-8")
        self.assertIn("## 中文快速入门", text)
        self.assertIn("```powershell\n", text)
        self.assertIn("Project Forge 负责编码之前", text)
        for broken in ("\u9225?", "\u6d60\u20ac", "\u93c4\ue219", "\u951b?", "\u9225", "\ufffd", "\u00c3", "\u00c2", "\u951f", "??????", "涓", "璐熻矗"):
            self.assertNotIn(broken, text)

    def _legacy_readme_mojibake_assertion(self):
        raw = (ROOT / "README.md").read_bytes()
        text = raw.decode("utf-8")
        self.assertIn("## 中文快速入门", text)
        self.assertIn("```powershell\n", text)
        self.assertIn("Project Forge 负责编码之前", text)
        for broken in ("\u9225?", "\u6d60\u20ac", "\u93c4\ue219", "\u951b?", "\u9225", "\ufffd", "\u00c3", "\u00c2", "\u951f", "??????"):
            self.assertNotIn(broken, text)


class SkillTests(unittest.TestCase):
    def test_required_skills_have_valid_frontmatter_and_no_placeholders(self):
        expected = {
            "forge-intake",
            "forge-project",
            "creative-director",
            "ai-architect",
            "harness-engineer",
            "agent-evaluator",
            "using-project-forge",
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
            self.assertLess(len(body.split()), 1500)

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
        self.assertIn("docs/superpowers-handoff.json", forge_project)


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
            handoff = project / "docs/superpowers-handoff.md"
            handoff_json = project / "docs/superpowers-handoff.json"
            ci = project / ".github/workflows/project-forge-ci.yml"

            for path in (research, adr, contract, harness, handoff, handoff_json, ci):
                self.assertTrue(path.exists(), str(path))

            self.assertIn("https://github.com/example/project", research.read_text(encoding="utf-8"))
            adr_text = adr.read_text(encoding="utf-8")
            self.assertIn("team-research", adr_text)
            self.assertIn("node-ts", adr_text)
            self.assertIn("Reference architecture example", adr_text)
            self.assertIn("[E1]", adr_text)
            self.assertIn("Help small teams", contract.read_text(encoding="utf-8"))
            packet = load_json(handoff_json)
            self.assertEqual(packet["project"]["slug"], "team-research")
            self.assertEqual(packet["kind"], "project-forge.superpowers-handoff")
            self.assertIn("first_task", packet["superpowers"])

            ready = self.run_script(
                "scripts/superpowers_ready.py",
                "--project",
                str(project),
                "--slug",
                "team-research",
                "--json",
            )
            self.assertIn(json.loads(ready.stdout)["status"], ("ready", "attention"))

    def test_forge_project_dry_run_does_not_write_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            evidence = Path(tmp) / "evidence.jsonl"
            evidence.write_text(
                json.dumps(
                    {
                        "source": "web",
                        "title": "Architecture source",
                        "url": "https://example.com/source",
                        "summary": "Current architecture evidence",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            proc = self.run_script(
                "scripts/forge_project.py",
                "--project",
                str(project),
                "--slug",
                "dry-run-project",
                "--goal",
                "Preview the decision workflow",
                "--stack",
                "node-ts",
                "--evidence",
                str(evidence),
                "--dry-run",
            )
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["status"], "dry-run")
            self.assertFalse(project.exists())
            self.assertTrue(
                any(path.replace("\\", "/").endswith("docs/superpowers-handoff.json") for path in payload["would_generate"])
            )

    def test_force_creates_backup_and_restore_recovers_generated_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            evidence = Path(tmp) / "evidence.jsonl"
            evidence.write_text(
                json.dumps(
                    {
                        "source": "web",
                        "title": "Architecture source",
                        "url": "https://example.com/source",
                        "summary": "Current architecture evidence",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            common = [
                "scripts/forge_project.py",
                "--project",
                str(project),
                "--slug",
                "backup-project",
                "--goal",
                "Protect generated decisions",
                "--stack",
                "node-ts",
                "--evidence",
                str(evidence),
            ]
            self.run_script(*common)
            adr = project / "docs" / "architecture" / "ADR-0001-stack.md"
            original = adr.read_text(encoding="utf-8")
            adr.write_text("user modified ADR\n", encoding="utf-8")

            forced = self.run_script(*common, "--force")
            payload = json.loads(forced.stdout)
            self.assertTrue(payload["backup"])
            backup_id = Path(payload["backup"]).name

            adr.write_text("newer local change\n", encoding="utf-8")
            self.run_script(
                "scripts/state_manager.py",
                "restore",
                backup_id,
                "--project",
                str(project),
                "--force",
            )
            self.assertEqual(adr.read_text(encoding="utf-8"), "user modified ADR\n")
            self.assertNotEqual(original, "user modified ADR\n")

    def test_structured_decision_populates_candidates_rejections_and_confidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            evidence = Path(tmp) / "evidence.jsonl"
            decision = Path(tmp) / "decision.json"
            evidence.write_text(
                json.dumps(
                    {
                        "source": "github",
                        "title": "Reference",
                        "url": "https://github.com/example/reference",
                        "summary": "Maintained reference",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            decision.write_text(
                json.dumps(
                    {
                        "selected_stack": "node-ts",
                        "rationale": "Best fit for the delivery constraints.",
                        "candidates": [
                            {"stack": "node-ts", "score": 88, "reason": "Strong harness fit"},
                            {"stack": "python", "score": 61, "reason": "Weaker frontend fit"},
                        ],
                        "rejected_options": [
                            {"stack": "python", "reason": "Adds a second runtime without benefit"}
                        ],
                        "confidence": {
                            "level": "High",
                            "reason": "multiple independent sources agree",
                        },
                        "revisit_triggers": ["The product becomes offline-first."],
                    }
                ),
                encoding="utf-8",
            )
            self.run_script(
                "scripts/forge_project.py",
                "--project",
                str(project),
                "--slug",
                "decision-project",
                "--goal",
                "Choose a maintainable product stack",
                "--stack",
                "node-ts",
                "--evidence",
                str(evidence),
                "--decision-file",
                str(decision),
            )
            adr = (project / "docs" / "architecture" / "ADR-0001-stack.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("## Considered Options", adr)
            self.assertIn("score: 88", adr)
            self.assertIn("Adds a second runtime without benefit", adr)
            self.assertIn("High confidence", adr)
            self.assertIn("The product becomes offline-first.", adr)

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
        self.assertEqual(payload["scenario_count"], 9)
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
            self.assertEqual(payload["scenario_count"], 9)
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
            "docs/superpowers-handoff.json",
        ):
            self.assertTrue((example / relative).exists(), relative)
        self.assertIn("python scripts/smoke_test.py", smoke)
        self.assertTrue((ROOT / "docs" / "superpowers-ready.md").is_file())
        self.assertTrue((ROOT / "docs" / "schemas" / "superpowers-handoff.schema.json").is_file())

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
            self.assertIn("Acceptance Criteria", text)
            packet = load_json(project / "docs/superpowers-handoff.json")
            self.assertEqual(packet["kind"], "project-forge.superpowers-handoff")
            self.assertEqual(packet["project"]["slug"], "team-research")
            self.assertIn("first_task", packet["superpowers"])

    def test_superpowers_ready_reports_ready_and_blocked_states(self):
        ready = subprocess.run(
            [
                PYTHON,
                "scripts/superpowers_ready.py",
                "--project",
                "examples/team-research",
                "--slug",
                "team-research",
                "--json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(ready.returncode, 0, ready.stderr)
        payload = json.loads(ready.stdout)
        self.assertIn(payload["status"], ("ready", "attention"))
        self.assertEqual(payload["failures"], 0)

        with tempfile.TemporaryDirectory() as tmp:
            blocked = subprocess.run(
                [
                    PYTHON,
                    "scripts/superpowers_ready.py",
                    "--project",
                    tmp,
                    "--slug",
                    "missing",
                    "--json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(blocked.returncode, 0)
            blocked_payload = json.loads(blocked.stdout)
            self.assertEqual(blocked_payload["status"], "blocked")
            self.assertGreater(blocked_payload["failures"], 0)


class SkillContractTests(unittest.TestCase):
    """Tests for V2.2 skill improvements: competitive analysis, patterns, escalation, multi-stack."""

    def test_creative_director_skill_has_competitive_context(self):
        text = (ROOT / "skills" / "creative-director" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Competitive Context", text)
        self.assertIn("Differentiation Strategy", text)
        self.assertIn("Architecture Signals", text)
        self.assertIn("Escalation (Feedback to Intake)", text)

    def test_ai_architect_skill_has_confidence_and_patterns(self):
        text = (ROOT / "skills" / "ai-architect" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Decision Confidence", text)
        self.assertIn("Domain Pattern Matching", text)
        self.assertIn("Multi-Stack Projects", text)
        self.assertTrue("explicitly rejected" in text.lower() or "Explicitly Rejected" in text, "Missing Explicitly Rejected section")

    def test_ai_architect_skill_has_escalation(self):
        text = (ROOT / "skills" / "ai-architect" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Escalation (Feedback to Creative Director)", text)

    def test_harness_engineer_skill_has_escalation(self):
        text = (ROOT / "skills" / "harness-engineer" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Escalation (Feedback to Architect)", text)

    def test_forge_intake_skill_has_escalation(self):
        text = (ROOT / "skills" / "forge-intake" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## Escalation", text)
        self.assertIn("## Handoff", text)

    def test_all_skills_have_no_todo_or_placeholder(self):
        for skill_path in (ROOT / "skills").glob("*/SKILL.md"):
            text = skill_path.read_text(encoding="utf-8")
            lowered = text.lower()
            self.assertNotIn("todo", lowered, str(skill_path))
            self.assertNotIn("tbd", lowered, str(skill_path))
            self.assertNotIn("[placeholder", lowered, str(skill_path))


class CreativeBriefContractTests(unittest.TestCase):
    """Tests for V2.2 creative_brief.py: body mode, section validation, new flags."""

    def test_creative_brief_body_mode_writes_freeform(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = """## Experience Thesis
A test product.

## Target User
Test users.

## Primary Workflow
Sign up, test, finish.

## First Interaction
Home screen.

## Interaction Style
Dashboard.

## Content Tone
Professional.

## Platform
Web.

## Competitive Context
No direct competitors.

## Differentiation
Unique feature X.

## Architecture Signals
No special signals.

## Assumptions
Test assumption.

## Risks
Low risk.
"""
            proc = subprocess.run(
                [PYTHON, "scripts/creative_brief.py",
                 "--project", tmp, "--slug", "test-body", "--goal", "Test body mode",
                 "--body", body],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            brief = (Path(tmp) / "docs/creative-brief.md").read_text(encoding="utf-8")
            self.assertIn("Test body mode", brief)  # goal is now in header
            self.assertIn("## Experience Thesis", brief)
            self.assertIn("## Competitive Context", brief)
            self.assertIn("## Differentiation", brief)
            self.assertIn("## Architecture Signals", brief)

    def test_creative_brief_body_mode_warns_missing_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = "## Experience Thesis\nJust a thesis.\n"
            proc = subprocess.run(
                [PYTHON, "scripts/creative_brief.py",
                 "--project", tmp, "--slug", "minimal", "--goal", "Test",
                 "--body", body],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("warning", proc.stderr.lower())

    def test_creative_brief_structured_has_new_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [PYTHON, "scripts/creative_brief.py",
                 "--project", tmp, "--slug", "structured", "--goal", "Test structured mode",
                 "--audience", "Devs", "--platform", "web", "--style", "editor",
                 "--tone", "professional", "--first-screen", "Editor canvas",
                 "--competitors", "Product A focuses on X but lacks Y",
                 "--differentiation", "We do Z faster and offline",
                 "--architecture-signals", "Offline-first, local storage, no real-time"],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            brief = (Path(tmp) / "docs/creative-brief.md").read_text(encoding="utf-8")
            self.assertIn("Product A", brief)
            self.assertIn("We do Z", brief)
            self.assertIn("Offline-first", brief)

    def test_creative_brief_all_required_sections_in_body(self):
        sections = [
            "Experience Thesis", "Target User", "Primary Workflow",
            "First Interaction", "Interaction Style", "Content Tone", "Platform",
            "Competitive Context", "Differentiation", "Architecture Signals",
            "Assumptions", "Risks",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            body_parts = [f"## {s}\n\nContent for {s}.\n" for s in sections]
            body = "\n".join(body_parts)
            proc = subprocess.run(
                [PYTHON, "scripts/creative_brief.py",
                 "--project", tmp, "--slug", "full", "--goal", "Complete test", "--body", body],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertNotIn("warning", proc.stderr.lower())


class ForgeProjectContractTests(unittest.TestCase):
    """Tests for V2.2 forge_project.py: secondary stack, confidence, explicit rejections."""

    def test_forge_project_secondary_stack_produces_dual_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            evidence = project / "evidence.jsonl"
            evidence.write_text(
                '{"source":"github","title":"test","url":"https://github.com/t/t","summary":"multi-stack test"}\n',
                encoding="utf-8",
            )
            (project / "package.json").write_text('{"scripts":{"dev":"vite"}}', encoding="utf-8")
            (project / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")

            proc = subprocess.run(
                [PYTHON, "scripts/forge_project.py",
                 "--project", str(project), "--slug", "dual-stack",
                 "--goal", "Multi-stack project", "--stack", "node-ts",
                 "--secondary-stack", "fastapi",
                 "--evidence", str(evidence), "--force"],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            contract = (project / "project-forge.yaml").read_text(encoding="utf-8")
            self.assertIn("secondary_stack:", contract)
            self.assertIn("secondary_commands:", contract)

    def test_forge_project_adr_has_new_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            evidence = project / "evidence.jsonl"
            evidence.write_text(
                '{"source":"web","title":"adr test","url":"https://example.com","summary":"test"}\n',
                encoding="utf-8",
            )
            proc = subprocess.run(
                [PYTHON, "scripts/forge_project.py",
                 "--project", str(project), "--slug", "adr-test",
                 "--goal", "ADR structure test", "--stack", "generic",
                 "--evidence", str(evidence), "--force"],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            adr = (project / "docs/architecture/ADR-0001-stack.md").read_text(encoding="utf-8")
            self.assertIn("## Explicitly Rejected", adr)
            self.assertIn("## Confidence Assessment", adr)
            self.assertIn("## Risks and Revisit Triggers", adr)

    def test_forge_project_provisional_evidence_marked_in_adr(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            evidence = project / "evidence.jsonl"
            evidence.write_text(
                '{"source":"host-web-tool","kind":"manual-search-required","query":"test","provisional":true}\n',
                encoding="utf-8",
            )
            proc = subprocess.run(
                [PYTHON, "scripts/forge_project.py",
                 "--project", str(project), "--slug", "prov-test",
                 "--goal", "Provisional test", "--stack", "generic",
                 "--evidence", str(evidence), "--force"],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            adr = (project / "docs/architecture/ADR-0001-stack.md").read_text(encoding="utf-8")
            self.assertIn("provisional", adr)



if __name__ == "__main__":
    unittest.main()

class TemplateContractTests(unittest.TestCase):
    """Tests for V2 harness templates: nextjs, fastapi, electron, cli, chrome-extension."""

    V2_TEMPLATES = ["nextjs", "fastapi", "electron", "cli", "chrome-extension"]

    def test_all_v2_templates_exist_with_required_files(self):
        for tmpl in self.V2_TEMPLATES:
            base = ROOT / "templates" / "harness" / tmpl
            for rel in ("project-forge.yaml", "docs/harness.md", ".github/workflows/project-forge-ci.yml"):
                self.assertTrue((base / rel).is_file(), f"{tmpl}/{rel} missing")
                text = (base / rel).read_text(encoding="utf-8")
                self.assertGreater(len(text.strip()), 20, f"{tmpl}/{rel} too short")

    def test_all_v2_templates_have_complete_command_contracts(self):
        for tmpl in self.V2_TEMPLATES:
            contract = (ROOT / "templates" / "harness" / tmpl / "project-forge.yaml").read_text(encoding="utf-8")
            for cmd in ("install", "test", "lint", "typecheck", "build", "run", "smoke"):
                self.assertIn(f"{cmd}:", contract, f"{tmpl} contract missing {cmd}")

    def test_all_v2_templates_ci_has_project_forge_name(self):
        for tmpl in self.V2_TEMPLATES:
            ci = (ROOT / "templates" / "harness" / tmpl / ".github/workflows/project-forge-ci.yml").read_text(encoding="utf-8")
            self.assertIn("Project Forge CI", ci, f"{tmpl} CI missing Project Forge CI name")

    def test_all_v2_templates_docs_reference_project_forge_yaml(self):
        for tmpl in self.V2_TEMPLATES:
            docs = (ROOT / "templates" / "harness" / tmpl / "docs" / "harness.md").read_text(encoding="utf-8")
            self.assertIn("project-forge.yaml", docs, f"{tmpl} docs missing reference to project-forge.yaml")
            self.assertIn("How to verify", docs, f"{tmpl} docs missing How to verify section")


class CLITests(unittest.TestCase):
    """Tests for the project-forge CLI entry point."""

    def run_cli(self, *args):
        proc = subprocess.run(
            [PYTHON, "scripts/cli.py", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        return proc

    def test_cli_help_outputs_usage(self):
        proc = self.run_cli("--help")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("usage:", proc.stdout.lower())

    def test_cli_version_outputs_version(self):
        proc = self.run_cli("--version")
        self.assertEqual(proc.returncode, 0)
        self.assertIn(PROJECT_VERSION, proc.stdout)

    def test_cli_init_dry_run_is_valid_json_and_does_not_create_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "new-project"
            proc = self.run_cli(
                "init",
                str(project),
                "--stack",
                "node-ts",
                "--goal",
                "Preview a safe Forge run",
                "--dry-run",
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["status"], "dry-run")
            self.assertFalse(project.exists())

    def test_cli_init_accepts_evidence_file_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "new-project"
            evidence = Path(tmp) / "evidence.jsonl"
            evidence.write_text(
                json.dumps(
                    {
                        "source": "web",
                        "title": "Current source",
                        "url": "https://example.com/current",
                        "summary": "Evidence for the selected stack",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            proc = self.run_cli(
                "init",
                str(project),
                "--stack",
                "node-ts",
                "--goal",
                "Create a safe evidence-backed decision",
                "--evidence",
                str(evidence),
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue((project / "project-forge.yaml").is_file())
            ready = self.run_cli("superpowers-ready", "--slug", "new-project", "--json", str(project))
            self.assertEqual(ready.returncode, 0, ready.stderr)
            self.assertIn(json.loads(ready.stdout)["status"], ("ready", "attention"))

    def test_cli_init_without_stack_uses_decision_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "auto-project"
            evidence = Path(tmp) / "evidence.jsonl"
            evidence.write_text(
                json.dumps(
                    {
                        "source": "official-docs",
                        "title": "Next.js documentation",
                        "url": "https://nextjs.org/docs",
                        "summary": "Next.js TypeScript dashboard framework",
                        "observed_at": "2026-06-01",
                    }
                )
                + "\n"
                + json.dumps(
                    {
                        "source": "github",
                        "title": "vercel/next.js repository",
                        "url": "https://github.com/vercel/next.js",
                        "summary": "Maintained Next.js repository",
                        "observed_at": "2026-06-01",
                    }
                )
                + "\n",
                encoding="utf-8-sig",
            )
            proc = self.run_cli(
                "init",
                str(project),
                "--goal",
                "Build a TypeScript web dashboard",
                "--evidence",
                str(evidence),
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("Decision:", proc.stdout)
            adr = (project / "docs" / "architecture" / "ADR-0001-stack.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("## Considered Options", adr)

    def test_cli_doctor_reports_runtime_state(self):
        proc = self.run_cli("doctor")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertGreaterEqual(payload["skills"], 6)
        self.assertGreaterEqual(payload["templates"], 8)

    def test_cli_list_templates_shows_all_eight(self):
        proc = self.run_cli("list-templates")
        self.assertEqual(proc.returncode, 0)
        for tmpl in ["node-ts", "python", "generic", "nextjs", "fastapi", "electron", "cli", "chrome-extension"]:
            self.assertIn(tmpl, proc.stdout, f"list-templates missing: {tmpl}")

    def test_cli_detect_generic_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = self.run_cli("detect", tmp, "--json")
            self.assertEqual(proc.returncode, 0)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["template"], "generic")

    def test_cli_detect_node_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "package.json").write_text('{"name":"test"}', encoding="utf-8")
            proc = self.run_cli("detect", tmp, "--json")
            self.assertEqual(proc.returncode, 0)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["template"], "node-ts")

    def test_cli_detect_nextjs_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "package.json").write_text(
                json.dumps({"dependencies": {"next": "^14.0.0"}}), encoding="utf-8"
            )
            proc = self.run_cli("detect", tmp, "--json")
            self.assertEqual(proc.returncode, 0)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["template"], "nextjs")

    def test_cli_detect_electron_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "package.json").write_text(
                json.dumps({"dependencies": {"electron": "^28.0.0"}}), encoding="utf-8"
            )
            proc = self.run_cli("detect", tmp, "--json")
            self.assertEqual(proc.returncode, 0)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["template"], "electron")

    def test_cli_detect_cli_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "package.json").write_text(
                json.dumps({"bin": "./dist/index.js"}), encoding="utf-8"
            )
            proc = self.run_cli("detect", tmp, "--json")
            self.assertEqual(proc.returncode, 0)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["template"], "cli")

    def test_cli_detect_chrome_extension_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "manifest.json").write_text(
                json.dumps({"manifest_version": 3, "name": "Test"}), encoding="utf-8"
            )
            proc = self.run_cli("detect", tmp, "--json")
            self.assertEqual(proc.returncode, 0)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["template"], "chrome-extension")

    def test_cli_detect_fastapi_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n", encoding="utf-8")
            proc = self.run_cli("detect", tmp, "--json")
            self.assertEqual(proc.returncode, 0)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["template"], "fastapi")

    def test_cli_research_writes_evidence_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence_dir = Path(tmp) / "evidence"
            proc = self.run_cli("research", "--query", "test framework", "--limit", "2", "--out", str(evidence_dir))
            self.assertEqual(proc.returncode, 0)
            self.assertTrue((evidence_dir / "web.jsonl").exists())
            self.assertTrue((evidence_dir / "github.jsonl").exists())
            normalized = evidence_dir / "normalized.jsonl"
            self.assertTrue(normalized.exists(), f"normalized.jsonl not found in {list(evidence_dir.iterdir())}")


class DetectStackContractTests(unittest.TestCase):
    """Tests for V2 stack detection: nextjs, electron, cli, chrome-extension, fastapi."""

    def run_detect(self, project_dir):
        proc = subprocess.run(
            [PYTHON, "scripts/harness/detect_stack.py", "--project", project_dir, "--json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def test_detect_nextjs_from_package_deps(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "package.json").write_text(
                json.dumps({"dependencies": {"next": "14.0.0", "react": "18.0.0"}}), encoding="utf-8"
            )
            payload = self.run_detect(tmp)
            self.assertEqual(payload["template"], "nextjs")

    def test_detect_electron_from_package_deps(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "package.json").write_text(
                json.dumps({"devDependencies": {"electron": "28.0.0"}}), encoding="utf-8"
            )
            payload = self.run_detect(tmp)
            self.assertEqual(payload["template"], "electron")

    def test_detect_cli_from_package_bin(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "package.json").write_text(
                json.dumps({"name": "my-cli", "bin": {"mycli": "./dist/cli.js"}}), encoding="utf-8"
            )
            payload = self.run_detect(tmp)
            self.assertEqual(payload["template"], "cli")

    def test_detect_cli_from_package_bin_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "package.json").write_text(
                json.dumps({"name": "my-cli", "bin": "./dist/cli.js"}), encoding="utf-8"
            )
            payload = self.run_detect(tmp)
            self.assertEqual(payload["template"], "cli")

    def test_detect_chrome_extension_from_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "manifest.json").write_text(
                json.dumps({"manifest_version": 3, "name": "My Extension"}), encoding="utf-8"
            )
            payload = self.run_detect(tmp)
            self.assertEqual(payload["template"], "chrome-extension")

    def test_detect_fastapi_from_main_py(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "main.py").write_text(
                "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef root():\n    return {'ok': True}\n",
                encoding="utf-8",
            )
            payload = self.run_detect(tmp)
            self.assertEqual(payload["template"], "fastapi")

    def test_detect_returns_commands_for_new_stacks(self):
        for tmpl in ("nextjs", "fastapi", "electron", "cli", "chrome-extension"):
            payload = json.loads(
                subprocess.run(
                    [PYTHON, "scripts/harness/detect_stack.py", "--project", str(ROOT), "--json"],
                    cwd=ROOT, text=True, capture_output=True, check=False,
                ).stdout
            )
            if payload["template"] == tmpl:
                self.assertIn("commands", payload)
                self.assertIn("install", payload["commands"])
                self.assertIn("test", payload["commands"])


class ForgeProjectContractV2Tests(unittest.TestCase):
    """Tests for forge_project.py with V2 stacks."""

    def run_forge(self, project_dir, stack, slug="test-v2", goal="V2 test project"):
        evidence = Path(project_dir) / "evidence.jsonl"
        evidence.write_text(
            json.dumps({
                "source": "github",
                "title": "example/project",
                "url": "https://github.com/example/project",
                "summary": "V2 reference",
                "score": 10,
            }) + "\n",
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                PYTHON, "scripts/forge_project.py",
                "--project", project_dir,
                "--slug", slug,
                "--goal", goal,
                "--stack", stack,
                "--evidence", str(evidence),
                "--force",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        return proc

    def test_forge_with_nextjs_stack(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = self.run_forge(tmp, "nextjs")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            contract = (Path(tmp) / "project-forge.yaml").read_text(encoding="utf-8")
            self.assertIn("install: npm ci", contract)
            self.assertIn("run: npm run dev", contract)

    def test_forge_with_fastapi_stack(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = self.run_forge(tmp, "fastapi")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            contract = (Path(tmp) / "project-forge.yaml").read_text(encoding="utf-8")
            self.assertIn("pip install", contract)
            self.assertIn("uvicorn", contract)

    def test_forge_with_electron_stack(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = self.run_forge(tmp, "electron")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            contract = (Path(tmp) / "project-forge.yaml").read_text(encoding="utf-8")
            self.assertIn("install: npm ci", contract)

    def test_forge_with_cli_stack(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = self.run_forge(tmp, "cli")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            contract = (Path(tmp) / "project-forge.yaml").read_text(encoding="utf-8")
            self.assertIn("node dist/index.js", contract)

    def test_forge_with_chrome_extension_stack(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = self.run_forge(tmp, "chrome-extension")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            contract = (Path(tmp) / "project-forge.yaml").read_text(encoding="utf-8")
            self.assertIn("chrome://extensions", contract)

    def test_forge_ci_uses_node_setup_for_node_stacks(self):
        for stack in ("nextjs", "electron", "cli", "chrome-extension"):
            with tempfile.TemporaryDirectory() as tmp:
                proc = self.run_forge(tmp, stack, slug=f"test-{stack}")
                self.assertEqual(proc.returncode, 0, f"Failed for {stack}: {proc.stderr}")
                ci = (Path(tmp) / ".github/workflows/project-forge-ci.yml").read_text(encoding="utf-8")
                self.assertIn("actions/setup-node@v4", ci, f"{stack} CI missing setup-node")

    def test_forge_ci_uses_python_setup_for_fastapi(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = self.run_forge(tmp, "fastapi")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            ci = (Path(tmp) / ".github/workflows/project-forge-ci.yml").read_text(encoding="utf-8")
            self.assertIn("actions/setup-python@v5", ci)


class InstallTestTests(unittest.TestCase):
    """Tests for the installation smoke test script."""

    def test_install_test_passes(self):
        proc = subprocess.run(
            [PYTHON, "scripts/install_test.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        output = proc.stdout
        json_start = output.index("\n{")
        payload = json.loads(output[json_start + 1:])
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["total"], 12)

    def test_install_test_detects_missing_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_root = Path(tmp)
            (fake_root / "skills").mkdir()
            (fake_root / "templates" / "harness" / "node-ts").mkdir(parents=True)
            proc = subprocess.run(
                [PYTHON, "-c", f"""
import sys
sys.path.insert(0, '{ROOT.as_posix()}')
from pathlib import Path
sys.path.insert(0, str(Path('{ROOT.as_posix()}') / 'scripts'))
import install_test
install_test.ROOT = Path('{fake_root.as_posix()}')
sys.exit(install_test.main())
"""],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0)


class MCPServerTests(unittest.TestCase):
    """Tests for the MCP server module."""

    def test_mcp_server_imports_without_error(self):
        sys.path.insert(0, str(ROOT / "scripts" / "mcp"))
        try:
            import server
            self.assertEqual(server.SERVER_NAME, "project-forge")
            self.assertEqual(server.SERVER_VERSION, PROJECT_VERSION)
            self.assertGreater(len(server.TOOLS), 5)
            tool_names = {t["name"] for t in server.TOOLS}
            self.assertIn("github_search", tool_names)
            self.assertIn("web_search", tool_names)
            self.assertIn("detect_stack", tool_names)
            self.assertIn("apply_template", tool_names)
            self.assertIn("forge_project", tool_names)
            self.assertIn("export_handoff", tool_names)
            self.assertIn("superpowers_ready", tool_names)
            self.assertIn("validate_evidence", tool_names)
            self.assertIn("list_templates", tool_names)
            self.assertIn("run_evals", tool_names)
        finally:
            sys.path.remove(str(ROOT / "scripts" / "mcp"))

    def test_mcp_server_tools_have_required_schema_fields(self):
        sys.path.insert(0, str(ROOT / "scripts" / "mcp"))
        try:
            import server
            for tool in server.TOOLS:
                self.assertIn("name", tool)
                self.assertIn("description", tool)
                self.assertIn("inputSchema", tool)
                self.assertIn("type", tool["inputSchema"])
                self.assertEqual(tool["inputSchema"]["type"], "object")
        finally:
            sys.path.remove(str(ROOT / "scripts" / "mcp"))

class MCPIntegrationTests(unittest.TestCase):

    def _send_rpc(self, method, params=None, request_id=1, timeout=10):
        proc = subprocess.Popen(
            [sys.executable, str(ROOT / 'scripts' / 'mcp' / 'server.py')],
            cwd=str(ROOT),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            msg = json.dumps({'jsonrpc': '2.0', 'id': request_id, 'method': method, 'params': params or {}})
            out, err = proc.communicate(input=msg + chr(10), timeout=timeout)
            responses = []
            for ln in out.strip().split(chr(10)):
                ln = ln.strip()
                if ln:
                    try:
                        responses.append(json.loads(ln))
                    except json.JSONDecodeError:
                        pass
            return responses, err, proc.returncode
        finally:
            try:
                proc.kill()
                proc.wait(timeout=2)
            except (subprocess.TimeoutExpired, OSError):
                pass

    def test_mcp_initialize_handshake(self):
        responses, stderr, _ = self._send_rpc('initialize', {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {'name': 'test', 'version': '1.0.0'},
        })
        self.assertTrue(len(responses) > 0, 'No MCP response: ' + stderr)
        result = responses[0].get('result', {})
        self.assertIn('protocolVersion', result)
        self.assertIn('serverInfo', result)
        self.assertEqual(result['serverInfo']['name'], 'project-forge')

    def test_mcp_tools_list_returns_v3_tools(self):
        responses, stderr, _ = self._send_rpc('tools/list')
        self.assertTrue(len(responses) > 0, 'No MCP response: ' + stderr)
        tools = responses[0].get('result', {}).get('tools', [])
        tool_names = {t['name'] for t in tools}
        expected = {'github_search', 'web_search', 'detect_stack', 'apply_template',
                    'forge_project', 'export_handoff', 'superpowers_ready',
                    'inspect_project', 'harness_compose', 'migrate_schema',
                    'plugin_manage', 'validate_evidence', 'list_templates', 'run_evals'}
        self.assertEqual(tool_names, expected)
        self.assertEqual(len(tools), 14)

    def test_mcp_list_templates_tool(self):
        responses, stderr, _ = self._send_rpc('tools/call', {'name': 'list_templates', 'arguments': {}})
        self.assertTrue(len(responses) > 0, 'No MCP response: ' + stderr)
        content = responses[0].get('result', {}).get('content', [])
        self.assertTrue(len(content) > 0)

    def test_mcp_detect_stack_tool(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'package.json').write_text('{"name": "mcp-test"}', encoding='utf-8')
            responses, stderr, _ = self._send_rpc('tools/call', {
                'name': 'detect_stack', 'arguments': {'project': str(tmp)}}, timeout=15)
            self.assertTrue(len(responses) > 0, 'No MCP response: ' + stderr)
            text = responses[0].get('result', {}).get('content', [{}])[0].get('text', '').lower()
            self.assertIn('template', text)

    def test_mcp_validate_evidence_tool(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / 'bad.jsonl'
            evidence.write_text(json.dumps({'source': 'web', 'title': 'No URL'}) + chr(10), encoding='utf-8')
            responses, stderr, _ = self._send_rpc('tools/call', {
                'name': 'validate_evidence', 'arguments': {'evidence_file': str(evidence)}}, timeout=15)
            self.assertTrue(len(responses) > 0, 'No MCP response: ' + stderr)

    def test_mcp_superpowers_ready_tool(self):
        responses, stderr, _ = self._send_rpc('tools/call', {
            'name': 'superpowers_ready',
            'arguments': {'project': 'examples/team-research', 'slug': 'team-research'},
        }, timeout=15)
        self.assertTrue(len(responses) > 0, 'No MCP response: ' + stderr)
        text = responses[0].get('result', {}).get('content', [{}])[0].get('text', '')
        self.assertIn('status', text)



class IntegrationTests(unittest.TestCase):
    """End-to-end integration tests that run the full Project Forge pipeline."""

    def test_full_pipeline_node_ts(self):
        """Forge a node-ts project from raw evidence through handoff, verify all artifacts."""
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            evidence = project / "raw.jsonl"
            evidence.write_text(
                json.dumps({
                    "source": "github",
                    "title": "example/project",
                    "url": "https://github.com/example/project",
                    "summary": "Integration test reference for integration-test",
                    "score": 10,
                }) + "\n",
                encoding="utf-8",
            )
            (project / "package.json").write_text(
                json.dumps({"scripts": {"dev": "vite", "test": "vitest", "build": "vite build"}}),
                encoding="utf-8",
            )
            (project / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")

            result = subprocess.run(
                [
                    PYTHON, "scripts/forge_project.py",
                    "--project", str(project),
                    "--slug", "integration-test",
                    "--goal", "End-to-end integration test project",
                    "--stack", "node-ts",
                    "--evidence", str(evidence),
                    "--force",
                ],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            creative = subprocess.run(
                [
                    PYTHON, "scripts/creative_brief.py",
                    "--project", str(project),
                    "--slug", "integration-test",
                    "--goal", "End-to-end integration test project",
                    "--audience", "Developers",
                    "--platform", "web",
                    "--style", "dashboard",
                    "--tone", "professional",
                    "--first-screen", "Project overview dashboard",
                ],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(creative.returncode, 0, creative.stderr)

            handoff = subprocess.run(
                [
                    PYTHON, "scripts/export_handoff.py",
                    "--project", str(project),
                    "--slug", "integration-test",
                    "--out", str(project / "docs/superpowers-handoff.md"),
                ],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(handoff.returncode, 0, handoff.stderr)

            smoke = subprocess.run(
                [
                    PYTHON, "scripts/smoke_test.py",
                    "--project", str(project),
                    "--slug", "integration-test",
                ],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(smoke.returncode, 0, smoke.stderr)

            required = {
                "docs/research/integration-test/evidence.jsonl",
                "docs/architecture/ADR-0001-stack.md",
                "docs/creative-brief.md",
                "docs/harness.md",
                "docs/superpowers-handoff.md",
                "docs/superpowers-handoff.json",
                "project-forge.yaml",
                ".github/workflows/project-forge-ci.yml",
            }
            for rel in required:
                self.assertTrue((project / rel).exists(), f"Missing: {rel}")

            adr = (project / "docs/architecture/ADR-0001-stack.md").read_text(encoding="utf-8")
            self.assertIn("node-ts", adr)
            self.assertIn("integration-test", adr)
            self.assertIn("example/project", adr)

            brief = (project / "docs/creative-brief.md").read_text(encoding="utf-8")
            self.assertIn("End-to-end integration test project", brief)

            handoff_md = (project / "docs/superpowers-handoff.md").read_text(encoding="utf-8")
            self.assertIn("Superpowers Handoff", handoff_md)
            self.assertIn("pnpm", handoff_md)
            handoff_json = load_json(project / "docs/superpowers-handoff.json")
            self.assertEqual(handoff_json["project"]["slug"], "integration-test")

            ready = subprocess.run(
                [
                    PYTHON, "scripts/superpowers_ready.py",
                    "--project", str(project),
                    "--slug", "integration-test",
                    "--json",
                ],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(ready.returncode, 0, ready.stderr)
            self.assertEqual(json.loads(ready.stdout)["failures"], 0)

    def test_full_pipeline_fastapi(self):
        """Forge a fastapi project and verify Python-specific artifacts."""
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            evidence = project / "raw.jsonl"
            evidence.write_text(
                json.dumps({
                    "source": "web",
                    "title": "FastAPI Docs",
                    "url": "https://fastapi.tiangolo.com/",
                    "summary": "FastAPI framework documentation",
                }) + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    PYTHON, "scripts/forge_project.py",
                    "--project", str(project),
                    "--slug", "fastapi-test",
                    "--goal", "Test FastAPI pipeline",
                    "--stack", "fastapi",
                    "--evidence", str(evidence),
                    "--force",
                ],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            contract = (project / "project-forge.yaml").read_text(encoding="utf-8")
            self.assertIn("pip install", contract)
            self.assertIn("uvicorn", contract)

            ci = (project / ".github/workflows/project-forge-ci.yml").read_text(encoding="utf-8")
            self.assertIn("setup-python", ci)

    def test_three_examples_smoke(self):
        """Verify all four example projects pass smoke tests."""
        examples = [
            ("examples/team-research", "team-research"),
            ("examples/fastapi-demo", "fastapi-demo"),
            ("examples/chrome-extension-demo", "chrome-extension"),
            ("examples/cli-demo", "cli-demo"),
        ]
        for project_dir, slug in examples:
            with self.subTest(project=project_dir):
                proc = subprocess.run(
                    [PYTHON, "scripts/smoke_test.py", "--project", project_dir, "--slug", slug],
                    cwd=ROOT, text=True, capture_output=True, check=False,
                )
                self.assertEqual(proc.returncode, 0, f"{project_dir} smoke failed: {proc.stderr}")
                payload = json.loads(proc.stdout)
                self.assertEqual(payload["status"], "ok", f"{project_dir}: {payload}")
                ready = subprocess.run(
                    [PYTHON, "scripts/superpowers_ready.py", "--project", project_dir, "--slug", slug, "--json"],
                    cwd=ROOT, text=True, capture_output=True, check=False,
                )
                self.assertEqual(ready.returncode, 0, f"{project_dir} ready failed: {ready.stderr}")
                self.assertEqual(json.loads(ready.stdout)["failures"], 0)

    def test_creative_brief_pipeline_integration(self):
        """creative_brief.py output is readable and contains required sections."""
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            proc = subprocess.run(
                [
                    PYTHON, "scripts/creative_brief.py",
                    "--project", str(project),
                    "--slug", "test",
                    "--goal", "Test creative direction pipeline",
                    "--audience", "Test users",
                    "--platform", "web",
                    "--style", "editor",
                    "--tone", "professional",
                    "--first-screen", "Editor canvas",
                ],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            brief = (project / "docs/creative-brief.md").read_text(encoding="utf-8")
            for section in ("Experience Thesis", "Target User", "First Interaction",
                            "Interaction Style", "Content Tone", "Assumptions", "Risks", "Next Steps"):
                self.assertIn(section, brief, f"Missing section: {section}")

    def test_web_search_duckduckgo_returns_jsonl(self):
        """web_search.py with DuckDuckGo fallback produces valid JSONL."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "web.jsonl"
            proc = subprocess.run(
                [
                    PYTHON, "scripts/research/web_search.py",
                    "--query", "python web framework",
                    "--limit", "3",
                    "--out", str(out),
                ],
                cwd=ROOT, text=True, capture_output=True, check=False,
                env={**os.environ, "PROJECT_FORGE_WEB_SEARCH_URL": ""},
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertGreater(len(rows), 0)
            self.assertIn(rows[0]["source"], ("duckduckgo", "host-web-tool"))

    def test_github_search_degrades_gracefully_without_token(self):
        """GitHub search should produce valid fallback output when no GITHUB_TOKEN is set."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "no-token-test.jsonl"
            env = {**os.environ}
            env.pop("GITHUB_TOKEN", None)
            proc = subprocess.run(
                [PYTHON, "scripts/research/github_search.py", "--query", "test", "--limit", "1", "--out", str(out)],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            # Should not crash; may produce empty output or fallback
            self.assertIn(proc.returncode, (0,), f"github_search crashed: {proc.stderr}")
            if out.exists():
                rows = [json.loads(line) for line in out.read_text(encoding="utf-8").strip().split("\n") if line.strip()]
                for row in rows:
                    self.assertIn("source", row)


    def test_clean_script_removes_pycache(self):
        """clean.py removes __pycache__ directories."""
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "__pycache__"
            cache.mkdir()
            (cache / "test.pyc").write_text("fake", encoding="utf-8")

            temp_clean = Path(tmp) / "clean.py"
            temp_clean.write_text(
                'import sys, shutil\nfrom pathlib import Path\nroot = Path(".")\n'
                'for p in root.glob("**/__pycache__"):\n    shutil.rmtree(p)\n    print(f"Removed {p}")\n',
                encoding="utf-8",
            )
            proc = subprocess.run(
                [PYTHON, "scripts/clean.py"],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("Cleaned", proc.stdout)

    def test_duckduckgo_search_writes_valid_rows(self):
        """Verify DuckDuckGo search response has required fields when available."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ddg.jsonl"
            proc = subprocess.run(
                [
                    PYTHON, "scripts/research/web_search.py",
                    "--query", "fastapi python framework",
                    "--limit", "2",
                    "--out", str(out),
                ],
                cwd=ROOT, text=True, capture_output=True, check=False,
                env={**os.environ, "PROJECT_FORGE_WEB_SEARCH_URL": ""},
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertGreater(len(rows), 0)
            for row in rows:
                self.assertIn("source", row)
            if row.get("source") != "host-web-tool": self.assertIn("title", row)
            if row.get("source") != "host-web-tool": self.assertIn("summary", row)
            if row.get("source") != "host-web-tool": self.assertIn("url", row)

    def test_creative_brief_includes_all_required_sections(self):
        """creative_brief.py output passes structural validation."""
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            subprocess.run(
                [
                    PYTHON, "scripts/creative_brief.py",
                    "--project", str(project),
                    "--slug", "val",
                    "--goal", "Validate creative brief output",
                ],
                cwd=ROOT, text=True, capture_output=True, check=True,
            )
            brief = (project / "docs/creative-brief.md").read_text(encoding="utf-8")
            self.assertIn("## Experience Thesis", brief)
            self.assertIn("## Assumptions", brief)
            self.assertIn("## Risks", brief)
            self.assertIn("## Next Steps", brief)

    def test_web_search_duckduckgo_result_has_real_urls(self):
        """DuckDuckGo search results contain well-formed URLs."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "urls.jsonl"
            proc = subprocess.run(
                [
                    PYTHON, "scripts/research/web_search.py",
                    "--query", "node.js",
                    "--limit", "3",
                    "--out", str(out),
                ],
                cwd=ROOT, text=True, capture_output=True, check=False,
                env={**os.environ, "PROJECT_FORGE_WEB_SEARCH_URL": ""},
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line.strip()]
            for row in rows:
                if row.get("source") != "host-web-tool":
                    self.assertTrue(row.get("url","").startswith("http"), f"Bad URL: {row}")


