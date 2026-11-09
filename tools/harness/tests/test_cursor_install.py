"""Transactional full Cursor component installation."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness.cursor_install import ConflictError, install_full, uninstall_full  # noqa: E402


def test_full_install_idempotence_and_manifest(tmp_path: Path) -> None:
    target = tmp_path / "project"
    first = install_full(ROOT, target)
    expected = 24
    assert first["installed"] == expected
    assert first["changed"] == expected
    assert first["components"] == "full"
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
        if calls == 2:
            raise OSError("injected symlink failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(os, "symlink", fail_second)
    with pytest.raises(OSError, match="injected"):
        install_full(ROOT, target)
    assert calls == 2
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
