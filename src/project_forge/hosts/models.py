"""Typed host installation results."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class Host(str, Enum):
    CODEX = "codex"
    CLAUDE = "claude"


class HostOperation(str, Enum):
    INSTALL = "install"
    VERIFY = "verify"
    UPDATE = "update"
    UNINSTALL = "uninstall"
    RESTORE = "restore"


@dataclass(frozen=True)
class PlannedChange:
    action: str
    path: str
    detail: str = ""


@dataclass
class HostResult:
    host: Host
    operation: HostOperation
    status: str
    plugin_dir: Path
    marketplace_file: Optional[Path] = None
    version: Optional[str] = None
    backup_dir: Optional[Path] = None
    dry_run: bool = False
    changes: List[PlannedChange] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self):
        return not self.errors and self.status not in {"invalid", "not_installed", "failed"}

    def to_dict(self):
        data = asdict(self)
        data["host"] = self.host.value
        data["operation"] = self.operation.value
        for key in ("plugin_dir", "marketplace_file", "backup_dir"):
            value = data[key]
            data[key] = str(value) if value is not None else None
        return data

