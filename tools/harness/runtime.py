"""Machine runtime under ``$HOME/.autoworkspace`` (shared Cursor/Pi catalog)."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

RUNTIME_DIRNAME = ".autoworkspace"
MANIFEST_NAME = ".runtime-manifest.json"
PAYLOAD_DIRS = ("skills", "extensions/autoworkspace")
PAYLOAD_CURSOR = (".cursor/agents", ".cursor/hooks", ".cursor/rules")
PAYLOAD_FILES = ("package.json", ".cursor/hooks.json")


class InstallFailure(ValueError):
    """Structured install/update failure: component + function + detail."""

    def __init__(self, component: str, function: str, detail: str) -> None:
        self.component = component
        self.function = function
        self.detail = detail
        super().__init__(format_failure(component, function, detail))

    def to_dict(self) -> dict[str, str]:
        return {"component": self.component, "function": self.function, "detail": self.detail}


def format_failure(component: str, function: str, detail: str) -> str:
    return f"FAIL {component} {function}: {detail}"


def runtime_root(home: Path | None = None) -> Path:
    return (home or Path.home()) / RUNTIME_DIRNAME


def require_runtime(home: Path | None = None) -> Path:
    root = runtime_root(home)
    if root.is_symlink():
        raise InstallFailure("runtime", "require_runtime", f"runtime must be a real directory, not a symlink: {root}")
    if not root.is_dir():
        raise InstallFailure(
            "runtime",
            "require_runtime",
            f"runtime missing: {root} (run scripts/runtime-sync.sh sync first)",
        )
    if not (root / "skills").is_dir() or not (root / "package.json").is_file():
        raise InstallFailure("runtime", "require_runtime", f"runtime incomplete: {root}")
    return root.resolve()


def relative_link_text(source: Path, destination: Path) -> str:
    """Return a relative symlink text from destination to source (both may not exist yet)."""
    return os.path.relpath(str(source.resolve()), start=str(destination.parent.resolve()))


def make_relative_symlink(source: Path, destination: Path) -> None:
    if destination.is_symlink() or destination.is_file():
        destination.unlink()
    elif destination.exists():
        raise InstallFailure(
            destination.name,
            "make_relative_symlink",
            f"cannot replace non-symlink path: {destination}",
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(relative_link_text(source, destination), destination)


def _copy_tree(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest, symlinks=False)


def _digest_tree(root: Path) -> str:
    hasher = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_dir() or path.is_symlink():
            continue
        rel = path.relative_to(root).as_posix()
        hasher.update(rel.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(path.read_bytes())
        hasher.update(b"\0")
    return hasher.hexdigest()


def _verify_payload_tree(root: Path, *, function: str) -> None:
    for relative in PAYLOAD_DIRS + PAYLOAD_CURSOR:
        path = root / relative
        if not path.is_dir():
            raise InstallFailure(relative, function, f"payload missing directory: {path}")
    for relative in PAYLOAD_FILES:
        path = root / relative
        if not path.is_file():
            raise InstallFailure(relative, function, f"payload missing file: {path}")


def sync_payload(source: Path, destination: Path, *, origin: str) -> dict[str, Any]:
    """Copy the harness payload into a real ``~/.autoworkspace`` directory."""
    source = source.resolve()
    if destination.is_symlink():
        raise InstallFailure("runtime", "sync_payload", f"runtime destination is a symlink: {destination}")
    destination = destination.resolve() if destination.exists() else destination.absolute()
    try:
        destination.relative_to(source)
    except ValueError:
        pass
    else:
        raise InstallFailure("runtime", "sync_payload", f"runtime destination is inside source: {destination}")
    for privileged in ("/", "/etc", "/usr", "/var", "/root"):
        if destination == Path(privileged):
            raise InstallFailure("runtime", "sync_payload", f"privileged runtime rejected: {destination}")

    staging = destination.parent / f".autoworkspace-staging-{os.getpid()}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    backup: Path | None = None

    try:
        for relative in PAYLOAD_DIRS:
            src = source / relative
            if not src.is_dir():
                raise InstallFailure(relative, "sync_payload", f"payload missing directory: {src}")
            _copy_tree(src, staging / relative)
        for relative in PAYLOAD_CURSOR:
            src = source / relative
            if not src.is_dir():
                raise InstallFailure(relative, "sync_payload", f"payload missing directory: {src}")
            _copy_tree(src, staging / relative)
        for relative in PAYLOAD_FILES:
            src = source / relative
            if not src.is_file():
                raise InstallFailure(relative, "sync_payload", f"payload missing file: {src}")
            dest = staging / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

        _verify_payload_tree(staging, function="sync_payload")

        version = json.loads((staging / "package.json").read_text(encoding="utf-8"))["version"]
        digest = _digest_tree(staging)
        manifest: dict[str, Any] = {
            "schema_version": 1,
            "version": str(version),
            "digest": digest,
            "origin": origin,
            "source": str(source),
        }
        (staging / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        if destination.exists():
            backup = destination.parent / f".autoworkspace-backup-{os.getpid()}"
            if backup.exists():
                shutil.rmtree(backup)
            destination.rename(backup)
            try:
                staging.rename(destination)
            except OSError:
                backup.rename(destination)
                backup = None
                raise
            shutil.rmtree(backup)
            backup = None
        else:
            staging.rename(destination)
        _verify_payload_tree(destination, function="sync_payload")
    except Exception:
        if backup is not None and backup.exists() and not destination.exists():
            backup.rename(destination)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)

    return manifest


def write_user_hooks_config(runtime: Path) -> Path:
    """Rewrite runtime hooks.json for user-scope Cursor (cwd is ~/.cursor)."""
    path = runtime / ".cursor" / "hooks.json"
    try:
        raw = path.read_text(encoding="utf-8")
        data: dict[str, Any] = json.loads(raw)
    except OSError as exc:
        raise InstallFailure("hooks.json", "write_user_hooks_config", f"unreadable hooks.json: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise InstallFailure("hooks.json", "write_user_hooks_config", f"invalid hooks.json: {exc}") from exc
    for entries in data.get("hooks", {}).values():
        for entry in entries:
            command = str(entry.get("command", ""))
            entry["command"] = command.replace("python3 .cursor/", "python3 ", 1)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # Post-write validation: user-scope commands must not retain the project prefix.
    rewritten = json.loads(path.read_text(encoding="utf-8"))
    for entries in rewritten.get("hooks", {}).values():
        for entry in entries:
            command = str(entry.get("command", ""))
            if not command.startswith("python3 hooks/"):
                raise InstallFailure(
                    "hooks.json",
                    "write_user_hooks_config",
                    f"user hook command must start with 'python3 hooks/': {command!r}",
                )
            if ".cursor/hooks/" in command:
                raise InstallFailure(
                    "hooks.json",
                    "write_user_hooks_config",
                    f"user hook command still uses .cursor/hooks/: {command!r}",
                )
    return path
