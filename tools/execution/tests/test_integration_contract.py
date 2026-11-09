"""Integration invariants for the canonical operation and evidence contract."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from execution import evidence  # noqa: E402
from execution.registry import (  # noqa: E402
    contract_operation_ids,
    get_operation,
    known_operation_ids,
    load_tools,
)


def _contract_operations() -> dict[str, dict[str, Any]]:
    operations: dict[str, dict[str, Any]] = {}
    for tool in load_tools(force=True).values():
        for operation in tool.operations:
            operations[str(operation["id"])] = operation
    return operations


def test_registry_is_single_source_for_operation_ids() -> None:
    assert known_operation_ids() == contract_operation_ids()


def test_runtime_policy_matches_registry() -> None:
    contracts = _contract_operations()
    for operation_id in known_operation_ids():
        spec = get_operation(operation_id)
        contract = contracts[operation_id]
        assert spec.effect == contract["effect"], operation_id
        assert spec.require_approval == contract.get("approval_required", False), operation_id
        assert spec.recovery_required == contract.get("recovery_required", False), operation_id


def test_completion_operations_are_runtime_resolvable() -> None:
    completion_ids = set().union(*evidence.PHASE_EVIDENCE_OPS.values())
    assert completion_ids <= known_operation_ids()


def test_public_e2e_does_not_construct_an_unexecuted_result() -> None:
    script = (ROOT / "scripts" / "tests" / "test_execution_e2e.sh").read_text(encoding="utf-8")
    assert "OpResult(" not in script
