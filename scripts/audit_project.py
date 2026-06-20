"""Audit an existing project: would we still choose this stack today?"""

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _load_contract(project: Path) -> Dict[str, Any]:
    contract_path = project / "project-forge.yaml"
    if not contract_path.exists():
        raise FileNotFoundError(f"No project-forge.yaml found in {project}")
    import project_forge.contract as contract_mod
    return contract_mod.load_contract(contract_path).to_dict()


def _load_evidence(project: Path) -> List[Dict[str, Any]]:
    evidence_path = project / "docs" / "research"
    if not evidence_path.exists():
        return []
    rows = []
    for evidence_file in sorted(evidence_path.glob("**/evidence.jsonl")):
        for line in evidence_file.read_text(encoding="utf-8-sig").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def run_audit(project_dir: str = ".") -> Dict[str, Any]:
    project = Path(project_dir).resolve()
    contract = _load_contract(project)

    current_stack = contract.get("stack") or contract.get("stacks", {}).get("primary")
    current_secondaries = contract.get("stacks", {}).get("secondary", []) or []
    goal = contract.get("meta", {}).get("goal") or contract.get("goal", "")

    evidence = _load_evidence(project)
    from project_forge.decision.engine import build_decision
    decision = build_decision({
        "goal": goal,
        "constraints": contract.get("meta", {}).get("constraints", []),
        "evidence": evidence,
    })

    top_candidate = decision["selected_architecture"]["id"] if decision.get("selected_architecture") else decision.get("selected_stack", "")
    ranking = decision.get("candidates", [])

    current_rank = None
    for idx, c in enumerate(ranking):
        if c["stack"] == current_stack:
            current_rank = idx + 1
            break

    still_recommended = current_stack == top_candidate
    verdict = "same"
    if not still_recommended and current_rank:
        verdict = f"dropped to rank {current_rank}"
    elif not current_rank:
        verdict = "not in top candidates"

    return {
        "audit_at": date.today().isoformat(),
        "project": str(project),
        "current_stack": current_stack,
        "current_secondaries": current_secondaries,
        "still_recommended": still_recommended,
        "verdict": verdict,
        "top_candidate": top_candidate,
        "top_candidate_score": ranking[0]["score"] if ranking else 0,
        "all_candidates": ranking,
        "decision_confidence": decision.get("decision_confidence", "unknown"),
        "recommendation": _recommendation(still_recommended, current_stack, top_candidate, decision),
    }


def _recommendation(still: bool, current: str, top: str, decision: Dict[str, Any]) -> str:
    if still:
        return f"Stack '{current}' is still the best choice based on current evidence. No change recommended."
    if decision.get("decision_confidence") == "High":
        return f"Stack '{top}' is now ranked higher than current '{current}'. Consider migration if the gap is significant."
    return f"Stack '{top}' edges ahead but decision confidence is {decision.get('decision_confidence', 'low')}. Stay on '{current}' and refresh evidence later."


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", default=".", help="Project directory")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    try:
        result = run_audit(args.project)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Audit: {result['project']}")
        print(f"  Current stack: {result['current_stack']}")
        print(f"  Still recommended: {result['still_recommended']}")
        print(f"  Verdict: {result['verdict']}")
        print(f"  Top candidate: {result['top_candidate']} (score: {result['top_candidate_score']})")
        print(f"  Confidence: {result['decision_confidence']}")
        print(f"  Recommendation: {result['recommendation']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
