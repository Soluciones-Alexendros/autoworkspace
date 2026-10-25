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
SCHEMA_VERSION = 1

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

    def record_symlink(path: Path, rel: str) -> None:
        try:
            target = os.readlink(path)
        except OSError as exc:
            raise ValueError(f"unreadable symlink {rel}: {exc}") from exc
        if os.path.isabs(target):
            resolved = Path(target)
        else:
            resolved = (path.parent / target).resolve()
        try:
            resolved.relative_to(root)
            entries[rel] = f"symlink:{_sha256_bytes(target.encode())}"
        except ValueError:
            entries[rel] = f"symlink-escape:{_sha256_bytes(target.encode())}"

    def record_file(path: Path, rel: str) -> None:
        h = hashlib.sha256()
        try:
            with open(path, "rb") as fh:
                for chunk in iter(lambda: fh.read(65536), b""):
                    h.update(chunk)
        except OSError as exc:
            raise ValueError(f"unreadable file {rel}: {exc}") from exc
        entries[rel] = f"file:{h.hexdigest()}"

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # Capture directory symlinks before filtering them out of descent.
        symlink_dirs = []
        kept = []
        for d in sorted(dirnames):
            if d in _EXCLUDE_DIR_NAMES or d.startswith(".venv"):
                continue
            child = Path(dirpath) / d
            try:
                rel_d = child.relative_to(root).as_posix()
            except ValueError:
                continue
            if _excluded(rel_d):
                continue
            if child.is_symlink():
                record_symlink(child, rel_d)
                symlink_dirs.append(d)
            else:
                kept.append(d)
        dirnames[:] = kept

        for name in sorted(filenames):
            path = Path(dirpath) / name
            try:
                rel = path.relative_to(root).as_posix()
            except ValueError:
                continue
            if _excluded(rel):
                continue
            if path.is_symlink():
                record_symlink(path, rel)
                continue
            if not path.is_file():
                # Non-file special nodes still affect identity
                st = path.lstat()
                entries[rel] = f"special:{st.st_mode}"
                continue
            record_file(path, rel)

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
        raise ValueError(f"run_id must be a UUID (got {run_id!r}); path separators and free-form ids rejected")
    if "/" in run_id or "\\" in run_id or ".." in run_id:
        raise ValueError("run_id path traversal rejected")
    return run_id


def _path_confined(path: Path, root: Path) -> Path:
    """Ensure path is under root using component-wise lstat (no follow)."""
    root = root.resolve()
    if path.is_absolute():
        candidate = path
    else:
        candidate = root / path
    # Walk components; reject any symlink ancestor outside root policy
    parts = candidate.parts
    # Rebuild from root when relative; for absolute, verify each component
    acc = Path(parts[0]) if candidate.is_absolute() else root
    start = 1 if candidate.is_absolute() else 0
    if not candidate.is_absolute():
        acc = root
        start = len(root.parts)
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
                if not target.is_absolute():
                    target = (acc / target).resolve()
                else:
                    target = target.resolve()
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


def _artifact_record(repo: Path, art: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(art, dict):
        path_s = str(art.get("path") or "")
        expected_hash = art.get("sha256")
    else:
        path_s = str(art)
        expected_hash = None
    if not path_s or ".." in Path(path_s).parts:
        raise ValueError(f"invalid artifact path: {path_s!r}")
    root = Path(repo).resolve()
    p = Path(path_s)
    if not p.is_absolute():
        p = root / p

    # Check symlink BEFORE resolve (H03)
    if p.is_symlink() or (p.exists() and p.is_symlink()):
        raise ValueError(f"artifact symlink rejected: {path_s}")
    # Also reject if any ancestor under repo is a symlink escaping
    try:
        # lstat the path itself
        if os.path.lexists(p) and os.path.islink(p):
            raise ValueError(f"artifact symlink rejected: {path_s}")
    except OSError as exc:
        raise ValueError(f"artifact unreadable: {path_s}: {exc}") from exc

    # Component check under root without following the leaf if missing
    cur = root
    rel_parts = []
    try:
        rel_try = p.resolve().relative_to(root)
        rel_parts = list(rel_try.parts)
    except (ValueError, OSError):
        # Fall back to string-relative construction
        try:
            rel_parts = list(p.relative_to(root).parts)
        except ValueError as exc:
            raise ValueError(f"artifact outside repo root: {path_s}") from exc

    for part in rel_parts:
        nxt = cur / part
        if nxt.is_symlink():
            target = Path(os.readlink(nxt))
            if not target.is_absolute():
                target = (cur / target).resolve()
            else:
                target = target.resolve()
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise ValueError(f"artifact symlink ancestor escapes: {nxt}") from exc
            # Policy: any symlink in artifact path is rejected for evidence
            raise ValueError(f"artifact symlink rejected: {nxt}")
        cur = nxt

    p = cur
    if not p.is_file() or p.is_symlink():
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
        "type": "file",
    }


def _require_nonempty_str(data: dict[str, Any], key: str) -> str:
    val = data.get(key)
    if val is None or (isinstance(val, str) and not val.strip()):
        raise ValueError(f"evidence missing required field: {key}")
    if not isinstance(val, str):
        raise ValueError(f"evidence field {key} must be string, got {type(val).__name__}")
    return val


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
    # Digests must look like hex sha256
    for dk in ("plan_digest", "input_digest", "output_digest"):
        dig = str(data[dk])
        if len(dig) != 64 or any(c not in "0123456789abcdef" for c in dig.lower()):
            raise ValueError(f"evidence {dk} must be sha256 hex")
    if for_complete:
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
        artifacts = data.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise ValueError("evidence artifacts required and non-empty for complete")


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
    require_complete_fields: bool = False,
) -> str:
    """Persist a validated run result; returns UUID run_id.

    Succeeded evidence always stores required bindings. When
    ``require_complete_fields`` is True (phase completion path), also demands
    phase-matched operation, verifications and artifacts.
    """
    if result.outcome in NON_TERMINAL:
        raise ValueError(f"non-terminal outcome cannot be stored as evidence: {result.outcome}")
    if result.outcome not in TERMINAL_OK and result.outcome != "failed":
        raise ValueError(f"unsupported outcome for evidence: {result.outcome}")
    # Validate run_id shape before semantic field checks (traversal tests).
    if result.run_id:
        run_id = _validate_run_id(result.run_id)
    else:
        run_id = str(uuid.uuid4())
        _validate_run_id(run_id)

    if result.outcome == "succeeded":
        if result.returncode not in (0, None):
            raise ValueError("succeeded requires returncode 0 or None")
        if result.detail.startswith("ACTION_FAILED:"):
            raise ValueError("succeeded rejects failed action detail")
        if not (result.plan_digest or "").strip():
            raise ValueError("succeeded requires plan_digest")
        if not (phase or "").strip():
            raise ValueError("succeeded requires phase")
        if not (skill or "").strip():
            raise ValueError("succeeded requires skill")
        if not (target or "").strip():
            raise ValueError("succeeded requires target")

    ed = evidence_dir(repo)
    ed.mkdir(parents=True, exist_ok=True)
    if ed.is_symlink():
        raise ValueError("evidence store must not be a symlink")

    root = Path(repo).resolve()
    out_digest = output_digest if output_digest is not None else work_digest(root)
    in_digest = input_digest if input_digest is not None else out_digest

    art_records = [_artifact_record(root, a) for a in (artifacts or [])]

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "operation_id": result.operation_id,
        "outcome": result.outcome,
        "returncode": result.returncode,
        "effect": result.effect,
        "plan_digest": result.plan_digest or "",
        "detail": _redact(result.detail),
        "artifacts": art_records,
        "input_digest": in_digest,
        "output_digest": out_digest,
        "work_digest": out_digest,
        "phase": phase,
        "skill": skill or "",
        "target": target or "",
        "verifications": list(verifications or []),
        "stored_at": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
    }

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


def load_evidence(
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

    # Strict structural validation — no fail-open on missing bindings (H01)
    complete = for_complete or expected_phase is not None
    _validate_succeeded_payload(data, for_complete=complete)

    root = Path(repo).resolve()
    arts = data.get("artifacts") or []
    if not isinstance(arts, list):
        raise ValueError("evidence artifacts must be a list")
    for art in arts:
        _artifact_record(root, art)

    if revalidate_content:
        current = work_digest(root)
        stored = data.get("output_digest") or ""
        if not stored:
            raise ValueError("evidence missing output_digest")
        if current != stored:
            raise ValueError(
                "evidence stale: workspace content digest changed since verification "
                f"(stored={stored[:12]}… current={current[:12]}…)"
            )

    if expected_phase is not None:
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

    if expected_skill is not None:
        if not data.get("skill"):
            raise ValueError("evidence missing skill")
        if data["skill"] != expected_skill:
            raise ValueError(f"evidence skill mismatch: {data['skill']} != {expected_skill}")
    if expected_target is not None:
        if not data.get("target"):
            raise ValueError("evidence missing target")
        if data["target"] != expected_target:
            raise ValueError(f"evidence target mismatch: {data['target']} != {expected_target}")
    if expected_operation is not None:
        if not data.get("operation_id"):
            raise ValueError("evidence missing operation_id")
        if data["operation_id"] != expected_operation:
            raise ValueError(f"evidence operation mismatch: {data['operation_id']} != {expected_operation}")

    return data


def new_run_id() -> str:
    return str(uuid.uuid4())
