#!/usr/bin/env python3
"""Check structural or executable Superpowers handoff readiness."""

import argparse
import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_forge.readiness import check_readiness


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--only", help="Comma-separated command names")
    parser.add_argument("--include-install", action="store_true")
    parser.add_argument("--include-run", action="store_true")
    parser.add_argument("--allow-legacy-shell", action="store_true")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--continue-on-failure", action="store_true")
    return parser.parse_args()


def print_human(payload):
    print(f"Project Forge Superpowers readiness: {payload['status']} ({payload['score']}%)")
    print(f"Readiness: {payload['readiness_status']}")
    for check in payload["checks"]:
        marker = {"pass": "OK", "warn": "WARN", "fail": "FAIL"}[check["status"]]
        print(f"  [{marker}] {check['id']}: {check['message']}")
    if payload.get("execution"):
        print(f"Verification report: {payload['execution']['report']}")


def main():
    args = parse_args()
    selected = [item.strip() for item in args.only.split(",") if item.strip()] if args.only else None
    try:
        payload = check_readiness(
            args.project,
            args.slug,
            execute=args.execute,
            selected=selected,
            include_install=args.include_install,
            include_run=args.include_run,
            allow_legacy_shell=args.allow_legacy_shell,
            timeout_seconds=args.timeout,
            continue_on_failure=args.continue_on_failure,
            strict=args.strict,
        )
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    payload["project"] = str(Path(args.project)).replace("\\", "/")
    payload["slug"] = args.slug
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_human(payload)
    return 1 if payload["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
