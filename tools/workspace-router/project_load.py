"""Load and validate .autoworkspace/project.yaml."""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML required: uv sync --frozen") from exc

PHASES = ("DEFINE", "SCHEMAS", "IMPLEMENT", "VALIDATE", "INTEGRATE", "STATUS")
PROFILES = ("P0", "P1", "P2")


class ProjectConfigError(ValueError):
    pass


def find_project_file(repo: Path) -> Path | None:
    candidate = repo / ".autoworkspace" / "project.yaml"
    return candidate if candidate.is_file() else None


def load_project(repo: Path | str) -> dict[str, Any]:
    root = Path(repo).resolve()
    path = find_project_file(root)
    if path is None:
        raise ProjectConfigError(f"missing {root / '.autoworkspace' / 'project.yaml'}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ProjectConfigError("project.yaml must be a mapping")
    validate_project(data)
    data["_root"] = str(root)
    data["_path"] = str(path)
    return data


def validate_project(data: dict[str, Any]) -> None:
    profile = data.get("profile", "P1")
    if profile not in PROFILES:
        raise ProjectConfigError(f"profile must be one of {PROFILES}, got {profile!r}")
    phases = data.get("phases") or list(PHASES)
    if not isinstance(phases, list) or not phases:
        raise ProjectConfigError("phases must be a non-empty list")
    for p in phases:
        if p not in PHASES:
            raise ProjectConfigError(f"unknown phase {p!r}; allowed {PHASES}")
    skills = data.get("skills") or {}
    if not isinstance(skills, dict):
        raise ProjectConfigError("skills must be a mapping")
    for key in ("enabled", "disabled"):
        val = skills.get(key, [])
        if val is None:
            continue
        if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
            raise ProjectConfigError(f"skills.{key} must be a list of strings")


def filter_skills(catalog: list[str], project: dict[str, Any]) -> list[str]:
    """Apply enabled/disabled against the real catalog.

    - enabled absent / null → default catalog
    - enabled: [] → allow none (blocks routing)
    - disabled always wins
    - names not in catalog are rejected (ProjectConfigError via validate or here)
    """
    catalog_set = set(catalog)
    skills = project.get("skills") or {}
    if "enabled" in skills and skills["enabled"] is not None:
        enabled = skills["enabled"]
        if not isinstance(enabled, list):
            raise ProjectConfigError("skills.enabled must be a list")
        unknown = [s for s in enabled if s not in catalog_set]
        if unknown:
            raise ProjectConfigError(f"skills.enabled not in catalog: {unknown}")
        base = list(enabled)
    else:
        base = list(catalog)
    disabled = skills.get("disabled") or []
    unknown_dis = [s for s in disabled if s not in catalog_set]
    if unknown_dis:
        raise ProjectConfigError(f"skills.disabled not in catalog: {unknown_dis}")
    disabled_set = set(disabled)
    return [s for s in base if s not in disabled_set]


def handoff_for_phase(project: dict[str, Any], phase: str) -> str | None:
    h = project.get("handoffs") or {}
    mapping = {
        "DEFINE": h.get("define", "plan-specification"),
        "SCHEMAS": h.get("continue", "plan-continue"),
        "IMPLEMENT": h.get("implement_back") or h.get("implement_front") or "role-back",
        "VALIDATE": h.get("validate", "plan-validators"),
        "INTEGRATE": h.get("integrate_publish") or h.get("integrate_hooks") or "project-publish",
        "STATUS": h.get("continue", "plan-continue"),
    }
    return mapping.get(phase)
