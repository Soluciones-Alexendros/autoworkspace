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
BROKEN: list[str] = []


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
    print(f"md revisados: {len(mds)}, rotos: {len(BROKEN)}")
    for b in BROKEN:
        print("BROKEN", b)
    print("LINKS:", "OK" if not BROKEN else "CON-FALLOS")
    return 1 if BROKEN else 0


if __name__ == "__main__":
    sys.exit(main())
