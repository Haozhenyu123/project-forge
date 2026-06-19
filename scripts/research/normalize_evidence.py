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


def main():
    args = parse_args()
    observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    seen_urls = set()
    merged = []

    for row in iter_records(args.input):
        url = row.get("url") or row.get("html_url") or row.get("link")
        if url:
            if url in seen_urls:
                continue
            seen_urls.add(url)
        normalized = dict(row)
        if url and "url" not in normalized:
            normalized["url"] = url
        normalized["observed_at"] = observed_at
        normalized["score"] = score(normalized)
        merged.append(normalized)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as handle:
        for row in merged:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
