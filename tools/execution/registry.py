"""Canonical execution registry: YAML SSOT + runtime OpSpec handlers."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML required") from exc

try:
    import jsonschema
except ImportError as exc:  # pragma: no cover
    raise SystemExit("jsonschema required: uv sync --frozen") from exc

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]
_REGISTRY_PATH = _HERE / "registry.yaml"
_SCHEMA_PATH = _HERE / "schemas" / "registry.schema.json"


@dataclass(frozen=True)
class OpSpec:
    operation_id: str
    effect: str
    skill: str
    require_approval: bool
    require_snapshot: bool = False
    timeout: int = 60
    recovery_required: bool = False
    argv_template: tuple[str, ...] | None = None
    description: str = ""


@dataclass(frozen=True)
class ToolSpec:
    tool_id: str
    skill: str
    entrypoint: str
    description: str
    execution_kind: str
    distribution: str
    operations: tuple[dict[str, Any], ...]
    raw: Mapping[str, Any]


_HANDLERS: dict[str, Callable[..., Any]] = {}
_TOOLS: dict[str, ToolSpec] | None = None
_CONTRACT_OPS: dict[str, dict[str, Any]] | None = None

# Runtime ops that run_registered dispatches. Each skill must exist as tool_id
# in registry.yaml. Declarative-only ops (agent/orchestrator) need no OpSpec.
OPERATIONS: dict[str, OpSpec] = {
    "create_snapshot": OpSpec(
        "create_snapshot",
        "write-workspace",
        "local-maintenance",
        require_approval=True,
        timeout=600,
        description="Create pre-change snapshot",
    ),
    "restore_snapshot": OpSpec(
        "restore_snapshot",
        "mutate-host",
        "local-maintenance",
        require_approval=True,
        require_snapshot=True,
        timeout=600,
        recovery_required=True,
        description="Restore snapshot into program staging only",
    ),
    "validate_snapshot": OpSpec(
        "validate_snapshot",
        "read",
        "local-maintenance",
        require_approval=False,
        description="Validate snapshot metadata",
    ),
    "clean_package_cache": OpSpec(
        "clean_package_cache",
        "mutate-host",
        "local-maintenance",
        require_approval=True,
        require_snapshot=True,
        timeout=600,
    ),
    "clean_journal": OpSpec(
        "clean_journal",
        "mutate-host",
        "local-maintenance",
        require_approval=True,
        require_snapshot=True,
        timeout=600,
    ),
    "clean_orphans": OpSpec(
        "clean_orphans",
        "mutate-host",
        "local-maintenance",
        require_approval=True,
        require_snapshot=True,
        timeout=600,
    ),
    "clean_temp": OpSpec(
        "clean_temp",
        "mutate-host",
        "local-maintenance",
        require_approval=True,
        require_snapshot=True,
        timeout=600,
    ),
    "clean_needrestart": OpSpec(
        "clean_needrestart",
        "mutate-host",
        "local-maintenance",
        require_approval=True,
        require_snapshot=True,
        timeout=600,
    ),
    "update_firmware": OpSpec(
        "update_firmware",
        "mutate-host",
        "local-maintenance",
        require_approval=True,
        require_snapshot=True,
        timeout=900,
    ),
    "clean_userspace_caches": OpSpec(
        "clean_userspace_caches",
        "mutate-host",
        "local-maintenance",
        require_approval=True,
        require_snapshot=True,
        timeout=600,
    ),
    "proton_send": OpSpec(
        "proton_send",
        "communicate-external",
        "local-email",
        require_approval=True,
        timeout=120,
        description="Send mail via Proton Bridge",
    ),
    "local_gates": OpSpec(
        "local_gates",
        "write-workspace",
        "project-publish",
        require_approval=False,
        timeout=1800,
        description="Local publish gates (may write via husky/gate scripts)",
    ),
}


def registry_path() -> Path:
    return _REGISTRY_PATH


def schema_path() -> Path:
    return _SCHEMA_PATH


def _load_yaml_registry() -> dict[str, Any]:
    text = _REGISTRY_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"{_REGISTRY_PATH}: root must be a mapping")
    return data


def _validate_schema(data: dict[str, Any]) -> list[str]:
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as exc:
        return [f"schema: {exc.message}"]
    return []


def load_tools(*, force: bool = False) -> dict[str, ToolSpec]:
    global _TOOLS, _CONTRACT_OPS
    if _TOOLS is not None and not force:
        return _TOOLS
    data = _load_yaml_registry()
    errs = _validate_schema(data)
    if errs:
        raise ValueError("; ".join(errs))
    tools: dict[str, ToolSpec] = {}
    contract_ops: dict[str, dict[str, Any]] = {}
    for raw in data.get("tools") or []:
        if not isinstance(raw, dict):
            raise ValueError("tool entry must be a mapping")
        tool_id = str(raw["tool_id"])
        if tool_id in tools:
            raise ValueError(f"duplicate tool_id: {tool_id}")
        ops = tuple(op for op in (raw.get("operations") or []) if isinstance(op, dict))
        spec = ToolSpec(
            tool_id=tool_id,
            skill=str(raw["skill"]),
            entrypoint=str(raw["entrypoint"]),
            description=str(raw["description"]),
            execution_kind=str(raw["execution_kind"]),
            distribution=str(raw["distribution"]),
            operations=ops,
            raw=raw,
        )
        tools[tool_id] = spec
        for op in ops:
            oid = str(op["id"])
            if oid in contract_ops:
                raise ValueError(f"duplicate operation id across registry: {oid}")
            contract_ops[oid] = {**op, "tool_id": tool_id, "skill": spec.skill}
    _TOOLS = tools
    _CONTRACT_OPS = contract_ops
    return tools


def known_tool_ids() -> frozenset[str]:
    return frozenset(load_tools())


def get_tool(tool_id: str) -> ToolSpec:
    tools = load_tools()
    if tool_id not in tools:
        raise KeyError(f"unknown tool_id: {tool_id}")
    return tools[tool_id]


def get_tool_for_skill(skill: str) -> ToolSpec | None:
    for tool in load_tools().values():
        if tool.skill == skill:
            return tool
    return None


def contract_operation_ids() -> frozenset[str]:
    load_tools()
    assert _CONTRACT_OPS is not None
    return frozenset(_CONTRACT_OPS)


def load_execution_contract_for_skill(skill: str) -> dict[str, Any]:
    """Return a contract-shaped dict for a skill from the central registry."""
    tool = get_tool_for_skill(skill)
    if tool is None:
        raise KeyError(f"no registry entry for skill: {skill}")
    raw = dict(tool.raw)
    raw["schema_version"] = 1
    raw["dialect"] = "autoworkspace.execution"
    raw["skill"] = tool.skill
    return raw


def register_handler(operation_id: str, handler: Callable[..., Any]) -> None:
    if operation_id not in OPERATIONS:
        raise KeyError(f"cannot register handler for unknown operation: {operation_id}")
    _HANDLERS[operation_id] = handler


def get_handler(operation_id: str) -> Callable[..., Any] | None:
    return _HANDLERS.get(operation_id)


def get_operation(operation_id: str) -> OpSpec:
    if operation_id not in OPERATIONS:
        raise KeyError(f"unknown operation: {operation_id}")
    return OPERATIONS[operation_id]


def known_operation_ids() -> frozenset[str]:
    return frozenset(OPERATIONS)


def resolve_argv(spec: OpSpec, params: dict[str, Any]) -> list[str]:
    """Build argv from template; never accept free-form argv from callers."""
    if spec.argv_template is None:
        return []
    argv = list(spec.argv_template)
    out: list[str] = []
    for part in argv:
        if part.startswith("{") and part.endswith("}"):
            key = part[1:-1]
            out.append(str(params.get(key, "")))
        else:
            out.append(part)
    return out


def check_registry(*, root: Path | None = None) -> list[str]:
    """Validate registry.yaml and consistency with runtime ops and skills/."""
    repo = root or _ROOT
    errors: list[str] = []
    try:
        data = _load_yaml_registry()
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [f"registry load: {exc}"]
    errors.extend(_validate_schema(data))

    try:
        tools = load_tools(force=True)
    except ValueError as exc:
        errors.append(str(exc))
        return errors

    skills_dir = repo / "skills"
    catalog = {p.name for p in skills_dir.iterdir() if p.is_dir()} if skills_dir.is_dir() else set()

    for path in skills_dir.glob("*/execution.yaml") if skills_dir.is_dir() else []:
        errors.append(f"forbidden skills execution.yaml: {path.relative_to(repo)}")

    seen_skills: set[str] = set()
    for tool_id, tool in tools.items():
        if tool.skill in seen_skills:
            errors.append(f"duplicate skill in registry: {tool.skill}")
        seen_skills.add(tool.skill)
        if tool.skill not in catalog:
            errors.append(f"tool {tool_id}: skill {tool.skill!r} not in skills/")
        if tool_id != tool.skill:
            # allowed but must be intentional; still require skill folder
            pass
        skill_path = skills_dir / tool.skill
        if skill_path.is_dir() and (skill_path / "execution.yaml").is_file():
            errors.append(f"tool {tool_id}: skill still has execution.yaml")

    for op_id, spec in OPERATIONS.items():
        if spec.skill not in tools and spec.skill not in {t.skill for t in tools.values()}:
            errors.append(f"runtime op {op_id}: skill {spec.skill!r} missing from registry")
        elif get_tool_for_skill(spec.skill) is None:
            errors.append(f"runtime op {op_id}: skill {spec.skill!r} missing from registry")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools.execution.registry")
    parser.add_argument("--check", action="store_true", help="Validate registry.yaml")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args(argv)
    if not args.check:
        parser.print_help()
        return 2
    errs = check_registry(root=args.root)
    if errs:
        for e in errs:
            print(f"FAIL {e}")
        print(f"REGISTRY: FAIL ({len(errs)} errors)")
        return 1
    tools = load_tools()
    n_ops = sum(len(t.operations) for t in tools.values())
    print(f"REGISTRY: OK ({len(tools)} tools, {n_ops} contract ops)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
