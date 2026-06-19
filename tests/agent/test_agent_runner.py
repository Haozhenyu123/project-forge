import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVAL_SCRIPTS = ROOT / "scripts" / "evals"
if str(EVAL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(EVAL_SCRIPTS))

import agent_runner


def write_fake_cli(directory, body):
    path = Path(directory) / "fake_cli.py"
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return [sys.executable, str(path)]


def base_scenario(scenario_id="fake-agent"):
    return {
        "id": scenario_id,
        "title": "Fake agent",
        "prompt": "Use Project Forge for this request.",
        "expected_skills": ["forge-intake"],
        "forbid_tools_before_skill": True,
        "response_assertions": {
            "contains": ["Project Forge brief"],
            "not_contains": ["implemented the application"],
        },
        "artifact_assertions": [
            {
                "path": "docs/creative-brief.md",
                "contains": ["isolated-home", "Experience Thesis"],
            }
        ],
        "command_assertions": [
            {
                "argv": [
                    "{python}",
                    "-c",
                    "from pathlib import Path; "
                    "assert 'Experience Thesis' in "
                    "Path('docs/creative-brief.md').read_text(encoding='utf-8')",
                ],
                "exit_code": 0,
            }
        ],
    }


class ScenarioCompatibilityTests(unittest.TestCase):
    def test_existing_static_scenarios_remain_valid_and_scorable(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "static-results.json"
            validate = subprocess.run(
                [
                    sys.executable,
                    "scripts/evals/validate_scenarios.py",
                    "evals/scenarios",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validate.returncode, 0, validate.stderr)
            self.assertEqual(json.loads(validate.stdout)["scenario_count"], 6)

            score = subprocess.run(
                [
                    sys.executable,
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
            self.assertEqual(score.returncode, 0, score.stderr)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["scenario_count"], 6)

    def test_live_agent_cases_validate(self):
        paths = sorted((ROOT / "evals" / "agent").glob("*.json"))
        self.assertEqual(
            [path.stem for path in paths],
            [
                "forge-flow",
                "no-search",
                "trendy-framework",
                "vague-idea",
            ],
        )
        for path in paths:
            scenario = agent_runner.load_scenario(path)
            self.assertEqual(scenario["id"], path.stem)
            self.assertTrue(scenario["expected_skills"])


class CliDetectionTests(unittest.TestCase):
    def test_missing_cli_is_reported_as_skip(self):
        scenario = base_scenario()
        with tempfile.TemporaryDirectory() as tmp:
            result = agent_runner.run_scenario(
                scenario=scenario,
                provider="codex",
                repo_root=ROOT,
                log_root=Path(tmp) / "logs",
                command_override=["definitely-not-a-real-project-forge-cli"],
            )
        self.assertEqual(result["status"], "skip")
        self.assertIn("unavailable", result["reason"].lower())

    def test_detected_but_unexecutable_cli_is_reported_as_skip(self):
        scenario = base_scenario()
        with tempfile.TemporaryDirectory() as tmp:
            denied = write_fake_cli(
                tmp,
                """
                import sys
                raise SystemExit(13)
                """,
            )
            result = agent_runner.run_scenario(
                scenario=scenario,
                provider="codex",
                repo_root=ROOT,
                log_root=Path(tmp) / "logs",
                command_override=denied,
            )
        self.assertEqual(result["status"], "skip")
        self.assertIn("probe", result["reason"].lower())


class AgentExecutionTests(unittest.TestCase):
    def test_codex_jsonl_run_uses_isolated_home_and_checks_artifacts(self):
        scenario = base_scenario("codex-fake")
        with tempfile.TemporaryDirectory() as tmp:
            fake = write_fake_cli(
                tmp,
                r"""
                import json
                import os
                import sys
                from pathlib import Path

                if "--version" in sys.argv:
                    print("codex-fake 1.0")
                    raise SystemExit(0)

                project = Path.cwd()
                artifact = project / "docs" / "creative-brief.md"
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_text(
                    "# Creative Brief\n\n## Experience Thesis\n\nisolated-home="
                    + os.environ["HOME"],
                    encoding="utf-8",
                )
                print(json.dumps({
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": "read .codex/skills/forge-intake/SKILL.md",
                    },
                }))
                print(json.dumps({
                    "type": "item.completed",
                    "item": {
                        "type": "agent_message",
                        "text": "Project Forge brief is ready.",
                    },
                }))
                """,
            )
            result = agent_runner.run_scenario(
                scenario=scenario,
                provider="codex",
                repo_root=ROOT,
                log_root=Path(tmp) / "logs",
                command_override=fake,
            )
            log_dir = Path(result["log_dir"])
            events = [
                json.loads(line)
                for line in (log_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(result["status"], "pass", result)
        self.assertTrue(result["isolation"]["temporary_home"])
        self.assertTrue(result["isolation"]["temporary_project"])
        self.assertEqual(result["skills"]["triggered"], ["forge-intake"])
        self.assertEqual(result["tools_before_skill"], [])
        self.assertTrue(events)

    def test_claude_stream_json_tool_use_is_normalized(self):
        scenario = base_scenario("claude-fake")
        with tempfile.TemporaryDirectory() as tmp:
            fake = write_fake_cli(
                tmp,
                r"""
                import json
                import os
                import sys
                from pathlib import Path

                if "--version" in sys.argv:
                    print("claude-fake 1.0")
                    raise SystemExit(0)

                artifact = Path.cwd() / "docs" / "creative-brief.md"
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_text(
                    "## Experience Thesis\n\nisolated-home=" + os.environ["HOME"],
                    encoding="utf-8",
                )
                print(json.dumps({
                    "type": "assistant",
                    "message": {
                        "content": [{
                            "type": "tool_use",
                            "name": "Skill",
                            "input": {"skill": "forge-intake"},
                        }]
                    },
                }))
                print(json.dumps({
                    "type": "result",
                    "result": "Project Forge brief is ready.",
                }))
                """,
            )
            result = agent_runner.run_scenario(
                scenario=scenario,
                provider="claude",
                repo_root=ROOT,
                log_root=Path(tmp) / "logs",
                command_override=fake,
            )

        self.assertEqual(result["status"], "pass", result)
        self.assertIn("Skill", result["tools"]["called"])
        self.assertEqual(result["skills"]["triggered"], ["forge-intake"])

    def test_tools_before_required_skill_fail_the_run(self):
        scenario = base_scenario("early-tool")
        events = [
            {
                "type": "item.completed",
                "item": {"type": "command_execution", "command": "python build.py"},
            },
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Skill",
                            "input": {"skill": "forge-intake"},
                        }
                    ]
                },
            },
            {"type": "result", "result": "Project Forge brief is ready."},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            artifact = project / "docs" / "creative-brief.md"
            artifact.parent.mkdir(parents=True)
            artifact.write_text(
                "## Experience Thesis\n\nisolated-home",
                encoding="utf-8",
            )
            assertions = agent_runner.evaluate_assertions(
                scenario=scenario,
                events=events,
                project_dir=project,
                plugin_dir=project / ".project-forge-plugin",
            )

        self.assertFalse(assertions["passed"])
        self.assertEqual(assertions["tools_before_skill"], ["command_execution"])

    def test_timeout_is_a_failed_run_with_preserved_logs(self):
        scenario = base_scenario("timeout")
        scenario["timeout_seconds"] = 0.1
        with tempfile.TemporaryDirectory() as tmp:
            fake = write_fake_cli(
                tmp,
                """
                import sys
                import time
                if "--version" in sys.argv:
                    print("fake 1.0")
                    raise SystemExit(0)
                time.sleep(5)
                """,
            )
            result = agent_runner.run_scenario(
                scenario=scenario,
                provider="codex",
                repo_root=ROOT,
                log_root=Path(tmp) / "logs",
                command_override=fake,
            )
            log_dir = Path(result["log_dir"])
            self.assertTrue((log_dir / "stderr.log").exists())

        self.assertEqual(result["status"], "fail")
        self.assertTrue(result["timed_out"])


if __name__ == "__main__":
    unittest.main()
