"""Deterministic DAG scheduling with bounded concurrency and verified closure."""

from __future__ import annotations

import sys
import threading
import uuid
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any

from orchestrator.model import RunContext, RunSummary
from orchestrator.ports import AdapterResult, SubagentAdapter
from orchestrator.runner import WorktreeAdapter
from orchestrator.worktrees import RunWorkspace

WORKSPACE_ROUTER = Path(__file__).resolve().parents[1] / "workspace-router"
if str(WORKSPACE_ROUTER) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROUTER))

from state_paths import state_file  # noqa: E402
from status_bump import (  # noqa: E402
    block_task,
    cancel_task,
    complete_task,
    fail_task,
    load_active_plan,
    load_status,
    ready_tasks,
    start_task,
)


def plan_schedule(document: Any) -> list[list[str]]:
    """Return deterministic topological waves without persistent writes."""
    pending = {str(task["id"]): set(task["depends_on"]) for task in document.tasks}
    completed: set[str] = set()
    waves: list[list[str]] = []
    while pending:
        ready = sorted(task_id for task_id, dependencies in pending.items() if dependencies <= completed)
        if not ready:
            raise ValueError("dependency cycle in active plan")
        waves.append(ready)
        completed.update(ready)
        for task_id in ready:
            del pending[task_id]
    return waves


class Scheduler:
    def __init__(
        self,
        repo: Path,
        *,
        adapter: SubagentAdapter | None,
        max_parallel: int = 4,
        resume: bool = True,
    ) -> None:
        max_parallel_cap = 8
        if not 1 <= max_parallel <= max_parallel_cap:
            raise ValueError(f"max_parallel must be between 1 and {max_parallel_cap}")
        self.repo = repo.resolve()
        self.adapter = adapter
        self.max_parallel = max_parallel
        self.resume = resume
        self.cancel_event = threading.Event()
        self.document = load_active_plan(self.repo)

    def cancel(self) -> None:
        self.cancel_event.set()

    def _recover_interrupted(self) -> None:
        status = load_status(self.repo)
        for task_id, task in status["tasks"].items():
            if task.get("state") in {"running", "awaiting_agent", "awaiting_approval"}:
                block_task(self.repo, task_id, detail="interrupted run; reconcile before retry")

    def dry_run(self) -> RunSummary:
        results = tuple(
            AdapterResult("simulated", detail=f"planned: {','.join(wave)}") for wave in plan_schedule(self.document)
        )
        return RunSummary("simulated", results)

    def _execute(self, task: dict[str, Any], context: RunContext) -> AdapterResult:
        task_id = str(task["id"])
        try:
            start_task(self.repo, task_id)
        except Exception as exc:
            return AdapterResult("failed", detail=f"start failed: {exc}")
        assert self.adapter is not None
        try:
            result = self.adapter.execute(task, context)
        except Exception as exc:
            result = AdapterResult("failed", detail=f"adapter error: {type(exc).__name__}: {exc}")
        if result.outcome == "succeeded":
            if not result.run_id:
                result = AdapterResult("failed", detail="succeeded adapter result has no evidence run_id")
            else:
                try:
                    complete_task(self.repo, task_id, run_id=result.run_id, target=str(self.repo))
                    return result
                except Exception as exc:
                    result = AdapterResult("failed", run_id=result.run_id, detail=f"completion failed: {exc}")
        if result.outcome in {"blocked", "cancelled", "failed", "simulated"}:
            try:
                if result.outcome == "blocked":
                    block_task(self.repo, task_id, detail=result.detail)
                elif result.outcome == "cancelled":
                    cancel_task(self.repo, task_id, detail=result.detail)
                else:
                    fail_task(self.repo, task_id, detail=result.detail or result.outcome)
            except Exception as exc:
                return AdapterResult("failed", detail=f"{result.detail}; state failure: {exc}")
        return result

    def run(self) -> RunSummary:  # noqa: C901, PLR0912  # DAG loop: schedule/wait/stop branches
        if self.adapter is None:
            raise ValueError("adapter required for non-dry-run execution")
        status = load_status(self.repo)
        if not self.resume and any(task.get("state") != "pending" for task in status["tasks"].values()):
            raise ValueError("resume=false requires pending tasks or an explicit reset")
        self._recover_interrupted()
        context = RunContext(
            repo=self.repo,
            plan_id=self.document.plan_id,
            plan_digest=self.document.digest,
            base_revision=self.document.base_revision,
            run_id=str(uuid.uuid4()),
            adapter=type(self.adapter).__name__,
            cancel_event=self.cancel_event,
        )
        workspace: RunWorkspace | None = None
        if isinstance(self.adapter, WorktreeAdapter):
            workspace = RunWorkspace(self.repo, context.base_revision, context.run_id)
            self.adapter.bind_workspace(workspace)
            if self.resume:
                self._rebuild_from_succeeded(workspace)
        results: list[AdapterResult] = []
        running: dict[Future[AdapterResult], dict[str, Any]] = {}
        stop_scheduling = False
        try:
            with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
                while True:
                    if not stop_scheduling and not self.cancel_event.is_set():
                        for task in ready_tasks(self.repo):
                            if len(running) >= self.max_parallel:
                                break
                            if task in running.values():
                                continue
                            running[executor.submit(self._execute, task, context)] = task
                    if not running:
                        break
                    done, _pending = wait(tuple(running), return_when=FIRST_COMPLETED)
                    for future in done:
                        task = running.pop(future)
                        result = future.result()
                        results.append(result)
                        if result.outcome != "succeeded" and task["on_failure"] == "stop":
                            stop_scheduling = True
                    if stop_scheduling and not running:
                        break
        finally:
            if workspace is not None:
                workspace.cleanup()
        final = load_status(self.repo)
        states = [task.get("state") for task in final["tasks"].values()]
        if any(state == "failed" for state in states):
            outcome = "failed"
        elif self.cancel_event.is_set() or any(state == "cancelled" for state in states):
            outcome = "cancelled"
        elif states and all(state == "succeeded" for state in states):
            outcome = "pass"
        else:
            outcome = "blocked"
        return RunSummary(outcome, tuple(results))

    def _rebuild_from_succeeded(self, workspace: RunWorkspace) -> None:
        status = load_status(self.repo)
        items: list[dict[str, Any]] = []
        for task_id, task in status.get("tasks", {}).items():
            if task.get("state") != "succeeded":
                continue
            run_id = str(task.get("run_id") or "")
            if not run_id:
                continue
            # Prefer artifacts under the current workspace run directory naming.
            candidates = list(state_file(self.repo, "runs").glob(f"*/{task_id}.patch"))
            if not candidates:
                continue
            patch = sorted(candidates)[-1]
            manifest_path = patch.with_suffix(".manifest.json")
            if not manifest_path.is_file():
                raise ValueError(f"succeeded task {task_id} missing manifest for resume")
            items.append({"patch": patch, "manifest": manifest_path})
        if items:
            # Order by plan dependency waves so rebuild stays topological.
            order = {task_id: index for index, wave in enumerate(plan_schedule(self.document)) for task_id in wave}
            items.sort(key=lambda item: order.get(Path(item["patch"]).stem, 10**9))
            workspace.rebuild_staging_from_artifacts(items)
