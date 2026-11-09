"""Detached worktree, binary patch and staging integration tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]


def _clean_clone_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in (
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_WORK_TREE",
        "GIT_DIR",
        "GIT_COMMON_DIR",
        "GIT_PREFIX",
    ):
        env.pop(key, None)
    return env


sys.path.insert(0, str(ROOT / "tools"))

from orchestrator.worktrees import WorktreeManager  # noqa: E402


def _isolated_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    subprocess.run(
        ["git", "clone", "--dissociate", f"file://{ROOT}", str(repo)],
        check=True,
        capture_output=True,
        env=_clean_clone_env(),
    )
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True, capture_output=True)
    return repo


def _head(repo: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


def _task(scope: list[str]) -> dict[str, Any]:
    return {"id": "writer", "write_scope": scope}


def test_untracked_patch_applies_to_staging_without_commit(tmp_path: Path) -> None:
    repo = _isolated_repo(tmp_path)
    manager = WorktreeManager(repo, _head(repo), temp_root=tmp_path / "worktrees")
    try:
        writer = manager.create("writer")
        (writer / "fixture-orchestration.txt").write_text("integrated\n", encoding="utf-8")
        patch, manifest = manager.capture_patch(writer, _task(["fixture-orchestration.txt"]))
        assert manifest["files"] == ["fixture-orchestration.txt"]
        staging = manager.create("staging")
        manager.apply_patch(staging, patch)
        assert (staging / "fixture-orchestration.txt").read_text(encoding="utf-8") == "integrated\n"
        assert subprocess.run(
            ["git", "rev-parse", "HEAD"], check=False, cwd=repo, capture_output=True, text=True
        ).stdout.strip() == _head(repo)
    finally:
        manager.cleanup()


def test_binary_untracked_patch_preserves_bytes(tmp_path: Path) -> None:
    repo = _isolated_repo(tmp_path)
    manager = WorktreeManager(repo, _head(repo), temp_root=tmp_path / "worktrees")
    payload = bytes(range(256))
    try:
        writer = manager.create("writer")
        (writer / "fixture.bin").write_bytes(payload)
        patch, _manifest = manager.capture_patch(writer, _task(["fixture.bin"]))
        staging = manager.create("staging")
        manager.apply_patch(staging, patch)
        assert (staging / "fixture.bin").read_bytes() == payload
    finally:
        manager.cleanup()


def test_write_scope_violation_is_rejected(tmp_path: Path) -> None:
    repo = _isolated_repo(tmp_path)
    manager = WorktreeManager(repo, _head(repo), temp_root=tmp_path / "worktrees")
    try:
        writer = manager.create("writer")
        (writer / "README.md").write_text("out of scope\n", encoding="utf-8")
        with pytest.raises(ValueError, match="write_scope"):
            manager.capture_patch(writer, _task(["allowed.txt"]))
    finally:
        manager.cleanup()


def test_cleanup_only_removes_temporary_worktrees(tmp_path: Path) -> None:
    repo = _isolated_repo(tmp_path)
    root = tmp_path / "worktrees"
    manager = WorktreeManager(repo, _head(repo), temp_root=root)
    writer = manager.create("writer")
    (writer / "temporary.txt").write_text("disposable", encoding="utf-8")
    manager.cleanup()
    assert not root.exists()
    listed = subprocess.run(
        ["git", "worktree", "list", "--porcelain"], check=False, cwd=repo, capture_output=True, text=True
    ).stdout
    assert str(writer) not in listed
