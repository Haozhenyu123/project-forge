#!/usr/bin/env python3
"""Run deterministic text checks against Project Forge eval responses."""

import argparse
import json
import re
import sys
from pathlib import Path


WORD_RE = re.compile(r"[a-z0-9]+")


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def words(text):
    return WORD_RE.findall(text.lower())


def normalize_phrase(text):
    return " ".join(words(text))


def keyword_tokens(text):
    ignored = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "or",
        "that",
        "the",
        "to",
        "until",
        "use",
        "with",
    }
    return [token for token in words(text) if len(token) > 2 and token not in ignored]


def check_phrase(label, phrase, response_text):
    haystack = normalize_phrase(response_text)
    normalized = normalize_phrase(phrase)
    tokens = keyword_tokens(phrase)
    matched_tokens = [token for token in tokens if token in haystack]
    passed = False
    if normalized and normalized in haystack:
        passed = True
    elif tokens:
        required = max(1, (len(tokens) + 1) // 2)
        passed = len(matched_tokens) >= required
    return {
        "label": label,
        "text": phrase,
        "passed": passed,
        "matched_keywords": matched_tokens,
    }


def iter_checks(scenario):
    for phrase in scenario.get("expected_behaviors", []):
        yield "expected_behavior", phrase
    rubric = scenario.get("rubric", {})
    for section, phrases in rubric.items():
        if isinstance(phrases, list):
            for phrase in phrases:
                yield f"rubric.{section}", phrase


def score_scenario(scenario, response_text):
    checks = [check_phrase(label, phrase, response_text) for label, phrase in iter_checks(scenario)]
    passed = [check for check in checks if check["passed"]]
    score = round(len(passed) / len(checks), 3) if checks else 0.0
    return {
        "id": scenario["id"],
        "title": scenario["title"],
        "score": score,
        "passed_checks": passed,
        "failed_checks": [check for check in checks if not check["passed"]],
        "response_file": f"{scenario['id']}.txt",
    }


def run(scenario_dir, responses_dir):
    scenario_paths = sorted(scenario_dir.glob("*.json"))
    results = []
    for path in scenario_paths:
        scenario = load_json(path)
        response_path = responses_dir / f"{scenario['id']}.txt"
        try:
            response_text = response_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            response_text = ""
        result = score_scenario(scenario, response_text)
        result["response_found"] = response_path.exists()
        results.append(result)
    return {
        "status": "ok",
        "scenario_count": len(results),
        "results": results,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario-dir", required=True, type=Path)
    parser.add_argument("--responses-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    if not args.scenario_dir.is_dir():
        print(f"{args.scenario_dir}: not a directory", file=sys.stderr)
        return 2
    if not args.responses_dir.is_dir():
        print(f"{args.responses_dir}: not a directory", file=sys.stderr)
        return 2

    try:
        payload = run(args.scenario_dir, args.responses_dir)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({"status": "ok", "scenario_count": payload["scenario_count"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
