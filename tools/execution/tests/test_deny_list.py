"""Shared shell-gate policy: data parity and decision parity with the Cursor hook."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from execution.deny_list import (  # noqa: E402
    DenyListError,
    decide_command,
    deny_list_path,
    load_policy,
)

HOOK = ROOT / ".cursor" / "hooks" / "shell_gate.py"
POLICY = deny_list_path(ROOT)


def _hook(payload: object) -> dict[str, str]:
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    decision: dict[str, str] = json.loads(proc.stdout)
    return decision


def test_policy_file_is_shipped_with_the_extension() -> None:
    assert POLICY.is_file()
    assert POLICY.parent == ROOT / "extensions" / "machineroom"
    raw = json.loads(POLICY.read_text(encoding="utf-8"))
    ids = [rule["id"] for rule in raw["deny"]]
    assert ids.count("rm-rf") == 1
    assert {"package-manager", "systemctl", "privilege", "remote-shell"} <= set(ids)
    assert raw["network"]["id"] == "outbound-network"
    assert "/tmp/machineroom-" in raw["allow"]["tmpPrefixes"]


def test_policy_loads_with_compiled_patterns() -> None:
    policy = load_policy(ROOT)
    assert all(isinstance(rule.pattern, re.Pattern) for rule in policy.deny)
    assert policy.rm_rf.pattern is policy.rm_rf.pattern


@pytest.mark.parametrize(
    "command",
    [
        "sudo pacman -Syu",
        "systemctl restart nginx",
        "rm -rf /home/user/documents",
        "mkfs.ext4 /dev/sda1",
        "dd if=/dev/zero of=/dev/sda",
        "shutdown -h now",
        "ufw disable",
        "ssh host",
        "apt-get upgrade",
    ],
)
def test_deny_rules_block_host_mutation(command: str) -> None:
    assert _hook({"command": command})["permission"] == "deny"


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf /tmp/machineroom-install-1",
        "rm -rf /tmp/test-cursor /tmp/test-pi",
        "curl --version",
    ],
)
def test_allow_exceptions(command: str) -> None:
    assert _hook({"command": command})["permission"] == "allow"


@pytest.mark.parametrize("command", ["curl https://example.com", "wget http://x/y", "git status"])
def test_network_and_unmatched_ask(command: str) -> None:
    assert _hook({"command": command})["permission"] == "ask"


def test_malformed_payloads_are_fail_closed() -> None:
    assert _hook({})["permission"] == "deny"
    assert _hook({"command": 42})["permission"] == "deny"


def test_python_and_hook_agree_on_the_whole_matrix() -> None:
    policy = load_policy(ROOT)
    commands = [
        "sudo pacman -Syu",
        "rm -rf /tmp/machineroom-x",
        "rm -rf /etc",
        "curl --version",
        "curl https://example.com",
        "git status",
        "systemctl status",
        "npm test",
    ]
    for command in commands:
        engine = decide_command(command, policy)
        hook = _hook({"command": command})
        assert engine == hook, command


def test_missing_policy_is_a_structured_failure(tmp_path: Path) -> None:
    with pytest.raises(DenyListError) as caught:
        load_policy(tmp_path)
    assert caught.value.component == "deny-list"
    assert caught.value.function == "load_policy"
    assert "unreadable" in caught.value.detail


def test_invalid_json_is_a_structured_failure(tmp_path: Path) -> None:
    target = deny_list_path(tmp_path)
    target.parent.mkdir(parents=True)
    target.write_text("{not-json", encoding="utf-8")
    with pytest.raises(DenyListError, match="invalid JSON"):
        load_policy(tmp_path)


def test_rule_without_rm_rf_is_rejected(tmp_path: Path) -> None:
    target = deny_list_path(tmp_path)
    target.parent.mkdir(parents=True)
    target.write_text(
        json.dumps(
            {
                "version": 1,
                "deny": [{"id": "x", "pattern": "x", "message": "m"}],
                "network": {"id": "net", "pattern": "curl", "message": "m"},
                "allow": {"helpOrVersion": "--help", "tmpPrefixes": ["/tmp/x-"]},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(DenyListError, match="rm-rf"):
        load_policy(tmp_path)
