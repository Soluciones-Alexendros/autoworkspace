"""RED: reproduce orchestration defects (per-task staging, existence verifier, read-only).

Desired contracts from the remediation SDD. Failures on baseline confirm the
audited cause before T07-T10 turn them GREEN.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]


def _clean_clone_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in (
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_WORK_TREE",
        "GIT_DIR",
        "GIT_COMMON_DIR",
        "GIT_PREFIX",
    ):
        env.pop(key, None)
    return env


sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "workspace-router"))

from execution.evidence import load_evidence  # noqa: E402
from execution.ops import OpResult  # noqa: E402
from orchestrator.model import RunContext  # noqa: E402
from orchestrator.ports import AdapterResult  # noqa: E402
from orchestrator.run import _default_verifier  # noqa: E402
from orchestrator.runner import WorktreeAdapter  # noqa: E402
from orchestrator.scheduler import Scheduler  # noqa: E402
from orchestrator.worktrees import WorktreeManager  # noqa: E402
from status_bump import activate_plan, load_status  # noqa: E402


def _fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    subprocess.run(
        ["git", "clone", "--dissociate", f"file://{ROOT}", str(repo)],
        check=True,
        capture_output=True,
        env=_clean_clone_env(),
    )
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True, capture_output=True)
    return repo


def _cleanup(repo: Path) -> None:
    shutil.rmtree(repo, ignore_errors=True)


def _op_result(task: dict[str, Any], context: RunContext, detail: str = "ok") -> OpResult:
    return OpResult(
        operation_id=str(task["operation"]),
        outcome="succeeded",
        returncode=0,
        duration_ms=1,
        detail=detail,
        effect="write-workspace",
        run_id=str(uuid.uuid4()),
        plan_digest=hashlib.sha256(context.plan_digest.encode()).hexdigest(),
    )


class DependentReaderAdapter:
    """Task B requires A's artifact already present in the writer workspace."""

    def __init__(self) -> None:
        self.saw_prior: bool | None = None

    def execute(self, task: dict[str, Any], context: RunContext) -> AdapterResult:
        if task["id"] == "task-a":
            (context.repo / "a.txt").write_text("from-a\n", encoding="utf-8")
            return AdapterResult("succeeded", operation_result=_op_result(task, context))
        prior = context.repo / "a.txt"
        self.saw_prior = prior.is_file() and prior.read_text(encoding="utf-8") == "from-a\n"
        if not self.saw_prior:
            return AdapterResult(
                "failed",
                detail="dependent writer missing integrated prior artifact",
                operation_result=_op_result(task, context, detail="missing prior"),
            )
        (context.repo / "b.txt").write_text("from-b\n", encoding="utf-8")
        return AdapterResult("succeeded", operation_result=_op_result(task, context))


def _activate_dependency_plan(repo: Path) -> None:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    data = {
        "schema_version": 1,
        "plan_id": "orchestration-red-deps",
        "base_revision": revision,
        "tasks": [
            {
                "id": "task-a",
                "phase": "IMPLEMENT",
                "operation": "implement_api",
                "roles": ["role-back"],
                "depends_on": [],
                "read_scope": ["README.md"],
                "write_scope": ["a.txt"],
                "artifacts": ["a-patch"],
                "acceptance": ["a-written"],
                "verification": ["independent-content-check"],
                "on_failure": "stop",
            },
            {
                "id": "task-b",
                "phase": "IMPLEMENT",
                "operation": "implement_api",
                "roles": ["role-back"],
                "depends_on": ["task-a"],
                "read_scope": ["a.txt"],
                "write_scope": ["b.txt"],
                "artifacts": ["b-patch"],
                "acceptance": ["b-sees-a"],
                "verification": ["independent-content-check"],
                "on_failure": "stop",
            },
        ],
    }
    path = repo / "plan-red.md"
    path.write_text("# RED\n\n```yaml aw-plan\n" + yaml.safe_dump(data, sort_keys=False) + "```\n")
    activate_plan(repo, path)


def _content_verifier(task: dict[str, Any]) -> Any:
    def verify(result: OpResult, staging: Path) -> list[dict[str, Any]]:
        path = staging / task["write_scope"][0]
        ok = path.is_file() and path.read_text(encoding="utf-8") == f"from-{task['id'][-1]}\n"
        return [{"kind": "implementation_deliverable", "ok": ok, "detail": "content"}]

    return verify


def test_dependent_receives_prior_artifact_in_shared_staging(tmp_path: Path) -> None:
    """Shared run staging must expose prior patches to dependents; baseline uses per-task staging."""
    repo = _fixture_repo(tmp_path)
    try:
        _activate_dependency_plan(repo)
        adapter = DependentReaderAdapter()
        wrapper = WorktreeAdapter(repo, adapter, _content_verifier)
        summary = Scheduler(repo, adapter=wrapper).run()
        assert adapter.saw_prior is True
        assert summary.outcome == "pass"
        status = load_status(repo)
        assert status["tasks"]["task-a"]["state"] == "succeeded"
        assert status["tasks"]["task-b"]["state"] == "succeeded"
    finally:
        _cleanup(repo)


class ReadOnlyAdapter:
    def execute(self, task: dict[str, Any], context: RunContext) -> AdapterResult:
        detail = f"readonly-ok:{task['id']}"
        return AdapterResult(
            "succeeded",
            detail=detail,
            operation_result=_op_result(task, context, detail=detail),
        )


def _activate_readonly_plan(repo: Path) -> None:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    data = {
        "schema_version": 1,
        "plan_id": "orchestration-red-ro",
        "base_revision": revision,
        "tasks": [
            {
                "id": "read-only",
                "phase": "VALIDATE",
                "operation": "local_gates",
                "roles": ["role-back"],
                "depends_on": [],
                "read_scope": ["README.md"],
                "write_scope": [],
                "artifacts": ["readonly-report"],
                "acceptance": ["readonly-evidence"],
                "verification": ["independent-content-check"],
                "on_failure": "stop",
            }
        ],
    }
    path = repo / "plan-ro.md"
    path.write_text("# RED RO\n\n```yaml aw-plan\n" + yaml.safe_dump(data, sort_keys=False) + "```\n")
    activate_plan(repo, path)


def test_readonly_task_stores_real_evidence(tmp_path: Path) -> None:
    """Read-only tasks must pass verify_and_store; baseline skips it and closes without evidence."""
    repo = _fixture_repo(tmp_path)
    try:
        _activate_readonly_plan(repo)
        wrapper = WorktreeAdapter(
            repo,
            ReadOnlyAdapter(),
            lambda task: lambda result, staging: [{"kind": "gate_result", "ok": True, "detail": result.detail}],
        )
        summary = Scheduler(repo, adapter=wrapper).run()
        status = load_status(repo)
        task = status["tasks"]["read-only"]
        assert summary.outcome == "pass", summary
        assert task["state"] == "succeeded"
        assert task.get("run_id"), "read-only close requires a run_id bound to evidence"
        evidence = load_evidence(
            repo,
            task["run_id"],
            expected_phase="VALIDATE",
            expected_skill="project-publish",
            expected_target=str(repo),
            for_complete=True,
        )
        assert evidence["plan_id"] == "orchestration-red-ro"
        assert evidence["task_id"] == "read-only"
    finally:
        _cleanup(repo)


def test_default_verifier_rejects_empty_or_wrong_content(tmp_path: Path) -> None:
    """Existence alone is not acceptance; empty/wrong staged bytes must fail."""
    task = {
        "id": "content-check",
        "phase": "IMPLEMENT",
        "operation": "implement_api",
        "write_scope": ["artifact.txt"],
        "verification": ["independent-content-check"],
    }
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "artifact.txt").write_text("", encoding="utf-8")
    result = OpResult(
        operation_id="implement_api",
        outcome="succeeded",
        returncode=0,
        duration_ms=1,
        detail="writer claimed success",
        effect="write-workspace",
        run_id=str(uuid.uuid4()),
        plan_digest="x" * 64,
    )
    checks = _default_verifier(task)(result, staging)
    assert checks
    assert all(not item["ok"] for item in checks), checks


def test_resume_rejects_stale_patch_digest(tmp_path: Path) -> None:
    """Resume must not accept a succeeded task whose stored patch no longer matches the manifest."""
    repo = _fixture_repo(tmp_path)
    try:
        _activate_dependency_plan(repo)
        adapter = DependentReaderAdapter()
        # First run will fail on task-b under baseline; force-succeed path for A only via direct write.
        # Seed a fake succeeded receipt with a mismatched patch to prove stale rejection once resume rebuilds.

        revision = load_status(repo)["active_plan"]["base_revision"]
        run_id = "stale-run"
        run_dir = repo / ".autoworkspace" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        patch = run_dir / "task-a.patch"
        manifest = run_dir / "task-a.manifest.json"
        patch.write_bytes(b"stale-patch-bytes")
        manifest.write_text(
            json.dumps(
                {
                    "files": ["a.txt"],
                    "sha256": {"a.txt": "0" * 64},
                    "base_revision": revision,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        # Desired API: reconstructing staging from this pair must raise / fail digest check.
        manager = WorktreeManager(repo, revision)
        try:
            staging = manager.create("resume-staging")
            # Preferred contract after T09: validate_manifest_against_patch or rebuild_staging.
            validate = getattr(manager, "validate_patch_manifest", None)
            rebuild = getattr(manager, "rebuild_staging_from_artifacts", None)
            assert callable(validate) or callable(rebuild), (
                "WorktreeManager must expose patch/manifest validation or staging rebuild"
            )
            if callable(validate):
                validate(patch, json.loads(manifest.read_text(encoding="utf-8")))
                raise AssertionError("stale patch/manifest pair must be rejected")
            if callable(rebuild):
                rebuild(staging, [{"patch": patch, "manifest": manifest}])
                raise AssertionError("stale patch/manifest pair must be rejected")
        except (ValueError, AssertionError) as exc:
            if "must expose" in str(exc) or "must be rejected" in str(exc):
                raise
            # ValueError from validation is the desired GREEN outcome.
            assert (
                "stale" in str(exc).lower()
                or "digest" in str(exc).lower()
                or "hash" in str(exc).lower()
                or "manifest" in str(exc).lower()
            )
        finally:
            manager.cleanup()
        # Silence unused under RED when API missing — assertion above already fails.
        _ = adapter
    finally:
        _cleanup(repo)
