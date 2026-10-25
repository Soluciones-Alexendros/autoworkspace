"""Common versioned run result schema (D03)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

RESULT_OUTCOMES = frozenset(
    {
        "succeeded",
        "failed",
        "partial",
        "blocked",
        "cancelled",
        "simulated",
        "not_applicable",
    }
)
NON_TERMINAL = frozenset({"awaiting_agent", "awaiting_approval"})

# CLI exit codes
EXIT_OK = 0
EXIT_FAILED = 1
EXIT_INVALID = 2
EXIT_BLOCKED = 3
EXIT_CANCELLED = 4


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_run_id() -> str:
    return str(uuid.uuid4())


def validate_result(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    outcome = doc.get("outcome")
    if outcome not in RESULT_OUTCOMES and outcome not in NON_TERMINAL:
        errors.append(f"invalid outcome: {outcome}")
    for key in ("run_id", "skill", "mode", "started_at", "finished_at"):
        if key not in doc:
            errors.append(f"missing {key}")
    actions = doc.get("actions") or []
    if not isinstance(actions, list):
        errors.append("actions must be a list")
    else:
        for a in actions:
            if a.get("status") == "completed":
                errors.append("status 'completed' is forbidden; use succeeded/simulated/…")
    return errors


def exit_code_for(outcome: str) -> int:
    if outcome in ("succeeded", "simulated", "not_applicable"):
        return EXIT_OK
    if outcome in ("failed", "partial"):
        return EXIT_FAILED
    if outcome == "blocked" or outcome in NON_TERMINAL:
        return EXIT_BLOCKED
    if outcome == "cancelled":
        return EXIT_CANCELLED
    return EXIT_INVALID


def build_result(
    *,
    skill: str,
    skill_version: str,
    mode: str,
    outcome: str,
    actions: list[dict[str, Any]] | None = None,
    verification: list[dict[str, Any]] | None = None,
    artifacts: list[dict[str, Any]] | None = None,
    errors: list[str] | None = None,
    work_digest: str | None = None,
    target_revision: str | None = None,
    component_version: str | None = None,
) -> dict[str, Any]:
    started = utcnow_iso()
    doc = {
        "schema_version": 1,
        "run_id": new_run_id(),
        "skill": skill,
        "skill_version": skill_version,
        "component_version": component_version,
        "target_revision": target_revision,
        "work_digest": work_digest,
        "mode": mode,
        "outcome": outcome,
        "actions": actions or [],
        "verification": verification or [],
        "artifacts": artifacts or [],
        "errors": errors or [],
        "started_at": started,
        "finished_at": utcnow_iso(),
    }
    errs = validate_result(doc)
    if errs:
        raise ValueError("; ".join(errs))
    return doc


def dumps_result(doc: dict[str, Any]) -> str:
    return json.dumps(doc, ensure_ascii=False, indent=2)
