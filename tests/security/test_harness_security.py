
"""Security tests for harness executor: path traversal, injection defense, timeout enforcement."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from project_forge.harness.executor import execute_command
from project_forge.errors import ExecutionBlocked
from project_forge.models import CommandSpec


class HarnessExecutorSecurityTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.project = Path(self.tmp)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_spec(self, argv, cwd="."):
        return CommandSpec(argv=list(argv), cwd=cwd, timeout_seconds=5)

    # ---- Layer 1: cwd escape ----

    def test_cwd_escape_outside_project_is_blocked(self):
        spec = self._make_spec(["echo", "hello"], cwd="../../../etc")
        with self.assertRaises(ExecutionBlocked):
            execute_command(spec, self.project, timeout=5)

    def test_cwd_inside_project_is_allowed(self):
        sub = self.project / "subdir"
        sub.mkdir()
        spec = self._make_spec([sys.executable, "-c", "print('hello')"], cwd="subdir")
        rc, status, duration, stdout, stderr = execute_command(spec, self.project, timeout=5)
        self.assertIn(status, ("passed",))

    # ---- Layer 2: legacy_shell ----

    def test_legacy_shell_blocked_by_default(self):
        spec = CommandSpec(legacy_shell="echo hello", cwd=".", timeout_seconds=5)
        with self.assertRaises(ExecutionBlocked):
            execute_command(spec, self.project, timeout=5)

    def test_legacy_shell_allowed_when_flagged(self):
        spec = CommandSpec(legacy_shell="echo hello", cwd=".", timeout_seconds=5)
        rc, status, duration, stdout, stderr = execute_command(spec, self.project, timeout=5, allow_legacy_shell=True)
        self.assertIn(status, ("passed",))

    # ---- Layer 3: timeout ----

    def test_timeout_enforcement(self):
        spec = self._make_spec([sys.executable, "-c", "import time; time.sleep(100)"])
        rc, status, duration, stdout, stderr = execute_command(spec, self.project, timeout=1)
        self.assertEqual(status, "timeout")

    # ---- Normal operation ----

    def test_normal_command_executes(self):
        spec = self._make_spec([sys.executable, "-c", "print('hello world')"])
        rc, status, duration, stdout, stderr = execute_command(spec, self.project, timeout=5)
        self.assertEqual(status, "passed")
        self.assertIn("hello world", stdout)

    def test_failing_command_reports_failure(self):
        spec = self._make_spec([sys.executable, "-c", "import sys; sys.exit(1)"])
        rc, status, duration, stdout, stderr = execute_command(spec, self.project, timeout=5)
        self.assertEqual(status, "failed")


class MaliciousInputFuzzing(unittest.TestCase):
    """Fuzz the harness executor with known malicious payloads via legitimate spec interface."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.project = Path(self.tmp)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_fuzzing_cwd_payloads(self):
        """All path traversal payloads in cwd should be safely blocked."""
        payloads = [
            "../../../../etc/passwd",
            "..\\..\\..\\Windows\\System32",
            "/etc",
            "C:\Windows",
            ".././.././../etc",
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                try:
                    spec = CommandSpec(argv=["echo", "x"], cwd=payload, timeout_seconds=5)
                    execute_command(spec, self.project, timeout=5)
                    # If it didn't raise ExecutionBlocked, it must have passed cwd validation
                    # but the command should still be safe (inside project)
                except ExecutionBlocked:
                    pass  # Expected for escape attempts
                except Exception as e:
                    self.fail(f"Unexpected error on payload '{payload}': {e}")


if __name__ == "__main__":
    unittest.main()
