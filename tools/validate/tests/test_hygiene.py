"""Tests de hygiene.py: .env versionado falla; .env.example pasa."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HYGIENE = Path(__file__).resolve().parents[1] / "hygiene.py"


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HYGIENE), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_env_example_ok(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".env.example").write_text("FOO=bar\n", encoding="utf-8")
    subprocess.run(["git", "add", ".env.example"], cwd=tmp_path, check=True, capture_output=True)
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "HYGIENE: OK" in r.stdout


def test_env_tracked_fails(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".env").write_text("SECRET=1\n", encoding="utf-8")
    subprocess.run(["git", "add", "-f", ".env"], cwd=tmp_path, check=True, capture_output=True)
    r = _run(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "secreto rastreado: .env" in r.stdout
