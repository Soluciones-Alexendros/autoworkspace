#!/usr/bin/env python3
"""Higiene del árbol: residuos rastreados, secretos y trailing whitespace.

Uso: python3 tools/validate/hygiene.py [--root DIR]
Exit 0 si limpio; 1 si hay fallos.
"""

from __future__ import annotations

import json
import re
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
# audit-quick-<YYYYMMDD>-<HHMMSS>.json: salida real de local-maintenance.
AUDIT_QUICK_NAME = re.compile(r"^audit-quick-\d{8}-\d{6}\.json$")
HOST_AUDIT_TOP_KEYS = frozenset({"metadata", "health_score", "findings", "summary"})
HOST_AUDIT_MAX_BYTES = 2_000_000
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


def _is_fixture_path(rel: str) -> bool:
    parts = Path(rel.replace("\\", "/")).parts
    return "fixtures" in parts or "testdata" in parts


def _looks_like_host_audit_json(path: Path) -> bool:
    """Detecta esquema de informe real sin devolver ni imprimir valores."""
    try:
        raw = path.read_bytes()
    except OSError:
        return False
    if len(raw) > HOST_AUDIT_MAX_BYTES:
        return False
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(data, dict) or not HOST_AUDIT_TOP_KEYS.issubset(data.keys()):
        return False
    meta = data.get("metadata")
    # Claves típicas de auditoría de host; no se leen los valores.
    return isinstance(meta, dict) and "hostname" in meta and "kernel" in meta


def check_host_reports(root: Path) -> None:
    """Rechaza informes reales / manifiestos de taller rastreados.

    Los mensajes solo incluyen la ruta relativa. Nunca el contenido detectado.
    """
    for rel in tracked_files(root):
        norm = rel.replace("\\", "/")
        name = Path(norm).name
        if name == "repos-taller.tsv" and not _is_fixture_path(norm):
            ERRORS.append(f"informe de host rastreado: {rel}")
            continue
        if AUDIT_QUICK_NAME.match(name) and not _is_fixture_path(norm):
            ERRORS.append(f"informe de host rastreado: {rel}")
            continue
        if not norm.endswith(".json") or _is_fixture_path(norm):
            continue
        if "skills/" not in norm and "tools/" not in norm:
            continue
        full = root / rel
        if full.is_file() and _looks_like_host_audit_json(full):
            ERRORS.append(f"informe de host rastreado: {rel}")


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
    check_host_reports(ROOT)
    check_trailing(ROOT)
    print(f"errores: {len(ERRORS)}")
    for e in ERRORS:
        print("FAIL", e)
    print("HYGIENE:", "OK" if not ERRORS else "CON-FALLOS")
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
