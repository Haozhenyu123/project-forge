"""Template lifecycle management: deprecation, migration, and end-of-life tracking.

Each template manifest may carry lifecycle metadata to signal when a stack is:
- active: fully supported
- deprecated: still works but migration recommended
- eol: end-of-life, no further updates
"""
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional


LIFECYCLE_STATUSES = ("active", "deprecated", "eol")


@dataclass
class LifecycleRecord:
    template_id: str
    status: str  # active, deprecated, eol
    since: str  # date when this status became effective
    migration_target: str = ""  # recommended replacement template
    migration_guide: str = ""  # path to migration doc
    reason: str = ""
    sunset_date: str = ""  # after this date, template is removed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "status": self.status,
            "since": self.since,
            "migration_target": self.migration_target,
            "migration_guide": self.migration_guide,
            "reason": self.reason,
            "sunset_date": self.sunset_date,
        }

    @classmethod
    def from_dict(cls, value):
        return cls(
            template_id=str(value.get("template_id", "")),
            status=str(value.get("status", "active")),
            since=str(value.get("since", "")),
            migration_target=str(value.get("migration_target", "")),
            migration_guide=str(value.get("migration_guide", "")),
            reason=str(value.get("reason", "")),
            sunset_date=str(value.get("sunset_date", "")),
        )


def load_lifecycle_registry(repo_root: Optional[Path] = None) -> Dict[str, LifecycleRecord]:
    """Load the template lifecycle registry from the catalog."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[3]
    path = repo_root / "catalog" / "lifecycle.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    records: Dict[str, LifecycleRecord] = {}
    for item in data.get("templates", []):
        rec = LifecycleRecord.from_dict(item)
        records[rec.template_id] = rec
    return records


def check_deprecated(template_id: str, registry: Optional[Dict[str, LifecycleRecord]] = None) -> Optional[LifecycleRecord]:
    """Check if a template is deprecated and return its lifecycle record if so."""
    registry = registry or load_lifecycle_registry()
    rec = registry.get(template_id)
    if rec and rec.status in ("deprecated", "eol"):
        return rec
    return None


def generate_migration_notice(deprecated_template: str, target: str, guide: str = "") -> str:
    """Generate a human-readable migration notice."""
    lines = [
        f"## Migration Notice",
        "",
        f"Template `{deprecated_template}` is deprecated.",
    ]
    if target:
        lines.append(f"Recommended replacement: `{target}`.")
    if guide:
        lines.append(f"Migration guide: [{guide}]({guide})")
    lines.append("")
    lines.append("To migrate: `project-forge migrate --from {deprecated_template} --to {target} [PROJECT_DIR]`")
    return "\n".join(lines)
