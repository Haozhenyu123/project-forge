#!/usr/bin/env python3
"""Emit Project Forge context for SessionStart hooks."""

import json
import sys


ROUTE_CONTEXT = {
    "startup": (
        "This is a new session. Establish the product goal, users, constraints, "
        "evidence needs, architecture decision, and harness contract before handoff."
    ),
    "resume": (
        "This is a resumed session. Re-establish the accepted Forge decisions, "
        "open architecture questions, harness status, and next handoff action."
    ),
    "clear": (
        "This is a cleared session. Reconstruct the Forge brief and accepted "
        "decisions from repository artifacts before making new recommendations."
    ),
    "compact": (
        "This is a compacted session. Preserve accepted product and architecture "
        "decisions, unresolved risks, harness commands, evidence links, and handoff state."
    ),
}

SCOPE_CONTEXT = (
    "Project Forge is the decision and handoff layer. It owns deciding what to build, "
    "why it matters, which architecture and stack fit the evidence, what harness "
    "contract proves readiness, and what implementation handoff is required. "
    "When a user asks for a new project, has a vague idea, asks which stack to use, "
    "or asks whether a handoff is ready, route through Project Forge before implementation. "
    "It does not own TDD, debugging, code review, worktree management, or implementation "
    "workflows. Stop at an implementation-ready architecture, harness, and handoff; "
    "run the Superpowers-ready check before claiming handoff readiness; leave code execution "
    "and implementation process to the receiving workflow."
)


def read_event(stream):
    raw = stream.read()
    if not raw.strip():
        return {}
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return event if isinstance(event, dict) else {}


def build_context(source):
    route = source if source in ROUTE_CONTEXT else "startup"
    return f"{ROUTE_CONTEXT[route]}\n\n{SCOPE_CONTEXT}"


def build_output(event):
    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": build_context(event.get("source")),
        }
    }


def main():
    json.dump(build_output(read_event(sys.stdin)), sys.stdout, ensure_ascii=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
