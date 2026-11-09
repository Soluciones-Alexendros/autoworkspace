"""Behavior of the public execute → verify → evidence pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from execution.evidence import load_evidence  # noqa: E402
from execution.ops import OpResult, VerifiedExecution, run_verified  # noqa: E402
from execution.registry import register_handler  # noqa: E402


def _write_spec(params: dict[str, Any]) -> int:
    path = Path(params["repo"]) / "spec.md"
    path.write_text(str(params["content"]), encoding="utf-8")
    return 0


def _verify_spec(result: OpResult, repo: Path) -> list[dict[str, Any]]:
    content = (repo / "spec.md").read_text(encoding="utf-8")
    return [{"kind": "spec_deliverable", "ok": content == "approved-spec\n", "detail": "content"}]


def _run(repo: Path, **overrides: Any) -> VerifiedExecution:
    params = overrides.pop("params", {"repo": str(repo), "content": "approved-spec\n"})
    options: dict[str, Any] = {
        "repo": repo,
        "phase": "DEFINE",
        "skill": "plan-specification",
        "target": str(repo),
        "plan_id": "fixture-plan",
        "task_id": "fixture-spec",
        "artifacts": ["spec.md"],
        "verifier": _verify_spec,
    }
    options.update(overrides)
    return run_verified("specify", params, **options)


def test_verified_execution_stores_real_input_output_and_task(tmp_path: Path) -> None:
    register_handler("specify", _write_spec)
    executed = _run(tmp_path)
    assert executed.outcome == "succeeded"
    assert executed.input_digest != executed.output_digest
    evidence = load_evidence(
        tmp_path,
        executed.run_id,
        expected_phase="DEFINE",
        expected_skill="plan-specification",
        expected_target=str(tmp_path),
        for_complete=True,
    )
    assert evidence["plan_id"] == "fixture-plan"
    assert evidence["task_id"] == "fixture-spec"
    assert evidence["operation_id"] == "specify"


def test_verifier_is_required_before_effects(tmp_path: Path) -> None:
    register_handler("specify", _write_spec)
    with pytest.raises(ValueError, match="verifier"):
        _run(tmp_path, verifier=None)
    assert not (tmp_path / "spec.md").exists()


def test_failed_verification_is_not_successful_evidence(tmp_path: Path) -> None:
    register_handler("specify", _write_spec)
    executed = _run(tmp_path, params={"repo": str(tmp_path), "content": "wrong\n"})
    assert executed.outcome == "failed"
    payload = json.loads(
        (tmp_path / ".autoworkspace" / "evidence" / f"{executed.run_id}.json").read_text(encoding="utf-8")
    )
    assert payload["outcome"] == "failed"
    with pytest.raises(ValueError, match="outcome"):
        load_evidence(tmp_path, executed.run_id, for_complete=True)


def test_skill_mismatch_is_rejected_before_effects(tmp_path: Path) -> None:
    register_handler("specify", _write_spec)
    with pytest.raises(ValueError, match="skill"):
        _run(tmp_path, skill="role-back")
    assert not (tmp_path / "spec.md").exists()
