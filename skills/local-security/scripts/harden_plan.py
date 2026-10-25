#!/usr/bin/env python3
"""harden_plan.py - Plan de hardening desde el baseline canonico (solo lectura).

Lee skills/local-security/references/hardening-baseline.md, extrae los IDs
de control, compara el estado actual (SSH/sysctl/firewall/auditd/journald)
contra el nivel deseado (--level 1|2|3) y emite plan P1-P4 con diff actual ->
deseado, nivel R y comandos de rollback. No aplica nada.
Uso: harden_plan.py [--level 2] [--baseline PATH] [--json out.json] [--md out.md]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys

logger = logging.getLogger("seguridad.harden_plan")

DEFAULT_BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "hardening-baseline.md")


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s", stream=sys.stderr)
    else:
        logging.getLogger().setLevel(level)


def run_cmd(cmd: str, timeout: int = 10) -> str:
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


def parse_control_ids(baseline_path: str) -> list[str]:
    """Extrae IDs de control (SSH-01, KR-22, ...) del baseline canonico."""
    try:
        with open(baseline_path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        logger.error("no se pudo leer baseline %r: %s", baseline_path, exc)
        return []
    ids = re.findall(r"\b(SSH|FW|FS|AU|KR|UA|SD|CR)-\d{2}\b", text)
    # re.findall con grupos devuelve solo el grupo; rehacer sin grupos:
    ids = re.findall(r"\b(?:SSH|FW|FS|AU|KR|UA|SD|CR)-\d{2}\b", text)
    seen: list[str] = []
    for cid in ids:
        if cid not in seen:
            seen.append(cid)
    return seen


def probe_current() -> dict:
    """Estado actual de los controles clave (solo lectura)."""
    state: dict[str, str] = {}
    out = run_cmd("sshd -T 2>/dev/null", timeout=10)
    eff = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            eff[parts[0].lower()] = parts[1]
    state["SSH-01"] = eff.get("permitrootlogin", "?")
    state["SSH-02"] = eff.get("passwordauthentication", "?")
    state["SSH-05"] = eff.get("maxauthtries", "?")
    for key in (
        "kernel.randomize_va_space",
        "kernel.kptr_restrict",
        "kernel.dmesg_restrict",
        "net.ipv4.tcp_syncookies",
        "fs.suid_dumpable",
        "fs.protected_hardlinks",
        "fs.protected_symlinks",
    ):
        state[key] = run_cmd(f"sysctl -n {key} 2>/dev/null", timeout=5).strip() or "?"
    for unit in ("ufw", "nftables", "firewalld", "auditd"):
        rc = run_cmd(f"systemctl is-active {unit} 2>/dev/null", timeout=10).strip()
        state[f"svc:{unit}"] = rc or "unknown"
    state["journald_storage"] = (
        run_cmd("grep '^Storage=' /etc/systemd/journald.conf 2>/dev/null | cut -d= -f2", timeout=10).strip() or "?"
    )
    return state


DESIRED = {
    "SSH-01": "no",
    "SSH-02": "no",
    "SSH-05": "<=4",
    "kernel.randomize_va_space": "2",
    "kernel.kptr_restrict": "2",
    "kernel.dmesg_restrict": "1",
    "net.ipv4.tcp_syncookies": "1",
    "fs.suid_dumpable": "0",
    "fs.protected_hardlinks": "1",
    "fs.protected_symlinks": "1",
}

ROLLBACK = {
    "SSH": "cp <backup>/sshd_config /etc/ssh/sshd_config && sshd -t && systemctl reload sshd",
    "sysctl": "sysctl -w <clave>=<valor-previo> ; rm /etc/sysctl.d/99-hardening.conf && sysctl --system",
    "firewall": "restaurar politica previa documentada en el plan + recargar (ufw/nft)",
    "auditd": "rm /etc/audit/rules.d/hardening.rules && augenrules --load (reboot si -e 2)",
    "bootloader": "editar /etc/default/grub, grub-mkconfig -o /boot/grub/grub.cfg, reboot en ventana",
}

RISK = {"SSH-01": "R2", "SSH-02": "R2", "SSH-05": "R2"}


def build_plan(level: int, baseline_ids: list[str], current: dict) -> list[dict]:
    plan: list[dict] = []
    prio = {1: "P1", 2: "P2"}.get(level, "P2")
    for ctrl, want in DESIRED.items():
        got = current.get(ctrl, "?")
        ok = (got == want) or (want == "<=4" and got.isdigit() and int(got) <= 4)
        if ok:
            continue
        family = ctrl.split("-")[0] if "-" in ctrl and not ctrl.startswith(("kernel", "net.", "fs.")) else "sysctl"
        plan.append(
            {
                "control": ctrl,
                "severity": prio,
                "current": got,
                "desired": want,
                "diff": f"{got} -> {want}",
                "risk": RISK.get(ctrl, "R1"),
                "rollback": ROLLBACK.get(family, ROLLBACK["sysctl"]),
                "in_baseline": ctrl in baseline_ids,
            }
        )
    # Controles de nivel 2/3 no probados aqui: se listan como pendientes de revision manual
    if level >= 2:
        for extra in ("FW-02", "AU-01", "UA-07", "CR-01"):
            plan.append(
                {
                    "control": extra,
                    "severity": "P2",
                    "current": "revisar",
                    "desired": "baseline §" + extra.split("-")[0],
                    "diff": "pendiente de revision manual",
                    "risk": "R2" if extra in ("FW-02", "UA-07") else "R1",
                    "rollback": "segun familia (§11 del baseline)",
                    "in_baseline": extra in baseline_ids,
                }
            )
    return plan


def render_md(plan: list[dict], level: int) -> str:
    lines = [f"# Plan de hardening — Nivel {level}", "", f"Controles con gap: {len(plan)}", ""]
    for item in plan:
        lines.append(f"## {item['control']} ({item['severity']}, {item['risk']})")
        lines.append(f"- Actual: `{item['current']}` → Deseado: `{item['desired']}`")
        lines.append(f"- Rollback: `{item['rollback']}`")
        lines.append("")
    lines.append("_Baseline canonico: references/hardening-baseline.md §11 (R1/R2 + rollback)._")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan de hardening desde el baseline canonico (solo lectura).")
    parser.add_argument("--level", type=int, choices=[1, 2, 3], default=2, help="Nivel CIS objetivo (defecto 2)")
    parser.add_argument("--baseline", default=DEFAULT_BASELINE, help="Ruta al baseline canonico")
    parser.add_argument("--json", default="", help="Fichero JSON de salida")
    parser.add_argument("--md", default="", help="Fichero Markdown de salida")
    parser.add_argument("--verbose", action="store_true", help="Logging verboso a stderr")
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    ids = parse_control_ids(args.baseline)
    if not ids:
        logger.error("baseline sin IDs o ilegible: %r", args.baseline)
        return 1
    current = probe_current()
    plan = build_plan(args.level, ids, current)
    print(f"harden_plan: nivel {args.level}, {len(ids)} controles en baseline, {len(plan)} gaps")

    if args.json:
        try:
            with open(args.json, "w", encoding="utf-8") as fh:
                json.dump(
                    {"level": args.level, "baseline_controls": len(ids), "plan": plan}, fh, indent=2, ensure_ascii=False
                )
                fh.write("\n")
        except (OSError, TypeError, ValueError) as exc:
            logger.error("no se pudo escribir %r: %s", args.json, exc)
            return 1
        print(f"Guardado en: {args.json}")
    if args.md:
        try:
            with open(args.md, "w", encoding="utf-8") as fh:
                fh.write(render_md(plan, args.level) + "\n")
        except (OSError, TypeError, ValueError) as exc:
            logger.error("no se pudo escribir %r: %s", args.md, exc)
            return 1
        print(f"Guardado en: {args.md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
