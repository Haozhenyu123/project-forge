"""Quality budget checks for the v0.3 domain package split."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class QualityBudgetTests(unittest.TestCase):
    def test_line_budgets_are_enforced_for_non_exempt_python_files(self):
        config = json.loads((ROOT / ".quality-budget.json").read_text(encoding="utf-8"))
        excluded = {item.replace("\\", "/") for item in config.get("excluded", [])}
        production_max = int(config["production_max_lines"])
        test_max = int(config["test_max_lines"])
        failures = []
        for base, limit in ((ROOT / "src", production_max), (ROOT / "tests", test_max)):
            for path in sorted(base.rglob("*.py")):
                relative = path.relative_to(ROOT).as_posix()
                if relative in excluded:
                    continue
                count = len(path.read_text(encoding="utf-8-sig").splitlines())
                if count > limit:
                    failures.append(f"{relative}: {count} > {limit}")
        self.assertEqual([], failures)

    def test_exceptions_are_documented(self):
        config = json.loads((ROOT / ".quality-budget.json").read_text(encoding="utf-8"))
        self.assertTrue(config.get("note"))
        self.assertIn("tests/test_project_forge.py", config.get("excluded", []))


if __name__ == "__main__":
    unittest.main()

