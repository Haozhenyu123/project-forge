#!/usr/bin/env python3
"""Manage Project Forge backups, run history, and local project state."""

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


STATE_DIR = Path(".project-forge")
BACKUPS_DIR = STATE_DIR / "backups"
HISTORY_DIR = STATE_DIR / "history"
STATE_FILE = STATE_DIR / "state.json"


def timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def relative_to_project(project, path):
    return path.resolve().relative_to(project.resolve())


def backup_files(project, paths, label="forge"):
    project = Path(project)
    existing = [Path(path) for path in paths if Path(path).exists()]
    if not existing:
        return None

    backup_id = f"{timestamp()}-{label}"
    backup_root = project / BACKUPS_DIR / backup_id
    manifest = {"id": backup_id, "created_at": timestamp(), "files": []}

    for source in existing:
        relative = relative_to_project(project, source)
        destination = backup_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        manifest["files"].append(str(relative).replace("\\", "/"))

    backup_root.mkdir(parents=True, exist_ok=True)
    (backup_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return backup_root


def list_backups(project):
    root = Path(project) / BACKUPS_DIR
    if not root.is_dir():
        return []
    backups = []
    for child in sorted(root.iterdir(), reverse=True):
        manifest = child / "manifest.json"
        if not manifest.is_file():
            continue
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        payload["path"] = str(child)
        backups.append(payload)
    return backups


def restore_backup(project, backup_id, force=False):
    project = Path(project)
    backup_root = project / BACKUPS_DIR / backup_id
    manifest_path = backup_root / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Unknown backup: {backup_id}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    targets = [project / Path(relative) for relative in manifest.get("files", [])]
    conflicts = [target for target in targets if target.exists()]
    if conflicts and not force:
        joined = ", ".join(str(path) for path in conflicts)
        raise FileExistsError(
            f"Refusing to overwrite current file(s): {joined}. Re-run with --force."
        )

    for relative in manifest.get("files", []):
        source = backup_root / Path(relative)
        destination = project / Path(relative)
        if not source.is_file():
            raise FileNotFoundError(f"Backup file is missing: {source}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return manifest


def record_run(project, payload):
    project = Path(project)
    run_id = f"{timestamp()}-{payload.get('slug', 'run')}"
    history_root = project / HISTORY_DIR
    history_root.mkdir(parents=True, exist_ok=True)
    history_path = history_root / f"{run_id}.json"
    record = dict(payload)
    record["id"] = run_id
    record["recorded_at"] = timestamp()
    history_path.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    state_path = project / STATE_FILE
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "last_run": run_id,
                "last_slug": payload.get("slug"),
                "last_stack": payload.get("stack"),
                "last_backup": payload.get("backup"),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return history_path


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List available backups")
    list_parser.add_argument("--project", default=".")

    restore_parser = subparsers.add_parser("restore", help="Restore a backup")
    restore_parser.add_argument("backup_id")
    restore_parser.add_argument("--project", default=".")
    restore_parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        if args.command == "list":
            print(json.dumps({"backups": list_backups(args.project)}, indent=2))
        elif args.command == "restore":
            payload = restore_backup(args.project, args.backup_id, args.force)
            print(json.dumps({"status": "ok", "restored": payload["id"]}))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
