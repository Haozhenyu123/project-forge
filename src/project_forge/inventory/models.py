"""Typed inventory records with stable JSON serialization."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class Service:
    """A statically detected runnable or deployable project unit."""

    id: str
    name: str
    path: str
    kind: str
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    entrypoints: List[str] = field(default_factory=list)
    ports: List[int] = field(default_factory=list)
    environment_variables: List[str] = field(default_factory=list)
    databases: List[str] = field(default_factory=list)
    queues: List[str] = field(default_factory=list)
    integrations: List[str] = field(default_factory=list)


@dataclass
class Workspace:
    """A package root declared by a monorepo workspace configuration."""

    path: str
    source: str


@dataclass
class Relationship:
    """A topology edge inferred from static configuration."""

    source: str
    target: str
    kind: str


@dataclass
class ArchitectureInventory:
    """Serializable output of one static scan."""

    schema_version: int = 1
    project_name: str = ""
    project_root: str = "."
    monorepo: bool = False
    workspaces: List[Workspace] = field(default_factory=list)
    services: List[Service] = field(default_factory=list)
    databases: List[str] = field(default_factory=list)
    queues: List[str] = field(default_factory=list)
    integrations: List[str] = field(default_factory=list)
    environment_variables: List[str] = field(default_factory=list)
    docker_files: List[str] = field(default_factory=list)
    compose_files: List[str] = field(default_factory=list)
    ci_files: List[str] = field(default_factory=list)
    deploy_files: List[str] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a deterministic JSON-ready mapping."""

        return asdict(self)
