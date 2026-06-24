"""Loop strategy: switch evaluation, confidence checks, and policy enforcement."""

from typing import Any, Dict, List, Optional

from .models import ConfidenceTier, CostTier, LoopPolicy, LoopSignal, SignalSeverity


def evaluate_switch(
    current_stack: str,
    candidate_stack: str,
    current_score: float,
    candidate_score: float,
    policy: LoopPolicy,
    evidence_sources: List[str],
    confidence: ConfidenceTier,
    migration_cost: CostTier,
    signal: LoopSignal,
) -> Dict[str, Any]:
    """Evaluate whether a primary stack switch should be allowed."""
    result = {
        "allowed": False,
        "reason": "",
        "current_stack": current_stack,
        "candidate_stack": candidate_stack,
        "current_score": current_score,
        "candidate_score": candidate_score,
        "score_delta": round(candidate_score - current_score, 2),
    }
    if not policy.allow_primary_stack_switch:
        result["reason"] = "Primary stack switching is disabled by policy."
        return result
    if signal.severity == SignalSeverity.CRITICAL and signal.kind.value in {
        "security_advisory",
        "license_conflict",
    }:
        result["allowed"] = True
        result["reason"] = "Critical security / license hard-block triggers forced switch."
        return result
    delta = candidate_score - current_score
    if delta < policy.switch_score_delta:
        result["reason"] = f"Score delta ({delta}) < required ({policy.switch_score_delta})."
        return result
    _confidence_rank = {"high": 3, "medium": 2, "low": 1}
    if _confidence_rank.get(confidence.value, 0) < _confidence_rank.get(policy.minimum_confidence.value, 2):
        result["reason"] = f"Confidence ({confidence.value}) < minimum ({policy.minimum_confidence.value})."
        return result
    unique_sources = len(set(evidence_sources))
    if unique_sources < policy.minimum_independent_sources:
        result["reason"] = f"Independent sources ({unique_sources}) < minimum ({policy.minimum_independent_sources})."
        return result
    if migration_cost == CostTier.HIGH:
        result["reason"] = "Migration cost is too high for automatic switch."
        return result
    result["allowed"] = True
    result["reason"] = f"Switch allowed: delta {delta}, confidence {confidence.value}, sources {unique_sources}, migration {migration_cost.value}."
    return result


def evaluate_confidence(
    decision_confidence: str,
    evidence_count: int,
    provisional_count: int,
    source_diversity: int,
) -> ConfidenceTier:
    """Evaluate overall decision confidence."""
    if decision_confidence == "High" and source_diversity >= 3 and provisional_count == 0:
        return ConfidenceTier.HIGH
    if decision_confidence == "Low" or provisional_count > evidence_count // 2:
        return ConfidenceTier.LOW
    return ConfidenceTier.MEDIUM


def classify_migration_cost(candidate_stack: str, current_stack: str) -> CostTier:
    """Heuristic classification of migration cost when switching primary stacks."""
    node_family = {"node-ts", "nextjs", "electron", "cli", "chrome-extension"}
    python_family = {"python", "fastapi"}
    if candidate_stack == current_stack:
        return CostTier.LOW
    if candidate_stack in node_family and current_stack in node_family:
        return CostTier.LOW
    if candidate_stack in python_family and current_stack in python_family:
        return CostTier.LOW
    if (candidate_stack in node_family and current_stack in python_family) or (
        candidate_stack in python_family and current_stack in node_family
    ):
        return CostTier.MEDIUM
    return CostTier.HIGH
