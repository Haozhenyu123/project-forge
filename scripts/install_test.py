#!/usr/bin/env python3
"""Verify Project Forge installation: manifests, skills, scripts, and templates."""

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_SKILLS = [
    "forge-intake",
    "forge-project",
    "creative-director",
    "ai-architect",
    "harness-engineer",
    "agent-evaluator",
]

REQUIRED_TEMPLATES = [
    "node-ts",
    "python",
    "generic",
    "nextjs",
    "fastapi",
    "electron",
    "cli",
    "chrome-extension",
]

REQUIRED_SCRIPTS = [
    "cli.py",
    "forge_project.py",
    "smoke_test.py",
    "export_handoff.py",
    "creative_brief.py",
    "clean.py",
    "install_test.py",
    "harness/detect_stack.py",
    "harness/apply_template.py",
    "research/github_search.py",
    "research/web_search.py",
    "research/normalize_evidence.py",
    "research/validate_evidence.py",
    "evals/validate_scenarios.py",
    "evals/run_scenarios.py",
    "mcp/server.py",
]


def fail(message):
    print(f"FAIL: {message}")
    return False


def check_codex_manifest():
    path = ROOT / ".codex-plugin" / "plugin.json"
    if not path.is_file():
        return fail(f"Missing Codex manifest: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    for field in ("name", "version", "skills"):
        if field not in data:
            return fail(f"Codex manifest missing field: {field}")
    if data["skills"] != "./skills/":
        return fail("Codex manifest skills path must be ./skills/")
    if "interface" not in data:
        return fail("Codex manifest missing interface block")
    interface = data["interface"]
    for field in ("shortDescription", "developerName", "category", "capabilities", "defaultPrompt"):
        if field not in interface:
            return fail(f"Codex manifest interface missing field: {field}")
    print("  [OK] Codex manifest")
    return True


def check_claude_manifest():
    path = ROOT / ".claude-plugin" / "plugin.json"
    if not path.is_file():
        return fail(f"Missing Claude Code manifest: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    for field in ("name", "version", "skills", "displayName"):
        if field not in data:
            return fail(f"Claude Code manifest missing field: {field}")
    if data["displayName"] != "Project Forge":
        return fail("Claude Code manifest displayName must be 'Project Forge'")
    print("  [OK] Claude Code manifest")
    return True


def check_skills():
    skills_dir = ROOT / "skills"
    found = {p.parent.name for p in skills_dir.glob("*/SKILL.md")}
    missing = set(REQUIRED_SKILLS) - found
    if missing:
        return fail(f"Missing skills: {', '.join(sorted(missing))}")
    for skill_name in REQUIRED_SKILLS:
        path = skills_dir / skill_name / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            return fail(f"Skill {skill_name} missing YAML frontmatter")
        if "todo" in text.lower() or "tbd" in text.lower() or "[placeholder" in text.lower():
            return fail(f"Skill {skill_name} contains TODO/TBD/placeholder")
    print("  [OK] Skills ({})".format(len(REQUIRED_SKILLS)))
    return True


def check_templates():
    templates_dir = ROOT / "templates" / "harness"
    for tmpl in REQUIRED_TEMPLATES:
        base = templates_dir / tmpl
        if not base.is_dir():
            return fail(f"Missing template directory: {tmpl}")
        for rel in ("project-forge.yaml", "docs/harness.md", ".github/workflows/project-forge-ci.yml"):
            if not (base / rel).is_file():
                return fail(f"Template {tmpl} missing file: {rel}")
            text = (base / rel).read_text(encoding="utf-8")
            if len(text.strip()) < 20:
                return fail(f"Template {tmpl}/{rel} is too short or empty")
        contract = (base / "project-forge.yaml").read_text(encoding="utf-8")
        for cmd in ("install", "test", "lint", "typecheck", "build", "run", "smoke"):
            if f"{cmd}:" not in contract:
                return fail(f"Template {tmpl} contract missing command: {cmd}")
    print("  [OK] Templates ({})".format(len(REQUIRED_TEMPLATES)))
    return True


def check_scripts():
    for rel in REQUIRED_SCRIPTS:
        path = ROOT / "scripts" / rel
        if not path.is_file():
            return fail(f"Missing script: scripts/{rel}")
    print("  [OK] Scripts ({})".format(len(REQUIRED_SCRIPTS)))
    return True


def check_python_syntax():
    for py_file in sorted((ROOT / "scripts").glob("**/*.py")):
        proc = subprocess.run(
            [sys.executable, "-m", "py_compile", str(py_file)],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            return fail(f"Python syntax error in {py_file.relative_to(ROOT)}:\n{proc.stderr}")
    print("  [OK] Python syntax (all scripts)")
    return True


def check_marketplace():
    path = ROOT / "install" / "codex-marketplace.personal.json"
    if not path.is_file():
        return fail("Missing marketplace config: install/codex-marketplace.personal.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return fail("Marketplace config is not a JSON object")
    if "plugins" not in data and not isinstance(data, list):
        return fail("Marketplace config has no plugins key")
    print("  [OK] Marketplace config")
    return True


def check_readme():
    path = ROOT / "README.md"
    if not path.is_file():
        return fail("Missing README.md")
    text = path.read_text(encoding="utf-8")
    for section in ("install", "verify", "update"):
        if section not in text.lower():
            return fail(f"README missing section about: {section}")
    print("  [OK] README")
    return True


def check_docs():
    for doc in ("docs/architecture.md", "docs/quickstart.md", "docs/smoke-test.md", "docs/superpowers-handoff.md"):
        path = ROOT / doc
        if not path.is_file():
            return fail(f"Missing doc: {doc}")
        text = path.read_text(encoding="utf-8")
        if len(text.strip()) < 50:
            return fail(f"Doc too short: {doc}")
    print("  [OK] Docs (4)")
    return True


def check_examples():
    examples = [
        ("examples/team-research", "team-research"),
        ("examples/fastapi-demo", "fastapi-demo"),
        ("examples/chrome-extension-demo", "chrome-extension"),
        ("examples/cli-demo", "cli-demo"),
    ]
    for project_dir, slug in examples:
        path = ROOT / project_dir
        if not path.is_dir():
            return fail(f"Missing example: {project_dir}")
        for rel in ("project-forge.yaml", "docs/harness.md", "docs/creative-brief.md"):
            if not (path / rel).is_file():
                return fail(f"Example {project_dir} missing: {rel}")
        contract = (path / "project-forge.yaml").read_text(encoding="utf-8")
        if slug not in contract:
            return fail(f"Example {project_dir} contract missing slug {slug}")
    print("  [OK] Examples (4)")
    return True


def check_makefile():
    path = ROOT / "Makefile"
    if not path.is_file():
        return fail("Missing Makefile")
    text = path.read_text(encoding="utf-8")
    for target in ("test", "verify", "clean", "smoke"):
        if target not in text:
            return fail(f"Makefile missing target: {target}")
    print("  [OK] Makefile")
    return True


def check_editorconfig():
    path = ROOT / ".editorconfig"
    if not path.is_file():
        return fail("Missing .editorconfig")
    text = path.read_text(encoding="utf-8")
    if "root = true" not in text:
        return fail(".editorconfig missing root declaration")
    print("  [OK] .editorconfig")
    return True


def main():
    print("Project Forge Installation Smoke Test")
    print(f"  Root: {ROOT}")
    print()

    checks = [
        ("Codex manifest", check_codex_manifest),
        ("Claude Code manifest", check_claude_manifest),
        ("Skills", check_skills),
        ("Harness templates", check_templates),
        ("Scripts", check_scripts),
        ("Python syntax", check_python_syntax),
        ("Marketplace config", check_marketplace),
        ("README", check_readme),
        ("Docs", check_docs),
        ("Examples", check_examples),
        ("Makefile", check_makefile),
        (".editorconfig", check_editorconfig),
    ]

    results = {}
    for name, fn in checks:
        results[name] = fn()

    print()
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    status = "ok" if passed == total else "FAIL"

    print(f"Result: {passed}/{total} checks passed")

    payload = {"status": status, "passed": passed, "total": total, "checks": {
        name: "ok" if result else "fail"
        for name, result in results.items()
    }}
    print(json.dumps(payload, sort_keys=True, indent=2))

    return 0 if status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())







