"""Tests for tools/validate/skill_spec.py."""

import importlib.util
from pathlib import Path

SPEC = Path(__file__).resolve().parents[1] / "skill_spec.py"


def load():
    spec = importlib.util.spec_from_file_location("skill_spec", SPEC)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_skill(root: Path, name: str, body: str, desc: str | None = None) -> None:
    skill = root / "skills" / name
    skill.mkdir(parents=True)
    description = desc or (f"{name} capability. Use when the operator asks for it. Not for other families.")
    (skill / "SKILL.md").write_text(
        f"""---
name: {name}
description: >-
  {description}
license: MIT
metadata:
  author: Soluciones-Alexendros
  version: "1.0.0"
  domain: {name.split("-", 1)[0]}
  type: atomic
  language: en
---

# {name}

{body}
""",
        encoding="utf-8",
    )


def seed_catalog(root: Path, names: list[str]) -> None:
    rows = "\n".join(f"| `build` | {n} | x |" for n in names)
    (root / "README.md").write_text(
        f"| Familia | Skill | Qué hace |\n| --- | --- | --- |\n{rows}\n",
        encoding="utf-8",
    )
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "TAXONOMY.md").write_text(
        " · ".join(names) + "\n",
        encoding="utf-8",
    )


def run_root(root: Path) -> list[str]:
    mod = load()
    mod.ERRORS.clear()
    mod.ROOT = root
    mod.SKILLS = root / "skills"
    sdirs = mod.skill_dirs(root)
    names = {p.name for p in sdirs}
    mod.check_catalog(root, names)
    for s in sdirs:
        mod.check_skill(root, s, names)
    return list(mod.ERRORS)


def test_description_without_boundary(tmp_path):
    write_skill(
        tmp_path,
        "plan-demo",
        "## Overview\n\nX.\n\n## When to Use\n\nY.\n\n## References\n\nZ.\n",
        desc="Does something. Use when you ask for design.",
    )
    seed_catalog(tmp_path, ["plan-demo"])
    errors = run_root(tmp_path)
    assert any("exclusion" in e for e in errors)


def test_arrow_to_missing_skill(tmp_path):
    write_skill(
        tmp_path,
        "plan-demo",
        "## Overview\n\nX.\n\n## When to Use\n\nY.\n\n## References\n\nZ.\n",
        desc="Does something. Use when you ask for design. Not for security (→ web-owasp).",
    )
    seed_catalog(tmp_path, ["plan-demo"])
    errors = run_root(tmp_path)
    assert any("inexistente" in e for e in errors)


def test_host_profile_heading(tmp_path):
    write_skill(
        tmp_path,
        "local-demo",
        "## Overview\n\nX.\n\n## When to Use\n\nY.\n\n## Perfil de Este Equipo\n\nhost.\n\n## References\n\nZ.\n",
    )
    seed_catalog(tmp_path, ["local-demo"])
    errors = run_root(tmp_path)
    assert any("H2 prohibido" in e for e in errors)


def test_catalog_mismatch(tmp_path):
    write_skill(
        tmp_path,
        "plan-demo",
        "## Overview\n\nX.\n\n## When to Use\n\nY.\n\n## References\n\nZ.\n",
    )
    seed_catalog(tmp_path, ["plan-demo", "web-ghost"])
    errors = run_root(tmp_path)
    assert any("README vs carpetas" in e or "TAXONOMY vs carpetas" in e for e in errors)


def test_smoke_required_when_scripts(tmp_path):
    write_skill(
        tmp_path,
        "local-demo",
        "## Overview\n\nX.\n\n## When to Use\n\nY.\n\n## Tools\n\ncli.\n\n## References\n\nZ.\n",
    )
    scripts = tmp_path / "skills" / "local-demo" / "scripts"
    scripts.mkdir()
    (scripts / "run.py").write_text("print(1)\n", encoding="utf-8")
    seed_catalog(tmp_path, ["local-demo"])
    errors = run_root(tmp_path)
    assert any("smoke_sh.sh" in e for e in errors)


def test_local_domain_is_accepted(tmp_path):
    write_skill(
        tmp_path,
        "local-demo",
        "## Overview\n\nX.\n\n## When to Use\n\nY.\n",
    )
    seed_catalog(tmp_path, ["local-demo"])
    errors = run_root(tmp_path)
    assert not any("unknown domain" in e for e in errors)


def test_legacy_system_domain_is_rejected(tmp_path):
    write_skill(
        tmp_path,
        "system-demo",
        "## Overview\n\nX.\n\n## When to Use\n\nY.\n",
    )
    seed_catalog(tmp_path, ["system-demo"])
    errors = run_root(tmp_path)
    assert any("unknown domain" in e for e in errors)
