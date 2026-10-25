#!/usr/bin/env python3
"""forense_collector.py - Recetas de forense-logs.md a cronologia JSON (solo lectura).

Recetas: auth (SSH/login sospechoso), sudo (uso de privilegios),
apparmor (denegaciones AVC), watch-key (clave auditd), pid (cronologia de
PID/binario), timeline (todo lo anterior ordenado por timestamp).
Reglas: hora del sistema primero, distinguir ruido de senal, nunca concluir
intrusion con un solo evento, guardar evidencia con timestamp.
Uso: forense_collector.py RECIPE [--since TXT] [--pid N] [--key CLAVE] [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import sys
from datetime import datetime, timezone

logger = logging.getLogger("seguridad.forense")

RECIPES = ("auth", "sudo", "apparmor", "watch-key", "pid", "timeline")


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s", stream=sys.stderr)
    else:
        logging.getLogger().setLevel(level)


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def run_cmd(cmd: str, timeout: int = 120) -> str:
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
        return proc.stdout
    except (subprocess.TimeoutExpired, OSError):
        return ""


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def collect_auth(since: str) -> list[dict]:
    events: list[dict] = []
    out = run_cmd(
        f"journalctl _COMM=sshd --since \"{since}\" --no-pager 2>/dev/null | grep -iE 'failed|accepted' | head -50"
    )
    for line in out.splitlines():
        if line.strip():
            events.append({"ts": line[:15], "source": "journalctl:sshd", "summary": line.strip()[:300]})
    out = run_cmd("last -f /var/log/wtmp 2>/dev/null | head -20")
    for line in out.splitlines():
        if line.strip():
            events.append({"ts": "", "source": "last:wtmp", "summary": line.strip()[:300]})
    return events


def collect_sudo(since: str) -> list[dict]:
    events: list[dict] = []
    out = run_cmd(
        f"journalctl _COMM=sudo --since \"{since}\" --no-pager 2>/dev/null | grep -E 'COMMAND|user' | head -50"
    )
    for line in out.splitlines():
        if line.strip():
            events.append({"ts": line[:15], "source": "journalctl:sudo", "summary": line.strip()[:300]})
    return events


def collect_apparmor(since: str) -> list[dict]:
    events: list[dict] = []
    if which("ausearch") is None:
        return [{"ts": "", "source": "ausearch", "summary": "ausearch no disponible"}]
    out = run_cmd(f"ausearch -m avc -ts {since} 2>/dev/null | grep 'apparmor=\"DENIED\"' | head -30")
    for line in out.splitlines():
        if line.strip():
            events.append({"ts": "", "source": "ausearch:avc", "summary": line.strip()[:300]})
    return events


def collect_watch_key(key: str, since: str) -> list[dict]:
    events: list[dict] = []
    if which("ausearch") is None:
        return [{"ts": "", "source": "ausearch", "summary": "ausearch no disponible"}]
    out = run_cmd(f"ausearch -k {key} -ts {since} 2>/dev/null | head -30")
    for line in out.splitlines():
        if line.strip():
            events.append({"ts": "", "source": f"ausearch:{key}", "summary": line.strip()[:300]})
    return events


def collect_pid(pid: str, since: str) -> list[dict]:
    events: list[dict] = []
    if which("ausearch") is not None:
        out = run_cmd(f"ausearch -p {pid} -ts {since} 2>/dev/null | head -20")
        for line in out.splitlines():
            if line.strip():
                events.append({"ts": "", "source": f"ausearch:pid:{pid}", "summary": line.strip()[:300]})
    out = run_cmd(f'journalctl _PID={pid} --since "{since}" --no-pager 2>/dev/null | head -20')
    for line in out.splitlines():
        if line.strip():
            events.append({"ts": line[:15], "source": f"journalctl:pid:{pid}", "summary": line.strip()[:300]})
    return events


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Recetas forenses a cronologia JSON (solo lectura).")
    parser.add_argument("recipe", choices=list(RECIPES), help="Receta de forense-logs.md")
    parser.add_argument("--since", default="today", help="Ventana temporal (defecto today)")
    parser.add_argument("--pid", default="", help="PID para receta pid")
    parser.add_argument("--key", default="identity", help="Clave auditd para receta watch-key")
    parser.add_argument("--json", default="", help="Fichero JSON de salida")
    parser.add_argument("--verbose", action="store_true", help="Logging verboso a stderr")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    clock = run_cmd("timedatectl 2>/dev/null | head -5").strip()
    events: list[dict] = []
    if args.recipe in ("auth", "timeline"):
        events += collect_auth("24 hours ago" if args.since == "today" else args.since)
    if args.recipe in ("sudo", "timeline"):
        events += collect_sudo("today" if args.since == "today" else args.since)
    if args.recipe in ("apparmor", "timeline"):
        events += collect_apparmor(args.since)
    if args.recipe == "watch-key":
        events += collect_watch_key(args.key, args.since)
    if args.recipe == "pid":
        if not args.pid:
            print("receta pid requiere --pid N", file=sys.stderr)
            return 2
        events += collect_pid(args.pid, "today" if args.since == "today" else args.since)
    events.sort(key=lambda e: (e.get("ts") or "", e.get("source") or ""))

    result = {
        "collected_at": utcnow(),
        "system_clock": clock,
        "recipe": args.recipe,
        "events": events,
        "note": "candidatos, no veredicto: buscar la cadena login->sudo->proceso->escritura",
    }
    print(f"forense: receta={args.recipe} eventos={len(events)}")
    if args.json:
        try:
            with open(args.json, "w", encoding="utf-8") as fh:
                json.dump(result, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
        except (OSError, TypeError, ValueError) as exc:
            logger.error("no se pudo escribir %r: %s", args.json, exc)
            return 1
        print(f"Evidencia guardada en: {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
