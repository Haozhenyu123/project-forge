"""Loop domain models: signals, state machine, strategy, episodes, iterations."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


# ── Loop Signal ────────────────────────────────────────────────

class SignalKind(str, Enum):
    VERIFICATION_FAILURE = "verification_failure"
    ARCHITECTURE_FEEDBACK = "architecture_feedback"
    CONSTRAINT_CHANGE = "constraint_change"
    EVIDENCE_EXPIRY = "evidence_expiry"
    SECURITY_ADVISORY = "security_advisory"
    LICENSE_CONFLICT = "license_conflict"
    SUPERPOWERS_FEEDBACK = "superpowers_feedback"
    MANUAL = "manual"


class SignalSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OwnerClassification(str, Enum):
    FORGE = "forge"
    SUPERPOWERS = "superpowers"
    HUMAN = "human"


@dataclass
class LoopSignal:
    signal_id: str
    source: str
    kind: SignalKind
    severity: SignalSeverity
    observed_at: str
    summary: str
    affected_constraints: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    verification_report: Optional[str] = None
    suggested_owner: Optional[OwnerClassification] = None
    artifact_refs: List[str] = field(default_factory=list)
    fingerprint: str = ""

    def __post_init__(self):
        if not self.fingerprint:
            self.fingerprint = self._compute_fingerprint()

    def _compute_fingerprint(self) -> str:
        import hashlib
        import json
        core = json.dumps(
            [self.signal_id, self.kind.value, self.source, self.summary],
            sort_keys=True,
        )
        return hashlib.sha256(core.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "source": self.source,
            "kind": self.kind.value,
            "severity": self.severity.value,
            "observed_at": self.observed_at,
            "summary": self.summary,
            "affected_constraints": self.affected_constraints,
            "evidence_refs": self.evidence_refs,
            "verification_report": self.verification_report,
            "suggested_owner": self.suggested_owner.value if self.suggested_owner else None,
            "artifact_refs": self.artifact_refs,
            "fingerprint": self.fingerprint,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoopSignal":
        return cls(
            signal_id=data["signal_id"],
            source=data.get("source", "unknown"),
            kind=SignalKind(data.get("kind", "manual")),
            severity=SignalSeverity(data.get("severity", "medium")),
            observed_at=data.get("observed_at", datetime.utcnow().isoformat()),
            summary=data.get("summary", ""),
            affected_constraints=data.get("affected_constraints", []),
            evidence_refs=data.get("evidence_refs", []),
            verification_report=data.get("verification_report"),
            suggested_owner=OwnerClassification(data["suggested_owner"])
            if data.get("suggested_owner")
            else None,
            artifact_refs=data.get("artifact_refs", []),
            fingerprint=data.get("fingerprint", ""),
        )


# ── Loop State Machine ────────────────────────────────────────

class LoopStatus(str, Enum):
    IDLE = "idle"
    COLLECTING = "collecting"
    EVALUATING = "evaluating"
    REVISING = "revising"
    HANDOFF_READY = "handoff_ready"
    AWAITING_FEEDBACK = "awaiting_feedback"
    BLOCKED = "blocked"
    FAILED = "failed"


# ── Loop Strategy / Policy ────────────────────────────────────

class ConfidenceTier(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CostTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class LoopPolicy:
    max_iterations: int = 3
    schedule: str = "weekly"
    allow_primary_stack_switch: bool = True
    switch_score_delta: int = 15
    minimum_confidence: ConfidenceTier = ConfidenceTier.MEDIUM
    minimum_independent_sources: int = 2
    allow_application_writes: bool = False
    execute_install_or_run: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_iterations": self.max_iterations,
            "schedule": self.schedule,
            "allow_primary_stack_switch": self.allow_primary_stack_switch,
            "switch_score_delta": self.switch_score_delta,
            "minimum_confidence": self.minimum_confidence.value,
            "minimum_independent_sources": self.minimum_independent_sources,
            "allow_application_writes": self.allow_application_writes,
            "execute_install_or_run": self.execute_install_or_run,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoopPolicy":
        return cls(
            max_iterations=data.get("max_iterations", 3),
            schedule=data.get("schedule", "weekly"),
            allow_primary_stack_switch=data.get("allow_primary_stack_switch", True),
            switch_score_delta=data.get("switch_score_delta", 15),
            minimum_confidence=ConfidenceTier(
                data.get("minimum_confidence", "medium")
            ),
            minimum_independent_sources=data.get("minimum_independent_sources", 2),
            allow_application_writes=data.get("allow_application_writes", False),
            execute_install_or_run=data.get("execute_install_or_run", False),
        )

    @classmethod
    def default(cls) -> "LoopPolicy":
        return cls()


# ── Episode & Iteration ───────────────────────────────────────

@dataclass
class LoopIteration:
    iteration_id: str
    index: int
    signal: LoopSignal
    decision_hash: str
    action: str  # revise, reroute, blocked, human_packet
    summary: str
    revision_changes: List[str] = field(default_factory=list)
    new_handoff: bool = False
    started_at: str = ""
    completed_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration_id": self.iteration_id,
            "index": self.index,
            "signal": self.signal.to_dict(),
            "decision_hash": self.decision_hash,
            "action": self.action,
            "summary": self.summary,
            "revision_changes": self.revision_changes,
            "new_handoff": self.new_handoff,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoopIteration":
        return cls(
            iteration_id=data["iteration_id"],
            index=data.get("index", 0),
            signal=LoopSignal.from_dict(data["signal"]),
            decision_hash=data.get("decision_hash", ""),
            action=data.get("action", ""),
            summary=data.get("summary", ""),
            revision_changes=data.get("revision_changes", []),
            new_handoff=data.get("new_handoff", False),
            started_at=data.get("started_at", ""),
            completed_at=data.get("completed_at", ""),
        )


@dataclass
class LoopEpisode:
    episode_id: str
    slug: str
    root_cause: str
    status: LoopStatus = LoopStatus.IDLE
    iterations: List[LoopIteration] = field(default_factory=list)
    signals: List[str] = field(default_factory=list)  # fingerprint set
    policy: LoopPolicy = field(default_factory=LoopPolicy.default)
    created_at: str = ""
    updated_at: str = ""

    @property
    def current_iteration(self) -> int:
        return len(self.iterations) + 1

    @property
    def latest_decision_hash(self) -> Optional[str]:
        if not self.iterations:
            return None
        return self.iterations[-1].decision_hash

    @property
    def has_stale_progress(self) -> bool:
        if len(self.iterations) < 2:
            return False
        last_two = self.iterations[-2:]
        return (
            last_two[0].decision_hash == last_two[1].decision_hash
            and last_two[1].action != "reroute"
        )

    @property
    def is_exhausted(self) -> bool:
        return len(self.iterations) >= self.policy.max_iterations

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "slug": self.slug,
            "root_cause": self.root_cause,
            "status": self.status.value,
            "iterations": [it.to_dict() for it in self.iterations],
            "signals": self.signals,
            "policy": self.policy.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoopEpisode":
        return cls(
            episode_id=data["episode_id"],
            slug=data.get("slug", ""),
            root_cause=data.get("root_cause", ""),
            status=LoopStatus(data.get("status", "idle")),
            iterations=[
                LoopIteration.from_dict(it)
                for it in data.get("iterations", [])
            ],
            signals=data.get("signals", []),
            policy=LoopPolicy.from_dict(data.get("policy", {})),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


# ── Human Decision Packet ─────────────────────────────────────

@dataclass
class HumanDecisionPacket:
    episode_id: str
    generated_at: str
    conflict_summary: str
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    evidence_summary: List[Dict[str, Any]] = field(default_factory=list)
    must_decide: List[str] = field(default_factory=list)
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "generated_at": self.generated_at,
            "conflict_summary": self.conflict_summary,
            "candidates": self.candidates,
            "evidence_summary": self.evidence_summary,
            "must_decide": self.must_decide,
            "recommendation": self.recommendation,
        }


# ── Loop Run Result ───────────────────────────────────────────

@dataclass
class LoopRunResult:
    episode_id: str
    status: LoopStatus
    iteration: int
    action: str
    decision_hash: str
    revision_applied: bool
    new_handoff: bool
    summary: str
    report_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "status": self.status.value,
            "iteration": self.iteration,
            "action": self.action,
            "decision_hash": self.decision_hash,
            "revision_applied": self.revision_applied,
            "new_handoff": self.new_handoff,
            "summary": self.summary,
            "report_path": self.report_path,
        }
