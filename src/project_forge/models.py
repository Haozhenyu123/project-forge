"""Typed domain models for Project Forge contracts."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Dict, List, Optional


COMMAND_ORDER = ("install", "test", "lint", "typecheck", "build", "run", "smoke")


class ReadinessStatus(str, Enum):
    STRUCTURALLY_READY = "structurally_ready"
    VERIFIED = "verified"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class CommandSpec:
    argv: List[str] = field(default_factory=list)
    cwd: str = "."
    timeout_seconds: int = 300
    mutates: bool = False
    legacy_shell: Optional[str] = None

    def validate(self):
        if not self.argv and not self.legacy_shell:
            raise ValueError("command requires argv or legacy_shell")
        if self.argv and self.legacy_shell:
            raise ValueError("command cannot define both argv and legacy_shell")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    def display(self):
        if self.argv:
            return " ".join(self.argv)
        return self.legacy_shell or ""

    @classmethod
    def from_dict(cls, value):
        if isinstance(value, str):
            return cls(legacy_shell=value)
        command = cls(
            argv=[str(item) for item in value.get("argv", [])],
            cwd=str(value.get("cwd", ".")),
            timeout_seconds=int(value.get("timeout_seconds", 300)),
            mutates=bool(value.get("mutates", False)),
            legacy_shell=value.get("legacy_shell"),
        )
        command.validate()
        return command


@dataclass
class StackContract:
    id: str
    template: str
    root: str = "."
    commands: Dict[str, CommandSpec] = field(default_factory=dict)
    environment: List[str] = field(default_factory=list)
    services: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, value):
        return cls(
            id=str(value.get("id") or value.get("template") or "stack"),
            template=str(value.get("template") or "generic"),
            root=str(value.get("root", ".")),
            commands={
                name: CommandSpec.from_dict(spec)
                for name, spec in (value.get("commands") or {}).items()
            },
            environment=[str(item) for item in value.get("environment", [])],
            services=[str(item) for item in value.get("services", [])],
        )


@dataclass
class ServiceContract:
    id: str
    kind: str
    required_by: List[str] = field(default_factory=list)
    healthcheck: Optional[CommandSpec] = None


@dataclass
class ProjectMeta:
    slug: str
    goal: str
    decision_status: str = "accepted"
    harness_status: str = "configured"


@dataclass
class ProjectContract:
    project: ProjectMeta
    primary: StackContract
    secondary: List[StackContract] = field(default_factory=list)
    services: List[ServiceContract] = field(default_factory=list)
    schema_version: int = 2
    migrated_from: Optional[int] = None
    verification_report: Optional[str] = None

    def all_stacks(self):
        return [self.primary, *self.secondary]

    def validate(self):
        if self.schema_version != 2:
            raise ValueError("only schema_version 2 can be written")
        ids = [stack.id for stack in self.all_stacks()]
        if len(ids) != len(set(ids)):
            raise ValueError("stack ids must be unique")
        for stack in self.all_stacks():
            if stack.root.startswith(("/", "\\")) or ".." in stack.root.replace("\\", "/").split("/"):
                raise ValueError(f"stack root must be project-relative: {stack.root}")
            missing = [name for name in COMMAND_ORDER if name not in stack.commands]
            if missing:
                raise ValueError(f"stack {stack.id} missing commands: {', '.join(missing)}")
            for command in stack.commands.values():
                command.validate()

    def to_dict(self):
        self.validate()
        payload = {
            "schema_version": self.schema_version,
            "project": asdict(self.project),
            "stacks": {
                "primary": stack_to_dict(self.primary),
                "secondary": [stack_to_dict(stack) for stack in self.secondary],
            },
            "services": [service_to_dict(service) for service in self.services],
            "commands": {
                name: command.display() for name, command in self.primary.commands.items()
            },
            "verification": {"latest_report": self.verification_report},
        }
        if self.migrated_from is not None:
            payload["migrated_from"] = self.migrated_from
        return payload


def command_to_dict(command):
    data = {
        "cwd": command.cwd,
        "timeout_seconds": command.timeout_seconds,
        "mutates": command.mutates,
    }
    if command.argv:
        data["argv"] = command.argv
    else:
        data["legacy_shell"] = command.legacy_shell
    return data


def stack_to_dict(stack):
    return {
        "id": stack.id,
        "template": stack.template,
        "root": stack.root,
        "commands": {name: command_to_dict(spec) for name, spec in stack.commands.items()},
        "environment": stack.environment,
        "services": stack.services,
    }


def service_to_dict(service):
    data = {"id": service.id, "kind": service.kind, "required_by": service.required_by}
    if service.healthcheck:
        data["healthcheck"] = command_to_dict(service.healthcheck)
    return data
