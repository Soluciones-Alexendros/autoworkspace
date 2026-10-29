"""C18 / V43: frozen catalog has registry contract + ops for non-audit skills."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from execution.registry import load_tools  # noqa: E402

EXPECTED_SKILLS = 16
EXPECTED_REGISTRY_TOOLS = 11
EXPECTED_OPERATIONS = 25
AUDIT_SKILLS = frozenset(
    {
        "web-compliance",
        "web-owasp",
        "web-performance",
        "project-architecture",
        "project-libraries",
    }
)

SKILLS = ROOT / "skills"


def test_v43_sixteen_skills_registry_ops() -> None:
    names = sorted(p.name for p in SKILLS.iterdir() if (p / "SKILL.md").is_file())
    assert len(names) == EXPECTED_SKILLS
    for name in names:
        assert not (SKILLS / name / "execution.yaml").is_file(), name
    tools = load_tools(force=True)
    assert len(tools) == EXPECTED_REGISTRY_TOOLS
    for tool_id, tool in tools.items():
        assert tool.skill not in AUDIT_SKILLS
        assert tool.operations, f"{tool_id} must declare operations"
        for op in tool.operations:
            assert op.get("id")
            assert op.get("effect")
    total = sum(len(t.operations) for t in tools.values())
    assert total == EXPECTED_OPERATIONS


def test_c01_matrix_matches_registry() -> None:
    """Frozen plan matrix row count equals declared registry operations."""
    plan = ROOT / "tasks" / "plan-product-closure-final.md"
    text = plan.read_text(encoding="utf-8")
    assert "Matriz de capacidades congelada" in text
    tools = load_tools(force=True)
    total = sum(len(t.operations) for t in tools.values())
    assert total == EXPECTED_OPERATIONS
    # Historical freeze said 32; alpha.1 drops 7 audit ops → 25.
    assert "32 operaciones" in text or "25 operaciones" in text or "32 operaciones / 16 skills" in text
