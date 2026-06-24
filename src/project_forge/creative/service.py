"""Creative Director recommendations with commercial reasoning."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .models import CreativeDecision, CreativeDirection




def _domain_directions(domain_tag: str, goal: str, constraints, evidence_rows, any_verified, team_ids, dashboard_ids, automation_ids):
    """Return domain-specific creative directions based on the domain tag."""
    # Default to universal if domain not recognized
    return _universal_directions(goal, constraints, evidence_rows, any_verified, team_ids, dashboard_ids, automation_ids)


def _universal_directions(goal: str, constraints, evidence_rows, any_verified, team_ids, dashboard_ids, automation_ids):
    """Return the three universal creative directions."""
def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _context(goal: str, constraints: Iterable[str]) -> str:
    return " ".join([goal, *[str(item) for item in constraints]]).lower()


def _evidence_ids(evidence: Iterable[Dict[str, object]], *needles: str) -> List[str]:
    ids: List[str] = []
    for row in evidence:
        text = " ".join(str(row.get(key, "")) for key in ("title", "summary", "source", "url")).lower()
        if any(needle in text for needle in needles):
            value = row.get("evidence_id")
            if value:
                ids.append(str(value))
    return sorted(set(ids))


def _confidence(ids: List[str], provisional: bool) -> str:
    if provisional or not ids:
        return "provisional"
    if len(ids) >= 2:
        return "medium"
    return "low"


def build_creative_decision(
    goal: str,
    constraints: Optional[Iterable[str]] = None,
    evidence: Optional[Iterable[Dict[str, object]]] = None,
    selected_direction_id: Optional[str] = None,
    domain_tag: str = "general",
) -> CreativeDecision:
    """Return three concrete angles and one default recommendation."""

    constraints = list(constraints or [])
    evidence_rows = list(evidence or [])
    context = _context(goal, constraints)
    any_verified = any(not row.get("provisional") for row in evidence_rows)
    team_ids = _evidence_ids(evidence_rows, "team", "collaboration", "workflow", "planning")
    dashboard_ids = _evidence_ids(evidence_rows, "dashboard", "analytics", "evidence", "decision")
    automation_ids = _evidence_ids(evidence_rows, "automation", "agent", "workflow", "developer")

    directions = [
        CreativeDirection(
            id="focused-mvp",
            name="Focused MVP",
            promise=f"Ship the smallest useful version of: {goal}",
            audience="a narrow first user group with an urgent, repeated workflow",
            reason="fastest path to validation and lowest scope risk",
            target_user_pain="The user needs one painful job completed reliably before broader platform value matters.",
            reachability=82,
            differentiation=62,
            value_signal=68,
            validation_speed=90,
            implementation_cost=35,
            evidence_confidence=_confidence(automation_ids, not any_verified),
            evidence_ids=automation_ids,
            provisional=not bool(automation_ids),
            architecture_signals=["small-scope", "single-primary-workflow", "fast-feedback"],
        ),
        CreativeDirection(
            id="guided-workflow",
            name="Guided Workflow",
            promise="Turn the problem into a step-by-step decision journey.",
            audience="users who know the outcome they want but not the sequence of choices",
            reason="best fit when the idea is vague and users need momentum more than customization",
            target_user_pain="The user is blocked by ambiguity, not lack of tools.",
            reachability=76,
            differentiation=74,
            value_signal=70,
            validation_speed=82,
            implementation_cost=48,
            evidence_confidence=_confidence(team_ids, not any_verified),
            evidence_ids=team_ids,
            provisional=not bool(team_ids),
            architecture_signals=["stateful-guidance", "decision-history", "human-readable-artifacts"],
        ),
        CreativeDirection(
            id="evidence-dashboard",
            name="Evidence Dashboard",
            promise="Make options, evidence, confidence, and next actions visible.",
            audience="teams that need shared confidence before implementation",
            reason="commercially strongest when stakeholders must compare options and justify tradeoffs",
            target_user_pain="The team needs decisions to be inspectable, repeatable, and defensible.",
            reachability=70,
            differentiation=80,
            value_signal=78,
            validation_speed=72,
            implementation_cost=58,
            evidence_confidence=_confidence(dashboard_ids, not any_verified),
            evidence_ids=dashboard_ids,
            provisional=not bool(dashboard_ids),
            architecture_signals=["auditability", "evidence-store", "multi-view-comparison"],
        ),
    ]
    default = "focused-mvp"
    if any(word in context for word in ("team", "stakeholder", "dashboard", "decision", "evidence")):
        default = "evidence-dashboard"
    if any(word in context for word in ("vague", "idea", "not sure", "ambiguous", "recommend")):
        default = "guided-workflow"
    selected = selected_direction_id if selected_direction_id in {item.id for item in directions} else default
    return CreativeDecision(
        goal=goal,
        selected_direction_id=selected,
        directions=directions,
        created_at=_now(),
        assumptions=[
            "Commercial reasoning is directional until user interviews, traffic, or payment intent are measured.",
            "Architecture choices must stay aligned with the accepted creative direction.",
        ],
    )


def render_brief(decision: CreativeDecision, slug: str) -> str:
    selected = next(item for item in decision.directions if item.id == decision.selected_direction_id)
    lines = [
        "# Creative Brief",
        "",
        f"- Project slug: `{slug}`",
        f"- Goal: {decision.goal}",
        f"- Selected direction: `{selected.name}`",
        f"- Created: {decision.created_at}",
        "",
        "## Experience Thesis",
        "",
        selected.promise,
        "",
        "## Target User",
        "",
        selected.audience,
        "",
        "## Primary Workflow",
        "",
        "Guide the user from an initial idea to an accepted product direction, then to architecture and harness readiness.",
        "",
        "## First Interaction",
        "",
        "Present three concrete angles, choose a default, and ask only for corrections that would change the decision.",
        "",
        "## Interaction Style",
        "",
        "Opinionated, evidence-aware, and concise; make the next decision obvious.",
        "",
        "## Content Tone",
        "",
        "Clear, commercially grounded, and calm.",
        "",
        "## Platform",
        "",
        "Host-agent workflow with repository artifacts; no SaaS backend required for V1.",
        "",
        "## Competitive Context",
        "",
        "Compare direct competitors, substitute workflows, and manual decision processes when evidence is available.",
        "",
        "## Differentiation",
        "",
        selected.reason,
        "",
        "## Architecture Signals",
        "",
        *[f"- {item}" for item in selected.architecture_signals],
        "",
        "## Assumptions",
        "",
        *[f"- {item}" for item in decision.assumptions],
        "",
        "## Risks",
        "",
        "- Direction is provisional when evidence confidence is low.",
        "- Architecture must be revisited if the accepted creative direction changes.",
        "- Product claims need validation before they become implementation scope.",
        "",
        "## Next Steps",
        "",
        "1. Feed the accepted direction into architecture scoring.",
        "2. Record evidence gaps as provisional instead of inventing confidence.",
        "3. Generate harness and handoff only after the direction is explicit.",
        "",
    ]
    return "\n".join(lines)


def write_creative_outputs(
    project: Path,
    slug: str,
    goal: str,
    evidence: Iterable[Dict[str, object]],
    selected_direction_id: Optional[str] = None,
) -> Dict[str, Path]:
    decision = build_creative_decision(goal, evidence=evidence, selected_direction_id=selected_direction_id)
    product_dir = Path(project) / "docs" / "product"
    product_dir.mkdir(parents=True, exist_ok=True)
    decision_path = product_dir / "creative-decision.json"
    decision_path.write_text(
        json.dumps(decision.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    brief_path = Path(project) / "docs" / "creative-brief.md"
    brief_path.parent.mkdir(parents=True, exist_ok=True)
    with brief_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_brief(decision, slug))
    return {"decision": decision_path, "brief": brief_path}
