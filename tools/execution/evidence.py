"""Evidence store: content digests (bytes), confined artifacts, phase binding."""
from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any

from execution.ops import NON_TERMINAL, OpResult

TERMINAL_OK = frozenset({"succeeded"})

# Paths (relative posix prefixes / names) excluded from content identity.
_EXCLUDE_DIR_NAMES = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        ".venv-aw",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        "dist",
        "build",
        ".eggs",
    }
)
_EXCLUDE_PREFIXES = (
    ".autoworkspace/evidence/",
    ".autoworkspace/status.yaml",
    ".autoworkspace/status.yaml.lock",
    ".autoworkspace/status.yaml.tmp",
    ".autoworkspace/journal/",
    ".autoworkspace/diary/",
)

_RUN_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

# Phase → allowed operation_id prefixes / exact ids for completion evidence.
PHASE_EVIDENCE_OPS: dict[str, frozenset[str]] = {
    "DEFINE": frozenset({"plan_specification", "local_gates", "spec_write"}),
    "SCHEMAS": frozenset({"plan_specification", "local_gates", "schema_write"}),
    "IMPLEMENT": frozenset({"local_gates", "implement"}),
    "VALIDATE": frozenset({"local_gates", "validate", "validate_snapshot"}),
    "INTEGRATE": frozenset({"local_gates", "integrate"}),
    "STATUS": frozenset({"local_gates", "status"}),
}


def _excluded(rel: str) -> bool:
    if any(rel == p.rstrip("/") or rel.startswith(p) for p in _EXCLUDE_PREFIXES):
        return True
    parts = rel.split("/")
    return any(p in _EXCLUDE_DIR_NAMES for p in parts)


def content_manifest(root: Path) -> dict[str, Any]:
    """Deterministic manifest: relative paths → sha256 of bytes (files) or link targets."""
    root = root.resolve()
    entries: dict[str, str] = {}
    if not root.is_dir():
        return {"schema_version": 1, "entries": entries, "digest": hashlib.sha256().hexdigest()}

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(
            d for d in dirnames if d not in _EXCLUDE_DIR_NAMES and not d.startswith(".venv")
        )
        for name in sorted(filenames):
            path = Path(dirpath) / name
            try:
                rel = path.relative_to(root).as_posix()
            except ValueError:
                continue
            if _excluded(rel):
                continue
            if path.is_symlink():
                try:
                    target = os.readlink(path)
                except OSError:
                    continue
                # Reject escapes outside root for identity purposes
                if os.path.isabs(target):
                    resolved = Path(target)
                else:
                    resolved = (path.parent / target).resolve()
                try:
                    resolved.relative_to(root)
                except ValueError:
                    entries[rel] = f"symlink-escape:{hashlib.sha256(target.encode()).hexdigest()}"
                    continue
                entries[rel] = f"symlink:{hashlib.sha256(target.encode()).hexdigest()}"
                continue
            if not path.is_file():
                continue
            h = hashlib.sha256()
            try:
                with open(path, "rb") as fh:
                    for chunk in iter(lambda: fh.read(65536), b""):
                        h.update(chunk)
            except OSError:
                continue
            entries[rel] = h.hexdigest()

    payload = json.dumps(entries, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode()).hexdigest()
    return {"schema_version": 1, "entries": entries, "digest": digest}


def work_digest(root: Path) -> str:
    """Content digest of workspace bytes (excludes evidence/status/admin)."""
    return content_manifest(root)["digest"]


def evidence_dir(repo: Path) -> Path:
    return Path(repo).resolve() / ".autoworkspace" / "evidence"


def _validate_run_id(run_id: str) -> str:
    if not run_id or not _RUN_ID_RE.match(run_id):
        raise ValueError(
            f"run_id must be a UUID (got {run_id!r}); path separators and free-form ids rejected"
        )
    if "/" in run_id or "\\" in run_id or ".." in run_id:
        raise ValueError("run_id path traversal rejected")
    return run_id


def _artifact_record(repo: Path, art: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(art, dict):
        path_s = str(art.get("path") or "")
        expected_hash = art.get("sha256")
    else:
        path_s = str(art)
        expected_hash = None
    if not path_s or ".." in Path(path_s).parts:
        raise ValueError(f"invalid artifact path: {path_s!r}")
    p = Path(path_s)
    if not p.is_absolute():
        p = Path(repo) / p
    p = p.resolve()
    root = Path(repo).resolve()
    try:
        p.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"artifact outside repo root: {path_s}") from exc
    if p.is_symlink():
        raise ValueError(f"artifact symlink rejected: {path_s}")
    if not p.is_file():
        raise ValueError(f"evidence artifact missing: {path_s}")
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    digest = h.hexdigest()
    if expected_hash and expected_hash != digest:
        raise ValueError(f"artifact content mismatch: {path_s}")
    return {
        "path": str(p.relative_to(root).as_posix()),
        "sha256": digest,
        "size": p.stat().st_size,
    }


def store_result(
    repo: Path,
    result: OpResult,
    *,
    artifacts: list[str | dict[str, Any]] | None = None,
    phase: str = "",
    skill: str = "",
    target: str = "",
    input_digest: str | None = None,
    output_digest: str | None = None,
    verifications: list[dict[str, Any]] | None = None,
) -> str:
    """Persist a validated run result; returns UUID run_id."""
    if result.outcome in NON_TERMINAL:
        raise ValueError(f"non-terminal outcome cannot be stored as evidence: {result.outcome}")
    if result.outcome not in TERMINAL_OK and result.outcome != "failed":
        raise ValueError(f"unsupported outcome for evidence: {result.outcome}")
    if result.outcome == "succeeded":
        if result.returncode not in (0, None):
            raise ValueError("succeeded requires returncode 0 or None")
        # Coherent: no failed actions encoded in detail markers
        if result.detail.startswith("ACTION_FAILED:"):
            raise ValueError("succeeded rejects failed action detail")

    if result.run_id:
        run_id = _validate_run_id(result.run_id)
    else:
        run_id = str(uuid.uuid4())
        _validate_run_id(run_id)

    ed = evidence_dir(repo)
    ed.mkdir(parents=True, exist_ok=True)
    # Confine store: reject if evidence dir is a symlink escape
    if ed.is_symlink():
        raise ValueError("evidence store must not be a symlink")

    root = Path(repo).resolve()
    out_digest = output_digest if output_digest is not None else work_digest(root)
    in_digest = input_digest if input_digest is not None else out_digest

    art_records = [_artifact_record(root, a) for a in (artifacts or [])]

    payload: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "operation_id": result.operation_id,
        "outcome": result.outcome,
        "returncode": result.returncode,
        "effect": result.effect,
        "plan_digest": result.plan_digest,
        "detail": _redact(result.detail),
        "artifacts": art_records,
        "input_digest": in_digest,
        "output_digest": out_digest,
        "work_digest": out_digest,  # alias for legacy readers
        "phase": phase,
        "skill": skill or "",
        "target": target or "",
        "verifications": list(verifications or []),
        "stored_at": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
    }
    path = ed / f"{run_id}.json"
    if path.exists():
        raise ValueError(f"evidence collision for run_id={run_id}")
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return run_id


def _redact(text: str) -> str:
    if not text:
        return ""
    # Strip common secret-ish patterns before persistence
    out = text
    for pat in (
        r"(?i)password[=:\s]+\S+",
        r"(?i)passwd[=:\s]+\S+",
        r"(?i)api[_-]?key[=:\s]+\S+",
        r"(?i)token[=:\s]+\S+",
        r"(?i)secret[=:\s]+\S+",
    ):
        out = re.sub(pat, "[REDACTED]", out)
    return out[:2000]


def load_evidence(
    repo: Path,
    run_id: str,
    *,
    revalidate_content: bool = True,
    expected_phase: str | None = None,
    expected_skill: str | None = None,
    expected_target: str | None = None,
    expected_operation: str | None = None,
) -> dict[str, Any]:
    _validate_run_id(run_id)
    ed = evidence_dir(repo)
    if ed.is_symlink():
        raise ValueError("evidence store symlink rejected")
    path = ed / f"{run_id}.json"
    if path.is_symlink():
        raise ValueError("evidence file symlink rejected")
    if not path.is_file():
        raise FileNotFoundError(f"evidence missing for run_id={run_id}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("outcome") in NON_TERMINAL:
        raise ValueError("evidence outcome is non-terminal")
    if data.get("outcome") != "succeeded":
        raise ValueError(f"evidence outcome not success: {data.get('outcome')}")

    root = Path(repo).resolve()
    for art in data.get("artifacts") or []:
        if isinstance(art, dict):
            _artifact_record(root, art)
        else:
            _artifact_record(root, art)

    if revalidate_content:
        current = work_digest(root)
        stored = data.get("output_digest") or data.get("work_digest") or ""
        if stored and current != stored:
            raise ValueError(
                "evidence stale: workspace content digest changed since verification "
                f"(stored={stored[:12]}… current={current[:12]}…)"
            )

    if expected_phase is not None:
        ev_phase = data.get("phase") or ""
        if ev_phase and ev_phase != expected_phase:
            raise ValueError(f"evidence phase mismatch: {ev_phase} != {expected_phase}")
        op = str(data.get("operation_id") or "")
        allowed = PHASE_EVIDENCE_OPS.get(expected_phase)
        if allowed is not None and op and op not in allowed:
            # Also allow exact skill-bound ops registered later via prefix match
            if not any(op == a or op.startswith(a + "_") for a in allowed):
                raise ValueError(
                    f"evidence operation {op!r} cannot complete phase {expected_phase}"
                )

    if expected_skill is not None and data.get("skill"):
        if data["skill"] != expected_skill:
            raise ValueError(f"evidence skill mismatch: {data['skill']} != {expected_skill}")
    if expected_target is not None and data.get("target"):
        if data["target"] != expected_target:
            raise ValueError(f"evidence target mismatch: {data['target']} != {expected_target}")
    if expected_operation is not None and data.get("operation_id"):
        if data["operation_id"] != expected_operation:
            raise ValueError(
                f"evidence operation mismatch: {data['operation_id']} != {expected_operation}"
            )

    return data


def new_run_id() -> str:
    return str(uuid.uuid4())
