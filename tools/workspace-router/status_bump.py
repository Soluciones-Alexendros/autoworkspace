"""Declarative status bump for .autoworkspace/status.yaml — transactional."""

from __future__ import annotations

import fcntl
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML required: uv sync --frozen") from exc

STATUS_PATH_PARTS = 3
PHASES = ("DEFINE", "SCHEMAS", "IMPLEMENT", "VALIDATE", "INTEGRATE", "STATUS")
PHASE_INDEX = {p: i for i, p in enumerate(PHASES)}


def status_path(repo: Path) -> Path:
    return Path(repo).resolve() / ".autoworkspace" / "status.yaml"


def load_status(repo: Path | str) -> dict[str, Any]:
    path = status_path(Path(repo))
    if not path.is_file():
        return {
            "schema_version": 1,
            "version": "0.1.0",
            "phase": "DEFINE",
            "advance": 0,
            "last_skill": "",
            "checksum_spec": "",
            "updated_at": "",
            "state_revision": 0,
            "history": [],
            "completed_run_ids": [],
        }
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("status.yaml must be a mapping")
    return data


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
                data = {
                    "schema_version": 1,
                    "version": "0.1.0",
                    "phase": "DEFINE",
                    "advance": 0,
                    "last_skill": "",
                    "checksum_spec": "",
                    "updated_at": "",
                    "state_revision": 0,
                    "history": [],
                    "completed_run_ids": [],
                }
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
            "schema_version": 1,
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
    """Public API: clear awaiting_agent after validated evidence (H14/C11).

    Does not advance the phase by itself — call advance_status after resolve
    (or use complete_after_resolve). Editing status.yaml manually is not required.
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
