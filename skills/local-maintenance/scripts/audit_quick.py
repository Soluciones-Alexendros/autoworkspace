#!/usr/bin/env python3
"""audit_quick.py - Health-check read-only (higiene/updates, subconjunto P0+P1).

Subconjunto de mantenimiento: PKG-01/03/05/07, FS-10, LOG-06, SRV-02, NET-04.
El hardening puro (SSH/KR/FS-05-08/AU/UA/CR) vive en local-security y NO se
verifica aqui. Los checks compartidos estan en common.py.
Uso: audit_quick.py [output-file] [profile-file]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time

from common import (
    BLUE,
    FindingCollector,
    check_fs_10_disk,
    check_log_06,
    check_net_04,
    check_pkg_01,
    check_pkg_03,
    check_pkg_05,
    check_pkg_07,
    check_srv_02,
    color,
    load_profile_family,
    run,
)

logger = logging.getLogger("mantenimiento.audit_quick")


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s", stream=sys.stderr)
    else:
        logging.getLogger().setLevel(level)


log_tag = color("[AUDIT-QUICK]", BLUE)


def run_check(cmd: str, timeout: int = 10) -> str:
    return run(cmd, timeout=timeout)


def sshd_value(key: str) -> str:
    """Compat: retained for tests/callers; hardening SSH vive en local-security."""
    out = run(f"sshd -T 2>/dev/null | grep '^{key} ' | awk '{{print $2}}'", timeout=10)
    return out.strip()


def run_quick_checks(collector: FindingCollector, pkg_mgr: str, runner=None) -> str:
    """Ejecuta la fase rapida (8 checks higiene) y devuelve running_kernel."""
    r = runner if runner is not None else run_check
    print(f"{log_tag} Verificando actualizaciones de seguridad...")
    check_pkg_01(collector, pkg_mgr, runner=r)
    print(f"{log_tag} Verificando kernel running vs installed...")
    running_kernel = check_pkg_03(collector, pkg_mgr, runner=r)
    print(f"{log_tag} Verificando paquetes huerfanos...")
    check_pkg_05(collector, pkg_mgr, runner=r)
    print(f"{log_tag} Verificando archivos de configuracion pendientes...")
    check_pkg_07(collector, pkg_mgr, runner=r)
    print(f"{log_tag} Verificando exposicion SSH...")
    check_net_04(collector, runner=r)
    print(f"{log_tag} Verificando uso de disco...")
    check_fs_10_disk(collector, runner=r)
    print(f"{log_tag} Verificando errores en journal...")
    check_log_06(collector, runner=r)
    print(f"{log_tag} Verificando servicios fallidos...")
    check_srv_02(collector, runner=r)
    return running_kernel


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Health-check read-only (higiene/updates P0+P1).")
    parser.add_argument("output_file", nargs="?", default=None, help="Fichero JSON de salida")
    parser.add_argument("profile_file", nargs="?", default="system-profile.json", help="Perfil del sistema")
    parser.add_argument("--verbose", action="store_true", help="Logging verboso a stderr")
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    output_file = args.output_file or f"audit-quick-{time.strftime('%Y%m%d-%H%M%S')}.json"
    profile_file = args.profile_file

    try:
        distro_family, pkg_mgr, distro_id, version_id, version_codename = load_profile_family(profile_file)
    except (OSError, ValueError) as exc:
        logger.error("no se pudo cargar perfil %r: %s", profile_file, exc)
        return 1

    collector = FindingCollector()

    print(f"{log_tag} Iniciando auditoria rapida (higiene/updates P0+P1)...")
    start_time = time.time()

    running_kernel = run_quick_checks(collector, pkg_mgr, runner=run_check)

    duration = int(time.time() - start_time)

    try:
        output = collector.build_output(
            "audit-quick", distro_id, distro_family, running_kernel, duration, version_id, version_codename
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
    print(f"{log_tag} Auditoria rapida completada en {duration}s")
    print(
        f"{log_tag} Health Score: {hs['overall']} (Security: {hs['security']}, Updates: {hs['updates']}, Hygiene: {hs['hygiene']}, Resources: {hs['resources']}, Stability: {hs['stability']})"
    )
    print(
        f"{log_tag} Resultados: {collector.passed} passed, {collector.failed} failed, {collector.warned} warned, {collector.skipped} skipped, {collector.errors} errors"
    )
    print(f"{log_tag} Guardado en: {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
