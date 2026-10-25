"""Execution ops and approval boundary tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from execution.approval import (  # noqa: E402
    ApprovalDecision,
    ApprovalProvider,
    ApprovalRequest,
    DenyProvider,
    is_insufficient_token,
    plan_digest,
)
from execution.ops import run_operation, run_registered  # noqa: E402
from execution.preflight import check_binaries, resolve_workspace_root  # noqa: E402
from execution.registry import register_handler  # noqa: E402


class AllowProvider(ApprovalProvider):
    def decide(self, request: ApprovalRequest) -> ApprovalDecision:
        return ApprovalDecision(True, "test allow", "test", request.plan_digest)


def test_deny_provider_blocks_mutation():
    d = DenyProvider().decide(ApprovalRequest("clean_routine", "/tmp", {}, ("mutate-host",), "abc"))
    assert d.allowed is False


def test_insufficient_tokens():
    assert is_insufficient_token("approved=true")
    assert is_insufficient_token("true")
    assert is_insufficient_token("1")
    assert is_insufficient_token("CONFIRM_SEND")


def test_shell_c_rejected_via_free_form():
    r = run_operation(
        operation_id="x",
        argv=["bash", "-c", "echo hi"],
        effect="read",
        target=".",
        require_approval=False,
    )
    assert r.outcome == "blocked"
    assert "free-form" in r.detail


def test_mutate_blocked_without_approval(monkeypatch):
    monkeypatch.setenv("AUTOWORKSPACE_APPROVAL_PROVIDER", "deny")
    r = run_registered("clean_journal", {"snapshot_id": "snap-1"}, target="/")
    assert r.outcome == "blocked"


def test_free_form_mutation_rejected():
    r = run_operation(
        operation_id="evil",
        argv=["true"],
        effect="mutate-host",
        target="/",
        require_approval=False,
    )
    assert r.outcome == "blocked"
    assert "free-form" in r.detail


def test_digest_includes_argv_change_invalidates(monkeypatch):
    monkeypatch.setattr("execution.ops.provider_from_env", lambda: AllowProvider())
    calls = []

    def handler(params):
        calls.append(params)
        return 0

    register_handler("clean_temp", handler)
    d1 = plan_digest(
        "clean_temp",
        "/",
        {"snapshot_id": "s"},
        ["mutate-host"],
        argv=[],
        cwd="/a",
        executable_id="x",
        effect="mutate-host",
    )
    d2 = plan_digest(
        "clean_temp",
        "/",
        {"snapshot_id": "s"},
        ["mutate-host"],
        argv=["evil"],
        cwd="/a",
        executable_id="x",
        effect="mutate-host",
    )
    assert d1 != d2


def test_argv_or_target_change_blocks_stale_approval(monkeypatch):
    """Provider that approves only a fixed digest — change invalidates."""
    fixed = {"digest": ""}

    class StaleProvider(ApprovalProvider):
        def decide(self, request: ApprovalRequest) -> ApprovalDecision:
            if not fixed["digest"]:
                fixed["digest"] = request.plan_digest
                return ApprovalDecision(True, "first", "test", request.plan_digest)
            return ApprovalDecision(True, "stale", "test", fixed["digest"])

    monkeypatch.setattr("execution.ops.provider_from_env", lambda: StaleProvider())
    register_handler("clean_temp", lambda p: 0)
    r1 = run_registered("clean_temp", {"snapshot_id": "s1"}, target="/t1")
    assert r1.outcome == "succeeded"
    r2 = run_registered("clean_temp", {"snapshot_id": "s2"}, target="/t1")
    assert r2.outcome == "blocked"


def test_handler_not_invoked_when_denied(monkeypatch):
    monkeypatch.setattr("execution.ops.provider_from_env", lambda: DenyProvider())
    invoked = []
    register_handler("clean_journal", lambda p: invoked.append(1) or 0)
    r = run_registered("clean_journal", {"snapshot_id": "s"}, target="/")
    assert r.outcome == "blocked"
    assert invoked == []


def test_preflight_missing_binary():
    r = check_binaries(["definitely-not-a-real-binary-xyz"])
    assert r.ok is False


def test_resolve_workspace():
    assert resolve_workspace_root(ROOT) == ROOT.resolve()


def test_digest_stable():
    a = plan_digest("op", "t", {"x": 1}, ["read"], argv=[], cwd="", executable_id="")
    b = plan_digest("op", "t", {"x": 1}, ["read"], argv=[], cwd="", executable_id="")
    assert a == b
