"""Portable preflight: resolve skill root and check requirements without installing."""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PreflightResult:
    ok: bool
    blocked_reasons: list[str] = field(default_factory=list)
    optional_missing: list[str] = field(default_factory=list)
    skill_root: str | None = None
    workspace_root: str | None = None


def resolve_workspace_root(start: Path | None = None) -> Path | None:
    cur = (start or Path.cwd()).resolve()
    for p in [cur, *cur.parents]:
        if (p / ".git").exists() and (p / "skills").is_dir():
            return p
        if (p / "skills").is_dir() and (p / "tools" / "workspace-router").is_dir():
            return p
    return None


def resolve_skill_root(
    skill: str,
    workspace: Path | None = None,
    *,
    skill_root: Path | None = None,
) -> Path | None:
    """Resolve skill root. Prefer explicit skill_root (standalone); else workspace/skills."""
    if skill_root is not None:
        candidate = Path(skill_root).resolve()
        if (candidate / "SKILL.md").is_file():
            return candidate
        return None
    ws = workspace or resolve_workspace_root()
    if ws is None:
        return None
    candidate = ws / "skills" / skill
    if (candidate / "SKILL.md").is_file():
        return candidate.resolve()
    return None


def check_binaries(required: list[str], optional: list[str] | None = None) -> PreflightResult:
    result = PreflightResult(ok=True)
    for b in required:
        if shutil.which(b) is None:
            result.ok = False
            result.blocked_reasons.append(f"missing required binary: {b}")
    for b in optional or []:
        if shutil.which(b) is None:
            result.optional_missing.append(b)
    return result


def check_shared_dependencies(skill_root: Path, deps: list[str]) -> list[str]:
    """Verify shared dependency paths relative to skill_root exist (or packaged copies)."""
    missing: list[str] = []
    for dep in deps:
        name = Path(dep).name  # tools/execution → execution
        candidates = [
            skill_root / dep,
            skill_root / "vendor" / dep,
            skill_root / "vendor" / name,
            skill_root / "lib" / dep,
            skill_root / "lib" / name,
            skill_root / name,
        ]
        # Workspace-relative: ../../tools/execution from skills/<name>
        candidates.append((skill_root / ".." / ".." / dep).resolve())
        if not any(c.exists() for c in candidates):
            missing.append(dep)
    return missing


def preflight_contract(
    contract: dict[str, Any],
    *,
    cwd: Path | None = None,
    skill_root: Path | None = None,
    allow_network: bool | None = None,
) -> PreflightResult:
    dist = contract.get("distribution")
    skill = contract["skill"]
    result = PreflightResult(ok=True)
    ws = resolve_workspace_root(cwd)
    result.workspace_root = str(ws) if ws else None

    if dist == "workspace-required" and ws is None and skill_root is None:
        result.ok = False
        result.blocked_reasons.append(
            "workspace-required skill: install full autoworkspace (skills/ + tools/); "
            "cwd is not an implicit installation"
        )
        return result

    resolved = resolve_skill_root(skill, ws, skill_root=skill_root)
    if resolved is None:
        result.ok = False
        result.blocked_reasons.append(f"skill root not found for {skill}")
        return result
    result.skill_root = str(resolved)

    # Shared dependencies (e.g. tools/execution) must be present for standalone
    shared = list(contract.get("shared_dependencies") or [])
    if dist == "standalone" and shared:
        missing = check_shared_dependencies(resolved, shared)
        if missing:
            result.ok = False
            result.blocked_reasons.append(
                f"standalone missing shared_dependencies: {missing}; "
                "package vendor copy or reclasificar workspace-required"
            )

    reqs = contract.get("system_requirements") or {}
    hard = list(reqs.get("binaries") or [])
    optional = list(reqs.get("optional_binaries") or [])
    bin_check = check_binaries(hard, optional)
    if not bin_check.ok:
        result.ok = False
        result.blocked_reasons.extend(bin_check.blocked_reasons)
    result.optional_missing.extend(bin_check.optional_missing)

    net_allowed = (
        allow_network
        if allow_network is not None
        else os.environ.get("AUTOWORKSPACE_ALLOW_NETWORK") == "1"
    )
    if reqs.get("network") and not net_allowed:
        result.ok = False
        result.blocked_reasons.append("network:required-but-not-authorized")

    return result
