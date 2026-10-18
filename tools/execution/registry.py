"""Canonical operation registry. CLIs pass only operation_id + typed params."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class OpSpec:
    operation_id: str
    effect: str
    skill: str
    require_approval: bool
    require_snapshot: bool = False
    timeout: int = 60
    recovery_required: bool = False
    # Optional argv template; if None, a registered Python handler is required.
    argv_template: tuple[str, ...] | None = None
    description: str = ""


# Handlers registered by skill modules at import/dispatch time.
_HANDLERS: dict[str, Callable[..., Any]] = {}

OPERATIONS: dict[str, OpSpec] = {
    "create_snapshot": OpSpec(
        "create_snapshot",
        "write-workspace",
        "local-maintenance",
        require_approval=True,
        timeout=600,
        description="Create pre-change snapshot",
    ),
    "restore_snapshot": OpSpec(
        "restore_snapshot",
        "mutate-host",
        "local-maintenance",
        require_approval=True,
        require_snapshot=True,
        timeout=600,
        recovery_required=True,
        description="Restore snapshot into program staging only",
    ),
    "validate_snapshot": OpSpec(
        "validate_snapshot",
        "read",
        "local-maintenance",
        require_approval=False,
        description="Validate snapshot metadata",
    ),
    "clean_package_cache": OpSpec(
        "clean_package_cache",
        "mutate-host",
        "local-maintenance",
        require_approval=True,
        require_snapshot=True,
        timeout=600,
    ),
    "clean_journal": OpSpec(
        "clean_journal",
        "mutate-host",
        "local-maintenance",
        require_approval=True,
        require_snapshot=True,
        timeout=600,
    ),
    "clean_orphans": OpSpec(
        "clean_orphans",
        "mutate-host",
        "local-maintenance",
        require_approval=True,
        require_snapshot=True,
        timeout=600,
    ),
    "clean_temp": OpSpec(
        "clean_temp",
        "mutate-host",
        "local-maintenance",
        require_approval=True,
        require_snapshot=True,
        timeout=600,
    ),
    "clean_needrestart": OpSpec(
        "clean_needrestart",
        "mutate-host",
        "local-maintenance",
        require_approval=True,
        require_snapshot=True,
        timeout=600,
    ),
    "update_firmware": OpSpec(
        "update_firmware",
        "mutate-host",
        "local-maintenance",
        require_approval=True,
        require_snapshot=True,
        timeout=900,
    ),
    "clean_userspace_caches": OpSpec(
        "clean_userspace_caches",
        "mutate-host",
        "local-maintenance",
        require_approval=True,
        require_snapshot=True,
        timeout=600,
    ),
    "proton_send": OpSpec(
        "proton_send",
        "communicate-external",
        "local-proton",
        require_approval=True,
        timeout=120,
        description="Send mail via Proton Bridge",
    ),
    "local_gates": OpSpec(
        "local_gates",
        "write-workspace",
        "project-publish",
        require_approval=False,
        timeout=1800,
        description="Local publish gates (may write via husky/gate scripts)",
    ),
}


def register_handler(operation_id: str, handler: Callable[..., Any]) -> None:
    if operation_id not in OPERATIONS:
        raise KeyError(f"cannot register handler for unknown operation: {operation_id}")
    _HANDLERS[operation_id] = handler


def get_handler(operation_id: str) -> Callable[..., Any] | None:
    return _HANDLERS.get(operation_id)


def get_operation(operation_id: str) -> OpSpec:
    if operation_id not in OPERATIONS:
        raise KeyError(f"unknown operation: {operation_id}")
    return OPERATIONS[operation_id]


def known_operation_ids() -> frozenset[str]:
    return frozenset(OPERATIONS)


def resolve_argv(spec: OpSpec, params: dict[str, Any]) -> list[str]:
    """Build argv from template; never accept free-form argv from callers."""
    if spec.argv_template is None:
        return []
    argv = list(spec.argv_template)
    # Simple substitution of {key} from params
    out: list[str] = []
    for part in argv:
        if part.startswith("{") and part.endswith("}"):
            key = part[1:-1]
            out.append(str(params.get(key, "")))
        else:
            out.append(part)
    return out
