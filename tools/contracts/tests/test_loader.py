"""Contract loader and result schema tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BLOCKED_EXIT_CODE = 3
EXPECTED_REGISTRY_TOOLS = 11

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from contracts.loader import (  # noqa: E402
    ContractError,
    load_execution_contract,
    validate_contract,
)
from contracts.result import build_result, exit_code_for, validate_result  # noqa: E402
from execution.registry import load_tools  # noqa: E402


def test_pilots_load() -> None:
    for name in ("local-maintenance", "plan-continue", "project-publish"):
        doc = load_execution_contract(ROOT / "skills" / name)
        assert doc["skill"] == name
        assert doc["schema_version"] == 1


def test_all_registry_contracts() -> None:
    tools = load_tools(force=True)
    assert len(tools) == EXPECTED_REGISTRY_TOOLS
    for tool in tools.values():
        doc = load_execution_contract(ROOT / "skills" / tool.skill)
        assert doc["skill"] == tool.skill
        assert doc["operations"]


def test_audit_skills_have_no_registry_entry() -> None:
    tools = load_tools(force=True)
    for name in (
        "web-compliance",
        "web-owasp",
        "web-performance",
        "project-architecture",
        "project-libraries",
    ):
        assert name not in tools
        with pytest.raises(ContractError):
            load_execution_contract(ROOT / "skills" / name)


def test_reject_unknown_field() -> None:
    errs = validate_contract(
        {
            "schema_version": 1,
            "skill": "role-back",
            "execution_kind": "agent",
            "distribution": "standalone",
            "operations": [{"id": "x", "effect": "read", "dry_run": "yes", "idempotency": "yes"}],
            "evil_exec": "rm -rf /",
        },
        skill_dir="role-back",
    )
    assert any("unknown" in e for e in errs)


def test_result_outcomes_and_exit_codes() -> None:
    doc = build_result(
        skill="local-maintenance",
        skill_version="5.0.0",
        mode="dry-run",
        outcome="simulated",
        actions=[{"operation_id": "a", "status": "simulated", "effect": "read"}],
    )
    assert validate_result(doc) == []
    assert exit_code_for("simulated") == 0
    assert exit_code_for("blocked") == BLOCKED_EXIT_CODE
    assert exit_code_for("failed") == 1


def test_forbid_completed_status() -> None:
    errs = validate_result(
        {
            "schema_version": 1,
            "run_id": "x",
            "skill": "s",
            "mode": "m",
            "outcome": "succeeded",
            "started_at": "t",
            "finished_at": "t",
            "actions": [{"status": "completed"}],
        }
    )
    assert errs
