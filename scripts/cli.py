#!/usr/bin/env python3
"""project-forge CLI: unified entry point for Project Forge workflows.

Usage:
  project-forge init [--stack STACK] [--goal GOAL] [PROJECT_DIR]
  project-forge detect [--json] [PROJECT_DIR]
  project-forge research --query QUERY [--limit N] [--out DIR]
  project-forge handoff --slug SLUG [--out FILE] [PROJECT_DIR]
  project-forge smoke --slug SLUG [PROJECT_DIR]
  project-forge validate-evidence [EVIDENCE_FILE]
  project-forge list-templates
  project-forge --version
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


SCRIPTS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_ROOT.parent

VERSION = "0.2.3"

TEMPLATES = [
    "node-ts",
    "python",
    "generic",
    "nextjs",
    "fastapi",
    "electron",
    "cli",
    "chrome-extension",
]


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def run_script(script, *args, cwd=None):
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_ROOT / script), *args],
        cwd=cwd or REPO_ROOT,
        text=True,
    )
    if proc.returncode != 0:
        sys.exit(proc.returncode)
    return proc.stdout


def cmd_init(args):
    project = Path(args.project or ".")
    project = project.resolve()

    if not project.exists():
        project.mkdir(parents=True)

    if not args.slug:
        args.slug = project.name.lower().replace(" ", "-").replace("_", "-")

    stack = args.stack
    if not stack:
        stdout = run_script("harness/detect_stack.py", "--project", str(project), "--json")
        detected = json.loads(stdout)
        if detected["template"] == "generic" and not args.stack:
            print(f"Detected generic project. Available templates: {', '.join(TEMPLATES)}")
            stack = "generic"
        else:
            stack = detected["template"]

    if stack not in TEMPLATES:
        fail(f"Unknown template: {stack}. Available: {', '.join(TEMPLATES)}")

    goal = args.goal or "Project created with Project Forge"
    if args.goal is None:
        print(f"Goal not specified; using default: {goal}")

    evidence_dir = args.evidence
    if not evidence_dir:
        evidence_dir = project / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        web_out = evidence_dir / "web.jsonl"
        github_out = evidence_dir / "github.jsonl"
        run_script(
            "research/web_search.py",
            "--query", goal,
            "--limit", "5",
            "--out", str(web_out),
        )
        run_script(
            "research/github_search.py",
            "--query", stack,
            "--limit", "5",
            "--out", str(github_out),
        )

    normalized = evidence_dir / "normalized.jsonl" if evidence_dir.is_dir() else evidence_dir
    if evidence_dir.is_dir():
        run_script(
            "research/normalize_evidence.py",
            "--input", str(evidence_dir),
            "--out", str(normalized),
        )

    run_script(
        "forge_project.py",
        "--project", str(project),
        "--slug", args.slug,
        "--goal", goal,
        "--stack", stack,
        "--evidence", str(normalized),
        "--force",
    )

    handoff = project / "docs" / "superpowers-handoff.md"
    run_script(
        "export_handoff.py",
        "--project", str(project),
        "--slug", args.slug,
        "--out", str(handoff),
    )

    print(f"Project Forge V2 initialized: {project}")
    print(f"  Stack: {stack}")
    print(f"  Slug: {args.slug}")
    print(f"  ADR: {project / 'docs' / 'architecture' / 'ADR-0001-stack.md'}")
    print(f"  Contract: {project / 'project-forge.yaml'}")
    print(f"  Handoff: {handoff}")


def cmd_detect(args):
    project = args.project or "."
    run_script("harness/detect_stack.py", "--project", project, *(["--json"] if args.json else []))


def cmd_research(args):
    evidence_dir = Path(args.out or "evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    run_script(
        "research/web_search.py",
        "--query", args.query,
        "--limit", str(args.limit or 5),
        "--out", str(evidence_dir / "web.jsonl"),
    )
    run_script(
        "research/github_search.py",
        "--query", args.query,
        "--limit", str(args.limit or 5),
        "--out", str(evidence_dir / "github.jsonl"),
    )
    normalized = evidence_dir / "normalized.jsonl"
    run_script(
        "research/normalize_evidence.py",
        "--input", str(evidence_dir),
        "--out", str(normalized),
    )
    print(f"Research complete: {normalized}")


def cmd_handoff(args):
    project = Path(args.project or ".")
    slug = args.slug
    out = args.out or str(project / "docs" / "superpowers-handoff.md")
    run_script(
        "export_handoff.py",
        "--project", str(project),
        "--slug", slug,
        "--out", out,
    )
    print(f"Handoff written: {out}")


def cmd_smoke(args):
    project = Path(args.project or ".")
    slug = args.slug
    run_script(
        "smoke_test.py",
        "--project", str(project),
        "--slug", slug,
    )
    print("Smoke test passed.")


def cmd_validate_evidence(args):
    run_script("research/validate_evidence.py", args.evidence_file)
    print("Evidence validation passed.")


def cmd_list_templates(args):
    print("Available harness templates:")
    for tmpl in TEMPLATES:
        tmpl_dir = REPO_ROOT / "templates" / "harness" / tmpl
        if tmpl_dir.is_dir():
            contract = tmpl_dir / "project-forge.yaml"
            first_line = ""
            if contract.is_file():
                first_line = contract.read_text(encoding="utf-8-sig").splitlines()[0]
                first_line = first_line.strip().replace("\ufeff", "")
            print(f"  {tmpl:<20} {first_line}")


def main():
    parser = argparse.ArgumentParser(
        description="Project Forge: AI-assisted architecture and harness engineering.",
        prog="project-forge",
    )
    parser.add_argument("--version", action="version", version=f"project-forge {VERSION}")

    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Initialize a new project with full Forge workflow")
    init_parser.add_argument("project", nargs="?", default=".", help="Project directory")
    init_parser.add_argument("--stack", choices=TEMPLATES, help="Harness template")
    init_parser.add_argument("--slug", help="Project slug (auto-derived from directory name)")
    init_parser.add_argument("--goal", help="Project goal description")
    init_parser.add_argument("--evidence", help="Path to pre-existing evidence file or directory")

    detect_parser = subparsers.add_parser("detect", help="Detect project stack")
    detect_parser.add_argument("project", nargs="?", default=".", help="Project directory")
    detect_parser.add_argument("--json", action="store_true", help="Output as JSON")

    research_parser = subparsers.add_parser("research", help="Gather evidence from GitHub and web")
    research_parser.add_argument("--query", required=True, help="Search query")
    research_parser.add_argument("--limit", type=int, help="Max results per source")
    research_parser.add_argument("--out", help="Output directory for evidence files")

    handoff_parser = subparsers.add_parser("handoff", help="Export Superpowers handoff")
    handoff_parser.add_argument("--slug", required=True, help="Project slug")
    handoff_parser.add_argument("--out", help="Output file path")
    handoff_parser.add_argument("project", nargs="?", default=".", help="Project directory")

    smoke_parser = subparsers.add_parser("smoke", help="Validate project artifacts")
    smoke_parser.add_argument("--slug", required=True, help="Project slug")
    smoke_parser.add_argument("project", nargs="?", default=".", help="Project directory")

    validate_parser = subparsers.add_parser("validate-evidence", help="Validate evidence file")
    validate_parser.add_argument("evidence_file", help="Path to evidence.jsonl")

    list_parser = subparsers.add_parser("list-templates", help="List available harness templates")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "init": cmd_init,
        "detect": cmd_detect,
        "research": cmd_research,
        "handoff": cmd_handoff,
        "smoke": cmd_smoke,
        "validate-evidence": cmd_validate_evidence,
        "list-templates": cmd_list_templates,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()

