#!/usr/bin/env python3
"""Autoworkspace router: phase → skill handoff using project.yaml variables.

Query commands (route/list/status) are read-only: they do not create scaffold.
Use --init explicitly to create .autoworkspace from templates.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

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
        skills_dir = ROOT / "skills"
        return sorted(
            p.name
            for p in skills_dir.iterdir()
            if p.is_dir() and (p / "SKILL.md").is_file()
        )
    data = json.loads(index.read_text(encoding="utf-8"))
    return [s["name"] for s in data.get("skills", [])]


def ensure_scaffold(repo: Path) -> None:
    """Explicit init only."""
    aw = repo / ".autoworkspace"
    aw.mkdir(parents=True, exist_ok=True)
    (aw / "schemas").mkdir(exist_ok=True)
    tmpl = ROOT / "templates" / "autoworkspace"
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
            f"missing {project_path}; run with --init to create scaffold "
            "(route/list/status do not write by default)"
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
        raise ProjectConfigError(
            f"handoff skill {skill!r} not in allowlist; refusing silent fallback"
        )
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


def main(argv: list[str] | None = None) -> int:
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
    args = ap.parse_args(argv)
    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"ERROR: not a directory: {repo}", file=sys.stderr)
        return 2

    if args.init and not args.phase and not args.list and not args.status:
        ensure_scaffold(repo)
        print(json.dumps({"init": True, "repo": str(repo)}) if args.json else f"initialized {repo}/.autoworkspace")
        return 0

    if args.list:
        try:
            if args.init:
                ensure_scaffold(repo)
            project = load_project(repo)
            allowed = filter_skills(load_catalog(), project)
        except ProjectConfigError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(json.dumps({"allowed_skills": allowed}) if args.json else "\n".join(allowed))
        return 0

    if args.status:
        try:
            status = load_status(repo)
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(status, ensure_ascii=False, indent=2) if args.json else status)
        return 0

    if not args.phase:
        print("ERROR: --phase required unless --init/--list/--status", file=sys.stderr)
        return 2

    if args.awaiting_agent:
        try:
            data = advance_status(
                repo, phase=args.phase, note=args.note, evidence_ok=False, allow_awaiting=True
            )
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else f"awaiting_agent phase={args.phase}")
        return 0

    if args.complete:
        if not args.run_id:
            print("ERROR: --complete requires --run-id of validated evidence", file=sys.stderr)
            return 2
        try:
            project = load_project(repo)
            skill = handoff_for_phase(project, args.phase) or ""
            catalog = load_catalog()
            allowed = filter_skills(catalog, project)
            if skill and skill not in allowed:
                print(f"ERROR: skill {skill} not in project allowlist", file=sys.stderr)
                return 2
            phases = project.get("phases") or list(PHASES)
            if args.phase not in phases:
                print(f"ERROR: phase {args.phase} not enabled in project config", file=sys.stderr)
                return 2
            data = advance_status(
                repo,
                phase=args.phase,
                skill=skill,
                note=args.note,
                evidence_ok=True,
                run_id=args.run_id,
            )
        except ProjectConfigError as exc:
            print(f"ERROR: invalid project config: {exc}", file=sys.stderr)
            return 2
        except (ValueError, FileNotFoundError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else f"completed phase={args.phase} rev={data.get('state_revision')}")
        return 0

    try:
        out = route(repo, args.phase, bump=args.bump, note=args.note, init=args.init)
    except ProjectConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"phase={out['phase']} skill={out['skill']} profile={out['profile']}")
        print(f"status version={out['status'].get('version')} advance={out['status'].get('advance')}")
        print(f"allowed={len(out['allowed_skills'])} skills")
        print(f"→ invoke skill tool / read skills/{out['skill']}/SKILL.md (route ≠ execute)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
