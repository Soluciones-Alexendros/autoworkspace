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
    lines: list = []
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


def diff_snapshot(base_dir: str, snapshot_id: str) -> tuple[list, list, int]:
    """Compara etc-checksums del snapshot contra el /etc actual.

    Devuelve (changed, missing, total). Solo /etc, solo lectura.
    """
    snap_file = os.path.join(base_dir, snapshot_id, "etc-checksums.txt")
    changed: list = []
    missing: list = []
    total = 0
    try:
        with open(snap_file, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError as exc:
        logger.error("no se pudo leer %r: %s", snap_file, exc)
        return [], [], 0
    for line in lines:
        parts = line.split()
        if len(parts) < 2:
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


def _inspect_and_extract_tar(tarball: str, restore_root: str) -> int:
    """Single open: inspect members then extract. Reject links/specials/escapes."""
    import tarfile

    root = os.path.realpath(restore_root)
    max_members = 10_000
    max_bytes = 512 * 1024 * 1024
    try:
        with tarfile.open(tarball, "r:*") as tf:
            members = tf.getmembers()
            if len(members) > max_members:
                logger.error("tar member quota exceeded: %s", len(members))
                return 1
            total = 0
            safe: list = []
            for member in members:
                if member.islnk() or member.issym():
                    logger.error("symlink/hardlink rejected: %s -> %s", member.name, member.linkname)
                    return 1
                name = member.name.lstrip("/")
                if name.startswith("..") or ".." in name.split("/"):
                    logger.error("path traversal in archive: %s", member.name)
                    return 1
                if os.path.isabs(member.name) or member.name.startswith("/"):
                    logger.error("absolute path in archive: %s", member.name)
                    return 1
                dest = os.path.realpath(os.path.join(root, name))
                if not dest.startswith(root + os.sep) and dest != root:
                    logger.error("escape path in archive: %s", member.name)
                    return 1
                if member.isdev() or member.ischr() or member.isblk() or member.isfifo():
                    logger.error("special file rejected: %s", member.name)
                    return 1
                if not (member.isfile() or member.isdir()):
                    logger.error("unsupported member type: %s", member.name)
                    return 1
                total += max(0, int(member.size or 0))
                if total > max_bytes:
                    logger.error("tar size quota exceeded")
                    return 1
                safe.append(member)
            filter_kw = {}
            if hasattr(tarfile, "data_filter"):
                filter_kw["filter"] = _tar_data_filter
            for member in safe:
                if filter_kw:
                    tf.extract(member, path=restore_root, set_attrs=False, **filter_kw)
                else:
                    tf.extract(member, path=restore_root, set_attrs=False)
    except (tarfile.TarError, OSError, KeyError) as exc:
        logger.error("tar inspect/extract failed: %s", exc)
        return 1
    return 0


def _safe_tar_members(tarball: str, restore_root: str) -> list[str] | None:
    """Compatibility wrapper — prefer _inspect_and_extract_tar for execute path."""
    import tarfile

    root = os.path.realpath(restore_root)
    safe: list[str] = []
    try:
        with tarfile.open(tarball, "r:*") as tf:
            for member in tf.getmembers():
                if member.islnk() or member.issym():
                    return None
                name = member.name.lstrip("/")
                if name.startswith("..") or ".." in name.split("/"):
                    return None
                if os.path.isabs(member.name) or member.name.startswith("/"):
                    return None
                dest = os.path.realpath(os.path.join(root, name))
                if not dest.startswith(root + os.sep) and dest != root:
                    return None
                if member.isdev() or member.ischr() or member.isblk() or member.isfifo():
                    return None
                if not (member.isfile() or member.isdir()):
                    return None
                safe.append(name)
    except (tarfile.TarError, OSError):
        return None
    return safe


def _tar_data_filter(member, dest_path):
    """Explicit extract filter for Python 3.12+; reject links/specials."""
    import tarfile

    if member.islnk() or member.issym():
        raise tarfile.FilterError(f"link rejected: {member.name}")
    if member.isdev() or member.ischr() or member.isblk() or member.isfifo():
        raise tarfile.FilterError(f"special rejected: {member.name}")
    name = member.name.lstrip("/")
    if ".." in name.split("/") or os.path.isabs(member.name):
        raise tarfile.FilterError(f"bad path: {member.name}")
    return member


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
    import tempfile

    if "/" in snapshot_id or snapshot_id in ("", ".", ".."):
        logger.error("snapshot_id inválido: %r", snapshot_id)
        print(f"snapshot_id inválido: {snapshot_id}", file=sys.stderr)
        return 2
    snapshot_path = os.path.join(base_dir, snapshot_id)
    if not os.path.isdir(snapshot_path):
        logger.error("snapshot inexistente: %r", snapshot_path)
        print(f"snapshot inexistente: {snapshot_id}", file=sys.stderr)
        return 1
    changed, missing, total = diff_snapshot(base_dir, snapshot_id)
    print(f"rollback {snapshot_id}: {total} ficheros vigilados, {len(changed)} cambiados, {len(missing)} eliminados")
    for path in (changed + missing)[:20]:
        print(f"  ~ {path}")
    tarball = os.path.join(snapshot_path, "etc-backup.tar.gz")
    if not execute:
        print("[dry-run] Sin cambios. Plan de restauracion:")
        if os.path.isfile(tarball):
            print(f"  tar -tzf {tarball}  # verificar contenido")
            print(
                f"  snapshot_state.py --rollback {snapshot_id} --execute "
                f"  # extract solo a staging creado por el programa"
            )
        if which("snapper") is not None:
            print("  snapper undochange <pre>..<post>  # alternativa btrfs (manual)")
        if which("timeshift") is not None:
            print("  timeshift --restore  # alternativa (interactivo, ventana acordada)")
        return 0

    # Staging: only program-created empty private dirs. Reject caller-supplied
    # existing paths even under tempfile.gettempdir().
    if restore_root:
        logger.error("caller-supplied --restore-root rejected; program creates staging")
        print(
            "ERROR: no se acepta --restore-root externo; el programa crea staging vacío propio.",
            file=sys.stderr,
        )
        return 3

    restore_root = tempfile.mkdtemp(prefix="aw-restore-")
    owned_marker = os.path.join(restore_root, ".aw-owned-staging")
    try:
        os.chmod(restore_root, 0o700)
        with open(owned_marker, "w", encoding="utf-8") as fh:
            fh.write(f"pid={os.getpid()}\n")
    except OSError as exc:
        logger.error("cannot claim staging: %s", exc)
        return 1
    owned_staging = True
    log_info(f"staging creado: {restore_root}")

    if not os.path.isfile(tarball):
        log_warn("sin etc-backup.tar.gz: restauracion manual con los comandos de arriba")
        return 1

    rc = _inspect_and_extract_tar(tarball, restore_root)
    if rc != 0:
        return rc
    log_info(f"Rollback {snapshot_id}: extracted to staging {restore_root} (owned={owned_staging}; not host /)")
    return 0


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


def create_snapshot_backend(snapshot_id: str, base_dir: str) -> int:
    """Create snapshot inventory/backup. Callable only from approved handlers."""
    if "/" in snapshot_id or "\\" in snapshot_id or snapshot_id in ("", ".", ".."):
        logger.error("snapshot_id inválido: %r", snapshot_id)
        return 2
    snapshot_path = os.path.join(base_dir, snapshot_id)

    pkg_mgr = detect_pkg_mgr()

    try:
        os.makedirs(snapshot_path, mode=0o700, exist_ok=True)
        os.chmod(snapshot_path, 0o700)
    except OSError as exc:
        logger.error("no se pudo crear %r: %s", snapshot_path, exc)
        return 1

    log_info(f"Creando snapshot: {snapshot_id}")
    log_info(f"Destino: {snapshot_path}")

    inventory_ok = True
    backend_name = "none"
    backend_status = "not_run"
    backup_status = "not_run"
    recovery_scope = "none"
    coverage = "inventory-only"

    metadata = {
        "id": snapshot_id,
        "snapshot_id": snapshot_id,
        "target_host": hostname(),
        "backend": backend_name,
        "coverage": coverage,
        "content_hash": "",
        "timestamp": utcnow_iso(),
        "hostname": hostname(),
        "user": _current_user(),
        "package_manager": pkg_mgr,
        "kernel": run("uname -r", timeout=5).strip(),
        "skill_version": SKILL_VERSION,
        "inventory_status": "pending",
        "backend_name": backend_name,
        "backend_status": backend_status,
        "backup_status": backup_status,
        "recovery_scope": recovery_scope,
        "integrity_status": "pending",
    }
    # Write placeholder metadata without content_hash; finalize after files exist.
    try:
        with open(f"{snapshot_path}/metadata.json", "w", encoding="utf-8") as fh:
            json.dump(metadata, fh, indent=2)
        os.chmod(f"{snapshot_path}/metadata.json", 0o600)
    except (OSError, TypeError, ValueError) as exc:
        logger.error("no se pudo escribir metadata.json: %s", exc)
        return 1

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
            run("systemctl list-unit-files --type=service --state=enabled --no-pager 2>/dev/null", timeout=15),
        )
        write_text(
            f"{snapshot_path}/services-running.txt",
            run("systemctl list-units --type=service --state=running --no-pager 2>/dev/null", timeout=15),
        )

        log_info("Capturando uso de espacio...")
        write_text(f"{snapshot_path}/disk-usage.txt", run("df -h 2>/dev/null", timeout=15))
        write_text(
            f"{snapshot_path}/cache-sizes.txt",
            run("du -sh /var/cache/pacman/pkg /var/cache/apt/archives /var/cache/dnf 2>/dev/null", timeout=30),
        )

        write_text(f"{snapshot_path}/journal-size.txt", run("journalctl --disk-usage 2>/dev/null", timeout=15))
    except OSError:
        inventory_ok = False

    metadata["inventory_status"] = "ok" if inventory_ok else "failed"

    if which("timeshift"):
        backend_name = "timeshift"
        log_info("Creando snapshot timeshift...")
        rc, _ = run_capture(
            f"timeshift --create --comments 'mantenimiento-linux: {snapshot_id}' --tags D 2>/dev/null",
            timeout=300,
        )
        backend_status = "ok" if rc == 0 else "failed"
        backup_status = backend_status
        recovery_scope = "partial" if rc == 0 else "none"
        coverage = "timeshift-partial" if rc == 0 else "inventory-only"
    elif which("snapper"):
        backend_name = "snapper"
        log_info("Creando snapshot snapper...")
        rc, _ = run_capture(
            f"snapper create --description 'mantenimiento-linux: {snapshot_id}' --cleanup-algorithm number 2>/dev/null",
            timeout=300,
        )
        backend_status = "ok" if rc == 0 else "failed"
        backup_status = backend_status
        recovery_scope = "partial" if rc == 0 else "none"
        coverage = "snapper-partial" if rc == 0 else "inventory-only"
    else:
        backend_name = "tar-config"
        log_warn("No hay timeshift/snapper. Backup tar de configs públicas (sin claves privadas)...")
        family = detect_pkg_mgr()
        etc_files = ["/etc/ssh/sshd_config", "/etc/fstab"]
        if family == "pacman":
            etc_files.extend(["/etc/pacman.conf", "/etc/pacman.d"])
        elif family == "apt":
            etc_files.extend(["/etc/apt/sources.list", "/etc/apt/preferences"])
        elif family == "dnf":
            etc_files.extend(["/etc/yum.repos.d/", "/etc/dnf/dnf.conf"])
        etc_str = " ".join(etc_files)
        rc, _ = run_capture(
            f"tar -czf '{snapshot_path}/etc-backup.tar.gz' {etc_str} 2>/dev/null",
            timeout=120,
        )
        backend_status = "ok" if rc == 0 else "failed"
        backup_status = "ok" if rc == 0 else "failed"
        recovery_scope = "partial" if rc == 0 else "none"
        coverage = "tar-config-partial" if rc == 0 else "inventory-only"
        if rc != 0:
            log_warn("Backup parcial de configs falló")

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
        metadata["outcome"] = "failed"
        try:
            with open(f"{snapshot_path}/metadata.json", "w", encoding="utf-8") as fh:
                json.dump(metadata, fh, indent=2)
            os.chmod(f"{snapshot_path}/metadata.json", 0o600)
        except OSError:
            pass
        logger.error("backend/backup falló: inventario puede existir pero no hay recuperación válida")
        print(
            "ERROR: captura de inventario no implica backup restaurable; backend falló",
            file=sys.stderr,
        )
        return 1

    log_info("Calculando hash del snapshot...")
    hash_lines = []
    try:
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
        # content_hash AFTER all inventory files; metadata written last (H08)
        content_hash = _content_hash_of_snapshot(snapshot_path)
        metadata["integrity_status"] = "ok"
        metadata["snapshot_hash"] = snapshot_hash
        metadata["content_hash"] = content_hash
        metadata["outcome"] = "partial" if recovery_scope == "partial" else "succeeded"
    except OSError as exc:
        logger.error("no se pudo calcular hash del snapshot: %s", exc)
        metadata["integrity_status"] = "failed"
        metadata["outcome"] = "failed"
        try:
            with open(f"{snapshot_path}/metadata.json", "w", encoding="utf-8") as fh:
                json.dump(metadata, fh, indent=2)
        except OSError:
            pass
        return 1

    try:
        with open(f"{snapshot_path}/metadata.json", "w", encoding="utf-8") as fh:
            json.dump(metadata, fh, indent=2)
        os.chmod(f"{snapshot_path}/metadata.json", 0o600)
    except OSError as exc:
        logger.error("no se pudo actualizar metadata: %s", exc)
        return 1

    log_info(f"Snapshot registrado: {snapshot_id} recovery_scope={recovery_scope}")
    log_info(f"Hash: {snapshot_hash}")
    log_info(f"Ubicación: {snapshot_path}")

    if os.environ.get("OUTPUT_JSON", "false") == "true":
        try:
            files_captured = sum(len(files) for _, _, files in os.walk(snapshot_path))
        except OSError as exc:
            logger.error("no se pudo contar ficheros del snapshot: %s", exc)
            return 1
        result = {
            "snapshot_id": snapshot_id,
            "snapshot_path": snapshot_path,
            "snapshot_hash": snapshot_hash,
            "content_hash": content_hash,
            "timestamp": utcnow_iso(),
            "package_manager": pkg_mgr,
            "files_captured": files_captured,
            "recovery_scope": recovery_scope,
            "backend_status": backend_status,
            "inventory_status": metadata["inventory_status"],
        }
        try:
            print(json.dumps(result, indent=2))
        except (TypeError, ValueError) as exc:
            logger.error("no se pudo serializar JSON de salida: %s", exc)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
