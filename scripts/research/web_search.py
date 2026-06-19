#!/usr/bin/env python3
"""Fetch web-search evidence. Uses DuckDuckGo API by default (no key needed),
or a custom provider via PROJECT_FORGE_WEB_SEARCH_URL env var."""

import argparse
import hashlib
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
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


def observed_at():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def cache_path(query, limit):
    cache_root = os.environ.get("PROJECT_FORGE_CACHE_DIR", "").strip()
    if not cache_root:
        return None
    digest = hashlib.sha256(f"{query}\0{limit}".encode("utf-8")).hexdigest()
    return Path(cache_root) / "web" / f"{digest}.json"


def read_cache(query, limit):
    path = cache_path(query, limit)
    if not path or not path.is_file():
        return None
    ttl = int(os.environ.get("PROJECT_FORGE_CACHE_TTL_SECONDS", "86400"))
    if time.time() - path.stat().st_mtime > ttl:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("rows")
    return rows if isinstance(rows, list) else None


def write_cache(query, limit, rows):
    path = cache_path(query, limit)
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"query": query, "limit": limit, "cached_at": observed_at(), "rows": rows},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def fetch_duckduckgo(query, limit):
    """Search DuckDuckGo Instant Answer API (no API key required)."""
    encoded = urllib.parse.quote(query)
    url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
    ctx = ssl.create_default_context()
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "project-forge-web-search/0.2.3"},
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
            "X-Subscription-Token": brave_key,
            "User-Agent": "project-forge-web-search/0.2.3",
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
        headers={"Accept": "application/json", "User-Agent": "project-forge-web-search/0.2.3"},
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
    row.setdefault("observed_at", observed_at())
    row.setdefault("provisional", False)
    row.setdefault("source_quality", "secondary")
    return row


def main():
    args = parse_args()
    provider = os.environ.get("PROJECT_FORGE_WEB_SEARCH_URL", "").strip()
    cached = read_cache(args.query, args.limit)
    if cached:
        write_jsonl(cached, args.out)
        return 0

    if provider:
        try:
            payload = fetch_provider(provider, args.query, args.limit)
            items = payload.get("items", []) if isinstance(payload, dict) else payload
            rows = [normalize_item(item, args.query) for item in items[:args.limit]]
            if rows:
                write_cache(args.query, args.limit, rows)
                write_jsonl(rows, args.out)
                return 0
        except (urllib.error.URLError, OSError, json.JSONDecodeError, TypeError):
            pass

    # Prefer a full search provider when configured.
    rows = fetch_brave(args.query, args.limit)
    if rows:
        rows = [normalize_item(item, args.query) for item in rows]
        write_cache(args.query, args.limit, rows)
        write_jsonl(rows, args.out)
        return 0

    # DuckDuckGo Instant Answer is a no-key fallback, not a full web index.
    rows = fetch_duckduckgo(args.query, args.limit)
    if rows:
        rows = [normalize_item(item, args.query) for item in rows]
        write_cache(args.query, args.limit, rows)
        write_jsonl(rows, args.out)
        return 0

    # No search provider succeeded - emit manual fallback
    write_jsonl(
        [{
            "source": "host-web-tool",
            "kind": "manual-search-required",
            "query": args.query,
            "summary": "No configured web provider returned current evidence.",
            "observed_at": observed_at(),
            "provisional": True,
            "source_quality": "unverified",
        }],
        args.out,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
