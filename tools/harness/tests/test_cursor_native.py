"""Cursor discovery B and policy C without requiring live model auth."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness.cursor import discovery_check, policy_check, resolve_agent_binary  # noqa: E402
from harness.cursor_install import install_full  # noqa: E402


def test_policy_allow_deny_ask_sentinel(tmp_path: Path) -> None:
    check = policy_check(tmp_path / "policy")
    assert check.outcome == "pass", check
    assert (tmp_path / "policy" / "sentinel-allow.txt").read_text(encoding="utf-8") == "allow-ok\n"
    assert not (tmp_path / "policy" / "sentinel-deny.txt").exists()
    assert not (tmp_path / "policy" / "sentinel-ask.txt").exists()


def test_discovery_after_full_install(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    result = install_full(ROOT, target)
    assert result["status"] == "ok"
    expected = {
        path.name
        for path in (ROOT / "skills").iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    }
    check = discovery_check(target, expected)
    assert check.outcome == "pass", check
    assert "aw-verifier.md" in check.detail


def test_agent_binary_resolvable_when_on_path() -> None:
    binary = resolve_agent_binary()
    # Environment-dependent: presence is asserted by native shell smoke.
    if binary:
        assert Path(binary).exists()
