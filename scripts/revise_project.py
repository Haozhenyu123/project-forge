"""Revise a project's architecture when Superpowers signals issues with the current handoff.
In v0.4.0, revise delegates to the Loop Engine for signal-aware processing.

Usage:
  project-forge revise [PROJECT] --slug SLUG --reason "..." [--constraint ...] [--refresh-evidence]
"""
import argparse, json, sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = str(REPO_ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


def run_revise(project_dir, slug, reason, new_constraints=None, refresh_evidence=False):
    # Delegate to Loop Engine when available (v0.4.0+)
    try:
        from project_forge.loop.service import ingest_signal, run_loop
        signal_data = {
            "signal_id": f"revise-{slug}-{reason[:20].replace(' ', '-').lower()}",
            "source": "project-forge.revise",
            "kind": "manual",
            "severity": "medium",
            "observed_at": date.today().isoformat(),
            "summary": reason,
            "affected_constraints": new_constraints or [],
            "suggested_owner": "forge",
        }
        ingest_result = ingest_signal(project_dir, signal_data)
        loop_result = run_loop(project_dir, slug, json_output=True)
        return {
            "revise_entry": "loop-delegated",
            "signal_ingest": ingest_result,
            "loop_run": loop_result,
        }
    except Exception:
        pass

    # Fallback: legacy revise flow
    project = Path(project_dir)
    contract_path = project / "project-forge.yaml"
    if not contract_path.exists():
        raise FileNotFoundError(f"No project-forge.yaml found in {project}")

    from project_forge.contract import load_contract
    contract = load_contract(contract_path, slug=slug)

    # Gather existing evidence
    evidence_path = project / "docs" / "research" / slug / "evidence.jsonl"
    evidence = []
    if evidence_path.is_file():
        for line in evidence_path.read_text(encoding="utf-8-sig").splitlines():
            if line.strip():
                try:
                    evidence.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    # Re-run decision with new constraints
    from project_forge.decision.engine import build_decision
    goal = getattr(contract.project, "goal", slug)
    existing_constraints = list(getattr(contract.project, "constraints", []) or [])
    all_constraints = existing_constraints + (new_constraints or [])

    decision = build_decision({
        "goal": goal,
        "constraints": all_constraints,
        "evidence": evidence,
    })

    # Record the revision in history
    history_dir = project / ".project-forge" / "revisions"
    history_dir.mkdir(parents=True, exist_ok=True)
    revision_record = {
        "at": date.today().isoformat(),
        "slug": slug,
        "reason": reason,
        "previous_stack": contract.primary.template if getattr(contract, "primary", None) else None,
        "new_top_candidate": decision.get("selected_stack"),
        "new_candidates": decision.get("candidates", []),
        "decision_confidence": decision.get("decision_confidence"),
        "revisit_triggers": decision.get("revisit_triggers", []),
    }
    rev_file = history_dir / f"{date.today().isoformat()}-{slug}.json"
    rev_file.write_text(json.dumps(revision_record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return revision_record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("project", nargs="?", default=".")
    p.add_argument("--slug", required=True)
    p.add_argument("--reason", required=True, help="Why is the architecture being revised?")
    p.add_argument("--constraint", action="append", default=[], help="Additional constraints")
    p.add_argument("--refresh-evidence", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    try:
        result = run_revise(args.project, args.slug, args.reason, args.constraint, args.refresh_evidence)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Revision recorded: {result['slug']}")
        print(f"  Reason: {result['reason']}")
        print(f"  Previous stack: {result.get('previous_stack')}")
        print(f"  New top candidate: {result.get('new_top_candidate')}")
        print(f"  Confidence: {result.get('decision_confidence')}")
        print(f"  Revision file: .project-forge/revisions/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
