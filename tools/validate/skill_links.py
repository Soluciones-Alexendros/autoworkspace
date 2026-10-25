#!/usr/bin/env python3
"""Validador de enlaces relativos en todos los .md del repo.

Uso: python3 tools/validate/skill_links.py [--root DIR]
Comprueba que todo enlace relativo [t](ruta) apunte a un fichero existente
(ignora URLs http/https, anclas puras y enlaces externos declarados).
Cubre: skills/, docs/, .github/, tools/, README.md y CHANGELOG.md.
Exit 0 sin rotos; 1 con rotos.
"""
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
        p for p in ROOT.rglob("*.md")
        if ".git" not in p.parts
        and "__pycache__" not in p.parts
        and ".archivado" not in str(p)
        and "node_modules" not in p.parts
    )
    for md in mds:
        check_md(md)
    check_adr_citations(ROOT)
    print(f"md revisados: {len(mds)}, rotos: {len(BROKEN)}, adr_citas: {len(ADR_STATUS_ERRORS)}")
    for b in BROKEN:
        print("BROKEN", b)
    for e in ADR_STATUS_ERRORS:
        print("ADR", e)
    print("LINKS:", "OK" if not BROKEN and not ADR_STATUS_ERRORS else "CON-FALLOS")
    return 1 if BROKEN or ADR_STATUS_ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
