"""SSOT naming constants and LEGACY_* isolation."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from harness import naming  # noqa: E402

NAMING_PATH = REPO_ROOT / "tools" / "harness" / "naming.py"


def test_brand_and_prefix_are_machineroom() -> None:
    assert naming.BRAND == "machineroom"
    assert naming.BRAND_TITLE == "Machineroom"
    assert naming.PREFIX == "mr"
    assert naming.RUNTIME_DIRNAME == ".machineroom"
    assert naming.PROJECT_DIRNAME == ".machineroom"
    assert naming.REPO == "Soluciones-Alexendros/machineroom"
    assert naming.SKILL_SELF == "project-machineroom"
    assert naming.EXTENSION_DIR == "machineroom"
    assert naming.AGENTS == ("mr-planner", "mr-verifier", "mr-worker")
    assert naming.SUBAGENT == "mr_subagent"
    assert naming.STATUS_CMD == "/mr-status"


def test_legacy_constants_preserve_autoworkspace() -> None:
    assert naming.LEGACY_BRAND == "autoworkspace"
    assert naming.LEGACY_BRAND_TITLE == "Autoworkspace"
    assert naming.LEGACY_PREFIX == "aw"
    assert naming.LEGACY_RUNTIME_DIRNAME == ".autoworkspace"
    assert naming.LEGACY_PROJECT_DIRNAME == ".autoworkspace"
    assert naming.LEGACY_REPO == "Soluciones-Alexendros/autoworkspace"
    assert naming.LEGACY_SKILL_SELF == "project-autoworkspace"
    assert naming.LEGACY_EXTENSION_DIR == "autoworkspace"
    assert naming.LEGACY_AGENTS == ("aw-planner", "aw-verifier", "aw-worker")
    assert naming.LEGACY_SUBAGENT == "aw_subagent"
    assert naming.LEGACY_STATUS_CMD == "/aw-status"


def test_autoworkspace_literals_only_on_legacy_lines() -> None:
    """Live naming.py may only spell autoworkspace/aw- on LEGACY_* lines."""
    lines = NAMING_PATH.read_text(encoding="utf-8").splitlines()
    offenders: list[str] = []
    for index, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
            continue
        if "LEGACY_" in line:
            continue
        lower = line.lower()
        if "autoworkspace" in lower or "aw-" in lower or "aw_" in lower:
            offenders.append(f"{index}:{line.strip()}")
    assert offenders == [], "non-LEGACY autoworkspace/aw literals:\n" + "\n".join(offenders)
