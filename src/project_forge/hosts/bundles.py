"""Build deterministic host-specific plugin bundles."""

import hashlib
import json
import zipfile
from pathlib import Path

from .models import Host
from .service import EXCLUDE_DIRS, package_entries


def checksum(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_host_files(root, host):
    root, host = Path(root), Host(host)
    excluded_manifest = ".claude-plugin" if host == Host.CODEX else ".codex-plugin"
    seen = set()
    for entry in package_entries(root):
        if entry == excluded_manifest:
            continue
        path = root / entry
        candidates = [path] if path.is_file() else sorted(path.rglob("*")) if path.is_dir() else []
        for candidate in candidates:
            relative = candidate.relative_to(root)
            if candidate.is_file() and not any(part in EXCLUDE_DIRS for part in relative.parts):
                if relative not in seen:
                    seen.add(relative)
                    yield candidate


def build_host_bundles(root, out):
    root, out = Path(root), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    name, version = package["name"], package["version"]
    artifacts = []
    checksums = []
    for host in Host:
        prefix = "%s-%s-%s" % (name, host.value, version)
        archive_path = out / (prefix + ".zip")
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in iter_host_files(root, host):
                relative = path.relative_to(root).as_posix()
                archive.write(path, "%s/%s" % (prefix, relative))
        digest = checksum(archive_path)
        descriptor = out / (prefix + ".submission.json")
        manifest = ".codex-plugin/plugin.json" if host == Host.CODEX else ".claude-plugin/plugin.json"
        descriptor.write_text(
            json.dumps(
                {
                    "archive": archive_path.name,
                    "host": host.value,
                    "manifest": manifest,
                    "name": name,
                    "sha256": digest,
                    "version": version,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        artifacts.extend([archive_path, descriptor])
        checksums.append("%s  %s" % (digest, archive_path.name))
    sums = out / "HOST-SHA256SUMS"
    sums.write_text("\n".join(checksums) + "\n", encoding="utf-8")
    artifacts.append(sums)
    return artifacts

