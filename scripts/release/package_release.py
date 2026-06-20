#!/usr/bin/env python3
"""Build Project Forge release archives and host submission bundles."""

import argparse
import hashlib
import json
import sys
import tarfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from project_forge.hosts import build_host_bundles


def iter_package_files(root):
    package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    for entry in package.get("files", []):
        path = root / entry
        if path.is_file():
            yield path
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and "__pycache__" not in child.parts:
                    yield child
    yield root / "package.json"


def checksum(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_archives(root, out):
    root = Path(root)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    name = package["name"]
    version = package["version"]
    prefix = f"{name}-{version}"
    files = sorted({path for path in iter_package_files(root)})

    zip_path = out / f"{prefix}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, f"{prefix}/{path.relative_to(root).as_posix()}")

    tar_path = out / f"{prefix}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as archive:
        for path in files:
            archive.add(path, f"{prefix}/{path.relative_to(root).as_posix()}")

    sums = out / "SHA256SUMS"
    sums.write_text(
        "\n".join(f"{checksum(path)}  {path.name}" for path in (zip_path, tar_path)) + "\n",
        encoding="utf-8",
    )
    return [zip_path, tar_path, sums]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--out", default="dist")
    parser.add_argument("--host-bundles", action="store_true")
    args = parser.parse_args(argv)
    artifacts = build_archives(args.root, args.out)
    if args.host_bundles:
        artifacts.extend(build_host_bundles(args.root, args.out))
    print(json.dumps({"artifacts": [str(path) for path in artifacts]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
