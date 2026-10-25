"""C18 / V43: frozen catalog has execution contract + verifiable mode per skill."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
SKILLS = ROOT / "skills"


def test_v43_sixteen_skills_with_operations():
    names = sorted(p.name for p in SKILLS.iterdir() if (p / "SKILL.md").is_file())
    assert len(names) == 16
    missing = []
    for name in names:
        exe = SKILLS / name / "execution.yaml"
        assert exe.is_file(), name
        data = yaml.safe_load(exe.read_text()) or {}
        assert data.get("skill") == name
        assert data.get("execution_kind") in {"script", "agent", "orchestrator"}
        ops = data.get("operations") or []
        assert ops, f"{name} must declare operations"
        for op in ops:
            assert op.get("id")
            assert op.get("effect")
    assert missing == []


def test_c01_matrix_matches_disk():
    """Frozen plan matrix row count equals declared operations."""
    plan = ROOT / "tasks" / "plan-product-closure-final.md"
    text = plan.read_text(encoding="utf-8")
    assert "Matriz de capacidades congelada" in text
    total = 0
    for p in sorted(SKILLS.glob("*/execution.yaml")):
        data = yaml.safe_load(p.read_text()) or {}
        total += len(data.get("operations") or [])
    assert total == 32
    assert "32 operaciones" in text or "32 operaciones / 16 skills" in text
