"""Deterministic product-direction and architecture decision engine."""

import argparse
import json
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

from project_forge.creative import build_creative_decision

from .catalog import CatalogSource, StackCatalog, StackDefinition, load_catalog
from .scoring import score_stack


def flatten_payload(payload: Dict[str, Any]) -> str:
    pieces = [payload.get("goal", "")]
    pieces.extend(payload.get("constraints", []) or [])
    for key in ("creative_brief", "creative_decision"):
        value = payload.get(key, {}) or {}
        if isinstance(value, dict):
            pieces.extend(str(item) for item in value.values())
        else:
            pieces.append(str(value))
    return " ".join(pieces).lower()


def product_directions(payload: Dict[str, Any]) -> tuple:
    decision = build_creative_decision(
        payload.get("goal") or "Untitled project",
        constraints=payload.get("constraints") or [],
        evidence=payload.get("evidence") or [],
    ).to_dict()
    directions = [
        {
            "id": item["id"],
            "name": item["name"],
            "promise": item["promise"],
            "audience": item["audience"],
            "reason": item["reason"],
            "scores": {
                "reachability": item["reachability"],
                "differentiation": item["differentiation"],
                "value_signal": item["value_signal"],
                "validation_speed": item["validation_speed"],
                "implementation_cost": item["implementation_cost"],
            },
            "evidence_ids": item["evidence_ids"],
            "evidence_confidence": item["evidence_confidence"],
            "provisional": item["provisional"],
        }
        for item in decision["directions"]
    ]
    return directions, decision["selected_direction"]


def detect_conflicts(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    context = flatten_payload(payload)
    conflicts: List[Dict[str, Any]] = []
    if "offline" in context and "instant sync" in context and "no server" in context:
        conflicts.append(
            {
                "id": "offline-sync-no-server",
                "constraints": ["offline-first", "instant sync", "no server"],
                "resolution": "Choose either local-first with later sync or server-backed sync.",
            }
        )
    return conflicts


def desired_capabilities(payload: Dict[str, Any]) -> Set[str]:
    context = flatten_payload(payload)
    caps: Set[str] = set()
    mapping = {
        "dashboard": "dashboard",
        "web": "web",
        "frontend": "frontend",
        "backend": "backend",
        "api": "api",
        "rest": "rest",
        "python": "python",
        "typescript": "typescript",
        "extension": "extension",
        "chrome": "extension",
        "cli": "cli",
        "real-time": "realtime",
        "realtime": "realtime",
        "ai": "ai",
        "data": "data",
        "desktop": "desktop",
        "offline": "offline",
    }
    for needle, cap in mapping.items():
        if needle in context:
            caps.add(cap)
    if not caps:
        caps.update({"web", "api"})
    return caps


def _custom_source(stack_id: str) -> CatalogSource:
    dimensions = [
        "maintenance_activity",
        "license",
        "security_risk",
        "deployment_cost",
        "complexity",
        "harness_availability",
    ]
    return CatalogSource(
        evidence_id=f"CUSTOM-{stack_id}",
        url="project-forge input",
        title=f"User supplied candidate stack {stack_id}",
        dimensions=dimensions,
        applicability="User supplied architecture candidate.",
    )


def _custom_stack(item: Dict[str, Any]) -> StackDefinition:
    stack_id = str(item.get("id") or item.get("name", "custom").lower().replace(" ", "-"))
    harnesses = list(item.get("harnesses") or item.get("harness", []) or [])
    if isinstance(item.get("harness"), dict):
        raw_harness = item["harness"]
        harness = {
            "primary": raw_harness.get("primary") or stack_id,
            "secondary": list(raw_harness.get("secondary") or []),
        }
    else:
        harness = {"primary": harnesses[0] if harnesses else "", "secondary": harnesses[1:]}
    raw_complexity = int(item.get("complexity", 50))
    baselines = {
        "maintenance_activity": int(item.get("maintenance", 50)),
        "license": int(item.get("license", 50)),
        "security_risk": int(item.get("security_risk", 50)),
        "deployment_cost": int(item.get("deployment_cost", 50)),
        "complexity": max(0, 100 - raw_complexity),
        "maturity_months": int(item.get("maturity_months", 0)),
    }
    return StackDefinition(
        id=stack_id,
        name=str(item.get("name") or stack_id),
        kind="custom",
        aliases=[str(value).lower() for value in item.get("aliases", [])],
        capabilities={str(value).lower() for value in item.get("capabilities", [])},
        harness=harness,
        baselines=baselines,
        sources=[_custom_source(stack_id)],
    )


def stack_pool(payload: Dict[str, Any], catalog: Optional[StackCatalog] = None) -> List[StackDefinition]:
    catalog = catalog or load_catalog()
    stacks = list(catalog.stacks)
    stacks.extend(_custom_stack(item) for item in payload.get("candidate_stacks") or [])
    return stacks


def _score_reason(stack: StackDefinition, scores: Dict[str, Any]) -> str:
    primary = stack.harness.get("primary") or "none"
    return f"Fit {scores['fit']} with harness {primary}"


def _reasons(stack: StackDefinition, scores: Dict[str, Any]) -> List[str]:
    reasons: List[str] = []
    if int(stack.baselines.get("maturity_months", 0)) < 18:
        reasons.append("maturity is too low for a default recommendation")
    if scores["source_diversity"] < 40:
        reasons.append("evidence diversity is weak")
    if not scores.get("evidence_ids"):
        reasons.append("no matched external evidence")
    if not stack.harness.get("primary"):
        reasons.append("no Project Forge harness is available")
    return reasons


def architecture_candidates(
    payload: Dict[str, Any],
    as_of: str,
    limit: bool = True,
    catalog: Optional[StackCatalog] = None,
) -> List[Dict[str, Any]]:
    scored: List[Dict[str, Any]] = []
    catalog = catalog or load_catalog()
    desired = desired_capabilities(payload)
    evidence = payload.get("evidence", []) or []
    weights = dict(catalog.default_weights)
    weights.update({key: float(value) for key, value in (payload.get("weights") or {}).items()})
    context = flatten_payload(payload)
    for stack in stack_pool(payload, catalog):
        scores = score_stack(stack, desired, evidence, weights, as_of)
        total = float(scores["total"])
        if int(stack.baselines.get("maturity_months", 0)) < 18:
            total = round(total * 0.45, 2)
        if stack.kind == "profile" and {"frontend", "backend"} <= desired:
            total = round(total + 12, 2)
        if stack.id == "nextjs-fastapi" and "python" in context and "typescript" in context:
            total = round(total + 6, 2)
        candidate = {
            "id": stack.id,
            "name": stack.name,
            "score": total,
            "scores": scores,
            "harness": {
                "primary": stack.harness.get("primary", ""),
                "secondary": list(stack.harness.get("secondary") or []),
            },
            "reason": _score_reason(stack, scores),
            "reasons": _reasons(stack, scores),
            "evidence_ids": scores.get("evidence_ids", []),
            "handoff": {
                "architecture_mode": "multi-stack"
                if stack.harness.get("secondary")
                else "single-stack",
                "required_commands": [
                    "install",
                    "test",
                    "lint",
                    "typecheck",
                    "build",
                    "run",
                    "smoke",
                ],
            },
        }
        scored.append(candidate)
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:3] if limit else scored


def confidence(candidates: Sequence[Dict[str, Any]], evidence: Sequence[Dict[str, Any]], conflicts):
    if conflicts or not candidates:
        return "Low"
    if not evidence:
        return "Low"
    selected = candidates[0]
    scores = selected["scores"]
    if scores["evidence_freshness"] >= 75 and scores["source_diversity"] >= 80:
        return "High"
    if scores["evidence_freshness"] >= 50:
        return "Medium"
    return "Low"


def revisit_triggers(candidates: Sequence[Dict[str, Any]], conflicts):
    triggers = []
    if conflicts:
        triggers.append(
            {
                "id": "resolve-conflicting-constraints",
                "reason": "Conflicting product or architecture constraints must be resolved before implementation.",
            }
        )
    if candidates and candidates[0]["scores"]["evidence_freshness"] < 50:
        triggers.append(
            {
                "id": "stale-evidence",
                "reason": "Refresh evidence before treating this decision as stable.",
            }
        )
    triggers.extend(
        [
            {
                "id": "harness-fails",
                "reason": "Revisit if install, test, build, or smoke commands cannot pass.",
            },
            {
                "id": "scope-shift",
                "reason": "Revisit if the product shifts from decision/handoff into implementation workflow ownership.",
            },
        ]
    )
    return triggers


def build_decision(payload: Dict[str, Any], as_of: Optional[str] = None) -> Dict[str, Any]:
    as_of = as_of or date.today().isoformat()
    directions, selected_direction = product_directions(payload)
    conflicts = detect_conflicts(payload)
    candidates = architecture_candidates(payload, as_of)
    all_candidates = architecture_candidates(payload, as_of, limit=False)
    selected = candidates[0]
    rejected = [
        {"id": item["id"], "name": item["name"], "reasons": item["reasons"] or [item["reason"]]}
        for item in all_candidates
        if item["id"] != selected["id"]
    ]
    result_confidence = confidence(candidates, payload.get("evidence", []) or [], conflicts)
    return {
        "schema_version": 2,
        "as_of": as_of,
        "goal": payload.get("goal", ""),
        "product_directions": directions,
        "selected_direction": selected_direction,
        "architecture_candidates": candidates,
        "selected_architecture": selected,
        "selected_stack": selected["harness"]["primary"],
        "secondary_stack": selected["harness"]["secondary"][0]
        if selected["harness"].get("secondary")
        else "",
        "rejected_options": rejected,
        "decision_confidence": result_confidence,
        "confidence": {
            "level": result_confidence,
            "reason": "based on constraint fit, evidence freshness, source diversity, maintenance, risk, cost, complexity, and harness availability",
        },
        "clarifying_questions": [
            "Who is the first user group?",
            "Which workflow must be useful on day one?",
        ]
        if result_confidence == "Low"
        else [],
        "assumptions": [
            "Project Forge stops at decision, architecture, harness, and handoff.",
            "Implementation execution is delegated to Superpowers or another implementation workflow.",
        ],
        "conflicts": conflicts,
        "revisit_triggers": revisit_triggers(candidates, conflicts),
        "rationale": selected["reason"],
        "candidates": [
            {"stack": item["harness"]["primary"], "score": item["score"], "reason": item["reason"]}
            for item in candidates
        ],
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input project brief JSON")
    parser.add_argument("--out", required=True, help="Output decision JSON")
    parser.add_argument("--as-of")
    args = parser.parse_args(argv)
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    decision = build_decision(payload, as_of=args.as_of)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0

