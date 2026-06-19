#!/usr/bin/env python3
"""Merge raw research evidence into scored, de-duplicated JSONL."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    return parser.parse_args()


def records_from_json(path):
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return payload["items"]
    if isinstance(payload, dict):
        return [payload]
    return []


def records_from_jsonl(path):
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def iter_records(input_dir):
    paths = sorted(
        [
            path
            for path in Path(input_dir).iterdir()
            if path.is_file() and path.suffix.lower() in (".json", ".jsonl")
        ],
        key=lambda path: path.name,
    )
    for path in paths:
        loader = records_from_jsonl if path.suffix.lower() == ".jsonl" else records_from_json
        for row in loader(path):
            if isinstance(row, dict):
                yield row


def score(row):
    stars = row.get("stars")
    if stars is None:
        stars = row.get("stargazers_count")
    try:
        return int(stars)
    except (TypeError, ValueError):
        return 1


def is_provisional(row):
    if "provisional" in row:
        return bool(row["provisional"])
    return row.get("source") == "host-web-tool" or row.get("kind") == "manual-search-required"


def relevance(row):
    value = row.get("relevance") or row.get("summary") or row.get("description")
    if value:
        return str(value)
    if row.get("query"):
        return f"Manual research required for query: {row['query']}"
    return "Supports project research decision."


def main():
    args = parse_args()
    observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    seen_urls = set()
    merged = []

    for index, row in enumerate(iter_records(args.input), start=1):
        url = row.get("url") or row.get("html_url") or row.get("link")
        if url:
            if url in seen_urls:
                continue
            seen_urls.add(url)
        normalized = dict(row)
        title = normalized.get("title") or normalized.get("name") or normalized.get("full_name")
        summary = normalized.get("summary") or normalized.get("description") or title
        normalized["evidence_id"] = str(normalized.get("evidence_id") or f"E{index}")
        if url and "url" not in normalized:
            normalized["url"] = url
        if title and "title" not in normalized:
            normalized["title"] = str(title)
        if summary and "summary" not in normalized:
            normalized["summary"] = str(summary)
        normalized["observed_at"] = str(normalized.get("observed_at") or observed_at)
        normalized["score"] = score(normalized)
        normalized["relevance"] = relevance(normalized)
        normalized["provisional"] = is_provisional(normalized)
        merged.append(normalized)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as handle:
        for row in merged:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
