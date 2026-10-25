"""Contract loader and result schema tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from contracts.loader import ContractError, load_execution_contract, validate_contract  # noqa: E402
from contracts.result import build_result, exit_code_for, validate_result  # noqa: E402


def test_pilots_load():
    for name in ("local-maintenance", "plan-continue", "web-compliance"):
        doc = load_execution_contract(ROOT / "skills" / name)
        assert doc["skill"] == name
        assert doc["schema_version"] == 1


def test_all_catalog_contracts():
    skills = ROOT / "skills"
    for d in sorted(p for p in skills.iterdir() if p.is_dir()):
        if not (d / "execution.yaml").is_file():
            pytest.fail(f"missing execution.yaml for {d.name}")
        load_execution_contract(d)


def test_reject_unknown_field():
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


def test_result_outcomes_and_exit_codes():
    doc = build_result(
        skill="local-maintenance",
        skill_version="5.0.0",
        mode="dry-run",
        outcome="simulated",
        actions=[{"operation_id": "a", "status": "simulated", "effect": "read"}],
    )
    assert validate_result(doc) == []
    assert exit_code_for("simulated") == 0
    assert exit_code_for("blocked") == 3
    assert exit_code_for("failed") == 1


def test_forbid_completed_status():
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
