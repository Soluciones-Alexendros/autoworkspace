#!/usr/bin/env python3
"""Fleet dashboard: read-only overview of all repos in ~/Repertorio.

Outputs JSON or table. Does not write anything.
"""

from __future__ import annotations
import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

REPERTORIO = Path("/home/alexendros/Repertorio")


@dataclass
class RepoStatus:
    name: str
    branch: str
    dirty_count: int
    has_autoworkspace: bool
    phase: Optional[str]
    advance: Optional[int]
    last_skill: Optional[str]
    last_commit: Optional[str]
    plan_docs: list[str]


def run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=10)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return -1, "", str(e)


def get_git_info(repo: Path) -> tuple[str, int, str]:
    """Return (branch, dirty_count, last_commit_iso)."""
    code, out, _ = run(["git", "branch", "--show-current"], repo)
    branch = out if code == 0 and out else "?"
    code, out, _ = run(["git", "status", "--porcelain"], repo)
    dirty = len(out.splitlines()) if code == 0 and out else 0
    code, out, _ = run(["git", "log", "-1", "--format=%ci"], repo)
    last_commit = out if code == 0 and out else None
    return branch, dirty, last_commit


def get_autoworkspace_status(repo: Path) -> tuple[bool, Optional[str], Optional[int], Optional[str]]:
    status_file = repo / ".autoworkspace" / "status.yaml"
    if not status_file.is_file():
        return False, None, None, None
    try:
        import yaml
        data = yaml.safe_load(status_file.read_text())
        return (
            True,
            data.get("phase"),
            data.get("advance"),
            data.get("last_skill"),
        )
    except Exception:
        return True, None, None, None


def find_plan_docs(repo: Path) -> list[str]:
    """Find plan documents in known locations."""
    plans = []
    # autoworkspace standard locations
    for pattern in [
        "docs/plans/*.md",
        "tasks/plan-*.md",
        ".autoworkspace/SPEC.md",
        "docs/00-governance/plan-status.md",
        "app/docs/plan-*.md",
        "docs/plans/*.md",
    ]:
        plans.extend(str(p.relative_to(repo)) for p in repo.glob(pattern))
    return sorted(set(plans))


def scan_repertorio() -> list[RepoStatus]:
    results = []
    for entry in REPERTORIO.iterdir():
        if not entry.is_dir():
            continue
        if not (entry / ".git").is_dir():
            continue
        branch, dirty, last_commit = get_git_info(entry)
        has_aw, phase, advance, last_skill = get_autoworkspace_status(entry)
        plan_docs = find_plan_docs(entry)
        results.append(RepoStatus(
            name=entry.name,
            branch=branch,
            dirty_count=dirty,
            has_autoworkspace=has_aw,
            phase=phase,
            advance=advance,
            last_skill=last_skill,
            last_commit=last_commit,
            plan_docs=plan_docs,
        ))
    return results


def print_table(repos: list[RepoStatus]) -> None:
    # Sort: dirty first, then by name
    repos.sort(key=lambda r: (-r.dirty_count, r.name))

    print(f"{'REPO':<30} {'BRANCH':<28} {'DIRTY':>5} {'AW':>3} {'PHASE':<12} {'ADV':>3} {'LAST_SKILL':<16} {'LAST_COMMIT':<19} {'PLANS'}")
    print("-" * 160)
    for r in repos:
        dirty_flag = "🔴" if r.dirty_count > 0 else "🟢"
        aw_flag = "✅" if r.has_autoworkspace else "❌"
        phase = r.phase or "-"
        adv = str(r.advance) if r.advance is not None else "-"
        skill = (r.last_skill or "-")[:15]
        commit = (r.last_commit or "-")[:18]
        plans = ", ".join(r.plan_docs) if r.plan_docs else "-"
        if len(plans) > 50:
            plans = plans[:47] + "..."
        print(f"{r.name:<30} {r.branch:<28} {dirty_flag}{r.dirty_count:>4} {aw_flag:>3} {phase:<12} {adv:>3} {skill:<16} {commit:<19} {plans}")


def print_json(repos: list[RepoStatus]) -> None:
    print(json.dumps([asdict(r) for r in repos], indent=2, ensure_ascii=False))


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Fleet status dashboard")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--repo", help="Filter to single repo")
    args = ap.parse_args()

    repos = scan_repertorio()
    if args.repo:
        repos = [r for r in repos if r.name == args.repo]
        if not repos:
            print(f"Repo {args.repo} not found", file=sys.stderr)
            sys.exit(1)

    if args.json:
        print_json(repos)
    else:
        print_table(repos)


if __name__ == "__main__":
    main()