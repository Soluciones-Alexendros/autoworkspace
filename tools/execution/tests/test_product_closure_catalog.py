"""C18 / V43: frozen catalog has registry contract + ops for non-audit skills."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from execution.registry import load_tools  # noqa: E402

EXPECTED_SKILLS = 17
EXPECTED_REGISTRY_TOOLS = 12
EXPECTED_OPERATIONS = 38
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


def test_c01_historical_matrix_remains_intact() -> None:
    """Current registry growth must not rewrite the historical plan freeze."""
    plan = ROOT / "tasks" / "plan-product-closure-final.md"
    text = plan.read_text(encoding="utf-8")
    assert "Matriz de capacidades congelada" in text
    assert ("operaciones" in text and "skills" in text) or "16 skills" in text or "17 skills" in text
    tools = load_tools(force=True)
    assert sum(len(t.operations) for t in tools.values()) == EXPECTED_OPERATIONS
