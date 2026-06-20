#!/usr/bin/env python3
"""Search GitHub repositories and write normalized evidence JSONL."""

import argparse
import json
import os
import sys
from pathlib import Path


SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_forge.evidence.providers import GitHubProvider, ProviderResult


def _fixture_result(path, query, limit):
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    items = payload.get("items", []) if isinstance(payload, dict) else payload
    provider = GitHubProvider(transport=lambda request, timeout: {"items": items})
    return provider.search(query, limit)


def write_jsonl(rows, out_path):
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--fixture")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    if args.fixture:
        result = _fixture_result(args.fixture, args.query, args.limit)
    else:
        result = GitHubProvider(token=os.environ.get("GITHUB_TOKEN", "")).search(
            args.query, args.limit
        )
    if args.strict and result.provisional:
        print(f"GitHub search failed: {result.error or 'provider unavailable'}", file=sys.stderr)
        return 1
    write_jsonl(result.rows, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
