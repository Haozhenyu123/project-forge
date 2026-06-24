"""Impact analysis: assess signal effects on evidence, ADR, risks, harness, and handoff."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import LoopEpisode, LoopIteration, LoopPolicy, LoopSignal, LoopStatus, SignalKind, SignalSeverity
from .signals import classify_owner, OwnerClassification


def compute_decision_hash(project_dir: Path) -> str:
    """Compute a stable hash from the current ADR and project-forge.yaml."""
    adr_path = project_dir / "docs" / "architecture" / "ADR-0001-stack.md"
    contract_path = project_dir / "project-forge.yaml"
    hasher = hashlib.sha256()
    for path in (adr_path, contract_path):
        if path.is_file():
            hasher.update(path.read_bytes())
    return hasher.hexdigest()[:16]


def impact_summary(signal: LoopSignal, project_dir: Path) -> Dict[str, Any]:
    """Produce a structured impact summary for a signal on the current project state."""
    summary: Dict[str, Any] = {
        "signal_id": signal.signal_id,
        "fingerprint": signal.fingerprint,
        "owner": classify_owner(signal).value,
        "affected_domains": [],
        "risk_escalations": [],
        "evidence_staleness": [],
        "recommended_action": "review",
        "reason": "",
    }
    # Domain impact
    if signal.kind == SignalKind.VERIFICATION_FAILURE:
        summary["affected_domains"] = ["harness", "readiness"]
        summary["recommended_action"] = "route_to_superpowers"
        summary["reason"] = "Verification failure is an implementation concern."
    elif signal.kind == SignalKind.ARCHITECTURE_FEEDBACK:
        summary["affected_domains"] = ["architecture", "harness", "risks"]
        summary["recommended_action"] = "revise_adr"
        summary["reason"] = "Architecture feedback suggests ADR mismatch."
    elif signal.kind == SignalKind.CONSTRAINT_CHANGE:
        summary["affected_domains"] = ["architecture", "product_direction", "risks"]
        summary["recommended_action"] = "revise_adr"
        summary["reason"] = f"Constraint change affects: {signal.affected_constraints}."
    elif signal.kind == SignalKind.EVIDENCE_EXPIRY:
        summary["affected_domains"] = ["evidence", "risks"]
        summary["recommended_action"] = "refresh_evidence"
        summary["reason"] = "Evidence has expired and may affect decision confidence."
    elif signal.kind == SignalKind.SECURITY_ADVISORY:
        summary["affected_domains"] = ["architecture", "risks", "evidence"]
        summary["recommended_action"] = "switch_or_block"
        summary["reason"] = "Security advisory may require stack change."
    elif signal.kind == SignalKind.LICENSE_CONFLICT:
        summary["affected_domains"] = ["architecture", "risks", "evidence"]
        summary["recommended_action"] = "switch_or_block"
        summary["reason"] = "License conflict may require stack change."
    elif signal.kind == SignalKind.SUPERPOWERS_FEEDBACK:
        summary["affected_domains"] = ["architecture", "harness"]
        summary["recommended_action"] = "revise_adr"
        summary["reason"] = "Superpowers feedback suggests direction/architecture mismatch."
    elif signal.kind == SignalKind.MANUAL:
        summary["affected_domains"] = ["architecture", "product_direction", "harness", "risks"]
        summary["recommended_action"] = "review"
        summary["reason"] = "Manual signal requires human review."
    if signal.severity in {SignalSeverity.CRITICAL, SignalSeverity.HIGH}:
        summary["risk_escalations"].append(f"{signal.kind.value}:{signal.signal_id}")
    return summary
