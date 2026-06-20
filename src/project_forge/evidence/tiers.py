"""Evidence quality tiering for weighted scoring.

Different evidence sources carry different weight. Official docs matter more than
low-star GitHub repos. This module assigns tier weights and provides an API for
the scoring engine.
"""

from .models import SourceQuality


# Tier weights: higher tier = more weight in scoring
QUALITY_TIER_WEIGHT: dict = {
    SourceQuality.PRIMARY: 1.0,               # Official docs, vendor specs
    SourceQuality.REGISTRY_METADATA: 0.9,      # npm/PyPI registry data
    SourceQuality.REPOSITORY_METADATA: 0.7,    # GitHub repo metadata
    SourceQuality.SECONDARY: 0.5,              # Blog posts, tutorials, community
    SourceQuality.UNVERIFIED: 0.2,             # Unknown sources, host-tool placeholder
}

# Additional ranking signals within the same tier
REPOSITORY_STAR_THRESHOLDS = [
    (10000, 1.0),
    (1000, 0.85),
    (100, 0.7),
    (10, 0.5),
    (0, 0.3),
]

DATEDNESS_PENALTY = {
    "current": 1.0,
    "aging": 0.8,
    "stale": 0.4,
    "unknown": 0.5,
}


def evidence_weight(row, adjust_for_stars=True, adjust_for_freshness=True):
    """Compute a composite weight for a single evidence row (0.0-1.0)."""
    quality = row.get("source_quality", "unverified")
    try:
        quality = SourceQuality(quality)
    except ValueError:
        quality = SourceQuality.UNVERIFIED

    base = QUALITY_TIER_WEIGHT.get(quality, 0.2)

    # Star-based adjustment for repository metadata
    if adjust_for_stars and quality == SourceQuality.REPOSITORY_METADATA:
        stars = int(row.get("stars", 0) or 0)
        star_mult = 0.5
        for threshold, multiplier in REPOSITORY_STAR_THRESHOLDS:
            if stars >= threshold:
                star_mult = multiplier
                break
        base *= star_mult

    # Freshness penalty
    if adjust_for_freshness:
        freshness = row.get("freshness", "unknown")
        base *= DATEDNESS_PENALTY.get(freshness, 0.5)

    return round(base, 3)


def weighted_evidence_score(rows, adjust_for_stars=True, adjust_for_freshness=True):
    """Compute an aggregate evidence quality score for a set of rows."""
    if not rows:
        return 0.0
    weights = [evidence_weight(r, adjust_for_stars, adjust_for_freshness) for r in rows]
    return round(sum(weights) / max(1, len(weights)), 3)


def evidence_quality_summary(rows):
    """Produce a human-readable summary of evidence quality."""
    tiers: dict = {}
    for row in rows:
        quality = str(row.get("source_quality", "unverified"))
        tiers.setdefault(quality, 0)
        tiers[quality] += 1

    weighted = weighted_evidence_score(rows)
    provisional_count = sum(1 for r in rows if r.get("provisional"))

    return {
        "total": len(rows),
        "by_tier": tiers,
        "weighted_score": weighted,
        "provisional_count": provisional_count,
        "provisional_ratio": round(provisional_count / max(1, len(rows)), 2),
        "grade": _grade(weighted),
    }


def _grade(score):
    if score >= 0.8: return "A"
    if score >= 0.6: return "B"
    if score >= 0.4: return "C"
    if score >= 0.2: return "D"
    return "F"
