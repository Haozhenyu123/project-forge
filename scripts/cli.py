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
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path


SCRIPTS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_ROOT.parent
SRC = str(REPO_ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

def cmd_loop(args):
    """Handle project-forge loop sub-commands."""
    from project_forge.loop.service import ingest_signal, run_loop, resume_loop, get_loop_status
    import json as _json
    if args.loop_command == "ingest":
        signal_path = Path(args.file)
        if not signal_path.is_file():
            fail(f"Signal file not found: {args.file}")
        try:
            signal_data = _json.loads(signal_path.read_text(encoding="utf-8"))
        except _json.JSONDecodeError as exc:
            fail(f"Invalid JSON in signal file: {exc}")
        result = ingest_signal(args.project, signal_data)
        print(_json.dumps(result, indent=2, sort_keys=True))
    elif args.loop_command == "run":
        result = run_loop(args.project, args.slug)
        if getattr(args, "json", False):
            print(_json.dumps(result, indent=2, sort_keys=True))
        else:
            status = result.get("status", "unknown")
            episode = result.get("episode_id", "?")
            iteration = result.get("iteration", 0)
            action = result.get("action", "?")
            summary = result.get("summary", "")
            print(f"Loop run: {status}")
            print(f"  Episode: {episode}")
            print(f"  Iteration: {iteration}")
            print(f"  Action: {action}")
            if summary:
                print(f"  Summary: {summary}")
            if result.get("report_path"):
                print(f"  Report: {result['report_path']}")
    elif args.loop_command == "status":
        result = get_loop_status(args.project)
        if getattr(args, "json", False):
            print(_json.dumps(result, indent=2, sort_keys=True))
        else:
            print(f"Loop Status: {result.get('status', 'unknown')}")
            if result.get("status") != "no_loop":
                print(f"  Episode: {result.get('episode_id', '?')}")
                print(f"  Slug: {result.get('slug', '?')}")
                print(f"  Iterations: {result.get('iterations', 0)}")
                print(f"  Signals Processed: {result.get('signals_processed', 0)}")
                print(f"  Root Cause: {result.get('root_cause', 'none')}")
    elif args.loop_command == "resume":
        result = resume_loop(args.project, args.reason or "")
        print(_json.dumps(result, indent=2, sort_keys=True))


VERSION = "1.0.0"



def _load_templates():
    """Return available harness template names derived from the live catalog."""
    try:
        from project_forge.decision.catalog import load_catalog
        catalog = load_catalog()
        return sorted({s.harness.get("primary", s.id) for s in catalog.stacks if s.harness.get("primary")})
    except Exception:
        return ["node-ts", "python", "generic", "nextjs", "fastapi", "electron", "cli", "chrome-extension"]



def _closest_match(value, choices):
    """Return the closest matching choice using Levenshtein distance, or None if too far."""
    best, best_dist = None, 999
    for choice in choices:
        if value.lower() == choice.lower():
            return choice
        # Simple edit distance for short strings
        dist = _edit_distance(value.lower()[:20], choice.lower()[:20])
        if dist < best_dist:
            best, best_dist = choice, dist
    return best if best_dist <= 3 else None


def _edit_distance(a, b):
    """Levenshtein distance for short strings."""
    if len(a) < len(b):
        a, b = b, a
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(curr[-1] + 1, prev[j + 1] + 1, prev[j] + (ca != cb)))
        prev = curr
    return prev[-1]



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

    print(f"[1/6] Initializing project: {project}")
    if not project.exists():
        project.mkdir(parents=True)

    print("[2/6] Gathering evidence...")
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

    print("[3/6] Selecting architecture stack...")
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

        # Interactive mode: guided probing for product depth
        if args.interactive:
            print()
            print("=" * 60)
            print("  Project Forge Interactive Mode")
            print("  Answer a few questions to refine your architecture.")
            print("=" * 60)
            print()
            print(f"  Domain detected: {decision_payload.get('selected_direction', {}).get('id', 'unknown')}")
            print(f"  Goal: {goal}")
            print()

            # Step 0: Probe product depth
            print("--- Product Depth ---")
            depth = input("  Is this a prototype/MVP or a production system? [prototype/mvp/production] (default: mvp): ").strip().lower() or "mvp"
            platform = input("  Target platforms? [web/mobile/mini-program/desktop/multi] (default: web): ").strip().lower() or "web"
            print()

            # Step 1: Pick creative direction
            print(f"Goal: {goal}")
            print()

            # Step 1: Pick creative direction
            directions = decision_payload.get("product_directions", [])
            if directions:
                print("Creative Directions:")
                for i, d in enumerate(directions, 1):
                    print(f"  [{i}] {d['name']}: {d['promise']}")
                    print(f"      Audience: {d['audience']}")
                    print(f"      Scores: reach={d['scores']['reachability']}, diff={d['scores']['differentiation']}, value={d['scores']['value_signal']}, speed={d['scores']['validation_speed']}, cost={d['scores']['implementation_cost']}")
                    print(f"      Evidence: {d['evidence_confidence']} ({len(d.get('evidence_ids', []))} sources)")
                    print()
                choice = input(f"Pick direction [1-{len(directions)}, default=1]: ").strip()
                try:
                    idx = int(choice) - 1 if choice else 0
                    if 0 <= idx < len(directions):
                        decision_payload["selected_direction"] = directions[idx]["id"]
                        # Re-run decision with selected direction
                        payload_for_rerun = json.loads(decision_input.read_text(encoding="utf-8"))
                        payload_for_rerun["selected_direction_id"] = directions[idx]["id"]
                        decision_input.write_text(json.dumps(payload_for_rerun, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                        run_script(
                            "decision/engine.py",
                            "--input", str(decision_input),
                            "--out", str(generated_decision),
                            "--as-of", date.today().isoformat(),
                        )
                        decision_payload = json.loads(generated_decision.read_text(encoding="utf-8"))
                except (ValueError, IndexError):
                    pass  # Keep default

            # Step 2: Pick architecture stack
            candidates = decision_payload.get("architecture_candidates", [])
            if candidates:
                print()
                print("Architecture Candidates (top 3):")
                for i, c in enumerate(candidates, 1):
                    primary = c.get("harness", {}).get("primary", c["id"])
                    secondary = c.get("harness", {}).get("secondary", [])
                    stack_desc = primary
                    if secondary:
                        stack_desc += " + " + ", ".join(secondary)
                    print(f"  [{i}] {c['name']} (score: {c['score']})")
                    print(f"      Stack: {stack_desc}")
                    print(f"      Reason: {c.get('reason', '')}")
                    dims = c.get("scores", {}).get("dimensions", {})
                    if dims:
                        dim_str = ", ".join(f"{k}={v['score']}" for k, v in list(dims.items())[:5])
                        print(f"      Dimensions: {dim_str}")
                    print()
                choice = input(f"Pick stack [1-{len(candidates)}, default=1]: ").strip()
                try:
                    idx = int(choice) - 1 if choice else 0
                    if 0 <= idx < len(candidates):
                        stack = candidates[idx].get("harness", {}).get("primary", candidates[idx]["id"])
                        secondaries = candidates[idx].get("harness", {}).get("secondary", [])
                        if secondaries and not args.secondary:
                            args.secondary = secondaries
                except (ValueError, IndexError):
                    pass  # Keep default

        args.decision_file = str(generated_decision)

    if not stack:
        if project.exists():
            stdout = run_script("harness/detect_stack.py", "--project", str(project), "--json")
            detected = json.loads(stdout)
            stack = detected["template"]
        else:
            stack = "generic"

    if stack not in _load_templates():
        fail(f"Unknown template: {stack}. Available: {', '.join(TEMPLATES)}")

    print("[4/6] Generating project artifacts...")
    forge_args = [
        "forge_project.py",
        "--project", str(project),
        "--slug", args.slug,
        "--goal", goal,
        "--stack", stack,
        "--evidence", str(normalized),
    ]
    if hasattr(args, "lang") and args.lang and args.lang != "zh":
        forge_args.extend(["--lang", args.lang])
    if args.decision_file:
        forge_args.extend(["--decision-file", str(Path(args.decision_file).resolve())])
    if args.force:
        forge_args.append("--force")
    for secondary in args.secondary:
        forge_args.extend(["--secondary", secondary])
    forge_output = run_script(*forge_args)

    print("[5/6] Exporting Superpowers handoff...")
    handoff = project / "docs" / "superpowers-handoff.md"
    handoff_json = project / "docs" / "superpowers-handoff.json"
    print("[6/6] Complete! Summary:")
    print(f"  Project: {project}")
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


def cmd_audit(args):
    audit_args = ["audit_project.py", args.project]
    if args.json:
        audit_args.append("--json")
    output = run_script(*audit_args)
    print(output, end="")

def cmd_feature(args):
    feature_args = ["feature_handoff.py", args.feature_command]
    if getattr(args, "slug", None): feature_args.extend(["--slug", args.slug])
    if getattr(args, "feature_id", None): feature_args.extend(["--feature", args.feature_id])
    if getattr(args, "goal", None): feature_args.extend(["--goal", args.goal])
    feature_args.append(getattr(args, "project", "."))
    output = run_script(*feature_args)
    print(output, end="")

def cmd_adr(args):
    """Handle ADR sub-commands."""
    import json as _json
    from datetime import date as _date

    project = Path(args.project or ".")
    adr_dir = project / "docs" / "architecture"
    adr_dir.mkdir(parents=True, exist_ok=True)

    if args.adr_command == "list":
        adrs = sorted(adr_dir.glob("ADR-*.md"))
        if not adrs:
            print("No ADRs found.")
        else:
            print(f"Found {len(adrs)} ADR(s):")
            for adr in adrs:
                first_line = adr.read_text(encoding="utf-8").splitlines()[0]
                print(f"  {adr.name} — {first_line.lstrip('# ')}")
        return

    if args.adr_command == "new":
        # Determine ADR number
        existing = sorted(adr_dir.glob("ADR-*.md"))
        next_num = len(existing) + 1
        adr_name = f"ADR-{next_num:04d}-{args.type}.md"
        adr_path = adr_dir / adr_name

        lang_labels = {
            "zh": {"title": "标题", "context": "上下文", "options": "候选方案",
                    "decision": "决策", "reason": "理由", "rejected": "被拒绝的方案",
                    "consequences": "影响", "risks": "风险", "verification": "验证策略"},
            "en": {"title": "Title", "context": "Context", "options": "Considered Options",
                    "decision": "Decision", "reason": "Rationale", "rejected": "Rejected Alternatives",
                    "consequences": "Consequences", "risks": "Risks", "verification": "Verification Strategy"},
        }
        L = lang_labels.get(args.lang, lang_labels["en"])

        options_list = []
        if args.options:
            try:
                options_list = _json.loads(args.options)
            except _json.JSONDecodeError:
                options_list = [args.options]

        md = f"# {adr_name} — {args.title}\n\n"
        md += f"**{L['title']}**: {args.title}\n\n"
        md += f"## {L['context']}\n\n[Describe the context from the project brief.]\n\n"
        md += f"## {L['options']}\n\n"
        for opt in options_list:
            md += f"- {opt}\n"
        if not options_list:
            md += "[List 2-3 candidate options with evidence for/against each.]\n"
        md += f"\n## {L['decision']}\n\n**{args.decision}**\n\n"
        md += f"### {L['reason']}\n\n{args.reason}\n\n"
        md += f"## {L['rejected']}\n\n[What was NOT chosen and why.]\n\n"
        md += f"## {L['consequences']}\n\n[What becomes easier. What becomes harder.]\n\n"
        md += f"## {L['risks']}\n\n[What could make this decision wrong.]\n\n"
        md += f"## {L['verification']}\n\n[How to confirm this decision works.]\n"

        adr_path.write_text(md, encoding="utf-8")
        print(f"ADR created: {adr_path}")
        print(f"Fill in the bracketed sections to complete.")

def cmd_estimate(args):
    """Estimate pipeline token consumption for a given project goal."""
    sys.path.insert(0, str(REPO_ROOT / "src"))

    # Auto-detect domain if not provided
    domain = args.domain
    if not domain:
        try:
            from project_forge.intent import classify_intent
            result = classify_intent(args.goal)
            domain = result.primary_domain
        except Exception:
            domain = "general"

    # Token estimation model
    # Based on empirical observation of GPT-4o system prompt + user + assistant patterns
    BASE_STEPS = {
        "forge-intake":       {"tokens": 3000,  "label": "Intake & domain classification"},
        "creative-director":  {"tokens": 0,     "label": "Creative Director probing"},
        "ai-architect":       {"tokens": 5000,  "label": "Architecture reasoning + ADR"},
        "harness-engineer":   {"tokens": 3000,  "label": "Harness template application"},
        "forge-project":      {"tokens": 2000,  "label": "Coordinator & handoff export"},
    }

    # Creative Director costs scale with probing depth
    probing = args.probing_depth
    BASE_STEPS["creative-director"]["tokens"] = 4000 + probing * 3000  # ~3K per probing round

    # Architect costs scale with sub-ADRs
    sub_adrs = args.sub_adrs
    BASE_STEPS["ai-architect"]["tokens"] = 5000 + sub_adrs * 4000  # ~4K per sub-ADR

    # Route-based adjustments
    route_skip = {
        "full_pipeline":     set(),
        "stack_given":       {"creative-director", "ai-architect"},
        "existing_project":  {"forge-intake", "creative-director", "ai-architect"},
        "multi_stack":       set(),  # Same as full but with extra harness compose
        "architecture_only": {"harness-engineer", "forge-project"},
    }

    skipped = route_skip.get(args.route, set())

    # Model pricing per 1M tokens (input+output blended)
    MODEL_PRICES = {
        "gpt-4o":        {"input": 2.50, "output": 10.00, "blended": 5.00},
        "gpt-4o-mini":   {"input": 0.15, "output": 0.60,  "blended": 0.30},
        "claude-3.5":    {"input": 3.00, "output": 15.00, "blended": 8.00},
        "deepseek-v3":   {"input": 0.27, "output": 1.10,  "blended": 0.50},
    }
    price = MODEL_PRICES.get(args.model, MODEL_PRICES["gpt-4o"])

    print()
    print("=" * 60)
    print(f"  Project Forge Token Estimation")
    print(f"  Goal: {args.goal[:50]}{'...' if len(args.goal) > 50 else ''}")
    print(f"  Domain: {domain}  |  Route: {args.route}")
    print(f"  Probing depth: {probing} rounds  |  Sub-ADRs: {sub_adrs}")
    print(f"  Model: {args.model}")
    print("=" * 60)
    print()

    total = 0
    print(f"{'Step':<25s} {'Tokens':>10s} {'Cost':>10s}")
    print("-" * 47)

    for step_name, info in BASE_STEPS.items():
        if step_name in skipped:
            print(f"{info['label']:<25s} {'skipped':>10s} {'---':>10s}")
            continue
        tokens = info["tokens"]
        cost = (tokens / 1_000_000) * price["blended"]
        total += tokens
        print(f"{info['label']:<25s} {tokens:>8,}  ${cost:>8.4f}")

    total_cost = (total / 1_000_000) * price["blended"]

    # Extra: multi-stack adds harness compose overhead
    if args.route == "multi_stack":
        extra = 4000
        total += extra
        print(f"{'Harness compose (multi)':<25s} {extra:>8,}  ${(extra/1_000_000)*price['blended']:>8.4f}")
        total_cost = (total / 1_000_000) * price["blended"]

    print("-" * 47)
    print(f"{'TOTAL':<25s} {total:>8,}  ${total_cost:>8.4f}")
    print()
    print(f"  Range (low-confidence inputs):   {int(total*0.7):,} — {int(total*1.5):,} tokens")
    print(f"  Equivalent GPT-4o-mini cost:     ${(total/1_000_000)*0.30:.4f}")
    print()

    if args.route == "stack_given":
        print("  Tip: You already know your stack. Skipping creative")
        print("  direction and architecture saves ~50% of the pipeline.")
    print()

def cmd_revise(args):
    revise_args = ["revise_project.py", args.project, "--slug", args.slug, "--reason", args.reason]
    for c in getattr(args, "constraint", []): revise_args.extend(["--constraint", c])
    if getattr(args, "refresh_evidence", False): revise_args.append("--refresh-evidence")
    if getattr(args, "json", False): revise_args.append("--json")
    output = run_script(*revise_args)
    print(output, end="")

def cmd_diff(args):
    diff_args = ["diff_decisions.py", args.project]
    if getattr(args, "json", False): diff_args.append("--json")
    output = run_script(*diff_args)
    print(output, end="")

def cmd_cross_host(args):
    cross_args = ["evals/cross_host_compare.py", args.project, "--hosts", args.hosts]
    if getattr(args, "json", False): cross_args.append("--json")
    output = run_script(*cross_args)
    print(output, end="")

def cmd_verify_impl(args):
    output = run_script("verify_implementation.py", args.project, *(["--json"] if getattr(args, "json", False) else []))
    print(output, end="")

def cmd_summary(args):
    s_args = ["executive_summary.py", args.project]
    if getattr(args, "out", None):
        s_args.extend(["--out", args.out])
    output = run_script(*s_args)
    print(output, end="")

def cmd_patterns(args):
    import subprocess as _sp
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    result = _sp.run(
        [sys.executable, "-c", "from project_forge.decision.patterns import extract_patterns_from_history, save_patterns; p=extract_patterns_from_history(); save_patterns(p); print(len(p), 'patterns saved')"],
        cwd=REPO_ROOT, text=True, capture_output=True, timeout=30, env=env,
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

def cmd_lifecycle(args):
    from project_forge.harness.lifecycle import load_lifecycle_registry, check_deprecated
    registry = load_lifecycle_registry()
    tmpl = getattr(args, "template", None)
    if tmpl:
        rec = check_deprecated(tmpl, registry)
        if rec:
            print(f"Template {tmpl}: {rec.status} (since {rec.since})")
        else:
            print(f"Template {tmpl}: active")
    else:
        for tid, rec in sorted(registry.items()):
            print(f"{tid}: {rec.status}")

def cmd_e2e(args):
    import subprocess as _sp
    result = _sp.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "evals" / "e2e_real_test.py")],
        cwd=REPO_ROOT, timeout=120,
    )
    sys.exit(result.returncode)

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


def cmd_template(args):
    """Manage harness templates: list, install from external sources."""
    import json as _json, shutil, zipfile as _zipfile

    templates_dir = REPO_ROOT / "templates" / "harness"

    if args.template_command == "list":
        templates = sorted(d.name for d in templates_dir.iterdir() if d.is_dir() and (d / "manifest.json").is_file())
        if args.json:
            print(_json.dumps({"templates": templates, "count": len(templates)}, indent=2))
        else:
            print(f"Available templates ({len(templates)}):")
            for t in templates:
                manifest = _json.loads((templates_dir / t / "manifest.json").read_text(encoding="utf-8"))
                print(f"  {t:<24s} {manifest.get('name', t)}")
        return

    if args.template_command == "install":
        source = Path(args.source)
        name = args.name

        if not source.exists():
            fail(f"Source not found: {source}")

        # If zip, extract first
        if source.suffix == ".zip":
            import tempfile
            extract_dir = Path(tempfile.mkdtemp(prefix="pf-tmpl-"))
            with _zipfile.ZipFile(source, "r") as zf:
                zf.extractall(extract_dir)
            # Find the template root (contains manifest.json)
            for root_dir, dirs, files in os.walk(extract_dir):
                if "manifest.json" in files:
                    source = Path(root_dir)
                    break
            else:
                fail("No manifest.json found in zip archive")

        manifest_path = source / "manifest.json"
        if not manifest_path.is_file():
            fail(f"No manifest.json found in {source}")

        manifest = _json.loads(manifest_path.read_text(encoding="utf-8"))
        if not name:
            name = manifest.get("kind", source.name)

        dest = templates_dir / name
        if dest.exists() and not args.force:
            fail(f"Template '{name}' already exists. Use --force to overwrite.")

        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source, dest, ignore=shutil.ignore_patterns("__pycache__", ".git"))

        # Validate
        required = ["manifest.json", "project-forge.yaml", "docs/harness.md"]
        missing = [f for f in required if not (dest / f).is_file()]
        if missing:
            shutil.rmtree(dest)
            fail(f"Template missing required files: {missing}")

        print(f"Template '{name}' installed: {dest}")

def cmd_list_templates(args):
    print("Available harness templates:")
    for tmpl in _load_templates():
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
    init_parser.add_argument("--stack", choices=_load_templates(), help="Harness template")
    init_parser.add_argument("--slug", help="Project slug (auto-derived from directory name)")
    init_parser.add_argument("--goal", help="Project goal description")
    init_parser.add_argument("--evidence", help="Path to pre-existing evidence file or directory")
    init_parser.add_argument("--decision-file", help="Structured architecture decision JSON")
    init_parser.add_argument("--secondary", action="append", default=[], help="Secondary TEMPLATE[:PATH]")
    init_parser.add_argument(
    "--weights",
    help="Custom scoring weights as JSON file path or inline key=value pairs (e.g. security=2.0,speed=0.8,maintain=1.2)"
)
    init_parser.add_argument("--force", action="store_true", help="Back up and replace generated files")
    init_parser.add_argument("--interactive", action="store_true", help="Pause at creative direction and architecture for manual selection")
    init_parser.add_argument("--lang", choices=["zh", "en"], default="zh", help="Output language for creative brief and ADR (zh=中文, en=English)")
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

    
    # --- Template management ---
    template_parser = subparsers.add_parser("template", help="Manage harness templates")
    tmpl_sub = template_parser.add_subparsers(dest="template_command", required=True)
    tmpl_list = tmpl_sub.add_parser("list", help="List available templates")
    tmpl_list.add_argument("--json", action="store_true")
    tmpl_install = tmpl_sub.add_parser("install", help="Install a template from a directory or zip")
    tmpl_install.add_argument("source", help="Path to template directory or zip file")
    tmpl_install.add_argument("--name", help="Template name (auto-detected if omitted)")
    tmpl_install.add_argument("--force", action="store_true")

    list_parser = subparsers.add_parser("list-templates", help="List available harness templates")

    backups_parser = subparsers.add_parser("backups", help="List Project Forge backups")
    backups_parser.add_argument("project", nargs="?", default=".", help="Project directory")

    restore_parser = subparsers.add_parser("restore", help="Restore generated files from a backup")
    restore_parser.add_argument("backup_id", help="Backup identifier")
    restore_parser.add_argument("project", nargs="?", default=".", help="Project directory")
    restore_parser.add_argument("--force", action="store_true", help="Replace current generated files")

    
    audit_parser = subparsers.add_parser("audit", help="Audit an existing project architecture")
    audit_parser.add_argument("project", nargs="?", default=".", help="Project directory")
    audit_parser.add_argument("--json", action="store_true", help="Output JSON")

    feature_parser = subparsers.add_parser("feature", help="Manage scoped feature-level handoffs")
    feature_sub = feature_parser.add_subparsers(dest="feature_command", required=True)
    feat_new = feature_sub.add_parser("new", help="Create a scoped feature")
    feat_new.add_argument("--slug", required=True)
    feat_new.add_argument("--feature", required=True, dest="feature_id")
    feat_new.add_argument("--goal", required=True)
    feat_new.add_argument("project", nargs="?", default=".")
    feat_list = feature_sub.add_parser("list", help="List scoped features")
    feat_list.add_argument("project", nargs="?", default=".")
    feat_handoff = feature_sub.add_parser("handoff", help="Generate feature-level handoff")
    feat_handoff.add_argument("--slug", required=True)
    feat_handoff.add_argument("--feature", required=True, dest="feature_id")
    feat_handoff.add_argument("project", nargs="?", default=".")

    
    # --- ADR management ---
    adr_parser = subparsers.add_parser("adr", help="Manage Architecture Decision Records")
    adr_sub = adr_parser.add_subparsers(dest="adr_command", required=True)
    adr_new = adr_sub.add_parser("new", help="Create a new ADR")
    adr_new.add_argument("project", nargs="?", default=".", help="Project directory")
    adr_new.add_argument("--type", choices=["stack", "database", "auth", "deployment"], required=True, help="ADR type")
    adr_new.add_argument("--title", required=True, help="ADR title")
    adr_new.add_argument("--slug", required=True, help="Project slug")
    adr_new.add_argument("--decision", required=True, help="Selected option")
    adr_new.add_argument("--options", help="JSON list of considered options")
    adr_new.add_argument("--reason", required=True, help="Decision rationale")
    adr_new.add_argument("--lang", choices=["zh", "en"], default="zh")
    adr_list = adr_sub.add_parser("list", help="List existing ADRs")
    adr_list.add_argument("project", nargs="?", default=".", help="Project directory")
    
    revise_parser = subparsers.add_parser("revise", help="Revise architecture when Superpowers signals issues")
    revise_parser.add_argument("project", nargs="?", default=".")
    revise_parser.add_argument("--slug", required=True)
    revise_parser.add_argument("--reason", required=True)
    revise_parser.add_argument("--constraint", action="append", default=[])
    revise_parser.add_argument("--refresh-evidence", action="store_true")
    revise_parser.add_argument("--json", action="store_true")

    diff_parser = subparsers.add_parser("diff", help="Compare two architecture decisions")
    diff_parser.add_argument("project", nargs="?", default=".")
    diff_parser.add_argument("--json", action="store_true")

    cross_host_parser = subparsers.add_parser("cross-host", help="Compare handoff quality across hosts")
    cross_host_parser.add_argument("project", nargs="?", default=".")
    cross_host_parser.add_argument("--hosts", default="codex,claude")
    cross_host_parser.add_argument("--json", action="store_true")

    verify_impl_parser = subparsers.add_parser("verify-implementation", help="Audit actual code against ADR promises")
    verify_impl_parser.add_argument("project", nargs="?", default=".")
    verify_impl_parser.add_argument("--json", action="store_true")

    summary_parser = subparsers.add_parser("summary", help="Generate executive summary for stakeholders")
    summary_parser.add_argument("project", nargs="?", default=".")
    summary_parser.add_argument("--out", help="Output file path")

    patterns_parser = subparsers.add_parser("patterns", help="Extract decision patterns from project history")

    lifecycle_parser = subparsers.add_parser("lifecycle", help="Check template lifecycle status")
    lifecycle_parser.add_argument("--template", help="Template name to check")
    lifecycle_parser.add_argument("--json", action="store_true")

    e2e_parser = subparsers.add_parser("e2e-test", help="Run real end-to-end pipeline tests")

    # --- Token estimation ---
    estimate_parser = subparsers.add_parser("estimate", help="Estimate pipeline token consumption before running")
    estimate_parser.add_argument("--goal", required=True, help="Project goal description")
    estimate_parser.add_argument("--domain", help="Domain tag (auto-detected if omitted)")
    estimate_parser.add_argument("--route", choices=["full_pipeline", "stack_given", "existing_project", "multi_stack", "architecture_only"], default="full_pipeline", help="Pipeline route mode")
    estimate_parser.add_argument("--probing-depth", type=int, choices=[1, 2, 3, 4, 5], default=3, help="Expected number of probing rounds")
    estimate_parser.add_argument("--sub-adrs", type=int, choices=[0, 1, 2, 3], default=0, help="Expected sub-ADR count")
    estimate_parser.add_argument("--model", choices=["gpt-4o", "gpt-4o-mini", "claude-3.5", "deepseek-v3"], default="gpt-4o", help="LLM model for cost estimation")

    subparsers.add_parser("doctor", help="Check Project Forge runtime and plugin installation")

    loop_parser = subparsers.add_parser("loop", help="Decision Loop Engineering")
    loop_sub = loop_parser.add_subparsers(dest="loop_command", required=True)
    loop_ingest = loop_sub.add_parser("ingest", help="Ingest a loop signal")
    loop_ingest.add_argument("project", nargs="?", default=".", help="Project directory")
    loop_ingest.add_argument("--file", required=True, help="Path to signal JSON file")
    loop_run = loop_sub.add_parser("run", help="Run one loop iteration")
    loop_run.add_argument("project", nargs="?", default=".", help="Project directory")
    loop_run.add_argument("--slug", required=True, help="Project slug")
    loop_run.add_argument("--json", action="store_true", help="JSON output")
    loop_status = loop_sub.add_parser("status", help="Show loop status")
    loop_status.add_argument("project", nargs="?", default=".", help="Project directory")
    loop_status.add_argument("--json", action="store_true", help="JSON output")
    loop_resume = loop_sub.add_parser("resume", help="Resume a blocked or failed loop")
    loop_resume.add_argument("project", nargs="?", default=".", help="Project directory")
    loop_resume.add_argument("--reason", help="Reason for resuming")

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
        "template": cmd_template,
    "list-templates": cmd_list_templates,
        "backups": cmd_backups,
        "restore": cmd_restore,
        "audit": cmd_audit,
        "feature": cmd_feature,
        "revise": cmd_revise,
        "diff": cmd_diff,
        "cross-host": cmd_cross_host,
        "verify-implementation": cmd_verify_impl,
        "summary": cmd_summary,
        "patterns": cmd_patterns,
        "lifecycle": cmd_lifecycle,
        "e2e-test": cmd_e2e,
        "doctor": cmd_doctor,
        "adr": cmd_adr,
    "estimate": cmd_estimate,
    "loop": cmd_loop,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()


