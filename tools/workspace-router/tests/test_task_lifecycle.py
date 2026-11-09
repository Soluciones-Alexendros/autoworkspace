"""Task-level lifecycle backed by real run_verified evidence."""

from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "workspace-router"))

from execution.ops import run_verified  # noqa: E402
from execution.registry import register_handler  # noqa: E402
from status_bump import (  # noqa: E402
    activate_plan,
    complete_task,
    fail_task,
    ready_tasks,
    retry_task,
    start_task,
)


def _task(task_id: str, dependencies: list[str]) -> dict:
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
    tasks = [_task("first", []), _task("second", [] if independent else ["first"])]
    document = {
        "schema_version": 1,
        "plan_id": "fixture-dag",
        "base_revision": "0" * 40,
        "tasks": tasks,
    }
    plan = root / "plan.md"
    plan.write_text("# Fixture\n\n```yaml aw-plan\n" + yaml.safe_dump(document, sort_keys=False) + "```\n")
    activate_plan(root, plan)


def _handler(params: dict) -> int:
    (Path(params["repo"]) / params["path"]).write_text(params["content"], encoding="utf-8")
    return 0


def _execute(root: Path, task_id: str):
    def verify(result, repo: Path) -> list[dict]:
        content = (repo / f"{task_id}.txt").read_text(encoding="utf-8")
        return [{"kind": "implementation_deliverable", "ok": content == f"ok-{task_id}\n"}]

    return run_verified(
        "implement_api",
        {"repo": str(root), "path": f"{task_id}.txt", "content": f"ok-{task_id}\n"},
        repo=root,
        phase="IMPLEMENT",
        skill="role-back",
        target=str(root),
        plan_id="fixture-dag",
        task_id=task_id,
        artifacts=[f"{task_id}.txt"],
        verifier=verify,
    )


def test_completion_unlocks_dependent_and_replays_without_double_advance(tmp_path: Path) -> None:
    register_handler("implement_api", _handler)
    _activate(tmp_path)
    assert [t["id"] for t in ready_tasks(tmp_path)] == ["first"]
    start_task(tmp_path, "first")
    with pytest.raises(ValueError, match="dependencies"):
        start_task(tmp_path, "second")
    executed = _execute(tmp_path, "first")
    completed = complete_task(tmp_path, "first", run_id=executed.run_id, target=str(tmp_path))
    revision = completed["state_revision"]
    assert completed["tasks"]["first"]["state"] == "succeeded"
    assert [t["id"] for t in ready_tasks(tmp_path)] == ["second"]
    replay = complete_task(tmp_path, "first", run_id=executed.run_id, target=str(tmp_path))
    assert replay["_idempotent_replay"] is True
    assert replay["state_revision"] == revision


def test_failure_blocks_dependents_and_retry_is_explicit(tmp_path: Path) -> None:
    _activate(tmp_path)
    start_task(tmp_path, "first")
    failed = fail_task(tmp_path, "first", detail="fixture failure")
    assert failed["tasks"]["first"]["state"] == "failed"
    assert ready_tasks(tmp_path) == []
    retried = retry_task(tmp_path, "first")
    assert retried["tasks"]["first"]["state"] == "ready"
    started = start_task(tmp_path, "first")
    assert started["tasks"]["first"]["attempts"] == 2  # noqa: PLR2004  # retry then restart


def test_evidence_from_another_task_cannot_complete(tmp_path: Path) -> None:
    register_handler("implement_api", _handler)
    _activate(tmp_path)
    start_task(tmp_path, "first")
    executed = _execute(tmp_path, "first")
    with pytest.raises(ValueError, match="task_id mismatch"):
        complete_task(tmp_path, "second", run_id=executed.run_id, target=str(tmp_path))


def test_concurrent_independent_completion_has_no_lost_update(tmp_path: Path) -> None:
    register_handler("implement_api", _handler)
    _activate(tmp_path, independent=True)
    # Isolate the status-lock assertion from intentional content invalidation:
    # both idempotent fixture handlers observe the same final workspace bytes.
    for task_id in ("first", "second"):
        (tmp_path / f"{task_id}.txt").write_text(f"ok-{task_id}\n", encoding="utf-8")
    executions = [_execute(tmp_path, "first"), _execute(tmp_path, "second")]
    start_task(tmp_path, "first")
    start_task(tmp_path, "second")
    barrier = threading.Barrier(2)
    revisions: list[int] = []
    errors: list[str] = []

    def complete(task_id: str, run_id: str) -> None:
        barrier.wait()
        try:
            result = complete_task(tmp_path, task_id, run_id=run_id, target=str(tmp_path))
            revisions.append(result["state_revision"])
        except Exception as exc:
            errors.append(str(exc))

    threads = [
        threading.Thread(target=complete, args=("first", executions[0].run_id)),
        threading.Thread(target=complete, args=("second", executions[1].run_id)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert not errors, errors
    assert sorted(revisions) == [4, 5]
