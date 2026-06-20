"""Auto-probe installed Superpowers versions and update the compatibility matrix."""
import json, sys, subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = REPO_ROOT / "compatibility" / "superpowers-matrix.json"


def probe_superpowers_version(superpowers_dir=None):
    """Try to detect Superpowers version from its installed location."""
    candidates = []
    if superpowers_dir:
        candidates.append(Path(superpowers_dir))
    # Common install locations
    for base in [
        Path.home() / ".codex" / "plugins" / "superpowers",
        Path.home() / ".claude" / "project-forge-marketplace" / "plugins" / "superpowers",
    ]:
        if base.is_dir():
            candidates.append(base)

    for candidate in candidates:
        for meta_file in ["package.json", "plugin.json", "VERSION", "version.txt"]:
            path = candidate / meta_file
            if not path.is_file():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
                version = data.get("version") or data.get("superpowers_version")
                if version:
                    return str(version)
            except (json.JSONDecodeError, OSError):
                pass
            try:
                text = path.read_text(encoding="utf-8-sig").strip()
                if text and len(text) < 30:
                    return text
            except OSError:
                pass
    return None


def update_matrix(version, host="codex"):
    if not MATRIX_PATH.is_file():
        print(f"Matrix not found: {MATRIX_PATH}", file=sys.stderr)
        return 1
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    existing = [e for e in matrix["versions"] if e["superpowers"] == version and host in e.get("hosts", [])]
    if existing:
        print(f"Version {version} already recorded for {host}: {existing[0]['status']}")
        return 0
    matrix["versions"].append({
        "superpowers": version,
        "hosts": [host],
        "mode": "probed",
        "required_skills": [],
        "status": "detected",
        "contracts": matrix.get("project_forge_contracts", [1, 2]),
        "note": "Auto-detected on filesystem. Real consumption test pending.",
    })
    MATRIX_PATH.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Added {version} for {host} to compatibility matrix")
    return 0


def main():
    version = probe_superpowers_version()
    if not version:
        print("No Superpowers installation detected. Pass --version manually.", file=sys.stderr)
        return 1
    print(f"Detected Superpowers version: {version}")
    return update_matrix(version)


if __name__ == "__main__":
    sys.exit(main())
