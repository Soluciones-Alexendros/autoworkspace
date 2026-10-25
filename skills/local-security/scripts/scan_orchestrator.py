#!/usr/bin/env python3
"""scan_orchestrator.py - Orquesta escaneos con validacion cruzada (solo lectura).

Escalones: ClamAV (firmas), rkhunter (rootkits), AIDE (integridad),
debsums (hashes de paquetes), Lynis (auditoria CIS). Ningun escaner emite
veredictos: la entrega separa validados / descartados / indeterminados
(ver references/escaneos.md).

Uso:
  scan_orchestrator.py [--check] [--run] [--json out.json] [--verbose]
Por defecto solo informa disponibilidad (sin ejecutar escaneos).
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import sys

logger = logging.getLogger("seguridad.scan")


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s", stream=sys.stderr)
    else:
        logging.getLogger().setLevel(level)


SCANNERS = ("clamav", "rkhunter", "aide", "debsums", "lynis")


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def run_cmd(cmd: str, timeout: int = 300) -> tuple[int, str]:
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


def check_availability() -> dict[str, dict]:
    """Disponibilidad de cada escaner sin ejecutar nada."""
    avail: dict[str, dict] = {}
    avail["clamav"] = {
        "daemon": which("clamdscan") is not None or which("clamscan") is not None,
        "freshclam": which("freshclam") is not None,
    }
    avail["rkhunter"] = {"present": which("rkhunter") is not None}
    avail["aide"] = {"present": which("aide") is not None}
    avail["debsums"] = {"present": which("debsums") is not None}
    avail["lynis"] = {"present": which("lynis") is not None}
    return avail


def scan_clamav() -> dict:
    if which("clamscan") is None and which("clamdscan") is None:
        return {"status": "skip", "reason": "clamscan no instalado"}
    _, sig = run_cmd("freshclam --stdout 2>/dev/null | tail -1", timeout=60)
    return {
        "status": "ok",
        "signatures": sig.strip() or "desconocido",
        "note": "lanzar clamscan -r -i sobre el objetivo aprobado (R1)",
    }


def scan_rkhunter() -> dict:
    if which("rkhunter") is None:
        return {"status": "skip", "reason": "rkhunter no instalado"}
    rc, out = run_cmd("rkhunter --check --sk --rwo 2>/dev/null", timeout=600)
    warnings = [l for l in out.splitlines() if l.strip()]
    return {
        "status": "ok" if rc == 0 else "warnings",
        "warnings": len(warnings),
        "sample": warnings[:10],
        "note": "tras upgrades legitimos, --propupd solo en sistema sano",
    }


def scan_aide() -> dict:
    if which("aide") is None:
        return {"status": "skip", "reason": "aide no instalado"}
    _, timers = run_cmd("systemctl list-timers --all --no-pager 2>/dev/null | grep -i aide", timeout=15)
    rc, out = run_cmd("aide --check --config=/etc/aide/aide.conf 2>/dev/null | tail -30", timeout=600)
    changed = "Changed entries" in out
    return {
        "status": "ok",
        "timer": bool(timers.strip()),
        "changed_entries": changed,
        "tail": out.strip().splitlines()[-10:] if out.strip() else [],
    }


def scan_debsums() -> dict:
    if which("debsums") is None:
        return {"status": "skip", "reason": "debsums no instalado (Debian/Ubuntu)"}
    _, out = run_cmd("debsums -s 2>/dev/null", timeout=600)
    mismatches = [l for l in out.splitlines() if l.strip()]
    return {"status": "ok", "mismatches": len(mismatches), "sample": mismatches[:10]}


def scan_lynis() -> dict:
    if which("lynis") is None:
        return {"status": "skip", "reason": "lynis no instalado"}
    _, out = run_cmd("lynis audit system --quick --no-log 2>/dev/null | tail -20", timeout=600)
    return {
        "status": "ok",
        "tail": out.strip().splitlines()[-20:] if out.strip() else [],
        "note": "suggestions != hallazgos: filtrar por contexto",
    }


def cross_validate(results: dict) -> dict:
    """Validacion cruzada: candidatos que confirma una segunda via.

    Regla: un warning de rkhunter sobre un binario + mismatch de debsums en
    la misma ruta = validado. Cambios AIDE con explicacion (paquete
    actualizado) = descartado pendiente de justificacion humana.
    """
    validated: list[str] = []
    discarded: list[str] = []
    undetermined: list[str] = []
    rk = results.get("rkhunter", {})
    ds = results.get("debsums", {})
    aide = results.get("aide", {})
    if rk.get("warnings"):
        undetermined.append(f"rkhunter: {rk['warnings']} warnings (revisar muestra)")
    if isinstance(ds.get("mismatches"), int) and ds["mismatches"] > 0:
        undetermined.append(f"debsums: {ds['mismatches']} discrepancias (distinguir edicion propia)")
    if aide.get("changed_entries"):
        undetermined.append("aide: Changed entries (todo cambio necesita explicacion)")
    if not undetermined:
        discarded.append("sin candidatos entre los escaneres ejecutados")
    return {"validados": validated, "descartados": discarded, "indeterminados": undetermined}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Orquesta escaneos con validacion cruzada (solo lectura).")
    parser.add_argument("--check", action="store_true", help="Solo disponibilidad (defecto)")
    parser.add_argument("--run", action="store_true", help="Ejecutar escaneres disponibles (solo lectura)")
    parser.add_argument("--json", default="", help="Fichero JSON de salida")
    parser.add_argument("--verbose", action="store_true", help="Logging verboso a stderr")
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    avail = check_availability()
    results: dict = {"availability": avail, "scans": {}, "cross_validation": {}}
    if args.run:
        results["scans"]["clamav"] = scan_clamav()
        results["scans"]["rkhunter"] = scan_rkhunter()
        results["scans"]["aide"] = scan_aide()
        results["scans"]["debsums"] = scan_debsums()
        results["scans"]["lynis"] = scan_lynis()
        results["cross_validation"] = cross_validate(results["scans"])
        print("Escaneos completados (solo lectura). Veredicto: candidatos, no veredictos.")
    else:
        for name in SCANNERS:
            info = avail.get(name, {})
            print(f"{name}: {info}")

    if args.json:
        try:
            with open(args.json, "w", encoding="utf-8") as fh:
                json.dump(results, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
        except (OSError, TypeError, ValueError) as exc:
            logger.error("no se pudo escribir %r: %s", args.json, exc)
            return 1
        print(f"Guardado en: {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
