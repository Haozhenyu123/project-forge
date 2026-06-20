"""Build Markdown and Schema v2 Superpowers handoff packets."""

import json
from pathlib import Path

from project_forge.contract import load_contract
from project_forge.models import COMMAND_ORDER, stack_to_dict


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL line {number} in {path}: {exc}") from exc
            if isinstance(value, dict):
                rows.append(value)
    return rows


def _optional_json(path):
    path = Path(path)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _relative(project, path):
    return str(Path(path).relative_to(project)).replace("\\", "/")


def build_packet(project, slug):
    project = Path(project)
    evidence_path = project / "docs" / "research" / slug / "evidence.jsonl"
    adr_path = project / "docs" / "architecture" / "ADR-0001-stack.md"
    harness_path = project / "docs" / "harness.md"
    contract_path = project / "project-forge.yaml"
    required = [evidence_path, adr_path, harness_path, contract_path]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing handoff input(s): " + ", ".join(missing))
    contract = load_contract(contract_path, slug=slug)
    evidence = read_jsonl(evidence_path)
    creative_path = project / "docs" / "product" / "creative-decision.json"
    inventory_path = project / "docs" / "architecture" / "inventory.json"
    verification_path = project / contract.verification_report if contract.verification_report else None
    verification = _optional_json(verification_path) if verification_path else None
    packet = {
        "schema_version": 2,
        "kind": "project-forge.superpowers-handoff",
        "project": {
            "slug": contract.project.slug or slug,
            "goal": contract.project.goal,
            "primary_stack": contract.primary.template,
            "secondary_stacks": [stack.template for stack in contract.secondary],
        },
        "artifacts": {
            "evidence": _relative(project, evidence_path),
            "adr": _relative(project, adr_path),
            "contract": "project-forge.yaml",
            "harness": _relative(project, harness_path),
            "creative_decision": _relative(project, creative_path) if creative_path.is_file() else None,
            "inventory": _relative(project, inventory_path) if inventory_path.is_file() else None,
            "verification_report": contract.verification_report,
        },
        "evidence": [
            {
                "evidence_id": row.get("evidence_id"),
                "title": row.get("title") or row.get("name"),
                "url": row.get("url") or row.get("html_url"),
                "summary": row.get("summary") or row.get("description"),
                "source": row.get("source"),
                "source_quality": row.get("source_quality"),
                "observed_at": row.get("observed_at"),
                "provisional": bool(row.get("provisional")),
            }
            for row in evidence[:12]
        ],
        "creative_decision": _optional_json(creative_path),
        "inventory": _optional_json(inventory_path),
        "harness": {
            "primary": stack_to_dict(contract.primary),
            "secondary": [stack_to_dict(stack) for stack in contract.secondary],
            "required_commands": list(COMMAND_ORDER),
        },
        "readiness": {
            "status": verification.get("status") if verification else "structurally_ready",
            "verification_report": contract.verification_report,
        },
        "compatibility": {
            "project_forge_contract": 2,
            "handoff_schema": 2,
            "superpowers": "see compatibility/superpowers.json",
        },
        "superpowers": {
            "assignment": "Consume this packet and implement without re-litigating accepted product and architecture decisions.",
            "first_task": "Implement the smallest user-visible workflow from the accepted creative direction and prove it with the harness contract.",
            "acceptance_criteria": [
                "Preserve the accepted ADR unless new evidence is recorded.",
                "Run the relevant structured harness commands and explain remaining failures.",
                "Keep implementation scope inside the accepted creative direction.",
                "Return to Project Forge when direction, architecture, or harness assumptions become stale.",
            ],
            "guardrails": [
                "Project Forge does not replace TDD, debugging, code review, worktrees, or branch completion.",
                "Do not silently replace provisional evidence with unsupported claims.",
                "Do not execute commands that are absent from the harness contract.",
            ],
            "consume_steps": [
                "Read this packet and the Markdown handoff.",
                "Open the ADR, creative decision, inventory, and evidence only when more detail is needed.",
                "Use Superpowers implementation workflows after accepting the packet.",
            ],
        },
        "boundary": {
            "project_forge_owns": ["product direction", "evidence", "architecture", "harness", "handoff"],
            "superpowers_owns": ["implementation planning", "TDD", "debugging", "review", "branch completion"],
        },
    }
    return packet


def render_markdown(packet, adr_text, harness_text):
    project = packet["project"]
    evidence = packet["evidence"]
    lines = [
        "# Superpowers Handoff",
        "",
        "## Brief",
        "",
        f"- Project slug: `{project['slug']}`",
        f"- Goal: {project['goal']}",
        f"- Primary stack: `{project['primary_stack']}`",
        f"- Secondary stacks: {', '.join(project['secondary_stacks']) or 'none'}",
        f"- First task: {packet['superpowers']['first_task']}",
        "",
        "## Evidence",
        "",
    ]
    for row in evidence:
        marker = " provisional" if row["provisional"] else ""
        lines.append(f"- [{row.get('evidence_id') or '?'}]{marker} {row.get('title')}: {row.get('summary')} ({row.get('url')})")
    lines.extend([
        "",
        "## Architecture Decision",
        "",
        "Read `docs/architecture/ADR-0001-stack.md` before changing architecture.",
        "",
        "```markdown",
        *[line for line in adr_text.splitlines() if line.strip()][:16],
        "```",
        "",
        "## Harness Commands",
        "",
    ])
    for stack in [packet["harness"]["primary"], *packet["harness"]["secondary"]]:
        lines.append(f"### {stack['id']} (`{stack['template']}` at `{stack['root']}`)")
        lines.append("")
        for name in COMMAND_ORDER:
            spec = stack["commands"][name]
            command = " ".join(spec.get("argv", [])) or spec.get("legacy_shell", "")
            lines.append(f"- `{name}`: `{command}`")
        lines.append("")
    lines.extend([
        "## Acceptance Criteria",
        "",
        *[f"- {item}" for item in packet["superpowers"]["acceptance_criteria"]],
        "",
        "## Guardrails",
        "",
        *[f"- {item}" for item in packet["superpowers"]["guardrails"]],
        "",
        "## Readiness",
        "",
        f"- Status: `{packet['readiness']['status']}`",
        f"- Verification report: `{packet['readiness']['verification_report'] or 'not run'}`",
        "",
        "## Machine-Readable Packet",
        "",
        "Source: `docs/superpowers-handoff.json` (Schema v2).",
        "",
        "## How Superpowers Should Consume This",
        "",
        *[f"{index}. {item}" for index, item in enumerate(packet["superpowers"]["consume_steps"], start=1)],
        "",
        "## Harness Notes",
        "",
        "```markdown",
        *[line for line in harness_text.splitlines() if line.strip()][:16],
        "```",
        "",
    ])
    return "\n".join(lines)


def export_handoff(project, slug, markdown_out=None, json_out=None):
    project = Path(project)
    packet = build_packet(project, slug)
    markdown_path = Path(markdown_out or project / "docs" / "superpowers-handoff.md")
    json_path = Path(json_out or project / "docs" / "superpowers-handoff.json")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    adr = (project / "docs" / "architecture" / "ADR-0001-stack.md").read_text(encoding="utf-8-sig")
    harness = (project / "docs" / "harness.md").read_text(encoding="utf-8-sig")
    with markdown_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_markdown(packet, adr, harness))
    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"markdown": markdown_path, "json": json_path, "packet": packet}
