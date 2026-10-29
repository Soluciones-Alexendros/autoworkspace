"""Deterministic tests for .cursor/hooks/shell_gate.py (stdin JSON → permission)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
GATE = REPO / ".cursor" / "hooks" / "shell_gate.py"


def _load_gate():
    spec = importlib.util.spec_from_file_location("shell_gate", GATE)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_stdin(payload: bytes | str) -> tuple[int, dict]:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    proc = subprocess.run(
        [sys.executable, str(GATE)],
        input=payload,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr.decode("utf-8", errors="replace")
    out = json.loads(proc.stdout.decode("utf-8"))
    return proc.returncode, out


def test_apt_get_upgrade_is_deny() -> None:
    code, out = _run_stdin(json.dumps({"command": "apt-get upgrade"}))
    assert code == 0
    assert out["permission"] == "deny"
    assert "run_registered" in out["agent_message"]
    assert "local-maintenance" in out["agent_message"]


def test_curl_example_is_ask() -> None:
    # Outbound network without local --help/-h/--version stays ask (doubt → ask, never allow).
    code, out = _run_stdin(json.dumps({"command": "curl https://example.com"}))
    assert code == 0
    assert out["permission"] == "ask"


def test_empty_json_object_is_deny_not_allow() -> None:
    code, out = _run_stdin("{}")
    assert code == 0
    assert out["permission"] == "deny"
    assert out["permission"] != "allow"


def test_invalid_json_is_deny_not_allow() -> None:
    code, out = _run_stdin("{not-json")
    assert code == 0
    assert out["permission"] == "deny"
    assert out["permission"] != "allow"


def test_script_does_not_invoke_shell(tmp_path: Path) -> None:
    """If the gate executed the payload, it would create the sentinel file."""
    sentinel = tmp_path / "sentinel"
    # Deliberately dangerous-looking command that would create the file if exec'd.
    cmd = f"touch {sentinel}"
    # Force matcher path via sudo so decide() runs; must not create sentinel.
    code, out = _run_stdin(json.dumps({"command": f"sudo {cmd}"}))
    assert code == 0
    assert out["permission"] == "deny"
    assert not sentinel.exists()


def test_curl_help_is_allow() -> None:
    mod = _load_gate()
    assert mod.decide({"command": "curl --help"})["permission"] == "allow"


def test_missing_command_field_is_deny() -> None:
    mod = _load_gate()
    assert mod.decide({"cwd": "/tmp"})["permission"] == "deny"


def test_empty_stdin_is_deny_not_allow() -> None:
    code, out = _run_stdin(b"")
    assert code == 0
    assert out["permission"] == "deny"
    assert out["permission"] != "allow"


def test_non_string_command_is_deny() -> None:
    mod = _load_gate()
    assert mod.decide({"command": ["apt-get", "upgrade"]})["permission"] == "deny"


@pytest.mark.parametrize(
    ("command", "skill_hint"),
    [
        ("sudo pacman -Syu", "local-"),
        ("systemctl restart sshd", "local-"),
        ("rm -rf /tmp/x", "local-"),
        ("mkfs.ext4 /dev/sdz", "local-"),
        ("dd if=/dev/zero of=/tmp/x bs=1M count=1", "local-"),
        ("shutdown -h now", "local-maintenance"),
        ("iptables -F", "local-security"),
        ("ssh user@host", "local-"),
    ],
)
def test_deny_families_point_at_run_registered(command: str, skill_hint: str) -> None:
    code, out = _run_stdin(json.dumps({"command": command}))
    assert code == 0
    assert out["permission"] == "deny"
    assert "run_registered" in out["agent_message"]
    assert skill_hint in out["agent_message"]


def test_wget_network_is_ask() -> None:
    code, out = _run_stdin(json.dumps({"command": "wget https://example.com"}))
    assert code == 0
    assert out["permission"] == "ask"


def test_decide_fallback_ask_for_unclassified_match() -> None:
    # Hook matcher may fire on strings the deny/network branches do not classify.
    mod = _load_gate()
    assert mod.decide({"command": "echo matched-but-unclassified"})["permission"] == "ask"


def test_session_start_emits_additional_context() -> None:
    script = REPO / ".cursor" / "hooks" / "session_start.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        input=b'{"session_id":"t","is_background_agent":false}',
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr.decode("utf-8", errors="replace")
    out = json.loads(proc.stdout.decode("utf-8"))
    assert "additional_context" in out
    assert "run_registered" in out["additional_context"]
    assert "--bump" in out["additional_context"]
    assert out["additional_context"].strip()
    # Hooks must not use exit 2 (deny-via-exit); permission is in JSON only.
    assert proc.returncode == 0

