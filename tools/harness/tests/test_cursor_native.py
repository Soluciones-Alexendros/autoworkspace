"""Cursor static A vs native B/C contracts without requiring live model auth for A."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness.cursor import (  # noqa: E402
    policy_check,
    resolve_agent_binary,
    static_install_check,
)
from harness.cursor_install import install_full  # noqa: E402


def test_policy_check_not_run_without_agent(tmp_path: Path) -> None:
    with patch("harness.cursor.resolve_agent_binary", return_value=None):
        check = policy_check(tmp_path / "project")
    assert check.outcome == "not_run", check
    assert "binary" in check.detail.lower()


def test_policy_check_not_run_without_auth(tmp_path: Path) -> None:
    with (
        patch("harness.cursor.resolve_agent_binary", return_value="/usr/bin/agent"),
        patch("harness.cursor.agent_authenticated", return_value=False),
    ):
        check = policy_check(tmp_path / "project")
    assert check.outcome == "not_run", check
    assert "authentication" in check.detail.lower()


def test_static_install_after_full_install(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    result = install_full(ROOT, target)
    assert result["status"] == "ok"
    expected = {path.name for path in (ROOT / "skills").iterdir() if path.is_dir() and (path / "SKILL.md").is_file()}
    check = static_install_check(target, expected)
    assert check.outcome == "pass", check
    assert "mr-verifier.md" in check.detail


def test_agent_binary_resolvable_when_on_path() -> None:
    binary = resolve_agent_binary()
    if binary:
        assert Path(binary).exists()
