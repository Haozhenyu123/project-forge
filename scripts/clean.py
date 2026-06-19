#!/usr/bin/env python3
"""Clean build artifacts and temporary files from the Project Forge workspace."""

import sys
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]

CLEAN_PATTERNS = [
    "**/__pycache__",
    "**/*.pyc",
    "**/*.pyo",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
]


def main():
    removed = 0
    for pattern in CLEAN_PATTERNS:
        for path in sorted(ROOT.glob(pattern)):
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
                print(f"Removed directory: {path.relative_to(ROOT)}")
                removed += 1
            elif path.is_file():
                path.unlink(missing_ok=True)
                print(f"Removed file: {path.relative_to(ROOT)}")
                removed += 1
    print(f"Cleaned {removed} items.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
