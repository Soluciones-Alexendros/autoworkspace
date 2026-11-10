"""Immutable deny-by-default execution policy for Pi/Cursor subagents."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Any, Mapping

FORBIDDEN_FLAGS = frozenset({"--force", "--yolo", "-f"})
SENSITIVE_ENV_PREFIXES = (
    "AWS_",
    "AZURE_",
    "GH_",
    "GITHUB_",
    "GITLAB_",
    "OPENAI_",
    "ANTHROPIC_",
    "CURSOR_",
    "NPM_",
    "TWINE_",
    "PYPI_",
    "DOCKER_",
    "KUBE",
    "HCLOUD_",
    "DIGITALOCEAN_",
)
SENSITIVE_ENV_EXACT = frozenset(
    {
        "API_KEY",
        "TOKEN",
        "SECRET",
        "PASSWORD",
        "PASSWD",
        "CREDENTIAL",
        "CREDENTIALS",
        "PRIVATE_KEY",
        "AUTH",
        "AUTHORIZATION",
        "AW_FIXTURE_SECRET",
        "HYGIENE_DENYLIST",
        "AUTOWORKSPACE_PRIVATE_PATTERNS",
        "SSH_AUTH_SOCK",
        "SSH_AGENT_PID",
        "CURSOR_API_KEY",
    }
)
BASE_ENV_KEYS = frozenset(
    {
        "PATH",
        "HOME",
        "USER",
        "LOGNAME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TZ",
        "TMPDIR",
        "TMP",
        "TEMP",
        "TERM",
        "COLORTERM",
        "NO_COLOR",
        "CI",
        "PWD",
        "XDG_RUNTIME_DIR",
        "XDG_CACHE_HOME",
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
        "UV_CACHE_DIR",
        "VIRTUAL_ENV",
        "PYTHONPATH",
        "PYTHONNOUSERSITE",
        "PYTHONUTF8",
        "PYTHONIOENCODING",
    }
)
READ_TOOLS = ("read", "grep", "find", "ls")
WRITE_TOOLS = ("write", "edit")


def is_sensitive_env(name: str) -> bool:
    upper = name.upper()
    if upper in SENSITIVE_ENV_EXACT:
        return True
    if any(token in upper for token in ("SECRET", "TOKEN", "PASSWORD", "PASSWD", "API_KEY", "PRIVATE_KEY")):
        return True
    return any(upper.startswith(prefix) for prefix in SENSITIVE_ENV_PREFIXES)


@dataclass(frozen=True)
class ExecutionPolicy:
    harness: str
    tools: tuple[str, ...]
    env: tuple[tuple[str, str], ...]
    forbidden_flags: tuple[str, ...]
    write_scope: tuple[str, ...]
    read_scope: tuple[str, ...]
    allow_shell: bool
    timeout_s: int
    credential_names: tuple[str, ...]
    digest: str

    def env_mapping(self) -> dict[str, str]:
        return dict(self.env)

    def as_artifact(self) -> dict[str, Any]:
        return {
            "harness": self.harness,
            "tools": list(self.tools),
            "forbidden_flags": list(self.forbidden_flags),
            "write_scope": list(self.write_scope),
            "read_scope": list(self.read_scope),
            "allow_shell": self.allow_shell,
            "timeout_s": self.timeout_s,
            "credential_names": list(self.credential_names),
            "env_names": sorted(name for name, _ in self.env),
            "digest": self.digest,
        }


def build_child_env(
    parent: Mapping[str, str] | None = None,
    *,
    credential_names: tuple[str, ...] = (),
) -> dict[str, str]:
    """Construct a deny-by-default child environment (no implicit secret inheritance)."""
    source = dict(parent if parent is not None else os.environ)
    allowed_credentials = {name for name in credential_names if name}
    child: dict[str, str] = {}
    for key in sorted(BASE_ENV_KEYS):
        if key in source and not is_sensitive_env(key):
            child[key] = source[key]
    for key in sorted(allowed_credentials):
        if key in source:
            child[key] = source[key]
    return child


def tools_for_task(task: Mapping[str, Any]) -> tuple[str, ...]:
    tools: list[str] = list(READ_TOOLS)
    if task.get("write_scope"):
        tools.extend(WRITE_TOOLS)
    return tuple(tools)


def assert_argv_policy(argv: list[str]) -> None:
    lowered = set(argv)
    for flag in FORBIDDEN_FLAGS:
        if flag in lowered:
            raise ValueError(f"forbidden auto-approval flag in argv: {flag}")


def build_policy(
    *,
    harness: str,
    task: Mapping[str, Any],
    timeout_s: int = 300,
    allow_shell: bool = False,
    credential_names: tuple[str, ...] = (),
    parent_env: Mapping[str, str] | None = None,
) -> ExecutionPolicy:
    if allow_shell:
        raise ValueError("arbitrary shell is disabled for subagents by default")
    write_scope = tuple(str(item) for item in (task.get("write_scope") or ()))
    read_scope = tuple(str(item) for item in (task.get("read_scope") or ()))
    tools = tools_for_task(task)
    env = build_child_env(parent_env, credential_names=credential_names)
    payload = {
        "harness": harness,
        "tools": list(tools),
        "forbidden_flags": sorted(FORBIDDEN_FLAGS),
        "write_scope": list(write_scope),
        "read_scope": list(read_scope),
        "allow_shell": False,
        "timeout_s": timeout_s,
        "credential_names": list(credential_names),
        "env_names": sorted(env),
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return ExecutionPolicy(
        harness=harness,
        tools=tools,
        env=tuple(sorted(env.items())),
        forbidden_flags=tuple(sorted(FORBIDDEN_FLAGS)),
        write_scope=write_scope,
        read_scope=read_scope,
        allow_shell=False,
        timeout_s=timeout_s,
        credential_names=tuple(credential_names),
        digest=digest,
    )
