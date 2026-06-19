#!/usr/bin/env python3
"""Fetch web-search evidence from a host-configured provider."""

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
    return parser.parse_args()


def write_jsonl(rows, out_path):
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def fetch_provider(url, query, limit):
    separator = "&" if urllib.parse.urlparse(url).query else "?"
    endpoint = url + separator + urllib.parse.urlencode({"q": query, "limit": limit})
    request = urllib.request.Request(
        endpoint,
        headers={"Accept": "application/json", "User-Agent": "project-forge-web-search"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_item(item, query):
    row = dict(item)
    row.setdefault("source", "web")
    row.setdefault("query", query)
    if "summary" not in row:
        row["summary"] = row.get("snippet") or row.get("description") or ""
    if "url" not in row and "link" in row:
        row["url"] = row["link"]
    return row


def main():
    args = parse_args()
    provider = os.environ.get("PROJECT_FORGE_WEB_SEARCH_URL", "").strip()
    if not provider:
        write_jsonl(
            [
                {
                    "source": "host-web-tool",
                    "kind": "manual-search-required",
                    "query": args.query,
                }
            ],
            args.out,
        )
        return 0

    payload = fetch_provider(provider, args.query, args.limit)
    items = payload.get("items", []) if isinstance(payload, dict) else payload
    rows = [normalize_item(item, args.query) for item in items[: args.limit]]
    write_jsonl(rows, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
