#!/usr/bin/env python3
"""session_logger.py - Registro forense append-only por sesión.

Port Python de session_logger.sh. Cada comando propuesto, validado, ejecutado
y su salida queda en un log inmutable (append-only).
"""

from __future__ import annotations

import argparse
import getpass
import logging
import os
import socket
import sys

from common import SKILL_VERSION, run, utcnow_iso

logger = logging.getLogger("mantenimiento.session_logger")


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s", stream=sys.stderr)
    else:
        logging.getLogger().setLevel(level)


LOG_DIR = os.environ.get("LOG_DIR", "/var/log/mantenimiento-linux")
SESSION_ID = (
    os.environ.get("SESSION_ID", "")
    or f"session-{utcnow_iso().replace('-', '').replace(':', '').replace('T', '-').replace('Z', '')}"
)
LOG_FILE = os.path.join(LOG_DIR, f"{SESSION_ID}.log")


def _ensure_log_dir() -> None:
    global LOG_DIR, LOG_FILE
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except OSError as exc:
        logger.warning("no se pudo crear LOG_DIR=%r (%s); usando fallback /tmp", LOG_DIR, exc)
        LOG_DIR = "/tmp/mantenimiento-linux/logs"
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
        except OSError as exc2:
            logger.error("no se pudo crear fallback LOG_DIR=%r: %s", LOG_DIR, exc2)
            raise
        LOG_FILE = os.path.join(LOG_DIR, f"{SESSION_ID}.log")


def _current_user() -> str:
    try:
        return getpass.getuser()
    except (OSError, KeyError) as exc:
        logger.warning("getpass.getuser() falló: %s", exc)
        return os.environ.get("USER", "unknown")


def _distro_id() -> str:
    out = run("grep '^ID=' /etc/os-release 2>/dev/null | cut -d= -f2", timeout=5)
    return out.strip().strip('"') or "unknown"


def init_log() -> None:
    _ensure_log_dir()
    try:
        user = _current_user()
        host = socket.gethostname()
    except OSError as exc:
        logger.error("no se pudo obtener hostname/usuario: %s", exc)
        raise
    header = (
        "=== mantenimiento-linux session log ===\n"
        f"SESSION_ID: {SESSION_ID}\n"
        f"TIMESTAMP: {utcnow_iso()}\n"
        f"HOSTNAME: {host}\n"
        f"USER: {user}\n"
        f"DISTRO: {_distro_id()}\n"
        f"KERNEL: {run('uname -r', timeout=5).strip()}\n"
        f"SKILL_VERSION: {SKILL_VERSION}\n"
        "======================================\n\n"
    )
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(header)
    except OSError as exc:
        logger.error("no se pudo escribir header en %r: %s", LOG_FILE, exc)
        raise


def log_event(
    type_: str = "INFO", risk_level: str = "R0", command: str = "", status: str = "", details: str = ""
) -> None:
    _ensure_log_dir()
    timestamp = utcnow_iso()
    lines = [f"[{timestamp}] [{type_}] [{risk_level}] {status}"]
    if command:
        lines.append(f"  COMMAND: {command}")
    if details:
        lines.append(f"  DETAILS: {details}")
    lines.append("")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    except OSError as exc:
        logger.error("no se pudo escribir evento en %r: %s", LOG_FILE, exc)
        raise


def log_proposed(cmd: str, risk_level: str) -> None:
    log_event("PROPOSED", risk_level, cmd, "pending")


def log_gate_result(cmd: str, risk_level: str, result: str) -> None:
    log_event("GATE", risk_level, cmd, result)


def log_executed(cmd: str, risk_level: str, exit_code: int, output: str = "") -> None:
    log_event("EXECUTED", risk_level, cmd, f"exit_code={exit_code}", output)


def log_error(context: str, error: str) -> None:
    log_event("ERROR", "R0", "", context, error)


def log_snapshot(snapshot_id: str, snapshot_path: str) -> None:
    log_event("SNAPSHOT", "R0", "", "created", f"id={snapshot_id} path={snapshot_path}")


def log_mode_start(mode: str) -> None:
    log_event("MODE", "R0", "", "start", f"mode={mode}")


def log_mode_end(mode: str, result: str) -> None:
    log_event("MODE", "R0", "", "end", f"mode={mode} result={result}")


def get_log_file() -> str:
    return LOG_FILE


def get_session_id() -> str:
    return SESSION_ID


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Registro forense append-only por sesión (inicializa log al ejecutar)."
    )
    parser.add_argument("--log-dir", default=None, help="Override LOG_DIR (por defecto env LOG_DIR)")
    parser.add_argument("--session-id", default=None, help="Override SESSION_ID (por defecto env/ autogenerado)")
    parser.add_argument("--verbose", action="store_true", help="Logging verboso a stderr")
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    global LOG_DIR, SESSION_ID, LOG_FILE
    if args.log_dir:
        LOG_DIR = args.log_dir
        LOG_FILE = os.path.join(LOG_DIR, f"{SESSION_ID}.log")
    if args.session_id:
        SESSION_ID = args.session_id
        LOG_FILE = os.path.join(LOG_DIR, f"{SESSION_ID}.log")
    try:
        init_log()
    except OSError:
        return 1
    print(f"Session log initialized: {LOG_FILE}")
    print(f"Session ID: {SESSION_ID}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
