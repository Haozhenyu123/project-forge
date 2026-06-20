"""Shared contract: valid architecture signals that Creative Director may emit and Architect must consume.

This contract ensures Creative Director output is machine-verifiable before the Architect uses it.
"""

from enum import Enum
from typing import Dict, FrozenSet, List


class ArchitectureSignal(str, Enum):
    """Signals that Creative Director attaches to each direction.

    The Architect MUST interpret every signal attached to the accepted direction.
    Unknown or missing signals result in lowered architectural confidence.
    """
    SMALL_SCOPE = "small-scope"
    SINGLE_PRIMARY_WORKFLOW = "single-primary-workflow"
    FAST_FEEDBACK = "fast-feedback"
    STATEFUL_GUIDANCE = "stateful-guidance"
    DECISION_HISTORY = "decision-history"
    HUMAN_READABLE_ARTIFACTS = "human-readable-artifacts"
    AUDITABILITY = "auditability"
    EVIDENCE_STORE = "evidence-store"
    MULTI_VIEW_COMPARISON = "multi-view-comparison"
    REAL_TIME = "real-time"
    OFFLINE_FIRST = "offline-first"
    MULTI_TENANT = "multi-tenant"
    EMBEDDABLE = "embeddable"


VALID_SIGNALS: FrozenSet[str] = frozenset(s.value for s in ArchitectureSignal)

# Signal → architecture implications (consumed by decision engine)
SIGNAL_IMPLICATIONS: Dict[str, List[str]] = {
    "small-scope": ["prefer-single-stack", "minimize-services", "fast-build-pipeline"],
    "single-primary-workflow": ["sequential-input-model", "linear-ci-pipeline"],
    "fast-feedback": ["hot-reload", "short-test-cycles", "quick-smoke"],
    "stateful-guidance": ["persistent-session", "decision-state-machine"],
    "decision-history": ["immutable-event-log", "audit-trail"],
    "human-readable-artifacts": ["markdown-output", "document-generation"],
    "auditability": ["immutable-records", "diffable-output", "provenance-tracking"],
    "evidence-store": ["structured-evidence-db", "normalization-pipeline"],
    "multi-view-comparison": ["parallel-comparison-ui", "weighted-scoring"],
    "real-time": ["websocket", "server-sent-events", "low-latency"],
    "offline-first": ["local-storage", "sync-engine", "conflict-resolution"],
    "multi-tenant": ["tenant-isolation", "row-level-security", "usage-metering"],
    "embeddable": ["library-api", "minimal-dependencies", "iframe-safe"],
}


def validate_creative_signals(direction_signals: List[str]) -> Dict[str, object]:
    """Validate that creative direction signals are recognized by the Architect."""
    recognized = [s for s in direction_signals if s in VALID_SIGNALS]
    unknown = [s for s in direction_signals if s not in VALID_SIGNALS]
    return {
        "valid": len(unknown) == 0,
        "recognized": recognized,
        "unknown": unknown,
        "implications": [SIGNAL_IMPLICATIONS.get(s, []) for s in recognized],
        "confidence_penalty": 0 if not unknown else 0.15 * len(unknown),
    }
