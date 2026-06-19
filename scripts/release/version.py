#!/usr/bin/env python3
"""Audit and synchronize Project Forge versions."""

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


@dataclass(eq=True)
class Mismatch:
    path: str
    actual: str
    expected: str


@dataclass(eq=True)
class AuditResult:
    version: str
    mismatches: list


def load_config(root):
    return json.loads((root / ".version-bump.json").read_text(encoding="utf-8"))


def get_field(data, field):
    current = data
    for part in field.split("."):
        current = current[int(part)] if part.isdigit() else current[part]
    return current


def set_field(data, field, value):
    current = data
    parts = field.split(".")
    for part in parts[:-1]:
        current = current[int(part)] if part.isdigit() else current[part]
    last = parts[-1]
    if last.isdigit():
        current[int(last)] = value
    else:
        current[last] = value


def source_version(root, config):
    source = config["source"]
    data = json.loads((root / source["path"]).read_text(encoding="utf-8"))
    return get_field(data, source["field"])


def target_version(root, target):
    path = root / target["path"]
    if target.get("type") == "regex":
        text = path.read_text(encoding="utf-8")
        match = re.search(target["pattern"], text, re.MULTILINE)
        return match.group("version") if match else None
    data = json.loads(path.read_text(encoding="utf-8"))
    return get_field(data, target["field"])


def write_target(root, target, version):
    path = root / target["path"]
    if target.get("type") == "regex":
        text = path.read_text(encoding="utf-8")
        text = re.sub(
            target["pattern"],
            lambda match: match.group(0).replace(match.group("version"), version),
            text,
            flags=re.MULTILINE,
        )
        path.write_text(text, encoding="utf-8")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    set_field(data, target["field"], version)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def audit_versions(root):
    root = Path(root)
    config = load_config(root)
    version = source_version(root, config)
    mismatches = []
    for target in config.get("targets", []):
        actual = target_version(root, target)
        if actual != version:
            mismatches.append(Mismatch(target["path"], actual, version))
    return AuditResult(version=version, mismatches=mismatches)


def sync_versions(root):
    root = Path(root)
    config = load_config(root)
    version = source_version(root, config)
    changed = []
    for target in config.get("targets", []):
        if target_version(root, target) != version:
            write_target(root, target, version)
            changed.append(target["path"])
    return changed


def bump_version(root, version):
    if not SEMVER_RE.match(version):
        raise ValueError("Expected semantic version")
    root = Path(root)
    config = load_config(root)
    source = config["source"]
    source_path = root / source["path"]
    data = json.loads(source_path.read_text(encoding="utf-8"))
    set_field(data, source["field"], version)
    source_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return [source["path"], *sync_versions(root)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["audit", "sync", "bump"])
    parser.add_argument("version", nargs="?")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    if args.command == "audit":
        result = audit_versions(args.root)
        print(json.dumps({"version": result.version, "mismatches": [m.__dict__ for m in result.mismatches]}))
        return 1 if result.mismatches else 0
    if args.command == "sync":
        print(json.dumps({"changed": sync_versions(args.root)}))
        return 0
    print(json.dumps({"changed": bump_version(args.root, args.version)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
