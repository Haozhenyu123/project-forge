"""Explainable architecture scoring with evidence lineage per dimension."""

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Iterable, List, Sequence, Set

from project_forge.evidence.normalize import normalize_records, parse_day

from .catalog import StackDefinition


DIMENSIONS = (
    "constraint_fit", "evidence_freshness", "source_diversity", "maintenance_activity",
    "license", "security_risk", "deployment_cost", "complexity", "harness_availability",
)


@dataclass
class DimensionScore:
    score: int
    weight: float
    evidence_ids: List[str]
    provisional: bool
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "weight": self.weight,
            "evidence_ids": self.evidence_ids,
            "provisional": self.provisional,
            "rationale": self.rationale,
        }


def evidence_for_stack(rows: Iterable[Dict[str, Any]], stack: StackDefinition) -> List[Dict[str, Any]]:
    aliases = {stack.id.lower(), stack.name.lower(), *stack.aliases}
    matched = []
    for row in rows:
        text = " ".join(str(row.get(key, "")) for key in ("title", "summary", "description", "url", "source")).lower()
        explicit = {str(item).lower() for item in row.get("evidence_for", [])}
        if stack.id.lower() in explicit or any(alias in text for alias in aliases):
            matched.append(row)
    return matched


def score_stack(
    stack: StackDefinition,
    desired: Set[str],
    evidence: Sequence[Dict[str, Any]],
    weights: Dict[str, float],
    as_of: str,
) -> Dict[str, Any]:
    normalized = normalize_records(evidence, as_of=as_of)
    matched = evidence_for_stack(normalized, stack)
    external_ids = [str(row["evidence_id"]) for row in matched if not row.get("provisional")]
    dimensions = {
        "constraint_fit": _fit(stack, desired, weights),
        "evidence_freshness": _freshness(matched, weights, as_of),
        "source_diversity": _diversity(matched, weights),
        "maintenance_activity": _baseline_with_signal(stack, matched, weights, "maintenance_activity"),
        "license": _license(stack, matched, weights),
        "security_risk": _security(stack, matched, weights),
        "deployment_cost": _baseline(stack, weights, "deployment_cost"),
        "complexity": _baseline(stack, weights, "complexity"),
        "harness_availability": _harness(stack, weights),
    }
    total = round(sum(value.score * value.weight for value in dimensions.values()), 2)
    return {
        "total": total,
        "dimensions": {key: value.to_dict() for key, value in dimensions.items()},
        "evidence_ids": sorted(set(external_ids)),
        **_legacy_fields(dimensions),
    }


def _dimension(score: int, weight: float, ids: List[str], provisional: bool, rationale: str) -> DimensionScore:
    return DimensionScore(max(0, min(100, round(score))), weight, sorted(set(ids)), provisional, rationale)


def _fit(stack: StackDefinition, desired: Set[str], weights: Dict[str, float]) -> DimensionScore:
    score = round(100 * len(desired & stack.capabilities) / max(1, len(desired)))
    ids = stack.source_ids("harness_availability")
    return _dimension(score, weights["constraint_fit"], ids, False, f"Matches {len(desired & stack.capabilities)} of {len(desired)} required capabilities.")


def _freshness(rows: List[Dict[str, Any]], weights: Dict[str, float], as_of: str) -> DimensionScore:
    dated = [(parse_day(row.get("observed_at")), row) for row in rows if not row.get("provisional")]
    dated = [(day, row) for day, row in dated if day]
    if not dated:
        return _dimension(0, weights["evidence_freshness"], [], True, "No dated external evidence matched this candidate.")
    current = parse_day(as_of) or date.today()
    newest = max(day for day, _ in dated)
    age = max(0, (current - newest).days)
    score = 100 if age <= 90 else 75 if age <= 365 else 35 if age <= 540 else 10
    ids = [row["evidence_id"] for _, row in dated]
    return _dimension(score, weights["evidence_freshness"], ids, False, f"Newest matched evidence is {age} days old.")


def _diversity(rows: List[Dict[str, Any]], weights: Dict[str, float]) -> DimensionScore:
    verified = [row for row in rows if not row.get("provisional")]
    sources = {str(row.get("source")) for row in verified if row.get("source")}
    score = min(100, len(sources) * 40)
    return _dimension(score, weights["source_diversity"], [row["evidence_id"] for row in verified], not verified, f"Matched {len(sources)} independent source types.")


def _baseline(stack: StackDefinition, weights: Dict[str, float], name: str) -> DimensionScore:
    ids = stack.source_ids(name)
    return _dimension(stack.baselines.get(name, 50), weights[name], ids, not bool(ids), "Versioned catalog baseline; refresh when project constraints change.")


def _baseline_with_signal(stack: StackDefinition, rows: List[Dict[str, Any]], weights: Dict[str, float], name: str) -> DimensionScore:
    baseline = stack.baselines.get(name, 50)
    verified = [row for row in rows if not row.get("provisional")]
    active = [row for row in verified if row.get("archived") is False or row.get("updated_at")]
    score = round(baseline * 0.7 + (90 if active else baseline) * 0.3)
    ids = stack.source_ids(name) + [row["evidence_id"] for row in active]
    return _dimension(score, weights[name], ids, not bool(verified), "Catalog baseline adjusted by matched maintenance metadata.")


def _license(stack: StackDefinition, rows: List[Dict[str, Any]], weights: Dict[str, float]) -> DimensionScore:
    verified = [row for row in rows if not row.get("provisional") and row.get("license")]
    restrictive = {"AGPL-3.0", "GPL-3.0", "SSPL-1.0", "BUSL-1.1"}
    score = stack.baselines.get("license", 50)
    if verified:
        score = min(score, 45) if any(str(row["license"]).upper() in restrictive for row in verified) else max(score, 85)
    ids = stack.source_ids("license") + [row["evidence_id"] for row in verified]
    return _dimension(score, weights["license"], ids, not bool(verified), "License metadata checked when available; catalog baseline otherwise.")


def _security(stack: StackDefinition, rows: List[Dict[str, Any]], weights: Dict[str, float]) -> DimensionScore:
    advisories = [row for row in rows if row.get("source") == "osv" and not row.get("provisional")]
    score = stack.baselines.get("security_risk", 50)
    if advisories:
        count = sum(int(row.get("vulnerability_count", 0)) for row in advisories)
        score = max(0, 100 - count * 12)
    ids = stack.source_ids("security_risk") + [row["evidence_id"] for row in advisories]
    return _dimension(score, weights["security_risk"], ids, not bool(advisories), "OSV advisory count adjusts the catalog risk baseline when present.")


def _harness(stack: StackDefinition, weights: Dict[str, float]) -> DimensionScore:
    primary = bool(stack.harness.get("primary"))
    ids = stack.source_ids("harness_availability")
    return _dimension(100 if primary else 0, weights["harness_availability"], ids, False, "First-class Project Forge harness coverage.")


def _legacy_fields(dimensions: Dict[str, DimensionScore]) -> Dict[str, int]:
    return {
        "fit": dimensions["constraint_fit"].score,
        "evidence_freshness": dimensions["evidence_freshness"].score,
        "source_diversity": dimensions["source_diversity"].score,
        "maintenance": dimensions["maintenance_activity"].score,
        "complexity": dimensions["complexity"].score,
        "harness_availability": dimensions["harness_availability"].score,
        "maturity": dimensions["maintenance_activity"].score,
    }
