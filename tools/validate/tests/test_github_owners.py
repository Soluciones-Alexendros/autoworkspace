#!/usr/bin/env python3
"""Tests de la validación de owners de enlaces a github.com (T4, P12)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "tools" / "validate" / "skill_links.py"


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


def _fixture(tmp_path: Path, body: str) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir()
    (tmp_path / "README.md").write_text("# fixture\n", encoding="utf-8")
    (docs / "nota.md").write_text(body, encoding="utf-8")
    return tmp_path


def test_foreign_owner_fails(tmp_path: Path) -> None:
    root = _fixture(tmp_path, "Ver https://github.com/Iniciativas-Alexendros/otro.\n")
    result = _run(root)
    assert result.returncode == 1, result.stdout
    assert "Iniciativas-Alexendros/otro" in result.stdout


def test_canon_owner_passes(tmp_path: Path) -> None:
    root = _fixture(
        tmp_path,
        "Ver https://github.com/Soluciones-Alexendros/autoworkspace y "
        "https://github.com/Alexendros/alexendrosdev y "
        "https://github.com/tt-a1i/archify.\n",
    )
    result = _run(root)
    assert result.returncode == 0, result.stdout


def test_term_ok_comment_exempts_line(tmp_path: Path) -> None:
    root = _fixture(
        tmp_path,
        "Ver https://github.com/otro-owner/repo. <!-- term-ok: cita externa -->\n",
    )
    result = _run(root)
    assert result.returncode == 0, result.stdout


def test_repo_head_passes_github_owners() -> None:
    result = _run(REPO)
    assert result.returncode == 0, result.stdout
    assert "owners: 0 hallazgo(s)" in result.stdout
