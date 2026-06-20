"""Project Forge artifact migrations."""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .contract import dump_contract, load_contract


def migration_preview(project):
    project = Path(project)
    contract_path = project / "project-forge.yaml"
    if not contract_path.is_file():
        raise FileNotFoundError(f"missing contract: {contract_path}")
    contract = load_contract(contract_path, slug=project.name)
    return {
        "status": "dry-run",
        "from": contract.migrated_from or contract.schema_version,
        "to": 2,
        "contract": str(contract_path),
        "would_backup": str(project / ".project-forge" / "migrations"),
    }


def migrate_project(project, dry_run=False):
    project = Path(project)
    if dry_run:
        return migration_preview(project)
    contract_path = project / "project-forge.yaml"
    original = contract_path.read_text(encoding="utf-8-sig")
    contract = load_contract(contract_path, slug=project.name)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = project / ".project-forge" / "migrations" / run_id / "project-forge.yaml"
    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_text(original, encoding="utf-8")
    with contract_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(dump_contract(contract))
    result = {
        "status": "migrated",
        "from": contract.migrated_from or 2,
        "to": 2,
        "backup": str(backup),
        "contract": str(contract_path),
    }
    (backup.parent / "migration.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def rollback_migration(project, backup):
    project = Path(project).resolve()
    source = Path(backup).resolve()
    allowed = project / ".project-forge" / "migrations"
    try:
        source.relative_to(allowed.resolve())
    except ValueError as exc:
        raise ValueError("migration backup is outside the project") from exc
    shutil.copy2(source, project / "project-forge.yaml")
