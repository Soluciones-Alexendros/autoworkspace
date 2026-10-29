#!/usr/bin/env python3
"""Thin delegate to the Proton driver. The skill does not own the client."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

DRIVER = Path(__file__).resolve().parents[3] / "tools" / "email" / "drivers" / "proton" / "proton_bridge.py"


if __name__ == "__main__":
    sys.argv[0] = str(DRIVER)
    raise SystemExit(runpy.run_path(str(DRIVER), run_name="__main__"))
