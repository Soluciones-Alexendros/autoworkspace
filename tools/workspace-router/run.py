#!/usr/bin/env python3
"""Machineroom router: phase → skill handoff using project.yaml variables.

Query commands (route/list/status) are read-only: they do not create scaffold.
Use --init explicitly to create .machineroom from templates.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
_TOOLS = Path(__file__).resolve().parents[1]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from project_load import (  # noqa: E402
    PHASES,
    ProjectConfigError,
    filter_skills,
    handoff_for_phase,
    load_project,
)
from state_paths import StateDirError, format_state_failure, migrate_state, state_dir  # noqa: E402
from status_bump import advance_status, load_status, migrate_status  # noqa: E402


def load_catalog() -> list[str]:
    index = ROOT / "skill-index.json"
    if not index.is_file():
        gen_path = ROOT / "tools" / "skill-index" / "generate.py"
        spec = importlib.util.spec_from_file_location("skill_index_generate", gen_path)
        if spec is not None and spec.loader is not None:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.ensure_index(ROOT)
    if not index.is_file():
        skills_dir = ROOT / "skills"
        return sorted(p.name for p in skills_dir.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())
    data = json.loads(index.read_text(encoding="utf-8"))
    return [s["name"] for s in data.get("skills", [])]


def ensure_scaffold(repo: Path) -> None:
    """Explicit init only."""
    aw = repo / ".machineroom"
    aw.mkdir(parents=True, exist_ok=True)
    (aw / "schemas").mkdir(exist_ok=True)
    tmpl = ROOT / "templates" / "harness"
    for name in ("project.yaml", "status.yaml"):
        dest = aw / name
        if not dest.is_file():
            dest.write_text((tmpl / name).read_text(encoding="utf-8"), encoding="utf-8")


def route(repo: Path, phase: str, *, bump: bool, note: str, init: bool = False) -> dict:
    if init:
        ensure_scaffold(repo)
    project_path = state_dir(repo) / "project.yaml"
    if not project_path.is_file():
        raise ProjectConfigError(
            f"missing {project_path}; run with --init to create scaffold (route/list/status do not write by default)"
        )
    try:
        project = load_project(repo)
    except ProjectConfigError:
        raise
    catalog = load_catalog()
    try:
        allowed = filter_skills(catalog, project)
    except ProjectConfigError:
        raise
    if not allowed:
        raise ProjectConfigError("no skills allowed (enabled: [] or all disabled)")
    skill = handoff_for_phase(project, phase)
    if skill is None or skill not in catalog:
        raise ProjectConfigError(f"unknown handoff skill for phase {phase}: {skill!r}")
    if skill not in allowed:
        raise ProjectConfigError(f"handoff skill {skill!r} not in allowlist; refusing silent fallback")
    result = {
        "repo": str(repo),
        "phase": phase,
        "skill": skill,
        "allowed_skills": allowed,
        "profile": project.get("profile"),
        "handoffs": project.get("handoffs") or {},
        "execution": "route_only",
        "note": "Router selects; it does not execute the skill",
    }
    if bump:
        # Legacy --bump: reject arbitrary SemVer bookkeeping
        raise ProjectConfigError(
            "--bump is disabled for arbitrary advances; use verified complete "
            "with evidence (T15) or an explicit migration path"
        )
    try:
        status = load_status(repo)
    except Exception:
        status = {}
    result["status"] = {
        "version": status.get("version"),
        "advance": status.get("advance"),
        "phase": status.get("phase"),
        "state_revision": status.get("state_revision"),
    }
    return result


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Machineroom phase router")
    ap.add_argument("--repo", default=".", help="Target repository path")
    ap.add_argument("--phase", choices=PHASES, help="Pipeline phase")
    ap.add_argument("--init", action="store_true", help="Create .machineroom scaffold")
    ap.add_argument("--migrate", action="store_true", help="Move legacy .machineroom to .machineroom")
    ap.add_argument("--list", action="store_true", help="List allowed skills (read-only)")
    ap.add_argument("--status", action="store_true", help="Show status.yaml (read-only)")
    ap.add_argument("--migrate-status", action="store_true", help="Persist status schema migration explicitly")
    ap.add_argument(
        "--bump",
        action="store_true",
        help="(disabled) legacy status bump — rejected",
    )
    ap.add_argument(
        "--complete",
        action="store_true",
        help="Complete phase with validated evidence (requires --run-id)",
    )
    ap.add_argument("--run-id", default="", help="Evidence run_id for --complete")
    ap.add_argument(
        "--awaiting-agent",
        action="store_true",
        help="Mark phase awaiting_agent without completing",
    )
    ap.add_argument("--note", default="", help="Optional status history note")
    ap.add_argument("--dry-run", action="store_true", help="Report without writing (with --migrate)")
    ap.add_argument("--json", action="store_true", help="JSON output")
    return ap.parse_args(argv)


def _fail(message: object) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 2


def _cmd_init(repo: Path, args: argparse.Namespace) -> int:
    ensure_scaffold(repo)
    print(json.dumps({"init": True, "repo": str(repo)}) if args.json else f"initialized {repo}/.machineroom")
    return 0


def _cmd_list(repo: Path, args: argparse.Namespace) -> int:
    try:
        if args.init:
            ensure_scaffold(repo)
        project = load_project(repo)
        allowed = filter_skills(load_catalog(), project)
    except ProjectConfigError as exc:
        return _fail(exc)
    print(json.dumps({"allowed_skills": allowed}) if args.json else "\n".join(allowed))
    return 0


def _cmd_migrate_state(repo: Path, args: argparse.Namespace) -> int:
    try:
        data = migrate_state(repo, dry_run=args.dry_run)
    except StateDirError as exc:
        print(format_state_failure(exc.component, exc.function, exc.detail), file=sys.stderr)
        return _fail(exc.detail)
    print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else data["detail"])
    return 0


def _cmd_status(repo: Path, args: argparse.Namespace) -> int:
    try:
        status = load_status(repo)
    except Exception as exc:  # el CLI informa de cualquier fallo de lectura
        return _fail(exc)
    print(json.dumps(status, ensure_ascii=False, indent=2) if args.json else status)
    return 0


def _cmd_migrate_status(repo: Path, args: argparse.Namespace) -> int:
    try:
        data = migrate_status(repo)
    except (ValueError, OSError) as exc:
        return _fail(exc)
    print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else "status migration complete")
    return 0


def _cmd_awaiting(repo: Path, args: argparse.Namespace) -> int:
    try:
        data = advance_status(repo, phase=args.phase, note=args.note, evidence_ok=False, allow_awaiting=True)
    except ValueError as exc:
        return _fail(exc)
    print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else f"awaiting_agent phase={args.phase}")
    return 0


class _InvalidProjectError(Exception):
    """The project configuration could not be loaded."""


def _complete_target(repo: Path, args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    try:
        project = load_project(repo)
    except ProjectConfigError as exc:
        raise _InvalidProjectError(str(exc)) from exc
    skill = handoff_for_phase(project, args.phase) or ""
    allowed = filter_skills(load_catalog(), project)
    if skill and skill not in allowed:
        raise ValueError(f"skill {skill} not in project allowlist")
    phases = project.get("phases") or list(PHASES)
    if args.phase not in phases:
        raise ValueError(f"phase {args.phase} not enabled in project config")
    return project, skill


def _cmd_complete(repo: Path, args: argparse.Namespace) -> int:
    if not args.run_id:
        return _fail("--complete requires --run-id of validated evidence")
    try:
        _project, skill = _complete_target(repo, args)
        data = advance_status(
            repo,
            phase=args.phase,
            skill=skill,
            note=args.note,
            evidence_ok=True,
            run_id=args.run_id,
        )
    except _InvalidProjectError as exc:
        return _fail(f"invalid project config: {exc}")
    except (ValueError, FileNotFoundError) as exc:
        return _fail(exc)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"completed phase={args.phase} rev={data.get('state_revision')}")
    return 0


def _cmd_route(repo: Path, args: argparse.Namespace) -> int:
    try:
        out = route(repo, args.phase, bump=args.bump, note=args.note, init=args.init)
    except ProjectConfigError as exc:
        return _fail(exc)
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"phase={out['phase']} skill={out['skill']} profile={out['profile']}")
        print(f"status version={out['status'].get('version')} advance={out['status'].get('advance')}")
        print(f"allowed={len(out['allowed_skills'])} skills")
        print(f"→ invoke skill tool / read skills/{out['skill']}/SKILL.md (route ≠ execute)")
    return 0


def _dispatch_phase(repo: Path, args: argparse.Namespace) -> int:
    if not args.phase:
        return _fail("--phase required unless --init/--list/--status")
    if args.awaiting_agent:
        return _cmd_awaiting(repo, args)
    if args.complete:
        return _cmd_complete(repo, args)
    return _cmd_route(repo, args)


_EXCLUSIVE_COMMANDS = ("migrate", "migrate_status", "init", "list", "status", "phase")


def _conflict(args: argparse.Namespace, owner: str) -> str | None:
    """Return an error message when a single-command flag is combined with others."""
    others = [f"--{name.replace('_', '-')}" for name in _EXCLUSIVE_COMMANDS if name != owner and getattr(args, name)]
    if not others:
        return None
    return f"--{owner.replace('_', '-')} cannot be combined with {', '.join(others)}"


def _dispatch(repo: Path, args: argparse.Namespace) -> int:
    if args.migrate or args.migrate_status:
        owner = "migrate" if args.migrate else "migrate_status"
        problem = _conflict(args, owner)
        if problem:
            return _fail(problem)
        return _cmd_migrate_state(repo, args) if args.migrate else _cmd_migrate_status(repo, args)
    if args.init and not (args.phase or args.list or args.status):
        return _cmd_init(repo, args)
    if args.list:
        return _cmd_list(repo, args)
    if args.status:
        return _cmd_status(repo, args)
    return _dispatch_phase(repo, args)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        return _fail(f"not a directory: {repo}")
    return _dispatch(repo, args)


if __name__ == "__main__":
    raise SystemExit(main())
