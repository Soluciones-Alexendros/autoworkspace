"""Structured aw-plan parser and DAG validation."""

from __future__ import annotations

import copy
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from contracts.plan import load_plan, parse_plan  # noqa: E402

FIXTURE = ROOT / "scripts" / "tests" / "fixtures" / "plans" / "minimal.md"
CURRENT_PLAN = ROOT / "tasks" / "plan-autoworkspace-integration.md"


def _document(data: dict[str, Any]) -> str:
    return "# Fixture\n\n```yaml aw-plan\n" + str(yaml.safe_dump(data, sort_keys=False)) + "```\n"


def _valid_data() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "plan_id": "fixture-v1",
        "base_revision": "0" * 40,
        "tasks": [
            {
                "id": "first",
                "phase": "IMPLEMENT",
                "operation": "implement_api",
                "roles": ["role-back"],
                "depends_on": [],
                "read_scope": ["README.md"],
                "write_scope": ["src/"],
                "artifacts": ["patch"],
                "acceptance": ["works"],
                "verification": ["pytest"],
                "on_failure": "stop",
            }
        ],
    }


def test_valid_fixture_and_digest() -> None:
    first = load_plan(FIXTURE)
    second = load_plan(FIXTURE)
    assert first.plan_id == "fixture-plan-v1"
    assert first.tasks[0]["id"] == "fixture-read"
    assert first.digest == second.digest


def test_current_increment_plan_is_valid_acyclic_dag() -> None:
    document = load_plan(CURRENT_PLAN)
    assert document.plan_id == "autoworkspace-integration-v1"
    assert len(document.tasks) == 35


def test_requires_exactly_one_block() -> None:
    data = _valid_data()
    with pytest.raises(ValueError, match="exactly one"):
        parse_plan(_document(data) + _document(data))


def test_rejects_duplicate_yaml_keys() -> None:
    text = _document(_valid_data()).replace("plan_id: fixture-v1", "plan_id: fixture-v1\nplan_id: other")
    with pytest.raises(ValueError, match="duplicate"):
        parse_plan(text)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda d: d["tasks"][0].update(depends_on=["missing"]), "unknown dependency"),
        (lambda d: d["tasks"][0].update(depends_on=["first"]), "cycle|self"),
        (lambda d: d["tasks"][0].update(write_scope=["../escape"]), "path"),
        (lambda d: d["tasks"][0].update(read_scope=["/etc"]), "path"),
    ],
)
def test_semantic_rejections(mutation: Callable[[dict[str, Any]], None], message: str) -> None:
    data = _valid_data()
    mutation(data)
    with pytest.raises(ValueError, match=message):
        parse_plan(_document(data))


def test_rejects_dependency_cycle() -> None:
    data = _valid_data()
    second = copy.deepcopy(data["tasks"][0])
    second["id"] = "second"
    second["depends_on"] = ["first"]
    data["tasks"][0]["depends_on"] = ["second"]
    data["tasks"].append(second)
    with pytest.raises(ValueError, match="cycle"):
        parse_plan(_document(data))


def test_schema_rejects_missing_task_contract() -> None:
    data = _valid_data()
    del data["tasks"][0]["verification"]
    with pytest.raises(ValueError, match="verification"):
        parse_plan(_document(data))
