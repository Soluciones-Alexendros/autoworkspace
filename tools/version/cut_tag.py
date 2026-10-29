#!/usr/bin/env python3
"""Corte de tag anotado vX.Y.Z a partir de package.json y CHANGELOG.md.

Uso:
  python3 tools/version/cut_tag.py [--root DIR] [--dry-run] [--apply] [--push]
  python3 tools/version/cut_tag.py --extract-notes 2.2.0 --notes-file notes.md

Exit 0 si no hay nada que cortar (sin sección/notas, ya etiquetado) o si el tag se creó.
Exit 1 en error de entorno git/FS.
Notas ausentes con --apply no fallan el job de release en main: se omite el corte
hasta que CHANGELOG tenga la sección fechada de package.json.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z][0-9A-Za-z.-]*))?$")
CHANGELOG_H2 = re.compile(
    r"^## \[([0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z][0-9A-Za-z.-]*)?)\] - (\d{4}-\d{2}-\d{2})(.*)$"
)
STABLE_TAG_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
RELEASE_PATHS = {
    "CHANGELOG.md",
    "package.json",
    ".github/workflows/release.yml",
    "tools/version/cut_tag.py",
    "tools/validate/release_coherence.py",
}


def git(args: list[str], root: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r


def parse_semver(ver: str) -> tuple[int, int, int]:
    m = SEMVER_RE.match(ver)
    if not m:
        raise ValueError(f"no semver: {ver}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def is_prerelease(ver: str) -> bool:
    m = SEMVER_RE.match(ver)
    return bool(m and m.group(4))


def package_version(root: Path) -> str:
    data = json.loads((root / "package.json").read_text(encoding="utf-8"))
    ver = str(data["version"])
    parse_semver(ver)
    return ver


def latest_tag(root: Path) -> str | None:
    r = git(["tag", "-l", "v*.*.*", "--sort=-v:refname"], root, check=False)
    if r.returncode != 0:
        return None
    for line in r.stdout.splitlines():
        tag = line.strip()
        if tag.startswith("v") and STABLE_TAG_RE.match(tag[1:]):
            return tag[1:]
    return None


def extract_notes(changelog: str, version: str) -> str:
    lines = changelog.splitlines()
    notes: list[str] = []
    capture = False
    for line in lines:
        found = CHANGELOG_H2.match(line)
        if line.startswith("## ["):
            if capture:
                break
            if found and found.group(1) == version:
                if "YANKED" in found.group(3):
                    raise ValueError(f"{version} está YANKED")
                capture = True
            continue
        if capture:
            notes.append(line)
    text = "\n".join(notes).strip()
    if not text:
        raise ValueError(f"notas vacías para {version}")
    return text + "\n"


def should_cut(pkg: str, tagged: str | None) -> bool:
    if tagged is None:
        return True
    return parse_semver(pkg) > parse_semver(tagged)


def repo_bump_required(changed: list[str], pkg: str, tagged: str | None) -> bool:
    hits = [p for p in changed if p in RELEASE_PATHS or p.startswith(".github/workflows/")]
    if not hits:
        return False
    if tagged is None:
        return False
    return parse_semver(pkg) <= parse_semver(tagged)


def cmd_extract(args: argparse.Namespace) -> int:
    text = (args.root / "CHANGELOG.md").read_text(encoding="utf-8")
    notes = extract_notes(text, args.extract_notes)
    if args.notes_file:
        Path(args.notes_file).write_text(notes, encoding="utf-8")
    else:
        sys.stdout.write(notes)
    return 0


def write_output(**kwargs: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        for key, value in kwargs.items():
            handle.write(f"{key}={value}\n")


def _refuse_prerelease(pkg: str, label: str) -> int:
    print(f"{label}: refuse prerelease package={pkg}; no stable tag")
    write_output(tagged="false", version=pkg, status="refused", reason="prerelease")
    return 1


def cmd_check_repo(args: argparse.Namespace) -> int:
    root = args.root
    pkg = package_version(root)
    tagged = latest_tag(root)
    r = git(["diff", "--name-only", f"{args.base}...HEAD"], root, check=False)
    changed = [line.strip() for line in r.stdout.splitlines() if line.strip()]
    st = git(["status", "--porcelain"], root, check=False)
    for line in st.stdout.splitlines():
        name = line[3:].strip().strip('"')
        if " -> " in name:
            name = name.split(" -> ")[-1].strip()
        if name:
            changed.append(name)
    if repo_bump_required(changed, pkg, tagged):
        print(f"CHECK-REPO: package.json {pkg} no está por delante del tag {tagged}")
        return 1
    print(f"CHECK-REPO: OK package={pkg} latest_tag={tagged}")
    return 0


def cmd_readiness(args: argparse.Namespace) -> int:
    """Strict release readiness (C20): missing/empty/YANKED notes → fail, never published."""
    root = args.root
    pkg = package_version(root)
    if is_prerelease(pkg):
        return _refuse_prerelease(pkg, "READINESS")
    tagged = latest_tag(root)
    changelog_path = root / "CHANGELOG.md"
    if not changelog_path.is_file():
        print(f"READINESS: fail reason=missing_changelog package={pkg}")
        write_output(tagged="false", version=pkg, status="not_ready", reason="missing_changelog")
        return 1
    try:
        changelog = changelog_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"READINESS: fail reason=fs_error package={pkg} err={exc}")
        write_output(tagged="false", version=pkg, status="error", reason="fs_error")
        return 1
    try:
        notes = extract_notes(changelog, pkg)
    except ValueError as e:
        reason = "yanked" if "YANKED" in str(e) else "missing_or_empty_notes"
        print(f"READINESS: fail reason={reason} package={pkg} detail={e}")
        write_output(tagged="false", version=pkg, status="not_ready", reason=reason)
        return 1
    if not should_cut(pkg, tagged):
        print(f"READINESS: fail reason=already_tagged package={pkg} latest_tag={tagged}")
        write_output(tagged="false", version=pkg, status="not_ready", reason="already_tagged")
        return 1
    print(f"READINESS: ok package={pkg} notes_bytes={len(notes)} latest_tag={tagged}")
    write_output(tagged="false", version=pkg, status="ready", reason="ok")
    if args.notes_file:
        Path(args.notes_file).write_text(notes, encoding="utf-8")
    return 0


def _cut_notes(args: argparse.Namespace, root: Path, pkg: str, tagged: str | None) -> tuple[str | None, int | None]:
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    try:
        return extract_notes(changelog, pkg), None
    except ValueError as e:
        if args.strict_readiness:
            print(f"CUT: fail ({e}); package={pkg}")
            write_output(tagged="false", version=pkg, status="not_ready", reason="notes")
            return None, 1
        # Ordinary push path: skip ≠ published
        print(f"CUT: skip ({e}); package={pkg} latest_tag={tagged}")
        write_output(tagged="false", version=pkg, status="skipped", reason=str(e))
        return None, 0


def _tag_and_push(args: argparse.Namespace, root: Path, tag: str, pkg: str) -> int | None:
    try:
        git(["tag", "-a", tag, "-m", tag], root)
    except RuntimeError as exc:
        print(f"CUT: fail git_error {exc}")
        write_output(tagged="false", version=pkg, status="error", reason="git_error")
        return 1
    if not args.push:
        return None
    try:
        git(["push", "origin", tag], root)
    except RuntimeError as exc:
        print(f"CUT: fail push_error {exc}")
        write_output(tagged="false", version=pkg, status="error", reason="push_error")
        return 1
    return None


def _cmd_cut_release(args: argparse.Namespace, pkg: str) -> int:
    root = args.root
    tagged = latest_tag(root)
    if args.strict_readiness:
        # Explicit release path: readiness failure is an error, never skip-success.
        rc = cmd_readiness(args)
        if rc != 0:
            return rc
    notes, skip_rc = _cut_notes(args, root, pkg, tagged)
    if skip_rc is not None:
        return skip_rc
    if not should_cut(pkg, tagged):
        print(f"CUT: skip package={pkg} latest_tag={tagged}")
        write_output(tagged="false", version=pkg, status="skipped", reason="already_tagged")
        return 0
    tag = f"v{pkg}"
    print(f"CUT: would tag {tag} (latest={tagged})")
    if notes is not None and args.notes_file:
        Path(args.notes_file).write_text(notes, encoding="utf-8")
    if not args.apply:
        write_output(tagged="false", version=pkg, status="dry_run", reason="ok")
        return 0
    failed = _tag_and_push(args, root, tag, pkg)
    if failed is not None:
        return failed
    print(f"CUT: created {tag}")
    write_output(tagged="true", version=pkg, status="published", reason="ok")
    return 0


def cmd_cut(args: argparse.Namespace) -> int:
    pkg = package_version(args.root)
    if is_prerelease(pkg):
        return _refuse_prerelease(pkg, "CUT")
    return _cmd_cut_release(args, pkg)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Cortar tag anotado del repo.")
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--dry-run", action="store_true", help="alias de no --apply")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--push", action="store_true")
    p.add_argument("--extract-notes", default=None, metavar="VERSION")
    p.add_argument("--notes-file", default=None)
    p.add_argument("--check-repo", action="store_true")
    p.add_argument(
        "--check-readiness",
        action="store_true",
        help="Strict readiness gate: missing/empty/YANKED notes fail (never published)",
    )
    p.add_argument(
        "--strict-readiness",
        action="store_true",
        help="On cut: treat missing notes as failure instead of skip",
    )
    p.add_argument("--base", default="origin/main")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.root = Path(args.root).resolve()
    if args.extract_notes:
        return cmd_extract(args)
    if args.check_repo:
        return cmd_check_repo(args)
    if args.check_readiness:
        return cmd_readiness(args)
    return cmd_cut(args)


if __name__ == "__main__":
    sys.exit(main())
