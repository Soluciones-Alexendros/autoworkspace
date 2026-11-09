"""Parse the single structured aw-plan block embedded in a canonical plan."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import jsonschema
import yaml

from contracts.loader import StrictLoader

_BLOCK_RE = re.compile(r"^```yaml aw-plan[\t ]*\n(.*?)^```[\t ]*$", re.MULTILINE | re.DOTALL)
_SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "plan.schema.json"


@dataclass(frozen=True)
class PlanDocument:
    plan_id: str
    base_revision: str
    tasks: tuple[dict[str, Any], ...]
    digest: str


def _schema() -> dict[str, Any]:
    data = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("plan schema must be a mapping")
    return data


def _validate_scope(task_id: str, field: str, scopes: list[str]) -> None:
    for scope in scopes:
        path = PurePosixPath(scope)
        if path.is_absolute() or ".." in path.parts or "\\" in scope or not scope.strip():
            raise ValueError(f"task {task_id}: invalid {field} path: {scope!r}")


def _validate_dependencies(tasks: list[dict[str, Any]]) -> None:
    ids = [str(task["id"]) for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate task id")
    known = set(ids)
    pending: dict[str, set[str]] = {}
    for task in tasks:
        task_id = str(task["id"])
        dependencies = set(task["depends_on"])
        unknown = dependencies - known
        if unknown:
            raise ValueError(f"task {task_id}: unknown dependency: {sorted(unknown)}")
        pending[task_id] = dependencies
    ordered: set[str] = set()
    while pending:
        ready = sorted(task_id for task_id, deps in pending.items() if deps <= ordered)
        if not ready:
            raise ValueError(f"dependency cycle or self-dependency: {sorted(pending)}")
        for task_id in ready:
            ordered.add(task_id)
            del pending[task_id]


def validate_plan(data: dict[str, Any]) -> None:
    try:
        jsonschema.validate(instance=data, schema=_schema())
    except jsonschema.ValidationError as exc:
        raise ValueError(f"invalid aw-plan: {exc.message}") from exc
    tasks = data["tasks"]
    for task in tasks:
        _validate_scope(str(task["id"]), "read_scope", task["read_scope"])
        _validate_scope(str(task["id"]), "write_scope", task["write_scope"])
    _validate_dependencies(tasks)


def parse_plan(text: str) -> PlanDocument:
    blocks = _BLOCK_RE.findall(text)
    if len(blocks) != 1:
        raise ValueError(f"expected exactly one yaml aw-plan block, found {len(blocks)}")
    data = yaml.load(blocks[0], Loader=StrictLoader)
    if not isinstance(data, dict):
        raise ValueError("aw-plan root must be a mapping")
    validate_plan(data)
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return PlanDocument(
        plan_id=str(data["plan_id"]),
        base_revision=str(data["base_revision"]),
        tasks=tuple(data["tasks"]),
        digest=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    )


def load_plan(path: Path) -> PlanDocument:
    return parse_plan(Path(path).read_text(encoding="utf-8"))
