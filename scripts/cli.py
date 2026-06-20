#!/usr/bin/env python3
"""project-forge CLI: unified entry point for Project Forge workflows.

Usage:
  project-forge init [--stack STACK] [--goal GOAL] [PROJECT_DIR]
  project-forge detect [--json] [PROJECT_DIR]
  project-forge research --query QUERY [--limit N] [--out DIR]
  project-forge handoff --slug SLUG [--out FILE] [PROJECT_DIR]
  project-forge superpowers-ready --slug SLUG [--json] [--strict] [PROJECT_DIR]
  project-forge inspect [--json] [PROJECT_DIR]
  project-forge harness compose --primary TEMPLATE:PATH [--secondary TEMPLATE:PATH]
  project-forge migrate --from 1 --to 2 [--dry-run] [PROJECT_DIR]
  project-forge smoke --slug SLUG [PROJECT_DIR]
  project-forge validate-evidence [EVIDENCE_FILE]
  project-forge list-templates
  project-forge --version
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path


SCRIPTS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_ROOT.parent

VERSION = "0.3.0"

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
        capture_output=True,
    )
    if proc.returncode != 0:
        if proc.stdout:
            print(proc.stdout, end="", file=sys.stderr)
        if proc.stderr:
            print(proc.stderr, end="", file=sys.stderr)
        sys.exit(proc.returncode)
    return proc.stdout


def write_decision_input(path, goal, evidence_path):
    evidence = []
    evidence_file = Path(evidence_path)
    if evidence_file.is_file():
        for line in evidence_file.read_text(encoding="utf-8-sig").splitlines():
            if line.strip():
                evidence.append(json.loads(line))
    payload = {
        "goal": goal,
        "constraints": [],
        "creative_brief": {},
        "evidence": evidence,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def cmd_init(args):
    project = Path(args.project or ".")
    project = project.resolve()

    if not args.slug:
        args.slug = project.name.lower().replace(" ", "-").replace("_", "-")

    stack = args.stack

    goal = args.goal or "Project created with Project Forge"

    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry-run",
                    "project": str(project),
                    "slug": args.slug,
                    "goal": goal,
                    "stack": stack or "auto",
                    "secondary": args.secondary,
                    "would_research": args.evidence is None,
                    "evidence": str(args.evidence) if args.evidence else None,
                    "would_generate": [
                        f"docs/research/{args.slug}/evidence.jsonl",
                        "docs/creative-brief.md",
                        "docs/architecture/ADR-0001-stack.md",
                        "project-forge.yaml",
                        "docs/harness.md",
                        "docs/superpowers-handoff.md",
                        "docs/superpowers-handoff.json",
                        ".github/workflows/project-forge-ci.yml",
                    ],
                    "force": args.force,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return

    if not project.exists():
        project.mkdir(parents=True)

    evidence_dir = Path(args.evidence) if args.evidence else None
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
            "--query", stack or goal,
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

    generated_decision = None
    if not stack and not args.decision_file:
        decision_dir = project / ".project-forge" / "decisions"
        decision_input = decision_dir / f"{args.slug}.input.json"
        generated_decision = decision_dir / f"{args.slug}.decision.json"
        write_decision_input(decision_input, goal, normalized)
        run_script(
            "decision/engine.py",
            "--input",
            str(decision_input),
            "--out",
            str(generated_decision),
            "--as-of",
            date.today().isoformat(),
        )
        decision_payload = json.loads(generated_decision.read_text(encoding="utf-8"))
        stack = decision_payload.get("selected_stack") or "generic"
        args.decision_file = str(generated_decision)

    if not stack:
        if project.exists():
            stdout = run_script("harness/detect_stack.py", "--project", str(project), "--json")
            detected = json.loads(stdout)
            stack = detected["template"]
        else:
            stack = "generic"

    if stack not in TEMPLATES:
        fail(f"Unknown template: {stack}. Available: {', '.join(TEMPLATES)}")

    forge_args = [
        "forge_project.py",
        "--project", str(project),
        "--slug", args.slug,
        "--goal", goal,
        "--stack", stack,
        "--evidence", str(normalized),
    ]
    if args.decision_file:
        forge_args.extend(["--decision-file", str(Path(args.decision_file).resolve())])
    if args.force:
        forge_args.append("--force")
    for secondary in args.secondary:
        forge_args.extend(["--secondary", secondary])
    forge_output = run_script(*forge_args)

    handoff = project / "docs" / "superpowers-handoff.md"
    handoff_json = project / "docs" / "superpowers-handoff.json"
    print(f"Project Forge initialized: {project}")
    print(f"  Stack: {stack}")
    print(f"  Slug: {args.slug}")
    print(f"  ADR: {project / 'docs' / 'architecture' / 'ADR-0001-stack.md'}")
    print(f"  Contract: {project / 'project-forge.yaml'}")
    print(f"  Handoff: {handoff}")
    print(f"  Handoff JSON: {handoff_json}")
    if generated_decision:
        print(f"  Decision: {generated_decision}")
    if forge_output.strip():
        print(f"  Run: {forge_output.strip()}")


def cmd_detect(args):
    project = args.project or "."
    output = run_script(
        "harness/detect_stack.py",
        "--project",
        project,
        *(["--json"] if args.json else []),
    )
    print(output, end="")


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
    handoff_args = [
        "export_handoff.py",
        "--project", str(project),
        "--slug", slug,
        "--out", out,
    ]
    if args.json_out:
        handoff_args.extend(["--json-out", args.json_out])
    run_script(*handoff_args)
    print(f"Handoff written: {out}")
    print(f"Handoff JSON written: {args.json_out or str(Path(out).with_suffix('.json'))}")


def cmd_superpowers_ready(args):
    project = Path(args.project or ".")
    ready_args = [
        "superpowers_ready.py",
        "--project", str(project),
        "--slug", args.slug,
    ]
    if args.json:
        ready_args.append("--json")
    if args.strict:
        ready_args.append("--strict")
    if args.execute:
        ready_args.append("--execute")
    if args.only:
        ready_args.extend(["--only", args.only])
    if args.include_install:
        ready_args.append("--include-install")
    if args.include_run:
        ready_args.append("--include-run")
    if args.allow_legacy_shell:
        ready_args.append("--allow-legacy-shell")
    ready_args.extend(["--timeout", str(args.timeout)])
    if args.continue_on_failure:
        ready_args.append("--continue-on-failure")
    output = run_script(*ready_args)
    print(output, end="")


def cmd_inspect(args):
    inspect_args = ["inspect_project.py", args.project]
    if args.json:
        inspect_args.append("--json")
    if args.out:
        inspect_args.extend(["--out-dir", args.out])
    print(run_script(*inspect_args), end="")


def cmd_harness_compose(args):
    compose_args = [
        "harness/compose.py",
        "--project", args.project,
        "--slug", args.slug,
        "--goal", args.goal,
        "--primary", args.primary,
    ]
    for secondary in args.secondary:
        compose_args.extend(["--secondary", secondary])
    if args.out:
        compose_args.extend(["--out", args.out])
    if args.dry_run:
        compose_args.append("--dry-run")
    print(run_script(*compose_args), end="")


def cmd_migrate(args):
    migrate_args = ["migrate.py", args.project, "--from", str(args.source), "--to", str(args.target)]
    if args.dry_run:
        migrate_args.append("--dry-run")
    if args.rollback:
        migrate_args.extend(["--rollback", args.rollback])
    print(run_script(*migrate_args), end="")


def cmd_plugin(args):
    plugin_args = ["install/manage.py", args.plugin_action, "--host", args.host]
    optional = {
        "--source": args.source,
        "--home": args.home,
        "--codex-home": args.codex_home,
        "--agents-home": args.agents_home,
        "--marketplace-root": args.marketplace_root,
        "--cachebuster": args.cachebuster,
        "--backup": args.backup,
    }
    for flag, value in optional.items():
        if value:
            plugin_args.extend([flag, value])
    if args.dry_run:
        plugin_args.append("--dry-run")
    print(run_script(*plugin_args), end="")


def cmd_smoke(args):
    project = Path(args.project or ".")
    slug = args.slug
    output = run_script(
        "smoke_test.py",
        "--project", str(project),
        "--slug", slug,
    )
    if output:
        print(output, end="")
    print("Smoke test passed.")


def cmd_validate_evidence(args):
    output = run_script("research/validate_evidence.py", args.evidence_file)
    if output:
        print(output, end="")
    print("Evidence validation passed.")


def cmd_backups(args):
    output = run_script("state_manager.py", "list", "--project", args.project)
    print(output, end="")


def cmd_restore(args):
    restore_args = [
        "state_manager.py",
        "restore",
        args.backup_id,
        "--project",
        args.project,
    ]
    if args.force:
        restore_args.append("--force")
    output = run_script(*restore_args)
    print(output, end="")


def cmd_doctor(args):
    checks = {
        "python": sys.version.split()[0],
        "repo_root": str(REPO_ROOT),
        "codex_manifest": (REPO_ROOT / ".codex-plugin" / "plugin.json").is_file(),
        "claude_manifest": (REPO_ROOT / ".claude-plugin" / "plugin.json").is_file(),
        "skills": len(list((REPO_ROOT / "skills").glob("*/SKILL.md"))),
        "templates": len(list((REPO_ROOT / "templates" / "harness").glob("*/project-forge.yaml"))),
        "codex_cli": shutil.which("codex"),
        "claude_cli": shutil.which("claude"),
        "git": shutil.which("git"),
    }
    checks["status"] = (
        "ok"
        if checks["codex_manifest"]
        and checks["claude_manifest"]
        and checks["skills"] >= 6
        and checks["templates"] >= 8
        else "error"
    )
    print(json.dumps(checks, indent=2, sort_keys=True))
    if checks["status"] != "ok":
        raise SystemExit(1)


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
    init_parser.add_argument("--decision-file", help="Structured architecture decision JSON")
    init_parser.add_argument("--secondary", action="append", default=[], help="Secondary TEMPLATE[:PATH]")
    init_parser.add_argument("--force", action="store_true", help="Back up and replace generated files")
    init_parser.add_argument("--dry-run", action="store_true", help="Show planned changes without writing")

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
    handoff_parser.add_argument("--json-out", help="Structured handoff JSON output path")
    handoff_parser.add_argument("project", nargs="?", default=".", help="Project directory")

    ready_parser = subparsers.add_parser("superpowers-ready", help="Check Superpowers handoff readiness")
    ready_parser.add_argument("--slug", required=True, help="Project slug")
    ready_parser.add_argument("--json", action="store_true", help="Output JSON")
    ready_parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    ready_parser.add_argument("--execute", action="store_true", help="Execute selected structured harness commands")
    ready_parser.add_argument("--only", help="Comma-separated command names")
    ready_parser.add_argument("--include-install", action="store_true", help="Include install command")
    ready_parser.add_argument("--include-run", action="store_true", help="Include long-running run command")
    ready_parser.add_argument("--allow-legacy-shell", action="store_true", help="Allow legacy shell strings")
    ready_parser.add_argument("--timeout", type=int, default=300, help="Per-command timeout seconds")
    ready_parser.add_argument("--continue-on-failure", action="store_true")
    ready_parser.add_argument("project", nargs="?", default=".", help="Project directory")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect an existing project architecture")
    inspect_parser.add_argument("project", nargs="?", default=".")
    inspect_parser.add_argument("--json", action="store_true")
    inspect_parser.add_argument("--out", help="Output directory")

    harness_parser = subparsers.add_parser("harness", help="Harness contract operations")
    harness_sub = harness_parser.add_subparsers(dest="harness_command", required=True)
    compose_parser = harness_sub.add_parser("compose", help="Compose Schema v2 harnesses")
    compose_parser.add_argument("--project", default=".")
    compose_parser.add_argument("--slug", required=True)
    compose_parser.add_argument("--goal", required=True)
    compose_parser.add_argument("--primary", required=True)
    compose_parser.add_argument("--secondary", action="append", default=[])
    compose_parser.add_argument("--out")
    compose_parser.add_argument("--dry-run", action="store_true")

    migrate_parser = subparsers.add_parser("migrate", help="Migrate Project Forge schemas")
    migrate_parser.add_argument("project", nargs="?", default=".")
    migrate_parser.add_argument("--from", dest="source", type=int, default=1)
    migrate_parser.add_argument("--to", dest="target", type=int, default=2)
    migrate_parser.add_argument("--dry-run", action="store_true")
    migrate_parser.add_argument("--rollback")

    plugin_parser = subparsers.add_parser("plugin", help="Manage Codex or Claude Code plugin installation")
    plugin_sub = plugin_parser.add_subparsers(dest="plugin_action", required=True)
    for action in ("install", "verify", "update", "uninstall", "restore"):
        action_parser = plugin_sub.add_parser(action, help=f"{action} a host plugin bundle")
        action_parser.add_argument("--host", choices=["codex", "claude"], required=True)
        action_parser.add_argument("--source")
        action_parser.add_argument("--home")
        action_parser.add_argument("--codex-home")
        action_parser.add_argument("--agents-home")
        action_parser.add_argument("--marketplace-root")
        action_parser.add_argument("--cachebuster")
        action_parser.add_argument("--backup")
        action_parser.add_argument("--dry-run", action="store_true")

    smoke_parser = subparsers.add_parser("smoke", help="Validate project artifacts")
    smoke_parser.add_argument("--slug", required=True, help="Project slug")
    smoke_parser.add_argument("project", nargs="?", default=".", help="Project directory")

    validate_parser = subparsers.add_parser("validate-evidence", help="Validate evidence file")
    validate_parser.add_argument("evidence_file", help="Path to evidence.jsonl")

    list_parser = subparsers.add_parser("list-templates", help="List available harness templates")

    backups_parser = subparsers.add_parser("backups", help="List Project Forge backups")
    backups_parser.add_argument("project", nargs="?", default=".", help="Project directory")

    restore_parser = subparsers.add_parser("restore", help="Restore generated files from a backup")
    restore_parser.add_argument("backup_id", help="Backup identifier")
    restore_parser.add_argument("project", nargs="?", default=".", help="Project directory")
    restore_parser.add_argument("--force", action="store_true", help="Replace current generated files")

    subparsers.add_parser("doctor", help="Check Project Forge runtime and plugin installation")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "init": cmd_init,
        "detect": cmd_detect,
        "research": cmd_research,
        "handoff": cmd_handoff,
        "superpowers-ready": cmd_superpowers_ready,
        "inspect": cmd_inspect,
        "harness": cmd_harness_compose,
        "migrate": cmd_migrate,
        "plugin": cmd_plugin,
        "smoke": cmd_smoke,
        "validate-evidence": cmd_validate_evidence,
        "list-templates": cmd_list_templates,
        "backups": cmd_backups,
        "restore": cmd_restore,
        "doctor": cmd_doctor,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()

