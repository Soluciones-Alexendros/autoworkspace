"""Approval provider boundary (D04). Digest detects change; it is not consent."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApprovalRequest:
    operation_id: str
    target: str
    params: dict[str, Any]
    effects: tuple[str, ...]
    plan_digest: str


@dataclass(frozen=True)
class ApprovalDecision:
    allowed: bool
    reason: str
    issuer: str
    covers_digest: str


def plan_digest(
    operation_id: str,
    target: str,
    params: dict[str, Any],
    effects: list[str],
    *,
    argv: list[str] | None = None,
    cwd: str | None = None,
    executable_id: str = "",
    effect: str | None = None,
) -> str:
    """SHA-256 over the full execution plan (not consent).

    Includes operation_id, target, params, effect(s), argv, cwd, executable_id.
    Changing any field invalidates a prior approval bound to this digest.
    """
    eff = effect if effect is not None else (effects[0] if effects else "")
    payload = json.dumps(
        {
            "operation_id": operation_id,
            "target": target,
            "params": params,
            "effect": eff,
            "effects": effects,
            "argv": list(argv or []),
            "cwd": cwd or "",
            "executable_id": executable_id or "",
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ApprovalProvider:
    """Trusted issuer interface. Env/file self-approvals are never sufficient alone."""

    def decide(self, request: ApprovalRequest) -> ApprovalDecision:
        raise NotImplementedError


class DenyProvider(ApprovalProvider):
    """Default: prepare plan, return blocked/awaiting_approval."""

    def decide(self, request: ApprovalRequest) -> ApprovalDecision:
        return ApprovalDecision(
            allowed=False,
            reason="no trusted approval provider configured; mutación blocked",
            issuer="deny-by-default",
            covers_digest=request.plan_digest,
        )


class InteractiveProvider(ApprovalProvider):
    """Local interactive confirmation for the executable CLI only."""

    def decide(self, request: ApprovalRequest) -> ApprovalDecision:
        if not sys_stdin_isatty():
            return ApprovalDecision(
                False,
                "non-interactive; cannot prompt",
                "interactive",
                request.plan_digest,
            )
        print(
            f"APPROVAL REQUIRED\n"
            f"  operation: {request.operation_id}\n"
            f"  target: {request.target}\n"
            f"  effects: {', '.join(request.effects)}\n"
            f"  digest: {request.plan_digest[:16]}…\n"
            f"Type the operation id to approve:",
            flush=True,
        )
        try:
            line = input().strip()
        except EOFError:
            return ApprovalDecision(False, "EOF", "interactive", request.plan_digest)
        if line == request.operation_id:
            return ApprovalDecision(
                True, "operator typed operation id", "interactive", request.plan_digest
            )
        return ApprovalDecision(
            False, "mismatched confirmation", "interactive", request.plan_digest
        )


def sys_stdin_isatty() -> bool:
    import sys

    return sys.stdin.isatty()


def provider_from_env() -> ApprovalProvider:
    mode = os.environ.get("AUTOWORKSPACE_APPROVAL_PROVIDER", "deny")
    if mode == "interactive":
        return InteractiveProvider()
    return DenyProvider()


def is_insufficient_token(token: str | None) -> bool:
    """Tokens that must never be treated as consent."""
    if not token:
        return True
    lowered = token.strip().lower()
    return lowered in {
        "true",
        "1",
        "yes",
        "approved",
        "approved=true",
        "confirm_send",
        "confirm-send",
    }
