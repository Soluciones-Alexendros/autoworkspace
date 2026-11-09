"""Pi subagent process behavior with an isolated fake executable."""

from __future__ import annotations

import os
import stat
import sys
import threading
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness.pi import PiSubagentAdapter  # noqa: E402
from orchestrator.model import RunContext  # noqa: E402
from orchestrator.ports import AdapterResult  # noqa: E402


def _binary(tmp_path: Path, behavior: str) -> Path:
    path = tmp_path / "pi-fixture"
    body = """import json, sys, time
behavior = "__BEHAVIOR__"
args = sys.argv[1:]
if behavior == 'args':
    print(json.dumps({'args': args}))
elif behavior == 'invalid':
    print('not-json')
elif behavior in {'timeout', 'cancel'}:
    time.sleep(10)
else:
    stop = 'error' if behavior == 'error' else 'stop'
    print(json.dumps({'type': 'message_end', 'message': {'role': 'assistant', 'content': [{'type': 'text', 'text': behavior}], 'stopReason': stop}}))
""".replace("__BEHAVIOR__", behavior)
    path.write_text("#!/usr/bin/env python3\n" + body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def _context(tmp_path: Path) -> RunContext:
    return RunContext(tmp_path, "fixture-plan", "a" * 64, "0" * 40, "run-fixture", "pi")


def _task(write: bool = True) -> dict[str, Any]:
    return {
        "id": "fixture-task",
        "phase": "IMPLEMENT",
        "operation": "implement_api",
        "roles": ["role-back"],
        "write_scope": ["out.txt"] if write else [],
    }


def _execute(tmp_path: Path, behavior: str, **kwargs: Any) -> AdapterResult:
    adapter = PiSubagentAdapter(binary=str(_binary(tmp_path, behavior)), **kwargs)
    return adapter.execute(_task(), _context(tmp_path))


def test_subagent_success_returns_actual_operation_result(tmp_path: Path) -> None:
    result = _execute(tmp_path, "success")
    assert result.outcome == "succeeded"
    assert result.operation_result is not None
    assert result.operation_result.operation_id == "implement_api"
    assert result.operation_result.run_id


def test_model_error_is_failed(tmp_path: Path) -> None:
    result = _execute(tmp_path, "error")
    assert result.outcome == "failed"
    assert "error" in result.detail


def test_invalid_json_is_failed(tmp_path: Path) -> None:
    result = _execute(tmp_path, "invalid")
    assert result.outcome == "failed"


def test_timeout_kills_process_and_requires_reconciliation(tmp_path: Path) -> None:
    started = time.monotonic()
    result = _execute(tmp_path, "timeout", timeout=1)
    assert result.outcome == "cancelled"
    assert "reconciliation" in result.detail
    assert time.monotonic() - started < 4


def test_cancellation_kills_process_group(tmp_path: Path) -> None:
    adapter = PiSubagentAdapter(binary=str(_binary(tmp_path, "cancel")), timeout=30)
    context = _context(tmp_path)
    timer = threading.Timer(0.2, context.cancel_event.set)
    timer.start()
    started = time.monotonic()
    result = adapter.execute(_task(), context)
    timer.join()
    assert result.outcome == "cancelled"
    assert time.monotonic() - started < 4
