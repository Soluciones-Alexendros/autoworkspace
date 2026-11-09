"""Deterministic DAG scheduling through task state and verified evidence."""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "workspace-router"))

from execution.ops import OpResult, run_verified  # noqa: E402
from execution.registry import register_handler  # noqa: E402
from orchestrator.model import RunContext  # noqa: E402
from orchestrator.ports import AdapterResult  # noqa: E402
from orchestrator.scheduler import Scheduler, plan_schedule  # noqa: E402
from status_bump import activate_plan, load_status, retry_task, start_task  # noqa: E402


def _task(task_id: str, dependencies: list[str]) -> dict[str, Any]:
    return {
        "id": task_id,
        "phase": "IMPLEMENT",
        "operation": "implement_api",
        "roles": ["role-back"],
        "depends_on": dependencies,
        "read_scope": ["README.md"],
        "write_scope": [f"{task_id}.txt"],
        "artifacts": [f"{task_id}.txt"],
        "acceptance": ["content-verified"],
        "verification": ["fixture-verifier"],
        "on_failure": "stop",
    }


def _activate(root: Path, independent: bool = False) -> None:
    data = {
        "schema_version": 1,
        "plan_id": "scheduler-fixture",
        "base_revision": "0" * 40,
        "tasks": [_task("first", []), _task("second", [] if independent else ["first"])],
    }
    path = root / "plan.md"
    path.write_text("# Fixture\n\n```yaml aw-plan\n" + yaml.safe_dump(data, sort_keys=False) + "```\n")
    activate_plan(root, path)


def test_plan_schedule_is_deterministic_and_topological(tmp_path: Path) -> None:
    _activate(tmp_path)
    scheduler = Scheduler(tmp_path, adapter=None)
    assert plan_schedule(scheduler.document) == [["first"], ["second"]]
    before = (tmp_path / ".autoworkspace" / "status.yaml").read_bytes()
    assert scheduler.dry_run().outcome == "simulated"
    assert (tmp_path / ".autoworkspace" / "status.yaml").read_bytes() == before


def test_invalid_parallelism_is_rejected(tmp_path: Path) -> None:
    _activate(tmp_path)
    with pytest.raises(ValueError, match="max_parallel"):
        Scheduler(tmp_path, adapter=None, max_parallel=0)


class ControlledAdapter:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.active = 0
        self.max_active = 0
        self.executed: list[str] = []
        self._lock = threading.Lock()

    def execute(self, task: dict[str, Any], context: RunContext) -> AdapterResult:
        with self._lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            self.executed.append(task["id"])
        time.sleep(0.05)
        try:
            if self.fail:
                return AdapterResult("failed", detail="injected failure")
            task_id = task["id"]

            def verify(result: OpResult, repo: Path) -> list[dict[str, Any]]:
                content = (repo / f"{task_id}.txt").read_text(encoding="utf-8")
                return [{"kind": "implementation_deliverable", "ok": content == f"ok-{task_id}\n"}]

            executed = run_verified(
                task["operation"],
                {"repo": str(context.repo), "path": f"{task_id}.txt", "content": f"ok-{task_id}\n"},
                repo=context.repo,
                phase=task["phase"],
                skill="role-back",
                target=str(context.repo),
                plan_id=context.plan_id,
                task_id=task_id,
                artifacts=[f"{task_id}.txt"],
                verifier=verify,
            )
            return AdapterResult(executed.outcome, run_id=executed.run_id)
        finally:
            with self._lock:
                self.active -= 1


def _handler(params: dict[str, Any]) -> int:
    (Path(params["repo"]) / params["path"]).write_text(params["content"], encoding="utf-8")
    return 0


def test_scheduler_executes_roles_and_completes_real_evidence(tmp_path: Path) -> None:
    register_handler("implement_api", _handler)
    _activate(tmp_path)
    adapter = ControlledAdapter()
    summary = Scheduler(tmp_path, adapter=adapter).run()
    assert summary.outcome == "pass"
    assert adapter.executed == ["first", "second"]
    states = load_status(tmp_path)["tasks"]
    assert states["first"]["state"] == "succeeded"
    assert states["second"]["state"] == "succeeded"


def test_scheduler_limits_parallelism_without_lost_update(tmp_path: Path) -> None:
    register_handler("implement_api", _handler)
    _activate(tmp_path, independent=True)
    for task_id in ("first", "second"):
        (tmp_path / f"{task_id}.txt").write_text(f"ok-{task_id}\n", encoding="utf-8")
    adapter = ControlledAdapter()
    summary = Scheduler(tmp_path, adapter=adapter, max_parallel=2).run()
    assert summary.outcome == "pass"
    assert adapter.max_active == 2
    assert load_status(tmp_path)["state_revision"] == 5


def test_failure_stops_dependents_and_returns_failed(tmp_path: Path) -> None:
    _activate(tmp_path)
    adapter = ControlledAdapter(fail=True)
    summary = Scheduler(tmp_path, adapter=adapter).run()
    assert summary.outcome == "failed"
    assert adapter.executed == ["first"]
    states = load_status(tmp_path)["tasks"]
    assert states["first"]["state"] == "failed"
    assert states["second"]["state"] == "pending"


def test_resume_does_not_repeat_verified_tasks(tmp_path: Path) -> None:
    register_handler("implement_api", _handler)
    _activate(tmp_path)
    adapter = ControlledAdapter()
    assert Scheduler(tmp_path, adapter=adapter).run().outcome == "pass"
    assert Scheduler(tmp_path, adapter=adapter).run().outcome == "pass"
    assert adapter.executed == ["first", "second"]


def test_interrupted_running_task_requires_explicit_retry(tmp_path: Path) -> None:
    register_handler("implement_api", _handler)
    _activate(tmp_path)
    start_task(tmp_path, "first")
    adapter = ControlledAdapter()
    interrupted = Scheduler(tmp_path, adapter=adapter).run()
    assert interrupted.outcome == "blocked"
    assert adapter.executed == []
    assert load_status(tmp_path)["tasks"]["first"]["state"] == "blocked"
    retry_task(tmp_path, "first")
    assert Scheduler(tmp_path, adapter=adapter).run().outcome == "pass"


class CancelAdapter:
    def __init__(self) -> None:
        self.started = threading.Event()

    def execute(self, task: dict[str, Any], context: RunContext) -> AdapterResult:
        self.started.set()
        assert context.cancel_event.wait(timeout=2)
        return AdapterResult("cancelled", detail="operator cancellation")


def test_cancellation_is_terminal_but_not_success(tmp_path: Path) -> None:
    _activate(tmp_path)
    adapter = CancelAdapter()
    scheduler = Scheduler(tmp_path, adapter=adapter)
    outcome: list[str] = []
    thread = threading.Thread(target=lambda: outcome.append(scheduler.run().outcome))
    thread.start()
    assert adapter.started.wait(timeout=2)
    scheduler.cancel()
    thread.join(timeout=3)
    assert outcome == ["cancelled"]
    assert load_status(tmp_path)["tasks"]["first"]["state"] == "cancelled"
    assert retry_task(tmp_path, "first")["tasks"]["first"]["state"] == "ready"
