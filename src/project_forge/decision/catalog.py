"""Load and validate the external, versioned stack catalog."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class CatalogSource:
    evidence_id: str
    url: str
    title: str
    dimensions: List[str]
    applicability: str


@dataclass
class StackDefinition:
    id: str
    name: str
    kind: str
    aliases: List[str]
    capabilities: Set[str]
    harness: Dict[str, Any]
    baselines: Dict[str, int]
    sources: List[CatalogSource] = field(default_factory=list)

    def source_ids(self, dimension: str) -> List[str]:
        return [source.evidence_id for source in self.sources if dimension in source.dimensions]


@dataclass
class StackCatalog:
    schema_version: int
    catalog_version: str
    observed_at: str
    default_weights: Dict[str, float]
    stacks: List[StackDefinition]


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_catalog_path() -> Path:
    return repository_root() / "catalog" / "stacks.v1.json"


def load_catalog(path: Optional[Path] = None) -> StackCatalog:
    catalog_path = path or default_catalog_path()
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported stack catalog schema")
    stacks = []
    seen = set()
    for value in payload.get("stacks", []):
        stack_id = str(value["id"])
        if stack_id in seen:
            raise ValueError(f"duplicate stack catalog id: {stack_id}")
        seen.add(stack_id)
        sources = [CatalogSource(**source) for source in value.get("sources", [])]
        if not sources:
            raise ValueError(f"stack {stack_id} has no baseline sources")
        stacks.append(
            StackDefinition(
                id=stack_id,
                name=str(value["name"]),
                kind=str(value.get("kind", "template")),
                aliases=[str(item).lower() for item in value.get("aliases", [])],
                capabilities={str(item).lower() for item in value.get("capabilities", [])},
                harness=dict(value.get("harness", {})),
                baselines={key: int(score) for key, score in value.get("baselines", {}).items()},
                sources=sources,
            )
        )
    template_ids = {stack.harness.get("primary") for stack in stacks if stack.kind == "template"}
    required = {"chrome-extension", "cli", "electron", "fastapi", "generic", "nextjs", "node-ts", "python"}
    if template_ids != required:
        raise ValueError(f"catalog template coverage mismatch: {sorted(template_ids ^ required)}")
    return StackCatalog(
        schema_version=1,
        catalog_version=str(payload["catalog_version"]),
        observed_at=str(payload["observed_at"]),
        default_weights={key: float(value) for key, value in payload["default_weights"].items()},
        stacks=stacks,
    )
