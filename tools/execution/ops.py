"""Typed operation runner: registry-only; no free-form argv/effect from callers."""

from __future__ import annotations

import os
import signal
import subprocess
import time
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
from execution.registry import OpSpec, get_handler, get_operation, resolve_argv

RESERVED_PARAM_KEYS = frozenset({"effect", "require_approval", "argv", "executable_id", "handler", "cwd_override"})


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
SHELL_FLAG_ARGC = 2
APPROVAL_EFFECTS = frozenset({"mutate-host", "communicate-external", "access-secret"})

# Outcomes that may never complete a pipeline phase.
NON_TERMINAL = frozenset({"simulated", "awaiting_agent", "awaiting_approval", "blocked"})


def _reject_shell_escape(argv: list[str]) -> str | None:
    if not argv:
        return None  # handler-only ops have empty argv
    base = os.path.basename(argv[0])
    if base in SHELL_ESCAPES and len(argv) >= SHELL_FLAG_ARGC and argv[1] in {"-c", "-lc"}:
        return "shell -c escape rejected"
    return None


def _make_run_id() -> str:
    return str(uuid.uuid4())


def _blocked_early(operation_id: str, message: str) -> OpResult:
    return OpResult(operation_id, "blocked", None, 0, message, "unknown")


def _blocked(
    operation_id: str,
    message: str,
    effect: str,
    *,
    digest: str,
    code: int | None = None,
) -> OpResult:
    return OpResult(operation_id, "blocked", code, 0, message, effect, plan_digest=digest)


def _handler_identity(handler: object) -> str:
    """Identity must not rely on __name__ alone (wrappers can collide) - H06/C06."""
    if handler is None:
        return ""
    return (
        f"{getattr(handler, '__module__', '?')}."
        f"{getattr(handler, '__qualname__', getattr(handler, '__name__', 'handler'))}"
        f"#{id(handler)}"
    )


@dataclass(frozen=True)
class _ExecContext:
    """Everything the gates and the executor need, resolved once."""

    operation_id: str
    target: str
    params: dict[str, Any]
    spec: OpSpec
    digest: str
    handler_id: str


def _approval_gate(ctx: _ExecContext) -> OpResult | None:
    spec = ctx.spec
    if not (spec.require_approval or spec.effect in APPROVAL_EFFECTS):
        return None
    provider = provider_from_env()
    decision = provider.decide(
        ApprovalRequest(
            ctx.operation_id,
            ctx.target,
            ctx.params,
            (spec.effect,),
            ctx.digest,
            effects_detail=f"skill={spec.skill}; handler={ctx.handler_id or 'argv'}",
        )
    )
    if not decision.allowed or decision.covers_digest != ctx.digest:
        return _blocked(ctx.operation_id, decision.reason, spec.effect, digest=ctx.digest)
    return None


def _gate_checks(ctx: _ExecContext, argv: list[str]) -> OpResult | None:
    """Approval, snapshot and shell-escape gates. None means the operation may run."""
    blocked = _approval_gate(ctx)
    if blocked is not None:
        return blocked
    if ctx.spec.require_snapshot and not ctx.params.get("snapshot_id"):
        return _blocked(ctx.operation_id, "snapshot_id required", ctx.spec.effect, digest=ctx.digest)
    bad = _reject_shell_escape(argv)
    if bad:
        return _blocked(ctx.operation_id, bad, ctx.spec.effect, digest=ctx.digest, code=2)
    return None


def _invoke_handler(ctx: _ExecContext, handler: Any, *, start: float, run_id: str) -> OpResult:
    op, effect, digest = ctx.operation_id, ctx.spec.effect, ctx.digest
    try:
        rc = handler(ctx.params)
        if isinstance(rc, OpResult):
            rc.run_id = rc.run_id or run_id
            rc.plan_digest = rc.plan_digest or digest
            return rc
        if rc is None:
            return OpResult(
                op,
                "blocked",
                None,
                int((time.monotonic() - start) * 1000),
                "handler returned None; not treated as success",
                effect,
                run_id=run_id,
                plan_digest=digest,
            )
        code = int(rc)
        outcome = "succeeded" if code == 0 else "failed"
        return OpResult(
            op,
            outcome,
            code,
            int((time.monotonic() - start) * 1000),
            "",
            effect,
            run_id=run_id,
            plan_digest=digest,
        )
    except Exception as exc:
        return OpResult(
            op,
            "failed",
            1,
            int((time.monotonic() - start) * 1000),
            str(exc)[:500],
            effect,
            run_id=run_id,
            plan_digest=digest,
        )


def _execute_argv(ctx: _ExecContext, *, argv: list[str], cwd: str | None, run_id: str) -> OpResult:
    if not argv:
        return _blocked(ctx.operation_id, "no handler and no argv_template", ctx.spec.effect, digest=ctx.digest)
    return _run_subprocess(
        ctx.operation_id,
        argv,
        ctx.spec.effect,
        timeout=ctx.spec.timeout,
        cwd=cwd,
        run_id=run_id,
        digest=ctx.digest,
    )


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
        return _blocked_early(operation_id, f"reserved parameters rejected: {sorted(unknown_reserved)}")
    params = dict(raw)
    if is_insufficient_token(str(params.get("approved", ""))):
        params.pop("approved", None)
    try:
        spec = get_operation(operation_id)
    except KeyError:
        return _blocked_early(operation_id, "unknown operation")

    argv = resolve_argv(spec, params)
    handler_id = _handler_identity(get_handler(operation_id))
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

    ctx = _ExecContext(
        operation_id=operation_id,
        target=target,
        params=params,
        spec=spec,
        digest=digest,
        handler_id=handler_id,
    )

    gated = _gate_checks(ctx, argv)
    if gated is not None:
        return gated

    # Re-resolve handler after approval; reject if identity changed
    handler_after = get_handler(operation_id)
    if _handler_identity(handler_after) != handler_id:
        return _blocked(
            operation_id,
            "handler identity changed between approval and execution",
            spec.effect,
            digest=digest,
        )

    start = time.monotonic()
    run_id = _make_run_id()
    if handler_after is not None:
        return _invoke_handler(ctx, handler_after, start=start, run_id=run_id)
    return _execute_argv(ctx, argv=argv, cwd=cwd, run_id=run_id)


def _run_subprocess(  # noqa: PLR0913  # ejecutor: keyword-only, espejo de la operación
    operation_id: str,
    argv: list[str],
    effect: str,
    *,
    timeout: int,
    cwd: str | None,
    run_id: str,
    digest: str,
) -> OpResult:
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


def run_operation(  # noqa: PLR0913  # API pública: keyword-only, espejo del schema
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
