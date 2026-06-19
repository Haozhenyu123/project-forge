#!/usr/bin/env python3
"""Write a creative-brief.md from a project goal, slug, and direction inputs."""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path


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
    parser.add_argument("--out", default="", help="Output path (default: docs/creative-brief.md)")
    return parser.parse_args()


def render_brief(args):
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
        "## Assumptions",
        "",
    ]
    if args.audience:
        lines.append(f"- Target user '{args.audience}' is an assumption; validate with user research.")
    if args.platform:
        lines.append(f"- Platform '{args.platform}' is an assumption; confirm deployment target.")
    if args.style:
        lines.append(f"- Interaction style '{args.style}' is an assumption; validate with a prototype.")
    if not any([args.audience, args.platform, args.style]):
        lines.append("- No explicit assumptions recorded; all direction decisions are provisional.")

    lines.extend([
        "",
        "## Risks",
        "",
        "- If the target user or platform is wrong, the MVP may need significant rework.",
        "- Vague goals lead to scope creep; pin down the first useful workflow before expanding.",
        "- Creative direction without user validation is speculation; test assumptions early.",
        "",
        "## Next Steps",
        "",
        "1. Hand this brief to `ai-architect` for evidence-backed stack selection.",
        "2. Run research scripts to gather GitHub and web evidence for the chosen direction.",
        "3. Apply a harness template once the stack is confirmed.",
        "",
    ])
    return "\n".join(lines)


def main():
    args = parse_args()
    project = Path(args.project)
    out = Path(args.out) if args.out else project / "docs" / "creative-brief.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_brief(args))
    print(f"Creative brief written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
