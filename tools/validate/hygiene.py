#!/usr/bin/env python3
"""Higiene del árbol: residuos rastreados, secretos y trailing whitespace.

Uso: python3 tools/validate/hygiene.py [--root DIR]
Exit 0 si limpio; 1 si hay fallos o la inspección no pudo completarse.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Literal, NamedTuple

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
ENUM_TIMEOUT_SEC = 60.0

Outcome = Literal["clear", "match", "error"]

ERRORS: list[str] = []


class EnumResult(NamedTuple):
    status: Literal["ok", "error"]
    files: list[str]
    reason: str = ""


def _is_git_repo(root: Path) -> bool:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=ENUM_TIMEOUT_SEC,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0 and r.stdout.strip() == "true"


def enumerate_tracked(root: Path, *, timeout: float = ENUM_TIMEOUT_SEC) -> EnumResult:
    """Lista tracked con git ls-files -z. Error => no limpio."""
    reason = ""
    if not _is_git_repo(root):
        reason = "raiz no es un repositorio Git"
    else:
        try:
            r = subprocess.run(
                ["git", "ls-files", "-z"],
                cwd=root,
                capture_output=True,
                check=False,
                timeout=timeout,
            )
        except FileNotFoundError:
            reason = "git ausente"
        except OSError as exc:
            reason = f"git no ejecutable: {type(exc).__name__}"
        except subprocess.TimeoutExpired:
            reason = "timeout enumerando tracked"
        else:
            if r.returncode != 0:
                reason = f"git ls-files rc={r.returncode}"
            else:
                try:
                    raw = r.stdout.decode("utf-8")
                except UnicodeDecodeError:
                    reason = "salida de git ls-files no UTF-8"
                else:
                    return EnumResult(status="ok", files=[p for p in raw.split("\0") if p])
    return EnumResult(status="error", files=[], reason=reason)


def _is_fixture_path(rel: str) -> bool:
    parts = Path(rel.replace("\\", "/")).parts
    return "fixtures" in parts or "testdata" in parts


def _read_capped(path: Path, max_bytes: int) -> tuple[Literal["ok", "error"], bytes, str]:
    """Lee como máximo max_bytes+1 para distinguir exacto vs exceso sin cargar todo."""
    try:
        with path.open("rb") as handle:
            raw = handle.read(max_bytes + 1)
    except OSError as exc:
        return "error", b"", f"lectura fallida: {type(exc).__name__}"
    if len(raw) > max_bytes:
        return "error", b"", "archivo supera presupuesto de inspección"
    return "ok", raw, ""


def _inspect_host_audit_json(path: Path) -> tuple[Outcome, str]:
    """CLEAR / MATCH / ERROR sin devolver ni imprimir contenido del informe."""
    outcome: Outcome = "clear"
    detail = ""
    if path.is_symlink():
        outcome, detail = "error", "symlink no inspeccionable"
    elif not path.is_file():
        outcome, detail = "error", "tipo no inspeccionable"
    else:
        status, raw, reason = _read_capped(path, HOST_AUDIT_MAX_BYTES)
        if status == "error":
            outcome, detail = "error", reason
        else:
            try:
                data = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                data = None
            if isinstance(data, dict) and HOST_AUDIT_TOP_KEYS.issubset(data.keys()):
                meta = data.get("metadata")
                if isinstance(meta, dict) and "hostname" in meta and "kernel" in meta:
                    outcome = "match"
    return outcome, detail


def check_host_reports(root: Path, tracked: list[str]) -> Outcome:
    """Rechaza informes reales / manifiestos de taller rastreados.

    Los mensajes solo incluyen la ruta relativa. Nunca el contenido detectado.
    """
    worst: Outcome = "clear"
    for rel in tracked:
        norm = rel.replace("\\", "/")
        name = Path(norm).name
        if name == "repos-taller.tsv" and not _is_fixture_path(norm):
            ERRORS.append(f"informe de host rastreado: {rel}")
            worst = "match"
            continue
        if AUDIT_QUICK_NAME.match(name) and not _is_fixture_path(norm):
            ERRORS.append(f"informe de host rastreado: {rel}")
            worst = "match"
            continue
        if not norm.endswith(".json") or _is_fixture_path(norm):
            continue
        if "skills/" not in norm and "tools/" not in norm:
            continue
        full = root / rel
        outcome, detail = _inspect_host_audit_json(full)
        if outcome == "match":
            ERRORS.append(f"informe de host rastreado: {rel}")
            worst = "match"
        elif outcome == "error":
            ERRORS.append(f"ERROR inspeccionable: {rel}: {detail}")
            worst = "error"
    return worst


def check_tracked(tracked: list[str]) -> Outcome:
    worst: Outcome = "clear"
    for rel in tracked:
        path = Path(rel)
        if path.name in RESIDUE_NAMES or path.suffix in RESIDUE_SUFFIXES:
            ERRORS.append(f"residuo rastreado: {rel}")
            worst = "match"
        if path.name.startswith(".archivado"):
            ERRORS.append(f"residuo rastreado: {rel}")
            worst = "match"
        # *.example (p. ej. .env.example) es plantilla versionada, no secreto.
        if path.suffix == ".example":
            continue
        if path.name == ".env" or path.name.startswith(".env.") or path.suffix in SECRET_NAMES:
            ERRORS.append(f"secreto rastreado: {rel}")
            worst = "match"
    return worst


def iter_text_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if path.is_symlink():
            continue
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix in TEXT_SUFFIXES or path.name in {"run-validation.sh"}:
            yield path


def check_trailing(root: Path) -> Outcome:
    worst: Outcome = "clear"
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
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                ERRORS.append(f"ERROR lectura trailing: {rel}: {type(exc).__name__}")
                return "error"
            for i, line in enumerate(text.splitlines(), 1):
                if line.endswith(" ") or line.endswith("\t"):
                    ERRORS.append(f"trailing whitespace {rel}:{i}")
                    worst = "match"
                    break
    return worst


def run_hygiene(root: Path) -> int:
    """Ejecuta controles; limpia estado entre invocaciones (H19)."""
    ERRORS.clear()
    enumerated = enumerate_tracked(root)
    if enumerated.status == "error":
        ERRORS.append(f"ERROR enumeracion: {enumerated.reason}")
        print(f"errores: {len(ERRORS)}")
        for e in ERRORS:
            print("FAIL", e)
        print("HYGIENE: CON-FALLOS")
        return 1
    tracked = enumerated.files
    check_tracked(tracked)
    check_host_reports(root, tracked)
    check_trailing(root)
    print(f"errores: {len(ERRORS)}")
    for e in ERRORS:
        print("FAIL", e)
    print("HYGIENE:", "OK" if not ERRORS else "CON-FALLOS")
    return 1 if ERRORS else 0


def main() -> int:
    return run_hygiene(ROOT)


if __name__ == "__main__":
    sys.exit(main())
