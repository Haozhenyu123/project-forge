#!/usr/bin/env python3
"""Compose primary and secondary harnesses into Schema v2."""

import argparse
import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_forge.contract import write_contract
from project_forge.harness import compose_contract


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--primary", required=True)
    parser.add_argument("--secondary", action="append", default=[])
    parser.add_argument("--out")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    project = Path(args.project)
    try:
        contract = compose_contract(
            args.slug,
            args.goal,
            args.primary,
            args.secondary,
            project_root=project if project.exists() else None,
        )
        payload = contract.to_dict()
        if args.dry_run:
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        out = Path(args.out or project / "project-forge.yaml")
        write_contract(out, contract)
        print(json.dumps({"status": "ok", "contract": str(out), "stacks": len(contract.all_stacks())}))
        return 0
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
