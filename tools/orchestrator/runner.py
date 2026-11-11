"""Subagent adapter wrapper that isolates writes and verifies staged patches."""

from __future__ import annotations

import contextlib
import json
import threading
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

from execution.evidence import work_digest
from execution.ops import OpResult, verify_and_store
from execution.registry import get_operation
from state_paths import state_file

from orchestrator.model import RunContext
from orchestrator.ports import AdapterResult, SubagentAdapter
from orchestrator.worktrees import RunWorkspace

Verifier = Callable[[OpResult, Path], list[dict[str, Any]]]
VerifierFactory = Callable[[dict[str, Any]], Verifier]


class WorktreeAdapter:
    """Execute tasks against a shared run staging area with transactional integration."""

    def __init__(self, repo: Path, adapter: SubagentAdapter, verifier_for: VerifierFactory) -> None:
        self.repo = repo.resolve()
        self.adapter = adapter
        self.verifier_for = verifier_for
        self._workspace: RunWorkspace | None = None
        self._lock = threading.Lock()

    def bind_workspace(self, workspace: RunWorkspace) -> None:
        with self._lock:
            self._workspace = workspace

    def _require_workspace(self, context: RunContext) -> RunWorkspace:
        with self._lock:
            if self._workspace is None:
                self._workspace = RunWorkspace(self.repo, context.base_revision, context.run_id)
            elif self._workspace.run_id != context.run_id:
                raise ValueError("run workspace bound to a different run_id")
            return self._workspace

    def execute(self, task: dict[str, Any], context: RunContext) -> AdapterResult:
        workspace = self._require_workspace(context)
        input_digest = work_digest(self.repo)
        write_scope = list(task.get("write_scope") or [])
        run_dir = state_file(self.repo, "runs", context.run_id)
        run_dir.mkdir(parents=True, exist_ok=True)

        if not write_scope:
            return self._execute_readonly(task, context, workspace, input_digest, run_dir)

        writer: Path | None = None
        try:
            writer = workspace.create_writer(str(task["id"]))
            child_context = replace(context, repo=writer)
            delegated = self.adapter.execute(task, child_context)
            if delegated.outcome != "succeeded" or delegated.operation_result is None:
                return delegated
            patch, manifest = workspace.manager.capture_patch(writer, task)
            patch_artifact = run_dir / f"{task['id']}.patch"
            manifest_artifact = run_dir / f"{task['id']}.manifest.json"
            patch_artifact.write_bytes(patch.read_bytes())
            manifest_artifact.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            policy_artifact = run_dir / f"{task['id']}.policy.json"
            policy_artifact.write_text(
                json.dumps({"harness": context.adapter, "task_id": task["id"]}, indent=2) + "\n",
                encoding="utf-8",
            )
            workspace.integrate(str(task["id"]), patch_artifact, manifest)
            operation_result: OpResult = delegated.operation_result
            verified = verify_and_store(
                operation_result,
                repo=self.repo,
                input_digest=input_digest,
                phase=str(task["phase"]),
                skill=get_operation(str(task["operation"])).skill,
                target=str(self.repo),
                plan_id=context.plan_id,
                task_id=str(task["id"]),
                artifacts=[
                    str(patch_artifact.relative_to(self.repo)),
                    str(manifest_artifact.relative_to(self.repo)),
                    str(policy_artifact.relative_to(self.repo)),
                ],
                verifier=self.verifier_for(task),
                verification_repo=workspace.staging,
            )
            return AdapterResult(
                verified.outcome,
                run_id=verified.run_id,
                detail=verified.result.detail,
                operation_result=verified.result,
            )
        except Exception as exc:
            return AdapterResult("failed", detail=f"worktree integration failed: {type(exc).__name__}: {exc}")
        finally:
            if writer is not None:
                with contextlib.suppress(Exception):
                    workspace.drop_writer(writer)

    def _execute_readonly(
        self,
        task: dict[str, Any],
        context: RunContext,
        workspace: RunWorkspace,
        input_digest: str,
        run_dir: Path,
    ) -> AdapterResult:
        try:
            delegated = self.adapter.execute(task, context)
            if delegated.outcome != "succeeded" or delegated.operation_result is None:
                return delegated
            artifact = run_dir / f"{task['id']}.readonly.json"
            payload = {
                "task_id": task["id"],
                "outcome": delegated.outcome,
                "detail": delegated.detail,
                "operation_id": delegated.operation_result.operation_id,
                "adapter_run_id": delegated.operation_result.run_id,
            }
            artifact.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            verified = verify_and_store(
                delegated.operation_result,
                repo=self.repo,
                input_digest=input_digest,
                phase=str(task["phase"]),
                skill=get_operation(str(task["operation"])).skill,
                target=str(self.repo),
                plan_id=context.plan_id,
                task_id=str(task["id"]),
                artifacts=[str(artifact.relative_to(self.repo))],
                verifier=self.verifier_for(task),
                verification_repo=workspace.staging,
            )
            return AdapterResult(
                verified.outcome,
                run_id=verified.run_id,
                detail=verified.result.detail,
                operation_result=verified.result,
            )
        except Exception as exc:
            return AdapterResult("failed", detail=f"readonly verification failed: {type(exc).__name__}: {exc}")
