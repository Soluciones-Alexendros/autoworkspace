"""Detached worktrees, binary patches, and cumulative run staging."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path, PurePosixPath
from typing import Any

from state_paths import state_file

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


def tree_digest(root: Path) -> str:
    """Stable SHA-256 over tracked worktree files under root.

    Staging / patch identity only. Follows ``Path.rglob`` file discovery and does
    **not** apply evidence exclusions or symlink-aware recording. For acceptance
    digests use ``execution.evidence.work_digest`` / ``content_manifest``.
    """
    digest = hashlib.sha256()
    root = root.resolve()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


class WorktreeManager:
    def __init__(self, repo: Path, base_revision: str, *, temp_root: Path | None = None) -> None:
        self.repo = repo.resolve()
        self.base_revision = base_revision
        self.temp_root = (temp_root or Path(tempfile.mkdtemp(prefix="machineroom-orchestration-"))).resolve()
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

    def remove(self, worktree: Path) -> None:
        worktree = worktree.resolve()
        worktree.relative_to(self.temp_root)
        if worktree in self._worktrees:
            self._worktrees.discard(worktree)
        if worktree.exists():
            shutil.rmtree(worktree)
        self._git(self.repo, ["worktree", "prune"])

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
        untracked = set(self._git(worktree, ["ls-files", "--others", "--exclude-standard"]).decode().splitlines())
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
            if relative in untracked:
                patches.append(
                    self._git(
                        worktree,
                        ["diff", "--binary", "--no-index", "--", "/dev/null", relative],
                        allowed_returncodes={1},
                    )
                )
        patch = self.temp_root / f"{task['id']}.patch"
        patch.write_bytes(b"".join(patches))
        if patch.stat().st_size == 0:
            raise ValueError(f"empty patch rejected for task {task['id']}")
        patch_sha256 = hashlib.sha256(patch.read_bytes()).hexdigest()
        manifest = {
            "files": files,
            "sha256": hashes,
            "base_revision": self.base_revision,
            "patch_sha256": patch_sha256,
            "task_id": str(task["id"]),
        }
        return patch, manifest

    def apply_patch(self, staging: Path, patch: Path) -> None:
        if not patch.is_file() or patch.stat().st_size == 0:
            raise ValueError(f"patch missing or empty: {patch}")
        self._git(staging, ["apply", "--check", str(patch)])
        self._git(staging, ["apply", str(patch)])

    def validate_patch_manifest(self, patch: Path, manifest: dict[str, Any]) -> None:
        if not patch.is_file() or patch.stat().st_size == 0:
            raise ValueError(f"stale or missing patch: {patch}")
        expected = str(manifest.get("patch_sha256") or "")
        actual = hashlib.sha256(patch.read_bytes()).hexdigest()
        if not expected:
            raise ValueError("manifest missing patch_sha256 digest")
        if expected != actual:
            raise ValueError(f"stale patch digest: manifest={expected} actual={actual}")
        if str(manifest.get("base_revision") or "") != self.base_revision:
            raise ValueError("stale manifest base_revision")

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


class RunWorkspace:
    """One shared staging area per orchestrator run with transactional integration."""

    def __init__(
        self,
        repo: Path,
        base_revision: str,
        run_id: str,
        *,
        temp_root: Path | None = None,
    ) -> None:
        self.repo = repo.resolve()
        self.base_revision = base_revision
        self.run_id = run_id
        self.manager = WorktreeManager(self.repo, base_revision, temp_root=temp_root)
        self.staging = self.manager.create("staging")
        self.lock = threading.RLock()
        self.accepted: list[dict[str, Any]] = []
        self._digest = tree_digest(self.staging)

    def create_writer(self, task_id: str) -> Path:
        with self.lock:
            writer = self.manager.create(f"{task_id}-writer")
            for item in self.accepted:
                self.manager.apply_patch(writer, Path(item["patch"]))
            if self.accepted:
                # Commit integrated priors so capture_patch only diffs this task's writes.
                self.manager._git(writer, ["add", "-A"])
                self.manager._git(
                    writer,
                    [
                        "-c",
                        "user.email=machineroom@local",
                        "-c",
                        "user.name=machineroom",
                        "commit",
                        "--no-gpg-sign",
                        "-m",
                        f"integrated-base-for-{task_id}",
                    ],
                )
            return writer

    def drop_writer(self, writer: Path) -> None:
        with self.lock:
            self.manager.remove(writer)

    def _verify_manifest_on_staging(self, manifest: dict[str, Any]) -> None:
        for relative, expected in (manifest.get("sha256") or {}).items():
            path = self.staging / relative
            if expected == "deleted":
                if path.exists():
                    raise ValueError(f"manifest digest mismatch (expected deleted): {relative}")
                continue
            if not path.is_file():
                raise ValueError(f"manifest digest mismatch (missing): {relative}")
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                raise ValueError(f"manifest digest mismatch for {relative}")

    def _restore_to_digest(self, expected_digest: str) -> None:
        # Recreate staging from base + accepted patches only.
        self.manager.remove(self.staging)
        self.staging = self.manager.create("staging")
        for item in self.accepted:
            self.manager.apply_patch(self.staging, Path(item["patch"]))
        restored = tree_digest(self.staging)
        if restored != expected_digest:
            raise ValueError(f"staging rollback digest mismatch: expected={expected_digest} actual={restored}")
        self._digest = restored

    def integrate(self, task_id: str, patch: Path, manifest: dict[str, Any]) -> str:
        with self.lock:
            before = self._digest
            try:
                self.manager.validate_patch_manifest(patch, manifest)
                self.manager.apply_patch(self.staging, patch)
                self._verify_manifest_on_staging(manifest)
                record = {
                    "task_id": task_id,
                    "patch": str(patch),
                    "manifest": manifest,
                    "files": list(manifest.get("files") or []),
                }
                self.accepted.append(record)
                self._digest = tree_digest(self.staging)
                self.write_integrated_manifest()
                return self._digest
            except Exception:
                self.accepted = [item for item in self.accepted if item["task_id"] != task_id]
                self._restore_to_digest(before)
                raise

    def write_integrated_manifest(self) -> Path:
        run_dir = state_file(self.repo, "runs", self.run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        files: list[str] = []
        sha256: dict[str, str] = {}
        order: list[str] = []
        for item in self.accepted:
            order.append(str(item["task_id"]))
            for relative in item.get("files") or []:
                if relative not in files:
                    files.append(relative)
            sha256.update(dict((item.get("manifest") or {}).get("sha256") or {}))
        payload = {
            "run_id": self.run_id,
            "base_revision": self.base_revision,
            "order": order,
            "files": files,
            "sha256": sha256,
            "staging_digest": self._digest,
        }
        path = run_dir / "integrated.manifest.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def rebuild_staging_from_artifacts(self, items: list[dict[str, Any]]) -> str:
        with self.lock:
            before = self._digest
            self.accepted = []
            try:
                self.manager.remove(self.staging)
                self.staging = self.manager.create("staging")
                for item in items:
                    patch = Path(item["patch"])
                    manifest = item["manifest"]
                    if isinstance(manifest, Path):
                        manifest = json.loads(manifest.read_text(encoding="utf-8"))
                    self.manager.validate_patch_manifest(patch, manifest)
                    self.manager.apply_patch(self.staging, patch)
                    self._verify_manifest_on_staging(manifest)
                    self.accepted.append(
                        {
                            "task_id": str(manifest.get("task_id") or patch.stem),
                            "patch": str(patch),
                            "manifest": manifest,
                            "files": list(manifest.get("files") or []),
                        }
                    )
                self._digest = tree_digest(self.staging)
                self.write_integrated_manifest()
                return self._digest
            except Exception:
                self._restore_to_digest(before)
                raise

    def cleanup(self) -> None:
        self.manager.cleanup()
