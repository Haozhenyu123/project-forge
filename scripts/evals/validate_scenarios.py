#!/usr/bin/env python3
"""Validate Project Forge evaluation scenario JSON files."""

import json
import sys
from pathlib import Path


REQUIRED_FIELDS = {
    "id": str,
    "title": str,
    "category": str,
    "prompt": str,
    "expected_behaviors": list,
}


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_scenario(path):
    data = load_json(path)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: scenario must be a JSON object")

    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in data:
            raise ValueError(f"{path}: missing required field '{field}'")
        if not isinstance(data[field], expected_type):
            raise ValueError(f"{path}: field '{field}' must be {expected_type.__name__}")

    if not data["id"].strip():
        raise ValueError(f"{path}: id must not be empty")
    if path.stem != data["id"]:
        raise ValueError(f"{path}: file name must match id")
    if not data["expected_behaviors"]:
        raise ValueError(f"{path}: expected_behaviors must not be empty")
    if not all(isinstance(item, str) and item.strip() for item in data["expected_behaviors"]):
        raise ValueError(f"{path}: expected_behaviors entries must be non-empty strings")

    return data


def main(argv):
    if len(argv) != 2:
        print("usage: validate_scenarios.py <scenario_dir>", file=sys.stderr)
        return 2

    scenario_dir = Path(argv[1])
    if not scenario_dir.is_dir():
        print(f"{scenario_dir}: not a directory", file=sys.stderr)
        return 2

    scenario_paths = sorted(scenario_dir.glob("*.json"))
    scenarios = []
    try:
        for path in scenario_paths:
            scenarios.append(validate_scenario(path))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    ids = [scenario["id"] for scenario in scenarios]
    if len(ids) != len(set(ids)):
        print("duplicate scenario id", file=sys.stderr)
        return 1

    payload = {
        "status": "ok",
        "scenario_count": len(scenarios),
        "scenario_ids": ids,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
