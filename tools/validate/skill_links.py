#!/usr/bin/env python3
"""Validador de enlaces relativos y de terminología en el repo.

Uso: python3 tools/validate/skill_links.py [--root DIR]
Comprueba que todo enlace relativo [t](ruta) apunte a un fichero existente
(ignora URLs http/https, anclas puras y enlaces externos declarados).
Cubre: skills/, docs/, .github/, tools/, README.md y CHANGELOG.md.
Después aplica el glosario: lee el bloque máquina de docs/GLOSARIO.md y
rechaza los términos prohibidos en los textos vivos.
Exit 0 sin rotos ni términos prohibidos; 1 en caso contrario.
"""

import fnmatch
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[sys.argv.index("--root") + 1]) if "--root" in sys.argv else Path(__file__).resolve().parents[2]
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
ADR_CITE_RE = re.compile(
    r"\bADR-(\d{4})\b(?:\s+[«\"]?([A-Za-z][A-Za-z /-]{2,40}))?",
)
BROKEN: list[str] = []
ADR_STATUS_ERRORS: list[str] = []
TERM_ERRORS: list[str] = []

GLOSSARY_REL = "docs/GLOSARIO.md"
TERM_SUFFIXES = {".md", ".yml", ".yaml", ".json"}
TERM_SCAN_DIRS = ("docs", "templates", "stacks", ".github")
TERM_SCAN_ROOT = (
    "README.md",
    "AGENTS.md",
    "ARCHITECTURE.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
)
TERM_OK_RE = re.compile(r"<!--\s*term-ok:")
TERM_SKIP_PARTS = {".git", "__pycache__", "node_modules", ".cache"}


def load_terminology(root: Path) -> list[dict[str, object]]:
    """Read the machine block of docs/GLOSARIO.md (```json ... ```)."""
    glossary = root / GLOSSARY_REL
    if not glossary.is_file():
        return []
    text = glossary.read_text(encoding="utf-8")
    for m in re.finditer(r"```json\n(.*?)\n```", text, re.S):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and isinstance(data.get("forbidden"), list):
            return [e for e in data["forbidden"] if isinstance(e, dict)]
    return []


def _allowed(rel: str, allow_paths: object) -> bool:
    if not isinstance(allow_paths, list):
        return False
    return any(isinstance(p, str) and fnmatch.fnmatch(rel, p) for p in allow_paths)


def _term_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for name in TERM_SCAN_ROOT:
        path = root / name
        if path.is_file():
            files.append(path)
    for dirname in TERM_SCAN_DIRS:
        base = root / dirname
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix in TERM_SUFFIXES:
                files.append(path)
    out: list[Path] = []
    for path in files:
        if TERM_SKIP_PARTS & set(path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        if rel == GLOSSARY_REL:
            continue
        out.append(path)
    return out


def check_terminology(root: Path) -> None:
    """Reject the glossary's forbidden patterns in live texts."""
    entries = load_terminology(root)
    if not entries:
        return
    compiled: list[tuple[re.Pattern[str], str, object]] = []
    for entry in entries:
        pattern = entry.get("pattern")
        use = entry.get("use")
        if not isinstance(pattern, str) or not isinstance(use, str):
            continue
        compiled.append((re.compile(pattern), use, entry.get("allow_paths")))
    for path in _term_files(root):
        rel = path.relative_to(root).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(lines, 1):
            if TERM_OK_RE.search(line):
                continue
            for regex, use, allow_paths in compiled:
                if _allowed(rel, allow_paths):
                    continue
                for m in regex.finditer(line):
                    TERM_ERRORS.append(f"{rel}:{i}: '{m.group(0)}' → usa '{use}'")


def load_adr_status(root: Path) -> dict[str, tuple[Path, str]]:
    """Map ADR-NNNN → (path, normalized status from file)."""
    out: dict[str, tuple[Path, str]] = {}
    dec = root / "docs" / "architecture" / "decisions"
    if not dec.is_dir():
        return out
    for path in sorted(dec.glob("ADR-*.md")):
        text = path.read_text(encoding="utf-8")
        m_id = re.search(r"adr_id:\s*\"?(ADR-\d{4})\"?", text)
        adr_id = m_id.group(1) if m_id else path.name.split("-")[0] + "-" + path.name.split("-")[1]
        if not adr_id.startswith("ADR-"):
            m_name = re.match(r"(ADR-\d{4})", path.name)
            adr_id = m_name.group(1) if m_name else path.stem
        status = ""
        m_fm = re.search(r'(?m)^status:\s*"([^"]+)"', text)
        if m_fm:
            status = m_fm.group(1)
        else:
            m_body = re.search(r"(?m)^\*\*Estado:\*\*\s*(.+)$", text)
            if m_body:
                status = m_body.group(1).strip()
        out[adr_id] = (path, status)
    return out


def normalize_status_token(s: str) -> str:
    s = s.strip().lower()
    for token in ("accepted", "proposed", "superseded", "deprecated"):
        if token in s:
            return token
    return s.split()[0] if s else ""


def check_adr_citations(root: Path) -> None:
    """Skills must not cite missing ADRs or a status that disagrees with the ADR file."""
    catalog = load_adr_status(root)
    skills = root / "skills"
    if not skills.is_dir():
        return
    for md in sorted(skills.rglob("*.md")):
        if any(p in md.parts for p in (".git", "__pycache__", "node_modules")):
            continue
        for i, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            for m in ADR_CITE_RE.finditer(line):
                num = m.group(1)
                adr_id = f"ADR-{num}"
                cited_status = m.group(2)
                if adr_id not in catalog:
                    ADR_STATUS_ERRORS.append(
                        f"{md.relative_to(root)}:{i}: cita {adr_id} inexistente en docs/architecture/decisions/"
                    )
                    continue
                if not cited_status:
                    continue
                # Ignore prose that is not a status word (e.g. "ADR-0006 reviews")
                norm_cite = normalize_status_token(cited_status)
                if norm_cite not in {"accepted", "proposed", "superseded", "deprecated"}:
                    continue
                _path, file_status = catalog[adr_id]
                norm_file = normalize_status_token(file_status)
                if norm_cite != norm_file and norm_cite not in file_status.lower():
                    ADR_STATUS_ERRORS.append(
                        f"{md.relative_to(root)}:{i}: {adr_id} citado como «{cited_status.strip()}» "
                        f"pero el fichero declara «{file_status}»"
                    )


def check_md(md: Path) -> None:
    in_fence = False
    for i, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue  # enlaces de ejemplo dentro de bloques de código
        line = re.sub(r"`[^`]*`", "", line)  # ignorar `código inline` de ejemplo
        for m in LINK_RE.finditer(line):
            target = m.group(1).strip()
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = target.split("#")[0]
            if not target:
                continue
            if not (md.parent / target).exists():
                BROKEN.append(f"{md.relative_to(ROOT)}:{i} -> {target}")


def main() -> int:
    mds = sorted(
        p
        for p in ROOT.rglob("*.md")
        if ".git" not in p.parts
        and "__pycache__" not in p.parts
        and ".archivado" not in str(p)
        and "node_modules" not in p.parts
    )
    for md in mds:
        check_md(md)
    check_adr_citations(ROOT)
    check_terminology(ROOT)
    print(f"md revisados: {len(mds)}, rotos: {len(BROKEN)}, adr_citas: {len(ADR_STATUS_ERRORS)}")
    for b in BROKEN:
        print("BROKEN", b)
    for e in ADR_STATUS_ERRORS:
        print("ADR", e)
    print(f"terminología: {len(TERM_ERRORS)} hallazgo(s)")
    for t in TERM_ERRORS:
        print("TERM", t)
    ok = not BROKEN and not ADR_STATUS_ERRORS and not TERM_ERRORS
    print("LINKS:", "OK" if ok else "CON-FALLOS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
