#!/usr/bin/env python3
"""Compatibility entrypoint for the Project Forge decision engine."""

import sys
from pathlib import Path


SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_forge.decision.engine import build_decision, main


if __name__ == "__main__":
    raise SystemExit(main())
