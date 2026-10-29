#!/usr/bin/env python3
"""Control privado de patrones (denylist) fail-closed y sin filtraciones.

Lee patrones desde AUTOWORKSPACE_PRIVATE_PATTERNS (o HYGIENE_DENYLIST como alias
de entrada). Nunca imprime patrones, valores coincidentes ni rutas del hallazgo.

Uso: python3 tools/validate/private_denylist.py [--root DIR]
Exit 0: CLEAR (inspección sin coincidencias) o NOT_RUN (config ausente/vacía).
Exit 1: REGEX_INVALID, errores de escaneo, timeout o DENYLIST_MATCH.
"""

from __future__ import annotations

import importlib.util
import os
import re
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal, cast

ROOT = Path(sys.argv[sys.argv.index("--root") + 1]) if "--root" in sys.argv else Path(__file__).resolve().parents[2]


def _load_enumerate_tracked() -> Callable[..., Any]:
    """Carga enumerate_tracked desde hygiene.py sin depender del PYTHONPATH."""
    path = Path(__file__).resolve().parent / "hygiene.py"
    spec = importlib.util.spec_from_file_location("_aw_hygiene_enum", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("no se pudo cargar hygiene.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_aw_hygiene_enum"] = mod
    spec.loader.exec_module(mod)
    return cast(Callable[..., Any], mod.enumerate_tracked)


enumerate_tracked = _load_enumerate_tracked()
ENV_KEYS = ("AUTOWORKSPACE_PRIVATE_PATTERNS", "HYGIENE_DENYLIST")
FILE_READ_MAX = 1_000_000
SCAN_TIMEOUT_SEC = 60.0
# Cap de complejidad: re DIGIT_LIMIT + timeout de motor no disponible de forma
# portable; limitamos longitud del patrón y usamos búsqueda lineal por archivo.
PATTERN_MAX_LEN = 512

ConfigReason = Literal["CONFIG_MISSING", "CONFIG_EMPTY"]
Code = Literal[
    "CONFIG_MISSING",
    "CONFIG_EMPTY",
    "NOT_RUN",
    "REGEX_INVALID",
    "ENUM_ERROR",
    "READ_ERROR",
    "TIMEOUT",
    "DENYLIST_MATCH",
    "CLEAR",
]


def _emit(code: Code) -> None:
    # Mensaje genérico: código estable, sin patrones ni rutas.
    print(f"private_denylist: {code}")


def _emit_not_run(reason: ConfigReason) -> int:
    """Config ausente/vacía: omitir inspección (not_run), nunca fail el job."""
    _emit("NOT_RUN")
    print(f"private_denylist: WARN not_run ({reason})", file=sys.stderr)
    return 0


def _load_raw_config() -> tuple[str | None, ConfigReason | None]:
    found = False
    for key in ENV_KEYS:
        if key in os.environ:
            found = True
            raw = os.environ.get(key)
            if raw is None:
                continue
            return raw, None
    if not found:
        return None, "CONFIG_MISSING"
    return "", None


def _parse_patterns(raw: str) -> tuple[list[re.Pattern[str]] | None, Code | None]:
    lines = [ln.strip() for ln in raw.replace(",", "\n").splitlines()]
    lines = [ln for ln in lines if ln]
    if not lines:
        return None, "CONFIG_EMPTY"
    compiled: list[re.Pattern[str]] = []
    for line in lines:
        if len(line) > PATTERN_MAX_LEN:
            return None, "REGEX_INVALID"
        try:
            compiled.append(re.compile(line))
        except re.error:
            return None, "REGEX_INVALID"
    return compiled, None


def _scan_files(root: Path, files: list[str], patterns: list[re.Pattern[str]]) -> Code:
    deadline = time.monotonic() + SCAN_TIMEOUT_SEC
    for rel in files:
        if time.monotonic() > deadline:
            return "TIMEOUT"
        path = root / rel
        if path.is_symlink() or not path.is_file():
            continue
        try:
            with path.open("rb") as handle:
                raw = handle.read(FILE_READ_MAX + 1)
        except OSError:
            return "READ_ERROR"
        if len(raw) > FILE_READ_MAX:
            # Archivo grande: escanear solo el prefijo acotado; no declarar CLEAR
            # sobre el resto no leído — error de límite.
            return "READ_ERROR"
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        for pat in patterns:
            if time.monotonic() > deadline:
                return "TIMEOUT"
            if pat.search(text):
                return "DENYLIST_MATCH"
    return "CLEAR"


def main_with_root(root: Path) -> int:
    raw, cfg_err = _load_raw_config()
    if cfg_err is None and raw is not None and raw.strip() == "":
        cfg_err = "CONFIG_EMPTY"
    if cfg_err is not None:
        return _emit_not_run(cfg_err)
    assert raw is not None
    patterns, perr = _parse_patterns(raw)
    if perr is not None:
        if perr == "CONFIG_EMPTY":
            return _emit_not_run("CONFIG_EMPTY")
        _emit(perr)
        return 1
    assert patterns is not None
    enumerated = enumerate_tracked(root)
    if enumerated.status == "error":
        _emit("ENUM_ERROR")
        return 1
    code = _scan_files(root, enumerated.files, patterns)
    if code != "CLEAR":
        _emit(code)
        return 1
    _emit("CLEAR")
    print("DENYLIST: CLEAR")
    return 0


def main() -> int:
    return main_with_root(ROOT)


if __name__ == "__main__":
    sys.exit(main())
