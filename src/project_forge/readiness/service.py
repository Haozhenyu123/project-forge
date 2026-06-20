"""Structural and executable Superpowers readiness checks."""

import json
from pathlib import Path

from project_forge.contract import load_contract, write_contract
from project_forge.handoff.service import export_handoff
from project_forge.harness.executor import execute_contract, write_report


ADR_SECTIONS = (
    "## Considered Options",
    "## Decision",
    "## Explicitly Rejected",
    "## Confidence Assessment",
    "## Risks and Revisit Triggers",
)


def _add(checks, check_id, status, message, path=None):
    item = {"id": check_id, "status": status, "message": message}
    if path:
        item["path"] = str(path).replace("\\", "/")
    checks.append(item)


def structural_checks(project, slug):
    project = Path(project)
    paths = {
        "evidence": project / "docs" / "research" / slug / "evidence.jsonl",
        "adr": project / "docs" / "architecture" / "ADR-0001-stack.md",
        "contract": project / "project-forge.yaml",
        "harness": project / "docs" / "harness.md",
        "handoff_markdown": project / "docs" / "superpowers-handoff.md",
        "handoff_json": project / "docs" / "superpowers-handoff.json",
    }
    checks = []
    for name, path in paths.items():
        _add(checks, f"artifact.{name}", "pass" if path.is_file() else "fail", f"{'Found' if path.is_file() else 'Missing'} {name}.", path)
    if paths["evidence"].is_file():
        rows = [json.loads(line) for line in paths["evidence"].read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        _add(checks, "evidence.rows", "pass" if rows else "fail", f"Evidence has {len(rows)} row(s).", paths["evidence"])
        if rows and all(row.get("provisional") for row in rows):
            _add(checks, "evidence.verified", "warn", "All evidence rows are provisional.", paths["evidence"])
        elif rows:
            _add(checks, "evidence.verified", "pass", "At least one evidence row is non-provisional.", paths["evidence"])
    if paths["adr"].is_file():
        text = paths["adr"].read_text(encoding="utf-8-sig")
        missing = [section for section in ADR_SECTIONS if section not in text]
        _add(checks, "adr.sections", "fail" if missing else "pass", "ADR missing: " + ", ".join(missing) if missing else "ADR contains decision-quality sections.", paths["adr"])
    contract = None
    if paths["contract"].is_file():
        try:
            contract = load_contract(paths["contract"], slug=slug)
            _add(checks, "contract.schema", "pass", f"Contract schema {contract.schema_version} loaded.", paths["contract"])
        except Exception as exc:
            _add(checks, "contract.schema", "fail", str(exc), paths["contract"])
    if paths["handoff_json"].is_file():
        try:
            handoff = json.loads(paths["handoff_json"].read_text(encoding="utf-8-sig"))
            schema = handoff.get("schema_version")
            _add(checks, "handoff.schema", "pass" if schema in {1, 2} else "fail", f"Handoff schema is {schema}.", paths["handoff_json"])
            _add(checks, "handoff.slug", "pass" if (handoff.get("project") or {}).get("slug") == slug else "fail", "Handoff slug matches." if (handoff.get("project") or {}).get("slug") == slug else "Handoff slug mismatch.", paths["handoff_json"])
        except (OSError, json.JSONDecodeError) as exc:
            _add(checks, "handoff.schema", "fail", str(exc), paths["handoff_json"])
    return checks, contract


def summarize(checks, execution=None, strict=False):
    failures = [item for item in checks if item["status"] == "fail"]
    warnings = [item for item in checks if item["status"] == "warn"]
    passed = [item for item in checks if item["status"] == "pass"]
    if failures or (strict and warnings):
        status = "blocked"
        readiness = "failed"
    elif execution and execution.get("status") == "verified":
        status = "ready"
        readiness = "verified"
    elif warnings:
        status = "attention"
        readiness = "structurally_ready"
    else:
        status = "ready"
        readiness = "structurally_ready"
    return {
        "status": status,
        "readiness_status": readiness,
        "score": round(100 * len(passed) / max(1, len(checks))),
        "passed": len(passed),
        "warnings": len(warnings),
        "failures": len(failures),
        "checks": checks,
        "execution": execution,
    }


def check_readiness(
    project,
    slug,
    execute=False,
    selected=None,
    include_install=False,
    include_run=False,
    allow_legacy_shell=False,
    timeout_seconds=300,
    continue_on_failure=False,
    strict=False,
):
    project = Path(project)
    checks, contract = structural_checks(project, slug)
    if any(item["status"] == "fail" for item in checks):
        return summarize(checks, strict=strict)
    execution = None
    if execute:
        results = execute_contract(
            contract,
            project,
            selected=selected,
            include_install=include_install,
            include_run=include_run,
            allow_legacy_shell=allow_legacy_shell,
            timeout_seconds=timeout_seconds,
            continue_on_failure=continue_on_failure,
        )
        report, payload = write_report(project, results, selected or ("test", "lint", "typecheck", "build", "smoke"))
        contract.verification_report = str(report.relative_to(project)).replace("\\", "/")
        write_contract(project / "project-forge.yaml", contract)
        export_handoff(project, slug)
        execution = {"status": payload["status"], "report": contract.verification_report, "results": payload["results"]}
        if payload["status"] != "verified":
            _add(checks, "execution.commands", "fail", "One or more harness commands failed.", report)
        else:
            _add(checks, "execution.commands", "pass", "Selected harness commands passed.", report)
    return summarize(checks, execution=execution, strict=strict)
