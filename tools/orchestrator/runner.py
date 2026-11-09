"""Subagent adapter wrapper that isolates writes and verifies staged patches."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

from execution.evidence import work_digest
from execution.ops import OpResult, verify_and_store
from execution.registry import get_operation

from orchestrator.model import RunContext
from orchestrator.ports import AdapterResult, SubagentAdapter
from orchestrator.worktrees import WorktreeManager

Verifier = Callable[[OpResult, Path], list[dict[str, Any]]]
VerifierFactory = Callable[[dict[str, Any]], Verifier]


class WorktreeAdapter:
    """Execute a writer in isolation and produce evidence after staged verification."""

    def __init__(self, repo: Path, adapter: SubagentAdapter, verifier_for: VerifierFactory) -> None:
        self.repo = repo.resolve()
        self.adapter = adapter
        self.verifier_for = verifier_for

    def execute(self, task: dict[str, Any], context: RunContext) -> AdapterResult:
        if not task["write_scope"]:
            return self.adapter.execute(task, context)
        manager = WorktreeManager(self.repo, context.base_revision)
        input_digest = work_digest(self.repo)
        try:
            writer = manager.create(f"{task['id']}-writer")
            staging = manager.create(f"{task['id']}-staging")
            child_context = replace(context, repo=writer)
            delegated = self.adapter.execute(task, child_context)
            if delegated.outcome != "succeeded" or delegated.operation_result is None:
                return delegated
            patch, manifest = manager.capture_patch(writer, task)
            run_dir = self.repo / ".autoworkspace" / "runs" / context.run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            patch_artifact = run_dir / f"{task['id']}.patch"
            manifest_artifact = run_dir / f"{task['id']}.manifest.json"
            shutil.copyfile(patch, patch_artifact)
            manifest_artifact.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            manager.apply_patch(staging, patch_artifact)
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
                ],
                verifier=self.verifier_for(task),
                verification_repo=staging,
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
            manager.cleanup()
