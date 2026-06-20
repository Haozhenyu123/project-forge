"""Bootstrap helpers for legacy script entrypoints."""

import sys
from pathlib import Path


def add_src(script_file):
    root = Path(script_file).resolve().parents[1]
    src = str(root / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    return root
