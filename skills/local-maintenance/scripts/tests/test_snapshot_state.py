"""Tests snapshot_state.py: --help, inválidos, error dir -> 1, doradas puras."""

import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path
from unittest.mock import patch

import pytest
import snapshot_state

EXIT_USAGE = 2
EXIT_BLOCKED = 3

SCRIPT = "snapshot_state.py"


def _run(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=".",
        env=e,
    )


def test_help_exit0() -> None:
    r = _run("--help")
    assert r.returncode == 0


def test_invalid_args_exit2() -> None:
    r = _run("--opcion-invalida-xyz")
    assert r.returncode == EXIT_USAGE


def test_invalid_snapshot_id_exit2(tmp_path: Path) -> None:
    r = _run("con/barra", "--snapshot-dir", str(tmp_path))
    assert r.returncode == EXIT_USAGE


def test_error_snapshot_dir_es_fichero_exit1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("x", encoding="utf-8")
    # Backend callable after approval; CLI itself always rejects create.
    assert snapshot_state.create_snapshot_backend("snap-1", str(blocker)) == 1


def test_md5_file_golden(tmp_path: Path) -> None:
    p = tmp_path / "a.txt"
    p.write_bytes(b"abc")
    assert snapshot_state.md5_file(str(p)) == hashlib.md5(b"abc").hexdigest()
    assert snapshot_state.md5_file(str(tmp_path / "noexiste")) == ""


def test_write_text_roundtrip_golden(tmp_path: Path) -> None:
    p = tmp_path / "w.txt"
    snapshot_state.write_text(str(p), "hola")
    assert p.read_text(encoding="utf-8") == "hola"


def test_detect_pkg_mgr_golden() -> None:
    mgr = snapshot_state.detect_pkg_mgr()
    assert isinstance(mgr, str)


# --- snapshot_state unit tests for coverage ---


def test_snapshot_detect_pkgmgr_pacman(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(snapshot_state, "which", lambda cmd: "/usr/bin/pacman" if cmd == "pacman" else None)
    mgr = snapshot_state.detect_pkg_mgr()
    assert mgr == "pacman"


def test_snapshot_detect_pkgmgr_apt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(snapshot_state, "which", lambda cmd: "/usr/bin/apt" if cmd == "apt" else None)
    mgr = snapshot_state.detect_pkg_mgr()
    assert mgr == "apt"


def test_snapshot_detect_pkgmgr_dnf(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(snapshot_state, "which", lambda cmd: "/usr/bin/dnf" if cmd == "dnf" else None)
    mgr = snapshot_state.detect_pkg_mgr()
    assert mgr == "dnf"


def test_snapshot_detect_pkgmgr_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(snapshot_state, "which", lambda cmd: None)
    mgr = snapshot_state.detect_pkg_mgr()
    assert mgr == ""


def test_snapshot_create_basic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()
    with (
        patch("snapshot_state.which", lambda cmd: "/usr/bin/pacman" if cmd == "pacman" else None),
        patch("snapshot_state.run_capture", return_value=(0, "pkg1\npkg2")),
        patch("snapshot_state.run", return_value="pkg1\npkg2"),
    ):
        rc = snapshot_state.create_snapshot_backend("snap-test", str(snap_dir))
        assert rc == 0
        meta = json.loads((snap_dir / "snap-test" / "metadata.json").read_text())
        assert meta["id"] == "snap-test"
        assert meta["content_hash"]
        assert meta["coverage"]


def test_snapshot_create_cli_always_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Env/flag never authorizes CLI create (V13/C05)."""
    monkeypatch.setenv("AUTOWORKSPACE_EXECUTION_APPROVED", "1")
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()
    rc = snapshot_state.main(["snap-test", "--snapshot-dir", str(snap_dir)])
    assert rc == EXIT_BLOCKED
    assert not (snap_dir / "snap-test").exists()


def test_snapshot_list(tmp_path: Path) -> None:
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()
    # Create a dummy snapshot
    meta = snap_dir / "snap-test" / "metadata.json"
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text('{"id": "snap-test", "packages": ["pkg1"]}', encoding="utf-8")
    rc = snapshot_state.main(["--list", "--snapshot-dir", str(snap_dir)])
    assert rc == 0


def test_snapshot_rollback_dry_run(tmp_path: Path) -> None:
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()
    meta = snap_dir / "snap-test" / "metadata.json"
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text('{"id": "snap-test", "packages": ["pkg1"]}', encoding="utf-8")
    rc = snapshot_state.main(["--rollback", "snap-test", "--snapshot-dir", str(snap_dir)])
    assert rc == 0  # dry-run by default


def test_snapshot_rollback_execute_rejects_host_root(tmp_path: Path) -> None:
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()
    meta = snap_dir / "snap-test" / "metadata.json"
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text('{"id": "snap-test", "packages": ["pkg1"]}', encoding="utf-8")
    (meta.parent / "etc-checksums.txt").write_text("abc123  /etc/fstab\n", encoding="utf-8")
    (meta.parent / "etc-backup.tar.gz").write_bytes(b"dummy")
    # Privileged host root must remain blocked
    rc = snapshot_state.rollback_snapshot(str(snap_dir), "snap-test", execute=True, restore_root="/")
    assert rc == EXIT_BLOCKED
    # Without --restore-root, program creates staging (bad tar → extract fail, not host write)
    rc2 = snapshot_state.main(["--rollback", "snap-test", "--snapshot-dir", str(snap_dir), "--execute"])
    assert rc2 != 0


def test_snapshot_rollback_execute_program_staging(tmp_path: Path) -> None:
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()
    meta = snap_dir / "snap-test" / "metadata.json"
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text('{"id": "snap-test"}', encoding="utf-8")
    (meta.parent / "etc-checksums.txt").write_text("abc123  /etc/fstab\n", encoding="utf-8")
    tarball = meta.parent / "etc-backup.tar.gz"
    with tarfile.open(tarball, "w:gz") as tf:
        info = tarfile.TarInfo(name="etc/fstab")
        data = b"UUID=test / ext4 defaults 0 1\n"
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    # Caller-supplied restore-root rejected
    rc_bad = snapshot_state.main(
        [
            "--rollback",
            "snap-test",
            "--snapshot-dir",
            str(snap_dir),
            "--execute",
            "--restore-root",
            str(tmp_path / "foreign"),
        ]
    )
    assert rc_bad == EXIT_BLOCKED
    # Program-owned staging (no --restore-root)
    rc = snapshot_state.main(["--rollback", "snap-test", "--snapshot-dir", str(snap_dir), "--execute"])
    assert rc == 0
