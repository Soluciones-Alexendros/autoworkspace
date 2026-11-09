"""Detached worktrees and binary patches for isolated task writers."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

# lint-staged / husky may leave these set; they break nested worktree operations.
_GIT_ENV_BLOCKLIST = (
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_WORK_TREE",
    "GIT_DIR",
    "GIT_COMMON_DIR",
    "GIT_PREFIX",
)


def _clean_git_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in _GIT_ENV_BLOCKLIST:
        env.pop(key, None)
    return env


class WorktreeManager:
    def __init__(self, repo: Path, base_revision: str, *, temp_root: Path | None = None) -> None:
        self.repo = repo.resolve()
        self.base_revision = base_revision
        self.temp_root = (temp_root or Path(tempfile.mkdtemp(prefix="autoworkspace-orchestration-"))).resolve()
        self.temp_root.mkdir(parents=True, exist_ok=True)
        self._worktrees: set[Path] = set()

    def _git(self, cwd: Path, args: list[str], *, allowed_returncodes: set[int] | None = None) -> bytes:
        allowed = allowed_returncodes or {0}
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            timeout=120,
            check=False,
            env=_clean_git_env(),
        )
        if result.returncode not in allowed:
            detail = result.stderr.decode("utf-8", errors="replace")[:1000]
            raise ValueError(f"git {args[0]} failed ({result.returncode}): {detail}")
        return result.stdout

    def create(self, name: str) -> Path:
        if not name or "/" in name or ".." in name:
            raise ValueError(f"invalid worktree name: {name!r}")
        path = self.temp_root / name
        if path.exists():
            raise ValueError(f"worktree already exists: {path}")
        self._git(self.repo, ["worktree", "add", "--detach", str(path), self.base_revision])
        self._worktrees.add(path)
        return path

    @staticmethod
    def _in_scope(path: str, scopes: list[str]) -> bool:
        candidate = PurePosixPath(path)
        for scope in scopes:
            if scope.endswith("/") and path.startswith(scope):
                return True
            if candidate.match(scope):
                return True
        return False

    def _changed_files(self, worktree: Path) -> list[str]:
        tracked = self._git(worktree, ["diff", "--name-only", "HEAD", "--", "."])
        untracked = self._git(worktree, ["ls-files", "--others", "--exclude-standard"])
        return sorted(
            set(tracked.decode().splitlines()) | set(untracked.decode().splitlines()),
        )

    def capture_patch(self, worktree: Path, task: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
        files = self._changed_files(worktree)
        scopes = list(task["write_scope"])
        outside = [path for path in files if not self._in_scope(path, scopes)]
        if outside:
            raise ValueError(f"changed files outside write_scope: {outside}")
        patches = [self._git(worktree, ["diff", "--binary", "--full-index", "HEAD", "--", "."])]
        hashes: dict[str, str] = {}
        for relative in files:
            path = worktree / relative
            if path.is_symlink():
                raise ValueError(f"symlink artifact rejected: {relative}")
            if path.is_file():
                hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
            elif not path.exists():
                hashes[relative] = "deleted"
            else:
                raise ValueError(f"non-file artifact rejected: {relative}")
            if relative in set(
                untracked
                for untracked in self._git(worktree, ["ls-files", "--others", "--exclude-standard"])
                .decode()
                .splitlines()
            ):
                patches.append(
                    self._git(
                        worktree,
                        ["diff", "--binary", "--no-index", "--", "/dev/null", relative],
                        allowed_returncodes={1},
                    )
                )
        patch = self.temp_root / f"{task['id']}.patch"
        patch.write_bytes(b"".join(patches))
        manifest = {"files": files, "sha256": hashes, "base_revision": self.base_revision}
        return patch, manifest

    def apply_patch(self, staging: Path, patch: Path) -> None:
        if not patch.is_file() or patch.stat().st_size == 0:
            raise ValueError(f"patch missing or empty: {patch}")
        self._git(staging, ["apply", "--check", str(patch)])
        self._git(staging, ["apply", str(patch)])

    def cleanup(self) -> None:
        for worktree in sorted(self._worktrees):
            try:
                worktree.resolve().relative_to(self.temp_root)
            except ValueError as exc:
                raise ValueError(f"worktree cleanup outside temporary root: {worktree}") from exc
            if worktree.exists():
                shutil.rmtree(worktree)
        self._git(self.repo, ["worktree", "prune"])
        if self.temp_root.exists():
            shutil.rmtree(self.temp_root)
        self._worktrees.clear()
