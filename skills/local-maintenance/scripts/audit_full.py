#!/usr/bin/env python3

"""audit_full.py - Auditoria completa de higiene/updates (P0-P4).

Fase 1: reutiliza audit_quick.run_quick_checks (PKG-01/03/05/07, FS-10,
LOG-06, SRV-02, NET-04). Fase 2: checks extendidos de higiene
(PKG-04/06/09, ARC-07, DEB-04, FS-09/11, LOG-08).
El hardening puro (SSH/KR/FS-05-08/AU/UA/CR/FW/SD) vive en local-security
y NO se verifica aqui (ver baseline canonico).
Uso: audit_full.py [output-file] [profile-file]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from collections.abc import Callable
from typing import Any

from audit_quick import run_quick_checks
from common import (
    BLUE,
    FindingCollector,
    check_arc_07,
    check_deb_04,
    check_fs_09,
    check_fs_11_inodes,
    check_log_08,
    check_pkg_04,
    check_pkg_06,
    check_pkg_09,
    color,
    load_profile_family,
    run,
    sshd_effective,
)

MIN_FIELDS = 2

log_tag = color("[AUDIT-FULL]", BLUE)

logger = logging.getLogger("mantenimiento.audit_full")


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s", stream=sys.stderr)
    else:
        logging.getLogger().setLevel(level)


def run_check(cmd: str, timeout: int = 10) -> str:
    return run(cmd, timeout=timeout)


def sshd_eff_get(key: str) -> str:
    """Compat: retained for tests/callers; hardening SSH vive en local-security."""
    for line in sshd_effective().splitlines():
        parts = line.split()
        if parts and parts[0].lower() == key and len(parts) >= MIN_FIELDS:
            return parts[1]
    return ""


def run_extended_checks(collector: FindingCollector, pkg_mgr: str, runner: Callable[..., Any] | None = None) -> None:
    """Fase 2: controles extendidos de higiene (solo audit_full)."""
    r = runner if runner is not None else run_check
    print(f"{log_tag} Fase 2: Controles extendidos de higiene (P2-P4)...")
    print(f"{log_tag} Verificando symlinks rotos...")
    check_fs_09(collector, runner=r)
    print(f"{log_tag} Verificando uso de inodos...")
    check_fs_11_inodes(collector, runner=r)
    print(f"{log_tag} Verificando fallos de arranque...")
    check_log_08(collector, runner=r)
    print(f"{log_tag} Verificando paquetes foraneos...")
    check_pkg_06(collector, pkg_mgr, runner=r)
    print(f"{log_tag} Verificando tamano de cache...")
    check_pkg_09(collector, pkg_mgr, runner=r)
    print(f"{log_tag} Verificando firmware...")
    check_pkg_04(collector, runner=r)
    print(f"{log_tag} Verificando actualizaciones parciales...")
    check_arc_07(collector, pkg_mgr, runner=r)
    if pkg_mgr == "apt":
        print(f"{log_tag} Verificando unattended-upgrades...")
        check_deb_04(collector, pkg_mgr, runner=r)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Auditoria completa de higiene/updates (P0-P4).")
    parser.add_argument("output_file", nargs="?", default=None, help="Fichero JSON de salida")
    parser.add_argument("profile_file", nargs="?", default="system-profile.json", help="Perfil del sistema")
    parser.add_argument("--verbose", action="store_true", help="Logging verboso a stderr")
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    output_file = args.output_file or f"audit-full-{time.strftime('%Y%m%d-%H%M%S')}.json"
    profile_file = args.profile_file

    try:
        distro_family, pkg_mgr, distro_id, version_id, version_codename = load_profile_family(profile_file)
    except (OSError, ValueError) as exc:
        logger.error("no se pudo cargar perfil %r: %s", profile_file, exc)
        return 1

    collector = FindingCollector()

    print(f"{log_tag} Fase 1: Controles rapidos (higiene P0+P1)...")
    start_time = time.time()

    running_kernel = run_quick_checks(collector, pkg_mgr, runner=run_check)
    run_extended_checks(collector, pkg_mgr, runner=run_check)

    duration = int(time.time() - start_time)

    try:
        output = collector.build_output(
            "audit-full", distro_id, distro_family, running_kernel, duration, version_id, version_codename
        )
    except (ValueError, TypeError, OSError) as exc:
        logger.error("no se pudo construir salida de auditoria: %s", exc)
        return 1
    try:
        with open(output_file, "w", encoding="utf-8") as fh:
            json.dump(output, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    except (OSError, TypeError, ValueError) as exc:
        logger.error("no se pudo escribir %r: %s", output_file, exc)
        print(f"Error: no se pudo escribir {output_file}: {exc}", file=sys.stderr)
        return 1

    hs = output["health_score"]
    print(f"{log_tag} Auditoria completada en {duration}s")
    print(
        f"{log_tag} Health Score: {hs['overall']} "
        f"(Security: {hs['security']}, Updates: {hs['updates']}, "
        f"Hygiene: {hs['hygiene']}, Resources: {hs['resources']}, "
        f"Stability: {hs['stability']})"
    )
    print(
        f"{log_tag} Resultados: {collector.passed} passed, "
        f"{collector.failed} failed, {collector.warned} warned, "
        f"{collector.skipped} skipped, {collector.errors} errors"
    )
    print(f"{log_tag} Guardado en: {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
