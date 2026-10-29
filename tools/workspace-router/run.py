#!/usr/bin/env python3
"""Autoworkspace router: phase → skill handoff using project.yaml variables.

Query commands (route/list/status) are read-only: they do not create scaffold.
Use --init explicitly to create .autoworkspace from templates.
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

from project_load import (  # noqa: E402
    PHASES,
    ProjectConfigError,
    filter_skills,
    handoff_for_phase,
    load_project,
)
from status_bump import advance_status, load_status  # noqa: E402


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
    aw = repo / ".autoworkspace"
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
    project_path = repo / ".autoworkspace" / "project.yaml"
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
    ap = argparse.ArgumentParser(description="Autoworkspace phase router")
    ap.add_argument("--repo", default=".", help="Target repository path")
    ap.add_argument("--phase", choices=PHASES, help="Pipeline phase")
    ap.add_argument("--init", action="store_true", help="Create .autoworkspace scaffold")
    ap.add_argument("--list", action="store_true", help="List allowed skills (read-only)")
    ap.add_argument("--status", action="store_true", help="Show status.yaml (read-only)")
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
    ap.add_argument("--json", action="store_true", help="JSON output")
    return ap.parse_args(argv)


def _fail(message: object) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 2


def _cmd_init(repo: Path, args: argparse.Namespace) -> int:
    ensure_scaffold(repo)
    print(json.dumps({"init": True, "repo": str(repo)}) if args.json else f"initialized {repo}/.autoworkspace")
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


def _cmd_status(repo: Path, args: argparse.Namespace) -> int:
    try:
        status = load_status(repo)
    except Exception as exc:  # el CLI informa de cualquier fallo de lectura
        return _fail(exc)
    print(json.dumps(status, ensure_ascii=False, indent=2) if args.json else status)
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


def _dispatch(repo: Path, args: argparse.Namespace) -> int:
    if args.init and not args.phase and not args.list and not args.status:
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
