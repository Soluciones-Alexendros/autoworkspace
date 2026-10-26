"""Terminología canónica: el glosario se aplica y la excepción por línea funciona."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SKILL_LINKS = REPO / "tools" / "validate" / "skill_links.py"
GLOSSARY = REPO / "docs" / "GLOSARIO.md"


def _fixture(tmp_path: Path, body: str) -> Path:
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    shutil.copy(GLOSSARY, tmp_path / "docs" / "GLOSARIO.md")
    (tmp_path / "docs" / "nota.md").write_text(body, encoding="utf-8")
    return tmp_path


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SKILL_LINKS), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_forbidden_term_fails(tmp_path: Path) -> None:
    root = _fixture(tmp_path, "# Nota\n\nCada cambio va en una rama de feature.\n")
    r = _run(root)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "rama de feature" in r.stdout
    assert "rama de tarea" in r.stdout


def test_term_ok_comment_exempts_line(tmp_path: Path) -> None:
    root = _fixture(
        tmp_path,
        "# Nota\n\nCada cambio iba en una rama de feature. <!-- term-ok: cita histórica -->\n",
    )
    r = _run(root)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "terminología: 0 hallazgo(s)" in r.stdout


def test_repo_head_passes_terminology() -> None:
    r = _run(REPO)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "terminología: 0 hallazgo(s)" in r.stdout
