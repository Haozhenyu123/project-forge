"""Typed evaluation results."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class EvalStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NOT_RUN = "not_run"


@dataclass
class CompatibilityResult:
    status: EvalStatus
    host: str
    superpowers_version: str
    reason: Optional[str] = None
    returncode: Optional[int] = None
    timed_out: bool = False
    assertions: Dict[str, bool] = field(default_factory=dict)
    failures: List[str] = field(default_factory=list)
    log_dir: Optional[str] = None
    isolated_home: bool = True
    isolated_project: bool = True
    plan_only: bool = True

    def to_dict(self):
        data = asdict(self)
        data["status"] = self.status.value
        return data

