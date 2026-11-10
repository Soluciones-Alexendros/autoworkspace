"""Transactional full Cursor component installation."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest  # noqa: I001 — keep pytest with stdlib for local style

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness.cursor_install import ConflictError, install_full, uninstall_full  # noqa: E402
from harness.runtime import sync_payload  # noqa: E402


def _user_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    sync_payload(ROOT, home / ".autoworkspace", origin="sync")
    return home


def test_full_install_idempotence_and_manifest(tmp_path: Path) -> None:
    target = tmp_path / "project"
    first = install_full(ROOT, target)
    expected = 24
    assert first["installed"] == expected
    assert first["changed"] == expected
    assert first["components"] == "full"
    assert first["scope"] == "project"
    assert first["omitted"] == []
    for relative in (
        ".cursor/skills/plan-continue",
        ".cursor/rules/autoworkspace.mdc",
        ".cursor/agents/aw-planner.md",
        ".cursor/agents/aw-worker.md",
        ".cursor/agents/aw-verifier.md",
        ".cursor/hooks.json",
        ".cursor/hooks/session_start.py",
        ".cursor/hooks/shell_gate.py",
    ):
        link = target / relative
        assert link.is_symlink(), relative
        assert Path(link.readlink()).is_absolute()
        assert link.exists()
    second = install_full(ROOT, target)
    assert second["changed"] == 0
    assert second["skipped"] == expected
    manifest = json.loads((target / ".cursor" / ".autoworkspace-full-manifest.json").read_text())
    assert len(manifest["resources"]) == expected


USER_SCOPE_COMPONENTS = 23  # 17 skills + 3 agents + hooks.json + 2 hook scripts


def test_user_scope_generates_hooks_and_omits_project_rule(tmp_path: Path) -> None:
    home = _user_home(tmp_path)
    target = home / ".cursor"
    result = install_full(ROOT, target, user_scope=True)
    assert result["scope"] == "user"
    assert result["installed"] == USER_SCOPE_COMPONENTS
    assert result["omitted"] == ["rules/autoworkspace.mdc"]
    assert result["notes"]
    hooks = target / "hooks.json"
    # User hooks run from ~/.cursor, so commands must not carry the .cursor/ prefix.
    data = json.loads(hooks.read_text())
    commands = [entry["command"] for entries in data["hooks"].values() for entry in entries]
    assert commands and not any(".cursor/hooks/" in command for command in commands), commands
    assert hooks.is_symlink()
    assert not Path(os.readlink(hooks)).is_absolute()
    assert not (target / "rules").exists()
    assert (target / "skills" / "plan-continue").is_symlink()
    assert (target / "agents" / "aw-verifier.md").is_symlink()
    second = install_full(ROOT, target, user_scope=True)
    assert second["changed"] == 0
    assert second["skipped"] == USER_SCOPE_COMPONENTS
    manifest = json.loads((target / ".autoworkspace-full-manifest.json").read_text())
    assert manifest["scope"] == "user"
    assert {"path": "hooks.json", "kind": "symlink"} in manifest["resources"]
    uninstalled = uninstall_full(home / ".autoworkspace", target)
    assert uninstalled["retained"] == []
    assert not hooks.exists()


def test_user_scope_prunes_project_only_rule_from_previous_manifest(tmp_path: Path) -> None:
    home = _user_home(tmp_path)
    target = home / ".cursor"
    # Seed a project-shaped install under the user path, then switch to user scope.
    install_full(ROOT, target)
    stale_rule = target / "rules" / "autoworkspace.mdc"
    assert stale_rule.is_symlink()
    result = install_full(ROOT, target, user_scope=True)
    assert result["pruned"] == ["rules/autoworkspace.mdc"]
    assert not stale_rule.exists()
    assert not (target / "rules").exists()
    assert (target / "hooks.json").is_symlink()


def test_user_scope_preserves_foreign_hooks_file(tmp_path: Path) -> None:
    home = _user_home(tmp_path)
    target = home / ".cursor"
    target.mkdir(parents=True)
    (target / "hooks.json").write_text('{"version": 1, "hooks": {}}', encoding="utf-8")
    with pytest.raises(ConflictError, match="real file/dir conflict"):
        install_full(ROOT, target, user_scope=True)
    assert (target / "hooks.json").read_text(encoding="utf-8") == '{"version": 1, "hooks": {}}'


def test_user_scope_retains_foreign_symlink_hooks(tmp_path: Path) -> None:
    home = _user_home(tmp_path)
    target = home / ".cursor"
    target.mkdir(parents=True)
    foreign = tmp_path / "foreign-hooks.json"
    foreign.write_text('{"version": 1, "hooks": {}}', encoding="utf-8")
    hooks = target / "hooks.json"
    hooks.symlink_to(foreign)
    with pytest.raises(ConflictError, match="foreign symlink conflict"):
        install_full(ROOT, target, user_scope=True)
    assert hooks.is_symlink() and hooks.resolve() == foreign.resolve()


def test_full_dry_run_creates_nothing(tmp_path: Path) -> None:
    target = tmp_path / "missing"
    result = install_full(ROOT, target, dry_run=True)
    assert result["dry_run"] is True
    assert not target.exists()


def test_real_conflict_aborts_before_any_write(tmp_path: Path) -> None:
    target = tmp_path / "project"
    (target / ".cursor" / "skills" / "plan-continue").mkdir(parents=True)
    with pytest.raises(ConflictError):
        install_full(ROOT, target)
    assert not (target / ".cursor" / "rules").exists()


def test_symlink_failure_rolls_back_prior_resources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "project"
    original = os.symlink
    calls = 0

    def fail_second(*args: Any, **kwargs: Any) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:  # noqa: PLR2004  # fail on second symlink
            raise OSError("injected symlink failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(os, "symlink", fail_second)
    with pytest.raises(OSError, match="injected"):
        install_full(ROOT, target)
    assert calls == 2  # noqa: PLR2004  # second call injected the failure
    assert not list(target.rglob("plan-continue"))


def test_uninstall_only_owned_unchanged_links(tmp_path: Path) -> None:
    target = tmp_path / "project"
    install_full(ROOT, target)
    foreign = target / ".cursor" / "rules" / "foreign.mdc"
    foreign.write_text("keep", encoding="utf-8")
    changed = target / ".cursor" / "skills" / "plan-continue"
    changed.unlink()
    changed.write_text("changed", encoding="utf-8")
    uninstall_full(ROOT, target)
    assert changed.read_text(encoding="utf-8") == "changed"
    assert foreign.read_text(encoding="utf-8") == "keep"
    assert not (target / ".cursor" / "skills" / "plan-validators").exists()
