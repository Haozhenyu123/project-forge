"""Typed evidence records shared by research and decision services."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List


class SourceQuality(str, Enum):
    PRIMARY = "primary"
    REPOSITORY_METADATA = "repository-metadata"
    REGISTRY_METADATA = "registry-metadata"
    SECONDARY = "secondary"
    UNVERIFIED = "unverified"


class Freshness(str, Enum):
    CURRENT = "current"
    AGING = "aging"
    STALE = "stale"
    UNKNOWN = "unknown"


@dataclass
class EvidenceRecord:
    evidence_id: str
    source: str
    title: str
    url: str
    summary: str
    observed_at: str
    canonical_url: str
    fingerprint: str
    source_quality: SourceQuality = SourceQuality.UNVERIFIED
    freshness: Freshness = Freshness.UNKNOWN
    provisional: bool = False
    relevance: str = "Supports project research decision."
    score: int = 1
    attributes: Dict[str, Any] = field(default_factory=dict)
    evidence_for: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["source_quality"] = self.source_quality.value
        data["freshness"] = self.freshness.value
        data.update(self.attributes)
        return data
