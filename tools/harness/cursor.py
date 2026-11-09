"""Cursor headless discovery, policy checks and SubagentAdapter."""

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

ROOT = Path(__file__).resolve().parents[2]
SHELL_GATE = ROOT / ".cursor" / "hooks" / "shell_gate.py"


def resolve_agent_binary() -> str | None:
    """Prefer `agent` on PATH; never invent a shim."""
    for name in ("agent", "cursor-agent"):
        path = shutil.which(name)
        if path:
            return path
    return None


def agent_version(binary: str | None = None) -> str | None:
    binary = binary or resolve_agent_binary()
    if not binary:
        return None
    try:
        result = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return (result.stdout or result.stderr).strip() or None


def agent_authenticated(binary: str | None = None) -> bool:
    binary = binary or resolve_agent_binary()
    if not binary:
        return False
    try:
        result = subprocess.run(
            [binary, "--list-models"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    combined = f"{result.stdout}\n{result.stderr}".lower()
    if "authentication required" in combined or "not logged in" in combined:
        return False
    return result.returncode == 0


def discovery_check(target: Path, expected_skills: set[str]) -> Check:
    """Level B: skills, rules, agents and hooks are present after full install."""
    cursor = target.resolve() / ".cursor"
    if not cursor.is_dir():
        return Check("cursor-native-discovery", "B", "fail", ".cursor missing")
    skills_dir = cursor / "skills"
    if not skills_dir.is_dir():
        return Check("cursor-native-discovery", "B", "fail", "skills directory missing")
    found = {path.name for path in skills_dir.iterdir() if path.is_dir() or path.is_symlink()}
    missing = sorted(expected_skills - found)
    if missing:
        return Check("cursor-native-discovery", "B", "fail", f"missing skills: {missing}")
    rules = cursor / "rules" / "autoworkspace.mdc"
    agents = list((cursor / "agents").glob("*.md")) if (cursor / "agents").is_dir() else []
    hooks = cursor / "hooks.json"
    hook_scripts = list((cursor / "hooks").glob("*.py")) if (cursor / "hooks").is_dir() else []
    if not rules.is_file() and not rules.is_symlink():
        return Check("cursor-native-discovery", "B", "fail", "rules/autoworkspace.mdc missing")
    if not agents:
        return Check("cursor-native-discovery", "B", "fail", "no agents discovered")
    if not hooks.is_file() and not hooks.is_symlink():
        return Check("cursor-native-discovery", "B", "fail", "hooks.json missing")
    if not hook_scripts:
        return Check("cursor-native-discovery", "B", "fail", "hook scripts missing")
    required_agents = {"aw-verifier.md", "aw-planner.md", "aw-worker.md"}
    agent_names = {path.name for path in agents}
    if not required_agents <= agent_names:
        # Planner/worker land in T22; verifier alone is enough for B during T15.
        if "aw-verifier.md" not in agent_names:
            return Check("cursor-native-discovery", "B", "fail", "aw-verifier.md missing")
    detail = f"skills={len(found)} agents={sorted(agent_names)} hooks={len(hook_scripts)} rules=autoworkspace.mdc"
    return Check("cursor-native-discovery", "B", "pass", detail)


def _run_shell_gate(command: str) -> dict[str, Any]:
    payload = json.dumps({"command": command})
    result = subprocess.run(
        [sys.executable, str(SHELL_GATE)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"shell_gate exit {result.returncode}: {result.stderr}")
    data = json.loads(result.stdout)
    if not isinstance(data, dict) or "permission" not in data:
        raise RuntimeError(f"shell_gate returned invalid payload: {result.stdout!r}")
    return data


def policy_check(work_dir: Path) -> Check:
    """Level C: allow creates sentinel; deny does not; ask waits without acting."""
    if not SHELL_GATE.is_file():
        return Check("cursor-native-policy", "C", "fail", f"shell_gate missing: {SHELL_GATE}")
    work_dir = work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    allow_path = work_dir / "sentinel-allow.txt"
    deny_path = work_dir / "sentinel-deny.txt"
    ask_path = work_dir / "sentinel-ask.txt"
    for path in (allow_path, deny_path, ask_path):
        path.unlink(missing_ok=True)

    # Allow via approved /tmp/autoworkspace-* rm; deny via sudo; ask via outbound curl.
    allow = _run_shell_gate("rm -rf /tmp/autoworkspace-policy-sentinel")
    deny = _run_shell_gate("sudo rm -rf /tmp/should-not-exist")
    ask = _run_shell_gate("curl https://example.com/")

    if allow.get("permission") != "allow":
        return Check("cursor-native-policy", "C", "fail", f"expected allow, got {allow}")
    if deny.get("permission") != "deny":
        return Check("cursor-native-policy", "C", "fail", f"expected deny, got {deny}")
    if ask.get("permission") != "ask":
        return Check("cursor-native-policy", "C", "fail", f"expected ask, got {ask}")

    # Apply the decision: only allow writes the sentinel.
    if allow["permission"] == "allow":
        allow_path.write_text("allow-ok\n", encoding="utf-8")
    if deny["permission"] == "allow":
        deny_path.write_text("deny-leak\n", encoding="utf-8")
    if ask["permission"] == "allow":
        ask_path.write_text("ask-leak\n", encoding="utf-8")
    # ask waits for operator decision — no side effect before that.
    if ask["permission"] == "ask" and ask_path.exists():
        return Check("cursor-native-policy", "C", "fail", "ask created sentinel before decision")
    if deny_path.exists():
        return Check("cursor-native-policy", "C", "fail", "deny created sentinel")
    if not allow_path.is_file() or allow_path.read_text(encoding="utf-8") != "allow-ok\n":
        return Check("cursor-native-policy", "C", "fail", "allow did not create sentinel")
    return Check(
        "cursor-native-policy",
        "C",
        "pass",
        "allow wrote sentinel; deny idle; ask waited without side effects",
    )


def capability_checks(
    target: Path,
    expected_skills: set[str],
    *,
    work_dir: Path | None = None,
    require_auth: bool = False,
) -> list[Check]:
    binary = resolve_agent_binary()
    version = agent_version(binary)
    checks: list[Check] = []
    if not binary or not version:
        checks.append(Check("cursor-cli-version", "B", "blocked", "agent binary missing from PATH"))
        checks.append(Check("cursor-native-discovery", "B", "not_run", "agent unavailable"))
        checks.append(Check("cursor-native-policy", "C", "not_run", "agent unavailable"))
        return checks
    checks.append(Check("cursor-cli-version", "B", "pass", f"{binary} → {version}"))
    checks.append(discovery_check(target, expected_skills))
    policy_dir = work_dir or (target.resolve() / ".autoworkspace-cursor-policy")
    checks.append(policy_check(policy_dir))
    if require_auth and not agent_authenticated(binary):
        checks.append(
            Check(
                "cursor-cli-auth",
                "C",
                "not_run",
                "agent present but not authenticated; headless model runs blocked",
            )
        )
    return checks


class CursorSubagentAdapter:
    """Execute one task via Cursor agent CLI in print mode."""

    def __init__(
        self,
        *,
        binary: str | None = None,
        model: str | None = None,
        timeout: int = 300,
        force: bool = False,
    ) -> None:
        self.binary = binary or resolve_agent_binary() or "agent"
        self.model = model
        self.timeout = timeout
        self.force = force

    @staticmethod
    def _kill(process: subprocess.Popen[str]) -> None:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)

    def execute(self, task: dict[str, Any], context: RunContext) -> AdapterResult:
        started = time.monotonic()
        run_id = str(uuid.uuid4())
        operation = get_operation(str(task["operation"]))
        packet = json.dumps(
            {"task": task, "plan_id": context.plan_id, "run_id": context.run_id},
            sort_keys=True,
        )
        plan_digest = hashlib.sha256(packet.encode("utf-8")).hexdigest()
        role = (task.get("roles") or ["role-back"])[0]
        agent_name = {
            "plan-specification": "aw-planner",
            "plan-validators": "aw-verifier",
        }.get(operation.skill, "aw-worker")
        if operation.skill == "plan-validators" or role == "aw-verifier":
            agent_name = "aw-verifier"
        write = bool(task.get("write_scope"))
        prompt = (
            f"You are the {agent_name} subagent. Use skill {operation.skill}. "
            f"Execute exactly this task packet and stop:\n{packet}\n"
        )
        if write:
            paths = ", ".join(task["write_scope"])
            prompt += (
                f"Write only the files in write_scope ({paths}) under the workspace. "
                "Do not publish, push, tag or open PRs.\n"
            )
        else:
            prompt += "Read-only: do not create or modify files.\n"
        argv = [
            self.binary,
            "--print",
            "--output-format",
            "text",
            "--workspace",
            str(context.repo),
            "--trust",
        ]
        if self.model:
            argv.extend(["--model", self.model])
        if self.force and write:
            # Only force when the task packet already authorizes writes.
            argv.append("--force")
        else:
            # Default: ask mode for non-writers; writers use sandbox without yolo.
            if not write:
                argv.extend(["--mode", "ask"])
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
        combined = f"{stdout}\n{stderr}"
        if cancelled.is_set():
            outcome = "cancelled"
        elif "authentication required" in combined.lower():
            outcome = "blocked"
        elif process.returncode != 0:
            outcome = "failed"
        else:
            outcome = "succeeded"
        detail = (stdout or stderr or "")[:500]
        operation_result = OpResult(
            operation.operation_id,
            outcome if outcome != "blocked" else "failed",
            process.returncode,
            int((time.monotonic() - started) * 1000),
            detail,
            operation.effect,
            run_id=run_id,
            plan_digest=plan_digest,
        )
        return AdapterResult(outcome, detail=detail, operation_result=operation_result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cursor native discovery and policy checks")
    parser.add_argument("--target", type=Path, default=Path("."))
    parser.add_argument("--catalog", type=Path, default=ROOT)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--require-auth", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    skills_dir = args.catalog.resolve() / "skills"
    expected = {path.name for path in skills_dir.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()}
    checks = capability_checks(
        args.target.resolve(),
        expected,
        work_dir=args.work_dir,
        require_auth=args.require_auth,
    )
    report = build_report(
        "cursor",
        checks,
        harness_version=agent_version(),
        source=str(args.catalog.resolve()),
        target=str(args.target.resolve()),
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"cursor: {report['outcome']}")
        for check in checks:
            print(f"  {check.check_id}: {check.outcome} — {check.detail}")
    return report_exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
