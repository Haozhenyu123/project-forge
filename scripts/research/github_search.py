#!/usr/bin/env python3
"""Search GitHub repositories and write normalized evidence JSONL."""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--fixture")
    return parser.parse_args()


def load_payload(args):
    if args.fixture:
        with open(args.fixture, "r", encoding="utf-8") as handle:
            return json.load(handle)

    params = urllib.parse.urlencode(
        {
            "q": args.query,
            "per_page": max(1, min(args.limit, 100)),
        }
    )
    request = urllib.request.Request(
        "https://api.github.com/search/repositories?" + params,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "project-forge-github-search",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", "Bearer " + token)

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_repo(repo, query):
    return {
        "source": "github",
        "title": repo.get("full_name") or repo.get("name") or "",
        "full_name": repo.get("full_name") or "",
        "url": repo.get("html_url") or repo.get("url") or "",
        "summary": repo.get("description") or "",
        "description": repo.get("description") or "",
        "stars": repo.get("stargazers_count", repo.get("stars", 0)) or 0,
        "forks": repo.get("forks_count", repo.get("forks", 0)) or 0,
        "language": repo.get("language"),
        "topics": repo.get("topics") or [],
        "updated_at": repo.get("updated_at"),
        "query": query,
    }


def write_jsonl(rows, out_path):
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def main():
    args = parse_args()
    payload = load_payload(args)
    items = payload.get("items", []) if isinstance(payload, dict) else payload
    rows = [normalize_repo(repo, args.query) for repo in items[: args.limit]]
    write_jsonl(rows, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
