#!/usr/bin/env python3
"""Migrate Project Forge artifacts between supported schemas."""

import argparse
import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_forge.migration import migrate_project, rollback_migration


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--from", dest="source", type=int, default=1)
    parser.add_argument("--to", dest="target", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--rollback")
    args = parser.parse_args()
    try:
        if args.rollback:
            rollback_migration(args.project, args.rollback)
            payload = {"status": "rolled-back", "backup": args.rollback}
        else:
            if (args.source, args.target) != (1, 2):
                raise ValueError("only migration 1 -> 2 is supported")
            payload = migrate_project(args.project, args.dry_run)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
