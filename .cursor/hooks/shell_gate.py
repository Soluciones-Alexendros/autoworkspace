#!/usr/bin/env python3
"""beforeShellExecution gate for host mutation and outbound network.

Does not execute the received command. Stdlib only. Always exit 0 with JSON.
failClosed on the hook definition covers real crashes; this script never uses
exit 2.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

_DENY_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\b(apt-get|apt|dnf|pacman)\b", re.I),
        "Package-manager mutation is denied. Use run_registered with local-maintenance.",
    ),
    (
        re.compile(r"\bsystemctl\b", re.I),
        "systemctl is denied. Use run_registered with local-maintenance or local-security.",
    ),
    (
        re.compile(r"\brm\s+-rf\b", re.I),
        "rm -rf is denied. Use run_registered with the matching local-* skill.",
    ),
    (
        re.compile(r"\bmkfs\b", re.I),
        "mkfs is denied. Host storage mutation requires run_registered (local-*).",
    ),
    (
        re.compile(r"\bdd\s+if=", re.I),
        "dd if= is denied. Host storage mutation requires run_registered (local-*).",
    ),
    (
        re.compile(r"\b(shutdown|reboot)\b", re.I),
        "shutdown/reboot is denied. Use run_registered with local-maintenance.",
    ),
    (
        re.compile(r"\b(iptables|nft|ufw)\b", re.I),
        "Firewall mutation is denied. Use run_registered with local-security.",
    ),
    (
        re.compile(r"\b(ssh|scp)\b", re.I),
        "ssh/scp is denied. Use run_registered with the matching local-* skill.",
    ),
    (
        re.compile(r"\bsudo\b", re.I),
        "sudo is denied. Use run_registered with the matching local-* skill.",
    ),
]

_HELP_OR_VERSION = re.compile(r"(^|\s)(--help|-h|--version)(\s|$)")


def _deny(user_message: str, agent_message: str) -> dict[str, str]:
    return {
        "permission": "deny",
        "user_message": user_message,
        "agent_message": agent_message,
    }


def _ask(user_message: str, agent_message: str) -> dict[str, str]:
    return {
        "permission": "ask",
        "user_message": user_message,
        "agent_message": agent_message,
    }


def _allow() -> dict[str, str]:
    return {"permission": "allow"}


def _is_help_or_version(command: str) -> bool:
    return bool(_HELP_OR_VERSION.search(command))


def decide(payload: dict[str, Any]) -> dict[str, str]:
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

    for pattern, agent_message in _DENY_PATTERNS:
        if pattern.search(command):
            return _deny(
                f"Blocked host-mutating or privileged shell: {command[:120]}",
                agent_message,
            )

    # Outbound network tools that matched the hook matcher (curl|wget|nc).
    # Allow only evident local help/version; real network stays ask (doubt → ask).
    if re.search(r"\b(curl|wget|nc)\b", command, re.I):
        if _is_help_or_version(command):
            return _allow()
        return _ask(
            f"Network shell requires confirmation: {command[:120]}",
            "Outbound network matched the shell gate. Prefer run_registered; ask the operator.",
        )

    return _ask(
        f"Shell gate matched; confirm: {command[:120]}",
        "Command matched the host/network matcher. Prefer run_registered; ask the operator.",
    )


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
    except Exception as exc:  # noqa: BLE001 — must never crash open; failClosed covers real crash
        result = _deny(
            "Shell gate: internal error.",
            f"shell_gate.py exception: {type(exc).__name__}. Denied; use run_registered.",
        )
    json.dump(result, sys.stdout, ensure_ascii=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
