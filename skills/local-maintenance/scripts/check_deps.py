#!/usr/bin/env python3
"""check_deps.py - Verifica dependencias requeridas y opcionales.

Port Python de check_deps.sh. Uso: check_deps.py [--verbose] [--install-hint]
"""

from __future__ import annotations

import argparse
import logging
import sys

from common import GREEN, RED, YELLOW, color, which

logger = logging.getLogger("mantenimiento.check_deps")


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s", stream=sys.stderr)
    else:
        logging.getLogger().setLevel(level)


REQUIRED = [
    ("timeout", "coreutils", "Instalar: pacman -S coreutils / apt install coreutils"),
    ("systemctl", "systemd", "Sistema systemd requerido"),
    ("ss", "iproute2", "Instalar: pacman -S iproute2 / apt install iproute2"),
    ("df", "coreutils", "Instalar: pacman -S coreutils / apt install coreutils"),
    ("find", "findutils", "Instalar: pacman -S findutils / apt install findutils"),
    ("grep", "grep", "Instalar: pacman -S grep / apt install grep"),
    ("awk", "gawk", "Instalar: pacman -S gawk / apt install gawk"),
]

OPTIONAL = [
    ("lynis", "lynis", "Instalar: pacman -S lynis / apt install lynis (auditoría CIS extendida)"),
    ("smartctl", "smartmontools", "Instalar: pacman -S smartmontools / apt install smartmontools (health disco)"),
    ("fwupdmgr", "fwupd", "Instalar: pacman -S fwupd / apt install fwupd (firmware updates)"),
    ("paccache", "pacman-contrib", "Instalar: pacman -S pacman-contrib (limpieza caché Arch)"),
    ("deborphan", "deborphan", "Instalar: apt install deborphan (huérfanos Debian)"),
    ("needrestart", "needrestart", "Instalar: apt install needrestart (servicios a reiniciar Debian)"),
    ("rpmconf", "rpmconf", "Instalar: dnf install rpmconf (configs RPM)"),
    ("ucf", "ucf", "Instalar: apt install ucf (configs Debian)"),
]


def check_cmd(spec: tuple[str, str, str], *, required: bool, verbose: bool, install_hint: bool) -> int:
    cmd, package, hint = spec
    if which(cmd) is not None:
        if verbose:
            print(color(f"[OK] {cmd} ({package})", GREEN))
        return 1
    if required:
        print(color(f"[MISSING] {cmd} ({package}) — REQUERIDO", RED))
    else:
        print(color(f"[MISSING] {cmd} ({package}) — opcional", YELLOW))
    if install_hint:
        print(f"  → {hint}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verifica dependencias requeridas y opcionales.")
    parser.add_argument("--verbose", action="store_true", help="Muestra dependencias encontradas")
    parser.add_argument("--install-hint", action="store_true", help="Muestra comandos de instalación")
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    verbose = args.verbose
    install_hint = args.install_hint

    missing_required = 0
    missing_optional = 0

    print("=== Verificación de dependencias ===")
    print()

    print("--- Requeridos ---")
    for cmd, package, hint in REQUIRED:
        if not check_cmd((cmd, package, hint), required=True, verbose=verbose, install_hint=install_hint):
            missing_required += 1

    print()
    print("--- Opcionales (mejoran la auditoría) ---")
    for cmd, package, hint in OPTIONAL:
        if not check_cmd((cmd, package, hint), required=False, verbose=verbose, install_hint=install_hint):
            missing_optional += 1

    print()
    print("--- Resumen ---")
    if missing_required > 0:
        logger.error("Faltan %d dependencias requeridas.", missing_required)
        print(color(f"Faltan {missing_required} dependencias requeridas.", RED))
        if install_hint:
            print("Usa --install-hint para ver comandos de instalación.")
        return 1
    print(color("Todas las dependencias requeridas están presentes.", GREEN))
    if missing_optional > 0:
        print(color(f"Faltan {missing_optional} dependencias opcionales (funcionalidad reducida).", YELLOW))
    return 0


if __name__ == "__main__":
    sys.exit(main())
