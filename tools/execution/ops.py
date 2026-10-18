"""Typed operation runner: registry-only; no free-form argv/effect from callers."""
from __future__ import annotations

import os
import signal
import subprocess
import uuid
from dataclasses import dataclass
from typing import Any

from execution.approval import (
    ApprovalRequest,
    DenyProvider,
    is_insufficient_token,
    plan_digest,
    provider_from_env,
)
from execution.registry import get_handler, get_operation, resolve_argv

RESERVED_PARAM_KEYS = frozenset(
    {"effect", "require_approval", "argv", "executable_id", "handler", "cwd_override"}
)


@dataclass
class OpResult:
    operation_id: str
    outcome: str
    returncode: int | None
    duration_ms: int
    detail: str
    effect: str
    run_id: str = ""
    plan_digest: str = ""


SHELL_ESCAPES = {"bash", "sh", "dash", "zsh"}

# Outcomes that may never complete a pipeline phase.
NON_TERMINAL = frozenset({"simulated", "awaiting_agent", "awaiting_approval", "blocked"})


def _reject_shell_escape(argv: list[str]) -> str | None:
    if not argv:
        return None  # handler-only ops have empty argv
    base = os.path.basename(argv[0])
    if base in SHELL_ESCAPES and len(argv) >= 2 and argv[1] in {"-c", "-lc"}:
        return "shell -c escape rejected"
    return None


def _make_run_id() -> str:
    return str(uuid.uuid4())


def run_registered(
    operation_id: str,
    params: dict[str, Any] | None = None,
    *,
    target: str = ".",
    cwd: str | None = None,
    executable_id: str = "autoworkspace",
) -> OpResult:
    """Execute a registered operation. Callers may not pass effect/argv/approval flags."""
    raw = dict(params or {})
    # Reject reserved keys instead of silently stripping when they indicate policy tampering
    unknown_reserved = RESERVED_PARAM_KEYS & set(raw)
    if unknown_reserved:
        return OpResult(
            operation_id,
            "blocked",
            None,
            0,
            f"reserved parameters rejected: {sorted(unknown_reserved)}",
            "unknown",
        )
    params = dict(raw)
    if is_insufficient_token(str(params.get("approved", ""))):
        params.pop("approved", None)

    try:
        spec = get_operation(operation_id)
    except KeyError:
        return OpResult(operation_id, "blocked", None, 0, "unknown operation", "unknown")

    argv = resolve_argv(spec, params)
    handler = get_handler(operation_id)
    handler_id = getattr(handler, "__name__", None) or (
        f"{handler.__module__}.{getattr(handler, '__qualname__', 'handler')}" if handler else ""
    )
    digest = plan_digest(
        operation_id,
        target,
        params,
        [spec.effect],
        argv=argv,
        cwd=cwd,
        executable_id=executable_id,
        effect=spec.effect,
        handler_id=handler_id,
        skill=spec.skill,
        timeout=spec.timeout,
    )

    if spec.require_approval or spec.effect in {
        "mutate-host",
        "communicate-external",
        "access-secret",
    }:
        provider = provider_from_env()
        decision = provider.decide(
            ApprovalRequest(
                operation_id,
                target,
                params,
                (spec.effect,),
                digest,
                effects_detail=f"skill={spec.skill}; handler={handler_id or 'argv'}",
            )
        )
        if not decision.allowed or decision.covers_digest != digest:
            return OpResult(
                operation_id,
                "blocked",
                None,
                0,
                decision.reason,
                spec.effect,
                plan_digest=digest,
            )

    if spec.require_snapshot and not params.get("snapshot_id"):
        return OpResult(
            operation_id,
            "blocked",
            None,
            0,
            "snapshot_id required",
            spec.effect,
            plan_digest=digest,
        )

    bad = _reject_shell_escape(argv)
    if bad:
        return OpResult(operation_id, "blocked", 2, 0, bad, spec.effect, plan_digest=digest)

    # Re-resolve handler after approval; reject if identity changed
    handler_after = get_handler(operation_id)
    handler_id_after = getattr(handler_after, "__name__", None) or (
        f"{handler_after.__module__}.{getattr(handler_after, '__qualname__', 'handler')}"
        if handler_after
        else ""
    )
    if handler_id_after != handler_id:
        return OpResult(
            operation_id,
            "blocked",
            None,
            0,
            "handler identity changed between approval and execution",
            spec.effect,
            plan_digest=digest,
        )

    import time

    start = time.monotonic()
    run_id = _make_run_id()

    if handler_after is not None:
        try:
            rc = handler_after(params)
            if isinstance(rc, OpResult):
                rc.run_id = rc.run_id or run_id
                rc.plan_digest = rc.plan_digest or digest
                return rc
            if rc is None:
                return OpResult(
                    operation_id,
                    "blocked",
                    None,
                    int((time.monotonic() - start) * 1000),
                    "handler returned None; not treated as success",
                    spec.effect,
                    run_id=run_id,
                    plan_digest=digest,
                )
            code = int(rc)
            outcome = "succeeded" if code == 0 else "failed"
            return OpResult(
                operation_id,
                outcome,
                code,
                int((time.monotonic() - start) * 1000),
                "",
                spec.effect,
                run_id=run_id,
                plan_digest=digest,
            )
        except Exception as exc:  # noqa: BLE001 — boundary
            return OpResult(
                operation_id,
                "failed",
                1,
                int((time.monotonic() - start) * 1000),
                str(exc)[:500],
                spec.effect,
                run_id=run_id,
                plan_digest=digest,
            )

    if not argv:
        return OpResult(
            operation_id,
            "blocked",
            None,
            0,
            "no handler and no argv_template",
            spec.effect,
            plan_digest=digest,
        )

    return _run_subprocess(
        operation_id,
        argv,
        spec.effect,
        timeout=spec.timeout,
        cwd=cwd,
        run_id=run_id,
        digest=digest,
    )


def _run_subprocess(
    operation_id: str,
    argv: list[str],
    effect: str,
    *,
    timeout: int,
    cwd: str | None,
    run_id: str,
    digest: str,
) -> OpResult:
    import time

    start = time.monotonic()
    try:
        proc = subprocess.Popen(
            argv,
            shell=False,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=5)
            return OpResult(
                operation_id,
                "cancelled",
                124,
                int((time.monotonic() - start) * 1000),
                "timeout; process group killed; reconciliation_required before retry",
                effect,
                run_id=run_id,
                plan_digest=digest,
            )
        rc = proc.returncode
        outcome = "succeeded" if rc == 0 else "failed"
        detail = (stderr or stdout or "")[:500]
        return OpResult(
            operation_id,
            outcome,
            rc,
            int((time.monotonic() - start) * 1000),
            detail,
            effect,
            run_id=run_id,
            plan_digest=digest,
        )
    except OSError as exc:
        return OpResult(
            operation_id,
            "failed",
            127,
            int((time.monotonic() - start) * 1000),
            str(exc),
            effect,
            run_id=run_id,
            plan_digest=digest,
        )


def run_operation(
    *,
    operation_id: str,
    argv: list[str] | None = None,
    effect: str | None = None,
    target: str = ".",
    params: dict[str, Any] | None = None,
    timeout: int = 60,
    cwd: str | None = None,
    require_approval: bool | None = None,
) -> OpResult:
    """Deprecated free-form entry. Always rejects caller-supplied argv/effect/approval.

    Use run_registered(operation_id, params). Tests that need arbitrary subprocesses
    must use an isolated fixture helper, not this product API.
    """
    _ = (timeout, cwd)
    if argv is not None or effect is not None or require_approval is not None:
        return OpResult(
            operation_id,
            "blocked",
            None,
            0,
            "free-form run_operation rejected; use run_registered(operation_id, params)",
            effect or "unknown",
        )
    return run_registered(operation_id, params, target=target, cwd=cwd)


_ = DenyProvider
