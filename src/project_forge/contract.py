"""Read, write, and migrate Project Forge contracts."""

import json
from pathlib import Path

from .errors import ContractError
from .models import (
    COMMAND_ORDER,
    CommandSpec,
    ProjectContract,
    ProjectMeta,
    ServiceContract,
    StackContract,
)


def _strip_quotes(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def _legacy_sections(text):
    sections = {}
    section = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw.startswith((" ", "\t")) and raw.rstrip().endswith(":"):
            section = raw.strip()[:-1]
            sections.setdefault(section, {})
            continue
        if section and ":" in raw:
            key, value = raw.split(":", 1)
            sections[section][key.strip()] = _strip_quotes(value)
    return sections


def _flow_yaml(text):
    payload = {}
    section = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        key, sep, value = raw.strip().partition(":")
        if not sep:
            continue
        if indent == 0:
            if value.strip():
                payload[key] = _decode_scalar(value.strip())
                section = None
            else:
                payload[key] = {}
                section = key
        elif indent == 2 and section:
            payload[section][key] = _decode_scalar(value.strip())
    return payload


def _decode_scalar(value):
    if not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        if value in {"true", "false"}:
            return value == "true"
        try:
            return int(value)
        except ValueError:
            return _strip_quotes(value)


def _optional_yaml(text):
    try:
        import yaml  # type: ignore
    except ImportError:
        return None
    value = yaml.safe_load(text)
    return value if isinstance(value, dict) else None


def load_payload(path):
    text = Path(path).read_text(encoding="utf-8-sig")
    stripped = text.lstrip()
    if stripped.startswith("{"):
        return json.loads(text)
    parsed = _optional_yaml(text)
    if parsed is not None:
        return parsed
    return _flow_yaml(text)


def load_contract(path, slug=None, goal=None):
    path = Path(path)
    text = path.read_text(encoding="utf-8-sig")
    payload = load_payload(path)
    if int(payload.get("schema_version", 0) or 0) == 2:
        return contract_from_v2(payload)
    return migrate_v1_text(text, slug=slug, goal=goal)


def contract_from_v2(payload):
    try:
        project_data = payload["project"]
        stacks = payload["stacks"]
        contract = ProjectContract(
            project=ProjectMeta(
                slug=str(project_data["slug"]),
                goal=str(project_data["goal"]),
                decision_status=str(project_data.get("decision_status", "accepted")),
                harness_status=str(project_data.get("harness_status", "configured")),
            ),
            primary=StackContract.from_dict(stacks["primary"]),
            secondary=[StackContract.from_dict(item) for item in stacks.get("secondary", [])],
            services=[
                ServiceContract(
                    id=str(item["id"]),
                    kind=str(item.get("kind", "service")),
                    required_by=[str(value) for value in item.get("required_by", [])],
                    healthcheck=CommandSpec.from_dict(item["healthcheck"])
                    if item.get("healthcheck") else None,
                )
                for item in payload.get("services", [])
            ],
            migrated_from=payload.get("migrated_from"),
            verification_report=(payload.get("verification") or {}).get("latest_report"),
        )
        contract.validate()
        return contract
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError(f"invalid schema v2 contract: {exc}") from exc


def migrate_v1_text(text, slug=None, goal=None):
    sections = _legacy_sections(text)
    project = sections.get("project", {})
    commands = sections.get("commands", {})
    template = sections.get("template", {}).get("name") or "generic"
    if not commands:
        top = _flow_yaml(text)
        commands = top.get("commands", {}) if isinstance(top.get("commands"), dict) else {}
        template = str(top.get("template") or template)
    normalized = {}
    for name in COMMAND_ORDER:
        value = commands.get(name) or f"echo {name} command not configured"
        normalized[name] = CommandSpec(legacy_shell=str(value))
    return ProjectContract(
        project=ProjectMeta(
            slug=slug or str(project.get("slug") or "project"),
            goal=goal or str(project.get("goal") or "Migrated Project Forge project"),
        ),
        primary=StackContract(id="primary", template=template, commands=normalized),
        migrated_from=1,
    )


def dump_contract(contract):
    payload = contract.to_dict()
    lines = [f"schema_version: {payload['schema_version']}", "project:"]
    for key, item in payload["project"].items():
        lines.append(f"  {key}: {json.dumps(item)}")
    lines.append("stacks: " + json.dumps(payload["stacks"], sort_keys=True))
    if contract.secondary:
        lines.append(f"secondary_stack: {contract.secondary[0].template}")
        lines.append("secondary_commands:")
        for key, command in contract.secondary[0].commands.items():
            lines.append(f"  {key}: {command.display()}")
    lines.append("services: " + json.dumps(payload["services"], sort_keys=True))
    lines.append("commands:")
    for key, item in payload["commands"].items():
        lines.append(f"  {key}: {item}")
    lines.append("verification: " + json.dumps(payload["verification"], sort_keys=True))
    if payload.get("migrated_from") is not None:
        lines.append(f"migrated_from: {payload['migrated_from']}")
    return "\n".join(lines) + "\n"


def write_contract(path, contract):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(dump_contract(contract))
