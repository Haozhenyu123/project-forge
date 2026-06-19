#!/usr/bin/env python3
"""Fetch web-search evidence. Uses DuckDuckGo API by default (no key needed),
or a custom provider via PROJECT_FORGE_WEB_SEARCH_URL env var."""

import argparse
import json
import os
import ssl
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


def fetch_duckduckgo(query, limit):
    """Search DuckDuckGo Instant Answer API (no API key required)."""
    encoded = urllib.parse.quote(query)
    url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
    ctx = ssl.create_default_context()
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "project-forge-web-search/0.2.2"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15, context=ctx) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return None

    items = []
    if payload.get("AbstractText"):
        items.append({
            "source": "duckduckgo",
            "title": payload.get("Heading") or query,
            "url": payload.get("AbstractURL") or f"https://duckduckgo.com/?q={encoded}",
            "summary": payload["AbstractText"],
        })
    if payload.get("RelatedTopics"):
        for topic in payload["RelatedTopics"][:limit]:
            if isinstance(topic, dict) and topic.get("Text"):
                items.append({
                    "source": "duckduckgo",
                    "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " ") or query,
                    "url": topic.get("FirstURL") or f"https://duckduckgo.com/?q={encoded}",
                    "summary": topic["Text"],
                })
    return items[:limit] if items else None



def fetch_brave(query, limit):
    """Search Brave Search API (requires BRAVE_API_KEY env var)."""
    brave_key = os.environ.get("BRAVE_API_KEY", "").strip()
    if not brave_key:
        return None
    encoded = urllib.parse.quote(query)
    url = f"https://api.search.brave.com/res/v1/web/search?q={encoded}&count={limit}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": brave_key,
            "User-Agent": "project-forge-web-search/0.2.2",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return None
    items = []
    for result in (payload.get("web", {}).get("results", []) or [])[:limit]:
        items.append({
            "source": "brave",
            "title": result.get("title", query),
            "url": result.get("url", ""),
            "summary": result.get("description", ""),
        })
    return items if items else None


def fetch_provider(url, query, limit):
    separator = "&" if urllib.parse.urlparse(url).query else "?"
    endpoint = url + separator + urllib.parse.urlencode({"q": query, "limit": limit})
    request = urllib.request.Request(
        endpoint,
        headers={"Accept": "application/json", "User-Agent": "project-forge-web-search/0.2.2"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_item(item, query):
    row = dict(item)
    row.setdefault("source", "web")
    row.setdefault("query", query)
    if "summary" not in row:
        row["summary"] = row.get("snippet") or row.get("description") or row.get("AbstractText") or row.get("Text") or ""
    if "url" not in row and "link" in row:
        row["url"] = row["link"]
    return row


def main():
    args = parse_args()
    provider = os.environ.get("PROJECT_FORGE_WEB_SEARCH_URL", "").strip()

    if provider:
        payload = fetch_provider(provider, args.query, args.limit)
        items = payload.get("items", []) if isinstance(payload, dict) else payload
        rows = [normalize_item(item, args.query) for item in items[:args.limit]]
        write_jsonl(rows, args.out)
        return 0

    # Try DuckDuckGo first (no key needed)
    rows = fetch_duckduckgo(args.query, args.limit)
    if rows:
        write_jsonl(rows, args.out)
        return 0

    # Try Brave Search as fallback (needs BRAVE_API_KEY)
    rows = fetch_brave(args.query, args.limit)
    if rows:
        write_jsonl(rows, args.out)
        return 0

    # No search provider succeeded - emit manual fallback
    write_jsonl(
        [{
            "source": "host-web-tool",
            "kind": "manual-search-required",
            "query": args.query,
        }],
        args.out,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
