"""Shared shell-gate decision engine (Cursor hook + Pi extension data).

The policy lives in ``extensions/machineroom/deny-list.json`` so the same file
ships with the Pi runtime payload and is read by the Cursor hook. Decision order
is deterministic: explicit ``rm -rf`` under approved ``/tmp`` prefixes allows,
otherwise the first deny rule wins, then outbound network asks, then anything the
hook matcher forwarded asks.

Failure modes (``DenyListError`` with ``component``/``function``/``detail``):
missing file, unreadable file, invalid JSON, wrong shape, and invalid regexes.
Every failure is fail-closed: ``decide`` raises and the caller must answer deny.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

COMPONENT = "deny-list"
DENY_LIST_NAME = Path("extensions") / "machineroom" / "deny-list.json"
PERMISSION_DENY = "deny"
PERMISSION_ASK = "ask"
PERMISSION_ALLOW = "allow"


class DenyListError(ValueError):
    """Structured deny-list failure: component + function + detail."""

    def __init__(self, function: str, detail: str) -> None:
        self.component = COMPONENT
        self.function = function
        self.detail = detail
        super().__init__(f"FAIL {COMPONENT} {function}: {detail}")

    def to_dict(self) -> dict[str, str]:
        return {"component": self.component, "function": self.function, "detail": self.detail}


@dataclass(frozen=True)
class Rule:
    """One deny rule: stable id, compiled pattern and operator-facing message."""

    rule_id: str
    pattern: re.Pattern[str]
    message: str


@dataclass(frozen=True)
class Policy:
    """Loaded shell-gate policy, ready to decide commands."""

    deny: tuple[Rule, ...]
    network: Rule
    help_or_version: re.Pattern[str]
    tmp_prefixes: tuple[str, ...]
    rm_rf: re.Pattern[str]


def deny_list_path(root: Path) -> Path:
    """Return the policy path for a repository or runtime root."""
    return Path(root).resolve() / DENY_LIST_NAME


def _rule(raw: Any, function: str) -> Rule:
    if not isinstance(raw, dict):
        raise DenyListError(function, f"rule must be an object: {raw!r}")
    rule_id = str(raw.get("id", "")).strip()
    pattern = str(raw.get("pattern", ""))
    message = str(raw.get("message", "")).strip()
    if not rule_id or not pattern or not message:
        raise DenyListError(function, f"rule needs id, pattern and message: {raw!r}")
    try:
        compiled = re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        raise DenyListError(function, f"invalid regex in rule {rule_id!r}: {exc}") from exc
    return Rule(rule_id, compiled, message)


def load_policy(root: Path) -> Policy:
    """Load and validate the policy. Raises ``DenyListError`` on any problem."""
    function = "load_policy"
    path = deny_list_path(root)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise DenyListError(function, f"unreadable deny list: {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise DenyListError(function, f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("deny"), list) or not raw["deny"]:
        raise DenyListError(function, f"deny must be a non-empty list: {path}")
    allow = raw.get("allow")
    if not isinstance(allow, dict):
        raise DenyListError(function, f"allow must be an object: {path}")
    prefixes = allow.get("tmpPrefixes")
    if not isinstance(prefixes, list) or not prefixes or not all(isinstance(p, str) for p in prefixes):
        raise DenyListError(function, "allow.tmpPrefixes must be a non-empty string list")
    help_or_version = str(allow.get("helpOrVersion", "")).strip()
    if not help_or_version:
        raise DenyListError(function, "allow.helpOrVersion is required")
    try:
        help_pattern = re.compile(help_or_version)
    except re.error as exc:
        raise DenyListError(function, f"invalid allow.helpOrVersion: {exc}") from exc
    deny = tuple(_rule(item, function) for item in raw["deny"])
    network = _rule(raw.get("network"), function)
    rm_rf_rule = next((rule for rule in deny if rule.rule_id == "rm-rf"), None)
    if rm_rf_rule is None:
        raise DenyListError(function, "deny list must keep the 'rm-rf' rule for the /tmp exception")
    return Policy(
        deny=deny,
        network=network,
        help_or_version=help_pattern,
        tmp_prefixes=tuple(prefixes),
        rm_rf=rm_rf_rule.pattern,
    )


def _allow_message() -> str:
    return "Allowed by the shell gate: command matches an explicit exception."


def _rm_rf_only_allowed_tmp(command: str, policy: Policy) -> bool:
    """True when every absolute path after ``rm -rf`` sits under an approved prefix."""
    if not policy.rm_rf.search(command):
        return False
    paths = re.findall(r"(?:^|\s)(/[^\s;|&]+)", command)
    if not paths:
        return False
    return all(path.startswith(policy.tmp_prefixes) for path in paths)


def decide_command(command: str, policy: Policy) -> dict[str, str]:
    """Return ``{permission, user_message, agent_message}`` for one shell command."""
    if _rm_rf_only_allowed_tmp(command, policy):
        return {"permission": PERMISSION_ALLOW, "user_message": _allow_message(), "agent_message": _allow_message()}
    for rule in policy.deny:
        if rule.pattern.search(command):
            return {
                "permission": PERMISSION_DENY,
                "user_message": f"Blocked host-mutating or privileged shell: {command[:120]}",
                "agent_message": rule.message,
            }
    if policy.network.pattern.search(command):
        if policy.help_or_version.search(command):
            return {
                "permission": PERMISSION_ALLOW,
                "user_message": _allow_message(),
                "agent_message": _allow_message(),
            }
        return {
            "permission": PERMISSION_ASK,
            "user_message": f"Network shell requires confirmation: {command[:120]}",
            "agent_message": policy.network.message,
        }
    return {
        "permission": PERMISSION_ASK,
        "user_message": f"Shell gate matched; confirm: {command[:120]}",
        "agent_message": "Command matched the host/network matcher. Prefer run_registered; ask the operator.",
    }
