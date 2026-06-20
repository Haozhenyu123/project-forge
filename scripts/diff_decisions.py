"""Decision history diff — compare two architecture decisions and explain what changed."""
import argparse, json, sys
from pathlib import Path
from datetime import date

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = str(REPO_ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


def _load_history_entries(project_dir):
    history_dir = Path(project_dir) / ".project-forge" / "history"
    entries = []
    if not history_dir.is_dir():
        return entries
    for f in sorted(history_dir.glob("*.json"), reverse=True):
        try:
            entries.append((f.name, json.loads(f.read_text(encoding="utf-8"))))
        except (json.JSONDecodeError, OSError):
            continue
    return entries


def diff_decisions(project_dir="."):
    entries = _load_history_entries(project_dir)
    if len(entries) < 2:
        print("Need at least 2 history entries to diff. Found:", len(entries))
        return None

    latest = entries[0]
    previous = entries[1]

    latest_name, latest_data = latest
    prev_name, prev_data = previous

    changes = {
        "latest": latest_name,
        "previous": prev_name,
        "stack_changed": False,
        "score_delta": None,
        "direction_changed": False,
        "confidence_changed": False,
        "new_evidence_count": 0,
        "lost_evidence_count": 0,
    }

    ls = latest_data.get("selected_stack")
    ps = prev_data.get("selected_stack")
    if ls and ps and ls != ps:
        changes["stack_changed"] = True
        changes["stack_from"] = ps
        changes["stack_to"] = ls

    ld = latest_data.get("selected_direction")
    pd = prev_data.get("selected_direction")
    if ld and pd and ld != pd:
        changes["direction_changed"] = True
        changes["direction_from"] = pd
        changes["direction_to"] = ld

    lc = latest_data.get("decision_confidence")
    pc = prev_data.get("decision_confidence")
    if lc != pc:
        changes["confidence_changed"] = True
        changes["confidence_from"] = pc
        changes["confidence_to"] = lc

    # Evidence diffs
    latest_evidence = set()
    for c in latest_data.get("architecture_candidates", [])[:3]:
        for eid in c.get("evidence_ids", []):
            latest_evidence.add(eid)
    prev_evidence = set()
    for c in prev_data.get("architecture_candidates", [])[:3]:
        for eid in c.get("evidence_ids", []):
            prev_evidence.add(eid)

    changes["new_evidence_ids"] = sorted(latest_evidence - prev_evidence)
    changes["lost_evidence_ids"] = sorted(prev_evidence - latest_evidence)
    changes["new_evidence_count"] = len(changes["new_evidence_ids"])
    changes["lost_evidence_count"] = len(changes["lost_evidence_ids"])

    # Revisions
    revisions_dir = Path(project_dir) / ".project-forge" / "revisions"
    if revisions_dir.is_dir():
        rev_files = sorted(revisions_dir.glob("*.json"))
        if rev_files:
            changes["revisions"] = []
            for rf in rev_files:
                try:
                    rev = json.loads(rf.read_text(encoding="utf-8"))
                    changes["revisions"].append({
                        "at": rev.get("at"),
                        "reason": rev.get("reason"),
                        "previous_stack": rev.get("previous_stack"),
                        "new_top_candidate": rev.get("new_top_candidate"),
                    })
                except (json.JSONDecodeError, OSError):
                    pass

    return changes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("project", nargs="?", default=".")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    diff = diff_decisions(args.project)
    if diff is None:
        return 1
    if args.json:
        print(json.dumps(diff, indent=2, sort_keys=True))
    else:
        print(f"Decision diff: {diff['latest']} vs {diff['previous']}")
        if diff["stack_changed"]:
            print(f"  Stack: {diff['stack_from']} → {diff['stack_to']}")
        if diff["direction_changed"]:
            print(f"  Direction: {diff['direction_from']} → {diff['direction_to']}")
        if diff["confidence_changed"]:
            print(f"  Confidence: {diff['confidence_from']} → {diff['confidence_to']}")
        if diff["new_evidence_count"]:
            print(f"  New evidence: {diff['new_evidence_count']} source(s)")
        if diff["lost_evidence_count"]:
            print(f"  Lost evidence: {diff['lost_evidence_count']} source(s)")
        if not any([diff["stack_changed"], diff["direction_changed"], diff["confidence_changed"]]):
            print("  No significant changes between these two decisions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
