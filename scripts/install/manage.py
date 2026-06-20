#!/usr/bin/env python3
"""Manage a local Project Forge plugin installation."""

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from project_forge.hosts import HostService


def build_service(args):
    home = Path(args.home or Path.home())
    if args.host == "codex":
        codex_home = Path(args.codex_home or os.environ.get("CODEX_HOME", home / ".codex"))
        agents_home = Path(args.agents_home or os.environ.get("AGENTS_HOME", home / ".agents"))
        return HostService.codex(args.source, codex_home, agents_home)
    root = Path(args.marketplace_root or home / ".claude" / "project-forge-marketplace")
    return HostService.claude(args.source, root)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "verify", "update", "uninstall", "restore"])
    parser.add_argument("--host", choices=["codex", "claude"], required=True)
    parser.add_argument("--source", default=str(ROOT))
    parser.add_argument("--home")
    parser.add_argument("--codex-home")
    parser.add_argument("--agents-home")
    parser.add_argument("--marketplace-root")
    parser.add_argument("--cachebuster")
    parser.add_argument("--backup")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    service = build_service(args)
    if args.action == "verify":
        result = service.verify()
    elif args.action == "restore":
        if not args.backup:
            parser.error("restore requires --backup")
        result = service.restore(args.backup, args.dry_run)
    else:
        method = getattr(service, args.action)
        if args.action in {"install", "update"}:
            result = method(args.cachebuster, args.dry_run)
        else:
            result = method(args.dry_run)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.ok or result.status == "not_installed" and args.action == "uninstall" else 1


if __name__ == "__main__":
    raise SystemExit(main())
