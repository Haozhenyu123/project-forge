"""Tests for the read-only architecture inventory scanner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_forge.inventory import render_markdown, scan_project


def write_fixture(root: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


MONOREPO_FIXTURE = {
    "package.json": json.dumps(
        {"name": "forge-fixture", "private": True, "workspaces": ["apps/*", "services/*"]}
    ),
    "apps/web/package.json": json.dumps(
        {
            "name": "web",
            "dependencies": {"next": "15.0.0", "react": "19.0.0", "stripe": "17.0.0"},
        }
    ),
    "apps/web/app/page.tsx": "process.env.NEXT_PUBLIC_API_URL; server.listen(3000);",
    "apps/web/.env.example": "NEXT_PUBLIC_API_URL=http://localhost:8000\nSTRIPE_KEY=placeholder\n",
    "apps/web/Dockerfile": "FROM node:22\n",
    "apps/web/vercel.json": "{}",
    "services/api/requirements.txt": "fastapi\npsycopg\ncelery\nopenai\n",
    "services/api/app/main.py": (
        "from fastapi import FastAPI\n"
        "import os\n"
        "database = os.getenv('DATABASE_URL')\n"
        "token = os.environ['OPENAI_API_KEY']\n"
        "uvicorn.run(app, port=8000)\n"
    ),
    "docker-compose.yml": (
        "services:\n"
        "  db:\n    image: postgres:17\n    ports: ['5432:5432']\n"
        "  queue:\n    image: rabbitmq:4\n    ports: ['5672:5672']\n"
    ),
    ".github/workflows/ci.yml": "name: CI\nenv:\n  TOKEN: ${{ secrets.DEPLOY_TOKEN }}\n",
    "k8s/api.yaml": "kind: Deployment\n",
}


class InventoryScannerTests(unittest.TestCase):
    def test_monorepo_fixture_discovers_architecture_and_topology(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fixture(root, MONOREPO_FIXTURE)

            inventory = scan_project(root)

        self.assertTrue(inventory.monorepo)
        self.assertEqual([item.path for item in inventory.workspaces], ["apps/web", "services/api"])
        self.assertEqual([item.path for item in inventory.services], ["apps/web", "services/api"])
        web, api = inventory.services
        self.assertEqual(web.frameworks, ["Next.js", "React"])
        self.assertIn("app/page.tsx", web.entrypoints[0])
        self.assertIn(3000, web.ports)
        self.assertEqual(api.frameworks, ["FastAPI"])
        self.assertIn(8000, api.ports)
        self.assertIn("PostgreSQL", inventory.databases)
        self.assertIn("RabbitMQ", inventory.queues)
        self.assertIn("OpenAI", inventory.integrations)
        self.assertIn("Stripe", inventory.integrations)
        self.assertIn("DEPLOY_TOKEN", inventory.environment_variables)
        self.assertIn("DATABASE_URL", inventory.environment_variables)
        self.assertEqual(inventory.compose_files, ["docker-compose.yml"])
        self.assertEqual(inventory.ci_files, [".github/workflows/ci.yml"])
        self.assertIn("k8s/api.yaml", inventory.deploy_files)
        markdown = render_markdown(inventory)
        self.assertIn("```mermaid", markdown)
        self.assertIn("service_apps_web", markdown)
        self.assertIn("db_PostgreSQL", markdown)

    def test_real_dotenv_is_never_opened_and_values_never_escape(self) -> None:
        secret = "SENTINEL-SHOULD-NEVER-BE-READ"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fixture(
                root,
                {
                    "package.json": json.dumps({"name": "safe", "dependencies": {"express": "5"}}),
                    "src/index.js": "const key = process.env.PAYMENT_API_KEY; app.listen(4100);",
                    ".env": f"PAYMENT_API_KEY={secret}\n",
                },
            )
            original_read_text = Path.read_text

            def guarded_read_text(path: Path, *args: object, **kwargs: object) -> str:
                if path.name == ".env":
                    raise AssertionError("scanner attempted to open .env")
                return original_read_text(path, *args, **kwargs)

            with mock.patch.object(Path, "read_text", new=guarded_read_text):
                inventory = scan_project(root)
                rendered = json.dumps(inventory.to_dict()) + render_markdown(inventory)

        self.assertIn("PAYMENT_API_KEY", inventory.environment_variables)
        self.assertNotIn(secret, rendered)

    def test_scan_never_executes_target_code_or_subprocesses(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            marker = root / "executed.txt"
            write_fixture(
                root,
                {
                    "requirements.txt": "flask\n",
                    "main.py": f"from pathlib import Path\nPath({str(marker)!r}).write_text('bad')\n",
                },
            )
            with mock.patch("subprocess.run", side_effect=AssertionError("command executed")):
                inventory = scan_project(root)

        self.assertFalse(marker.exists())
        self.assertEqual(inventory.services[0].frameworks, ["Flask"])

    def test_compatibility_script_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fixture(root, {"package.json": json.dumps({"name": "tiny"}), "index.js": "app.listen(5050);"})
            result = subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "inspect_project.py"), str(root), "--json"],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            json_path = root / "docs" / "architecture" / "inventory.json"
            markdown_path = root / "docs" / "architecture" / "inventory.md"

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["project_name"], root.name)
            self.assertTrue(json_path.is_file())
            self.assertTrue(markdown_path.is_file())
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8")), payload)
            self.assertIn("flowchart LR", markdown_path.read_text(encoding="utf-8"))

    def test_no_write_mode_has_no_artifact_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fixture(root, {"main.py": "print('not executed')\n"})
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "inspect_project.py"),
                    str(root),
                    "--json",
                    "--no-write",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((root / "docs").exists())


if __name__ == "__main__":
    unittest.main()
