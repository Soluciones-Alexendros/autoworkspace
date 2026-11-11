"""Complete controlled path: delegate → patch → staging → verify → close."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]

sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "workspace-router"))

from execution.evidence import load_evidence  # noqa: E402
from execution.ops import OpResult  # noqa: E402
from orchestrator.model import RunContext  # noqa: E402
from orchestrator.ports import AdapterResult  # noqa: E402
from orchestrator.runner import Verifier, WorktreeAdapter  # noqa: E402
from orchestrator.scheduler import Scheduler  # noqa: E402
from orchestrator.worktrees import _clean_git_env  # noqa: E402
from status_bump import activate_plan, load_status  # noqa: E402


def _task(task_id: str, phase: str, operation: str, path: str, dependencies: list[str]) -> dict[str, Any]:
    return {
        "id": task_id,
        "phase": phase,
        "operation": operation,
        "roles": ["role-back"],
        "depends_on": dependencies,
        "read_scope": ["README.md"],
        "write_scope": [path],
        "artifacts": [f"{task_id}-patch"],
        "acceptance": ["staged-content-verified"],
        "verification": ["independent-content-check"],
        "on_failure": "stop",
    }


def _activate(root: Path) -> None:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    data = {
        "schema_version": 1,
        "plan_id": "worktree-full-flow",
        "base_revision": revision,
        "tasks": [
            _task("define-spec", "DEFINE", "specify", "spec.md", []),
            _task("implement-output", "IMPLEMENT", "implement_api", "implementation.txt", ["define-spec"]),
            _task("validate-output", "VALIDATE", "local_gates", "validation.txt", ["implement-output"]),
        ],
    }
    path = root / "plan.md"
    path.write_text("# Fixture\n\n```yaml aw-plan\n" + yaml.safe_dump(data, sort_keys=False) + "```\n")
    activate_plan(root, path)


class WriteAdapter:
    def __init__(self, wrong_validation: bool = False) -> None:
        self.wrong_validation = wrong_validation

    def execute(self, task: dict[str, Any], context: RunContext) -> AdapterResult:
        content = "wrong\n" if self.wrong_validation and task["id"] == "validate-output" else f"{task['id']}\n"
        (context.repo / task["write_scope"][0]).write_text(content, encoding="utf-8")
        operation = OpResult(
            operation_id=task["operation"],
            outcome="succeeded",
            returncode=0,
            duration_ms=1,
            detail="controlled writer executed",
            effect="write-workspace",
            run_id=str(uuid.uuid4()),
            plan_digest=hashlib.sha256(context.plan_digest.encode()).hexdigest(),
        )
        return AdapterResult("succeeded", operation_result=operation)


def _verifier(task: dict[str, Any]) -> Verifier:
    kind = {
        "DEFINE": "spec_deliverable",
        "IMPLEMENT": "implementation_deliverable",
        "VALIDATE": "gate_result",
    }[task["phase"]]

    def verify(result: OpResult, staging: Path) -> list[dict[str, Any]]:
        content = (staging / task["write_scope"][0]).read_text(encoding="utf-8")
        return [{"kind": kind, "ok": content == f"{task['id']}\n", "detail": "staged bytes"}]

    return verify


def _fixture_repo(tmp_path: Path) -> Path:
    """Clone into an isolated repo so lint-staged cannot race the operator index."""
    repo = tmp_path / "repo"
    subprocess.run(
        ["git", "clone", "--dissociate", f"file://{ROOT}", str(repo)],
        check=True,
        capture_output=True,
        env=_clean_git_env(),
    )
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True, capture_output=True)
    return repo


def _cleanup_fixture(repo: Path) -> None:
    shutil.rmtree(repo, ignore_errors=True)


def test_complete_flow_closes_without_applying_to_operator_checkout(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    try:
        _activate(repo)
        adapter = WorktreeAdapter(repo, WriteAdapter(), _verifier)
        summary = Scheduler(repo, adapter=adapter).run()
        assert summary.outcome == "pass", summary
        status = load_status(repo)
        for task_id, phase, skill in (
            ("define-spec", "DEFINE", "plan-specification"),
            ("implement-output", "IMPLEMENT", "role-back"),
            ("validate-output", "VALIDATE", "project-publish"),
        ):
            task = status["tasks"][task_id]
            assert task["state"] == "succeeded"
            evidence = load_evidence(
                repo,
                task["run_id"],
                expected_phase=phase,
                expected_skill=skill,
                expected_target=str(repo),
                for_complete=True,
            )
            assert evidence["plan_id"] == "worktree-full-flow"
        for produced in ("spec.md", "implementation.txt", "validation.txt"):
            assert not (repo / produced).exists()
        runs = list((repo / ".machineroom" / "runs").glob("*/*.patch"))
        assert len(runs) == 3  # noqa: PLR2004  # three-phase fixture patches
    finally:
        _cleanup_fixture(repo)


def test_failed_staging_verification_prevents_close(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    try:
        _activate(repo)
        adapter = WorktreeAdapter(repo, WriteAdapter(wrong_validation=True), _verifier)
        summary = Scheduler(repo, adapter=adapter).run()
        assert summary.outcome == "failed"
        status = load_status(repo)
        assert status["tasks"]["define-spec"]["state"] == "succeeded"
        assert status["tasks"]["implement-output"]["state"] == "succeeded"
        assert status["tasks"]["validate-output"]["state"] == "failed"
    finally:
        _cleanup_fixture(repo)
