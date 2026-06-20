"""Heuristic effort estimation based on stack complexity and project signals.

Does NOT replace real planning; gives Superpowers a rough scale reference.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from project_forge.models import EffortEstimate


_STACK_BASELINE_DAYS: Dict[str, Dict[str, Any]] = {
    "nextjs": {"m3": 5, "m6": 15, "m12": 40, "cost": "low"},
    "node-ts": {"m3": 5, "m6": 12, "m12": 35, "cost": "low"},
    "python": {"m3": 5, "m6": 15, "m12": 40, "cost": "low"},
    "fastapi": {"m3": 7, "m6": 20, "m12": 45, "cost": "medium"},
    "electron": {"m3": 15, "m6": 40, "m12": 80, "cost": "medium"},
    "chrome-extension": {"m3": 8, "m6": 20, "m12": 40, "cost": "low"},
    "cli": {"m3": 5, "m6": 15, "m12": 30, "cost": "low"},
    "generic": {"m3": 0, "m6": 0, "m12": 0, "cost": "unknown"},
}

_SIGNAL_MULTIPLIERS: Dict[str, float] = {
    "small-scope": 0.6,
    "single-primary-workflow": 0.75,
    "fast-feedback": 0.85,
    "stateful-guidance": 1.3,
    "multi-view-comparison": 1.4,
    "real-time": 1.5,
    "offline-first": 1.6,
    "multi-tenant": 1.7,
    "embeddable": 0.8,
}

_SECONDARY_STACK_COST: float = 1.35  # each additional stack adds ~35%


def estimate_effort(
    primary_stack: str,
    secondary_stacks: Optional[List[str]] = None,
    creative_signals: Optional[List[str]] = None,
    scope_months: int = 6,
) -> EffortEstimate:
    """Produce a heuristic effort estimate."""
    baseline = _STACK_BASELINE_DAYS.get(primary_stack, _STACK_BASELINE_DAYS["generic"])
    scope_key = f"m{scope_months}" if f"m{scope_months}" in baseline else "m6"
    base_days = int(baseline.get(scope_key, 0))

    if base_days == 0:
        return EffortEstimate(
            development_days=0,
            infrastructure_cost_tier="unknown",
            team_size_recommendation="Unknown — choose a concrete stack first",
            complexity_drivers=["No stack selected"],
            confidence="low",
        )

    multiplier = 1.0
    drivers: List[str] = [f"Base: {primary_stack} ({scope_months}-month scope)"]

    # Signal multipliers
    for signal in (creative_signals or []):
        m = _SIGNAL_MULTIPLIERS.get(signal)
        if m and m != 1.0:
            multiplier *= m
            drivers.append(f"Signal '{signal}': x{m}")

    # Secondary stacks
    secondaries = secondary_stacks or []
    if secondaries:
        multiplier *= _SECONDARY_STACK_COST ** len(secondaries)
        drivers.append(f"Secondary stacks: {secondaries} (x{_SECONDARY_STACK_COST ** len(secondaries):.1f})")

    estimated_days = max(1, round(base_days * multiplier))

    # Team size
    if estimated_days <= 15:
        team = "1 developer"
    elif estimated_days <= 40:
        team = "1-2 developers"
    elif estimated_days <= 80:
        team = "2-3 developers"
    else:
        team = "3-5 developers"

    # Cost tier
    cost = str(baseline.get("cost", "low"))
    if multiplier > 1.5:
        cost = "high" if cost == "medium" else "medium"

    return EffortEstimate(
        development_days=estimated_days,
        infrastructure_cost_tier=cost,
        team_size_recommendation=team,
        complexity_drivers=drivers,
        confidence="medium" if estimated_days <= 60 else "low",
    )
