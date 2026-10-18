#!/usr/bin/env python3
"""apparmor_lifecycle.py - Ciclo de vida de perfiles AppArmor (por defecto dry-run).

genprof/autodep -> complain -> soak de dias de uso real -> aa-logprof -> enforce.
Con `audit deny` de credenciales desde el dia 1 (se activan al enforce).
Ver references/apparmor-playbook.md antes de tocar perfiles.

Uso:
  apparmor_lifecycle.py [--state FILE] status
  apparmor_lifecycle.py [--state FILE] genprof --profile NOMBRE --binary RUTA
  apparmor_lifecycle.py [--state FILE] complain --profile NOMBRE
  apparmor_lifecycle.py [--state FILE] soak --profile NOMBRE --days N
  apparmor_lifecycle.py [--state FILE] logprof --profile NOMBRE
  apparmor_lifecycle.py [--state FILE] enforce --profile NOMBRE [--execute]
(--state tambien se acepta despues del subcomando.)
Sin --execute solo imprime el plan (no ejecuta nada privilegiado).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone

logger = logging.getLogger("seguridad.apparmor")

STAGES = ("genprof", "complain", "soak", "logprof", "enforce")
DEFAULT_STATE = os.path.expanduser("~/.local/share/system-security/apparmor-lifecycle.json")


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s", stream=sys.stderr)
    else:
        logging.getLogger().setLevel(level)


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def load_state(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(path: str, data: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        return True
    except (OSError, TypeError, ValueError) as exc:
        logger.error("no se pudo guardar estado %r: %s", path, exc)
        return False


def validate_logprof_parseable(profile: str) -> bool:
    """La toolchain perl debe poder parsear el archivo (playbook §10)."""
    if which("aa-logprof") is None:
        return False
    try:
        proc = subprocess.run(
            ["sh", "-c", "echo F | aa-logprof -f /etc/apparmor.d/" + profile],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=30, text=True, check=False,
        )
        return "skipping unparseable" not in (proc.stdout + proc.stderr).lower()
    except (OSError, subprocess.TimeoutExpired):
        return False


def cmd_status(state: dict) -> int:
    profiles = state.get("profiles", {})
    if not profiles:
        print("sin perfiles en seguimiento")
        return 0
    for name, info in profiles.items():
        print(f"{name}: etapa={info.get('stage', '?')} soak_desde={info.get('soak_since', '-')}")
    return 0


def advance(state_path: str, profile: str, stage: str, days: int = 0, execute: bool = False) -> int:
    state = load_state(state_path)
    profiles = state.setdefault("profiles", {})
    info = profiles.setdefault(profile, {"stage": "none"})
    idx_new = STAGES.index(stage)
    idx_cur = STAGES.index(info["stage"]) if info.get("stage") in STAGES else -1
    if idx_new < idx_cur:
        print(f"retroceso no permitido: {info.get('stage')} -> {stage} (usar disable manual)")
        return 1
    if stage == "soak":
        info["soak_since"] = utcnow()
        info["soak_days"] = days
        print(f"soak iniciado para {profile}: {days} dias de uso real desde {info['soak_since']}")
    if stage == "enforce":
        if not validate_logprof_parseable(profile):
            print(f"BLOQUEADO: aa-logprof no parsea /etc/apparmor.d/{profile} (ver playbook §10)")
            return 1
        if execute:
            print(
                "BLOCKED: host AppArmor enforce is not registered in "
                "tools/execution/registry.py; refusing silent mutation. "
                f"Manual (operator): aa-enforce /etc/apparmor.d/{profile}",
                file=sys.stderr,
            )
            return 3
        else:
            print(f"[dry-run] aa-enforce /etc/apparmor.d/{profile} (host mutate blocked without registry)")
        info["stage"] = stage
    else:
        cmds = {
            "genprof": f"aa-genprof {profile}  # o aa-autodep; ruta resuelta con readlink -f (playbook §5)",
            "complain": f"aa-complain /etc/apparmor.d/{profile}",
            "logprof": f"aa-logprof -f /etc/apparmor.d/{profile}",
        }
        print(cmds.get(stage, stage))
        info["stage"] = stage
    info["updated"] = utcnow()
    if not save_state(state_path, state):
        return 1
    print(f"{profile}: etapa actual = {info['stage']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ciclo de vida de perfiles AppArmor (dry-run por defecto).")
    common_opts = argparse.ArgumentParser(add_help=False)
    common_opts.add_argument("--state", default=DEFAULT_STATE, help="Fichero de estado JSON")
    common_opts.add_argument("--verbose", action="store_true", help="Logging verboso a stderr")
    parser.add_argument("--state", default=DEFAULT_STATE, help="Fichero de estado JSON")
    parser.add_argument("--verbose", action="store_true", help="Logging verboso a stderr")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Estado de perfiles en seguimiento", parents=[common_opts])
    p = sub.add_parser("genprof", help="Generar perfil base", parents=[common_opts])
    p.add_argument("--profile", required=True)
    p.add_argument("--binary", default="")
    p = sub.add_parser("complain", help="Pasar a complain", parents=[common_opts])
    p.add_argument("--profile", required=True)
    p = sub.add_parser("soak", help="Iniciar soak de uso real", parents=[common_opts])
    p.add_argument("--profile", required=True)
    p.add_argument("--days", type=int, default=3)
    p = sub.add_parser("logprof", help="Procesar logs con aa-logprof", parents=[common_opts])
    p.add_argument("--profile", required=True)
    p = sub.add_parser("enforce", help="Pasar a enforce (valida parseo)", parents=[common_opts])
    p.add_argument("--profile", required=True)
    p.add_argument("--execute", action="store_true", help="Mostrar comando real (no lo ejecuta)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    if args.command == "status":
        return cmd_status(load_state(args.state))
    days = getattr(args, "days", 0) or 0
    execute = getattr(args, "execute", False)
    return advance(args.state, args.profile, args.command, days=days, execute=execute)


if __name__ == "__main__":
    sys.exit(main())
