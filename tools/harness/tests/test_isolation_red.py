"""RED: reproduce isolation defects (inherited env, writer shell, --force).

These assertions encode the desired least-privilege contract. They must fail on
the audited baseline for the documented cause; GREEN comes in T04–T06.
"""

from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness.cursor import CursorSubagentAdapter  # noqa: E402
from harness.pi import PiSubagentAdapter  # noqa: E402
from orchestrator.model import RunContext  # noqa: E402


FIXTURE_SECRET = "AW_FIXTURE_SECRET_NOT_REAL"
FIXTURE_SECRET_VALUE = "red-secret-value-not-real"


def _capture_binary(tmp_path: Path, name: str, *, pi_jsonl: bool) -> Path:
    """Fake harness that dumps argv/env to capture.json (avoids OpResult detail truncation)."""
    path = tmp_path / name
    capture = tmp_path / "capture.json"
    if pi_jsonl:
        body = f"""#!/usr/bin/env python3
import json, os, sys
payload = {{"args": sys.argv[1:], "env": dict(os.environ)}}
Path = __import__("pathlib").Path
Path({str(capture)!r}).write_text(json.dumps(payload), encoding="utf-8")
print(json.dumps({{
    "type": "message_end",
    "message": {{
        "role": "assistant",
        "content": [{{"type": "text", "text": "captured"}}],
        "stopReason": "stop",
    }},
}}))
"""
    else:
        body = f"""#!/usr/bin/env python3
import json, os, sys
payload = {{"args": sys.argv[1:], "env": dict(os.environ)}}
Path = __import__("pathlib").Path
Path({str(capture)!r}).write_text(json.dumps(payload), encoding="utf-8")
print("captured")
"""
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def _load_capture(tmp_path: Path) -> dict[str, Any]:
    data = json.loads((tmp_path / "capture.json").read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"capture.json must be an object, got {type(data).__name__}")
    return data


def _context(tmp_path: Path) -> RunContext:
    return RunContext(tmp_path, "isolation-red", "a" * 64, "0" * 40, "run-isolation-red", "pi")


def _write_task() -> dict[str, Any]:
    return {
        "id": "isolation-writer",
        "phase": "IMPLEMENT",
        "operation": "implement_api",
        "roles": ["role-back"],
        "write_scope": ["out.txt"],
    }


def test_pi_writer_tools_exclude_arbitrary_shell(tmp_path: Path) -> None:
    """Writers must not receive bash/shell; baseline currently appends bash."""
    adapter = PiSubagentAdapter(binary=str(_capture_binary(tmp_path, "pi-red", pi_jsonl=True)))
    result = adapter.execute(_write_task(), _context(tmp_path))
    assert result.outcome == "succeeded", result.detail
    args = _load_capture(tmp_path)["args"]
    tools_idx = args.index("--tools")
    tools = {name.strip() for name in args[tools_idx + 1].split(",")}
    assert "bash" not in tools
    assert "sh" not in tools
    assert {"write", "edit"} <= tools


def test_pi_child_env_denies_unauthorized_parent_secrets(tmp_path: Path, monkeypatch: Any) -> None:
    """Child env is deny-by-default; baseline inherits the parent environment."""
    monkeypatch.setenv(FIXTURE_SECRET, FIXTURE_SECRET_VALUE)
    assert os.environ.get(FIXTURE_SECRET) == FIXTURE_SECRET_VALUE
    adapter = PiSubagentAdapter(binary=str(_capture_binary(tmp_path, "pi-red", pi_jsonl=True)))
    result = adapter.execute(_write_task(), _context(tmp_path))
    assert result.outcome == "succeeded", result.detail
    child_env = _load_capture(tmp_path)["env"]
    assert FIXTURE_SECRET not in child_env
    assert FIXTURE_SECRET_VALUE not in child_env.values()


def test_cursor_writer_argv_never_includes_force_or_yolo(tmp_path: Path) -> None:
    """Acceptance must reject auto-approval; argv never carries --force/--yolo."""
    with pytest.raises(ValueError, match="force|yolo|auto-approval"):
        CursorSubagentAdapter(
            binary=str(_capture_binary(tmp_path, "agent-red", pi_jsonl=False)),
            force=True,
        )
    adapter = CursorSubagentAdapter(
        binary=str(_capture_binary(tmp_path, "agent-red", pi_jsonl=False)),
        force=False,
    )
    result = adapter.execute(_write_task(), _context(tmp_path))
    assert result.outcome == "succeeded", result.detail
    args = _load_capture(tmp_path)["args"]
    assert "--force" not in args
    assert "--yolo" not in args
    assert not any(arg == "--force" or arg.startswith("--force=") for arg in args)


def test_cursor_child_env_denies_unauthorized_parent_secrets(tmp_path: Path, monkeypatch: Any) -> None:
    """Cursor child must not inherit unauthorized secrets from the parent."""
    monkeypatch.setenv(FIXTURE_SECRET, FIXTURE_SECRET_VALUE)
    adapter = CursorSubagentAdapter(
        binary=str(_capture_binary(tmp_path, "agent-red", pi_jsonl=False)),
        force=False,
    )
    result = adapter.execute(_write_task(), _context(tmp_path))
    assert result.outcome == "succeeded", result.detail
    child_env = _load_capture(tmp_path)["env"]
    assert FIXTURE_SECRET not in child_env
    assert FIXTURE_SECRET_VALUE not in child_env.values()
