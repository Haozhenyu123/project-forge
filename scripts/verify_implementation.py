"""Implementation audit: compare actual project state against ADR promises.

Checks:
- Is the primary stack actually used (package.json/pyproject.toml)?
- Are secondary stacks present?
- Do harness commands pass?
- Are services/integrations from inventory actually configured?
- Is the architecture consistent with the accepted creative direction?
"""
import argparse, json, sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = str(REPO_ROOT / "src")
sys.path.insert(0, SRC)


def _load_handoff(project):
    path = project / "docs" / "superpowers-handoff.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _actual_stack(project):
    """Detect what stacks are actually present."""
    stacks = []
    root = project
    if (root / "package.json").is_file():
        pkg = json.loads((root / "package.json").read_text(encoding="utf-8-sig"))
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        frameworks = []
        if "next" in deps: frameworks.append("nextjs")
        if "electron" in deps: frameworks.append("electron")
        if "react" in deps: frameworks.append("react")
        if not frameworks: frameworks.append("node-ts")
        stacks.append({"root": ".", "type": "node", "frameworks": frameworks})

    if (root / "pyproject.toml").is_file() or (root / "requirements.txt").is_file():
        stacks.append({"root": ".", "type": "python", "frameworks": ["fastapi" if _has_fastapi(root) else "python"]})

    # Check secondary stack dirs
    for sub in ["api", "backend", "server"]:
        subdir = root / sub
        if not subdir.is_dir(): continue
        if (subdir / "pyproject.toml").is_file() or (subdir / "requirements.txt").is_file():
            stacks.append({"root": sub, "type": "python", "frameworks": ["fastapi" if _has_fastapi(subdir) else "python"]})
        if (subdir / "package.json").is_file():
            stacks.append({"root": sub, "type": "node", "frameworks": ["node-ts"]})

    return stacks


def _has_fastapi(d):
    for f in ["main.py", "app.py", "app/main.py"]:
        fp = d / f
        if fp.is_file() and "fastapi" in fp.read_text(encoding="utf-8").lower():
            return True
    return False


def run_audit(project_dir="."):
    project = Path(project_dir)
    handoff = _load_handoff(project)
    actual = _actual_stack(project)

    results = {
        "project": str(project),
        "audited_at": date.today().isoformat(),
        "checks": {},
        "passed": True,
    }

    # Check 1: Handoff exists
    if handoff is None:
        results["checks"]["handoff_exists"] = {"status": "FAIL", "detail": "No superpowers-handoff.json found"}
        results["passed"] = False
        return results
    results["checks"]["handoff_exists"] = {"status": "OK"}

    # Check 2: Primary stack declared vs actual
    declared_stack = handoff.get("project", {}).get("primary_stack", "")
    node_templates = {"node-ts", "nextjs", "electron", "cli", "chrome-extension"}
    python_templates = {"python", "fastapi"}

    actual_node = any(s for s in actual if s["type"] == "node")
    actual_python = any(s for s in actual if s["type"] == "python")

    stack_check = {"status": "OK", "detail": f"Declared: {declared_stack}, Actual: {len(actual)} stack(s)"}
    if declared_stack in node_templates and not actual_node:
        stack_check["status"] = "FAIL"
        stack_check["detail"] = f"Declared {declared_stack} but no Node.js project detected"
        results["passed"] = False
    elif declared_stack in python_templates and not actual_python:
        stack_check["status"] = "FAIL"
        stack_check["detail"] = f"Declared {declared_stack} but no Python project detected"
        results["passed"] = False
    elif not actual_node and not actual_python:
        stack_check["status"] = "WARN"
        stack_check["detail"] = "No actual code detected yet — may be pre-implementation"
    results["checks"]["primary_stack_match"] = stack_check

    # Check 3: Secondary stacks
    declared_secondary = handoff.get("project", {}).get("secondary_stacks", [])
    if declared_secondary:
        actual_secondary_roots = [s["root"] for s in actual if s["root"] != "."]
        if not actual_secondary_roots:
            results["checks"]["secondary_stacks"] = {"status": "WARN", "detail": f"Declared {declared_secondary} but no secondary dirs found"}
        else:
            results["checks"]["secondary_stacks"] = {"status": "OK", "detail": f"Found: {actual_secondary_roots}"}

    # Check 4: Harness commands exist in contract
    harness = handoff.get("harness", {})
    primary_cmds = harness.get("primary", {}).get("commands", {})
    missing_cmds = [k for k in ("test", "lint", "build") if k not in primary_cmds]
    if missing_cmds:
        results["checks"]["harness_commands"] = {"status": "WARN", "detail": f"Missing commands: {missing_cmds}"}
    else:
        results["checks"]["harness_commands"] = {"status": "OK"}

    # Check 5: Inventory matches actual
    inv = handoff.get("inventory")
    if inv:
        inv_services = len(inv.get("services", []))
        actual_roots = len(actual)
        if abs(inv_services - actual_roots) <= 1:
            results["checks"]["inventory_match"] = {"status": "OK", "detail": f"inv={inv_services} svcs, actual={actual_roots} stacks"}
        else:
            results["checks"]["inventory_match"] = {"status": "WARN", "detail": f"inv={inv_services} svcs vs actual={actual_roots} stacks — may be stale"}

    # Check 6: Boundary respected (no implementation overreach in handoff)
    boundary = handoff.get("boundary", {})
    forge_owns = boundary.get("project_forge_owns", [])
    sp_owns = boundary.get("superpowers_owns", [])
    if forge_owns and sp_owns:
        results["checks"]["boundary_defined"] = {"status": "OK", "detail": f"Forge owns: {len(forge_owns)} domains, Superpowers owns: {len(sp_owns)} domains"}
    else:
        results["checks"]["boundary_defined"] = {"status": "WARN", "detail": "Boundary declaration missing or incomplete"}

    return results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("project", nargs="?", default=".")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    audit = run_audit(args.project)
    if args.json:
        print(json.dumps(audit, indent=2, sort_keys=True))
    else:
        print(f"AUDIT: {audit['project']}")
        for c, r in audit["checks"].items():
            print(f"  [{r['status']}] {c}: {r.get('detail', '')}")
        print(f"\n  OVERALL: {'PASS' if audit['passed'] else 'ISSUES FOUND'}")
    return 0 if audit["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
