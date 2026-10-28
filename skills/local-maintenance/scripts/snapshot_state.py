#!/usr/bin/env python3

"""snapshot_state.py - Captura pre-cambio (paquetes, configs, espacio, servicios).

Port Python de snapshot_state.sh. Crea un snapshot reversible antes de
acciones R1+. Uso: snapshot_state.py [snapshot-id]
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import logging
import os
import sys
import tarfile
import tempfile
from typing import Any

from common import (
    SKILL_VERSION,
    hostname,
    log_info,
    log_warn,
    run,
    run_capture,
    utcnow_iso,
    which,
)

MIN_FIELDS = 2
MAX_TAR_MEMBERS = 10_000
MAX_TAR_BYTES = 512 * 1024 * 1024

SNAPSHOT_DIR = os.environ.get("SNAPSHOT_DIR", os.path.expanduser("~/.local/share/mantenimiento-linux/snapshots"))

logger = logging.getLogger("mantenimiento.snapshot")


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s", stream=sys.stderr)
    else:
        logging.getLogger().setLevel(level)


def _current_user() -> str:
    try:
        return getpass.getuser()
    except (OSError, KeyError) as exc:
        logger.warning("getpass.getuser() falló: %s", exc)
        return os.environ.get("USER", "unknown")


def md5_file(path: str) -> str:
    digest = hashlib.md5()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                digest.update(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


def detect_pkg_mgr() -> str:
    if which("pacman"):
        return "pacman"
    if which("apt"):
        return "apt"
    if which("dnf"):
        return "dnf"
    return ""


def write_text(path: str, content: str) -> None:
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
    except OSError as exc:
        logger.error("no se pudo escribir %r: %s", path, exc)
        raise


def capture_packages(pkg_mgr: str, snapshot_path: str) -> None:
    if pkg_mgr == "pacman":
        write_text(f"{snapshot_path}/packages-installed.txt", run("pacman -Q 2>/dev/null", timeout=30))
        write_text(f"{snapshot_path}/packages-explicit.txt", run("pacman -Qe 2>/dev/null", timeout=30))
        write_text(f"{snapshot_path}/packages-orphans.txt", run("pacman -Qtdq 2>/dev/null", timeout=30))
        write_text(f"{snapshot_path}/packages-foreign.txt", run("pacman -Qmq 2>/dev/null", timeout=30))
    elif pkg_mgr == "apt":
        write_text(f"{snapshot_path}/packages-installed.txt", run("dpkg --get-selections 2>/dev/null", timeout=30))
        write_text(
            f"{snapshot_path}/packages-explicit.txt",
            run("apt list --manual-installed 2>/dev/null | tail -n +2", timeout=60),
        )
    elif pkg_mgr == "dnf":
        write_text(f"{snapshot_path}/packages-installed.txt", run("rpm -qa 2>/dev/null", timeout=30))
        write_text(
            f"{snapshot_path}/packages-explicit.txt",
            run("dnf list installed 2>/dev/null | tail -n +2", timeout=60),
        )


def capture_etc_checksums(snapshot_path: str) -> None:
    lines: list[str] = []
    for root, _dirs, files in os.walk("/etc"):
        for name in files:
            full = os.path.join(root, name)
            digest = md5_file(full)
            if digest:
                lines.append(f"{digest}  {full}\n")
    write_text(f"{snapshot_path}/etc-checksums.txt", "".join(lines))


def capture_config_pending(pkg_mgr: str, snapshot_path: str) -> None:
    if pkg_mgr == "pacman":
        out = run("find /etc -name '*.pacnew' -o -name '*.pacsave' 2>/dev/null", timeout=30)
    elif pkg_mgr == "apt":
        out = run("find /etc -name '*.dpkg-*' -o -name '*.ucf-*' 2>/dev/null", timeout=30)
    else:
        out = run("find /etc -name '*.rpmnew' -o -name '*.rpmsave' 2>/dev/null", timeout=30)
    write_text(f"{snapshot_path}/config-pending.txt", out)


def list_snapshots(base_dir: str) -> int:
    """Lista snapshots con metadata (solo lectura)."""
    try:
        entries = sorted(os.listdir(base_dir))
    except OSError as exc:
        logger.error("no se pudo listar %r: %s", base_dir, exc)
        return 1
    found = 0
    for name in entries:
        meta_path = os.path.join(base_dir, name, "metadata.json")
        if not os.path.isfile(meta_path):
            continue
        try:
            with open(meta_path, encoding="utf-8") as fh:
                meta = json.load(fh)
            print(f"{name}  {meta.get('timestamp', '?')}  {meta.get('package_manager', '?')}")
        except (OSError, ValueError):
            print(f"{name}  (metadata ilegible)")
        found += 1
    if not found:
        print("(sin snapshots)")
    return 0


def diff_snapshot(base_dir: str, snapshot_id: str) -> tuple[list[str], list[str], int]:
    """Compara etc-checksums del snapshot contra el /etc actual.

    Devuelve (changed, missing, total). Solo /etc, solo lectura.
    """
    snap_file = os.path.join(base_dir, snapshot_id, "etc-checksums.txt")
    changed: list[str] = []
    missing: list[str] = []
    total = 0
    try:
        with open(snap_file, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError as exc:
        logger.error("no se pudo leer %r: %s", snap_file, exc)
        return [], [], 0
    for line in lines:
        parts = line.split()
        if len(parts) < MIN_FIELDS:
            continue
        digest, path = parts[0], parts[-1]
        if not path.startswith("/etc/"):
            continue
        total += 1
        current = md5_file(path)
        if not current:
            missing.append(path)
        elif current != digest:
            changed.append(path)
    return changed, missing, total


class _TarRejectedError(Exception):
    """A tar member failed one of the safety checks."""


def _member_error(member: tarfile.TarInfo, root: str) -> str | None:
    """Describe why a tar member is unsafe, or None when it is acceptable."""

    name = member.name.lstrip("/")
    dest = os.path.realpath(os.path.join(root, name))
    checks: list[str | None] = [
        (
            f"symlink/hardlink rejected: {member.name} -> {member.linkname}"
            if member.islnk() or member.issym()
            else None
        ),
        (f"path traversal in archive: {member.name}" if name.startswith("..") or ".." in name.split("/") else None),
        (
            f"absolute path in archive: {member.name}"
            if os.path.isabs(member.name) or member.name.startswith("/")
            else None
        ),
        (f"escape path in archive: {member.name}" if not dest.startswith(root + os.sep) and dest != root else None),
        (
            f"special file rejected: {member.name}"
            if member.isdev() or member.ischr() or member.isblk() or member.isfifo()
            else None
        ),
        (f"unsupported member type: {member.name}" if not (member.isfile() or member.isdir()) else None),
    ]
    return next((check for check in checks if check is not None), None)


def _collect_safe_members(members: list[tarfile.TarInfo], root: str) -> list[tarfile.TarInfo]:
    """Return the members that pass every check, enforcing the size quotas."""

    if len(members) > MAX_TAR_MEMBERS:
        raise _TarRejectedError(f"tar member quota exceeded: {len(members)}")
    safe: list[tarfile.TarInfo] = []
    total = 0
    for member in members:
        error = _member_error(member, root)
        if error is not None:
            raise _TarRejectedError(error)
        total += max(0, int(member.size or 0))
        if total > MAX_TAR_BYTES:
            raise _TarRejectedError("tar size quota exceeded")
        safe.append(member)
    return safe


def _inspect_and_extract_tar(tarball: str, restore_root: str) -> int:
    """Single open: inspect members then extract. Reject links/specials/escapes."""

    root = os.path.realpath(restore_root)
    try:
        with tarfile.open(tarball, "r:*") as tf:
            safe = _collect_safe_members(tf.getmembers(), root)
            filter_kw: dict[str, Any] = {}
            if hasattr(tarfile, "data_filter"):
                filter_kw["filter"] = _tar_data_filter
            for member in safe:
                tf.extract(member, path=restore_root, set_attrs=False, **filter_kw)
    except _TarRejectedError as exc:
        logger.error("%s", exc)
        return 1
    except (tarfile.TarError, OSError, KeyError) as exc:
        logger.error("tar inspect/extract failed: %s", exc)
        return 1
    return 0


def _safe_tar_members(tarball: str, restore_root: str) -> list[str] | None:
    """Compatibility wrapper — prefer _inspect_and_extract_tar for execute path."""

    root = os.path.realpath(restore_root)
    safe: list[str] = []
    try:
        with tarfile.open(tarball, "r:*") as tf:
            for member in tf.getmembers():
                if _member_error(member, root) is not None:
                    return None
                safe.append(member.name.lstrip("/"))
    except (tarfile.TarError, OSError):
        return None
    return safe


def _tar_data_filter(member: tarfile.TarInfo, dest_path: str) -> tarfile.TarInfo:
    """Explicit extract filter for Python 3.12+; reject links/specials."""

    if member.islnk() or member.issym():
        raise tarfile.FilterError(f"link rejected: {member.name}")
    if member.isdev() or member.ischr() or member.isblk() or member.isfifo():
        raise tarfile.FilterError(f"special rejected: {member.name}")
    name = member.name.lstrip("/")
    if ".." in name.split("/") or os.path.isabs(member.name):
        raise tarfile.FilterError(f"bad path: {member.name}")
    return member


def _check_rollback_target(base_dir: str, snapshot_id: str) -> tuple[str, int | None]:
    """Validate the snapshot id and return its path plus an exit code on failure."""

    if "/" in snapshot_id or snapshot_id in ("", ".", ".."):
        logger.error("snapshot_id inválido: %r", snapshot_id)
        print(f"snapshot_id inválido: {snapshot_id}", file=sys.stderr)
        return "", 2
    snapshot_path = os.path.join(base_dir, snapshot_id)
    if not os.path.isdir(snapshot_path):
        logger.error("snapshot inexistente: %r", snapshot_path)
        print(f"snapshot inexistente: {snapshot_id}", file=sys.stderr)
        return "", 1
    return snapshot_path, None


def _rollback_dry_run(snapshot_id: str, tarball: str) -> int:
    """Print the manual restore plan; nothing is touched."""

    print("[dry-run] Sin cambios. Plan de restauracion:")
    if os.path.isfile(tarball):
        print(f"  tar -tzf {tarball}  # verificar contenido")
        print(
            f"  snapshot_state.py --rollback {snapshot_id} --execute   # extract solo a staging creado por el programa"
        )
    if which("snapper") is not None:
        print("  snapper undochange <pre>..<post>  # alternativa btrfs (manual)")
    if which("timeshift") is not None:
        print("  timeshift --restore  # alternativa (interactivo, ventana acordada)")
    return 0


def _claim_staging() -> tuple[str, int | None]:
    """Create the private staging directory and its ownership marker."""

    restore_root = tempfile.mkdtemp(prefix="aw-restore-")
    owned_marker = os.path.join(restore_root, ".aw-owned-staging")
    try:
        os.chmod(restore_root, 0o700)
        with open(owned_marker, "w", encoding="utf-8") as fh:
            fh.write(f"pid={os.getpid()}\n")
    except OSError as exc:
        logger.error("cannot claim staging: %s", exc)
        return restore_root, 1
    return restore_root, None


def _extract_staging(staging: str, tarball: str, snapshot_id: str) -> int:
    """Extract the snapshot tarball into the owned staging directory."""

    if not os.path.isfile(tarball):
        log_warn("sin etc-backup.tar.gz: restauracion manual con los comandos de arriba")
        return 1
    rc = _inspect_and_extract_tar(tarball, staging)
    if rc != 0:
        return rc
    log_info(f"Rollback {snapshot_id}: extracted to staging {staging} (owned=True; not host /)")
    return 0


def rollback_snapshot(
    base_dir: str,
    snapshot_id: str,
    execute: bool = False,
    restore_root: str | None = None,
) -> int:
    """Rollback against a snapshot.

    Dry-run by default. Real extract only into a program-created staging dir
    (tempfile under control). Absolute / caller-supplied privileged roots rejected.
    """

    snapshot_path, failed = _check_rollback_target(base_dir, snapshot_id)
    if failed is not None:
        return failed
    changed, missing, total = diff_snapshot(base_dir, snapshot_id)
    print(f"rollback {snapshot_id}: {total} ficheros vigilados, {len(changed)} cambiados, {len(missing)} eliminados")
    for path in (changed + missing)[:20]:
        print(f"  ~ {path}")
    tarball = os.path.join(snapshot_path, "etc-backup.tar.gz")
    if not execute:
        return _rollback_dry_run(snapshot_id, tarball)

    # Staging: only program-created empty private dirs. Reject caller-supplied
    # existing paths even under tempfile.gettempdir().
    if restore_root:
        logger.error("caller-supplied --restore-root rejected; program creates staging")
        print(
            "ERROR: no se acepta --restore-root externo; el programa crea staging vacío propio.",
            file=sys.stderr,
        )
        return 3

    staging, failed = _claim_staging()
    if failed is not None:
        return failed
    log_info(f"staging creado: {staging}")
    return _extract_staging(staging, tarball, snapshot_id)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Captura pre-cambio (snapshot reversible antes de R1+).")
    parser.add_argument("snapshot_id", nargs="?", default=None, help="ID del snapshot")
    parser.add_argument("--snapshot-dir", default=None, help="Override directorio base de snapshots")
    parser.add_argument("--list", action="store_true", help="Listar snapshots existentes")
    parser.add_argument("--rollback", default="", help="ID del snapshot contra el que comparar/restaurar")
    parser.add_argument("--execute", action="store_true", help="Ejecutar rollback (por defecto dry-run)")
    parser.add_argument(
        "--restore-root",
        default="",
        help="Raíz temporal explícita para extract (obligatoria con --execute; no se admite /)",
    )
    parser.add_argument("--verbose", action="store_true", help="Logging verboso a stderr")
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    base_dir = args.snapshot_dir or os.environ.get("SNAPSHOT_DIR", SNAPSHOT_DIR)
    if not base_dir:
        logger.error("directorio base de snapshots vacío")
        return 1
    if args.list:
        return list_snapshots(base_dir)
    if args.rollback:
        return rollback_snapshot(
            base_dir,
            args.rollback,
            execute=args.execute,
            restore_root=args.restore_root or None,
        )
    snapshot_id = (
        args.snapshot_id or f"snap-{utcnow_iso().replace('-', '').replace(':', '').replace('T', '-').replace('Z', '')}"
    )
    if "/" in snapshot_id or "\\" in snapshot_id or snapshot_id in ("", ".", ".."):
        logger.error("snapshot_id inválido: %r", snapshot_id)
        print(f"snapshot_id inválido: {snapshot_id}", file=sys.stderr)
        return 2
    # CLI create is never consent. Env/flag/hash cannot authorize (H05/C05).
    # Backend is reachable only via create_snapshot_backend after run_registered.
    _ = os.environ.pop("AUTOWORKSPACE_EXECUTION_APPROVED", None)
    logger.error("create_snapshot CLI blocked; use run_registered('create_snapshot', …)")
    print(
        "ERROR: snapshot create via CLI rejected; use run_registered('create_snapshot', …)",
        file=sys.stderr,
    )
    return 3


def _content_hash_of_snapshot(snapshot_path: str) -> str:
    """SHA-256 over inventory files excluding metadata.json (written last)."""
    h = hashlib.sha256()
    for root, _dirs, files in os.walk(snapshot_path):
        for name in sorted(files):
            if name == "metadata.json":
                continue
            full = os.path.join(root, name)
            if os.path.islink(full):
                h.update(os.readlink(full).encode())
            elif os.path.isfile(full):
                with open(full, "rb") as fh:
                    for chunk in iter(lambda: fh.read(65536), b""):
                        h.update(chunk)
    return h.hexdigest()


_TAR_ETC_BASE = ["/etc/ssh/sshd_config", "/etc/fstab"]
_TAR_ETC_EXTRA: dict[str, list[str]] = {
    "pacman": ["/etc/pacman.conf", "/etc/pacman.d"],
    "apt": ["/etc/apt/sources.list", "/etc/apt/preferences"],
    "dnf": ["/etc/yum.repos.d/", "/etc/dnf/dnf.conf"],
}


def _prepare_snapshot_dir(snapshot_path: str) -> bool:
    try:
        os.makedirs(snapshot_path, mode=0o700, exist_ok=True)
        os.chmod(snapshot_path, 0o700)
    except OSError as exc:
        logger.error("no se pudo crear %r: %s", snapshot_path, exc)
        return False
    return True


def _initial_metadata(snapshot_id: str, pkg_mgr: str) -> dict[str, Any]:
    backend_name = "none"
    return {
        "id": snapshot_id,
        "snapshot_id": snapshot_id,
        "target_host": hostname(),
        "backend": backend_name,
        "coverage": "inventory-only",
        "content_hash": "",
        "timestamp": utcnow_iso(),
        "hostname": hostname(),
        "user": _current_user(),
        "package_manager": pkg_mgr,
        "kernel": run("uname -r", timeout=5).strip(),
        "skill_version": SKILL_VERSION,
        "inventory_status": "pending",
        "backend_name": backend_name,
        "backend_status": "not_run",
        "backup_status": "not_run",
        "recovery_scope": "none",
        "integrity_status": "pending",
    }


def _dump_metadata(snapshot_path: str, metadata: dict[str, Any]) -> bool:
    """Write metadata.json with restrictive permissions. False on filesystem error."""
    target = f"{snapshot_path}/metadata.json"
    try:
        with open(target, "w", encoding="utf-8") as fh:
            json.dump(metadata, fh, indent=2)
        os.chmod(target, 0o600)
    except OSError:
        return False
    return True


def _write_initial_metadata(snapshot_path: str, metadata: dict[str, Any]) -> bool:
    target = f"{snapshot_path}/metadata.json"
    try:
        with open(target, "w", encoding="utf-8") as fh:
            json.dump(metadata, fh, indent=2)
        os.chmod(target, 0o600)
    except (OSError, TypeError, ValueError) as exc:
        logger.error("no se pudo escribir metadata.json: %s", exc)
        return False
    return True


def _capture_inventory(snapshot_path: str, pkg_mgr: str) -> bool:
    try:
        log_info("Capturando lista de paquetes (inventario, no backup restaurable)...")
        capture_packages(pkg_mgr, snapshot_path)

        log_info("Capturando checksums de /etc...")
        capture_etc_checksums(snapshot_path)

        log_info("Capturando archivos de configuración pendientes...")
        capture_config_pending(pkg_mgr, snapshot_path)

        log_info("Capturando estado de servicios...")
        write_text(
            f"{snapshot_path}/services-enabled.txt",
            run(
                "systemctl list-unit-files --type=service --state=enabled --no-pager 2>/dev/null",
                timeout=15,
            ),
        )
        write_text(
            f"{snapshot_path}/services-running.txt",
            run(
                "systemctl list-units --type=service --state=running --no-pager 2>/dev/null",
                timeout=15,
            ),
        )

        log_info("Capturando uso de espacio...")
        write_text(f"{snapshot_path}/disk-usage.txt", run("df -h 2>/dev/null", timeout=15))
        write_text(
            f"{snapshot_path}/cache-sizes.txt",
            run(
                "du -sh /var/cache/pacman/pkg /var/cache/apt/archives /var/cache/dnf 2>/dev/null",
                timeout=30,
            ),
        )

        write_text(
            f"{snapshot_path}/journal-size.txt",
            run("journalctl --disk-usage 2>/dev/null", timeout=15),
        )
    except OSError:
        return False
    return True


def _backend_result(name: str, rc: int, coverage_prefix: str) -> tuple[str, str, str, str, str]:
    status = "ok" if rc == 0 else "failed"
    scope = "partial" if rc == 0 else "none"
    coverage = f"{coverage_prefix}-partial" if rc == 0 else "inventory-only"
    return name, status, status, scope, coverage


def _tar_etc_files(family: str) -> list[str]:
    etc_files = list(_TAR_ETC_BASE)
    etc_files.extend(_TAR_ETC_EXTRA.get(family, []))
    return etc_files


def _run_backend(snapshot_path: str, snapshot_id: str, pkg_mgr: str) -> tuple[str, str, str, str, str]:
    if which("timeshift"):
        log_info("Creando snapshot timeshift...")
        rc, _ = run_capture(
            f"timeshift --create --comments 'mantenimiento-linux: {snapshot_id}' --tags D 2>/dev/null",
            timeout=300,
        )
        return _backend_result("timeshift", rc, "timeshift")
    if which("snapper"):
        log_info("Creando snapshot snapper...")
        rc, _ = run_capture(
            f"snapper create --description 'mantenimiento-linux: {snapshot_id}' --cleanup-algorithm number 2>/dev/null",
            timeout=300,
        )
        return _backend_result("snapper", rc, "snapper")
    log_warn("No hay timeshift/snapper. Backup tar de configs públicas (sin claves privadas)...")
    etc_str = " ".join(_tar_etc_files(pkg_mgr))
    rc, _ = run_capture(
        f"tar -czf '{snapshot_path}/etc-backup.tar.gz' {etc_str} 2>/dev/null",
        timeout=120,
    )
    if rc != 0:
        log_warn("Backup parcial de configs falló")
    return _backend_result("tar-config", rc, "tar-config")


def _write_hashes(snapshot_path: str) -> str:
    hash_lines: list[tuple[str, str]] = []
    for root, _dirs, files in os.walk(snapshot_path):
        for name in files:
            if name == "metadata.json":
                continue
            full = os.path.join(root, name)
            digest = md5_file(full)
            if digest:
                hash_lines.append((full, digest))
    hash_lines.sort(key=lambda item: item[0])
    with open(f"{snapshot_path}/SNAPSHOT-HASHES.txt", "w", encoding="utf-8") as fh:
        for full, digest in hash_lines:
            fh.write(f"{digest}  {full}\n")

    hashes_digest = hashlib.md5()
    with open(f"{snapshot_path}/SNAPSHOT-HASHES.txt", "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            hashes_digest.update(chunk)
    snapshot_hash = hashes_digest.hexdigest()
    write_text(f"{snapshot_path}/SNAPSHOT-HASH.txt", snapshot_hash + "\n")
    return snapshot_hash


def _snapshot_hashes(snapshot_path: str, metadata: dict[str, Any], recovery_scope: str) -> tuple[str, str] | None:
    log_info("Calculando hash del snapshot...")
    try:
        snapshot_hash = _write_hashes(snapshot_path)
        # content_hash AFTER all inventory files; metadata written last (H08)
        content_hash = _content_hash_of_snapshot(snapshot_path)
    except OSError as exc:
        logger.error("no se pudo calcular hash del snapshot: %s", exc)
        metadata["integrity_status"] = "failed"
        metadata["outcome"] = "failed"
        return None
    metadata["integrity_status"] = "ok"
    metadata["snapshot_hash"] = snapshot_hash
    metadata["content_hash"] = content_hash
    metadata["outcome"] = "partial" if recovery_scope == "partial" else "succeeded"
    return snapshot_hash, content_hash


def _fail_backend(snapshot_path: str, metadata: dict[str, Any]) -> int:
    metadata["outcome"] = "failed"
    _dump_metadata(snapshot_path, metadata)
    logger.error("backend/backup falló: inventario puede existir pero no hay recuperación válida")
    print(
        "ERROR: captura de inventario no implica backup restaurable; backend falló",
        file=sys.stderr,
    )
    return 1


def _json_result(snapshot_path: str, metadata: dict[str, Any]) -> dict[str, Any]:
    files_captured = sum(len(files) for _, _, files in os.walk(snapshot_path))
    return {
        "snapshot_id": metadata["id"],
        "snapshot_path": snapshot_path,
        "snapshot_hash": metadata["snapshot_hash"],
        "content_hash": metadata["content_hash"],
        "timestamp": utcnow_iso(),
        "package_manager": metadata["package_manager"],
        "files_captured": files_captured,
        "recovery_scope": metadata["recovery_scope"],
        "backend_status": metadata["backend_status"],
        "inventory_status": metadata["inventory_status"],
    }


def _emit_json(snapshot_path: str, metadata: dict[str, Any]) -> int:
    try:
        result = _json_result(snapshot_path, metadata)
    except OSError as exc:
        logger.error("no se pudo contar ficheros del snapshot: %s", exc)
        return 1
    try:
        print(json.dumps(result, indent=2))
    except (TypeError, ValueError) as exc:
        logger.error("no se pudo serializar JSON de salida: %s", exc)
        return 1
    return 0


def _finalize(snapshot_path: str, snapshot_id: str, metadata: dict[str, Any], recovery_scope: str) -> int:
    hashes = _snapshot_hashes(snapshot_path, metadata, recovery_scope)
    if hashes is None:
        _dump_metadata(snapshot_path, metadata)
        return 1
    snapshot_hash, _content_hash = hashes

    if not _dump_metadata(snapshot_path, metadata):
        logger.error("no se pudo actualizar metadata")
        return 1

    log_info(f"Snapshot registrado: {snapshot_id} recovery_scope={recovery_scope}")
    log_info(f"Hash: {snapshot_hash}")
    log_info(f"Ubicación: {snapshot_path}")

    if os.environ.get("OUTPUT_JSON", "false") == "true":
        return _emit_json(snapshot_path, metadata)
    return 0


def create_snapshot_backend(snapshot_id: str, base_dir: str) -> int:
    """Create snapshot inventory/backup. Callable only from approved handlers."""
    if "/" in snapshot_id or "\\" in snapshot_id or snapshot_id in ("", ".", ".."):
        logger.error("snapshot_id inválido: %r", snapshot_id)
        return 2
    snapshot_path = os.path.join(base_dir, snapshot_id)

    pkg_mgr = detect_pkg_mgr()

    if not _prepare_snapshot_dir(snapshot_path):
        return 1

    log_info(f"Creando snapshot: {snapshot_id}")
    log_info(f"Destino: {snapshot_path}")

    metadata = _initial_metadata(snapshot_id, pkg_mgr)
    if not _write_initial_metadata(snapshot_path, metadata):
        return 1

    metadata["inventory_status"] = "ok" if _capture_inventory(snapshot_path, pkg_mgr) else "failed"

    backend_name, backend_status, backup_status, recovery_scope, coverage = _run_backend(
        snapshot_path, snapshot_id, pkg_mgr
    )

    metadata.update(
        {
            "backend": backend_name,
            "backend_name": backend_name,
            "backend_status": backend_status,
            "backup_status": backup_status,
            "recovery_scope": recovery_scope,
            "coverage": coverage,
            "backend_required": True,
        }
    )

    if backend_status == "failed":
        return _fail_backend(snapshot_path, metadata)

    return _finalize(snapshot_path, snapshot_id, metadata, recovery_scope)


if __name__ == "__main__":
    sys.exit(main())
