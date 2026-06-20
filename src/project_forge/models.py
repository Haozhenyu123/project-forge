"""Canonical data models for Project Forge Schema v2 and beyond."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


COMMAND_ORDER = ("install", "test", "lint", "typecheck", "build", "run", "smoke")


class ReadinessStatus(str, Enum):
    STRUCTURALLY_READY = "structurally_ready"
    VERIFIED = "verified"
    PARTIAL = "partial"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class CommandSpec:
    argv: List[str] = field(default_factory=list)
    cwd: str = "."
    mutates: bool = False
    timeout_seconds: int = 300
    legacy_shell: str = ""

    def validate(self):
        if not self.argv and not self.legacy_shell:
            raise ValueError("CommandSpec requires argv or legacy_shell")
        if self.legacy_shell and not self.legacy_shell.strip():
            raise ValueError("legacy_shell must not be whitespace-only")

    def display(self):
        return " ".join(self.argv) or self.legacy_shell

    @classmethod
    def from_dict(cls, value):
        if isinstance(value, dict):
            return cls(
                argv=[str(a) for a in value.get("argv", [])],
                cwd=str(value.get("cwd", ".")),
                mutates=bool(value.get("mutates", False)),
                timeout_seconds=int(value.get("timeout_seconds", 300)),
                legacy_shell=str(value.get("legacy_shell", "")),
            )
        return cls(legacy_shell=str(value))


@dataclass
class StackContract:
    id: str = ""
    template: str = ""
    root: str = "."
    commands: Dict[str, CommandSpec] = field(default_factory=dict)
    environment: List[str] = field(default_factory=list)
    services: List["ServiceContract"] = field(default_factory=list)

    @classmethod
    def from_dict(cls, value):
        return cls(
            id=str(value.get("id", "")),
            template=str(value.get("template", "")),
            root=str(value.get("root", ".")),
            commands={k: CommandSpec.from_dict(v) for k, v in value.get("commands", {}).items()},
            environment=[str(e) for e in value.get("environment", [])],
            services=[ServiceContract.from_dict(s) for s in value.get("services", [])],
        )


@dataclass
class ServiceContract:
    id: str = ""
    name: str = ""
    kind: str = "service"
    image: str = ""
    port: int = 0
    required_by: List[str] = field(default_factory=list)
    healthcheck: Optional[CommandSpec] = None

    @classmethod
    def from_dict(cls, value):
        return cls(
            id=str(value.get("id", value.get("name", ""))),
            name=str(value.get("name", value.get("id", ""))),
            kind=str(value.get("kind", "service")),
            image=str(value.get("image", "")),
            port=int(value.get("port", 0)),
            required_by=[str(r) for r in value.get("required_by", [])],
            healthcheck=CommandSpec.from_dict(value["healthcheck"]) if value.get("healthcheck") else None,
        )


@dataclass
class ProjectMeta:
    slug: str = ""
    goal: str = ""
    decision_status: str = "accepted"
    harness_status: str = "configured"
    constraints: List[str] = field(default_factory=list)
    migrated_from: Optional[int] = None


@dataclass
class RiskItem:
    """A registered risk associated with an architecture decision."""
    id: str
    category: str  # security, maintenance, performance, deployment, complexity
    description: str
    likelihood: str  # low, medium, high
    impact: str  # low, medium, high
    mitigation: str
    signal_trigger: str = ""  # what evidence change would escalate this risk

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "description": self.description,
            "likelihood": self.likelihood,
            "impact": self.impact,
            "mitigation": self.mitigation,
            "signal_trigger": self.signal_trigger,
        }

    @classmethod
    def from_dict(cls, value):
        return cls(
            id=str(value.get("id", "")),
            category=str(value.get("category", "")),
            description=str(value.get("description", "")),
            likelihood=str(value.get("likelihood", "medium")),
            impact=str(value.get("impact", "medium")),
            mitigation=str(value.get("mitigation", "")),
            signal_trigger=str(value.get("signal_trigger", "")),
        )


@dataclass
class EffortEstimate:
    """Heuristic effort estimate for the chosen architecture."""
    development_days: int = 0
    infrastructure_cost_tier: str = "low"  # low, medium, high
    team_size_recommendation: str = "1-2 developers"
    complexity_drivers: List[str] = field(default_factory=list)
    confidence: str = "low"  # low, medium, high

    def to_dict(self) -> Dict[str, Any]:
        return {
            "development_days": self.development_days,
            "infrastructure_cost_tier": self.infrastructure_cost_tier,
            "team_size_recommendation": self.team_size_recommendation,
            "complexity_drivers": self.complexity_drivers,
            "confidence": self.confidence,
        }


@dataclass
class DecisionPattern:
    """Reusable decision pattern extracted from project history."""
    id: str
    name: str
    trigger_conditions: List[str]  # what project characteristics trigger this pattern
    recommended_stack: str
    confidence: str
    usage_count: int = 1
    last_seen: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "trigger_conditions": self.trigger_conditions,
            "recommended_stack": self.recommended_stack,
            "confidence": self.confidence,
            "usage_count": self.usage_count,
            "last_seen": self.last_seen,
        }


@dataclass
class ProjectContract:
    schema_version: int = 2
    project: ProjectMeta = field(default_factory=ProjectMeta)
    primary: StackContract = field(default_factory=StackContract)
    secondary: List[StackContract] = field(default_factory=list)
    services: List[ServiceContract] = field(default_factory=list)
    verification_report: str = ""
    risks: List[RiskItem] = field(default_factory=list)
    effort_estimate: Optional[EffortEstimate] = None
    commands: Dict[str, CommandSpec] = field(default_factory=dict)
    migrated_from: Optional[int] = None

    def all_stacks(self):
        return [self.primary, *self.secondary]

    def validate(self):
        errors = []
        for stack in self.all_stacks():
            missing = [name for name in COMMAND_ORDER if name not in stack.commands]
            if missing:
                errors.append(f"Stack {stack.id}: missing commands: {missing}")
        if not self.project.slug:
            errors.append("Project slug is required")
        return errors

    def to_dict(self):
        result: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "project": {
                "slug": self.project.slug,
                "goal": self.project.goal,
                "decision_status": self.project.decision_status,
                "harness_status": self.project.harness_status,
                "constraints": self.project.constraints,
            },
            "stacks": {
                "primary": self._serialize_stack(self.primary),
                "secondary": [self._serialize_stack(s) for s in self.secondary],
            },
            "services": [service_to_dict(s) for s in self.services],
            "verification": {"latest_report": self.verification_report} if self.verification_report else {},
            "risks": [r.to_dict() for r in self.risks],
            "effort_estimate": self.effort_estimate.to_dict() if self.effort_estimate else None,
            # Backward compat
            "commands": {k: command_to_dict(v) for k, v in self.commands.items()} if self.commands else {},
        }
        if self.commands:
            result["commands"] = {k: command_to_dict(v) for k, v in self.commands.items()}
        return result

    @staticmethod
    def _serialize_stack(stack):
        return {
            "id": stack.id,
            "template": stack.template,
            "root": stack.root,
            "commands": {k: command_to_dict(v) for k, v in stack.commands.items()},
            "environment": stack.environment,
            "services": [service_to_dict(s) for s in stack.services],
        }


def command_to_dict(command):
    if command.legacy_shell:
        return command.legacy_shell
    return {"argv": command.argv, "cwd": command.cwd, "mutates": command.mutates, "timeout_seconds": command.timeout_seconds}


def stack_to_dict(stack):
    return {
        "id": stack.id,
        "template": stack.template,
        "root": stack.root,
        "commands": {k: command_to_dict(v) for k, v in stack.commands.items()},
    }


def service_to_dict(service):
    return {"id": service.id, "name": service.name, "kind": service.kind, "image": service.image, "port": service.port}
