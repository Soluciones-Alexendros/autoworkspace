"""Unit tests for deny-by-default execution policy."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness.policy import (  # noqa: E402
    assert_argv_policy,
    build_child_env,
    build_policy,
    tools_for_task,
)


def test_build_child_env_drops_secrets() -> None:
    env = build_child_env(
        {
            "PATH": "/usr/bin",
            "HOME": "/tmp/home",
            "MR_FIXTURE_SECRET": "nope",
            "GITHUB_TOKEN": "ghs_nope",
            "LANG": "C",
        }
    )
    assert env["PATH"] == "/usr/bin"
    assert "MR_FIXTURE_SECRET" not in env
    assert "GITHUB_TOKEN" not in env


def test_explicit_credential_names_are_passed() -> None:
    env = build_child_env(
        {"PATH": "/bin", "CURSOR_API_KEY": "k", "MR_FIXTURE_SECRET": "x"},
        credential_names=("CURSOR_API_KEY",),
    )
    assert env["CURSOR_API_KEY"] == "k"
    assert "MR_FIXTURE_SECRET" not in env


def test_writer_tools_exclude_bash() -> None:
    tools = tools_for_task({"write_scope": ["a.txt"]})
    assert "write" in tools and "edit" in tools
    assert "bash" not in tools


def test_policy_digest_stable_without_secret_values() -> None:
    task = {"write_scope": ["a.txt"], "read_scope": ["README.md"]}
    first = build_policy(harness="pi", task=task, parent_env={"PATH": "/bin", "TOKEN": "secret"})
    second = build_policy(harness="pi", task=task, parent_env={"PATH": "/bin", "TOKEN": "other"})
    assert first.digest == second.digest
    assert "secret" not in str(first.as_artifact())


def test_forbidden_flags_rejected() -> None:
    try:
        assert_argv_policy(["agent", "--print", "--force"])
    except ValueError as exc:
        assert "--force" in str(exc)
    else:
        raise AssertionError("expected ValueError")
