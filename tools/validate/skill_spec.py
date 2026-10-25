#!/usr/bin/env python3
"""Validador de spec de skills (Agent Skills + STANDARD.md del repo).

Uso: python3 tools/validate/skill_spec.py [--root DIR]
Exit 0 si todas las skills cumplen; 1 en caso contrario (lista errores).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML no instalado. uv sync --frozen")
    sys.exit(1)

ROOT = Path(sys.argv[sys.argv.index("--root") + 1]) if "--root" in sys.argv else Path(__file__).resolve().parents[2]
SKILLS = ROOT / "skills"

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
SKILL_TOKEN_RE = re.compile(r"\b((?:plan|local|project|web|role)-[a-z0-9-]+)\b")
ARROW_RE = re.compile(r"→\s*`?((?:plan|local|project|web|role)-[a-z0-9-]+)`?")
H2_RE = re.compile(r"^## (.+?)\s*$", re.M)
PROHIBITED_DIRS = {"agents", "infrastructure", "languages"}
DOMINIOS = {"plan", "local", "project", "web", "role"}
TIPOS = {"atomic", "orchestrator", "router", "audit"}
REQUIRED_H2 = ("Overview", "When to Use")
FORBIDDEN_H2 = {
    "What it does / Purpose",
    "When to use me / Triggering",
    "Usage",
    "Structure",
}
MAX_BODY_LINES = 500
MAX_BODY_TOKENS = 5000
ERRORS: list[str] = []
TEST_DIR_NAMES = {"tests"}
TEST_FILE_PREFIX = "test_"


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def err(skill: str, msg: str) -> None:
    ERRORS.append(f"[{skill}] {msg}")


def parse_frontmatter(text: str, skill: str) -> dict | None:
    if not text.startswith("---\n"):
        err(skill, "SKILL.md no empieza con '---'")
        return None
    end = text.find("\n---", 4)
    if end == -1:
        err(skill, "frontmatter sin cierre '---'")
        return None
    fm_text = text[4:end]
    try:
        fm = yaml.safe_load(fm_text)
        if not isinstance(fm, dict):
            err(skill, "frontmatter no es un dict YAML válido")
            return None
    except yaml.YAMLError as e:
        err(skill, f"frontmatter YAML inválido: {e}")
        return None
    return fm


def skill_dirs(root: Path) -> list[Path]:
    skills = root / "skills"
    if not skills.is_dir():
        return []
    return sorted(p for p in skills.iterdir() if p.is_dir())


def catalog_names(text: str) -> set[str]:
    return set(SKILL_TOKEN_RE.findall(text))


def git_ls_files(root: Path, rel: str) -> list[str]:
    try:
        r = subprocess.run(
            ["git", "ls-files", rel],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []
    if r.returncode != 0:
        return []
    return [line for line in r.stdout.splitlines() if line.strip()]


def is_test_path(path: Path, sdir: Path) -> bool:
    rel = path.relative_to(sdir)
    if any(part in TEST_DIR_NAMES for part in rel.parts):
        return True
    return path.name.startswith(TEST_FILE_PREFIX) or path.name == "conftest.py"


def has_exec_scripts(sdir: Path) -> bool:
    for path in sdir.rglob("*"):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if path.suffix not in {".py", ".sh"}:
            continue
        if is_test_path(path, sdir):
            continue
        return True
    return False


def check_catalog(root: Path, names: set[str]) -> None:
    readme = root / "README.md"
    taxonomy = root / "docs" / "TAXONOMY.md"
    if not readme.is_file():
        ERRORS.append("[catalog] falta README.md")
        return
    if not taxonomy.is_file():
        ERRORS.append("[catalog] falta docs/TAXONOMY.md")
        return
    readme_names = catalog_names(readme.read_text(encoding="utf-8"))
    tax_names = catalog_names(taxonomy.read_text(encoding="utf-8"))
    if names != readme_names:
        missing = sorted(names - readme_names)
        extra = sorted(readme_names - names)
        ERRORS.append(f"[catalog] README vs carpetas missing={missing} extra={extra}")
    if names != tax_names:
        missing = sorted(names - tax_names)
        extra = sorted(tax_names - names)
        ERRORS.append(f"[catalog] TAXONOMY vs carpetas missing={missing} extra={extra}")


def check_description(skill: str, desc: str, names: set[str]) -> None:
    if not (1 <= len(desc) <= 1024):
        err(skill, f"description len={len(desc)} (1-1024)")
    if "Use when" not in desc:
        err(skill, "description without 'Use when'")
    if "Not for" not in desc and "Do not use" not in desc:
        err(skill, "description without exclusion clause ('Not for'/'Do not use')")
    for target in ARROW_RE.findall(desc):
        if target not in names:
            err(skill, f"description apunta a skill inexistente: {target}")


def check_headings(skill: str, body: str, needs_tools: bool) -> None:
    headings = H2_RE.findall(body)
    for required in REQUIRED_H2:
        if required not in headings:
            err(skill, f"falta H2 '{required}'")
    if needs_tools and "Tools" not in headings:
        err(skill, "missing H2 'Tools' (has executables)")
    for heading in headings:
        if heading in FORBIDDEN_H2 or heading.startswith("Perfil de Este Equipo"):
            err(skill, f"H2 prohibido: {heading}")
    if "sudoers.d" in body:
        err(skill, "SKILL.md no puede documentar sudoers.d")
    # Patrones privados: AUTOWORKSPACE_PRIVATE_PATTERNS (local) o secreto CI HYGIENE_DENYLIST.
    patterns_raw = os.environ.get("AUTOWORKSPACE_PRIVATE_PATTERNS", "").strip()
    for raw in patterns_raw.replace(",", "\n").splitlines():
        pat = raw.strip()
        if not pat:
            continue
        if re.search(pat, body, re.I):
            err(skill, f"SKILL.md coincide con patrón privado configurado ({pat!r})")


def check_residues(root: Path, sdir: Path) -> None:
    skill = sdir.name
    for d in PROHIBITED_DIRS:
        if (sdir / d).is_dir():
            err(skill, f"directorio prohibido: {d}/")
    refs = sdir / "references"
    if refs.is_dir():
        for sub in refs.iterdir():
            if sub.is_dir():
                err(skill, f"references/ contiene subdirectorio: {sub.name}/")
    if list(sdir.glob(".archivado*")):
        err(skill, "contiene .archivado*")
    rel = str(sdir.relative_to(root))
    for tracked in git_ls_files(root, rel):
        name = Path(tracked).name
        if name in {"LICENSE", "LICENSE.txt"}:
            err(skill, f"fichero {name} por skill (licencia global)")
        if name == "__pycache__" or tracked.endswith(".pyc") or "/__pycache__/" in tracked:
            err(skill, f"residuo rastreado: {tracked}")
        if ".pytest_cache" in tracked:
            err(skill, f"residuo rastreado: {tracked}")


def check_smoke(sdir: Path) -> None:
    skill = sdir.name
    smoke = sdir / "scripts" / "tests" / "smoke_sh.sh"
    has_scripts = has_exec_scripts(sdir)
    if has_scripts and not smoke.is_file():
        err(skill, "falta scripts/tests/smoke_sh.sh (hay ejecutables)")
    if smoke.is_file() and not has_scripts:
        err(skill, "smoke presente sin ejecutables fuera de tests/")


def check_upstash_modes(sdir: Path) -> None:
    modes = sdir / "modes"
    if not modes.is_dir():
        return
    for mode in modes.iterdir():
        if not mode.is_dir():
            continue
        refs = mode / "references"
        if not refs.is_dir():
            continue
        for sub in refs.iterdir():
            if sub.is_dir():
                err(sdir.name, f"modes/{mode.name}/references/ contiene subdirectorio: {sub.name}/")


def check_skill(root: Path, sdir: Path, names: set[str]) -> None:
    skill = sdir.name
    f = sdir / "SKILL.md"
    if not f.is_file():
        err(skill, "falta SKILL.md")
        return
    text = f.read_text(encoding="utf-8")
    fm = parse_frontmatter(text, skill)
    if fm is None:
        return

    name = fm.get("name", "")
    if name != skill:
        err(skill, f"name '{name}' != carpeta '{skill}'")
    if not NAME_RE.match(str(name)) or len(str(name)) > 64:
        err(skill, f"name inválido: '{name}'")

    desc = fm.get("description", "")
    if not isinstance(desc, str):
        err(skill, "description debe ser string")
        desc = ""
    check_description(skill, desc, names)

    if fm.get("license") != "MIT":
        err(skill, "license != MIT")

    meta = fm.get("metadata", {})
    if not isinstance(meta, dict):
        err(skill, "metadata debe ser un dict")
        return

    required_meta = {
        "author": None,
        "version": None,
        "domain": None,
        "type": None,
        "language": "en",
    }
    for key, expected in required_meta.items():
        if key not in meta:
            err(skill, f"metadata sin '{key}'")
        elif expected is not None and meta[key] != expected:
            err(skill, f"metadata.{key}='{meta[key]}' expected '{expected}'")

    ver = meta.get("version", "")
    if ver and not SEMVER_RE.match(str(ver)):
        err(skill, f"version no semver X.Y.Z: '{ver}'")

    dom = meta.get("domain", "")
    if dom and dom not in DOMINIOS:
        err(skill, f"unknown domain: {dom}")

    tipo = meta.get("type", "")
    if tipo and tipo not in TIPOS:
        err(skill, f"unknown type: {tipo} (must be one of: {', '.join(sorted(TIPOS))})")

    body = text.split("\n---", 1)[-1]
    body_lines = len(body.splitlines())
    if body_lines > MAX_BODY_LINES:
        err(skill, f"cuerpo {body_lines} líneas (> {MAX_BODY_LINES})")
    body_tokens = estimate_tokens(body)
    if body_tokens > MAX_BODY_TOKENS:
        err(skill, f"cuerpo ~{body_tokens} tokens (> {MAX_BODY_TOKENS})")

    needs_tools = has_exec_scripts(sdir)
    check_headings(skill, body, needs_tools)
    check_residues(root, sdir)
    check_smoke(sdir)
    check_upstash_modes(sdir)


def main() -> int:
    root = ROOT
    if not SKILLS.is_dir():
        print(f"no existe {SKILLS}")
        return 1
    sdirs = skill_dirs(root)
    names = {p.name for p in sdirs}
    check_catalog(root, names)
    for s in sdirs:
        check_skill(root, s, names)
    print(f"skills: {len(sdirs)}, errores: {len(ERRORS)}")
    for e in ERRORS:
        print("FAIL", e)
    print("SPEC:", "OK" if not ERRORS else "CON-FALLOS")
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
