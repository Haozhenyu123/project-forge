#!/usr/bin/env python3
"""Export Markdown and Schema v2 Superpowers handoff packets."""

import argparse
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_forge.handoff import export_handoff


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out")
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        export_handoff(args.project, args.slug, args.out, args.json_out)
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
