"""Machine runtime sync and relative user-link helpers."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness.cursor_install import ConflictError, install_full, uninstall_full  # noqa: E402
from harness.doctor import cursor_full_check, skill_link_check  # noqa: E402
from harness.runtime import make_relative_symlink, sync_payload  # noqa: E402

USER_SCOPE_COMPONENTS = 23  # 17 skills + 3 agents + hooks.json + 2 hook scripts


def _runtime(home: Path) -> Path:
    dest = home / ".autoworkspace"
    sync_payload(ROOT, dest, origin="sync")
    return dest


def test_sync_payload_rejects_symlink_destination(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    dest = home / ".autoworkspace"
    dest.symlink_to(tmp_path / "elsewhere")
    with pytest.raises(ValueError, match="symlink"):
        sync_payload(ROOT, dest, origin="sync")


def test_sync_payload_copies_harness_payload(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    manifest = sync_payload(ROOT, home / ".autoworkspace", origin="sync")
    runtime = home / ".autoworkspace"
    assert runtime.is_dir() and not runtime.is_symlink()
    assert (runtime / "skills" / "plan-continue" / "SKILL.md").is_file()
    assert (runtime / ".cursor" / "agents" / "aw-verifier.md").is_file()
    assert (runtime / "extensions" / "autoworkspace" / "index.ts").is_file()
    assert manifest["origin"] == "sync"
    assert (runtime / ".runtime-manifest.json").is_file()


def test_user_scope_relative_links_from_runtime(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    runtime = _runtime(home)
    target = home / ".cursor"
    result = install_full(ROOT, target, user_scope=True)
    assert result["scope"] == "user"
    assert result["installed"] == USER_SCOPE_COMPONENTS
    assert result["source_root"] == str(runtime.resolve())
    hooks = target / "hooks.json"
    assert hooks.is_symlink()
    assert not Path(os.readlink(hooks)).is_absolute()
    assert hooks.resolve() == (runtime / ".cursor" / "hooks.json").resolve()
    data = json.loads(hooks.read_text(encoding="utf-8"))
    commands = [entry["command"] for entries in data["hooks"].values() for entry in entries]
    assert commands and not any(".cursor/hooks/" in command for command in commands), commands
    skill = target / "skills" / "plan-continue"
    assert skill.is_symlink()
    assert not Path(os.readlink(skill)).is_absolute()
    assert skill.resolve() == (runtime / "skills" / "plan-continue").resolve()
    assert "Work/autoworkspace" not in os.readlink(skill)
    second = install_full(ROOT, target, user_scope=True)
    assert second["changed"] == 0
    assert second["skipped"] == USER_SCOPE_COMPONENTS
    check = cursor_full_check(home)
    assert check.outcome == "pass", check.detail
    uninstalled = uninstall_full(runtime, target)
    assert uninstalled["retained"] == []
    assert not hooks.exists()


def test_user_scope_requires_runtime(tmp_path: Path) -> None:
    home = tmp_path / "home"
    target = home / ".cursor"
    target.mkdir(parents=True)
    with pytest.raises(ValueError, match="runtime missing"):
        install_full(ROOT, target, user_scope=True)


def test_user_scope_preserves_foreign_hooks_file(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    _runtime(home)
    target = home / ".cursor"
    target.mkdir(parents=True)
    (target / "hooks.json").write_text('{"version": 1, "hooks": {}}', encoding="utf-8")
    with pytest.raises(ConflictError, match="real file/dir conflict"):
        install_full(ROOT, target, user_scope=True)
    assert (target / "hooks.json").read_text(encoding="utf-8") == '{"version": 1, "hooks": {}}'


def test_user_scope_migrates_prior_checkout_manifest(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    runtime = _runtime(home)
    target = home / ".cursor"
    # Simulate prior absolute install from the development checkout.
    target.mkdir(parents=True)
    (target / "skills").mkdir()
    old = target / "skills" / "plan-continue"
    old.symlink_to(ROOT / "skills" / "plan-continue")
    manifest = {
        "schema_version": 2,
        "source_root": str(ROOT),
        "components": "full",
        "scope": "user",
        "resources": [{"path": "skills/plan-continue", "kind": "symlink"}],
        "omitted": ["rules/autoworkspace.mdc"],
        "version": "7.1.2",
    }
    (target / ".autoworkspace-full-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    result = install_full(ROOT, target, user_scope=True)
    assert result["status"] == "ok"
    assert old.resolve() == (runtime / "skills" / "plan-continue").resolve()
    assert not Path(os.readlink(old)).is_absolute()


def test_relative_skill_links_pass_doctor(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    runtime = _runtime(home)
    skills = home / ".cursor" / "skills"
    skills.mkdir(parents=True)
    for skill in (runtime / "skills").iterdir():
        if skill.is_dir() and (skill / "SKILL.md").is_file():
            make_relative_symlink(skill, skills / skill.name)
    check = skill_link_check(home, "cursor", source_root=runtime)
    assert check.outcome == "pass", check.detail
    assert "relative" in check.detail
