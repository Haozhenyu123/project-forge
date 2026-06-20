#!/usr/bin/env python3
"""CI quality budget gate: enforce line-count limits from .quality-budget.json."""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def load_budget():
    budget_path = REPO_ROOT / ".quality-budget.json"
    if not budget_path.exists():
        return {}, set(), 400, 600
    data = json.loads(budget_path.read_text(encoding="utf-8"))
    prod_max = int(data.get("production_max_lines", 400))
    test_max = int(data.get("test_max_lines", 600))
    excluded = set(data.get("excluded", []))
    exception_map = {}
    for exc in data.get("exceptions", []):
        exception_map[exc.get("file", "")] = exc.get("reason", "No reason recorded")
    return exception_map, excluded, prod_max, test_max

def is_test_file(path: Path) -> bool:
    name = path.name
    return "test_" in name or name.startswith("test")

def line_count(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except Exception:
        return 0
    return len([l for l in text.splitlines() if l.strip() or l == ""])

def main():
    exception_map, excluded, prod_max, test_max = load_budget()
    violations = []
    for root_dir in [REPO_ROOT / "src", REPO_ROOT / "tests"]:
        if not root_dir.exists():
            continue
        for py_file in sorted(root_dir.rglob("*.py")):
            rel = str(py_file.relative_to(REPO_ROOT))
            if rel in exception_map:
                print(f"SKIP (exception): {rel}")
                continue
            if rel in excluded:
                print(f"SKIP (excluded): {rel}")
                continue
            count = line_count(py_file)
            limit = test_max if is_test_file(py_file) else prod_max
            if count > limit:
                violations.append(f"OVER BUDGET: {rel} has {count} lines (limit: {limit})")
    if violations:
        print("\n=== QUALITY BUDGET VIOLATIONS ===")
        for v in violations:
            print(v)
        print(f"\n{len(violations)} file(s) exceed the quality budget.")
        return 1
    print(f"Quality budget gate passed ({prod_max} prod / {test_max} test)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
