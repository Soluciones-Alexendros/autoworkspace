"""git check-ignore -q must be called with one path (P12 errata)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPO_GITIGNORE = Path(__file__).resolve().parents[3] / ".gitignore"


def test_check_ignore_env_paths_separately(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    shutil.copy(REPO_GITIGNORE, tmp_path / ".gitignore")
    (tmp_path / ".env").write_text("SECRET=1\n", encoding="utf-8")
    (tmp_path / ".env.local").write_text("SECRET=2\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text("FOO=\n", encoding="utf-8")

    for name in (".env", ".env.local"):
        r = subprocess.run(
            ["git", "check-ignore", "-q", name],
            cwd=tmp_path,
            check=False,
            capture_output=True,
        )
        assert r.returncode == 0, f"{name} should be ignored (got {r.returncode})"

    r_ex = subprocess.run(
        ["git", "check-ignore", "-q", ".env.example"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
    )
    assert r_ex.returncode != 0, ".env.example must not be ignored"
