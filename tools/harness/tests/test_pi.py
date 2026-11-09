"""Pi RPC discovery parsing and capability outcomes."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import pi  # noqa: E402


def _commands(names: list[str], origin: str = "package") -> list[dict[str, Any]]:
    return [
        {
            "name": f"skill:{name}",
            "source": "skill",
            "sourceInfo": {"origin": origin, "path": f"/package/skills/{name}/SKILL.md"},
        }
        for name in names
    ]


def test_rpc_response_requires_successful_get_commands() -> None:
    response = {
        "type": "response",
        "command": "get_commands",
        "success": True,
        "data": {"commands": _commands(["one"])},
    }
    assert pi.skill_commands(response) == _commands(["one"])
    with pytest.raises(ValueError, match="get_commands"):
        pi.skill_commands({"type": "response", "success": False})


def test_discovery_checks_names_and_package_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/pi")
    monkeypatch.setattr(pi, "rpc_commands", lambda cwd: _commands(["one", "two"]))
    check = pi.discovery_check(Path("."), {"one", "two"})
    assert check.outcome == "pass"


def test_discovery_rejects_missing_or_non_package_skill(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/pi")
    monkeypatch.setattr(pi, "rpc_commands", lambda cwd: _commands(["one"], origin="top-level"))
    check = pi.discovery_check(Path("."), {"one", "two"})
    assert check.outcome == "fail"
    assert "two" in check.detail or "package" in check.detail


def test_missing_binary_is_not_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: None)
    check = pi.discovery_check(Path("."), {"one"})
    assert check.outcome == "not_run"
