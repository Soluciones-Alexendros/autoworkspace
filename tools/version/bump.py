#!/usr/bin/env python3
"""Autoversionado semver por magnitud de cambio.

Sube `metadata.version` de las skills afectadas segun la magnitud:
  major = actualizacion incompatible (breaking)
  minor = desarrollo menor, nueva funcionalidad compatible
  patch = parcheado, fix compatible

Uso:
  python3 tools/version/bump.py --type minor --skills codigo-seguridad
  python3 tools/version/bump.py --type parche --all --dry-run
  python3 tools/version/bump.py --type fix --auto --base origin/main
  python3 tools/version/bump.py --check --auto --base origin/main

Sin dependencias externas. Exit 0 si aplica (o no hay nada que hacer);
exit 1 con error de uso/entorno; exit 2 en --check si falta bump.
"""

import argparse
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "skills"
CHANGELOG = ROOT / "CHANGELOG.md"

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
VERSION_LINE_RE = re.compile(r'^(\s*version:\s*)["\']?(\d+\.\d+\.\d+)["\']?(\s*)$')

SKILLS_PATH_PARTS = 2
KINDS = ("major", "minor", "patch")
RANK = {"patch": 0, "minor": 1, "major": 2}

ALIASES = {
    "major": {"major", "actualizacion-mayor", "actualizacion", "breaking", "incompatible", "mayor"},
    "minor": {"minor", "desarrollo-menor", "menor", "feature", "funcionalidad", "nueva-funcionalidad"},
    "patch": {"patch", "parche", "parcheado", "fix", "correccion", "hotfix", "rev"},
}
for _k in list(ALIASES):
    ALIASES[_k] = {_a for _a in ALIASES[_k]}


def normalize_kind(raw: str) -> str:
    norm = unicodedata.normalize("NFKD", raw.strip().lower())
    norm = "".join(c for c in norm if not unicodedata.combining(c))
    norm = norm.replace("_", "-").replace(" ", "-")
    for kind in KINDS:
        if norm in ALIASES[kind]:
            return kind
    raise ValueError(f"magnitud desconocida: '{raw}' (usar: major|minor|patch o alias ES)")


def bump_version(current: str, kind: str) -> str:
    m = SEMVER_RE.match(current.strip())
    if not m:
        raise ValueError(f"version no semver: '{current}'")
    major, minor, patch = (int(m.group(i)) for i in (1, 2, 3))
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def read_skill_version(sdir: Path) -> str:
    text = (sdir / "SKILL.md").read_text(encoding="utf-8")
    for line in text.splitlines():
        m = VERSION_LINE_RE.match(line)
        if m:
            return m.group(2)
    raise ValueError(f"[{sdir.name}] sin linea 'version: X.Y.Z' en SKILL.md")


def write_skill_version(sdir: Path, new: str) -> str:
    path = sdir / "SKILL.md"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    old = None
    for i, line in enumerate(lines):
        body = line.rstrip("\n")
        m = VERSION_LINE_RE.match(body)
        if m:
            old = m.group(2)
            quote = '"' if '"' in body else ("'" if "'" in body else '"')
            lines[i] = f"{m.group(1)}{quote}{new}{quote}\n"
            break
    if old is None:
        raise ValueError(f"[{sdir.name}] sin linea 'version: X.Y.Z' en SKILL.md")
    path.write_text("".join(lines), encoding="utf-8")
    return old


def list_skills(root: Path = ROOT) -> list[str]:
    d = root / "skills"
    return sorted(p.name for p in d.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())


def skills_from_paths(paths: list[str]) -> list[str]:
    out: list[str] = []
    for p in paths:
        parts = Path(p).parts
        if len(parts) >= SKILLS_PATH_PARTS and parts[0] == "skills":
            name = parts[1]
            if name not in out:
                out.append(name)
    return sorted(out)


def git(args: list[str], root: Path = ROOT) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def resolve_base(base: str, root: Path = ROOT) -> str:
    for candidate in (base, "main", "HEAD"):
        try:
            git(["rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}"], root)
            return candidate
        except RuntimeError:
            continue
    raise RuntimeError("sin base git resoluble (ni base, ni main, ni HEAD)")


def changed_paths(base: str, root: Path = ROOT) -> list[str]:
    paths: set[str] = set()
    try:
        out = git(["diff", "--name-only", f"{base}...HEAD"], root)
        paths.update(p for p in out.splitlines() if p.strip())
    except RuntimeError:
        pass
    st = git(["status", "--porcelain"], root)
    for line in st.splitlines():
        name = line[3:].strip().strip('"')
        if " -> " in name:
            name = name.split(" -> ")[-1].strip()
        if name:
            paths.add(name)
    return sorted(paths)


def version_at(base: str, skill: str, root: Path = ROOT) -> str | None:
    try:
        out = git(["show", f"{base}:skills/{skill}/SKILL.md"], root)
    except RuntimeError:
        return None
    for line in out.splitlines():
        m = VERSION_LINE_RE.match(line)
        if m:
            return m.group(2)
    return None


def latest_repo_tag(root: Path = ROOT) -> str | None:
    try:
        out = git(["describe", "--tags", "--abbrev=0"], root).strip()
    except RuntimeError:
        return None
    return out.lstrip("v") if out else None


def update_changelog(entries: list[tuple[str, str, str, str]], message: str | None) -> None:
    header = "# Changelog\n"
    text = CHANGELOG.read_text(encoding="utf-8") if CHANGELOG.is_file() else header
    if not text.endswith("\n"):
        text += "\n"
    lines = [f"- `{skill}` {old} -> {new} ({kind})" for skill, old, new, kind in entries]
    if message:
        lines.append(f"\n  {message}")
    block = "\n".join(lines)
    if "## [Unreleased]" in text:
        text = text.replace("## [Unreleased]", f"## [Unreleased]\n\n{block}", 1)
    else:
        head, sep, rest = text.partition("\n")
        insert = f"{head}\n\n## [Unreleased]\n\n{block}\n"
        text = insert + (sep + rest if sep else "")
    CHANGELOG.write_text(text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Autoversionado semver por magnitud (major|minor|patch).")
    p.add_argument("--root", default=str(ROOT), help="raiz del repo")
    p.add_argument("--type", "-t", dest="kind", default=None, help="magnitud: major|minor|patch (+alias ES)")
    p.add_argument("--skills", default=None, help="lista coma-separada de skills")
    p.add_argument("--all", action="store_true", help="todas las skills")
    p.add_argument("--auto", action="store_true", help="detectar skills por git diff/status")
    p.add_argument("--base", default="origin/main", help="ref base para --auto/--check")
    p.add_argument("--check", action="store_true", help="verifica bump ya aplicado vs base (CI)")
    p.add_argument("--dry-run", "-n", action="store_true", help="no escribe cambios")
    p.add_argument("--no-changelog", action="store_true", help="no toca CHANGELOG.md")
    p.add_argument("--message", "-m", default=None, help="mensaje extra para el CHANGELOG")
    p.add_argument("--tag", action="store_true", help="crea tag de repo vX.Y.Z (max bump)")
    return p


def resolve_targets(args: argparse.Namespace, root: Path) -> list[str]:
    if args.skills:
        wanted = [s.strip() for s in args.skills.split(",") if s.strip()]
        known = set(list_skills(root))
        unknown = [s for s in wanted if s not in known]
        if unknown:
            raise ValueError(f"skills desconocidas: {', '.join(unknown)}")
        return sorted(set(wanted))
    if args.all:
        return list_skills(root)
    if args.auto:
        base = resolve_base(args.base, root)
        return [s for s in skills_from_paths(changed_paths(base, root)) if (root / "skills" / s).is_dir()]
    raise ValueError("indicar objetivo: --skills, --all o --auto")


def cmd_check(targets: list[str], base: str, root: Path) -> int:
    if not targets:
        print("CHECK: sin skills afectadas, nada que exigir")
        return 0
    missing: list[str] = []
    for skill in targets:
        old = version_at(base, skill, root)
        try:
            cur = read_skill_version(root / "skills" / skill)
        except ValueError as e:
            missing.append(str(e))
            continue
        if old is None:
            print(f"CHECK NEW: {skill}@{cur} (skill nueva, OK)")
        elif cur == old:
            missing.append(f"{skill} sigue en {cur} (sin bump vs {base})")
        else:
            print(f"CHECK OK: {skill} {old} -> {cur}")
    if missing:
        print("CHECK: FALTA BUMP en:")
        for m in missing:
            print(f"  - {m}")
        print("Aplicar: python3 tools/version/bump.py --auto --type <major|minor|patch>")
        return 2
    print("CHECK: todo versionado")
    return 0


def _fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def _apply_bumps(args: Any, targets: list[str], root: Path, kind: str) -> list[tuple[str, str, str, str]]:
    entries: list[tuple[str, str, str, str]] = []
    for skill in targets:
        sdir = root / "skills" / skill
        cur = read_skill_version(sdir)
        new = bump_version(cur, kind)
        if args.dry_run:
            print(f"DRY: {skill} {cur} -> {new} ({kind})")
        else:
            write_skill_version(sdir, new)
            print(f"BUMP: {skill} {cur} -> {new} ({kind})")
        entries.append((skill, cur, new, kind))
    return entries


def _report_repo(top: str, root: Path) -> str | None:
    repo_current = latest_repo_tag(root)
    if not repo_current or not SEMVER_RE.match(repo_current):
        print(f"REPO: sin tag previo resoluble; magnitud agregada: {top}")
        return None
    repo_next = bump_version(repo_current, top)
    print(f"REPO: v{repo_current} -> v{repo_next} (sugerido, magnitud {top})")
    return repo_next


def _emit_tag(args: Any, entries: list[tuple[str, str, str, str]], repo_next: str | None, top: str, root: Path) -> None:
    if not (args.tag and not args.dry_run and repo_next):
        return
    names = ", ".join(s for s, _, _, _ in entries)
    git(["tag", "-a", f"v{repo_next}", "-m", f"v{repo_next} ({top}): {names}"], root)
    print(f"TAG: v{repo_next} creado (recordar: git push origin v{repo_next})")


def _run_check(args: Any, targets: list[str], root: Path) -> int:
    try:
        base = resolve_base(args.base, root)
    except RuntimeError as e:
        return _fail(str(e))
    return cmd_check(targets, base, root)


def _resolve_kind(raw: str | None) -> str:
    if not raw:
        raise ValueError("--type es obligatorio (salvo --check)")
    return normalize_kind(raw)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    try:
        targets = resolve_targets(args, root)
    except ValueError as e:
        return _fail(str(e))
    if args.check:
        return _run_check(args, targets, root)
    try:
        kind = _resolve_kind(args.kind)
    except ValueError as e:
        return _fail(str(e))
    if not targets:
        print("BUMP: sin skills afectadas, nada que hacer")
        return 0
    try:
        entries = _apply_bumps(args, targets, root, kind)
    except ValueError as e:
        return _fail(str(e))
    top = max((k for _, _, _, k in entries), key=lambda k: RANK[k])
    repo_next = _report_repo(top, root)
    if not args.dry_run and not args.no_changelog and entries:
        update_changelog(entries, args.message)
        print("CHANGELOG: entrada [Unreleased] actualizada")
    _emit_tag(args, entries, repo_next, top, root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
