"""Typed creative-decision records."""

from dataclasses import asdict, dataclass, field
from typing import Dict, List


@dataclass
class CreativeDirection:
    id: str
    name: str
    promise: str
    audience: str
    reason: str
    target_user_pain: str
    reachability: int
    differentiation: int
    value_signal: int
    validation_speed: int
    implementation_cost: int
    evidence_confidence: str
    evidence_ids: List[str] = field(default_factory=list)
    provisional: bool = True
    architecture_signals: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass
class CreativeDecision:
    goal: str
    selected_direction_id: str
    directions: List[CreativeDirection]
    created_at: str
    schema_version: int = 1
    assumptions: List[str] = field(default_factory=list)
    next_decision: str = "Confirm the selected direction before architecture is treated as accepted."

    def to_dict(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "goal": self.goal,
            "created_at": self.created_at,
            "selected_direction_id": self.selected_direction_id,
            "selected_direction": next(
                item.to_dict() for item in self.directions if item.id == self.selected_direction_id
            ),
            "directions": [item.to_dict() for item in self.directions],
            "assumptions": self.assumptions,
            "next_decision": self.next_decision,
        }

