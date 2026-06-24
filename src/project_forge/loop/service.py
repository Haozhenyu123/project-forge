"""Loop service: main orchestration for the Decision Loop Engine."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    LoopEpisode,
    LoopIteration,
    LoopPolicy,
    LoopRunResult,
    LoopSignal,
    LoopStatus,
    SignalKind,
)
from .signals import classify_owner, deduplicate_signals, is_duplicate, validate_signal, OwnerClassification
from .state_machine import can_transition, next_action, transition
from .impact import compute_decision_hash, impact_summary
from .convergence import check_convergence, generate_human_packet
from .strategy import evaluate_switch, classify_migration_cost, evaluate_confidence
from .storage import (
    backup_file,
    ensure_dirs,
    ingest_signal_to_inbox,
    list_inbox,
    load_state,
    move_to_processed,
    save_iteration,
    save_state,
    rollback_state,
)
from .report import save_report


def load_policy(project_dir: Path) -> LoopPolicy:
    """Load loop policy from project-forge.yaml, falling back to defaults."""
    contract_path = project_dir / "project-forge.yaml"
    if not contract_path.is_file():
        return LoopPolicy.default()
    try:
        from project_forge.contract import load_payload
        payload = load_payload(contract_path)
        loop_config = payload.get("loop") or {}
        if loop_config:
            return LoopPolicy.from_dict(loop_config)
    except Exception:
        pass
    return LoopPolicy.default()


def ingest_signal(project_dir: str, signal_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and ingest a single loop signal. Returns result dict."""
    project = Path(project_dir)
    errors = validate_signal(signal_data)
    if errors:
        return {"status": "invalid", "errors": errors}
    signal = LoopSignal.from_dict(signal_data)
    owner = classify_owner(signal)
    # Check for duplicates
    state = load_state(project)
    known_fps = state.signals if state else []
    fp = signal.fingerprint
    if is_duplicate(signal, known_fps):
        return {
            "status": "duplicate",
            "signal_id": signal.signal_id,
            "fingerprint": fp,
            "owner": owner.value,
            "message": "Signal already processed.",
        }
    ingest_signal_to_inbox(project, signal)
    return {
        "status": "ingested",
        "signal_id": signal.signal_id,
        "fingerprint": fp,
        "owner": owner.value,
        "kind": signal.kind.value,
    }


def run_loop(
    project_dir: str,
    slug: str,
    json_output: bool = False,
) -> Dict[str, Any]:
    """Execute one iteration of the decision loop."""
    project = Path(project_dir)
    policy = load_policy(project)
    state = load_state(project) or _create_episode(project, slug, policy)
    dirs = ensure_dirs(project)
    # Collect signals from inbox
    inbox_signals = list_inbox(project)
    if not inbox_signals and state.status == LoopStatus.IDLE:
        return {
            "status": "idle",
            "message": "No signals in inbox. Loop is idle.",
            "episode_id": state.episode_id,
        }
    # Deduplicate
    new_signals = deduplicate_signals(inbox_signals, state.signals)
    if not new_signals:
        return {
            "status": "idle",
            "message": "All inbox signals have been processed.",
            "episode_id": state.episode_id,
        }
    # Transition to collecting if idle or awaiting feedback
    if state.status in {LoopStatus.IDLE, LoopStatus.AWAITING_FEEDBACK}:
        state = transition(state, LoopStatus.COLLECTING)
    # Route each signal
    routed_forge = []
    routed_sp = []
    routed_human = []
    for signal in new_signals:
        owner = classify_owner(signal)
        if owner == OwnerClassification.FORGE:
            routed_forge.append(signal)
        elif owner == OwnerClassification.SUPERPOWERS:
            routed_sp.append(signal)
        else:
            routed_human.append(signal)
        move_to_processed(project, signal)
        state.signals.append(signal.fingerprint)
    # Determine primary signal for this iteration (highest severity forge signal)
    primary_signal = None
    if routed_forge:
        primary_signal = max(
            routed_forge, key=lambda s: _severity_rank(s)
        )
    elif routed_human:
        primary_signal = routed_human[0]
    elif routed_sp:
        # Route to superpowers — no forge revision needed
        state.status = LoopStatus.AWAITING_FEEDBACK
        save_state(project, state)
        save_report(state, project)
        return {
            "status": "rerouted",
            "message": f"{len(routed_sp)} signal(s) routed to Superpowers.",
            "episode_id": state.episode_id,
            "signals_count": len(routed_sp),
        }
    else:
        save_state(project, state)
        return {
            "status": state.status.value,
            "message": "No actionable signals for this run.",
            "episode_id": state.episode_id,
        }
    # Evaluate
    if state.status != LoopStatus.EVALUATING:
        state = transition(state, LoopStatus.EVALUATING)
    decision_hash = compute_decision_hash(project)
    impact = impact_summary(primary_signal, project)
    # Convergence check
    convergence = check_convergence(state, primary_signal, decision_hash)
    if convergence["action"] == "blocked":
        state.status = LoopStatus.BLOCKED
        iteration = _record_iteration(state, primary_signal, decision_hash, "blocked",
                                       convergence["reason"])
        save_state(project, state)
        save_iteration(project, state.episode_id, iteration)
        save_report(state, project)
        return LoopRunResult(
            episode_id=state.episode_id, status=LoopStatus.BLOCKED,
            iteration=iteration.index, action="blocked",
            decision_hash=decision_hash,
            revision_applied=False, new_handoff=False,
            summary=convergence["reason"],
            report_path=str(Path("docs") / "loop" / f"LOOP-{state.episode_id}.md"),
        ).to_dict()
    if convergence["action"] == "human_packet":
        # Generate human decision packet
        packet = _build_human_packet(state, project, primary_signal)
        iteration = _record_iteration(state, primary_signal, decision_hash, "human_packet",
                                       "Human Decision Packet generated: " + packet.conflict_summary[:120])
        state.status = LoopStatus.BLOCKED
        # Save packet
        packet_path = dirs["runs"] / state.episode_id / f"human-packet-{iteration.iteration_id}.json"
        packet_path.write_text(json.dumps(packet.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        save_state(project, state)
        save_iteration(project, state.episode_id, iteration)
        save_report(state, project)
        return LoopRunResult(
            episode_id=state.episode_id, status=LoopStatus.BLOCKED,
            iteration=iteration.index, action="human_packet",
            decision_hash=decision_hash,
            revision_applied=False, new_handoff=False,
            summary="Human Decision Packet generated — loop exhausted.",
            report_path=str(Path("docs") / "loop" / f"LOOP-{state.episode_id}.md"),
        ).to_dict()
    # Revise
    state = transition(state, LoopStatus.REVISING)
    revision_result = _apply_revision(project, slug, primary_signal, impact, state.policy)
    decision_hash_after = compute_decision_hash(project)
    iteration = _record_iteration(
        state, primary_signal, decision_hash_after,
        "revise", impact["reason"],
        revision_changes=revision_result.get("changes", []),
        new_handoff=revision_result.get("handoff_generated", False),
    )
    # Handoff ready
    state = transition(state, LoopStatus.HANDOFF_READY)
    # Generate new handoff if needed
    if revision_result.get("handoff_generated") or not revision_result.get("handoff_generated", True):
        try:
            from project_forge.handoff.service import export_handoff
            export_handoff(project, slug)
            iteration.new_handoff = True
        except Exception as exc:
            iteration.summary += f" (handoff export failed: {exc})"
    # Awaiting feedback
    state = transition(state, LoopStatus.AWAITING_FEEDBACK)
    save_state(project, state)
    save_iteration(project, state.episode_id, iteration)
    save_report(state, project)
    return LoopRunResult(
        episode_id=state.episode_id, status=state.status,
        iteration=iteration.index, action="revise",
        decision_hash=decision_hash_after,
        revision_applied=True,
        new_handoff=iteration.new_handoff,
        summary=iteration.summary,
        report_path=str(Path("docs") / "loop" / f"LOOP-{state.episode_id}.md"),
    ).to_dict()


def resume_loop(project_dir: str, reason: str = "") -> Dict[str, Any]:
    """Resume a blocked or failed loop episode."""
    project = Path(project_dir)
    state = load_state(project)
    if state is None:
        return {"status": "error", "message": "No active loop state found."}
    if state.status not in {LoopStatus.BLOCKED, LoopStatus.FAILED}:
        return {
            "status": "error",
            "message": f"Loop is not blocked or failed. Current status: {state.status.value}.",
        }
    # Transition to collecting to restart the feedback loop
    state = transition(state, LoopStatus.COLLECTING, reason)
    state.root_cause = state.root_cause or reason
    state.updated_at = datetime.utcnow().isoformat()
    save_state(project, state)
    save_report(state, project)
    return {
        "status": "resumed",
        "episode_id": state.episode_id,
        "new_status": LoopStatus.COLLECTING.value,
        "reason": reason,
    }


def get_loop_status(project_dir: str) -> Dict[str, Any]:
    """Return current loop status."""
    project = Path(project_dir)
    state = load_state(project)
    if state is None:
        return {"status": "no_loop", "message": "No loop state exists."}
    return {
        "status": state.status.value,
        "episode_id": state.episode_id,
        "slug": state.slug,
        "root_cause": state.root_cause,
        "iterations": len(state.iterations),
        "signals_processed": len(state.signals),
        "policy": state.policy.to_dict(),
        "created_at": state.created_at,
        "updated_at": state.updated_at,
    }


def _create_episode(project: Path, slug: str, policy: LoopPolicy) -> LoopEpisode:
    episode_id = f"{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    return LoopEpisode(
        episode_id=episode_id,
        slug=slug,
        root_cause="",
        status=LoopStatus.IDLE,
        policy=policy,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )


def _severity_rank(signal: LoopSignal) -> int:
    order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    return order.get(signal.severity.value, 0)


def _record_iteration(
    episode: LoopEpisode,
    signal: LoopSignal,
    decision_hash: str,
    action: str,
    summary: str,
    revision_changes: List[str] = None,
    new_handoff: bool = False,
) -> LoopIteration:
    now = datetime.utcnow().isoformat()
    iteration_id = f"iter-{episode.current_iteration:03d}-{uuid.uuid4().hex[:6]}"
    it = LoopIteration(
        iteration_id=iteration_id,
        index=episode.current_iteration,
        signal=signal,
        decision_hash=decision_hash,
        action=action,
        summary=summary,
        revision_changes=revision_changes or [],
        new_handoff=new_handoff,
        started_at=episode.updated_at or now,
        completed_at=now,
    )
    episode.iterations.append(it)
    episode.updated_at = now
    return it


def _apply_revision(
    project: Path,
    slug: str,
    signal: LoopSignal,
    impact: Dict[str, Any],
    policy: LoopPolicy,
) -> Dict[str, Any]:
    """Apply revision to project artifacts based on signal and impact."""
    changes = []
    handoff_generated = False
    # 1. Re-run decision engine with updated evidence
    try:
        from project_forge.decision.engine import build_decision
        from project_forge.contract import load_contract
        contract_path = project / "project-forge.yaml"
        contract = load_contract(contract_path, slug=slug)
        evidence_path = project / "docs" / "research" / slug / "evidence.jsonl"
        evidence = []
        if evidence_path.is_file():
            for line in evidence_path.read_text(encoding="utf-8-sig").splitlines():
                if line.strip():
                    try:
                        evidence.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        payload = {
            "goal": contract.project.goal,
            "constraints": list(contract.project.constraints) + signal.affected_constraints,
            "evidence": evidence,
        }
        decision = build_decision(payload)
        new_stack = decision.get("selected_stack", "")
        old_stack = contract.primary.template if getattr(contract, "primary", None) else ""
        if new_stack != old_stack:
            # Evaluate switch
            current_score = 0
            for cand in decision.get("candidates", []):
                if cand.get("stack") == old_stack:
                    current_score = cand.get("score", 0)
                    break
            candidate_score = decision.get("candidates", [{}])[0].get("score", 0)
            evidence_sources = [e.get("source", "") for e in evidence[:12] if e.get("source")]
            provisional_count = sum(1 for e in evidence if e.get("provisional"))
            confidence = evaluate_confidence(
                decision.get("decision_confidence", "Low"),
                len(evidence), provisional_count,
                len(set(evidence_sources)),
            )
            migration_cost = classify_migration_cost(new_stack, old_stack)
            switch_eval = evaluate_switch(
                old_stack, new_stack, current_score, candidate_score,
                policy, evidence_sources, confidence, migration_cost, signal,
            )
            if switch_eval["allowed"]:
                # Update contract
                try:
                    contract.primary.template = new_stack
                    from project_forge.contract import write_contract
                    write_contract(contract_path, contract)
                    changes.append(f"Primary stack switched: {old_stack} → {new_stack}")
                except Exception:
                    pass
            else:
                changes.append(f"Stack switch rejected: {switch_eval['reason']}")
        # Save ADR revision
        try:
            adr_path = project / "docs" / "architecture" / "ADR-0001-stack.md"
            if adr_path.is_file():
                backup_file(adr_path)
                # Append revision note
                with adr_path.open("a", encoding="utf-8", newline="\n") as f:
                    f.write(f"\n\n## Loop Revision {datetime.utcnow().isoformat()}\n\n")
                    f.write(f"- Signal: {signal.signal_id} ({signal.kind.value})\n")
                    f.write(f"- Summary: {signal.summary}\n")
                    f.write(f"- Action: revised architecture stack to {new_stack}\n" if new_stack != old_stack else f"- Action: architecture kept ({old_stack}), {switch_eval['reason'] if 'switch_eval' in dir() else 'no switch needed'}\n")
                changes.append("ADR updated with loop revision note.")
        except Exception:
            pass
        changes.append(f"Decision re-evaluated with {len(evidence)} evidence items.")
    except Exception as exc:
        changes.append(f"Revision failed: {exc}")
    return {"changes": changes, "handoff_generated": handoff_generated}


def _build_human_packet(
    episode: LoopEpisode, project: Path, signal: LoopSignal
) -> Any:
    """Build a human decision packet from the current project state."""
    candidates = []
    evidence = []
    try:
        from project_forge.decision.engine import build_decision
        from project_forge.contract import load_contract
        contract_path = project / "project-forge.yaml"
        contract = load_contract(contract_path, slug=episode.slug)
        evidence_path = project / "docs" / "research" / episode.slug / "evidence.jsonl"
        if evidence_path.is_file():
            for line in evidence_path.read_text(encoding="utf-8-sig").splitlines():
                if line.strip():
                    try:
                        evidence.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        payload = {
            "goal": contract.project.goal,
            "constraints": list(contract.project.constraints),
            "evidence": evidence,
        }
        decision = build_decision(payload)
        candidates = decision.get("candidates", [])
    except Exception:
        pass
    return generate_human_packet(episode, candidates, evidence)
