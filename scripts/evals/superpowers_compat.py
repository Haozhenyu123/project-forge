#!/usr/bin/env python3
"""Run a plan-only Project Forge to Superpowers compatibility check."""

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from project_forge.evals import run_compatibility


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=["codex", "claude"], required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--plugin-root", default=str(ROOT))
    parser.add_argument("--superpowers-dir")
    parser.add_argument("--superpowers-version", default="5.1.3")
    parser.add_argument("--matrix", default=str(ROOT / "compatibility" / "superpowers-matrix.json"))
    parser.add_argument("--log-root", default=str(ROOT / ".project-forge" / "compatibility"))
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--no-credential-check", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    result = run_compatibility(
        host=args.host,
        project=args.project,
        plugin_root=args.plugin_root,
        superpowers_dir=args.superpowers_dir,
        superpowers_version=args.superpowers_version,
        matrix_path=args.matrix,
        log_root=args.log_root,
        timeout_seconds=args.timeout,
        require_credentials=not args.no_credential_check,
    )
    payload = result.to_dict()
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if payload["status"] in {"pass", "not_run"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

