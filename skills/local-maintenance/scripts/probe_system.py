#!/usr/bin/env python3

"""probe_system.py - Fingerprint del sistema (solo lectura).

Port Python de probe_system.sh. Genera system-profile.json con información
completa del sistema. Uso: probe_system.py [output-file]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any

from common import (
    SKILL_VERSION,
    detect_distro,
    hostname,
    log_info,
    run,
    service_active,
    to_int,
    utcnow_iso,
    which,
)

DF_FIELDS = 7
SS_FIELDS = 5


def get_kernel_info() -> dict[str, Any]:
    release = run("uname -r", timeout=5).strip()
    version = run("uname -v", timeout=5).strip()
    arch = run("uname -m", timeout=5).strip()
    cmdline = ""
    try:
        with open("/proc/cmdline", encoding="utf-8", errors="replace") as fh:
            cmdline = fh.read().strip()
    except OSError:
        pass
    return {
        "release": release,
        "version": version,
        "arch": arch,
        "cmdline": cmdline,
    }


def get_hardware_info() -> dict[str, Any]:
    cpu_model = run("lscpu | grep 'Model name' | cut -d: -f2 | xargs", timeout=10).strip()
    cpu_cores = to_int(run("nproc", timeout=5).strip())
    cpu_threads = to_int(run("lscpu | grep '^CPU(s):' | awk '{print $2}'", timeout=10).strip())
    mem_total = to_int(run("free -b | awk '/^Mem:/{print $2}'", timeout=10).strip())
    mem_available = to_int(run("free -b | awk '/^Mem:/{print $7}'", timeout=10).strip())
    swap_total = to_int(run("free -b | awk '/^Swap:/{print $2}'", timeout=10).strip())

    if not cpu_model:
        cpu_model = "unknown"

    disks: list[dict[str, Any]] = []
    lsblk_out = run(
        "lsblk -J -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL 2>/dev/null",
        timeout=10,
    )
    if lsblk_out.strip():
        try:
            data = json.loads(lsblk_out)
            disks = [d for d in data.get("blockdevices", []) if d.get("type") == "disk"]
        except json.JSONDecodeError:
            disks = []

    smart_available = which("smartctl") is not None

    return {
        "cpu_model": cpu_model,
        "cpu_cores": cpu_cores,
        "cpu_threads": cpu_threads,
        "mem_total_bytes": mem_total,
        "mem_available_bytes": mem_available,
        "swap_total_bytes": swap_total,
        "disks": disks,
        "smart_available": smart_available,
    }


def get_disk_usage() -> dict[str, Any]:
    df_out = run(
        "df -h -x tmpfs -x devtmpfs -x squashfs "
        "--output=source,fstype,size,used,avail,pcent,target 2>/dev/null | tail -n +2",
        timeout=10,
    )
    mounts = []
    for line in df_out.splitlines():
        parts = line.split(None, 6)
        if len(parts) < DF_FIELDS:
            continue
        source, fstype, size, used, avail, pcent, target = parts
        mounts.append(
            {
                "source": source,
                "fstype": fstype,
                "size": size,
                "used": used,
                "avail": avail,
                "use_percent": pcent,
                "mountpoint": target,
            }
        )
    return {"mounts": mounts}


def get_systemd_info() -> dict[str, Any]:
    def unit_names(cmd: str) -> list[str]:
        out = run(cmd, timeout=10)
        names = [line.split()[0] for line in out.splitlines() if line.split()]
        return names

    failed_services = unit_names("systemctl --failed --no-legend --no-pager 2>/dev/null")
    enabled_services = unit_names(
        "systemctl list-unit-files --type=service --state=enabled --no-legend --no-pager 2>/dev/null"
    )
    running_services = unit_names(
        "systemctl list-units --type=service --state=running --no-legend --no-pager 2>/dev/null"
    )
    boot_time = run("systemd-analyze 2>/dev/null | head -1", timeout=15).strip()
    blame_out = run("systemd-analyze blame --no-pager 2>/dev/null | head -20", timeout=15)
    top_blame = []
    for line in blame_out.splitlines():
        tokens = line.split()
        if tokens:
            top_blame.append(" ".join(tokens[:4]))

    return {
        "failed_services": failed_services,
        "enabled_services": enabled_services,
        "running_services": running_services,
        "boot_time": boot_time,
        "top_blame": top_blame,
    }


def get_network_info() -> dict[str, Any]:
    ss_out = run("ss -tuln 2>/dev/null | tail -n +2", timeout=10)
    ports = set()
    for line in ss_out.splitlines():
        parts = line.split()
        if len(parts) < SS_FIELDS:
            continue
        local = parts[4]
        if ":" in local:
            port = local.rsplit(":", 1)[-1]
            if port.isdigit():
                ports.add(int(port))
    listening_ports = sorted(ports)

    interfaces: list[dict[str, Any]] = []
    ip_out = run("ip -j addr show 2>/dev/null", timeout=10)
    if ip_out.strip():
        try:
            data = json.loads(ip_out)
            for iface in data:
                addrs = [a.get("local") for a in iface.get("addr_info", []) if a.get("family") in ("inet", "inet6")]
                interfaces.append({"name": iface.get("ifname"), "addr": addrs})
        except json.JSONDecodeError:
            interfaces = []

    firewall_active = False
    firewall_type = ""
    for name in ("ufw", "nftables", "iptables", "firewalld"):
        if service_active(name):
            firewall_active = True
            firewall_type = name
            break

    return {
        "listening_ports": [str(p) for p in listening_ports],
        "interfaces": interfaces,
        "firewall_active": firewall_active,
        "firewall_type": firewall_type,
    }


def get_package_info(pkg_mgr: str) -> dict[str, Any]:
    pkg_count = orphan_count = foreign_count = pacnew_count = cache_size_mb = 0

    if pkg_mgr == "pacman":
        pkg_count = to_int(run("pacman -Q 2>/dev/null | wc -l", timeout=30).strip())
        orphan_count = to_int(run("pacman -Qtdq 2>/dev/null | wc -l", timeout=30).strip())
        foreign_count = to_int(run("pacman -Qmq 2>/dev/null | wc -l", timeout=30).strip())
        pacnew_count = to_int(
            run("find /etc -name '*.pacnew' -o -name '*.pacsave' 2>/dev/null | wc -l", timeout=30).strip()
        )
        cache_size_mb = to_int(run("du -sm /var/cache/pacman/pkg 2>/dev/null | cut -f1", timeout=30).strip())
    elif pkg_mgr == "apt":
        pkg_count = to_int(run("dpkg -l 2>/dev/null | grep '^ii' | wc -l", timeout=30).strip())
        orphan_count = to_int(run("apt autoremove --dry-run 2>/dev/null | grep '^Remv' | wc -l", timeout=60).strip())
        foreign_count = to_int(run("apt list --manual-installed 2>/dev/null | tail -n +2 | wc -l", timeout=60).strip())
        pacnew_count = to_int(
            run("find /etc -name '*.dpkg-*' -o -name '*.ucf-*' 2>/dev/null | wc -l", timeout=30).strip()
        )
        cache_size_mb = to_int(run("du -sm /var/cache/apt/archives 2>/dev/null | cut -f1", timeout=30).strip())
    elif pkg_mgr == "dnf":
        pkg_count = to_int(run("rpm -qa 2>/dev/null | wc -l", timeout=30).strip())
        orphan_count = to_int(run("dnf repoquery --unneeded 2>/dev/null | wc -l", timeout=60).strip())
        foreign_count = to_int(run("dnf list extras 2>/dev/null | tail -n +2 | wc -l", timeout=60).strip())
        pacnew_count = to_int(
            run("find /etc -name '*.rpmnew' -o -name '*.rpmsave' 2>/dev/null | wc -l", timeout=30).strip()
        )
        cache_size_mb = to_int(run("du -sm /var/cache/dnf 2>/dev/null | cut -f1", timeout=30).strip())

    return {
        "total_packages": pkg_count,
        "orphans": orphan_count,
        "foreign_packages": foreign_count,
        "config_files_pending": pacnew_count,
        "cache_size_mb": cache_size_mb,
    }


def get_journal_info() -> dict[str, Any]:
    disk_usage = run(
        "journalctl --disk-usage 2>/dev/null | grep -oE '[0-9.]+[GMK]' | head -1",
        timeout=15,
    ).strip()
    if not disk_usage:
        disk_usage = "0B"

    errors_24h = to_int(
        run("journalctl -p 0..3 --since '24 hours ago' --no-pager 2>/dev/null | grep -c .", timeout=30).strip()
    )

    coredumps = to_int(run("coredumpctl list 2>/dev/null | tail -1 | awk '{print $1}'", timeout=15).strip())

    return {"disk_usage": disk_usage, "errors_24h": errors_24h, "coredumps": coredumps}


def get_firmware_info() -> dict[str, Any]:
    fwupd_available = which("fwupdmgr") is not None
    updates_available = 0
    devices = 0
    if fwupd_available:
        updates_available = to_int(run("fwupdmgr get-updates 2>/dev/null | grep -c '^Device:'", timeout=30).strip())
        devices = to_int(run("fwupdmgr get-devices 2>/dev/null | grep -c '^Device:'", timeout=30).strip())
    return {"fwupd_available": fwupd_available, "updates_available": updates_available, "devices": devices}


def get_modern_stack() -> dict[str, Any]:
    """Stack moderno: homed, btrfs/snapshots, energia, oomd/zram, helpers (ES)."""
    homed_active = service_active("systemd-homed")
    homectl_users = []
    if which("homectl") is not None:
        out = run("homectl list --no-legend --no-pager 2>/dev/null", timeout=10)
        homectl_users = [line.split()[0] for line in out.splitlines() if line.split()]
    timers = run("systemctl list-timers --all --no-legend --no-pager 2>/dev/null", timeout=15)
    snapper_cfgs = []
    if which("snapper") is not None:
        out = run("snapper list-configs --no-headers 2>/dev/null", timeout=15)
        snapper_cfgs = [line.split()[0] for line in out.splitlines() if line.split()]
    ppd_profile = ""
    if which("powerprofilesctl") is not None:
        ppd_profile = run("powerprofilesctl get 2>/dev/null", timeout=10).strip()
    zram_devs = run("zramctl --noheadings --output NAME,DISKSIZE 2>/dev/null", timeout=10).strip()
    needrestart_pending = ""
    if which("needrestart") is not None:
        needrestart_pending = run("needrestart -r l 2>/dev/null | head -5", timeout=60).strip()
    return {
        "identity": {
            "systemd_homed_active": homed_active,
            "homectl_users": homectl_users,
        },
        "snapshots": {
            "btrfs_assistant": which("btrfs-assistant") is not None,
            "snapper_configs": snapper_cfgs,
            "timeshift": which("timeshift") is not None,
            "timeshift_auto_timer": "timeshift" in timers,
        },
        "power": {
            "auto_cpufreq": service_active("auto-cpufreq"),
            "tuned": service_active("tuned"),
            "tuned_ppd": service_active("tuned-ppd"),
            "power_profiles_daemon": service_active("power-profiles-daemon"),
            "power_profile": ppd_profile,
        },
        "memory_pressure": {
            "systemd_oomd": service_active("systemd-oomd"),
            "zram_generator_conf": os.path.isfile("/etc/systemd/zram-generator.conf"),
            "zram_devices": zram_devs,
        },
        "helpers": {
            "nvchecker": which("nvchecker") is not None,
            "needrestart": which("needrestart") is not None,
            "needrestart_pending": needrestart_pending,
            "pacdiff": which("pacdiff") is not None,
            "ucf": which("ucf") is not None,
        },
    }


logger = logging.getLogger("mantenimiento.probe")


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s", stream=sys.stderr)
    else:
        logging.getLogger().setLevel(level)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fingerprint del sistema (solo lectura).")
    parser.add_argument("output_file", nargs="?", default="system-profile.json", help="Fichero JSON de salida")
    parser.add_argument("--verbose", action="store_true", help="Logging verboso a stderr")
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    output_file = args.output_file

    log_info("Iniciando fingerprint del sistema...")

    try:
        distro = detect_distro()
    except (OSError, ValueError) as exc:
        logger.error("no se pudo detectar distro: %s", exc)
        return 1
    pkg_mgr = distro["package_manager"]

    try:
        profile = {
            "metadata": {
                "timestamp": utcnow_iso(),
                "hostname": hostname(),
                "skill_version": SKILL_VERSION,
            },
            "distro": distro,
            "kernel": get_kernel_info(),
            "hardware": get_hardware_info(),
            "disk": get_disk_usage(),
            "systemd": get_systemd_info(),
            "network": get_network_info(),
            "packages": get_package_info(pkg_mgr),
            "journal": get_journal_info(),
            "firmware": get_firmware_info(),
            "modern_stack": get_modern_stack(),
        }
    except (OSError, ValueError) as exc:
        logger.error("fallo recolectando perfil: %s", exc)
        return 1

    try:
        with open(output_file, "w", encoding="utf-8") as fh:
            json.dump(profile, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    except (OSError, TypeError, ValueError) as exc:
        logger.error("no se pudo escribir %r: %s", output_file, exc)
        print(f"Error: no se pudo escribir {output_file}: {exc}", file=sys.stderr)
        return 1

    log_info(f"Perfil guardado en {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
