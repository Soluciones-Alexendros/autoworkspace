"""D2/H2: one-time migration of the machine runtime to ``~/.machineroom``."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness.runtime import (  # noqa: E402
    LEGACY_RUNTIME_DIRNAME,
    RUNTIME_DIRNAME,
    InstallFailure,
    legacy_runtime_root,
    migrate_legacy_runtime,
    runtime_root,
    sync_payload,
)


def test_runtime_root_uses_new_brand(tmp_path: Path) -> None:
    assert RUNTIME_DIRNAME == ".machineroom"
    assert LEGACY_RUNTIME_DIRNAME == ".autoworkspace"
    assert runtime_root(tmp_path) == tmp_path / ".machineroom"
    assert legacy_runtime_root(tmp_path) == tmp_path / ".autoworkspace"


def test_migrate_moves_legacy_runtime(tmp_path: Path) -> None:
    legacy = tmp_path / ".autoworkspace"
    (legacy / "skills").mkdir(parents=True)
    (legacy / "package.json").write_text('{"version": "7.1.4"}', encoding="utf-8")

    result = migrate_legacy_runtime(tmp_path)

    assert result["migrated"] is True
    assert result["from"] == str(legacy)
    assert result["to"] == str(tmp_path / ".machineroom")
    assert not legacy.exists()
    assert (tmp_path / ".machineroom" / "package.json").is_file()


def test_migrate_refuses_two_runtimes(tmp_path: Path) -> None:
    (tmp_path / ".autoworkspace").mkdir()
    (tmp_path / ".machineroom").mkdir()
    with pytest.raises(InstallFailure) as caught:
        migrate_legacy_runtime(tmp_path)
    assert caught.value.component == "runtime"
    assert caught.value.function == "migrate_legacy_runtime"
    assert "two runtimes" in caught.value.detail
    assert (tmp_path / ".autoworkspace").is_dir()


def test_migrate_refuses_legacy_symlink(tmp_path: Path) -> None:
    (tmp_path / ".autoworkspace").symlink_to(tmp_path / "elsewhere")
    with pytest.raises(InstallFailure, match="symlink"):
        migrate_legacy_runtime(tmp_path)


def test_migrate_is_idempotent(tmp_path: Path) -> None:
    already = migrate_legacy_runtime(tmp_path)
    assert already["migrated"] is False
    assert already["detail"] == "no legacy runtime"

    (tmp_path / ".machineroom").mkdir()
    second = migrate_legacy_runtime(tmp_path)
    assert second["migrated"] is False
    assert second["detail"] == "already migrated"


def test_sync_targets_new_runtime_and_marks_manifest(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    destination = runtime_root(home)
    manifest = sync_payload(ROOT, destination, origin="sync")
    assert destination.is_dir() and not destination.is_symlink()
    assert manifest["origin"] == "sync"
    assert (destination / ".runtime-manifest.json").is_file()
    assert not legacy_runtime_root(home).exists()
