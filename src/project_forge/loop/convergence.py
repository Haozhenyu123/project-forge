"""Convergence detection: determine when a loop has converged, stalled, or exhausted."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import (
    ConfidenceTier,
    HumanDecisionPacket,
    LoopEpisode,
    LoopIteration,
    LoopPolicy,
    LoopSignal,
    LoopStatus,
)


def check_convergence(
    episode: LoopEpisode,
    current_signal: LoopSignal,
    decision_hash: str,
) -> Dict[str, Any]:
    """Check whether the episode has converged or needs escalation."""
    result: Dict[str, Any] = {
        "converged": False,
        "blocked": False,
        "exhausted": False,
        "action": "continue",
        "reason": "",
    }
    # Check stale progress: two consecutive same-hash iterations
    if episode.has_stale_progress:
        result["blocked"] = True
        result["action"] = "blocked"
        result["reason"] = (
            "Two consecutive iterations produced the same decision hash "
            "without rerouting — loop is stuck."
        )
        return result
    # Check exhaustion
    if episode.is_exhausted:
        result["exhausted"] = True
        result["action"] = "human_packet"
        result["reason"] = (
            f"Maximum iterations ({episode.policy.max_iterations}) reached "
            "without convergence."
        )
        return result
    # Check: if last iteration was a revision that produced a handoff, we are in feedback loop
    if episode.iterations:
        last = episode.iterations[-1]
        if last.new_handoff and last.action in ("revise", "human_packet"):
            result["converged"] = False
            result["action"] = "await_feedback"
            result["reason"] = "Handoff generated, awaiting Superpowers feedback."
            return result
    result["action"] = "continue"
    result["reason"] = "Proceeding with evaluation."
    return result


def generate_human_packet(
    episode: LoopEpisode,
    candidates: List[Dict[str, Any]],
    evidence: List[Dict[str, Any]],
) -> HumanDecisionPacket:
    """Generate a Human Decision Packet when the loop exhausts without convergence."""
    conflict_lines = []
    for it in episode.iterations:
        conflict_lines.append(
            f"- Iteration {it.index}: {it.action} — {it.summary}"
        )
    must_decide = []
    if episode.has_stale_progress:
        must_decide.append(
            "Two consecutive iterations produced the same decision hash. "
            "Should Project Forge force a stack switch or accept the current architecture?"
        )
    if episode.is_exhausted:
        must_decide.append(
            f"The loop exhausted after {len(episode.iterations)} iterations. "
            "Choose one of the candidate architectures or accept manual intervention."
        )
    if not must_decide:
        must_decide.append("Review the following candidates and evidence, then decide.")
    # Recommend the highest-scored candidate still available
    recommendation = ""
    if candidates:
        top = candidates[0]
        recommendation = (
            f"Recommended: {top.get('stack', top.get('id', 'unknown'))} "
            f"(score: {top.get('score', 'N/A')}) — {top.get('reason', '')}"
        )
    return HumanDecisionPacket(
        episode_id=episode.episode_id,
        generated_at=datetime.utcnow().isoformat(),
        conflict_summary="\n".join(conflict_lines),
        candidates=candidates,
        evidence_summary=[
            {"id": e.get("evidence_id", ""),
             "title": e.get("title", ""),
             "provisional": e.get("provisional", False)}
            for e in (evidence or [])[:8]
        ],
        must_decide=must_decide,
        recommendation=recommendation,
    )
