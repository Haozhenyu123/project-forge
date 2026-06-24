"""Loop state machine: legal transitions and guard conditions."""

from typing import Dict, Set, Tuple

from .models import LoopEpisode, LoopStatus


# Legal transitions: (from, to) pairs
TRANSITIONS: Set[Tuple[LoopStatus, LoopStatus]] = {
    (LoopStatus.IDLE, LoopStatus.COLLECTING),
    (LoopStatus.IDLE, LoopStatus.FAILED),
    (LoopStatus.COLLECTING, LoopStatus.EVALUATING),
    (LoopStatus.COLLECTING, LoopStatus.FAILED),
    (LoopStatus.EVALUATING, LoopStatus.REVISING),
    (LoopStatus.EVALUATING, LoopStatus.BLOCKED),
    (LoopStatus.EVALUATING, LoopStatus.FAILED),
    (LoopStatus.REVISING, LoopStatus.HANDOFF_READY),
    (LoopStatus.REVISING, LoopStatus.BLOCKED),
    (LoopStatus.REVISING, LoopStatus.FAILED),
    (LoopStatus.HANDOFF_READY, LoopStatus.AWAITING_FEEDBACK),
    (LoopStatus.HANDOFF_READY, LoopStatus.FAILED),
    (LoopStatus.AWAITING_FEEDBACK, LoopStatus.COLLECTING),
    (LoopStatus.AWAITING_FEEDBACK, LoopStatus.IDLE),
    (LoopStatus.AWAITING_FEEDBACK, LoopStatus.FAILED),
    # Blocked can transition to any state on resume
    (LoopStatus.BLOCKED, LoopStatus.COLLECTING),
    (LoopStatus.BLOCKED, LoopStatus.EVALUATING),
    (LoopStatus.BLOCKED, LoopStatus.IDLE),
    # Failed can be reset
    (LoopStatus.FAILED, LoopStatus.IDLE),
}


def can_transition(current: LoopStatus, target: LoopStatus) -> bool:
    """Check if a transition is legal."""
    return (current, target) in TRANSITIONS


def transition(
    episode: LoopEpisode, target: LoopStatus, reason: str = ""
) -> LoopEpisode:
    """Attempt to transition an episode to a new status. Raises ValueError if illegal."""
    if not can_transition(episode.status, target):
        raise ValueError(
            f"Illegal transition: {episode.status.value} -> {target.value}"
        )
    episode.status = target
    return episode


def next_action(episode: LoopEpisode) -> str:
    """Return the recommended next action based on current status."""
    status = episode.status

    if status == LoopStatus.IDLE:
        return "await_input"
    elif status == LoopStatus.COLLECTING:
        return "gather_signals"
    elif status == LoopStatus.EVALUATING:
        return "evaluate_impact"
    elif status == LoopStatus.REVISING:
        return "apply_revision"
    elif status == LoopStatus.HANDOFF_READY:
        return "generate_handoff"
    elif status == LoopStatus.AWAITING_FEEDBACK:
        return "await_feedback"
    elif status == LoopStatus.BLOCKED:
        return "needs_human"
    elif status == LoopStatus.FAILED:
        return "needs_recovery"

    return "unknown"
