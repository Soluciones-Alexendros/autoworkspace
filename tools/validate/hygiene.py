#!/usr/bin/env python3
"""Higiene del árbol: residuos rastreados, secretos y trailing whitespace.

Uso: python3 tools/validate/hygiene.py [--root DIR]
Exit 0 si limpio; 1 si hay fallos.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(sys.argv[sys.argv.index("--root") + 1]) if "--root" in sys.argv else Path(__file__).resolve().parents[2]
RESIDUE_NAMES = {"__pycache__", ".pytest_cache"}
RESIDUE_SUFFIXES = {".pyc", ".tmp", ".bak", ".log"}
SECRET_NAMES = {".env", ".pem", ".key"}
TEXT_SUFFIXES = {".md", ".py", ".sh", ".yml", ".yaml", ".json", ".toml"}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv"}
ERRORS: list[str] = []


def tracked_files(root: Path) -> list[str]:
    try:
        r = subprocess.run(
            ["git", "ls-files"],
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


def check_tracked(root: Path) -> None:
    for rel in tracked_files(root):
        path = Path(rel)
        if path.name in RESIDUE_NAMES or path.suffix in RESIDUE_SUFFIXES:
            ERRORS.append(f"residuo rastreado: {rel}")
        if path.name.startswith(".archivado"):
            ERRORS.append(f"residuo rastreado: {rel}")
        # *.example (p. ej. .env.example) es plantilla versionada, no secreto.
        if path.suffix == ".example":
            continue
        if path.name == ".env" or path.name.startswith(".env.") or path.suffix in SECRET_NAMES:
            ERRORS.append(f"secreto rastreado: {rel}")


def iter_text_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix in TEXT_SUFFIXES or path.name in {"run-validation.sh"}:
            yield path


def check_trailing(root: Path) -> None:
    for path in iter_text_files(root):
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if (
            str(rel).startswith("skills/")
            or str(rel).startswith("tools/")
            or str(rel).startswith("docs/")
            or str(rel).startswith(".github/")
            or path.name == "run-validation.sh"
        ):
            for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if line.endswith(" ") or line.endswith("\t"):
                    ERRORS.append(f"trailing whitespace {rel}:{i}")
                    break


def main() -> int:
    check_tracked(ROOT)
    check_trailing(ROOT)
    print(f"errores: {len(ERRORS)}")
    for e in ERRORS:
        print("FAIL", e)
    print("HYGIENE:", "OK" if not ERRORS else "CON-FALLOS")
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
