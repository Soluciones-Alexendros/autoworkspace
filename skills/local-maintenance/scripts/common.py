#!/usr/bin/env python3
"""Utilidades compartidas para mantenimiento-linux (port Python nativo).

Reemplaza las funciones comunes de los scripts bash (run_cmd/run_check,
detección de distro/gestor de paquetes, logging con color, recolección de
hallazgos y cálculo del Health Score) sin depender de jq ni de subprocesos
bash. Todo el parsing se hace con la librería estándar.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("mantenimiento.common")


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s", stream=sys.stderr)
    else:
        logging.getLogger().setLevel(level)


COMPONENT_VERSION = "2.1.0"


def skill_version_from_manifest() -> str:
    """Read metadata.version from the skill SKILL.md (canonical skill version)."""
    skill_md = Path(__file__).resolve().parents[1] / "SKILL.md"
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return COMPONENT_VERSION
    if not text.startswith("---"):
        return COMPONENT_VERSION
    end = text.find("\n---", 4)
    if end == -1:
        return COMPONENT_VERSION
    try:
        import yaml

        fm = yaml.safe_load(text[4:end])
    except Exception:
        return COMPONENT_VERSION
    if not isinstance(fm, dict):
        return COMPONENT_VERSION
    meta = fm.get("metadata") or {}
    version = meta.get("version") if isinstance(meta, dict) else None
    if isinstance(version, str) and version.strip():
        return version.strip()
    return COMPONENT_VERSION


SKILL_VERSION = skill_version_from_manifest()  # skill manifest version; not component_version

# --- Colores ANSI (desactivados si no hay TTY o está NO_COLOR) ---
_USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"

CATEGORIES = ("security", "updates", "hygiene", "resources", "stability")
SEVERITIES = ("P0", "P1", "P2", "P3", "P4")
STATUSES = ("PASS", "FAIL", "WARN", "SKIP", "ERROR")

# Peso de cada categoría en el Health Score (suma 100).
CATEGORY_WEIGHTS = {
    "security": 35,
    "updates": 25,
    "hygiene": 20,
    "resources": 10,
    "stability": 10,
}

# Puntuación por estado: SKIP/ERROR no puntúan (no ensucian el denominador).
STATUS_VALUES = {"PASS": 100, "WARN": 40, "FAIL": 0}

# Peso por severidad: un fallo P0 pesa más que uno P4.
SEVERITY_WEIGHTS = {"P0": 8, "P1": 4, "P2": 2, "P3": 1, "P4": 1}


def color(text: str, code: str) -> str:
    return f"{code}{text}{NC}" if _USE_COLOR else text


def log_info(msg: str) -> None:
    print(color(f"[INFO] {msg}", GREEN))


def log_pass(msg: str) -> None:
    print(color(f"[PASS] {msg}", GREEN))


def log_fail(msg: str) -> None:
    print(color(f"[FAIL] {msg}", RED))


def log_warn(msg: str) -> None:
    print(color(f"[WARN] {msg}", YELLOW))


def log_error(msg: str) -> None:
    logger.error("%s", msg)
    print(color(f"[ERROR] {msg}", RED))


def log_debug(msg: str) -> None:
    print(color(f"[DEBUG] {msg}", BLUE))


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def hostname() -> str:
    return socket.gethostname()


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


@dataclass
class RunResult:
    """Structured subprocess outcome. Empty stdout alone is not 'healthy'."""

    returncode: int
    stdout: str
    stderr: str = ""
    timed_out: bool = False
    error: str = ""
    argv: list[str] | None = None


def run_result(
    argv: list[str],
    *,
    timeout: int = 10,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> RunResult:
    """Typed argv runner (shell=False). Rejects shell-interpreter escapes."""
    if not argv:
        return RunResult(returncode=2, stdout="", error="empty argv")
    binary = os.path.basename(argv[0])
    if binary in {"bash", "sh", "dash", "zsh"} and len(argv) >= 2 and argv[1] in {"-c", "-lc"}:
        return RunResult(returncode=2, stdout="", error="shell -c escape rejected", argv=list(argv))
    try:
        proc = subprocess.run(
            argv,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True,
            check=False,
            cwd=cwd,
            env=env,
        )
        return RunResult(
            returncode=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            argv=list(argv),
        )
    except subprocess.TimeoutExpired as exc:
        return RunResult(
            returncode=124,
            stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
            stderr=(exc.stderr or "") if isinstance(exc.stderr, str) else "",
            timed_out=True,
            error="timeout",
            argv=list(argv),
        )
    except OSError as exc:
        return RunResult(returncode=127, stdout="", error=str(exc), argv=list(argv))


def run(cmd: str, timeout: int = 10) -> str:
    """Legacy shell runner. Prefer run_result/run_capture for new code.

    Returns stdout only. Callers must not treat '' as proof of health — use
    run_capture or run_result to preserve return codes and timeouts.
    """
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            executable="/bin/bash",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            logger.debug("run rc=%s stderr=%s cmd=%r", proc.returncode, (proc.stderr or "")[:200], cmd)
        return proc.stdout or ""
    except subprocess.TimeoutExpired:
        logger.warning("run timeout cmd=%r", cmd)
        return ""
    except OSError as exc:
        logger.warning("run OSError %s cmd=%r", exc, cmd)
        return ""


def run_capture(cmd: str, timeout: int = 10) -> tuple[int, str]:
    """Legacy shell runner returning (returncode, stdout). Prefer run_result."""
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            executable="/bin/bash",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout or ""
    except subprocess.TimeoutExpired:
        return 124, ""
    except OSError:
        return 127, ""


def count_nonempty(text: str) -> int:
    """Cuenta líneas no vacías (equivale a `grep -c .`, sin el bug de 0)."""
    return sum(1 for line in text.splitlines() if line.strip())


def to_int(value: str, default: int = 0) -> int:
    value = (value or "").strip()
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def sysctl_get(key: str) -> str:
    return run(f"sysctl -n {key} 2>/dev/null", timeout=5).strip()


def service_active(unit: str) -> bool:
    """Verifica si un servicio systemd está activo leyendo su estado real."""
    rc, out = run_capture(f"systemctl is-active {unit} 2>/dev/null", timeout=10)
    return out.strip() == "active"


def read_os_release() -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        with open("/etc/os-release", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                values[key] = val.strip().strip('"').strip("'")
    except OSError:
        pass
    return values


# --- Detección de distro y gestor de paquetes ---

_ARCH_IDS = {"arch", "endeavouros", "cachyos", "manjaro", "garuda", "artix"}
_DEBIAN_IDS = {
    "debian",
    "ubuntu",
    "linuxmint",
    "pop",
    "elementary",
    "kali",
    "parrot",
    "zorin",
}
_RHEL_IDS = {
    "fedora",
    "rhel",
    "centos",
    "almalinux",
    "rocky",
    "ol",
    "scientific",
}
_SUSE_IDS = {"opensuse", "opensuse-leap", "opensuse-tumbleweed", "sles"}


def detect_distro() -> dict[str, str]:
    release = read_os_release()
    distro_id = release.get("ID", "unknown")
    distro_like = release.get("ID_LIKE", "")
    version_id = release.get("VERSION_ID", "")
    version_codename = release.get("VERSION_CODENAME", "")

    family = "unknown"
    pkg_mgr = "unknown"
    aur_helper = ""

    if distro_id in _ARCH_IDS:
        family, pkg_mgr = "arch", "pacman"
        if which("yay"):
            aur_helper = "yay"
        if which("paru"):
            aur_helper = "paru"
    elif distro_id in _DEBIAN_IDS:
        family, pkg_mgr = "debian", "apt"
    elif distro_id in _RHEL_IDS:
        family, pkg_mgr = "rhel", "dnf"
    elif any(distro_id.startswith(prefix) for prefix in ("opensuse",)) or distro_id == "sles":
        family, pkg_mgr = "suse", "zypper"
    else:
        # Fallback por gestor de paquetes
        if which("pacman"):
            family, pkg_mgr = "arch", "pacman"
        elif which("apt"):
            family, pkg_mgr = "debian", "apt"
        elif which("dnf"):
            family, pkg_mgr = "rhel", "dnf"
        elif which("zypper"):
            family, pkg_mgr = "suse", "zypper"

    return {
        "distro_id": distro_id,
        "distro_like": distro_like,
        "version_id": version_id,
        "version_codename": version_codename,
        "family": family,
        "package_manager": pkg_mgr,
        "aur_helper": aur_helper,
    }


def detect_pkg_mgr() -> tuple[str, str]:
    """Devuelve (family, package_manager)."""
    distro = detect_distro()
    return distro["family"], distro["package_manager"]


def load_profile_family(profile_file: str) -> tuple[str, str, str, str, str]:
    """Carga family, package_manager, distro_id, version_id, version_codename de un system-profile.json si existe."""
    if os.path.isfile(profile_file):
        try:
            with open(profile_file, encoding="utf-8") as fh:
                profile = json.load(fh)
            family = profile.get("distro", {}).get("family", "unknown")
            pkg_mgr = profile.get("distro", {}).get("package_manager", "unknown")
            distro_id = profile.get("distro", {}).get("distro_id", "unknown")
            version_id = profile.get("distro", {}).get("version_id", "")
            version_codename = profile.get("distro", {}).get("version_codename", "")
            if family and pkg_mgr:
                return family, pkg_mgr, distro_id, version_id, version_codename
        except (OSError, json.JSONDecodeError):
            pass
    distro = detect_distro()
    return (
        distro["family"],
        distro["package_manager"],
        distro["distro_id"],
        distro["version_id"],
        distro["version_codename"],
    )


# --- Recolección de hallazgos y Health Score (compartido audit_quick/full) ---


class FindingCollector:
    """Recolecta hallazgos y calcula el Health Score con la fórmula del skill."""

    def __init__(self) -> None:
        self.findings: list[dict[str, str]] = []
        self._counters: dict[str, int] = {status: 0 for status in STATUSES}

    def add(
        self,
        id: str,
        category: str,
        severity: str,
        title: str,
        description: str,
        control: str,
        status: str,
        evidence: str,
        remediation: str,
        risk_level: str,
    ) -> None:
        self.findings.append(
            {
                "id": id,
                "category": category,
                "severity": severity,
                "title": title,
                "description": description,
                "control": control,
                "status": status,
                "evidence": evidence,
                "remediation": remediation,
                "risk_level": risk_level,
            }
        )
        self._counters[status] = self._counters.get(status, 0) + 1

    @property
    def total(self) -> int:
        return len(self.findings)

    @property
    def passed(self) -> int:
        return self._counters.get("PASS", 0)

    @property
    def failed(self) -> int:
        return self._counters.get("FAIL", 0)

    @property
    def warned(self) -> int:
        return self._counters.get("WARN", 0)

    @property
    def skipped(self) -> int:
        return self._counters.get("SKIP", 0)

    @property
    def errors(self) -> int:
        return self._counters.get("ERROR", 0)

    def category_coverage(self, category: str) -> dict[str, int]:
        """How many findings exist and how many are scorable (PASS/WARN/FAIL)."""
        total = 0
        scorable = 0
        unscored = 0
        for finding in self.findings:
            if finding["category"] != category:
                continue
            total += 1
            if finding["status"] in STATUS_VALUES:
                scorable += 1
            else:
                unscored += 1
        return {"total": total, "scorable": scorable, "unscored": unscored}

    def _category_score(self, category: str) -> int | None:
        """Weighted mean of PASS/WARN/FAIL. None when nothing was scorable.

        SKIP/ERROR are not treated as perfect health. A category with only
        SKIP/ERROR or with no findings returns None (not_checked), never 100.
        """
        weight = 0
        weighted = 0
        for finding in self.findings:
            if finding["category"] != category:
                continue
            value = STATUS_VALUES.get(finding["status"])
            if value is None:
                continue
            severity_weight = SEVERITY_WEIGHTS.get(finding["severity"], 1)
            weight += severity_weight
            weighted += severity_weight * value
        if weight == 0:
            return None
        return weighted // weight

    def health_score(self) -> dict[str, Any]:
        scores: dict[str, Any] = {}
        covered_weight = 0
        covered_sum = 0
        for category in CATEGORIES:
            score = self._category_score(category)
            scores[category] = score
            if score is not None:
                w = CATEGORY_WEIGHTS[category]
                covered_weight += w
                covered_sum += score * w
        overall = (covered_sum // covered_weight) if covered_weight else None
        return {
            "overall": overall,
            "check_coverage": self.total,
            "categories_scored": covered_weight,
            **scores,
        }

    def summary(self) -> dict[str, object]:
        by_severity = {sev: sum(1 for f in self.findings if f["severity"] == sev) for sev in SEVERITIES}
        coverage = {cat: self.category_coverage(cat) for cat in CATEGORIES}
        return {
            "total_checks": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "warned": self.warned,
            "skipped": self.skipped,
            "errors": self.errors,
            "check_coverage": self.total,
            "category_coverage": coverage,
            "by_severity": by_severity,
        }

    def build_output(
        self,
        mode: str,
        distro: str,
        family: str,
        kernel: str,
        duration_seconds: int,
        version_id: str = "",
        version_codename: str = "",
        skill_version: str = SKILL_VERSION,
    ) -> dict[str, Any]:
        return {
            "metadata": {
                "timestamp": utcnow_iso(),
                "mode": mode,
                "hostname": hostname(),
                "distro": distro,
                "family": family,
                "version_id": version_id,
                "version_codename": version_codename,
                "kernel": kernel,
                "duration_seconds": duration_seconds,
                "skill_version": skill_version,
            },
            "health_score": self.health_score(),
            "findings": self.findings,
            "summary": self.summary(),
        }


# --- Utilidades de sshd (audit_full) ---

_SSHD_KEYS = (
    "permitrootlogin",
    "passwordauthentication",
    "permitemptypasswords",
    "maxauthtries",
    "clientaliveinterval",
    "clientalivecountmax",
    "allowusers",
    "allowgroups",
)


def sshd_effective() -> str:
    """Devuelve la config efectiva de sshd como líneas 'clave valor' (minúsculas).

    Intenta `sshd -T` (requiere root); si devuelve vacío, parsea los ficheros
    de configuración. Corrige la recursión infinita del bash original.
    """
    output = run("sshd -T 2>/dev/null", timeout=10)
    if output.strip():
        return output

    files = ["/etc/ssh/sshd_config"]
    files += sorted(f for f in glob_sorted("/etc/ssh/sshd_config.d/*.conf"))
    lines: list[str] = []
    for path in files:
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    stripped = line.strip().lower()
                    if not stripped or stripped.startswith("#"):
                        continue
                    for key in _SSHD_KEYS:
                        if stripped.startswith(key + " "):
                            parts = stripped.split()
                            if len(parts) >= 2:
                                lines.append(f"{parts[0]} {parts[1]}")
                            break
        except OSError:
            continue
    return "\n".join(lines) + ("\n" if lines else "")


def glob_sorted(pattern: str) -> list[str]:
    import glob

    return sorted(glob.glob(pattern))


def _sshd_get(key: str) -> str:
    for line in sshd_effective().splitlines():
        parts = line.split()
        if parts and parts[0].lower() == key and len(parts) >= 2:
            return parts[1]
    return ""


# --- Checks compartidos de higiene/updates (audit_quick + audit_full) ---
# Subconjunto de mantenimiento: PKG-*, FS-09/10/11, LOG-06/08, SRV-02, NET-04
# (+ ARC-07/DEB-04 como adaptadores de distro). El hardening puro
# (SSH/KR/FS-05-08/AU/UA/CR) vive en local-security y NO se verifica aqui.
# Cada check acepta `runner` (firma run(cmd, timeout)) para tests.


def _run_with(runner, cmd: str, timeout: int = 10) -> str:
    fn = runner if runner is not None else run
    try:
        return fn(cmd, timeout=timeout)
    except TypeError:
        return fn(cmd)


def check_pkg_01(collector: FindingCollector, pkg_mgr: str, runner=None) -> None:
    """PKG-01: actualizaciones de seguridad pendientes."""
    if pkg_mgr == "pacman":
        try:
            news_out = _run_with(runner, "curl -s https://news.archlinux.org/index.xml 2>/dev/null", 30)
            sec_pkg_names = set()
            if "<title>" in news_out and "</title>" in news_out:
                for m in re.finditer(r"<title>(.*?)</title>", news_out):
                    title = m.group(1).lower()
                    if any(w in title for w in ["security", "security update"]):
                        sec_pkg_names.add(m.group(1))
            pkg_updates = _run_with(runner, "checkupdates 2>/dev/null", 60)
            sec_updates = 0
            for pkg_line in pkg_updates.splitlines():
                pkg_name = pkg_line.split()[0] if pkg_line.split() else ""
                if pkg_name in sec_pkg_names or any(
                    sn.lower().split(":")[-1].strip().lower() == pkg_name.lower() for sn in sec_pkg_names
                ):
                    sec_updates += 1
        except (OSError, ValueError, re.error) as exc:
            logger.warning("fallo verificando updates pacman (se asume 0): %s", exc)
            sec_updates = 0
        if sec_updates > 0:
            collector.add(
                "PKG-01",
                "updates",
                "P1",
                f"{sec_updates} actualizaciones de seguridad pendientes",
                "Paquetes con actualizaciones de seguridad disponibles",
                "PKG-01",
                "FAIL",
                f"News check -> {sec_updates}",
                "Ejecutar pacman -Syu tras leer noticias Arch",
                "R2",
            )
        else:
            collector.add(
                "PKG-01",
                "updates",
                "P1",
                "Sin actualizaciones de seguridad pendientes",
                "Sistema actualizado en seguridad",
                "PKG-01",
                "PASS",
                "0 actualizaciones de seguridad",
                "",
                "R0",
            )
    elif pkg_mgr == "apt":
        pkg_updates = _run_with(runner, "apt list --upgradable 2>/dev/null | grep -vE '^(Listing|Listando)' ", 60)
        sec_updates = count_nonempty(pkg_updates)
        if sec_updates > 0:
            collector.add(
                "PKG-01",
                "updates",
                "P1",
                f"{sec_updates} actualizaciones pendientes",
                "Actualizaciones disponibles",
                "PKG-01",
                "FAIL",
                f"apt list --upgradable -> {sec_updates}",
                "Ejecutar apt full-upgrade",
                "R2",
            )
        else:
            collector.add(
                "PKG-01",
                "updates",
                "P1",
                "Sin actualizaciones pendientes",
                "Sistema actualizado",
                "PKG-01",
                "PASS",
                "0 actualizaciones",
                "",
                "R0",
            )
    elif pkg_mgr == "dnf":
        sec_updates = to_int(_run_with(runner, "dnf check-update --security 2>/dev/null | grep -v '^$' | wc -l", 60))
        if sec_updates > 0:
            collector.add(
                "PKG-01",
                "updates",
                "P1",
                f"{sec_updates} actualizaciones de seguridad pendientes",
                "Paquetes con actualizaciones de seguridad disponibles",
                "PKG-01",
                "FAIL",
                f"dnf check-update --security -> {sec_updates}",
                "Ejecutar dnf upgrade --security",
                "R2",
            )
        else:
            collector.add(
                "PKG-01",
                "updates",
                "P1",
                "Sin actualizaciones de seguridad pendientes",
                "Sistema actualizado en seguridad",
                "PKG-01",
                "PASS",
                "0 actualizaciones de seguridad",
                "",
                "R0",
            )
    else:
        collector.add(
            "PKG-01",
            "updates",
            "P1",
            "Gestor de paquetes desconocido",
            "No se pudo verificar",
            "PKG-01",
            "SKIP",
            f"pkg_mgr={pkg_mgr}",
            "",
            "R0",
        )


def check_pkg_03(collector: FindingCollector, pkg_mgr: str, runner=None) -> str:
    """PKG-03: kernel running vs installed. Devuelve running_kernel."""
    running_kernel = _run_with(runner, "uname -r", 5).strip()
    installed_kernel = ""
    if pkg_mgr == "pacman":
        for kernel_pkg in ("linux", "linux-lts", "linux-zen", "linux-hardened"):
            kv = _run_with(runner, f"pacman -Q {kernel_pkg} 2>/dev/null | awk '{{print $2}}'").strip()
            if kv:
                installed_kernel = kv
                break
        if not installed_kernel:
            installed_kernel = "unknown"
        running_base = running_kernel.split("-")[0] if "-" in running_kernel else running_kernel
        installed_base = installed_kernel.split("-")[0] if "-" in installed_kernel else installed_kernel
        mismatch = running_base != installed_base
    elif pkg_mgr == "apt":
        installed_kernel = _run_with(
            runner,
            "dpkg -l 'linux-image-*' 2>/dev/null | grep '^ii' | awk '{print $2}' "
            "| grep -E '^linux-image-[0-9]' | sed 's/linux-image-//' | sort -Vr | head -1",
        ).strip()
        mismatch = bool(installed_kernel) and running_kernel != installed_kernel
    elif pkg_mgr == "dnf":
        installed_kernel = _run_with(runner, "rpm -q kernel 2>/dev/null | tail -1 | sed 's/kernel-//'").strip()
        mismatch = bool(installed_kernel) and running_kernel != installed_kernel
    else:
        collector.add(
            "PKG-03",
            "updates",
            "P1",
            "Gestor de paquetes desconocido",
            "No se pudo verificar",
            "PKG-03",
            "SKIP",
            f"pkg_mgr={pkg_mgr}",
            "",
            "R0",
        )
        return running_kernel
    if mismatch:
        collector.add(
            "PKG-03",
            "updates",
            "P1",
            f"Kernel running ({running_kernel}) != installed ({installed_kernel})",
            "Reinicio pendiente para cargar nuevo kernel",
            "PKG-03",
            "FAIL",
            f"uname -r: {running_kernel}, instalado: {installed_kernel}",
            "Reiniciar sistema",
            "R2",
        )
    else:
        collector.add(
            "PKG-03",
            "updates",
            "P1",
            "Kernel running coincide con instalado",
            "No hay reinicio pendiente de kernel",
            "PKG-03",
            "PASS",
            f"running: {running_kernel}, installed: {installed_kernel}",
            "",
            "R0",
        )
    return running_kernel


def check_pkg_05(collector: FindingCollector, pkg_mgr: str, runner=None) -> None:
    """PKG-05: paquetes huerfanos."""
    if pkg_mgr == "pacman":
        orphans = _run_with(runner, "pacman -Qtdq 2>/dev/null", 60)
        orphan_count = count_nonempty(orphans)
        detail, fix = (f"pacman -Qtdq -> {orphan_count} paquetes", "Revisar y eliminar con pacman -Rns $(pacman -Qtdq)")
    elif pkg_mgr == "apt":
        orphans = _run_with(runner, "apt autoremove --dry-run 2>/dev/null | grep '^Remv'", 120)
        orphan_count = count_nonempty(orphans)
        detail, fix = (f"apt autoremove --dry-run -> {orphan_count}", "Ejecutar apt autoremove --purge")
    elif pkg_mgr == "dnf":
        orphans = _run_with(runner, "dnf repoquery --unneeded 2>/dev/null", 60)
        orphan_count = count_nonempty(orphans)
        detail, fix = (f"dnf repoquery --unneeded -> {orphan_count}", "Ejecutar dnf autoremove")
    else:
        collector.add(
            "PKG-05",
            "hygiene",
            "P3",
            "Gestor desconocido",
            "No se pudo verificar",
            "PKG-05",
            "SKIP",
            f"pkg_mgr={pkg_mgr}",
            "",
            "R0",
        )
        return
    if orphan_count > 0:
        collector.add(
            "PKG-05",
            "hygiene",
            "P3",
            f"{orphan_count} paquetes huerfanos detectados",
            "Paquetes sin dependientes que pueden limpiarse",
            "PKG-05",
            "WARN",
            detail,
            fix,
            "R1",
        )
    else:
        collector.add(
            "PKG-05", "hygiene", "P3", "Sin paquetes huerfanos", "Limpio", "PKG-05", "PASS", "0 huerfanos", "", "R0"
        )


def check_pkg_07(collector: FindingCollector, pkg_mgr: str, runner=None) -> None:
    """PKG-07: archivos de configuracion pendientes (.pacnew/pacdiff/ucf)."""
    if pkg_mgr == "pacman":
        pending = _run_with(runner, "find /etc -name '*.pacnew' -o -name '*.pacsave' 2>/dev/null", 30)
        fix = "Ejecutar pacdiff y fusionar cambios"
    elif pkg_mgr == "apt":
        pending = _run_with(
            runner,
            "find /etc -name '*.dpkg-new' -o -name '*.dpkg-old' -o -name '*.ucf-new' -o -name '*.ucf-old' 2>/dev/null",
            30,
        )
        fix = "Revisar con ucf o dpkg-reconfigure"
    elif pkg_mgr == "dnf":
        pending = _run_with(runner, "find /etc -name '*.rpmnew' -o -name '*.rpmsave' 2>/dev/null", 30)
        fix = "Revisar con rpmconf"
    else:
        collector.add(
            "PKG-07",
            "hygiene",
            "P2",
            "Gestor desconocido",
            "No se pudo verificar",
            "PKG-07",
            "SKIP",
            f"pkg_mgr={pkg_mgr}",
            "",
            "R0",
        )
        return
    pending_count = count_nonempty(pending)
    if pending_count > 0:
        collector.add(
            "PKG-07",
            "hygiene",
            "P2",
            f"{pending_count} archivos de configuracion pendientes",
            "Configuraciones nuevas de paquetes no fusionadas",
            "PKG-07",
            "FAIL",
            f"find /etc -> {pending_count}",
            fix,
            "R2",
        )
    else:
        collector.add(
            "PKG-07",
            "hygiene",
            "P2",
            "Sin archivos de configuracion pendientes",
            "Configuraciones al dia",
            "PKG-07",
            "PASS",
            "0 pendientes",
            "",
            "R0",
        )


def check_pkg_06(collector: FindingCollector, pkg_mgr: str, runner=None) -> None:
    """PKG-06: paquetes foraneos (AUR/manuales). Solo audit_full."""
    if pkg_mgr == "pacman":
        foreign_count = count_nonempty(_run_with(runner, "pacman -Qmq 2>/dev/null", 60))
        detail = f"pacman -Qmq -> {foreign_count}"
    elif pkg_mgr == "apt":
        # "manual-installed" NO equivale a "fuera de repos": cuenta también los
        # paquetes marcados a mano que sí existen en los repos (falso positivo
        # masivo verificado: 343 contados vs 8 reales). Se comparan los nombres
        # instalados contra los disponibles en el archive de apt.
        avail = _run_with(
            runner,
            "apt-cache dumpavail 2>/dev/null | awk '/^Package: /{print $2}' | sort -u",
            120,
        )
        avail_names = {line.strip() for line in avail.splitlines() if line.strip()}
        installed = _run_with(runner, "dpkg-query -W -f='${binary:Package}\\n' 2>/dev/null", 60)
        foreign = []
        for line in installed.splitlines():
            name = line.strip()
            if not name:
                continue
            base = name.split(":", 1)[0]
            if base not in avail_names and name not in avail_names:
                foreign.append(base)
        foreign_count = len(foreign)
        detail = f"dpkg-query vs apt-cache dumpavail -> {foreign_count}"
        if foreign:
            detail += ": " + ", ".join(sorted(set(foreign))[:10])
    elif pkg_mgr == "dnf":
        foreign_count = count_nonempty(_run_with(runner, "dnf list extras 2>/dev/null | tail -n +2", 60))
        detail = f"dnf list extras -> {foreign_count}"
    else:
        collector.add(
            "PKG-06",
            "hygiene",
            "P3",
            "Gestor desconocido",
            "No se pudo verificar",
            "PKG-06",
            "SKIP",
            f"pkg_mgr={pkg_mgr}",
            "",
            "R0",
        )
        return
    threshold = 20 if pkg_mgr == "pacman" else 50
    if foreign_count > threshold:
        collector.add(
            "PKG-06",
            "hygiene",
            "P3",
            f"{foreign_count} paquetes foraneos (fuera de repos oficiales)",
            "Muchos paquetes fuera de repositorios oficiales",
            "PKG-06",
            "WARN",
            detail,
            "Revisar y limitar paquetes foraneos/manuales",
            "R1",
        )
    else:
        collector.add(
            "PKG-06",
            "hygiene",
            "P3",
            f"{foreign_count} paquetes foraneos",
            "Cantidad dentro de rango aceptable",
            "PKG-06",
            "PASS",
            detail,
            "",
            "R0",
        )


def check_pkg_09(collector: FindingCollector, pkg_mgr: str, runner=None) -> None:
    """PKG-09: tamano de cache de paquetes. Solo audit_full."""
    if pkg_mgr == "pacman":
        cache_size = to_int(_run_with(runner, "du -sm /var/cache/pacman/pkg 2>/dev/null | cut -f1", 30))
        limit, fix = 2000, "Limpiar cache: paccache -r -k 3"
    elif pkg_mgr == "apt":
        cache_size = to_int(_run_with(runner, "du -sm /var/cache/apt/archives 2>/dev/null | cut -f1", 30))
        limit, fix = 1000, "Limpiar cache: apt autoclean"
    elif pkg_mgr == "dnf":
        cache_size = to_int(_run_with(runner, "du -sm /var/cache/dnf 2>/dev/null | cut -f1", 30))
        limit, fix = 1000, "Limpiar cache: dnf clean packages"
    else:
        collector.add(
            "PKG-09",
            "hygiene",
            "P4",
            "Gestor desconocido",
            "No se pudo verificar",
            "PKG-09",
            "SKIP",
            f"pkg_mgr={pkg_mgr}",
            "",
            "R0",
        )
        return
    if cache_size > limit:
        collector.add(
            "PKG-09",
            "hygiene",
            "P4",
            f"Cache de paquetes: {cache_size}MB (> {limit}MB)",
            "Cache de paquetes muy grande",
            "PKG-09",
            "WARN",
            f"du -sm -> {cache_size}MB",
            fix,
            "R1",
        )
    else:
        collector.add(
            "PKG-09",
            "hygiene",
            "P4",
            f"Cache de paquetes: {cache_size}MB",
            "Tamano de cache aceptable",
            "PKG-09",
            "PASS",
            f"du -sm -> {cache_size}MB",
            "",
            "R0",
        )


def check_pkg_04(collector: FindingCollector, runner=None) -> None:
    """PKG-04: firmware actualizable (fwupd). Solo audit_full."""
    if which("fwupdmgr") is None:
        collector.add(
            "PKG-04",
            "updates",
            "P2",
            "fwupd no instalado",
            "No se puede verificar firmware",
            "PKG-04",
            "SKIP",
            "fwupdmgr no encontrado",
            "Instalar fwupd para verificar firmware",
            "R0",
        )
        return
    fw_updates = to_int(_run_with(runner, "fwupdmgr get-updates 2>/dev/null | grep -c 'Device:'", 60))
    if fw_updates > 0:
        collector.add(
            "PKG-04",
            "updates",
            "P2",
            f"{fw_updates} actualizaciones de firmware disponibles",
            "Dispositivos con firmware actualizable",
            "PKG-04",
            "WARN",
            f"fwupdmgr get-updates -> {fw_updates} dispositivos",
            "Ejecutar: fwupdmgr update",
            "R2",
        )
    else:
        collector.add(
            "PKG-04",
            "updates",
            "P2",
            "Sin actualizaciones de firmware",
            "Firmware al dia",
            "PKG-04",
            "PASS",
            "0 actualizaciones",
            "",
            "R0",
        )


def check_arc_07(collector: FindingCollector, pkg_mgr: str, runner=None) -> None:
    """ARC-07: actualizaciones parciales peligrosas (Arch). Solo audit_full."""
    if pkg_mgr != "pacman":
        collector.add(
            "ARC-07",
            "updates",
            "P4",
            "Verificacion de actualizaciones parciales N/A",
            "Solo aplicable a Arch Linux",
            "ARC-07",
            "SKIP",
            f"PKG_MGR={pkg_mgr}",
            "",
            "R0",
        )
        return
    partial = _run_with(runner, "grep 'pacman -Sy$' /var/log/pacman.log 2>/dev/null | tail -5", 30)
    partial_count = count_nonempty(partial)
    if partial_count > 0:
        collector.add(
            "ARC-07",
            "updates",
            "P1",
            "Actualizaciones parciales detectadas en log",
            "Se detecto 'pacman -Sy' sin '-u' (actualizacion parcial peligrosa)",
            "ARC-07",
            "WARN",
            f"grep 'pacman -Sy$' /var/log/pacman.log -> {partial_count}",
            "Usar siempre 'pacman -Syu' para actualizaciones completas",
            "R2",
        )
    else:
        collector.add(
            "ARC-07",
            "updates",
            "P1",
            "Sin actualizaciones parciales detectadas",
            "Correcto",
            "ARC-07",
            "PASS",
            "0 actualizaciones parciales",
            "",
            "R0",
        )


def check_deb_04(collector: FindingCollector, pkg_mgr: str, runner=None) -> None:
    """DEB-04: unattended-upgrades activo. Solo audit_full en apt."""
    if pkg_mgr != "apt":
        return
    if service_active("unattended-upgrades"):
        collector.add(
            "DEB-04",
            "updates",
            "P2",
            "unattended-upgrades activo",
            "Actualizaciones automaticas de seguridad habilitadas",
            "DEB-04",
            "PASS",
            "systemctl is-active unattended-upgrades -> active",
            "",
            "R0",
        )
    else:
        collector.add(
            "DEB-04",
            "updates",
            "P2",
            "unattended-upgrades INACTIVO",
            "Sin actualizaciones automaticas de seguridad",
            "DEB-04",
            "WARN",
            "systemctl is-active unattended-upgrades -> inactive",
            "Activar: systemctl enable --now unattended-upgrades",
            "R2",
        )


def check_fs_09(collector: FindingCollector, runner=None) -> None:
    """FS-09: symlinks rotos en /etc, /usr, /boot."""
    broken = _run_with(runner, "find /etc /usr /boot -xtype l 2>/dev/null | head -20", 120)
    symlink_count = count_nonempty(broken)
    if symlink_count > 0:
        collector.add(
            "FS-09",
            "hygiene",
            "P3",
            f"{symlink_count} symlinks rotos en /etc, /usr, /boot",
            "Enlaces simbolicos que apuntan a archivos inexistentes",
            "FS-09",
            "WARN",
            f"find /etc /usr /boot -xtype l -> {symlink_count}",
            "Investigar y eliminar symlinks rotos (no borrar ciegamente)",
            "R1",
        )
    else:
        collector.add(
            "FS-09", "hygiene", "P3", "Sin symlinks rotos", "Correcto", "FS-09", "PASS", "0 symlinks rotos", "", "R0"
        )


def check_fs_10_disk(collector: FindingCollector, runner=None) -> None:
    """FS-10: uso de disco critico (higiene)."""
    df_out = _run_with(
        runner, "df -h -x tmpfs -x devtmpfs -x squashfs --output=source,target,pcent 2>/dev/null | tail -n +2", 15
    )
    seen = set()
    for line in df_out.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        source = parts[0]
        if source in seen:
            continue
        seen.add(source)
        mountpoint = parts[1]
        use_pcent = parts[2].rstrip("%")
        if not use_pcent.isdigit():
            continue
        use_pcent_i = int(use_pcent)
        if use_pcent_i >= 90:
            collector.add(
                "FS-10",
                "resources",
                "P1",
                f"Disco {mountpoint} al {use_pcent_i}%",
                "Espacio critico, riesgo de fallo",
                "FS-10",
                "FAIL",
                f"df -h {mountpoint} -> {use_pcent_i}%",
                "Limpiar espacio o expandir particion",
                "R2",
            )
        elif use_pcent_i >= 80:
            collector.add(
                "FS-10",
                "resources",
                "P2",
                f"Disco {mountpoint} al {use_pcent_i}%",
                "Espacio bajo, planificar limpieza",
                "FS-10",
                "WARN",
                f"df -h {mountpoint} -> {use_pcent_i}%",
                "Ejecutar rutina de limpieza",
                "R1",
            )
        else:
            collector.add(
                "FS-10",
                "resources",
                "P4",
                f"Disco {mountpoint} al {use_pcent_i}%",
                "Espacio adecuado",
                "FS-10",
                "PASS",
                f"df -h {mountpoint} -> {use_pcent_i}%",
                "",
                "R0",
            )


def check_fs_11_inodes(collector: FindingCollector, runner=None) -> None:
    """FS-11: uso de inodos. Solo audit_full."""
    inode_out = _run_with(runner, "df -i / /boot /var /home 2>/dev/null | tail -n +2", 15)
    for line in inode_out.splitlines():
        parts = line.split()
        if len(parts) < 6:
            continue
        mountpoint = parts[5]
        inode_pcent = parts[4].rstrip("%")
        if not inode_pcent.isdigit():
            continue
        inode_pcent_i = int(inode_pcent)
        if inode_pcent_i >= 90:
            collector.add(
                "FS-11",
                "resources",
                "P2",
                f"Inodos {mountpoint} al {inode_pcent_i}%",
                "Inodos casi agotados",
                "FS-11",
                "FAIL",
                f"df -i {mountpoint} -> {inode_pcent_i}%",
                "Eliminar archivos pequenos innecesarios",
                "R2",
            )
        elif inode_pcent_i >= 80:
            collector.add(
                "FS-11",
                "resources",
                "P3",
                f"Inodos {mountpoint} al {inode_pcent_i}%",
                "Uso de inodos elevado",
                "FS-11",
                "WARN",
                f"df -i {mountpoint} -> {inode_pcent_i}%",
                "Monitorear uso de inodos",
                "R1",
            )
        else:
            collector.add(
                "FS-11",
                "resources",
                "P4",
                f"Inodos {mountpoint} al {inode_pcent_i}%",
                "Uso de inodos adecuado",
                "FS-11",
                "PASS",
                f"df -i {mountpoint} -> {inode_pcent_i}%",
                "",
                "R0",
            )


def check_log_06(collector: FindingCollector, runner=None) -> None:
    """LOG-06: errores en journal ultimas 24h."""
    emerg = to_int(
        _run_with(runner, "journalctl -p emerg --since '24 hours ago' --no-pager 2>/dev/null | grep -c .", 60)
    )
    alert = to_int(
        _run_with(runner, "journalctl -p alert --since '24 hours ago' --no-pager 2>/dev/null | grep -c .", 60)
    )
    crit = to_int(_run_with(runner, "journalctl -p crit --since '24 hours ago' --no-pager 2>/dev/null | grep -c .", 60))
    err = to_int(_run_with(runner, "journalctl -p err --since '24 hours ago' --no-pager 2>/dev/null | grep -c .", 60))
    journal_errors = emerg + alert + crit + err
    if journal_errors > 50:
        collector.add(
            "LOG-06",
            "stability",
            "P2",
            f"{journal_errors} errores (prioridad 0-3) en ultimas 24h",
            "Alto volumen de errores en logs",
            "LOG-06",
            "WARN",
            f"journalctl -p 0..3 --since '24h' -> {journal_errors} lineas",
            "Investigar errores recurrentes",
            "R0",
        )
    elif journal_errors > 0:
        collector.add(
            "LOG-06",
            "stability",
            "P3",
            f"{journal_errors} errores (prioridad 0-3) en ultimas 24h",
            "Algunos errores en logs",
            "LOG-06",
            "PASS",
            f"journalctl -p 0..3 --since '24h' -> {journal_errors} lineas",
            "Monitorear",
            "R0",
        )
    else:
        collector.add(
            "LOG-06",
            "stability",
            "P4",
            "Sin errores criticos en journal 24h",
            "Logs limpios",
            "LOG-06",
            "PASS",
            "0 errores",
            "",
            "R0",
        )


def check_log_08(collector: FindingCollector, runner=None) -> None:
    """LOG-08: fallos de arranque. Solo audit_full."""
    emerg = to_int(_run_with(runner, "journalctl -b -p emerg --no-pager 2>/dev/null | grep -c .", 60))
    alert = to_int(_run_with(runner, "journalctl -b -p alert --no-pager 2>/dev/null | grep -c .", 60))
    crit = to_int(_run_with(runner, "journalctl -b -p crit --no-pager 2>/dev/null | grep -c .", 60))
    err = to_int(_run_with(runner, "journalctl -b -p err --no-pager 2>/dev/null | grep -c .", 60))
    boot_failures = emerg + alert + crit + err
    if boot_failures > 20:
        collector.add(
            "LOG-08",
            "stability",
            "P2",
            f"{boot_failures} errores en arranque actual",
            "Muchos errores durante el arranque",
            "LOG-08",
            "WARN",
            f"journalctl -b -p 0..3 -> {boot_failures} lineas",
            "Investigar errores de arranque con journalctl -b",
            "R0",
        )
    elif boot_failures > 0:
        collector.add(
            "LOG-08",
            "stability",
            "P3",
            f"{boot_failures} errores en arranque actual",
            "Algunos errores durante el arranque",
            "LOG-08",
            "PASS",
            f"journalctl -b -p 0..3 -> {boot_failures} lineas",
            "Monitorear",
            "R0",
        )
    else:
        collector.add(
            "LOG-08",
            "stability",
            "P4",
            "Sin errores en arranque actual",
            "Arranque limpio",
            "LOG-08",
            "PASS",
            "0 errores",
            "",
            "R0",
        )


def check_srv_02(collector: FindingCollector, runner=None) -> None:
    """SRV-02: servicios systemd fallidos."""
    failed_svcs = _run_with(runner, "systemctl --failed --no-legend --no-pager 2>/dev/null", 15)
    failed_count = count_nonempty(failed_svcs)
    if failed_count > 0:
        collector.add(
            "SRV-02",
            "resources",
            "P1",
            f"{failed_count} servicios systemd fallidos",
            "Servicios que no iniciaron correctamente — riesgo de disponibilidad",
            "SRV-02",
            "FAIL",
            f"systemctl --failed -> {failed_count}",
            "Investigar con systemctl status <servicio> y journalctl -u <servicio>",
            "R2",
        )
    else:
        collector.add(
            "SRV-02",
            "resources",
            "P1",
            "Sin servicios fallidos",
            "Todos los servicios activos",
            "SRV-02",
            "PASS",
            "0 fallidos",
            "",
            "R0",
        )


def check_net_04(collector: FindingCollector, runner=None) -> None:
    """NET-04: SSH expuesto a Internet."""
    ssh_listening = _run_with(runner, "ss -tuln 2>/dev/null | grep ':22 '", 10)
    if ssh_listening.strip():
        if "0.0.0.0:22" in ssh_listening or ":::22" in ssh_listening:
            collector.add(
                "NET-04",
                "security",
                "P0",
                "SSH escuchando en todas las interfaces (0.0.0.0/::)",
                "SSH expuesto a Internet potencialmente",
                "NET-04",
                "WARN",
                f"ss -tuln | grep :22 -> {ssh_listening.strip()}",
                "Restringir SSH a interfaces internas o usar firewall",
                "R2",
            )
        else:
            collector.add(
                "NET-04",
                "security",
                "P0",
                "SSH escuchando en interfaz especifica",
                "No expuesto a todas las interfaces",
                "NET-04",
                "PASS",
                f"ss -tuln | grep :22 -> {ssh_listening.strip()}",
                "",
                "R0",
            )
    else:
        collector.add(
            "NET-04",
            "security",
            "P0",
            "SSH no esta escuchando en puerto 22",
            "Puerto SSH no estandar o servicio detenido",
            "NET-04",
            "PASS",
            "ss -tuln | grep :22 -> (none)",
            "",
            "R0",
        )


def main(argv: list[str] | None = None) -> int:
    """Entry point librería común (no ejecuta auditoría; solo --help/self-check)."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Utilidades compartidas mantenimiento-linux (librería, sin acción por defecto)."
    )
    parser.add_argument("--verbose", action="store_true", help="Logging verboso a stderr")
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Verifica imports y funciones puras básicas (no toca el sistema)",
    )
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    if args.self_check:
        try:
            assert count_nonempty("a\n\nb\n") == 2
            assert to_int("42") == 42 and to_int("x", default=7) == 7
            c = FindingCollector()
            c.add("T-01", "security", "P0", "t", "d", "c", "PASS", "e", "", "R0")
            assert c.passed == 1 and c.total == 1
        except AssertionError as exc:
            logger.error("self-check fallido: %s", exc)
            return 1
        print("common self-check OK")
        return 0
    parser.print_usage(sys.stdout)
    print("common.py es una librería; impórtala desde los demás scripts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
