#!/usr/bin/env python3
"""beforeShellExecution gate for host mutation and outbound network.

The policy lives in ``extensions/machineroom/deny-list.json`` and is shared with
the Pi extension, so the two harnesses cannot drift. This script does not execute
the received command. Stdlib only. Always exit 0 with JSON: ``failClosed`` on the
hook definition covers a real crash, and internal errors answer ``deny``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from execution.deny_list import DenyListError, decide_command, load_policy  # noqa: E402


def _deny(user_message: str, agent_message: str) -> dict[str, str]:
    return {"permission": "deny", "user_message": user_message, "agent_message": agent_message}


def decide(payload: dict[str, object]) -> dict[str, str]:
    """Decide one payload. Any malformed input or policy error denies (fail-closed)."""
    if "command" not in payload:
        return _deny(
            "Shell gate: missing command field.",
            "beforeShellExecution payload lacked command; denied. Do not invent a command.",
        )
    command = payload["command"]
    if not isinstance(command, str):
        return _deny(
            "Shell gate: command must be a string.",
            "beforeShellExecution command was not a string; denied.",
        )
    try:
        policy = load_policy(ROOT)
    except DenyListError as exc:
        return _deny(
            "Shell gate: policy unavailable.",
            f"{exc}. Denied; fix the deny list or use run_registered.",
        )
    return decide_command(command, policy)


def main() -> int:
    try:
        raw = sys.stdin.read()
        try:
            payload = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            payload = None
        if not isinstance(payload, dict):
            result = _deny(
                "Shell gate: invalid JSON on stdin.",
                "beforeShellExecution stdin was empty or invalid JSON; denied.",
            )
        else:
            result = decide(payload)
    except Exception as exc:  # broad catch: never crash-open
        result = _deny(
            "Shell gate: internal error.",
            f"shell_gate.py exception: {type(exc).__name__}. Denied; use run_registered.",
        )
    json.dump(result, sys.stdout, ensure_ascii=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
