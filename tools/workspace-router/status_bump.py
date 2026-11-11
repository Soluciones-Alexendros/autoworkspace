"""Declarative status bump for .machineroom/status.yaml — transactional."""

from __future__ import annotations

import fcntl
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from contracts.plan import PlanDocument

_TOOLS = Path(__file__).resolve().parents[1]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from state_paths import state_file as _state_file  # noqa: E402

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML required: uv sync --frozen") from exc

STATUS_PATH_PARTS = 3
STATUS_SCHEMA_VERSION = 2
PHASES = ("DEFINE", "SCHEMAS", "IMPLEMENT", "VALIDATE", "INTEGRATE", "STATUS")
PHASE_INDEX = {p: i for i, p in enumerate(PHASES)}


def status_path(repo: Path) -> Path:
    root = Path(repo).resolve()
    return _state_file(root, "status.yaml")


def _default_status() -> dict[str, Any]:
    return {
        "schema_version": STATUS_SCHEMA_VERSION,
        "version": "0.1.0",
        "phase": "DEFINE",
        "advance": 0,
        "last_skill": "",
        "checksum_spec": "",
        "updated_at": "",
        "state_revision": 0,
        "history": [],
        "completed_run_ids": [],
        "active_plan": None,
        "plan_digest": "",
        "tasks": {},
    }


def _migrate_status_data(data: dict[str, Any]) -> dict[str, Any]:
    version = data.get("schema_version", 1)
    if version not in (1, STATUS_SCHEMA_VERSION):
        raise ValueError(f"unsupported status schema_version: {version}")
    migrated = _default_status()
    migrated.update(data)
    migrated["schema_version"] = STATUS_SCHEMA_VERSION
    migrated.setdefault("active_plan", None)
    migrated.setdefault("plan_digest", "")
    migrated.setdefault("tasks", {})
    return migrated


def load_status(repo: Path | str) -> dict[str, Any]:
    path = status_path(Path(repo))
    if not path.is_file():
        return _default_status()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("status.yaml must be a mapping")
    return _migrate_status_data(data)


def migrate_status(repo: Path | str, *, write: bool = True) -> dict[str, Any]:
    """Explicitly persist the current status schema without selecting a plan."""
    root = Path(repo).resolve()
    if not write:
        return load_status(root)
    return _with_status_lock(root, lambda data: data)


def _confined_plan_path(repo: Path, path: Path | str) -> tuple[Path, str]:
    root = repo.resolve()
    candidate = Path(path)
    resolved = (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError(f"plan outside repo rejected: {path}") from exc
    if not resolved.is_file():
        raise ValueError(f"plan is not a file: {resolved}")
    return resolved, relative


def activate_plan(repo: Path | str, plan_path: Path | str) -> dict[str, Any]:
    """Select exactly one parsed plan and initialize its task states."""
    _ensure_tools_on_path()
    from contracts.plan import load_plan  # noqa: PLC0415

    root = Path(repo).resolve()
    resolved, relative = _confined_plan_path(root, plan_path)
    document = load_plan(resolved)

    def activate(data: dict[str, Any]) -> dict[str, Any]:
        current = data.get("active_plan")
        if current:
            if current.get("path") == relative and current.get("digest") == document.digest:
                return data
            raise ValueError("another active plan or plan revision exists; explicit reset required")
        out = dict(data)
        out["active_plan"] = {
            "plan_id": document.plan_id,
            "path": relative,
            "base_revision": document.base_revision,
            "digest": document.digest,
        }
        out["plan_digest"] = document.digest
        out["tasks"] = {
            str(task["id"]): {"state": "pending", "depends_on": list(task["depends_on"])} for task in document.tasks
        }
        out["phase"] = str(document.tasks[0]["phase"])
        out["state_revision"] = int(out.get("state_revision") or 0) + 1
        out["updated_at"] = _utc_stamp()
        return out

    return _with_status_lock(root, activate)


def load_active_plan(repo: Path | str) -> PlanDocument:
    """Load the selected plan and reject identity drift."""
    _ensure_tools_on_path()
    from contracts.plan import load_plan  # noqa: PLC0415

    root = Path(repo).resolve()
    status = load_status(root)
    active = status.get("active_plan")
    if not isinstance(active, dict) or not active:
        raise ValueError("no active plan")
    resolved, relative = _confined_plan_path(root, str(active.get("path") or ""))
    document = load_plan(resolved)
    expected = {
        "plan_id": document.plan_id,
        "base_revision": document.base_revision,
        "digest": document.digest,
    }
    if any(active.get(key) != value for key, value in expected.items()) or relative != active.get("path"):
        raise ValueError("active plan identity or digest changed")
    if status.get("plan_digest") != document.digest:
        raise ValueError("active plan digest binding mismatch")
    return document


def _task_definition(document: Any, task_id: str) -> dict[str, Any]:
    for task in document.tasks:
        if task["id"] == task_id:
            return task
    raise ValueError(f"unknown task in active plan: {task_id}")


def _task_entry(data: dict[str, Any], task_id: str) -> dict[str, Any]:
    tasks = data.get("tasks") or {}
    entry = tasks.get(task_id)
    if not isinstance(entry, dict):
        raise ValueError(f"task not initialized in status: {task_id}")
    return entry


def _dependencies_complete(data: dict[str, Any], task: dict[str, Any]) -> bool:
    return all(_task_entry(data, str(dependency)).get("state") == "succeeded" for dependency in task["depends_on"])


def _set_task_state(data: dict[str, Any], task_id: str, state: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = dict(data)
    tasks = dict(out.get("tasks") or {})
    entry = dict(_task_entry(out, task_id))
    entry["state"] = state
    entry["updated_at"] = _utc_stamp()
    tasks[task_id] = entry
    out["tasks"] = tasks
    return out, entry


def ready_tasks(repo: Path | str) -> list[dict[str, Any]]:
    document = load_active_plan(repo)
    status = load_status(repo)
    return [
        task
        for task in document.tasks
        if _task_entry(status, str(task["id"])).get("state") in {"pending", "ready"}
        and _dependencies_complete(status, task)
    ]


def start_task(repo: Path | str, task_id: str) -> dict[str, Any]:
    root = Path(repo).resolve()
    document = load_active_plan(root)
    task = _task_definition(document, task_id)

    def start(data: dict[str, Any]) -> dict[str, Any]:
        entry = _task_entry(data, task_id)
        if not _dependencies_complete(data, task):
            raise ValueError(f"task dependencies not succeeded: {task_id}")
        if entry.get("state") not in {"pending", "ready"}:
            raise ValueError(f"task {task_id} cannot start from {entry.get('state')}")
        out, updated = _set_task_state(data, task_id, "running")
        updated["attempts"] = int(updated.get("attempts") or 0) + 1
        out["tasks"][task_id] = updated
        out["phase"] = str(task["phase"])
        out["state_revision"] = int(out.get("state_revision") or 0) + 1
        out["updated_at"] = _utc_stamp()
        return out

    return _with_status_lock(root, start)


def await_task(repo: Path | str, task_id: str, *, state: str = "awaiting_agent") -> dict[str, Any]:
    if state not in {"awaiting_agent", "awaiting_approval"}:
        raise ValueError(f"invalid awaiting state: {state}")
    root = Path(repo).resolve()
    document = load_active_plan(root)
    _task_definition(document, task_id)

    def await_state(data: dict[str, Any]) -> dict[str, Any]:
        if _task_entry(data, task_id).get("state") != "running":
            raise ValueError(f"task {task_id} must be running before {state}")
        out, _entry = _set_task_state(data, task_id, state)
        out["state_revision"] = int(out.get("state_revision") or 0) + 1
        return out

    return _with_status_lock(root, await_state)


def _apply_task_completion(  # noqa: PLR0913  # locked completion context
    data: dict[str, Any],
    *,
    root: Path,
    task_id: str,
    run_id: str,
    target: str,
    skill: str,
    replay: dict[str, bool],
) -> dict[str, Any]:
    """Pure-ish status mutation for one successful task (load_evidence under lock)."""
    from execution.evidence import load_evidence  # noqa: PLC0415

    current_document = load_active_plan(root)
    current_task = _task_definition(current_document, task_id)
    evidence = load_evidence(
        root,
        run_id,
        revalidate_content=True,
        expected_phase=str(current_task["phase"]),
        expected_skill=skill,
        expected_target=target,
        expected_operation=str(current_task["operation"]),
        for_complete=True,
    )
    if evidence.get("plan_id") != current_document.plan_id:
        raise ValueError(f"evidence plan_id mismatch: {evidence.get('plan_id')}")
    if evidence.get("task_id") != task_id:
        raise ValueError(f"evidence task_id mismatch: {evidence.get('task_id')}")
    receipt_key = f"{task_id}:{run_id}"
    receipts = dict(data.get("task_receipts") or {})
    if receipt_key in receipts:
        replay["idempotent"] = True
        return data
    entry = _task_entry(data, task_id)
    if entry.get("state") != "running":
        raise ValueError(f"task {task_id} cannot complete from {entry.get('state')}")
    out, updated = _set_task_state(data, task_id, "succeeded")
    updated.update(
        {
            "run_id": run_id,
            "output_digest": evidence["output_digest"],
            "completed_at": _utc_stamp(),
        }
    )
    out["tasks"][task_id] = updated
    receipts[receipt_key] = {
        "plan_id": current_document.plan_id,
        "plan_digest": current_document.digest,
        "output_digest": evidence["output_digest"],
        "at": _utc_stamp(),
    }
    out["task_receipts"] = receipts
    out["state_revision"] = int(out.get("state_revision") or 0) + 1
    out["advance"] = int(out.get("advance") or 0) + 1
    out["last_skill"] = skill
    out["updated_at"] = _utc_stamp()
    remaining = [item for item in current_document.tasks if out["tasks"][str(item["id"])].get("state") != "succeeded"]
    out["phase"] = str(remaining[0]["phase"]) if remaining else "STATUS"
    history = list(out.get("history") or [])
    history.append(
        {
            "phase": current_task["phase"],
            "task_id": task_id,
            "plan_id": current_document.plan_id,
            "run_id": run_id,
            "state_revision": out["state_revision"],
            "at": out["updated_at"],
            "evidence_ok": True,
        }
    )
    out["history"] = history[-50:]
    return out


def complete_task(
    repo: Path | str,
    task_id: str,
    *,
    run_id: str,
    target: str,
) -> dict[str, Any]:
    """Task-level closure with evidence + receipts (not phase ``advance_status``)."""
    root = Path(repo).resolve()
    document = load_active_plan(root)
    task = _task_definition(document, task_id)
    _ensure_tools_on_path()
    from execution.registry import get_operation  # noqa: PLC0415

    spec = get_operation(str(task["operation"]))
    replay = {"idempotent": False}

    def complete(data: dict[str, Any]) -> dict[str, Any]:
        return _apply_task_completion(
            data,
            root=root,
            task_id=task_id,
            run_id=run_id,
            target=target,
            skill=spec.skill,
            replay=replay,
        )

    result = _with_status_lock(root, complete)
    if replay["idempotent"]:
        result = dict(result)
        result["_idempotent_replay"] = True
    return result


def fail_task(repo: Path | str, task_id: str, *, detail: str) -> dict[str, Any]:
    root = Path(repo).resolve()
    document = load_active_plan(root)
    _task_definition(document, task_id)

    def fail(data: dict[str, Any]) -> dict[str, Any]:
        state = _task_entry(data, task_id).get("state")
        if state not in {"running", "awaiting_agent", "awaiting_approval"}:
            raise ValueError(f"task {task_id} cannot fail from {state}")
        out, entry = _set_task_state(data, task_id, "failed")
        entry["detail"] = detail[:500]
        out["tasks"][task_id] = entry
        out["state_revision"] = int(out.get("state_revision") or 0) + 1
        return out

    return _with_status_lock(root, fail)


def _interrupt_task(repo: Path | str, task_id: str, *, state: str, detail: str) -> dict[str, Any]:
    root = Path(repo).resolve()
    document = load_active_plan(root)
    _task_definition(document, task_id)

    def interrupt(data: dict[str, Any]) -> dict[str, Any]:
        current = _task_entry(data, task_id).get("state")
        if current not in {"running", "awaiting_agent", "awaiting_approval"}:
            raise ValueError(f"task {task_id} cannot transition to {state} from {current}")
        out, entry = _set_task_state(data, task_id, state)
        entry["detail"] = detail[:500]
        out["tasks"][task_id] = entry
        out["state_revision"] = int(out.get("state_revision") or 0) + 1
        return out

    return _with_status_lock(root, interrupt)


def block_task(repo: Path | str, task_id: str, *, detail: str) -> dict[str, Any]:
    return _interrupt_task(repo, task_id, state="blocked", detail=detail)


def cancel_task(repo: Path | str, task_id: str, *, detail: str) -> dict[str, Any]:
    return _interrupt_task(repo, task_id, state="cancelled", detail=detail)


def retry_task(repo: Path | str, task_id: str) -> dict[str, Any]:
    root = Path(repo).resolve()
    document = load_active_plan(root)
    _task_definition(document, task_id)

    def retry(data: dict[str, Any]) -> dict[str, Any]:
        state = _task_entry(data, task_id).get("state")
        if state not in {"failed", "blocked", "cancelled"}:
            raise ValueError(f"task {task_id} cannot retry from {state}")
        out, _entry = _set_task_state(data, task_id, "ready")
        out["state_revision"] = int(out.get("state_revision") or 0) + 1
        return out

    return _with_status_lock(root, retry)


def _bump_semver(version: str, kind: str) -> str:
    parts = version.strip().split(".")
    while len(parts) < STATUS_PATH_PARTS:
        parts.append("0")
    major, minor, patch = (int(parts[0]), int(parts[1]), int(parts[2]))
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def bump_kind_for_phase(phase: str) -> str:
    if phase == "INTEGRATE":
        return "minor"
    return "patch"


def _assert_phase_transition(
    current: str,
    target: str,
    *,
    allow_restart: bool = False,
) -> None:
    """Explicit forward graph: same phase only for idempotent re-complete; +1 next.

    Retroceso/reinicio only when allow_restart=True (explicit reset operation).
    """
    if current not in PHASE_INDEX or target not in PHASE_INDEX:
        raise ValueError(f"unknown phase in transition {current!r} → {target!r}")
    cur_i, tgt_i = PHASE_INDEX[current], PHASE_INDEX[target]
    if tgt_i == cur_i:
        return  # same phase — idempotent re-complete handled by run_id dedup
    if tgt_i == cur_i + 1:
        return
    if allow_restart and tgt_i == 0 and cur_i == len(PHASES) - 1:
        # STATUS → DEFINE only as explicit restart
        return
    if tgt_i < cur_i:
        raise ValueError(f"phase regress {current} → {target} rejected; use explicit restart operation if authorized")
    raise ValueError(
        f"invalid phase jump {current} → {target}; "
        f"next allowed is {PHASES[cur_i + 1] if cur_i + 1 < len(PHASES) else current}"
    )


def _with_status_lock(root: Path, fn):
    """Acquire exclusive lock, load status, run fn(data) -> data, write, release."""
    path = status_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with open(lock_path, "a+", encoding="utf-8") as lockf:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
        try:
            if path.is_file():
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                if not isinstance(data, dict):
                    raise ValueError("status.yaml must be a mapping")
            else:
                data = _default_status()
            data = _migrate_status_data(data)
            new_data = fn(data)
            if new_data is None:
                return data
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(
                yaml.safe_dump(new_data, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
            os.replace(tmp, path)
            return new_data
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)


def _atomic_write_yaml(path: Path, data: dict[str, Any]) -> None:
    """Legacy helper — prefer _with_status_lock for transactional updates."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(lock_path, "a+", encoding="utf-8") as lockf:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
        try:
            tmp.write_text(
                yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
            os.replace(tmp, path)
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)


@dataclass(frozen=True)
class _AdvanceContext:
    """Everything a completion needs, resolved once."""

    root: Path
    phase: str
    skill: str
    checksum_spec: str
    note: str
    run_id: str
    target: str
    allow_restart: bool
    bump_product_version: bool
    expected_revision: int | None


def _utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stamp_awaiting(data: dict[str, Any], phase: str) -> dict[str, Any]:
    out = dict(data)
    out["awaiting_agent"] = True
    out["awaiting_phase"] = phase
    out["updated_at"] = _utc_stamp()
    return out


def _receipt_key(phase: str, run_id: str) -> str:
    return f"{phase}:{run_id}"


def _seen_completion(data: dict[str, Any], run_id: str, phase: str) -> bool:
    receipts = data.get("completion_receipts") or {}
    if isinstance(receipts, dict) and _receipt_key(phase, run_id) in receipts:
        return True
    # Legacy window still consulted
    completed = list(data.get("completed_run_ids") or [])
    return run_id in completed


def _ensure_tools_on_path() -> None:
    tools = Path(__file__).resolve().parents[1]
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))


def _validated_evidence(ctx: _AdvanceContext) -> dict[str, Any]:
    """Revalidate evidence UNDER lock so stale content cannot complete (H19)."""
    from execution.evidence import load_evidence  # noqa: PLC0415  # import opcional: requiere tools/ en sys.path

    evidence = load_evidence(
        ctx.root,
        ctx.run_id,
        revalidate_content=True,
        expected_phase=ctx.phase,
        expected_skill=ctx.skill or None,
        expected_target=ctx.target or None,
        for_complete=True,
    )
    if evidence.get("outcome") != "succeeded":
        raise ValueError("evidence outcome is not succeeded")
    return evidence


def _completion_entry(
    ctx: _AdvanceContext,
    progress: dict[str, Any],
    evidence: dict[str, Any],
    now: str,
) -> dict[str, Any]:
    return {
        "advance": progress["advance"],
        "version": progress["product_version"],
        "state_revision": progress["state_revision"],
        "phase": ctx.phase,
        "skill": ctx.skill,
        "at": now,
        "note": ctx.note,
        "evidence_ok": True,
        "run_id": ctx.run_id,
        "work_digest": evidence.get("output_digest") or evidence.get("work_digest", ""),
    }


def _apply_completion(
    ctx: _AdvanceContext,
    data: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    """Return (state, idempotent_replay)."""
    out = dict(data)
    if _seen_completion(out, ctx.run_id, ctx.phase):
        return out, True
    if out.get("awaiting_agent"):
        raise ValueError("awaiting_agent must be resolved before complete")
    current = str(out.get("phase") or "DEFINE")
    _assert_phase_transition(current, ctx.phase, allow_restart=ctx.allow_restart)

    cur_rev = int(out.get("state_revision") or 0)
    if ctx.expected_revision is not None and ctx.expected_revision != cur_rev:
        raise ValueError(f"stale state_revision: expected {ctx.expected_revision}, have {cur_rev}")

    product_version = str(out.get("version") or "0.1.0")
    if ctx.bump_product_version:
        product_version = _bump_semver(product_version, bump_kind_for_phase(ctx.phase))
    state_revision = cur_rev + 1
    advance = int(out.get("advance") or 0) + 1
    now = _utc_stamp()
    progress = {"state_revision": state_revision, "advance": advance, "product_version": product_version}

    history = list(out.get("history") or [])
    history.append(_completion_entry(ctx, progress, evidence, now))
    evidence_log = list(out.get("evidence_log") or [])
    evidence_log.append(
        {
            "state_revision": state_revision,
            "checksum_spec": ctx.checksum_spec or evidence.get("plan_digest", ""),
            "run_id": ctx.run_id,
            "at": now,
            "phase": ctx.phase,
        }
    )
    completed = list(out.get("completed_run_ids") or [])
    completed.append(ctx.run_id)
    receipts = dict(out.get("completion_receipts") or {})
    receipts[_receipt_key(ctx.phase, ctx.run_id)] = {
        "at": now,
        "state_revision": state_revision,
        "plan_digest": evidence.get("plan_digest", ""),
        "output_digest": evidence.get("output_digest", ""),
    }
    out.update(
        {
            "schema_version": STATUS_SCHEMA_VERSION,
            "version": product_version,
            "state_revision": state_revision,
            "phase": ctx.phase,
            "advance": advance,
            "last_skill": ctx.skill,
            "checksum_spec": ctx.checksum_spec or out.get("checksum_spec") or "",
            "updated_at": now,
            "history": history[-50:],
            "evidence_log": evidence_log,
            # Compact window for diagnostics; durable identity is receipts.
            "completed_run_ids": completed[-200:],
            "completion_receipts": receipts,
            "awaiting_agent": False,
        }
    )
    out.pop("awaiting_phase", None)
    return out, False


def _advance_once(ctx: _AdvanceContext) -> dict[str, Any]:
    evidence = _validated_evidence(ctx)
    data, idempotent = _apply_completion(ctx, load_status(ctx.root), evidence)
    if idempotent:
        data = dict(data)
        data["_idempotent_replay"] = True
    return data


def _advance_locked(ctx: _AdvanceContext) -> dict[str, Any]:
    replay: dict[str, bool] = {"idempotent": False}

    def _run(data: dict[str, Any]) -> dict[str, Any]:
        evidence = _validated_evidence(ctx)
        out, idempotent = _apply_completion(ctx, data, evidence)
        replay["idempotent"] = idempotent
        return out

    result = _with_status_lock(ctx.root, _run)
    if replay["idempotent"]:
        result = dict(result)
        result["_idempotent_replay"] = True
    return result


def advance_status(  # noqa: PLR0913  # API pública: keyword-only, espejo del contrato de estado
    repo: Path | str,
    *,
    phase: str,
    skill: str = "",
    checksum_spec: str = "",
    note: str = "",
    write: bool = True,
    bump_product_version: bool = False,
    evidence_ok: bool = False,
    run_id: str = "",
    allow_awaiting: bool = False,
    allow_restart: bool = False,
    expected_revision: int | None = None,
    target: str = "",
) -> dict[str, Any]:
    """Advance bookkeeping under a full read→validate→write lock.

    Completing a phase requires validated evidence bound to phase/skill/target.
    Repeating the same run_id is idempotent (no double advance).
    """
    if phase not in PHASES:
        raise ValueError(f"unknown phase {phase!r}")

    root = Path(repo).resolve()

    if allow_awaiting and not evidence_ok:
        if not write:
            return _stamp_awaiting(load_status(root), phase)
        return _with_status_lock(root, lambda data: _stamp_awaiting(data, phase))

    if not evidence_ok:
        raise ValueError(
            "refusing status advance without evidence_ok=True "
            "(simulated/awaiting_agent/blocked must not complete a phase)"
        )
    if not run_id:
        raise ValueError("refusing status advance without validated run_id evidence")

    _ensure_tools_on_path()
    ctx = _AdvanceContext(
        root=root,
        phase=phase,
        skill=skill,
        checksum_spec=checksum_spec,
        note=note,
        run_id=run_id,
        target=target,
        allow_restart=allow_restart,
        bump_product_version=bump_product_version,
        expected_revision=expected_revision,
    )
    if not write:
        return _advance_once(ctx)
    return _advance_locked(ctx)


def resolve_awaiting_agent(  # noqa: PLR0913  # API pública: keyword-only
    repo: Path | str,
    *,
    run_id: str,
    phase: str,
    skill: str = "",
    target: str = "",
    write: bool = True,
) -> dict[str, Any]:
    """Clear awaiting_agent after validated evidence (H14/C11).

    Does not advance the phase by itself — call ``advance_status`` after resolve.
    Task-level closure uses ``complete_task`` (evidence + receipts); phase-level
    closure uses ``advance_status`` / CLI ``--complete``. Editing status.yaml
    manually is not required.
    """
    if phase not in PHASES:
        raise ValueError(f"unknown phase {phase!r}")
    if not run_id:
        raise ValueError("run_id required to resolve awaiting_agent")

    root = Path(repo).resolve()
    tools = Path(__file__).resolve().parents[1]
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    from execution.evidence import load_evidence  # noqa: PLC0415  # import opcional: requiere tools/ en sys.path

    def _resolve(data: dict[str, Any]) -> dict[str, Any]:
        data = dict(data)
        if not data.get("awaiting_agent"):
            data["_resolve_noop"] = True
            return data
        awaiting_phase = str(data.get("awaiting_phase") or phase)
        if awaiting_phase != phase:
            raise ValueError(f"awaiting_phase mismatch: status has {awaiting_phase}, got {phase}")
        # Validate evidence under lock
        evidence = load_evidence(
            root,
            run_id,
            revalidate_content=True,
            expected_phase=phase,
            expected_skill=skill or None,
            expected_target=target or None,
            for_complete=True,
        )
        if evidence.get("outcome") != "succeeded":
            raise ValueError("evidence outcome is not succeeded")
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        data["awaiting_agent"] = False
        data.pop("awaiting_phase", None)
        data["updated_at"] = now
        data["last_resolve_run_id"] = run_id
        return data

    if not write:
        return _resolve(load_status(root))
    return _with_status_lock(root, _resolve)
