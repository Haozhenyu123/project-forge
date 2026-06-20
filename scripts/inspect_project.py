#!/usr/bin/env python3
"""Compatibility entrypoint for Project Forge architecture inspection."""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_forge.inventory.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
