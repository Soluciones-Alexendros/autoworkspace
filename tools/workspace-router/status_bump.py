"""Declarative status bump for .autoworkspace/status.yaml — transactional."""
from __future__ import annotations

import fcntl
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML required: pip install -r requirements-dev.txt") from exc

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
    while len(parts) < 3:
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
        raise ValueError(
            f"phase regress {current} → {target} rejected; "
            "use explicit restart operation if authorized"
        )
    raise ValueError(
        f"invalid phase jump {current} → {target}; "
        f"next allowed is {PHASES[cur_i + 1] if cur_i + 1 < len(PHASES) else current}"
    )


def _with_status_lock(root: Path, fn):  # noqa: ANN001
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


def advance_status(
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
            data = load_status(root)
            data = dict(data)
            data["awaiting_agent"] = True
            data["awaiting_phase"] = phase
            data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            return data

        def _await(data: dict[str, Any]) -> dict[str, Any]:
            data = dict(data)
            data["awaiting_agent"] = True
            data["awaiting_phase"] = phase
            data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            return data

        return _with_status_lock(root, _await)

    if not evidence_ok:
        raise ValueError(
            "refusing status advance without evidence_ok=True "
            "(simulated/awaiting_agent/blocked must not complete a phase)"
        )
    if not run_id:
        raise ValueError("refusing status advance without validated run_id evidence")

    import sys

    tools = Path(__file__).resolve().parents[1]
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    from execution.evidence import load_evidence

    replay = {"idempotent": False, "evidence": None}

    def _receipt_key(ph: str, rid: str) -> str:
        return f"{ph}:{rid}"

    def _seen_completion(data: dict[str, Any], rid: str, ph: str) -> bool:
        receipts = data.get("completion_receipts") or {}
        if isinstance(receipts, dict) and _receipt_key(ph, rid) in receipts:
            return True
        # Legacy window still consulted
        completed = list(data.get("completed_run_ids") or [])
        return rid in completed

    def _advance(data: dict[str, Any]) -> dict[str, Any]:
        data = dict(data)
        # Revalidate evidence UNDER lock so stale content between pre-check and
        # commit cannot complete (H19).
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
        replay["evidence"] = evidence

        if _seen_completion(data, run_id, phase):
            replay["idempotent"] = True
            return data

        if data.get("awaiting_agent"):
            raise ValueError("awaiting_agent must be resolved before complete")

        current = str(data.get("phase") or "DEFINE")
        _assert_phase_transition(current, phase, allow_restart=allow_restart)

        cur_rev = int(data.get("state_revision") or 0)
        if expected_revision is not None and expected_revision != cur_rev:
            raise ValueError(
                f"stale state_revision: expected {expected_revision}, have {cur_rev}"
            )

        product_version = str(data.get("version") or "0.1.0")
        if bump_product_version:
            kind = bump_kind_for_phase(phase)
            product_version = _bump_semver(product_version, kind)
        state_revision = cur_rev + 1
        advance = int(data.get("advance") or 0) + 1
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry = {
            "advance": advance,
            "version": product_version,
            "state_revision": state_revision,
            "phase": phase,
            "skill": skill,
            "at": now,
            "note": note,
            "evidence_ok": True,
            "run_id": run_id,
            "work_digest": evidence.get("output_digest") or evidence.get("work_digest", ""),
        }
        history = list(data.get("history") or [])
        history.append(entry)
        evidence_log = list(data.get("evidence_log") or [])
        evidence_log.append(
            {
                "state_revision": state_revision,
                "checksum_spec": checksum_spec or evidence.get("plan_digest", ""),
                "run_id": run_id,
                "at": now,
                "phase": phase,
            }
        )
        completed = list(data.get("completed_run_ids") or [])
        completed.append(run_id)
        receipts = dict(data.get("completion_receipts") or {})
        receipts[_receipt_key(phase, run_id)] = {
            "at": now,
            "state_revision": state_revision,
            "plan_digest": evidence.get("plan_digest", ""),
            "output_digest": evidence.get("output_digest", ""),
        }
        data.update(
            {
                "schema_version": 1,
                "version": product_version,
                "state_revision": state_revision,
                "phase": phase,
                "advance": advance,
                "last_skill": skill,
                "checksum_spec": checksum_spec or data.get("checksum_spec") or "",
                "updated_at": now,
                "history": history[-50:],
                "evidence_log": evidence_log,
                # Compact window for diagnostics; durable identity is receipts.
                "completed_run_ids": completed[-200:],
                "completion_receipts": receipts,
                "awaiting_agent": False,
            }
        )
        data.pop("awaiting_phase", None)
        return data

    if not write:
        data = _advance(load_status(root))
        if replay["idempotent"]:
            data = dict(data)
            data["_idempotent_replay"] = True
        return data

    result = _with_status_lock(root, _advance)
    if replay["idempotent"]:
        result = dict(result)
        result["_idempotent_replay"] = True
    return result


def resolve_awaiting_agent(
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
    import sys

    tools = Path(__file__).resolve().parents[1]
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    from execution.evidence import load_evidence

    def _resolve(data: dict[str, Any]) -> dict[str, Any]:
        data = dict(data)
        if not data.get("awaiting_agent"):
            data["_resolve_noop"] = True
            return data
        awaiting_phase = str(data.get("awaiting_phase") or phase)
        if awaiting_phase != phase:
            raise ValueError(
                f"awaiting_phase mismatch: status has {awaiting_phase}, got {phase}"
            )
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
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        data["awaiting_agent"] = False
        data.pop("awaiting_phase", None)
        data["updated_at"] = now
        data["last_resolve_run_id"] = run_id
        return data

    if not write:
        return _resolve(load_status(root))
    return _with_status_lock(root, _resolve)
