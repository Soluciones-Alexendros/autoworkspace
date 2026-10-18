"""Evidence store for validated RunResults used by phase complete."""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from execution.ops import NON_TERMINAL, OpResult

TERMINAL_OK = frozenset({"succeeded"})


def work_digest(root: Path) -> str:
    """Stable digest of tracked tree metadata (paths + sizes + mtimes)."""
    root = root.resolve()
    h = hashlib.sha256()
    if not root.is_dir():
        return h.hexdigest()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        # skip heavy/irrelevant
        dirnames[:] = [
            d
            for d in dirnames
            if d not in {".git", "node_modules", ".venv", ".venv-aw", "__pycache__"}
        ]
        for name in sorted(filenames):
            path = Path(dirpath) / name
            try:
                st = path.stat()
            except OSError:
                continue
            rel = path.relative_to(root).as_posix()
            h.update(f"{rel}:{st.st_size}:{int(st.st_mtime)}".encode())
    return h.hexdigest()


def evidence_dir(repo: Path) -> Path:
    return Path(repo).resolve() / ".autoworkspace" / "evidence"


def store_result(repo: Path, result: OpResult, *, artifacts: list[str] | None = None) -> str:
    """Persist a validated run result; returns run_id."""
    if result.outcome in NON_TERMINAL:
        raise ValueError(f"non-terminal outcome cannot be stored as evidence: {result.outcome}")
    if result.outcome not in TERMINAL_OK and result.outcome != "failed":
        raise ValueError(f"unsupported outcome for evidence: {result.outcome}")
    run_id = result.run_id or f"{result.operation_id}:{int(time.time())}"
    ed = evidence_dir(repo)
    ed.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "run_id": run_id,
        "operation_id": result.operation_id,
        "outcome": result.outcome,
        "returncode": result.returncode,
        "effect": result.effect,
        "plan_digest": result.plan_digest,
        "detail": result.detail,
        "artifacts": list(artifacts or []),
        "work_digest": work_digest(Path(repo)),
        "stored_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    path = ed / f"{run_id.replace(':', '_')}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return run_id


def load_evidence(repo: Path, run_id: str) -> dict[str, Any]:
    ed = evidence_dir(repo)
    path = ed / f"{run_id.replace(':', '_')}.json"
    if not path.is_file():
        raise FileNotFoundError(f"evidence missing for run_id={run_id}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("outcome") in NON_TERMINAL:
        raise ValueError("evidence outcome is non-terminal")
    if data.get("outcome") != "succeeded":
        raise ValueError(f"evidence outcome not success: {data.get('outcome')}")
    for art in data.get("artifacts") or []:
        if not Path(art).is_file() and not (Path(repo) / art).is_file():
            raise ValueError(f"evidence artifact missing: {art}")
    return data
