#!/usr/bin/env python3
"""CLI for active-plan scheduling with Pi or Cursor native adapters."""

from __future__ import annotations

from typing import Any, cast

import argparse
import json
import os
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from execution.ops import OpResult  # noqa: E402
from execution.registry import get_operation  # noqa: E402
from harness.cursor import CursorSubagentAdapter  # noqa: E402
from harness.pi import PiSubagentAdapter  # noqa: E402
from orchestrator.ports import SubagentAdapter  # noqa: E402
from orchestrator.runner import Verifier, WorktreeAdapter  # noqa: E402
from orchestrator.scheduler import Scheduler  # noqa: E402


def _default_verifier(task: dict[str, Any]) -> Verifier:
    operation = get_operation(str(task["operation"]))
    kinds = operation.required_verifications or ("staged_paths",)

    def verify(result: OpResult, staging: Path) -> list[dict[str, Any]]:
        write_scope = cast(list[str], task.get("write_scope") or [])
        missing = [path for path in write_scope if not (staging / path).exists()]
        ok = result.outcome == "succeeded" and not missing
        detail = "missing=" + ",".join(missing) if missing else (result.detail or "verified")
        return [{"kind": kind, "ok": ok, "detail": detail} for kind in kinds]

    return verify


def _build_adapter(name: str) -> SubagentAdapter:
    if name == "pi":
        model = os.environ.get("AW_PI_MODEL", "kimi-coding/k3.1-pro")
        inner: SubagentAdapter = PiSubagentAdapter(model=model)
    else:
        cursor_model = os.environ.get("AW_CURSOR_MODEL")
        force = os.environ.get("AW_CURSOR_FORCE", "0") == "1"
        inner = CursorSubagentAdapter(model=cursor_model, force=force)
    return inner


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Autoworkspace DAG orchestrator")
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--plan", type=Path, help="Unused; active plan is loaded from the repo status")
    parser.add_argument("--adapter", choices=("pi", "cursor"), required=True)
    parser.add_argument("--max-parallel", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true", default=True)
    parser.add_argument("--no-worktree", action="store_true", help="Call the harness adapter without WorktreeAdapter")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        inner = _build_adapter(args.adapter)
        adapter: SubagentAdapter
        if args.dry_run or args.no_worktree:
            adapter = inner
        else:
            adapter = WorktreeAdapter(args.repo.resolve(), inner, _default_verifier)
        scheduler = Scheduler(
            args.repo,
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
