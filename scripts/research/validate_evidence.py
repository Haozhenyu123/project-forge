#!/usr/bin/env python3
"""Validate Project Forge normalized evidence JSONL."""

import argparse
import json
import sys
from pathlib import Path


NON_PROVISIONAL_REQUIRED = (
    "source",
    "title",
    "url",
    "summary",
    "observed_at",
    "relevance",
    "provisional",
    "evidence_id",
    "score",
)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", help="Path to evidence.jsonl")
    return parser.parse_args()


def iter_rows(path):
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"line {line_number}: expected JSON object")
            yield line_number, row


def missing_non_provisional_fields(row):
    missing = []
    for field in NON_PROVISIONAL_REQUIRED:
        if field == "provisional":
            if field not in row or row[field] is not False:
                missing.append(field)
        elif field not in row or row[field] in (None, ""):
            missing.append(field)
    return missing


def main():
    args = parse_args()
    path = Path(args.evidence)
    row_count = 0
    provisional_count = 0

    try:
        for line_number, row in iter_rows(path):
            row_count += 1
            if bool(row.get("provisional")):
                provisional_count += 1
                continue
            missing = missing_non_provisional_fields(row)
            if missing:
                fields = ", ".join(missing)
                raise ValueError(f"line {line_number}: missing required field(s): {fields}")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "status": "ok",
                "row_count": row_count,
                "provisional_count": provisional_count,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
