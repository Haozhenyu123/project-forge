import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "scripts" / "runtime"
SESSION_START = RUNTIME / "session_start.py"


class SessionStartRuntimeTests(unittest.TestCase):
    def _run_python_entry(self, source):
        event = {
            "session_id": "runtime-test",
            "cwd": str(ROOT),
            "hook_event_name": "SessionStart",
            "source": source,
        }
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env.pop("CLAUDE_PLUGIN_ROOT", None)
            env.pop("CODEX_PLUGIN_ROOT", None)
            proc = subprocess.run(
                [sys.executable, str(SESSION_START)],
                cwd=tmp,
                input=json.dumps(event),
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stderr, "")
        return json.loads(proc.stdout)

    def test_session_start_emits_structured_json(self):
        payload = self._run_python_entry("startup")
        self.assertEqual(
            payload["hookSpecificOutput"]["hookEventName"],
            "SessionStart",
        )
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Project Forge", context)
        self.assertIn("architecture", context.lower())
        self.assertIn("handoff", context.lower())

    def test_session_start_routes_all_supported_sources(self):
        expected_route_text = {
            "startup": "new session",
            "resume": "resumed session",
            "clear": "cleared session",
            "compact": "compacted session",
        }
        contexts = {}
        for source, route_text in expected_route_text.items():
            with self.subTest(source=source):
                payload = self._run_python_entry(source)
                context = payload["hookSpecificOutput"]["additionalContext"]
                self.assertIn(route_text, context.lower())
                contexts[source] = context
        self.assertEqual(len(set(contexts.values())), 4)

    def test_context_excludes_implementation_workflows(self):
        context = self._run_python_entry("startup")[
            "hookSpecificOutput"
        ]["additionalContext"].lower()
        forbidden = (
            "run tdd",
            "debug the code",
            "perform code review",
            "create a worktree",
            "implement the code",
        )
        for phrase in forbidden:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, context)
        self.assertIn("does not own", context)

    @unittest.skipUnless(os.name == "nt", "Windows cmd entry test")
    def test_windows_cmd_entry_emits_json(self):
        event = json.dumps({
            "hook_event_name": "SessionStart",
            "source": "resume",
        })
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                ["cmd.exe", "/d", "/c", str(RUNTIME / "session_start.cmd")],
                cwd=tmp,
                input=event,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertIn(
            "resumed session",
            payload["hookSpecificOutput"]["additionalContext"].lower(),
        )


class PluginRuntimeConfigurationTests(unittest.TestCase):
    def _assert_mcp_initializes(self, server, root_variable):
        script = Path(server["args"][0].replace(root_variable, str(ROOT)))
        cwd = Path(server["cwd"].replace(root_variable, str(ROOT)))
        self.assertTrue(script.is_file())
        self.assertTrue(cwd.is_dir())
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "runtime-test", "version": "1.0"},
            },
        })
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["HOME"] = tmp
            proc = subprocess.run(
                [sys.executable, str(script)],
                cwd=cwd,
                input=request + "\n",
                text=True,
                capture_output=True,
                check=False,
                env=env,
                timeout=10,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        response = json.loads(proc.stdout.strip().splitlines()[0])
        self.assertEqual(
            response["result"]["serverInfo"]["name"],
            "project-forge",
        )

    def test_hook_config_registers_every_session_start_route(self):
        config = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        entries = config["hooks"]["SessionStart"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["matcher"], "startup|resume")
        handler = entries[0]["hooks"][0]
        self.assertEqual(handler["type"], "command")
        self.assertIn("session_start.py", handler["command"])

    def test_codex_manifest_registers_hooks_and_mcp(self):
        manifest = json.loads(
            (ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["hooks"], "./hooks/hooks.json")
        mcp_path = ROOT / manifest["mcpServers"].removeprefix("./")
        config = json.loads(mcp_path.read_text(encoding="utf-8"))
        server = config["project-forge"]
        self.assertEqual(server["command"], "python")
        self.assertIn("${PLUGIN_ROOT}/scripts/mcp/server.py", server["args"])
        self._assert_mcp_initializes(server, "${PLUGIN_ROOT}")

    def test_claude_manifest_registers_hooks_and_mcp(self):
        manifest = json.loads(
            (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["hooks"], "./hooks/hooks.json")
        mcp_path = ROOT / manifest["mcpServers"].removeprefix("./")
        config = json.loads(mcp_path.read_text(encoding="utf-8"))
        server = config["mcpServers"]["project-forge"]
        self.assertEqual(server["command"], "python")
        self.assertIn(
            "${CLAUDE_PLUGIN_ROOT}/scripts/mcp/server.py",
            server["args"],
        )
        self._assert_mcp_initializes(server, "${CLAUDE_PLUGIN_ROOT}")


if __name__ == "__main__":
    unittest.main()
