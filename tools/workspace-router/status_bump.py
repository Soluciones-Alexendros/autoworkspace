"""Declarative status bump for .autoworkspace/status.yaml."""
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


def _assert_phase_transition(current: str, target: str) -> None:
    """Reject illegal jumps (e.g. DEFINE → INTEGRATE)."""
    if current not in PHASE_INDEX or target not in PHASE_INDEX:
        raise ValueError(f"unknown phase in transition {current!r} → {target!r}")
    cur_i, tgt_i = PHASE_INDEX[current], PHASE_INDEX[target]
    # Allow same phase (re-complete) or +1 step only
    if tgt_i > cur_i + 1:
        raise ValueError(
            f"invalid phase jump {current} → {target}; "
            f"next allowed is {PHASES[cur_i + 1] if cur_i + 1 < len(PHASES) else current}"
        )


def _atomic_write_yaml(path: Path, data: dict[str, Any]) -> None:
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
) -> dict[str, Any]:
    """Advance bookkeeping. Completing a phase requires validated evidence.

    evidence_ok alone is insufficient — run_id must resolve to a stored
    successful (non-simulated) result unless allow_awaiting records a non-complete state.
    """
    if phase not in PHASES:
        raise ValueError(f"unknown phase {phase!r}")
    if allow_awaiting and not evidence_ok:
        # Record awaiting_agent without completing
        root = Path(repo).resolve()
        data = load_status(root)
        data["awaiting_agent"] = True
        data["awaiting_phase"] = phase
        data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if write:
            _atomic_write_yaml(status_path(root), data)
        return data

    if not evidence_ok:
        raise ValueError(
            "refusing status advance without evidence_ok=True "
            "(simulated/awaiting_agent/blocked must not complete a phase)"
        )
    if not run_id:
        raise ValueError("refusing status advance without validated run_id evidence")

    # Lazy import to avoid circular deps when tools/ not on path for callers
    import sys

    tools = Path(__file__).resolve().parents[1]
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    from execution.evidence import load_evidence

    root = Path(repo).resolve()
    evidence = load_evidence(root, run_id)
    if evidence.get("outcome") != "succeeded":
        raise ValueError("evidence outcome is not succeeded")

    data = load_status(root)
    current = str(data.get("phase") or "DEFINE")
    _assert_phase_transition(current, phase)

    product_version = str(data.get("version") or "0.1.0")
    if bump_product_version:
        kind = bump_kind_for_phase(phase)
        product_version = _bump_semver(product_version, kind)
    expected_rev = int(data.get("state_revision") or 0)
    state_revision = expected_rev + 1
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
        "work_digest": evidence.get("work_digest", ""),
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
            "awaiting_agent": False,
        }
    )
    if write:
        _atomic_write_yaml(status_path(root), data)
    return data
