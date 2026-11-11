#!/usr/bin/env python3
"""CLI for active-plan scheduling with Pi or Cursor native adapters."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

WORKSPACE_ROUTER = TOOLS / "workspace-router"
if str(WORKSPACE_ROUTER) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROUTER))

from contracts.plan import load_plan  # noqa: E402
from harness.cursor import CursorSubagentAdapter  # noqa: E402
from harness.pi import PiSubagentAdapter  # noqa: E402
from status_bump import activate_plan, load_status  # noqa: E402

from orchestrator.ports import SubagentAdapter  # noqa: E402
from orchestrator.runner import Verifier, WorktreeAdapter  # noqa: E402
from orchestrator.scheduler import Scheduler  # noqa: E402
from orchestrator.verifiers import resolve as resolve_verifier  # noqa: E402


def _default_verifier(task: Mapping[str, Any]) -> Verifier:
    return resolve_verifier(dict(task))


def _build_adapter(name: str) -> SubagentAdapter:
    if name == "pi":
        model = os.environ.get("MR_PI_MODEL", "kimi-coding/k3.1-pro")
        inner: SubagentAdapter = PiSubagentAdapter(model=model)
    else:
        if os.environ.get("MR_CURSOR_FORCE", "0") == "1":
            raise ValueError("MR_CURSOR_FORCE is forbidden; auto-approval cannot produce PASS")
        cursor_model = os.environ.get("MR_CURSOR_MODEL")
        inner = CursorSubagentAdapter(model=cursor_model)
    return inner


def _resolve_plan(repo: Path, plan_path: Path | None, *, dry_run: bool) -> None:
    if plan_path is None:
        status = load_status(repo)
        if not status.get("active_plan"):
            raise ValueError("no active plan; pass --plan PATH")
        return
    document = load_plan(plan_path if plan_path.is_absolute() else (repo / plan_path))
    status = load_status(repo)
    active = status.get("active_plan")
    relative = (
        plan_path.resolve().relative_to(repo.resolve()).as_posix()
        if plan_path.is_absolute()
        else Path(plan_path).as_posix()
    )
    if dry_run:
        # Validate only; do not write status.
        _ = document
        return
    if active:
        if active.get("path") == relative and active.get("digest") == document.digest:
            return
        raise ValueError(
            "active plan conflict: pass an explicit reset before switching plans "
            f"(active={active.get('path')} digest={active.get('digest')})"
        )
    activate_plan(repo, plan_path if plan_path.is_absolute() else (repo / plan_path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Machineroom DAG orchestrator")
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument(
        "--plan", type=Path, help="Plan document with aw-plan block (validated; activates when not dry-run)"
    )
    parser.add_argument("--adapter", choices=("pi", "cursor"), required=True)
    parser.add_argument("--max-parallel", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true", default=True)
    parser.add_argument("--no-worktree", action="store_true", help="Call the harness adapter without WorktreeAdapter")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    try:
        _resolve_plan(repo, args.plan, dry_run=args.dry_run)
        if args.dry_run and args.plan is not None:
            document = load_plan(args.plan if args.plan.is_absolute() else (repo / args.plan))
            from orchestrator.scheduler import plan_schedule  # noqa: PLC0415

            waves = plan_schedule(document)
            payload = {
                "outcome": "simulated",
                "plan_id": document.plan_id,
                "digest": document.digest,
                "waves": waves,
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "simulated")
            return 0
        inner = _build_adapter(args.adapter)
        adapter: SubagentAdapter = (
            inner if args.dry_run or args.no_worktree else WorktreeAdapter(repo, inner, _default_verifier)
        )
        scheduler = Scheduler(
            repo,
            adapter=adapter,
            max_parallel=args.max_parallel,
            resume=args.resume,
        )
        if args.dry_run:
            summary = scheduler.dry_run()
            print(json.dumps(summary.as_dict(), ensure_ascii=False, indent=2) if args.json else "simulated")
            return 0
        summary = scheduler.run()
        payload = summary.as_dict()
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else payload.get("outcome"))
        if summary.outcome == "pass":
            return 0
        if summary.outcome in {"blocked", "not_run"}:
            return 3
        return 1
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
