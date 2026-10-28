#!/usr/bin/env python3

"""clean_routine.py - Limpieza aprobada (cache, journal, huérfanos, temporales).

Single path: operation_id → validate → approve → handler → record.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import logging
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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

import snapshot_state as snap

# Ensure tools/ is importable for execution registry
_TOOLS = Path(__file__).resolve().parents[3] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from execution.ops import run_registered  # noqa: E402  # requiere _TOOLS en sys.path
from execution.registry import register_handler  # noqa: E402  # requiere _TOOLS en sys.path


@dataclass
class _CleanState:
    """Estado del proceso; sustituye a las variables globales de módulo."""

    dry_run: bool = True
    execute: bool = False
    snapshot_id: str = ""
    output_file: str = ""
    json_output: str = ""
    pkg_mgr: str = ""
    keep_versions: int = 3
    journal_vacuum_time: str = "7d"
    journal_vacuum_size: str = "500M"
    json_mode: bool = False
    with_firmware: bool = False


_STATE = _CleanState()

REQUIRED_META_FIELDS = ("id", "target_host", "backend", "coverage", "content_hash")
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
    if args.execute:
        _STATE.dry_run, _STATE.execute = False, True
    else:
        _STATE.dry_run, _STATE.execute = True, False
    _STATE.snapshot_id = args.snapshot_id or ""
    _STATE.output_file = args.output or ""
    _STATE.keep_versions = args.keep_versions
    _STATE.journal_vacuum_time = args.journal_time
    _STATE.journal_vacuum_size = args.journal_size
    _STATE.with_firmware = bool(args.firmware)
    if args.json is not None:
        _STATE.json_mode = True
        _STATE.json_output = args.json or ""
    else:
        _STATE.json_mode = False
        _STATE.json_output = ""


def _record(action: str, status: str, rc: int = 0, detail: str = "") -> None:
    ACTION_RESULTS.append({"action": action, "status": status, "rc": rc, "detail": detail})


def _snapshot_dir() -> str:
    return os.environ.get(
        "SNAPSHOT_DIR",
        os.path.expanduser("~/.local/share/mantenimiento-linux/snapshots"),
    )


def _snapshot_id_error(snapshot_id: str) -> str | None:
    if not snapshot_id or "/" in snapshot_id or snapshot_id in (".", ".."):
        return "invalid snapshot_id"
    return None


def _load_snapshot_meta(path: str) -> tuple[dict[str, Any] | None, str]:
    meta_path = os.path.join(path, "metadata.json")
    if not os.path.isfile(meta_path):
        return None, "metadata.json missing"
    try:
        with open(meta_path, encoding="utf-8") as fh:
            meta = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"metadata unreadable: {exc}"
    if not isinstance(meta, dict):
        return None, "metadata must be an object"
    return meta, ""


def _missing_meta_field(meta: dict[str, Any]) -> str | None:
    # Require explicit identity and scope — incomplete metadata is insufficient (H08)
    for key in REQUIRED_META_FIELDS:
        val = meta.get(key)
        if val is None or (isinstance(val, str) and not str(val).strip()):
            return f"metadata missing required field: {key}"
    return None


def _content_digest(path: str) -> str:
    # Recompute content hash over inventory files (exclude metadata.json itself)
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
    return h.hexdigest()


def _snapshot_meta_error(meta: dict[str, Any], snapshot_id: str, path: str) -> str | None:
    missing = _missing_meta_field(meta)
    if missing:
        return missing
    if meta.get("id") != snapshot_id:
        return "metadata id does not match snapshot_id"
    if meta.get("backend_status") == "failed":
        return "snapshot backend_status=failed"
    if meta.get("recovery_scope") in (None, "", "none") and meta.get("backend_required"):
        return "recovery_scope insufficient with required backend"
    if _content_digest(path) != str(meta.get("content_hash")):
        return "snapshot content_hash mismatch"
    return None


def validate_snapshot(snapshot_id: str) -> tuple[bool, str]:
    """Validate snapshot id, directory, coverage and integrity before mutation."""
    id_error = _snapshot_id_error(snapshot_id)
    if id_error:
        return False, id_error
    path = os.path.join(_snapshot_dir(), snapshot_id)
    if not os.path.isdir(path):
        return False, f"snapshot directory missing: {path}"
    meta, meta_error = _load_snapshot_meta(path)
    if meta is None:
        return False, meta_error
    error = _snapshot_meta_error(meta, snapshot_id, path)
    if error:
        return False, error
    return True, path


def effective_operation_params() -> dict[str, Any]:
    """Full effective plan — everything handlers may use (not just snapshot_id)."""
    return {
        "snapshot_id": _STATE.snapshot_id,
        "pkg_mgr": _STATE.pkg_mgr,
        "keep_versions": _STATE.keep_versions,
        "journal_time": _STATE.journal_vacuum_time,
        "journal_size": _STATE.journal_vacuum_size,
        "with_firmware": _STATE.with_firmware,
    }


def apply_operation_params(params: dict[str, Any]) -> None:
    """Bind approved plan into process state before handler body runs."""
    if params.get("snapshot_id"):
        _STATE.snapshot_id = str(params["snapshot_id"])
    if "pkg_mgr" in params and params["pkg_mgr"] is not None:
        _STATE.pkg_mgr = str(params["pkg_mgr"])
    if "keep_versions" in params and params["keep_versions"] is not None:
        _STATE.keep_versions = int(params["keep_versions"])
    if "journal_time" in params and params["journal_time"] is not None:
        _STATE.journal_vacuum_time = str(params["journal_time"])
    if "journal_size" in params and params["journal_size"] is not None:
        _STATE.journal_vacuum_size = str(params["journal_size"])
    if "with_firmware" in params and params["with_firmware"] is not None:
        _STATE.with_firmware = bool(params["with_firmware"])


def _register_handlers() -> None:

    def _wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
        def handler(params: dict[str, Any]) -> int:
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


def _handle_create_snapshot(params: dict[str, Any]) -> int:
    """Invoke snapshot backend in-process after registry approval (no env consent)."""
    apply_operation_params(params or {})
    sid = params.get("snapshot_id") or _STATE.snapshot_id
    if not sid:
        sid = f"snap-{utcnow_iso().replace('-', '').replace(':', '').replace('T', '-').replace('Z', '')}"
        _STATE.snapshot_id = sid
    base_dir = params.get("snapshot_dir") or _snapshot_dir()
    rc = snap.create_snapshot_backend(sid, base_dir)
    if rc != 0:
        log_error(f"Creación de snapshot falló (rc={rc})")
        return rc
    _STATE.snapshot_id = sid
    log_info(f"Snapshot ID: {_STATE.snapshot_id}")
    return 0


def _handle_validate_snapshot(params: dict[str, Any]) -> int:
    apply_operation_params(params or {})
    sid = str(params.get("snapshot_id") or _STATE.snapshot_id)
    ok, detail = validate_snapshot(sid)
    if not ok:
        log_error(f"Snapshot inválido: {detail}")
        return 1
    return 0


def dispatch_operation(operation_id: str) -> int:
    """Single path: dry-run simulates; execute goes through registry approval + handler."""
    if operation_id == "update_firmware" and not _STATE.with_firmware:
        _record(operation_id, "skipped", 0, "requires --firmware")
        return 0

    if _STATE.dry_run:
        log_info(f"[DRY-RUN] {operation_id}")
        _record(operation_id, "simulated", 0, "dry-run")
        return 0

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
    if _STATE.pkg_mgr == "pacman":
        cache_size = run("du -sh /var/cache/pacman/pkg 2>/dev/null | cut -f1", timeout=30).strip()
        log_info(f"Tamaño actual: {cache_size}")
        rc, _ = run_capture(f"paccache -r -k {_STATE.keep_versions} 2>/dev/null", timeout=600)
        if rc != 0:
            log_warn("paccache falló")
            raise RuntimeError("paccache failed")
    elif _STATE.pkg_mgr == "apt":
        cache_size = run("du -sh /var/cache/apt/archives 2>/dev/null | cut -f1", timeout=30).strip()
        log_info(f"Tamaño actual: {cache_size}")
        rc, _ = run_capture("apt-get autoclean 2>/dev/null", timeout=600)
        if rc != 0:
            log_warn("apt-get autoclean falló")
            raise RuntimeError("apt autoclean failed")
    elif _STATE.pkg_mgr == "dnf":
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
        f"journalctl --vacuum-time={_STATE.journal_vacuum_time} --vacuum-size={_STATE.journal_vacuum_size} 2>/dev/null",
        timeout=600,
    )
    if rc != 0:
        log_warn("journal vacuum falló")
        raise RuntimeError("journal vacuum failed")
    return 0


def clean_orphans() -> int:
    log_info("=== Limpieza de paquetes huérfanos ===")
    if _STATE.pkg_mgr == "pacman":
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
    elif _STATE.pkg_mgr == "apt":
        rc, _ = run_capture("apt autoremove --purge -y 2>/dev/null", timeout=600)
        if rc != 0:
            log_warn("apt autoremove falló")
            raise RuntimeError("apt autoremove failed")
    elif _STATE.pkg_mgr == "dnf":
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
    if not _STATE.with_firmware:
        log_info("Omitido: requiere --firmware explicito (R2)")
        return 0
    rc, _ = run_capture("fwupdmgr update 2>/dev/null", timeout=900)
    if rc != 0:
        log_warn("fwupdmgr update fallo")
        raise RuntimeError("fwupdmgr failed")
    return 0


def clean_userspace_caches() -> int:
    log_info("=== Caches userspace ===")
    home = os.path.expanduser("~")
    cache_dir = os.path.join(home, ".cache")
    size = run(f"du -sh {cache_dir} 2>/dev/null | cut -f1", timeout=60).strip()
    log_info(f"Tamano ~/.cache: {size or '?'}")
    thumb = os.path.join(cache_dir, "thumbnails")
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
        _STATE.json_output
        or f"clean-routine-{utcnow_iso().replace('-', '').replace(':', '').replace('T', '-').replace('Z', '')}.json"
    )
    actions = list(ACTION_RESULTS)
    if not actions:
        for name in CLEAN_OPS:
            if name == "update_firmware" and not _STATE.with_firmware:
                actions.append({"action": name, "status": "skipped", "rc": 0, "detail": ""})
            elif _STATE.dry_run:
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
            "distro": _STATE.pkg_mgr,
            "dry_run": _STATE.dry_run,
            "snapshot_id": _STATE.snapshot_id or "none",
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

    if not _STATE.snapshot_id:
        log_warn("No se especificó --snapshot-id. Creando snapshot (requiere aprobación)...")
        result = run_registered("create_snapshot", {}, target=hostname() or ".")
        if result.outcome != "succeeded":
            _record("create_snapshot", result.outcome, result.returncode or 1, result.detail)
            return 3 if result.outcome == "blocked" else 1
        _record("create_snapshot", "succeeded", 0, result.run_id)
    else:
        result = run_registered(
            "validate_snapshot",
            {"snapshot_id": _STATE.snapshot_id},
            target=hostname() or ".",
        )
        # validate_snapshot is read — still go through registry
        if result.outcome == "blocked":
            # read ops shouldn't block on approval; treat handler failure
            pass
        if result.outcome not in ("succeeded",) and result.outcome != "blocked":
            ok, detail = validate_snapshot(_STATE.snapshot_id)
            if not ok:
                _record("validate_snapshot", "failed", 1, detail)
                return 1
        ok, detail = validate_snapshot(_STATE.snapshot_id)
        if not ok:
            log_error(f"Snapshot inválido: {detail}")
            _record("validate_snapshot", "failed", 1, detail)
            return 1
        _record("validate_snapshot", "succeeded", 0, detail)
    return 0


def _init_runtime(argv: list[str] | None) -> int | None:
    ACTION_RESULTS.clear()
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    apply_args(args)
    _register_handlers()

    _STATE.pkg_mgr = detect_pkg_mgr()
    if not _STATE.pkg_mgr:
        logger.error("No se pudo detectar gestor de paquetes")
        log_error("No se pudo detectar gestor de paquetes")
        return 1

    log_info("Iniciando rutina de limpieza")
    log_info("Modo: " + ("DRY-RUN" if _STATE.dry_run else "EJECUCIÓN"))
    log_info(f"Gestor de paquetes: {_STATE.pkg_mgr}")
    return None


def _preflight_snapshot() -> int | None:
    if not _STATE.execute:
        return None
    snap_rc = _ensure_snapshot_for_execute()
    if snap_rc == 0:
        return None
    if _STATE.json_mode:
        with contextlib.suppress(OSError, TypeError, ValueError):
            generate_json_output()
    return snap_rc


def _post_verify() -> None:
    if not _STATE.execute or any(a.get("status") == "blocked" for a in ACTION_RESULTS):
        return
    # Post-clean verify is read-only
    try:
        verify_clean()
    except Exception as exc:
        log_warn(f"verify_clean: {exc}")


def _emit_summary(failed: int) -> None:
    if failed:
        log_error(f"Rutina finalizada con {failed} acción(es) fallidas/bloqueadas")
    else:
        log_info("Rutina de limpieza completada")


def _final_rc(failed: int) -> int:
    if not _STATE.execute:
        return 0
    if failed:
        return 1
    if any(a.get("status") == "blocked" for a in ACTION_RESULTS):
        return 3
    return 0


def main(argv: list[str] | None = None) -> int:
    init_rc = _init_runtime(argv)
    if init_rc is not None:
        return init_rc

    preflight_rc = _preflight_snapshot()
    if preflight_rc is not None:
        return preflight_rc

    for op_id in CLEAN_OPS:
        dispatch_operation(op_id)

    _post_verify()
    failed = sum(1 for a in ACTION_RESULTS if a.get("status") in ("failed", "blocked"))
    _emit_summary(failed)

    if _STATE.json_mode:
        try:
            generate_json_output()
        except (OSError, TypeError, ValueError) as exc:
            logger.error("no se pudo generar JSON: %s", exc)
            return 1
    return _final_rc(failed)


if __name__ == "__main__":
    sys.exit(main())
