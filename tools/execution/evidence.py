"""Evidence store: content digests (bytes), confined artifacts, phase binding."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

from execution.ops import NON_TERMINAL, OpResult

TERMINAL_OK = frozenset({"succeeded"})
SCHEMA_VERSION = 1
SHA256_HEX_LEN = 64

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

# Exact operation_id allowlists per phase (no permissive prefixes).
# local_gates / validate_snapshot never complete DEFINE or IMPLEMENT.
PHASE_EVIDENCE_OPS: dict[str, frozenset[str]] = {
    "DEFINE": frozenset({"plan_specification", "spec_write"}),
    "SCHEMAS": frozenset({"plan_specification", "schema_write"}),
    "IMPLEMENT": frozenset({"implement"}),
    "VALIDATE": frozenset({"local_gates", "validate", "validate_snapshot"}),
    "INTEGRATE": frozenset({"local_gates", "integrate"}),
    "STATUS": frozenset({"local_gates", "status"}),
}

# Required fields for succeeded evidence (store and load).
REQUIRED_SUCCEEDED_FIELDS = (
    "schema_version",
    "run_id",
    "operation_id",
    "outcome",
    "plan_digest",
    "input_digest",
    "output_digest",
    "phase",
    "skill",
    "target",
)

# Phase → required verification kinds (must appear with ok=True).
PHASE_REQUIRED_VERIFICATIONS: dict[str, frozenset[str]] = {
    "DEFINE": frozenset({"spec_deliverable"}),
    "SCHEMAS": frozenset({"schema_deliverable"}),
    "IMPLEMENT": frozenset({"implementation_deliverable"}),
    "VALIDATE": frozenset({"gate_result"}),
    "INTEGRATE": frozenset({"integrate_result"}),
    "STATUS": frozenset({"status_result"}),
}


def _excluded(rel: str) -> bool:
    if any(rel == p.rstrip("/") or rel.startswith(p) for p in _EXCLUDE_PREFIXES):
        return True
    parts = rel.split("/")
    return any(p in _EXCLUDE_DIR_NAMES for p in parts)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _lstat_type(path: Path) -> str:
    st = path.lstat()
    if path.is_symlink():
        return "symlink"
    if path.is_dir():
        return "dir"
    if path.is_file():
        return "file"
    return f"special:{st.st_mode}"


def _record_symlink(entries: dict[str, str], root: Path, path: Path, rel: str) -> None:
    try:
        target = os.readlink(path)
    except OSError as exc:
        raise ValueError(f"unreadable symlink {rel}: {exc}") from exc
    resolved = Path(target) if os.path.isabs(target) else (path.parent / target).resolve()
    kind = "symlink"
    try:
        resolved.relative_to(root)
    except ValueError:
        kind = "symlink-escape"
    entries[rel] = f"{kind}:{_sha256_bytes(target.encode())}"


def _record_file(entries: dict[str, str], path: Path, rel: str) -> None:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
    except OSError as exc:
        raise ValueError(f"unreadable file {rel}: {exc}") from exc
    entries[rel] = f"file:{h.hexdigest()}"


def _walk_dirs(root: Path, dirpath: str, dirnames: list[str], entries: dict[str, str]) -> list[str]:
    """Record directory symlinks and return the dirnames still worth descending."""
    kept: list[str] = []
    for name in sorted(dirnames):
        if name in _EXCLUDE_DIR_NAMES or name.startswith(".venv"):
            continue
        child = Path(dirpath) / name
        try:
            rel = child.relative_to(root).as_posix()
        except ValueError:
            continue
        if _excluded(rel):
            continue
        if child.is_symlink():
            _record_symlink(entries, root, child, rel)
        else:
            kept.append(name)
    return kept


def _walk_files(root: Path, dirpath: str, filenames: list[str], entries: dict[str, str]) -> None:
    for name in sorted(filenames):
        path = Path(dirpath) / name
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if _excluded(rel):
            continue
        if path.is_symlink():
            _record_symlink(entries, root, path, rel)
        elif not path.is_file():
            # Non-file special nodes still affect identity
            entries[rel] = f"special:{path.lstat().st_mode}"
        else:
            _record_file(entries, path, rel)


def content_manifest(root: Path) -> dict[str, Any]:
    """Deterministic manifest: relative paths → type + sha256 of bytes or link targets.

    Directory symlinks are recorded without following. Unreadable relevant files
    raise. Depth-first via os.walk(followlinks=False); symlink dirs appear as
    entries via an explicit scan of dirnames.
    """
    root = root.resolve()
    entries: dict[str, str] = {}
    if not root.is_dir():
        return {"schema_version": 1, "entries": entries, "digest": hashlib.sha256().hexdigest()}

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = _walk_dirs(root, dirpath, dirnames, entries)
        _walk_files(root, dirpath, filenames, entries)

    payload = json.dumps(entries, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode()).hexdigest()
    return {"schema_version": 1, "entries": entries, "digest": digest}


def work_digest(root: Path) -> str:
    """Content digest of workspace bytes (excludes evidence/status/admin)."""
    return str(content_manifest(root)["digest"])


def evidence_dir(repo: Path) -> Path:
    return Path(repo).resolve() / ".autoworkspace" / "evidence"


def _validate_run_id(run_id: str) -> str:
    if not run_id or not _RUN_ID_RE.match(run_id):
        raise ValueError(f"run_id must be a UUID (got {run_id!r}); path separators and free-form ids rejected")
    if "/" in run_id or "\\" in run_id or ".." in run_id:
        raise ValueError("run_id path traversal rejected")
    return run_id


def _path_confined(path: Path, root: Path) -> Path:
    """Ensure path is under root using component-wise lstat (no follow)."""
    root = root.resolve()
    candidate = path if path.is_absolute() else root / path
    # Walk components; reject any symlink ancestor outside root policy
    parts = candidate.parts
    # Rebuild from root when relative; for absolute, verify each component
    acc = Path(parts[0]) if candidate.is_absolute() else root
    1 if candidate.is_absolute() else 0
    if not candidate.is_absolute():
        acc = root
        len(root.parts)
        parts = candidate.parts
        # relative already rooted
        acc = root
        for part in Path(path).parts:
            if part in ("", "."):
                continue
            if part == "..":
                raise ValueError(f"path traversal rejected: {path}")
            nxt = acc / part
            if nxt.is_symlink():
                # Symlink component: resolve target and require under root
                target = Path(os.readlink(nxt))
                target = (acc / target).resolve() if not target.is_absolute() else target.resolve()
                try:
                    target.relative_to(root)
                except ValueError as exc:
                    raise ValueError(f"symlink ancestor escapes root: {nxt}") from exc
                acc = target
            else:
                acc = nxt
        return acc

    # Absolute path: resolve fully then check confinement
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"artifact outside repo root: {path}") from exc
    return resolved


def _artifact_spec(art: str | dict[str, Any]) -> tuple[str, Any]:
    """Normalize an artifact entry to (path string, expected sha256 or None)."""
    if isinstance(art, dict):
        return str(art.get("path") or ""), art.get("sha256")
    return str(art), None


def _reject_leaf_symlink(p: Path, path_s: str) -> None:
    try:
        if p.is_symlink() or (os.path.lexists(p) and os.path.islink(p)):
            raise ValueError(f"artifact symlink rejected: {path_s}")
    except OSError as exc:
        raise ValueError(f"artifact unreadable: {path_s}: {exc}") from exc


def _relative_parts(root: Path, p: Path, path_s: str) -> list[str]:
    try:
        return list(p.resolve().relative_to(root).parts)
    except (ValueError, OSError):
        pass
    try:
        return list(p.relative_to(root).parts)
    except ValueError as exc:
        raise ValueError(f"artifact outside repo root: {path_s}") from exc


def _assert_no_symlink_ancestors(root: Path, rel_parts: list[str]) -> Path:
    """Reject any symlink component under root; symlinks are never valid evidence."""
    cur = root
    for part in rel_parts:
        nxt = cur / part
        if nxt.is_symlink():
            target = Path(os.readlink(nxt))
            target = target.resolve() if target.is_absolute() else (cur / target).resolve()
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise ValueError(f"artifact symlink ancestor escapes: {nxt}") from exc
            raise ValueError(f"artifact symlink rejected: {nxt}")
        cur = nxt
    return cur


def _file_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _artifact_record(repo: Path, art: str | dict[str, Any]) -> dict[str, Any]:
    path_s, expected_hash = _artifact_spec(art)
    if not path_s or ".." in Path(path_s).parts:
        raise ValueError(f"invalid artifact path: {path_s!r}")
    root = Path(repo).resolve()
    p = Path(path_s)
    if not p.is_absolute():
        p = root / p

    # Check symlink BEFORE resolve (H03)
    _reject_leaf_symlink(p, path_s)
    p = _assert_no_symlink_ancestors(root, _relative_parts(root, p, path_s))
    if not p.is_file() or p.is_symlink():
        raise ValueError(f"evidence artifact missing: {path_s}")

    digest = _file_sha256(p)
    if expected_hash and expected_hash != digest:
        raise ValueError(f"artifact content mismatch: {path_s}")
    return {
        "path": str(p.relative_to(root).as_posix()),
        "sha256": digest,
        "size": p.stat().st_size,
        "type": "file",
    }


def _require_nonempty_str(data: dict[str, Any], key: str) -> str:
    val = data.get(key)
    if val is None or (isinstance(val, str) and not val.strip()):
        raise ValueError(f"evidence missing required field: {key}")
    if not isinstance(val, str):
        raise ValueError(f"evidence field {key} must be string, got {type(val).__name__}")
    return val


def _validate_digests(data: dict[str, Any]) -> None:
    for dk in ("plan_digest", "input_digest", "output_digest"):
        dig = str(data[dk])
        if len(dig) != SHA256_HEX_LEN or any(c not in "0123456789abcdef" for c in dig.lower()):
            raise ValueError(f"evidence {dk} must be sha256 hex")


def _validate_completion_requirements(data: dict[str, Any]) -> None:
    phase = str(data["phase"])
    op = str(data["operation_id"])
    allowed = PHASE_EVIDENCE_OPS.get(phase)
    if allowed is None:
        raise ValueError(f"unknown phase: {phase}")
    if op not in allowed:
        raise ValueError(f"evidence operation {op!r} cannot complete phase {phase}")
    required_v = PHASE_REQUIRED_VERIFICATIONS.get(phase, frozenset())
    verifications = data.get("verifications")
    if not isinstance(verifications, list) or not verifications:
        raise ValueError("evidence verifications required and non-empty for complete")
    kinds = {str(v.get("kind")) for v in verifications if isinstance(v, dict) and v.get("ok") is True}
    missing = required_v - kinds
    if missing:
        raise ValueError(f"evidence missing required verifications: {sorted(missing)}")


def _validate_succeeded_payload(data: dict[str, Any], *, for_complete: bool = False) -> None:
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"evidence schema_version must be {SCHEMA_VERSION}, got {data.get('schema_version')!r}")
    for key in REQUIRED_SUCCEEDED_FIELDS:
        if key in ("schema_version", "outcome"):
            continue
        _require_nonempty_str(data, key)
    if data.get("outcome") != "succeeded":
        raise ValueError(f"evidence outcome not success: {data.get('outcome')}")
    _validate_run_id(str(data["run_id"]))
    _validate_digests(data)
    if for_complete:
        _validate_completion_requirements(data)
        artifacts = data.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise ValueError("evidence artifacts required and non-empty for complete")


def _assert_storable_outcome(result: OpResult) -> None:
    if result.outcome in NON_TERMINAL:
        raise ValueError(f"non-terminal outcome cannot be stored as evidence: {result.outcome}")
    if result.outcome not in TERMINAL_OK and result.outcome != "failed":
        raise ValueError(f"unsupported outcome for evidence: {result.outcome}")


def _assert_succeeded_bindings(result: OpResult, phase: str, skill: str, target: str) -> None:
    if result.outcome != "succeeded":
        return
    if result.returncode not in (0, None):
        raise ValueError("succeeded requires returncode 0 or None")
    if result.detail.startswith("ACTION_FAILED:"):
        raise ValueError("succeeded rejects failed action detail")
    if not (result.plan_digest or "").strip():
        raise ValueError("succeeded requires plan_digest")
    for field, value in (("phase", phase), ("skill", skill), ("target", target)):
        if not (value or "").strip():
            raise ValueError(f"succeeded requires {field}")


def _resolve_run_id(result: OpResult) -> str:
    # Validate run_id shape before semantic field checks (traversal tests).
    if result.run_id:
        return _validate_run_id(result.run_id)
    run_id = str(uuid.uuid4())
    _validate_run_id(run_id)
    return run_id


def _store_payload(
    result: OpResult,
    run_id: str,
    bindings: dict[str, Any],
    digests: tuple[str, str],
    root: Path,
) -> dict[str, Any]:
    in_digest, out_digest = digests
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "operation_id": result.operation_id,
        "outcome": result.outcome,
        "returncode": result.returncode,
        "effect": result.effect,
        "plan_digest": result.plan_digest or "",
        "detail": _redact(result.detail),
        "artifacts": [_artifact_record(root, a) for a in (bindings.get("artifacts") or [])],
        "input_digest": in_digest,
        "output_digest": out_digest,
        "work_digest": out_digest,
        "phase": bindings.get("phase") or "",
        "skill": bindings.get("skill") or "",
        "target": bindings.get("target") or "",
        "verifications": list(bindings.get("verifications") or []),
        "stored_at": now,
    }


def store_result(  # noqa: PLR0913  # API pública de evidencia: keyword-only, espejo del schema
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
    require_complete_fields: bool = False,
) -> str:
    """Persist a validated run result; returns UUID run_id.

    Succeeded evidence always stores required bindings. When
    ``require_complete_fields`` is True (phase completion path), also demands
    phase-matched operation, verifications and artifacts.
    """
    _assert_storable_outcome(result)
    run_id = _resolve_run_id(result)
    _assert_succeeded_bindings(result, phase, skill, target)

    ed = evidence_dir(repo)
    ed.mkdir(parents=True, exist_ok=True)
    if ed.is_symlink():
        raise ValueError("evidence store must not be a symlink")

    root = Path(repo).resolve()
    out_digest = output_digest if output_digest is not None else work_digest(root)
    in_digest = input_digest if input_digest is not None else out_digest

    bindings: dict[str, Any] = {
        "artifacts": artifacts,
        "phase": phase,
        "skill": skill,
        "target": target,
        "verifications": verifications,
    }
    payload = _store_payload(result, run_id, bindings, (in_digest, out_digest), root)
    if result.outcome == "succeeded":
        _validate_succeeded_payload(payload, for_complete=require_complete_fields)

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


def _read_evidence_file(repo: Path, run_id: str) -> dict[str, Any]:
    _validate_run_id(run_id)
    ed = evidence_dir(repo)
    if ed.is_symlink():
        raise ValueError("evidence store symlink rejected")
    path = ed / f"{run_id}.json"
    if path.is_symlink():
        raise ValueError("evidence file symlink rejected")
    if not path.is_file():
        raise FileNotFoundError(f"evidence missing for run_id={run_id}")
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if data.get("outcome") in NON_TERMINAL:
        raise ValueError("evidence outcome is non-terminal")
    if data.get("outcome") != "succeeded":
        raise ValueError(f"evidence outcome not success: {data.get('outcome')}")
    return data


def _check_artifacts(root: Path, data: dict[str, Any]) -> None:
    arts = data.get("artifacts") or []
    if not isinstance(arts, list):
        raise ValueError("evidence artifacts must be a list")
    for art in arts:
        _artifact_record(root, art)


def _check_output_digest(root: Path, data: dict[str, Any]) -> None:
    current = work_digest(root)
    stored = data.get("output_digest") or ""
    if not stored:
        raise ValueError("evidence missing output_digest")
    if current != stored:
        raise ValueError(
            "evidence stale: workspace content digest changed since verification "
            f"(stored={stored[:12]}… current={current[:12]}…)"
        )


def _check_phase_operation(data: dict[str, Any], expected_phase: str) -> None:
    ev_phase = data.get("phase") or ""
    if not ev_phase:
        raise ValueError("evidence missing phase")
    if ev_phase != expected_phase:
        raise ValueError(f"evidence phase mismatch: {ev_phase} != {expected_phase}")
    op = str(data.get("operation_id") or "")
    if not op:
        raise ValueError("evidence missing operation_id")
    allowed = PHASE_EVIDENCE_OPS.get(expected_phase)
    if allowed is None:
        raise ValueError(f"unknown phase: {expected_phase}")
    # Exact match only — no permissive prefixes (H02)
    if op not in allowed:
        raise ValueError(f"evidence operation {op!r} cannot complete phase {expected_phase}")


def _check_expected_field(
    data: dict[str, Any],
    key: str,
    expected: str,
    *,
    missing: str,
    label: str,
) -> None:
    actual = data.get(key)
    if not actual:
        raise ValueError(missing)
    if actual != expected:
        raise ValueError(f"evidence {label} mismatch: {actual} != {expected}")


def load_evidence(  # noqa: PLR0913  # API pública de evidencia: keyword-only, espejo del schema
    repo: Path,
    run_id: str,
    *,
    revalidate_content: bool = True,
    expected_phase: str | None = None,
    expected_skill: str | None = None,
    expected_target: str | None = None,
    expected_operation: str | None = None,
    for_complete: bool = False,
) -> dict[str, Any]:
    data = _read_evidence_file(repo, run_id)
    # Strict structural validation — no fail-open on missing bindings (H01)
    complete = for_complete or expected_phase is not None
    _validate_succeeded_payload(data, for_complete=complete)

    root = Path(repo).resolve()
    _check_artifacts(root, data)

    if revalidate_content:
        _check_output_digest(root, data)

    if expected_phase is not None:
        _check_phase_operation(data, expected_phase)

    if expected_skill is not None:
        _check_expected_field(data, "skill", expected_skill, missing="evidence missing skill", label="skill")
    if expected_target is not None:
        _check_expected_field(data, "target", expected_target, missing="evidence missing target", label="target")
    if expected_operation is not None:
        _check_expected_field(
            data,
            "operation_id",
            expected_operation,
            missing="evidence missing operation_id",
            label="operation",
        )

    return data


def new_run_id() -> str:
    return str(uuid.uuid4())
