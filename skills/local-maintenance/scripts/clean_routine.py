#!/usr/bin/env python3
"""clean_routine.py - Limpieza aprobada (cache, journal, huérfanos, temporales).

Single path: operation_id → validate → approve → handler → record.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from common import (
    BLUE,
    GREEN,
    RED,
    SKILL_VERSION,
    color,
    hostname,
    log_warn,
    run,
    run_capture,
    utcnow_iso,
    which,
)

try:
    import risk_gate
except ImportError:  # pragma: no cover
    risk_gate = None  # type: ignore

# Ensure tools/ is importable for execution registry
_TOOLS = Path(__file__).resolve().parents[3] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

DRY_RUN = True
EXECUTE = False
SNAPSHOT_ID = ""
OUTPUT_FILE = ""
JSON_OUTPUT = ""
PKG_MGR = ""
KEEP_VERSIONS = 3
JOURNAL_VACUUM_TIME = "7d"
JOURNAL_VACUUM_SIZE = "500M"
JSON_MODE = False
WITH_FIRMWARE = False
ACTION_RESULTS: list[dict[str, object]] = []

logger = logging.getLogger("mantenimiento.clean")

CLEAN_OPS = (
    "clean_package_cache",
    "clean_journal",
    "clean_orphans",
    "clean_temp",
    "clean_needrestart",
    "update_firmware",
    "clean_userspace_caches",
)


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s", stream=sys.stderr)
    else:
        logging.getLogger().setLevel(level)


def log_info(msg: str) -> None:
    print(color(f"[CLEAN] {msg}", BLUE))


def log_success(msg: str) -> None:
    print(color(f"[SUCCESS] {msg}", GREEN))


def log_error(msg: str) -> None:
    logger.error("%s", msg)
    print(color(f"[ERROR] {msg}", RED))


def detect_pkg_mgr() -> str:
    """Detecta gestor; devuelve '' si no hay ninguno (main decide exit 1)."""
    mgr = ""
    if which("pacman"):
        mgr = "pacman"
    if which("apt"):
        mgr = "apt"
    if which("dnf"):
        mgr = "dnf"
    return mgr


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rutina de limpieza aprobada (por defecto --dry-run).")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", dest="dry_run", action="store_true", default=None, help="Solo simular (defecto)")
    mode.add_argument("--execute", dest="execute", action="store_true", default=None, help="Ejecutar limpieza real")
    parser.add_argument("--snapshot-id", default="", help="ID de snapshot previo (requerido en --execute)")
    parser.add_argument("--output", default="", help="Fichero de salida (reservado)")
    parser.add_argument("--keep-versions", type=int, default=3, help="Versiones a conservar en caché (defecto 3)")
    parser.add_argument("--journal-time", default="7d", help="Vacuum time del journal (defecto 7d)")
    parser.add_argument("--journal-size", default="500M", help="Vacuum size del journal (defecto 500M)")
    parser.add_argument("--json", nargs="?", const="", default=None, help="Generar JSON (opcional fichero)")
    parser.add_argument(
        "--firmware", action="store_true", default=False, help="Incluir fwupdmgr update (R2, solo con --execute)"
    )
    parser.add_argument("--verbose", action="store_true", help="Logging verboso a stderr")
    return parser


def apply_args(args: argparse.Namespace) -> None:
    global DRY_RUN, EXECUTE, SNAPSHOT_ID, OUTPUT_FILE, JSON_OUTPUT
    global KEEP_VERSIONS, JOURNAL_VACUUM_TIME, JOURNAL_VACUUM_SIZE, JSON_MODE
    global WITH_FIRMWARE
    if args.execute:
        DRY_RUN, EXECUTE = False, True
    else:
        DRY_RUN, EXECUTE = True, False
    SNAPSHOT_ID = args.snapshot_id or ""
    OUTPUT_FILE = args.output or ""
    KEEP_VERSIONS = args.keep_versions
    JOURNAL_VACUUM_TIME = args.journal_time
    JOURNAL_VACUUM_SIZE = args.journal_size
    WITH_FIRMWARE = bool(args.firmware)
    if args.json is not None:
        JSON_MODE = True
        JSON_OUTPUT = args.json or ""
    else:
        JSON_MODE = False
        JSON_OUTPUT = ""


def _record(action: str, status: str, rc: int = 0, detail: str = "") -> None:
    ACTION_RESULTS.append({"action": action, "status": status, "rc": rc, "detail": detail})


def _snapshot_dir() -> str:
    return os.environ.get(
        "SNAPSHOT_DIR",
        os.path.expanduser("~/.local/share/mantenimiento-linux/snapshots"),
    )


def validate_snapshot(snapshot_id: str) -> tuple[bool, str]:
    """Validate snapshot id, directory, coverage and integrity before mutation."""
    if not snapshot_id or "/" in snapshot_id or snapshot_id in (".", ".."):
        return False, "invalid snapshot_id"
    path = os.path.join(_snapshot_dir(), snapshot_id)
    if not os.path.isdir(path):
        return False, f"snapshot directory missing: {path}"
    meta_path = os.path.join(path, "metadata.json")
    if not os.path.isfile(meta_path):
        return False, "metadata.json missing"
    try:
        with open(meta_path, encoding="utf-8") as fh:
            meta = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"metadata unreadable: {exc}"
    if not isinstance(meta, dict):
        return False, "metadata must be an object"
    # Require explicit identity and scope — incomplete metadata is insufficient (H08)
    for key in ("id", "target_host", "backend", "coverage", "content_hash"):
        val = meta.get(key)
        if val is None or (isinstance(val, str) and not str(val).strip()):
            return False, f"metadata missing required field: {key}"
    if meta.get("id") != snapshot_id:
        return False, "metadata id does not match snapshot_id"
    if meta.get("backend_status") == "failed":
        return False, "snapshot backend_status=failed"
    if meta.get("recovery_scope") in (None, "", "none") and meta.get("backend_required"):
        return False, "recovery_scope insufficient with required backend"
    # Recompute content hash over inventory files (exclude metadata.json itself)
    import hashlib

    h = hashlib.sha256()
    for dirpath, _, filenames in os.walk(path):
        for name in sorted(filenames):
            if name == "metadata.json":
                continue
            fp = os.path.join(dirpath, name)
            if os.path.islink(fp):
                h.update(os.readlink(fp).encode())
            elif os.path.isfile(fp):
                with open(fp, "rb") as fh:
                    for chunk in iter(lambda: fh.read(65536), b""):
                        h.update(chunk)
    digest = h.hexdigest()
    if digest != str(meta.get("content_hash")):
        return False, "snapshot content_hash mismatch"
    return True, path


def effective_operation_params() -> dict:
    """Full effective plan — everything handlers may use (not just snapshot_id)."""
    return {
        "snapshot_id": SNAPSHOT_ID,
        "pkg_mgr": PKG_MGR,
        "keep_versions": KEEP_VERSIONS,
        "journal_time": JOURNAL_VACUUM_TIME,
        "journal_size": JOURNAL_VACUUM_SIZE,
        "with_firmware": WITH_FIRMWARE,
    }


def apply_operation_params(params: dict) -> None:
    """Bind approved plan into process state before handler body runs."""
    global SNAPSHOT_ID, PKG_MGR, KEEP_VERSIONS, JOURNAL_VACUUM_TIME, JOURNAL_VACUUM_SIZE
    global WITH_FIRMWARE
    if params.get("snapshot_id"):
        SNAPSHOT_ID = str(params["snapshot_id"])
    if "pkg_mgr" in params and params["pkg_mgr"] is not None:
        PKG_MGR = str(params["pkg_mgr"])
    if "keep_versions" in params and params["keep_versions"] is not None:
        KEEP_VERSIONS = int(params["keep_versions"])
    if "journal_time" in params and params["journal_time"] is not None:
        JOURNAL_VACUUM_TIME = str(params["journal_time"])
    if "journal_size" in params and params["journal_size"] is not None:
        JOURNAL_VACUUM_SIZE = str(params["journal_size"])
    if "with_firmware" in params and params["with_firmware"] is not None:
        WITH_FIRMWARE = bool(params["with_firmware"])


def _register_handlers() -> None:
    from execution.registry import register_handler

    def _wrap(fn):
        def handler(params: dict) -> int:
            apply_operation_params(params or {})
            result = fn()
            # None is never success — let run_registered treat it as blocked.
            if result is None:
                return None  # type: ignore[return-value]
            return int(result)

        return handler

    register_handler("clean_package_cache", _wrap(clean_package_cache))
    register_handler("clean_journal", _wrap(clean_journal))
    register_handler("clean_orphans", _wrap(clean_orphans))
    register_handler("clean_temp", _wrap(clean_temp))
    register_handler("clean_needrestart", _wrap(clean_needrestart))
    register_handler("update_firmware", _wrap(update_firmware))
    register_handler("clean_userspace_caches", _wrap(clean_userspace_caches))
    register_handler("create_snapshot", _handle_create_snapshot)
    register_handler("validate_snapshot", _handle_validate_snapshot)


def _handle_create_snapshot(params: dict) -> int:
    """Invoke snapshot backend in-process after registry approval (no env consent)."""
    global SNAPSHOT_ID
    apply_operation_params(params or {})
    sid = params.get("snapshot_id") or SNAPSHOT_ID
    if not sid:
        sid = f"snap-{utcnow_iso().replace('-', '').replace(':', '').replace('T', '-').replace('Z', '')}"
        SNAPSHOT_ID = sid
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    import snapshot_state as snap  # noqa: WPS433

    base_dir = params.get("snapshot_dir") or _snapshot_dir()
    rc = snap.create_snapshot_backend(sid, base_dir)
    if rc != 0:
        log_error(f"Creación de snapshot falló (rc={rc})")
        return rc
    SNAPSHOT_ID = sid
    log_info(f"Snapshot ID: {SNAPSHOT_ID}")
    return 0


def _handle_validate_snapshot(params: dict) -> int:
    apply_operation_params(params or {})
    sid = str(params.get("snapshot_id") or SNAPSHOT_ID)
    ok, detail = validate_snapshot(sid)
    if not ok:
        log_error(f"Snapshot inválido: {detail}")
        return 1
    return 0


def dispatch_operation(operation_id: str) -> int:
    """Single path: dry-run simulates; execute goes through registry approval + handler."""
    if operation_id == "update_firmware" and not WITH_FIRMWARE:
        _record(operation_id, "skipped", 0, "requires --firmware")
        return 0

    if DRY_RUN:
        log_info(f"[DRY-RUN] {operation_id}")
        _record(operation_id, "simulated", 0, "dry-run")
        return 0

    from execution.ops import run_registered

    params = effective_operation_params()
    result = run_registered(operation_id, params, target=hostname() or ".")
    if result.outcome == "blocked":
        log_error(f"blocked {operation_id}: {result.detail}")
        _record(operation_id, "blocked", result.returncode or 3, result.detail)
        return 3
    if result.outcome == "succeeded":
        log_success(f"OK: {operation_id}")
        _record(operation_id, "succeeded", 0, result.run_id)
        return 0
    log_error(f"FALLÓ: {operation_id}: {result.detail}")
    _record(operation_id, "failed", result.returncode or 1, result.detail)
    return 1


def clean_package_cache() -> int:
    log_info("=== Limpieza de caché de paquetes ===")
    if PKG_MGR == "pacman":
        cache_size = run("du -sh /var/cache/pacman/pkg 2>/dev/null | cut -f1", timeout=30).strip()
        log_info(f"Tamaño actual: {cache_size}")
        rc, _ = run_capture(f"paccache -r -k {KEEP_VERSIONS} 2>/dev/null", timeout=600)
        if rc != 0:
            log_warn("paccache falló")
            raise RuntimeError("paccache failed")
    elif PKG_MGR == "apt":
        cache_size = run("du -sh /var/cache/apt/archives 2>/dev/null | cut -f1", timeout=30).strip()
        log_info(f"Tamaño actual: {cache_size}")
        rc, _ = run_capture("apt-get autoclean 2>/dev/null", timeout=600)
        if rc != 0:
            log_warn("apt-get autoclean falló")
            raise RuntimeError("apt autoclean failed")
    elif PKG_MGR == "dnf":
        cache_size = run("du -sh /var/cache/dnf 2>/dev/null | cut -f1", timeout=30).strip()
        log_info(f"Tamaño actual: {cache_size}")
        rc, _ = run_capture("dnf clean packages -y 2>/dev/null", timeout=600)
        if rc != 0:
            log_warn("dnf clean falló")
            raise RuntimeError("dnf clean failed")
    return 0


def clean_journal() -> int:
    log_info("=== Limpieza de journal ===")
    journal_size = run("journalctl --disk-usage 2>/dev/null", timeout=15).strip()
    log_info(f"Tamaño actual: {journal_size}")
    rc, _ = run_capture(
        f"journalctl --vacuum-time={JOURNAL_VACUUM_TIME} --vacuum-size={JOURNAL_VACUUM_SIZE} 2>/dev/null",
        timeout=600,
    )
    if rc != 0:
        log_warn("journal vacuum falló")
        raise RuntimeError("journal vacuum failed")
    return 0


def clean_orphans() -> int:
    log_info("=== Limpieza de paquetes huérfanos ===")
    if PKG_MGR == "pacman":
        orphans = run("pacman -Qtdq 2>/dev/null", timeout=60).strip()
        orphan_list = [p for p in orphans.splitlines() if p.strip()]
        if not orphan_list:
            log_info("Sin paquetes huérfanos")
            return 0
        log_info(f"Huérfanos detectados: {len(orphan_list)}")
        for pkg in orphan_list:
            log_info(f"Eliminando: {pkg}")
            rc, _ = run_capture(f"pacman -Rns {pkg} --noconfirm 2>/dev/null", timeout=600)
            if rc != 0:
                log_warn(f"No se pudo eliminar {pkg}")
    elif PKG_MGR == "apt":
        rc, _ = run_capture("apt autoremove --purge -y 2>/dev/null", timeout=600)
        if rc != 0:
            log_warn("apt autoremove falló")
            raise RuntimeError("apt autoremove failed")
    elif PKG_MGR == "dnf":
        rc, _ = run_capture("dnf autoremove -y 2>/dev/null", timeout=600)
        if rc != 0:
            log_warn("dnf autoremove falló")
            raise RuntimeError("dnf autoremove failed")
    return 0


def clean_temp() -> int:
    log_info("=== Limpieza de archivos temporales ===")
    run("find /tmp -type f -atime +7 -delete 2>/dev/null", timeout=300)
    run("find /var/tmp -type f -atime +7 -delete 2>/dev/null", timeout=300)
    log_success("Temporales limpiados")
    return 0


def clean_needrestart() -> int:
    log_info("=== Servicios que piden reinicio (needrestart) ===")
    if which("needrestart") is None:
        log_info("needrestart no instalado (instalar para detectar reinicios pendientes)")
        return 0
    rc, _ = run_capture("needrestart -r a 2>/dev/null", timeout=600)
    if rc != 0:
        log_warn("needrestart -r a fallo o requirio intervencion")
        raise RuntimeError("needrestart failed")
    return 0


def update_firmware() -> int:
    log_info("=== Firmware (fwupdmgr, R2) ===")
    if which("fwupdmgr") is None:
        log_info("fwupd no instalado")
        return 0
    if not WITH_FIRMWARE:
        log_info("Omitido: requiere --firmware explicito (R2)")
        return 0
    rc, _ = run_capture("fwupdmgr update 2>/dev/null", timeout=900)
    if rc != 0:
        log_warn("fwupdmgr update fallo")
        raise RuntimeError("fwupdmgr failed")
    return 0


def clean_userspace_caches() -> int:
    import os as _os

    log_info("=== Caches userspace ===")
    home = _os.path.expanduser("~")
    cache_dir = _os.path.join(home, ".cache")
    size = run(f"du -sh {cache_dir} 2>/dev/null | cut -f1", timeout=60).strip()
    log_info(f"Tamano ~/.cache: {size or '?'}")
    thumb = _os.path.join(cache_dir, "thumbnails")
    run(f"rm -rf {thumb}/* 2>/dev/null", timeout=120)
    run(
        f"find {cache_dir} -type f -atime +30 ! -path '*mozilla*' ! -path '*chromium*' "
        "! -path '*Chromium*' ! -path '*Proton*' -delete 2>/dev/null",
        timeout=300,
    )
    log_success("Caches userspace limpiadas")
    return 0


def verify_clean() -> None:
    log_info("=== Verificación post-limpieza ===")
    failed = run("systemctl --failed --no-legend --no-pager 2>/dev/null", timeout=15)
    failed_count = sum(1 for line in failed.splitlines() if line.strip())
    if failed_count > 0:
        log_warn(f"{failed_count} servicios fallidos detectados")
    else:
        log_success("Sin servicios fallidos")

    df_out = run("df -h / 2>/dev/null | tail -1", timeout=15).strip()
    if df_out:
        print(df_out)
    journal_out = run("journalctl --disk-usage 2>/dev/null", timeout=15).strip()
    if journal_out:
        print(journal_out)


def generate_json_output() -> None:
    json_file = (
        JSON_OUTPUT
        or f"clean-routine-{utcnow_iso().replace('-', '').replace(':', '').replace('T', '-').replace('Z', '')}.json"
    )
    actions = list(ACTION_RESULTS)
    if not actions:
        for name in CLEAN_OPS:
            if name == "update_firmware" and not WITH_FIRMWARE:
                actions.append({"action": name, "status": "skipped", "rc": 0, "detail": ""})
            elif DRY_RUN:
                actions.append({"action": name, "status": "simulated", "rc": 0, "detail": ""})
            else:
                actions.append({"action": name, "status": "failed", "rc": 1, "detail": "no result recorded"})
    completed = sum(1 for a in actions if a.get("status") == "succeeded")
    failed = sum(1 for a in actions if a.get("status") in ("failed", "blocked"))
    simulated = sum(1 for a in actions if a.get("status") == "simulated")
    skipped = sum(1 for a in actions if a.get("status") == "skipped")
    result = {
        "metadata": {
            "timestamp": utcnow_iso(),
            "mode": "clean-routine",
            "hostname": hostname(),
            "distro": PKG_MGR,
            "dry_run": DRY_RUN,
            "snapshot_id": SNAPSHOT_ID or "none",
            "skill_version": SKILL_VERSION,
        },
        "actions": actions,
        "summary": {
            "total_actions": len(actions),
            "completed": completed,
            "failed": failed,
            "simulated": simulated,
            "skipped": skipped,
        },
    }
    try:
        with open(json_file, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
    except (OSError, TypeError, ValueError) as exc:
        logger.error("no se pudo escribir JSON %r: %s", json_file, exc)
        raise
    log_info(f"JSON output: {json_file}")


def _ensure_snapshot_for_execute() -> int:
    """Authorize snapshot create/validate before any host effect."""
    global SNAPSHOT_ID
    from execution.ops import run_registered

    if not SNAPSHOT_ID:
        log_warn("No se especificó --snapshot-id. Creando snapshot (requiere aprobación)...")
        result = run_registered("create_snapshot", {}, target=hostname() or ".")
        if result.outcome != "succeeded":
            _record("create_snapshot", result.outcome, result.returncode or 1, result.detail)
            return 3 if result.outcome == "blocked" else 1
        _record("create_snapshot", "succeeded", 0, result.run_id)
    else:
        result = run_registered(
            "validate_snapshot",
            {"snapshot_id": SNAPSHOT_ID},
            target=hostname() or ".",
        )
        # validate_snapshot is read — still go through registry
        if result.outcome == "blocked":
            # read ops shouldn't block on approval; treat handler failure
            pass
        if result.outcome not in ("succeeded",) and result.outcome != "blocked":
            ok, detail = validate_snapshot(SNAPSHOT_ID)
            if not ok:
                _record("validate_snapshot", "failed", 1, detail)
                return 1
        ok, detail = validate_snapshot(SNAPSHOT_ID)
        if not ok:
            log_error(f"Snapshot inválido: {detail}")
            _record("validate_snapshot", "failed", 1, detail)
            return 1
        _record("validate_snapshot", "succeeded", 0, detail)
    return 0


def main(argv: list[str] | None = None) -> int:
    global SNAPSHOT_ID, PKG_MGR
    ACTION_RESULTS.clear()
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    apply_args(args)
    _register_handlers()

    PKG_MGR = detect_pkg_mgr()
    if not PKG_MGR:
        logger.error("No se pudo detectar gestor de paquetes")
        log_error("No se pudo detectar gestor de paquetes")
        return 1

    log_info("Iniciando rutina de limpieza")
    log_info("Modo: " + ("DRY-RUN" if DRY_RUN else "EJECUCIÓN"))
    log_info(f"Gestor de paquetes: {PKG_MGR}")

    if EXECUTE:
        snap_rc = _ensure_snapshot_for_execute()
        if snap_rc != 0:
            if JSON_MODE:
                try:
                    generate_json_output()
                except (OSError, TypeError, ValueError):
                    pass
            return snap_rc

    for op_id in CLEAN_OPS:
        dispatch_operation(op_id)

    if EXECUTE and not any(a.get("status") == "blocked" for a in ACTION_RESULTS):
        # Post-clean verify is read-only
        try:
            verify_clean()
        except Exception as exc:  # noqa: BLE001
            log_warn(f"verify_clean: {exc}")

    failed = sum(1 for a in ACTION_RESULTS if a.get("status") in ("failed", "blocked"))
    if failed:
        log_error(f"Rutina finalizada con {failed} acción(es) fallidas/bloqueadas")
    else:
        log_info("Rutina de limpieza completada")

    if JSON_MODE:
        try:
            generate_json_output()
        except (OSError, TypeError, ValueError) as exc:
            logger.error("no se pudo generar JSON: %s", exc)
            return 1
    if failed and EXECUTE:
        return 1
    if any(a.get("status") == "blocked" for a in ACTION_RESULTS) and EXECUTE:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
