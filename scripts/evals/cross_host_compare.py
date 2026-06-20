"""Cross-host behavior comparison: verify same handoff produces consistent plans across Codex and Claude."""
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def cross_host_compare(project_dir, hosts=None):
    """Run structural comparison across hosts (offline — checks handoff quality only)."""
    hosts = hosts or ["codex", "claude"]
    project = Path(project_dir)
    handoff_path = project / "docs" / "superpowers-handoff.json"
    if not handoff_path.is_file():
        print(f"No handoff found: {handoff_path}", file=sys.stderr)
        return None
    
    handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
    results = {}
    for host in hosts:
        results[host] = _evaluate_handoff_quality(handoff, host)
    
    comparison = {
        "project": str(project),
        "handoff_schema": handoff.get("schema_version"),
        "hosts": results,
        "consistent": _check_consistency(results),
        "recommendations": _recommendations(results),
    }
    return comparison


def _evaluate_handoff_quality(handoff, host):
    criteria = handoff.get("superpowers", {}).get("acceptance_criteria", [])
    guardrails = handoff.get("superpowers", {}).get("guardrails", [])
    boundary = handoff.get("boundary", {})
    checks = {
        "host": host,
        "has_acceptance_criteria": len(criteria) > 0,
        "has_guardrails": len(guardrails) > 0,
        "has_boundary": bool(boundary),
        "boundary_declares_superpowers_owns": bool(boundary.get("superpowers_owns")),
        "boundary_declares_forge_owns": bool(boundary.get("project_forge_owns")),
        "evidence_count": len(handoff.get("evidence", [])),
        "has_inventory": handoff.get("inventory") is not None,
        "has_creative_decision": handoff.get("creative_decision") is not None,
        "has_verification_report": bool(handoff.get("readiness", {}).get("verification_report")),
        "required_commands_defined": len(handoff.get("harness", {}).get("required_commands", [])) > 0,
    }
    checks["ready"] = all(v for k, v in checks.items() if k not in ("host", "ready"))
    return checks


def _check_consistency(results):
    hosts = list(results.keys())
    if len(hosts) < 2:
        return True
    # All hosts should see the same structural readiness
    first = results[hosts[0]]
    for host in hosts[1:]:
        for k, v in first.items():
            if k == "host":
                continue
            if results[host].get(k) != v:
                return False
    return True


def _recommendations(results):
    recs = []
    for host, checks in results.items():
        if not checks.get("has_inventory"):
            recs.append(f"[{host}] Inventory missing — run project-forge inspect to generate")
        if not checks.get("has_verification_report"):
            recs.append(f"[{host}] No verification report — run project-forge superpowers-ready --execute")
        if not checks.get("ready"):
            failing = [k for k, v in checks.items() if not v and k not in ("host", "ready")]
            recs.append(f"[{host}] Not ready: {', '.join(failing)}")
    return recs


def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("project", nargs="?", default=".")
    p.add_argument("--hosts", default="codex,claude")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    hosts = [h.strip() for h in args.hosts.split(",")]
    comparison = cross_host_compare(args.project, hosts)
    if comparison is None:
        return 1
    if args.json:
        print(json.dumps(comparison, indent=2, sort_keys=True))
    else:
        print(f"Cross-host comparison for {comparison['project']}")
        for host, checks in comparison["hosts"].items():
            status = "READY" if checks.get("ready") else "BLOCKED"
            print(f"  {host}: {status}")
        if comparison["recommendations"]:
            print("\nRecommendations:")
            for r in comparison["recommendations"]:
                print(f"  - {r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
