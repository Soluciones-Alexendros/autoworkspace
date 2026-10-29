#!/usr/bin/env python3

"""vulns_check.py - Chequeo de vulnerabilidades apt + snap/flatpak (solo lectura).

Fuentes: apt (actualizaciones de seguridad), snap refresh --list,
flatpak actualizaciones. Sin red degrada a solo-informe local con aviso
explicito (no inventa CVEs sin fuente).
Uso: vulns_check.py [--json out.json] [--verbose]
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import sys
from typing import Any

logger = logging.getLogger("seguridad.vulns")


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s", stream=sys.stderr)
    else:
        logging.getLogger().setLevel(level)


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def run_cmd(cmd: str, timeout: int = 120) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            executable="/bin/bash",
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout
    except (subprocess.TimeoutExpired, OSError) as exc:
        logger.warning("comando fallo %r: %s", cmd, exc)
        return 1, ""


def has_network() -> bool:
    _, out = run_cmd("getent hosts security.ubuntu.com 2>/dev/null", timeout=10)
    return bool(out.strip())


def check_apt() -> dict[str, Any]:
    if which("apt") is None:
        return {"status": "skip", "reason": "apt no disponible"}
    _, out = run_cmd("apt list --upgradable 2>/dev/null | grep -vE '^(Listing|Listando)'", timeout=120)
    lines = [ln for ln in out.splitlines() if ln.strip()]
    sec = [ln for ln in lines if "-security" in ln or "security" in ln.lower()]
    return {"status": "ok", "upgradable": len(lines), "security": len(sec), "sample": lines[:10]}


def check_snap() -> dict[str, Any]:
    if which("snap") is None:
        return {"status": "skip", "reason": "snap no instalado"}
    _, out = run_cmd("snap refresh --list 2>/dev/null", timeout=120)
    lines = [ln for ln in out.splitlines() if ln.strip()]
    return {"status": "ok", "pending": max(0, len(lines) - 1) if lines else 0, "sample": lines[:10]}


def check_flatpak() -> dict[str, Any]:
    if which("flatpak") is None:
        return {"status": "skip", "reason": "flatpak no instalado"}
    _, out = run_cmd("flatpak remote-ls --updates 2>/dev/null", timeout=120)
    lines = [ln for ln in out.splitlines() if ln.strip()]
    return {"status": "ok", "pending": len(lines), "sample": lines[:10]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chequeo de vulnerabilidades apt+snap/flatpak (solo lectura).")
    parser.add_argument("--json", default="", help="Fichero JSON de salida")
    parser.add_argument("--verbose", action="store_true", help="Logging verboso a stderr")
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    online = has_network()
    result: dict[str, Any] = {"network": online, "sources": {}}
    if not online:
        logger.warning("sin red: modo degradado, solo informe local")
        print("AVISO: sin red — modo degradado (solo informe local, sin datos de seguridad frescos)")
    result["sources"]["apt"] = check_apt()
    result["sources"]["snap"] = check_snap()
    result["sources"]["flatpak"] = check_flatpak()

    total = sum(
        int(v.get("security", v.get("pending", 0)) or 0) for v in result["sources"].values() if isinstance(v, dict)
    )
    result["summary"] = {"pending_security_signals": total, "degraded": not online}
    print(f"vulns: {total} senales pendientes (degradado={not online})")

    if args.json:
        try:
            with open(args.json, "w", encoding="utf-8") as fh:
                json.dump(result, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
        except (OSError, TypeError, ValueError) as exc:
            logger.error("no se pudo escribir %r: %s", args.json, exc)
            return 1
        print(f"Guardado en: {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
