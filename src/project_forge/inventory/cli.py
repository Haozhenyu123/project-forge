"""Command-line adapter for static project inspection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from .render import write_inventory
from .scanner import scan_project


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect a project architecture without executing project code."
    )
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument(
        "--out-dir",
        help="Artifact directory (default: PROJECT/docs/architecture)",
    )
    parser.add_argument("--json", action="store_true", help="Also print inventory JSON")
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Inspect and print without creating inventory artifacts",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    project = Path(args.project).resolve()
    try:
        inventory = scan_project(project)
        paths = ()
        if not args.no_write:
            output = Path(args.out_dir).resolve() if args.out_dir else project / "docs" / "architecture"
            paths = write_inventory(inventory, output)
        if args.json:
            print(json.dumps(inventory.to_dict(), indent=2, sort_keys=True))
        elif paths:
            print("\n".join(str(path) for path in paths))
        return 0
    except (OSError, ValueError) as exc:
        print(f"project-forge inspect: {exc}", file=sys.stderr)
        return 2
