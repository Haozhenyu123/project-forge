#!/usr/bin/env python3
"""Merge raw research evidence into normalized, de-duplicated JSONL."""

import argparse
import json
import sys
from pathlib import Path


SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_forge.evidence.normalize import normalize_records


def records_from_json(path):
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return payload["items"]
    return [payload] if isinstance(payload, dict) else []


def records_from_jsonl(path):
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def iter_records(input_path):
    path = Path(input_path)
    paths = sorted(path.iterdir()) if path.is_dir() else [path]
    for item in paths:
        if not item.is_file() or item.suffix.lower() not in {".json", ".jsonl"}:
            continue
        loader = records_from_jsonl if item.suffix.lower() == ".jsonl" else records_from_json
        for row in loader(item):
            if isinstance(row, dict):
                yield row


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--as-of")
    args = parser.parse_args(argv)
    rows = normalize_records(iter_records(args.input), as_of=args.as_of)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
