"""Allowed verifier catalog — no arbitrary commands from plan Markdown/YAML."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from execution.ops import OpResult
from execution.registry import get_operation

Verifier = Callable[[OpResult, Path], list[dict[str, Any]]]

ALLOWED_VERIFIER_IDS = frozenset(
    {
        "document-review",
        "pytest-harness-policy",
        "pytest-orchestrator",
        "native-gate-contract",
        "native-cursor-bc",
        "native-cursor-e2e",
        "native-pi-e2e",
        "release-fixture-gate",
        "canonical-local-gates",
        "canon-gates",
        "independent-plan-review",
        "release-public-evidence",
        "release-public-smoke",
        "independent-content-check",
        "staged-paths",
    }
)


def resolve_verifier_ids(task: dict[str, Any]) -> tuple[str, ...]:
    raw = list(task.get("verification") or [])
    if not raw:
        raise ValueError(f"task {task.get('id')}: verification list is empty")
    unknown = sorted({str(item) for item in raw} - ALLOWED_VERIFIER_IDS)
    if unknown:
        raise ValueError(f"task {task.get('id')}: unknown verification ids: {unknown}")
    return tuple(str(item) for item in raw)


def content_acceptance_verifier(task: dict[str, Any]) -> Verifier:
    """Default acceptance: non-empty staged bytes matching the task id (writers)."""
    operation = get_operation(str(task["operation"]))
    kinds = operation.required_verifications or ("staged_paths",)
    write_scope = list(task.get("write_scope") or [])
    task_id = str(task["id"])

    def verify(result: OpResult, staging: Path) -> list[dict[str, Any]]:
        if result.outcome != "succeeded":
            return [{"kind": kind, "ok": False, "detail": result.detail or "not succeeded"} for kind in kinds]
        if not write_scope:
            detail = (result.detail or "").strip()
            ok = bool(detail)
            return [{"kind": kind, "ok": ok, "detail": detail or "empty read-only detail"} for kind in kinds]
        failures: list[str] = []
        for relative in write_scope:
            path = staging / relative
            if not path.is_file():
                failures.append(f"missing:{relative}")
                continue
            content = path.read_text(encoding="utf-8")
            if content == "":
                failures.append(f"empty:{relative}")
            elif content != f"{task_id}\n":
                failures.append(f"content-mismatch:{relative}")
        ok = not failures
        detail = "ok" if ok else ",".join(failures)
        return [{"kind": kind, "ok": ok, "detail": detail} for kind in kinds]

    return verify


def resolve(task: dict[str, Any]) -> Verifier:
    """Resolve plan verification ids to an executable verifier (catalog only)."""
    resolve_verifier_ids(task)
    return content_acceptance_verifier(task)
