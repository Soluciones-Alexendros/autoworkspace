"""Load and semantically validate skills/*/execution.yaml (local extension)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML required") from exc

try:
    import jsonschema
except ImportError as exc:  # pragma: no cover
    raise SystemExit("jsonschema required: pip install -r requirements-dev.txt") from exc

DIALECT = "autoworkspace.execution"
SCHEMA_VERSION = 1
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EFFECTS = {
    "read",
    "write-workspace",
    "mutate-host",
    "communicate-external",
    "access-secret",
}
KINDS = {"agent", "script", "orchestrator"}
DISTRIBUTIONS = {"standalone", "workspace-required"}
TRI = {"yes", "no", "unknown"}
CRITICAL_KEYS = {
    "schema_version",
    "skill",
    "execution_kind",
    "distribution",
    "operations",
}

_SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "execution.schema.json"
_SCHEMA: dict[str, Any] | None = None


class ContractError(ValueError):
    pass


def _schema() -> dict[str, Any]:
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    return _SCHEMA


def _reject_duplicate_keys(loader: yaml.SafeLoader, node: yaml.nodes.MappingNode):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=False)
        if key in mapping:
            raise ContractError(f"duplicate YAML key: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=True)
    return mapping


class StrictLoader(yaml.SafeLoader):
    pass


StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _reject_duplicate_keys,
)


def load_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if len(text) > 200_000:
        raise ContractError(f"{path}: contract too large")
    data = yaml.load(text, Loader=StrictLoader)
    if not isinstance(data, dict):
        raise ContractError(f"{path}: root must be a mapping")
    return data


def _skill_md_version(skill_path: Path) -> str | None:
    skill_md = skill_path / "SKILL.md"
    if not skill_md.is_file():
        return None
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    try:
        fm = yaml.safe_load(text[4:end])
    except Exception:
        return None
    if not isinstance(fm, dict):
        return None
    meta = fm.get("metadata") or {}
    version = meta.get("version") if isinstance(meta, dict) else None
    if isinstance(version, str) and version.strip():
        return version.strip().strip('"')
    return None


def validate_contract(
    data: dict[str, Any],
    *,
    skill_dir: str,
    skill_path: Path | None = None,
    catalog_skills: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    # JSON Schema (draft 2020-12)
    try:
        jsonschema.validate(instance=data, schema=_schema())
    except jsonschema.ValidationError as exc:
        errors.append(f"schema: {exc.message}")

    for key in CRITICAL_KEYS:
        if key not in data:
            errors.append(f"missing critical key: {key}")
    unknown_critical = [
        k
        for k in data
        if k
        not in {
            "schema_version",
            "dialect",
            "skill",
            "skill_version",
            "execution_kind",
            "distribution",
            "shared_dependencies",
            "system_requirements",
            "operations",
            "handoffs",
            "normative_sources",
            "automation_limits",
        }
    ]
    if unknown_critical:
        errors.append(f"unknown fields (reject critical unknown): {unknown_critical}")
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"unsupported schema_version: {data.get('schema_version')}")
    if data.get("dialect", DIALECT) != DIALECT:
        errors.append(f"unsupported dialect: {data.get('dialect')}")
    skill = data.get("skill")
    if not isinstance(skill, str) or not NAME_RE.match(skill):
        errors.append("skill id invalid")
    elif skill != skill_dir:
        errors.append(f"skill {skill!r} != directory {skill_dir!r}")
    if data.get("execution_kind") not in KINDS:
        errors.append("execution_kind invalid")
    if data.get("distribution") not in DISTRIBUTIONS:
        errors.append("distribution invalid")

    # skill_version vs SKILL.md — hard error
    if skill_path is not None and data.get("skill_version"):
        md_ver = _skill_md_version(skill_path)
        if md_ver and md_ver != str(data["skill_version"]):
            errors.append(
                f"skill_version {data['skill_version']!r} != SKILL.md metadata.version {md_ver!r}"
            )

    ops = data.get("operations")
    op_ids: set[str] = set()
    if not isinstance(ops, list) or not ops:
        errors.append("operations must be a non-empty list")
    else:
        seen = set()
        for op in ops:
            if not isinstance(op, dict):
                errors.append("operation must be mapping")
                continue
            oid = op.get("id")
            if oid in seen:
                errors.append(f"duplicate operation id: {oid}")
            seen.add(oid)
            if isinstance(oid, str):
                op_ids.add(oid)
            if op.get("effect") not in EFFECTS:
                errors.append(f"operation {oid}: bad effect")
            if op.get("dry_run") not in TRI:
                errors.append(f"operation {oid}: dry_run must be yes|no|unknown")
            if op.get("idempotency") not in TRI:
                errors.append(f"operation {oid}: idempotency must be yes|no|unknown")

    for h in data.get("handoffs") or []:
        if not isinstance(h, dict) or "skill" not in h:
            errors.append("handoff missing skill")
            continue
        hs = str(h["skill"])
        if not NAME_RE.match(hs):
            errors.append(f"handoff skill invalid: {hs}")
        elif catalog_skills is not None and hs not in catalog_skills:
            errors.append(f"handoff skill does not exist: {hs}")

    return errors


def load_execution_contract(
    skill_path: Path,
    *,
    catalog_skills: set[str] | None = None,
) -> dict[str, Any]:
    """Load contract from an explicit skill root (standalone-safe)."""
    path = skill_path / "execution.yaml"
    if not path.is_file():
        raise ContractError(f"missing {path}")
    data = load_yaml(path)
    errs = validate_contract(
        data,
        skill_dir=skill_path.name,
        skill_path=skill_path,
        catalog_skills=catalog_skills,
    )
    if errs:
        raise ContractError("; ".join(errs))
    return data
