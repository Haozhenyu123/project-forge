"""Feature-level handoff: scoped, iterative handoffs for individual features.

Usage:
  project-forge feature new --slug SLUG --feature FEATURE_ID --goal "..." [PROJECT]
  project-forge feature list [PROJECT]
  project-forge feature handoff --slug SLUG --feature FEATURE_ID [PROJECT]
"""
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = str(REPO_ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


def _now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def cmd_feature_new(project_dir, slug, feature_id, goal):
    project = Path(project_dir)
    features_dir = project / ".project-forge" / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    feature_path = features_dir / f"{feature_id}.json"

    if feature_path.exists():
        existing = json.loads(feature_path.read_text(encoding="utf-8"))
        print(f"Feature {feature_id} already exists (created {existing.get('created_at')})")
        return existing

    # Scope the feature within the parent project's creative direction
    creative_path = project / "docs" / "product" / "creative-decision.json"
    parent_direction = None
    if creative_path.is_file():
        parent_direction = json.loads(creative_path.read_text(encoding="utf-8"))

    feature = {
        "schema_version": 1,
        "feature_id": feature_id,
        "slug": slug,
        "goal": goal,
        "parent_direction_id": parent_direction.get("selected_direction_id") if parent_direction else None,
        "created_at": _now(),
        "status": "scoped",
        "handoffs": [],
    }
    feature_path.write_text(json.dumps(feature, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Feature created: {feature_id}")
    print(f"  Goal: {goal}")
    return feature


def cmd_feature_list(project_dir):
    project = Path(project_dir)
    features_dir = project / ".project-forge" / "features"
    if not features_dir.is_dir():
        print("No features defined yet.")
        return []
    features = []
    for f in sorted(features_dir.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        features.append({
            "id": data["feature_id"],
            "goal": data["goal"],
            "status": data.get("status", "scoped"),
            "created_at": data["created_at"],
        })
    if not features:
        print("No features defined yet.")
        return []
    print(f"Features ({len(features)}):")
    for feat in features:
        print(f"  [{feat['status']}] {feat['id']}: {feat['goal'][:80]}...")
    return features


def cmd_feature_handoff(project_dir, slug, feature_id):
    project = Path(project_dir)
    feature_path = project / ".project-forge" / "features" / f"{feature_id}.json"
    if not feature_path.is_file():
        print(f"Feature {feature_id} not found. Run 'project-forge feature new' first.", file=sys.stderr)
        return None

    from project_forge.handoff.service import build_packet, export_handoff
    feature = json.loads(feature_path.read_text(encoding="utf-8"))

    # Generate feature-scoped handoff
    feature_handoff_dir = project / "docs" / "handoffs" / feature_id
    feature_handoff_dir.mkdir(parents=True, exist_ok=True)

    # Use the parent packet as base, scope to feature
    result = export_handoff(project, slug,
                            markdown_out=str(feature_handoff_dir / "superpowers-handoff.md"),
                            json_out=str(feature_handoff_dir / "superpowers-handoff.json"))
    packet = result["packet"]
    packet["project"]["feature_id"] = feature_id
    packet["project"]["feature_goal"] = feature["goal"]
    packet["superpowers"]["first_task"] = feature["goal"]
    packet["superpowers"]["assignment"] = f"Implement feature '{feature_id}' within the accepted architecture."

    # Update packet JSON with feature scope
    (feature_handoff_dir / "superpowers-handoff.json").write_text(
        json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Record handoff in feature manifest
    feature.setdefault("handoffs", []).append({
        "at": _now(),
        "handoff_dir": str(feature_handoff_dir.relative_to(project)),
    })
    feature_path.write_text(json.dumps(feature, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"Feature handoff generated: {feature_handoff_dir}")
    return packet


def main():
    p = argparse.ArgumentParser(description=__doc__)
    subs = p.add_subparsers(dest="feature_command", required=True)

    new_p = subs.add_parser("new", help="Create a scoped feature")
    new_p.add_argument("--slug", required=True)
    new_p.add_argument("--feature", required=True, dest="feature_id")
    new_p.add_argument("--goal", required=True)
    new_p.add_argument("project", nargs="?", default=".")

    list_p = subs.add_parser("list", help="List scoped features")
    list_p.add_argument("project", nargs="?", default=".")

    handoff_p = subs.add_parser("handoff", help="Generate feature-level handoff")
    handoff_p.add_argument("--slug", required=True)
    handoff_p.add_argument("--feature", required=True, dest="feature_id")
    handoff_p.add_argument("project", nargs="?", default=".")

    args = p.parse_args()
    if args.feature_command == "new":
        cmd_feature_new(args.project, args.slug, args.feature_id, args.goal)
    elif args.feature_command == "list":
        cmd_feature_list(args.project)
    elif args.feature_command == "handoff":
        cmd_feature_handoff(args.project, args.slug, args.feature_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
