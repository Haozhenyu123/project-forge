#!/usr/bin/env python3
"""Write a creative-brief.md from a project goal, slug, and direction inputs.

Supports two modes:
1. CLI flags for structured fields (fast, for scripts)
2. --body for freeform Markdown (for agent-authored rich briefs)

Mode 2 is preferred when the agent writes competitive analysis, differentiation,
and architecture signals that cannot be expressed through flat CLI flags.
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_SECTIONS = [
    "Experience Thesis",
    "Target User",
    "Primary Workflow",
    "First Interaction",
    "Interaction Style",
    "Content Tone",
    "Platform",
    "Competitive Context",
    "Differentiation",
    "Architecture Signals",
    "Assumptions",
    "Risks",
]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="Target project directory")
    parser.add_argument("--slug", required=True, help="Project slug")
    parser.add_argument("--goal", required=True, help="Project goal in one sentence")
    parser.add_argument("--audience", default="", help="Target user description")
    parser.add_argument("--platform", default="", help="Target platform (web, desktop, mobile, cli, extension)")
    parser.add_argument("--style", default="", help="Interaction style (dashboard, editor, guided, etc.)")
    parser.add_argument("--tone", default="", help="Content tone (professional, playful, calm, exact)")
    parser.add_argument("--first-screen", default="", help="What the user sees first")
    parser.add_argument("--competitors", default="", help="Competing products or approaches and their gaps")
    parser.add_argument("--differentiation", default="", help="What makes this product different from alternatives")
    parser.add_argument("--architecture-signals", default="", help="Creative choices that constrain architecture (e.g. real-time, offline-first, collaborative)")
    parser.add_argument("--body", default="", help="Freeform Markdown body; overrides structured fields when present")
    parser.add_argument("--out", default="", help="Output path (default: docs/creative-brief.md)")
    return parser.parse_args()


def render_structured(args):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Creative Brief",
        "",
        f"- Project slug: `{args.slug}`",
        f"- Created: {now}",
        "",
        "## Experience Thesis",
        "",
        args.goal,
        "",
        "## Target User",
        "",
        args.audience or "Not specified; infer from the goal before implementing.",
        "",
        "## Primary Workflow",
        "",
        f"User arrives at {args.first_screen or 'the first useful interaction'} and proceeds through the core task.",
        "",
        "## First Interaction",
        "",
        args.first_screen or "Not specified; start with the smallest useful workflow.",
        "",
        "## Interaction Style",
        "",
        args.style or "Not specified; prefer the style that matches the user's expectation and platform conventions.",
        "",
        "## Content Tone",
        "",
        args.tone or "Not specified; default to clear, direct language.",
        "",
        "## Platform",
        "",
        args.platform or "Not specified; choose the platform that best fits the user's context and workflow.",
        "",
        "## Competitive Context",
        "",
        args.competitors or "No competitive analysis provided. Research existing solutions before finalizing direction.",
        "",
        "## Differentiation",
        "",
        args.differentiation or "No differentiation strategy provided. Define what makes this product uniquely valuable.",
        "",
        "## Architecture Signals",
        "",
        args.architecture_signals or "No architecture signals recorded. The architect should infer constraints from the platform and interaction style.",
        "",
        "## Assumptions",
        "",
    ]
    if args.audience:
        lines.append(f"- Target user '{args.audience}' is an assumption; validate with user research.")
    if args.platform:
        lines.append(f"- Platform '{args.platform}' is an assumption; confirm deployment target.")
    if args.style:
        lines.append(f"- Interaction style '{args.style}' is an assumption; validate with a prototype.")
    if args.differentiation:
        lines.append(f"- Differentiation claim is an assumption; test against user expectations.")
    if not any([args.audience, args.platform, args.style, args.differentiation]):
        lines.append("- No explicit assumptions recorded; all direction decisions are provisional.")

    lines.extend([
        "",
        "## Risks",
        "",
        "- If the target user or platform is wrong, the MVP may need significant rework.",
        "- Vague goals lead to scope creep; pin down the first useful workflow before expanding.",
        "- Creative direction without user validation is speculation; test assumptions early.",
        "- Missing competitive context means the product may duplicate existing solutions.",
        "",
        "## Next Steps",
        "",
        "1. Hand this brief to `ai-architect` for evidence-backed stack selection.",
        "2. Architect should use Architecture Signals to narrow the stack search space.",
        "3. Run research scripts to gather GitHub and web evidence for the chosen direction.",
        "4. Apply a harness template once the stack is confirmed.",
        "",
    ])
    return "\n".join(lines)


def validate_body_sections(body_text):
    """Check that a freeform brief has the expected section headers."""
    missing = []
    for section in REQUIRED_SECTIONS:
        pattern = rf"^##\s+{re.escape(section)}"
        if not re.search(pattern, body_text, re.MULTILINE):
            missing.append(section)
    return missing


def render_freeform(args, body_text):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    header = f"# Creative Brief\n\n- Project slug: `{args.slug}`\n- Goal: {args.goal}\n- Created: {now}\n\n"
    return header + body_text.strip() + "\n"


def main():
    args = parse_args()
    project = Path(args.project)
    out = Path(args.out) if args.out else project / "docs" / "creative-brief.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    if not args.body and not args.slug:
        print("error: --slug is required", file=sys.stderr)
        return 1

    if args.body:
        content = render_freeform(args, args.body)
        missing = validate_body_sections(args.body)
        if missing:
            print("warning: creative brief is missing recommended sections:", ", ".join(missing), file=sys.stderr)
    else:
        content = render_structured(args)

    with out.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    print(f"Creative brief written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
