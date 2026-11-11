"""Cursor headless discovery, policy checks and SubagentAdapter."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from execution.ops import OpResult  # noqa: E402
from execution.registry import get_operation  # noqa: E402
from orchestrator.model import RunContext  # noqa: E402
from orchestrator.ports import AdapterResult  # noqa: E402

from harness.base import Check, build_report, report_exit_code  # noqa: E402
from harness.policy import assert_argv_policy, build_policy  # noqa: E402
from harness.subprocess_run import run_cancellable_subprocess  # noqa: E402

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


def static_install_check(target: Path, expected_skills: set[str]) -> Check:  # noqa: PLR0911
    """Level A: filesystem presence after install (not native discovery)."""
    cursor = target.resolve() / ".cursor"
    if not cursor.is_dir():
        return Check("cursor-static-install", "A", "fail", ".cursor missing")
    skills_dir = cursor / "skills"
    if not skills_dir.is_dir():
        return Check("cursor-static-install", "A", "fail", "skills directory missing")
    found = {path.name for path in skills_dir.iterdir() if path.is_dir() or path.is_symlink()}
    missing = sorted(expected_skills - found)
    if missing:
        return Check("cursor-static-install", "A", "fail", f"missing skills: {missing}")
    rules = cursor / "rules" / "machineroom.mdc"
    agents = list((cursor / "agents").glob("*.md")) if (cursor / "agents").is_dir() else []
    hooks = cursor / "hooks.json"
    hook_scripts = list((cursor / "hooks").glob("*.py")) if (cursor / "hooks").is_dir() else []
    if not rules.is_file() and not rules.is_symlink():
        return Check("cursor-static-install", "A", "fail", "rules/machineroom.mdc missing")
    if not agents:
        return Check("cursor-static-install", "A", "fail", "no agents discovered")
    if not hooks.is_file() and not hooks.is_symlink():
        return Check("cursor-static-install", "A", "fail", "hooks.json missing")
    if not hook_scripts:
        return Check("cursor-static-install", "A", "fail", "hook scripts missing")
    agent_names = {path.name for path in agents}
    if "mr-verifier.md" not in agent_names:
        return Check("cursor-static-install", "A", "fail", "mr-verifier.md missing")
    detail = f"skills={len(found)} agents={sorted(agent_names)} hooks={len(hook_scripts)} rules=machineroom.mdc"
    return Check("cursor-static-install", "A", "pass", detail)


def cursor_discovery_check(target: Path, expected_skills: set[str]) -> Check:
    """Level B: Cursor CLI must load hooks (sessionStart) — filesystem alone is not enough."""
    binary = resolve_agent_binary()
    if not binary:
        return Check("cursor-native-discovery", "B", "not_run", "agent binary missing")
    static = static_install_check(target, expected_skills)
    if static.outcome != "pass":
        return Check("cursor-native-discovery", "B", "fail", f"static precheck failed: {static.detail}")
    root = target.resolve()
    marker = root / ".machineroom-cursor-session-marker"
    marker.unlink(missing_ok=True)
    hooks_json = root / ".cursor" / "hooks.json"
    if not hooks_json.exists():
        return Check("cursor-native-discovery", "B", "fail", "hooks.json missing")
    original_hooks = hooks_json.read_text(encoding="utf-8")
    probe = root / ".machineroom-session-probe.py"
    original_session = root / ".cursor" / "hooks" / "session_start.py"
    probe.write_text(
        "#!/usr/bin/env python3\n"
        "from __future__ import annotations\n"
        "import json, runpy, sys\n"
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('session-start-ok\\n', encoding='utf-8')\n"
        f"sys.path.insert(0, str(Path({str(original_session.parent)!r})))\n"
        f"runpy.run_path({str(original_session)!r}, run_name='__main__')\n",
        encoding="utf-8",
    )
    probe.chmod(probe.stat().st_mode | 0o100)
    payload = json.loads(original_hooks)
    payload.setdefault("hooks", {})["sessionStart"] = [{"command": f"python3 {probe}"}]
    # Replace possibly-symlinked hooks.json with a real file Cursor will load.
    if hooks_json.is_symlink() or not hooks_json.is_file():
        hooks_json.unlink()
    hooks_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    try:
        result = subprocess.run(
            [
                binary,
                "--print",
                "--mode",
                "ask",
                "--trust",
                "--workspace",
                str(root),
                "Reply with exactly: PONG",
            ],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return Check("cursor-native-discovery", "B", "fail", f"agent invocation failed: {exc}")
    finally:
        if hooks_json.exists() or hooks_json.is_symlink():
            hooks_json.unlink()
        hooks_json.write_text(original_hooks, encoding="utf-8")
        probe.unlink(missing_ok=True)
    if not marker.is_file():
        return Check(
            "cursor-native-discovery",
            "B",
            "fail",
            "sessionStart marker missing after agent run (static paths alone are insufficient); "
            f"agent_exit={result.returncode} stderr={(result.stderr or '')[:200]}",
        )
    detail = f"sessionStart observed via Cursor; agent_exit={result.returncode}"
    return Check("cursor-native-discovery", "B", "pass", detail)


def _policy_probe_source(decisions: Path) -> str:
    return (
        "#!/usr/bin/env python3\n"
        "from __future__ import annotations\n"
        "import json, sys\n"
        "from pathlib import Path\n"
        f"DECISIONS = Path({str(decisions)!r})\n"
        "payload = json.load(sys.stdin)\n"
        "cmd = str(payload.get('command') or '')\n"
        "if 'MR_POLICY_DENY' in cmd:\n"
        "    permission = 'deny'\n"
        "elif 'MR_POLICY_ASK' in cmd:\n"
        "    permission = 'ask'\n"
        "elif 'MR_POLICY_ALLOW' in cmd:\n"
        "    permission = 'allow'\n"
        "else:\n"
        "    permission = 'allow'\n"
        "record = {'command': cmd, 'permission': permission, 'hook_event_name': payload.get('hook_event_name')}\n"
        "with DECISIONS.open('a', encoding='utf-8') as fh:\n"
        "    fh.write(json.dumps(record, sort_keys=True) + '\\n')\n"
        "out = {'permission': permission}\n"
        "if permission != 'allow':\n"
        "    out['user_message'] = f'policy probe {permission}'\n"
        "    out['agent_message'] = f'policy probe returned {permission}'\n"
        "print(json.dumps(out))\n"
    )


def _install_policy_probe(
    root: Path,
    *,
    original_hooks: str,
    probe: Path,
    decisions: Path,
) -> None:
    probe.write_text(_policy_probe_source(decisions), encoding="utf-8")
    probe.chmod(probe.stat().st_mode | 0o100)
    payload = json.loads(original_hooks)
    payload.setdefault("hooks", {})["beforeShellExecution"] = [
        {"command": f"python3 {probe}", "failClosed": True, "timeout": 10}
    ]
    hooks_json = root / ".cursor" / "hooks.json"
    if hooks_json.is_symlink() or not hooks_json.is_file():
        hooks_json.unlink()
    hooks_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _restore_policy_hooks(hooks_json: Path, original_hooks: str, probe: Path) -> None:
    if hooks_json.exists() or hooks_json.is_symlink():
        hooks_json.unlink()
    hooks_json.write_text(original_hooks, encoding="utf-8")
    probe.unlink(missing_ok=True)


def _run_policy_agent(binary: str, root: Path) -> subprocess.CompletedProcess[str]:
    prompt = (
        "You MUST use the Shell tool exactly three times in this workspace. Do not skip any.\n"
        "1) Run exactly: echo MR_POLICY_ALLOW > .machineroom-policy-allow.txt\n"
        "2) Run exactly: echo MR_POLICY_DENY > .machineroom-policy-deny.txt\n"
        "3) Run exactly: echo MR_POLICY_ASK > .machineroom-policy-ask.txt\n"
        "After attempting all three, reply with exactly: POLICY_DONE\n"
    )
    argv = [
        binary,
        "--print",
        "--output-format",
        "text",
        "--trust",
        "--sandbox",
        "enabled",
        "--workspace",
        str(root),
        prompt,
    ]
    assert_argv_policy(argv)
    return subprocess.run(
        argv,
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


def _assert_policy_outcomes(  # noqa: PLR0913  # outcome paths + agent_exit for receipt
    *,
    decisions: Path,
    allow_effect: Path,
    deny_effect: Path,
    ask_effect: Path,
    agent_exit: int,
    policy_root: Path,
) -> Check:
    if not decisions.is_file():
        return Check(
            "cursor-native-policy",
            "C",
            "fail",
            f"beforeShellExecution decisions missing — Cursor did not invoke the policy probe; agent_exit={agent_exit}",
        )
    seen: dict[str, str] = {}
    for line in decisions.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        permission = str(row.get("permission") or "")
        command = str(row.get("command") or "")
        for token in ("ALLOW", "DENY", "ASK"):
            if f"MR_POLICY_{token}" in command:
                seen[token.lower()] = permission
    expected = {"allow": "allow", "deny": "deny", "ask": "ask"}
    if seen != expected:
        return Check(
            "cursor-native-policy",
            "C",
            "fail",
            f"hook decisions incomplete or wrong: {seen!r}; agent_exit={agent_exit}",
        )
    if not allow_effect.is_file():
        return Check("cursor-native-policy", "C", "fail", "allow permission did not produce shell side effect")
    if deny_effect.is_file():
        return Check("cursor-native-policy", "C", "fail", "deny permission still produced a side effect")
    if ask_effect.is_file():
        return Check(
            "cursor-native-policy",
            "C",
            "fail",
            "ask permission produced a side effect in headless mode (expected blocked pending approval)",
        )
    receipt = {
        "decisions": seen,
        "allow_effect": allow_effect.read_text(encoding="utf-8").strip(),
        "agent_exit": agent_exit,
        "force_flags": False,
    }
    (policy_root / "policy-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return Check(
        "cursor-native-policy",
        "C",
        "pass",
        "beforeShellExecution allow/deny/ask observed via Cursor without --force/--yolo; "
        f"allow_effect={allow_effect.name}",
    )


def policy_check(target: Path, work_dir: Path | None = None) -> Check:
    """Level C: Cursor must invoke beforeShellExecution; observe allow/deny/ask without --force/--yolo.

    The harness never calls shell_gate.py / the probe directly for proof, and never
    writes the allow/deny/ask effect files itself.
    """
    binary = resolve_agent_binary()
    if not binary:
        return Check("cursor-native-policy", "C", "not_run", "agent binary missing")
    if not agent_authenticated(binary):
        return Check(
            "cursor-native-policy",
            "C",
            "not_run",
            "agent authentication required for headless policy probe",
        )
    root = target.resolve()
    policy_root = (work_dir or (root / ".machineroom-cursor-policy")).resolve()
    policy_root.mkdir(parents=True, exist_ok=True)
    hooks_json = root / ".cursor" / "hooks.json"
    hooks_dir = root / ".cursor" / "hooks"
    if not hooks_json.exists():
        return Check("cursor-native-policy", "C", "fail", "hooks.json missing before policy probe")
    hooks_dir.mkdir(parents=True, exist_ok=True)
    original_hooks = hooks_json.read_text(encoding="utf-8")
    probe = hooks_dir / "mr_policy_probe.py"
    decisions = root / ".machineroom-policy-decisions.jsonl"
    allow_effect = root / ".machineroom-policy-allow.txt"
    deny_effect = root / ".machineroom-policy-deny.txt"
    ask_effect = root / ".machineroom-policy-ask.txt"
    for path in (decisions, allow_effect, deny_effect, ask_effect):
        path.unlink(missing_ok=True)
    _install_policy_probe(root, original_hooks=original_hooks, probe=probe, decisions=decisions)
    try:
        result = _run_policy_agent(binary, root)
    except ValueError as exc:
        return Check("cursor-native-policy", "C", "fail", f"forbidden argv for policy probe: {exc}")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return Check("cursor-native-policy", "C", "fail", f"agent policy probe failed: {exc}")
    finally:
        _restore_policy_hooks(hooks_json, original_hooks, probe)

    return _assert_policy_outcomes(
        decisions=decisions,
        allow_effect=allow_effect,
        deny_effect=deny_effect,
        ask_effect=ask_effect,
        agent_exit=result.returncode,
        policy_root=policy_root,
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
    checks.append(static_install_check(target, expected_skills))
    if not binary or not version:
        checks.append(Check("cursor-cli-version", "B", "blocked", "agent binary missing from PATH"))
        checks.append(Check("cursor-native-discovery", "B", "not_run", "agent unavailable"))
        checks.append(Check("cursor-native-policy", "C", "not_run", "agent unavailable"))
        return checks
    checks.append(Check("cursor-cli-version", "B", "pass", f"{binary} → {version}"))
    checks.append(cursor_discovery_check(target, expected_skills))
    policy_dir = work_dir or (target.resolve() / ".machineroom-cursor-policy")
    checks.append(policy_check(target, work_dir=policy_dir))
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
        credential_names: tuple[str, ...] = (),
    ) -> None:
        if force:
            raise ValueError("auto-approval (--force/--yolo) is forbidden for Cursor acceptance")
        self.binary = binary or resolve_agent_binary() or "agent"
        self.model = model
        self.timeout = timeout
        self.credential_names = credential_names

    def execute(self, task: dict[str, Any], context: RunContext) -> AdapterResult:
        started = time.monotonic()
        run_id = str(uuid.uuid4())
        operation = get_operation(str(task["operation"]))
        packet = json.dumps(
            {"task": task, "plan_id": context.plan_id, "run_id": context.run_id},
            sort_keys=True,
        )
        plan_digest = hashlib.sha256(packet.encode("utf-8")).hexdigest()
        policy = build_policy(
            harness="cursor",
            task=task,
            timeout_s=self.timeout,
            credential_names=self.credential_names,
        )
        role = (task.get("roles") or ["role-back"])[0]
        agent_name = {
            "plan-specification": "mr-planner",
            "plan-validators": "mr-verifier",
        }.get(operation.skill, "mr-worker")
        if operation.skill == "plan-validators" or role == "mr-verifier":
            agent_name = "mr-verifier"
        write = bool(policy.write_scope)
        prompt = (
            f"You are the {agent_name} subagent. Use skill {operation.skill}. "
            f"Execute exactly this task packet and stop:\n{packet}\n"
        )
        if write:
            paths = ", ".join(policy.write_scope)
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
            "--sandbox",
            "enabled",
        ]
        if self.model:
            argv.extend(["--model", self.model])
        if not write:
            argv.extend(["--mode", "ask"])
        argv.append(prompt)
        assert_argv_policy(argv)
        run = run_cancellable_subprocess(
            argv,
            cwd=str(context.repo),
            env=policy.env_mapping(),
            timeout=self.timeout,
            cancel_event=context.cancel_event,
        )
        if run.timed_out:
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
        combined = f"{run.stdout}\n{run.stderr}"
        if run.cancelled:
            outcome = "cancelled"
        elif "authentication required" in combined.lower():
            outcome = "blocked"
        elif run.returncode != 0:
            outcome = "failed"
        else:
            outcome = "succeeded"
        detail = (run.stdout or run.stderr or "")[:500]
        operation_result = OpResult(
            operation.operation_id,
            outcome if outcome != "blocked" else "failed",
            run.returncode,
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
