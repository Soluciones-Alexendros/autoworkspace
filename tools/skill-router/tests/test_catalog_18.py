"""Catalog gate: 18 skills, the renamed self-audit entry, coherent index.

The Pi/Cursor listings are operator evidence (``not_run`` in CI); this test only
covers what the repository can prove. The post-rename Pi RPC re-check lives in
``test_pi_catalog_discovery.py`` and skips when the binary is unavailable.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

EXPECTED_COUNT = 18
RENAMED = "project-machineroom"
REMOVED = "project-autoworkspace"


def _catalog_dirs() -> list[Path]:
    return sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir() and (p / "SKILL.md").is_file())


def test_catalog_has_eighteen_skills() -> None:
    dirs = _catalog_dirs()
    assert len(dirs) == EXPECTED_COUNT, [p.name for p in dirs]
    names = {p.name for p in dirs}
    assert RENAMED in names
    assert REMOVED not in names


def test_directory_name_matches_frontmatter() -> None:
    for path in _catalog_dirs():
        frontmatter = path.joinpath("SKILL.md").read_text(encoding="utf-8").split("---", 2)[1]
        match = re.search(r"^name:\s*(\S+)\s*$", frontmatter, re.MULTILINE)
        assert match is not None, path
        assert match.group(1) == path.name, path


def _build_index() -> dict:
    spec = importlib.util.spec_from_file_location(
        "skill_index_generate", ROOT / "tools" / "skill-index" / "generate.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_index(ROOT)


def test_index_lists_the_same_catalog() -> None:
    indexed = {skill["name"] for skill in _build_index()["skills"]}
    assert indexed == {p.name for p in _catalog_dirs()}
    assert RENAMED in indexed


def test_router_and_registry_reference_the_renamed_skill() -> None:
    intent = (ROOT / "tools" / "skill-router" / "intent-map.yaml").read_text(encoding="utf-8")
    registry = (ROOT / "tools" / "execution" / "registry.yaml").read_text(encoding="utf-8")
    assert RENAMED in intent
    assert RENAMED in registry
    assert REMOVED not in intent
    assert REMOVED not in registry
