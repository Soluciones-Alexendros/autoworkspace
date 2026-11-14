"""Post-rename Pi discovery re-check (H4): 17 catalog skills announced.

Runs Pi in RPC mode with a fresh process (equivalent to ``/reload`` in a new
session) and asserts the catalog skills are announced. Skips with an explicit
``not_run`` reason when the Pi binary is unavailable, so CI never reads a missing
binary as PASS.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness.pi import rpc_commands  # noqa: E402

RENAMED = "project-machineroom"


def _catalog_names() -> set[str]:
    return {p.name for p in (ROOT / "skills").iterdir() if p.is_dir() and (p / "SKILL.md").is_file()}


def test_pi_announces_the_whole_catalog_after_rename() -> None:
    if shutil.which("pi") is None:
        pytest.skip("Pi binary not on PATH: catalog discovery is not_run in this environment")
    announced = {
        str(command.get("name", "")).removeprefix("skill:")
        for command in rpc_commands(ROOT)
        if command.get("source") == "skill"
    }
    catalog = _catalog_names()
    missing = sorted(catalog - announced)
    assert not missing, f"Pi did not announce: {missing}"
    assert RENAMED in announced
    # A stale user runtime (~/.machineroom migration pending) may still announce
    # the pre-rename id; that is host state, covered by the closure migration and
    # asserted absent at repository level in test_catalog_18.py.
