#!/usr/bin/env python3
"""Validador de enlaces relativos y de terminología en el repo.

Uso: python3 tools/validate/skill_links.py [--root DIR]
Comprueba que todo enlace relativo [t](ruta) apunte a un fichero existente
(ignora URLs http/https, anclas puras y enlaces externos declarados).
Cubre: skills/, docs/, .github/, tools/, README.md y CHANGELOG.md.
Después aplica el glosario: lee el bloque máquina de docs/GLOSARIO.md y
rechaza los términos prohibidos en los textos vivos.
Por último valida que todo enlace a github.com de docs/, templates/ y la raíz
tenga un owner del canon o de la lista permitida del script.
Exit 0 sin rotos, términos prohibidos ni owners no permitidos; 1 en caso contrario.
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
TermPatterns = list[tuple["re.Pattern[str]", str, object]]

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

LINK_SCAN_DIRS = ("docs", "templates")
LINK_SUFFIXES = {".md", ".yml", ".yaml"}
GITHUB_URL_RE = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")
ALLOWED_OWNERS = frozenset(
    {
        "Soluciones-Alexendros",
        "Alexendros",
        "tt-a1i",  # Archify: fuentes de diagramas (T5)
        "actions",  # GitHub official actions
        "github",  # github/codeql-action
        "google",  # google/osv-scanner-action
        "astral-sh",  # setup-uv
        "docker",  # docker/* official actions
        "softprops",  # action-gh-release
        "pypa",  # trusted publishing
        "mozilla",  # CODE_OF_CONDUCT: escalera de aplicación
        "apps",  # github.com/apps/<slug>: páginas de GitHub App
    }
)
OWNER_ERRORS: list[str] = []


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


def _compile_terms(entries: list[dict[str, object]]) -> TermPatterns:
    compiled: TermPatterns = []
    for entry in entries:
        pattern = entry.get("pattern")
        use = entry.get("use")
        if isinstance(pattern, str) and isinstance(use, str):
            compiled.append((re.compile(pattern), use, entry.get("allow_paths")))
    return compiled


def _scan_lines(rel: str, lines: list[str], compiled: TermPatterns) -> None:
    for i, line in enumerate(lines, 1):
        if TERM_OK_RE.search(line):
            continue
        for regex, use, allow_paths in compiled:
            if _allowed(rel, allow_paths):
                continue
            for m in regex.finditer(line):
                TERM_ERRORS.append(f"{rel}:{i}: '{m.group(0)}' → usa '{use}'")


def check_terminology(root: Path) -> None:
    """Reject the glossary's forbidden patterns in live texts."""
    compiled = _compile_terms(load_terminology(root))
    if not compiled:
        return
    for path in _term_files(root):
        rel = path.relative_to(root).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        _scan_lines(rel, lines, compiled)


def _link_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for name in TERM_SCAN_ROOT:
        path = root / name
        if path.is_file():
            files.append(path)
    for dirname in LINK_SCAN_DIRS:
        base = root / dirname
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix in LINK_SUFFIXES:
                files.append(path)
    return [p for p in files if not (TERM_SKIP_PARTS & set(p.parts))]


def check_github_owners(root: Path) -> None:
    """Reject github.com links whose owner is outside the fleet allowlist."""
    for path in _link_files(root):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            if TERM_OK_RE.search(line):
                continue
            for m in GITHUB_URL_RE.finditer(line):
                if m.group(1) in ALLOWED_OWNERS:
                    continue
                OWNER_ERRORS.append(f"{rel}:{i}: '{m.group(0)}' → owner no permitido")


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
        stripped = re.sub(r"`[^`]*`", "", line)  # ignorar `código inline` de ejemplo
        for m in LINK_RE.finditer(stripped):
            target = m.group(1).strip()
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = target.split("#")[0]
            if not target:
                continue
            if not (md.parent / target).exists():
                BROKEN.append(f"{md.relative_to(ROOT)}:{i} -> {target}")


def main() -> int:
    mds = sorted(p for p in ROOT.rglob("*.md") if not (TERM_SKIP_PARTS & set(p.parts)) and ".archivado" not in str(p))
    for md in mds:
        check_md(md)
    check_adr_citations(ROOT)
    check_terminology(ROOT)
    check_github_owners(ROOT)
    print(f"md revisados: {len(mds)}, rotos: {len(BROKEN)}, adr_citas: {len(ADR_STATUS_ERRORS)}")
    for b in BROKEN:
        print("BROKEN", b)
    for e in ADR_STATUS_ERRORS:
        print("ADR", e)
    print(f"terminología: {len(TERM_ERRORS)} hallazgo(s)")
    for t in TERM_ERRORS:
        print("TERM", t)
    print(f"owners: {len(OWNER_ERRORS)} hallazgo(s)")
    for o in OWNER_ERRORS:
        print("OWNER", o)
    ok = not BROKEN and not ADR_STATUS_ERRORS and not TERM_ERRORS and not OWNER_ERRORS
    print("LINKS:", "OK" if ok else "CON-FALLOS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
