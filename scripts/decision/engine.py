#!/usr/bin/env python3
"""Deterministic product-direction and architecture decision engine."""

import argparse
import json
from datetime import date, datetime
from pathlib import Path


KNOWN_STACKS = [
    {
        "id": "nextjs",
        "name": "Next.js",
        "capabilities": {"web", "dashboard", "typescript", "frontend", "content"},
        "maintenance": 88,
        "complexity": 58,
        "maturity_months": 120,
        "harness": {"primary": "nextjs", "secondary": []},
        "aliases": ["next", "next.js", "react"],
    },
    {
        "id": "fastapi",
        "name": "FastAPI",
        "capabilities": {"api", "backend", "python", "rest", "openapi", "ai"},
        "maintenance": 84,
        "complexity": 42,
        "maturity_months": 90,
        "harness": {"primary": "fastapi", "secondary": []},
        "aliases": ["fastapi", "python api"],
    },
    {
        "id": "node-ts",
        "name": "Node.js + TypeScript",
        "capabilities": {"web", "api", "typescript", "cli", "realtime", "backend"},
        "maintenance": 82,
        "complexity": 45,
        "maturity_months": 180,
        "harness": {"primary": "node-ts", "secondary": []},
        "aliases": ["node", "typescript", "node.js"],
    },
    {
        "id": "python",
        "name": "Python",
        "capabilities": {"python", "cli", "automation", "data", "ai"},
        "maintenance": 86,
        "complexity": 35,
        "maturity_months": 300,
        "harness": {"primary": "python", "secondary": []},
        "aliases": ["python"],
    },
    {
        "id": "chrome-extension",
        "name": "Chrome Extension MV3",
        "capabilities": {"extension", "browser", "typescript", "web"},
        "maintenance": 74,
        "complexity": 54,
        "maturity_months": 96,
        "harness": {"primary": "chrome-extension", "secondary": []},
        "aliases": ["chrome", "extension", "manifest v3"],
    },
    {
        "id": "nextjs-fastapi",
        "name": "Next.js + FastAPI",
        "capabilities": {
            "web",
            "dashboard",
            "typescript",
            "frontend",
            "api",
            "backend",
            "python",
            "rest",
        },
        "maintenance": 86,
        "complexity": 72,
        "maturity_months": 80,
        "harness": {"primary": "nextjs", "secondary": ["fastapi"]},
        "aliases": ["nextjs fastapi", "next.js fastapi", "typescript frontend python backend"],
    },
]


def words(value):
    return {
        token.strip(".,:;()[]{}").lower()
        for token in str(value).replace("-", " ").replace("/", " ").split()
        if token.strip(".,:;()[]{}")
    }


def flatten_payload(payload):
    pieces = [payload.get("goal", "")]
    pieces.extend(payload.get("constraints", []) or [])
    brief = payload.get("creative_brief", {}) or {}
    if isinstance(brief, dict):
        pieces.extend(str(value) for value in brief.values())
    else:
        pieces.append(str(brief))
    return " ".join(pieces).lower()


def parse_date(value):
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None


def age_days(observed_at, as_of):
    observed = parse_date(observed_at)
    current = parse_date(as_of)
    if not observed or not current:
        return 9999
    return max(0, (current - observed).days)


def evidence_for_stack(evidence, stack):
    aliases = {stack["id"], stack["name"].lower(), *stack.get("aliases", [])}
    matched = []
    for row in evidence:
        text = " ".join(
            str(row.get(key, ""))
            for key in ("title", "summary", "description", "url", "source")
        ).lower()
        if any(alias.lower() in text for alias in aliases):
            matched.append(row)
    return matched


def product_directions(payload):
    goal = payload.get("goal") or "Untitled project"
    context = flatten_payload(payload)
    directions = [
        {
            "id": "focused-mvp",
            "name": "Focused MVP",
            "promise": f"Deliver the smallest useful version of: {goal}",
            "audience": "the most constrained first user group",
            "reason": "lowest scope risk and fastest validation",
        },
        {
            "id": "guided-workflow",
            "name": "Guided Workflow",
            "promise": "Turn the problem into a step-by-step user journey",
            "audience": "users who need clarity more than customization",
            "reason": "best when the idea is vague or the workflow is new",
        },
        {
            "id": "evidence-dashboard",
            "name": "Evidence Dashboard",
            "promise": "Make decisions visible, comparable, and auditable",
            "audience": "teams that need shared confidence before implementation",
            "reason": "best when stakeholders must compare options",
        },
    ]
    selected = "evidence-dashboard" if "team" in context or "dashboard" in context else "focused-mvp"
    return directions, next(item for item in directions if item["id"] == selected)


def detect_conflicts(payload):
    context = flatten_payload(payload)
    conflicts = []
    if "offline" in context and "instant sync" in context and "no server" in context:
        conflicts.append(
            {
                "id": "offline-sync-no-server",
                "constraints": ["offline-first", "instant sync", "no server"],
                "resolution": "Choose either local-first with later sync or server-backed sync.",
            }
        )
    return conflicts


def desired_capabilities(payload):
    context = flatten_payload(payload)
    caps = set()
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
    }
    for needle, cap in mapping.items():
        if needle in context:
            caps.add(cap)
    if not caps:
        caps.update({"web", "api"})
    return caps


def source_diversity(rows):
    return len({row.get("source") for row in rows if row.get("source")})


def freshness_score(rows, as_of):
    if not rows:
        return 0
    newest_age = min(age_days(row.get("observed_at"), as_of) for row in rows)
    if newest_age <= 90:
        return 100
    if newest_age <= 365:
        return 75
    if newest_age <= 540:
        return 50
    return 20


def score_stack(stack, payload, as_of):
    evidence = payload.get("evidence", []) or []
    caps = desired_capabilities(payload)
    matched = evidence_for_stack(evidence, stack)
    fit = round(100 * len(caps & set(stack["capabilities"])) / max(1, len(caps)))
    fresh = freshness_score(matched, as_of)
    diversity = min(100, source_diversity(matched) * 40)
    maintenance = int(stack.get("maintenance", 50))
    complexity = max(0, 100 - int(stack.get("complexity", 50)))
    harness = 100 if stack.get("harness", {}).get("primary") else 0
    maturity = 100 if int(stack.get("maturity_months", 0)) >= 18 else 20
    total = round(
        fit * 0.30
        + fresh * 0.18
        + diversity * 0.12
        + maintenance * 0.15
        + complexity * 0.12
        + harness * 0.08
        + maturity * 0.05,
        2,
    )
    return {
        "fit": fit,
        "evidence_freshness": fresh,
        "source_diversity": diversity,
        "maintenance": maintenance,
        "complexity": complexity,
        "harness_availability": harness,
        "maturity": maturity,
        "total": total,
    }


def stack_pool(payload):
    custom = payload.get("candidate_stacks")
    if custom:
        converted = []
        for item in custom:
            converted.append(
                {
                    "id": item.get("id") or item.get("name", "custom").lower(),
                    "name": item.get("name") or item.get("id") or "Custom",
                    "capabilities": set(item.get("capabilities", [])),
                    "maintenance": item.get("maintenance", 50),
                    "complexity": item.get("complexity", 50),
                    "maturity_months": item.get("maturity_months", 0),
                    "harness": {
                        "primary": (item.get("harnesses") or [""])[0],
                        "secondary": [],
                    },
                    "aliases": item.get("aliases", []),
                }
            )
        return KNOWN_STACKS + converted
    return KNOWN_STACKS


def architecture_candidates(payload, as_of, limit=True):
    scored = []
    context = flatten_payload(payload)
    for stack in stack_pool(payload):
        scores = score_stack(stack, payload, as_of)
        if int(stack.get("maturity_months", 0)) < 18:
            scores["total"] = round(scores["total"] * 0.45, 2)
        if (
            stack["id"] == "nextjs-fastapi"
            and "frontend" in context
            and "backend" in context
        ):
            scores["total"] = round(scores["total"] + 18, 2)
        reasons = []
        if int(stack.get("maturity_months", 0)) < 18:
            reasons.append("maturity is too low for a default recommendation")
        if scores["source_diversity"] < 40:
            reasons.append("evidence diversity is weak")
        scored.append(
            {
                "id": stack["id"],
                "name": stack["name"],
                "score": scores["total"],
                "scores": scores,
                "harness": stack["harness"],
                "reason": f"Fit {scores['fit']} with harness {stack['harness']['primary']}",
                "reasons": reasons,
                "handoff": {
                    "architecture_mode": "multi-stack"
                    if stack["harness"].get("secondary")
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
        )
    scored.sort(key=lambda item: item["score"], reverse=True)
    if not limit:
        return scored
    # Keep the visible ADR set focused. Full rejected options are still retained.
    return scored[:3]


def confidence(candidates, evidence, conflicts):
    if conflicts:
        return "Low"
    if not evidence:
        return "Low"
    selected = candidates[0]
    if selected["scores"]["evidence_freshness"] >= 75 and selected["scores"]["source_diversity"] >= 80:
        return "High"
    if selected["scores"]["evidence_freshness"] >= 50:
        return "Medium"
    return "Low"


def revisit_triggers(candidates, conflicts):
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


def build_decision(payload, as_of=None):
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
        "schema_version": 1,
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
            "reason": "based on constraint fit, evidence freshness, source diversity, maturity, and harness availability",
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input project brief JSON")
    parser.add_argument("--out", required=True, help="Output decision JSON")
    parser.add_argument("--as-of")
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    decision = build_decision(payload, as_of=args.as_of)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
