"""Native Pi package discovery through the model-free RPC get_commands API."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any

TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from execution.ops import OpResult  # noqa: E402
from execution.registry import get_operation  # noqa: E402
from harness.base import Check, build_report, report_exit_code  # noqa: E402
from orchestrator.model import RunContext  # noqa: E402
from orchestrator.ports import AdapterResult  # noqa: E402


def response_commands(response: dict[str, Any]) -> list[dict[str, Any]]:
    if response.get("type") != "response" or response.get("command") != "get_commands" or response.get("success") is not True:
        raise ValueError("Pi get_commands response missing or unsuccessful")
    commands = response.get("data", {}).get("commands")
    if not isinstance(commands, list):
        raise ValueError("Pi get_commands commands must be a list")
    return [command for command in commands if isinstance(command, dict)]


def skill_commands(response: dict[str, Any]) -> list[dict[str, Any]]:
    return [command for command in response_commands(response) if command.get("source") == "skill"]


def rpc_commands(cwd: Path, *, timeout: int = 20, env: dict[str, str] | None = None) -> list[dict[str, Any]]:
    process = subprocess.Popen(
        ["pi", "--mode", "rpc", "--no-session"],
        cwd=str(cwd),
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(json.dumps({"id": "aw-skills", "type": "get_commands"}) + "\n", timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)
        raise ValueError(f"Pi RPC timeout after {timeout}s") from None
    if process.returncode != 0:
        raise ValueError(f"Pi RPC exited {process.returncode}: {stderr[:500]}")
    responses = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            responses.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError("Pi RPC returned invalid JSONL") from exc
    for response in responses:
        if isinstance(response, dict) and response.get("command") == "get_commands":
            return response_commands(response)
    raise ValueError("Pi RPC did not return get_commands")


def discovery_check(cwd: Path, expected_skills: set[str], *, require_package: bool = True) -> Check:
    if shutil.which("pi") is None:
        return Check("pi-native-discovery", "B", "not_run", "Pi binary not found")
    try:
        commands = rpc_commands(cwd)
    except (OSError, ValueError) as exc:
        return Check("pi-native-discovery", "B", "fail", str(exc)[:500])
    by_name = {
        str(command.get("name", "")).removeprefix("skill:"): command
        for command in commands
        if str(command.get("name", "")).startswith("skill:")
    }
    missing = sorted(expected_skills - set(by_name))
    if missing:
        return Check("pi-native-discovery", "B", "fail", f"missing skills: {missing}")
    if require_package:
        wrong_origin = sorted(
            name
            for name in expected_skills
            if by_name[name].get("sourceInfo", {}).get("origin") != "package"
        )
        if wrong_origin:
            return Check("pi-native-discovery", "B", "fail", f"skills not loaded from a package: {wrong_origin}")
    return Check("pi-native-discovery", "B", "pass", f"{len(expected_skills)} skills discovered natively")


class PiSubagentAdapter:
    """Execute one task in an isolated Pi JSON-mode subprocess."""

    def __init__(
        self,
        *,
        binary: str = "pi",
        model: str | None = None,
        timeout: int = 300,
    ) -> None:
        self.binary = binary
        self.model = model
        self.timeout = timeout

    @staticmethod
    def _kill(process: subprocess.Popen[str]) -> None:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)

    def execute(self, task: dict[str, Any], context: RunContext) -> AdapterResult:
        started = time.monotonic()
        run_id = str(uuid.uuid4())
        operation = get_operation(str(task["operation"]))
        packet = json.dumps({"task": task, "plan_id": context.plan_id, "run_id": context.run_id}, sort_keys=True)
        plan_digest = hashlib.sha256(packet.encode("utf-8")).hexdigest()
        write = bool(task.get("write_scope"))
        tools = ["read", "grep", "find", "ls"]
        if write:
            tools += ["write", "edit", "bash"]
        prompt = f"/skill:{operation.skill}\n\nExecute exactly this task packet:\n{packet}"
        if write:
            paths = ", ".join(task["write_scope"])
            expected = "\n".join(f"{path} must contain exactly: {task['id']}" for path in task["write_scope"])
            prompt += (
                f"\nWrite only these files under the workspace ({paths}).\n"
                f"{expected}\n"
                "Do not publish, push, tag or open PRs. Stop when the files exist."
            )
        argv = [
            self.binary,
            "--mode",
            "json",
            "-p",
            "--no-session",
            "--tools",
            ",".join(tools),
        ]
        if self.model:
            argv.extend(["--model", self.model])
        argv.append(prompt)
        process = subprocess.Popen(
            argv,
            cwd=str(context.repo),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        cancelled = threading.Event()
        watcher_done = threading.Event()

        def watch_cancellation() -> None:
            while not watcher_done.is_set() and process.poll() is None:
                if context.cancel_event.wait(0.05):
                    cancelled.set()
                    self._kill(process)
                    return

        watcher = threading.Thread(target=watch_cancellation)
        watcher.start()
        try:
            stdout, stderr = process.communicate(timeout=self.timeout)
        except subprocess.TimeoutExpired:
            self._kill(process)
            process.wait(timeout=5)
            watcher_done.set()
            watcher.join(timeout=1)
            operation_result = OpResult(
                operation.operation_id,
                "cancelled",
                124,
                int((time.monotonic() - started) * 1000),
                "timeout; process group killed; reconciliation_required before retry",
                operation.effect,
                run_id=run_id,
                plan_digest=plan_digest,
            )
            return AdapterResult("cancelled", detail=operation_result.detail, operation_result=operation_result)
        watcher_done.set()
        watcher.join(timeout=1)
        stop_reason = ""
        final_text = ""
        try:
            for line in stdout.splitlines():
                if not line.strip():
                    continue
                event = json.loads(line)
                if event.get("type") == "message_end":
                    message = event.get("message", {})
                    if message.get("role") == "assistant":
                        stop_reason = str(message.get("stopReason") or stop_reason)
                        content = message.get("content") or []
                        final_text = "".join(
                            str(part.get("text", "")) for part in content if isinstance(part, dict) and part.get("type") == "text"
                        )
        except (json.JSONDecodeError, AttributeError) as exc:
            stop_reason = "error"
            final_text = f"invalid Pi JSONL: {exc}"
        if cancelled.is_set():
            outcome = "cancelled"
        elif process.returncode != 0 or stop_reason in {"error", "aborted"}:
            outcome = "failed"
        else:
            outcome = "succeeded"
        detail = (final_text or stderr or "")[:500]
        operation_result = OpResult(
            operation.operation_id,
            outcome,
            process.returncode,
            int((time.monotonic() - started) * 1000),
            detail,
            operation.effect,
            run_id=run_id,
            plan_digest=plan_digest,
        )
        return AdapterResult(outcome, detail=detail, operation_result=operation_result)


def _version() -> str | None:
    if shutil.which("pi") is None:
        return None
    try:
        result = subprocess.run(["pi", "--version"], capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pi native package discovery check")
    parser.add_argument("--cwd", type=Path, default=Path("."))
    parser.add_argument("--catalog", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--allow-top-level", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    skills_dir = args.catalog.resolve() / "skills"
    expected = {path.name for path in skills_dir.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()}
    check = discovery_check(args.cwd.resolve(), expected, require_package=not args.allow_top_level)
    report = build_report(
        "pi",
        [check],
        harness_version=_version(),
        source=str(args.catalog.resolve()),
        target=str(args.cwd.resolve()),
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"pi: {report['outcome']}: {check.detail}")
    return report_exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
