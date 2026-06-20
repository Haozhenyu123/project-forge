"""Decision pattern library: extract reusable patterns from project history.

As Project Forge is used across multiple projects, patterns emerge:
- "Most dashboard projects end up with Next.js + FastAPI"
- "CLI tools with offline requirements always pick node-ts"
These patterns serve as warm-start recommendations for new projects.
"""

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from project_forge.models import DecisionPattern


def _repo_root():
    return Path(__file__).resolve().parents[3]


def _pattern_library_path() -> Path:
    return _repo_root() / ".project-forge" / "patterns" / "decision-patterns.json"


def extract_patterns_from_history(history_dir: Optional[Path] = None) -> List[DecisionPattern]:
    """Scan all project histories and extract recurring decision patterns."""
    history_dir = history_dir or _repo_root() / ".project-forge" / "history"
    if not history_dir.is_dir():
        return []

    patterns: Dict[str, DecisionPattern] = {}

    for hist_file in sorted(history_dir.glob("*.json")):
        try:
            data = json.loads(hist_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        stack = data.get("selected_stack") or data.get("stack", "")
        goal = data.get("goal", "")
        creative = data.get("selected_direction", "")

        if not stack:
            continue

        # Build a pattern key from goal keywords
        keywords = _extract_keywords(goal)
        for kw in keywords:
            key = f"{kw}->{stack}"
            if key in patterns:
                patterns[key].usage_count += 1
                patterns[key].last_seen = date.today().isoformat()
            else:
                patterns[key] = DecisionPattern(
                    id=f"PAT-{kw}-{stack}",
                    name=f"{kw.title()} → {stack}",
                    trigger_conditions=[kw],
                    recommended_stack=stack,
                    confidence="low",
                    usage_count=1,
                    last_seen=date.today().isoformat(),
                )

    return sorted(patterns.values(), key=lambda p: p.usage_count, reverse=True)


def _extract_keywords(goal: str) -> List[str]:
    """Extract key domain words from a goal string."""
    domain_keywords = [
        "dashboard", "api", "cli", "extension", "desktop", "mobile",
        "realtime", "offline", "data", "ai", "automation", "workflow",
        "saas", "team", "collaboration", "planning", "monorepo",
        "frontend", "backend", "full-stack", "web", "content",
    ]
    lowered = goal.lower()
    return [kw for kw in domain_keywords if kw in lowered]


def save_patterns(patterns: List[DecisionPattern], output_path: Optional[Path] = None):
    """Persist extracted patterns to disk."""
    output_path = output_path or _pattern_library_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": 1,
        "updated_at": date.today().isoformat(),
        "patterns": [p.to_dict() for p in patterns],
    }
    output_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_patterns() -> List[DecisionPattern]:
    """Load saved patterns."""
    path = _pattern_library_path()
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [DecisionPattern(**p) for p in data.get("patterns", [])]


def recommend_from_patterns(goal: str, min_usage: int = 2) -> Optional[DecisionPattern]:
    """Recommend a stack based on matching patterns, if any confident match exists."""
    patterns = load_patterns()
    keywords = _extract_keywords(goal)
    for p in patterns:
        if p.usage_count >= min_usage and any(kw in p.trigger_conditions for kw in keywords):
            return p
    return None
