"""Confinement and quota tests for verified bootstrap archives."""

from __future__ import annotations

import io
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness.bootstrap import safe_extract  # noqa: E402


def _archive(root: Path, members: list[tuple[str, bytes]]) -> Path:
    path = root / "fixture.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        for name, content in members:
            info = tarfile.TarInfo(name)
            info.size = len(content)
            info.mode = 0o600
            archive.addfile(info, io.BytesIO(content))
    return path


def test_valid_archive_extracts_private_files(tmp_path: Path) -> None:
    archive = _archive(tmp_path, [("package/file.txt", b"content")])
    destination = tmp_path / "new-target"
    safe_extract(archive, destination)
    assert (destination / "package" / "file.txt").read_bytes() == b"content"
    private_mode = 0o700
    assert destination.stat().st_mode & 0o777 == private_mode


def test_existing_destination_is_rejected(tmp_path: Path) -> None:
    archive = _archive(tmp_path, [("package/file.txt", b"content")])
    destination = tmp_path / "existing"
    destination.mkdir()
    with pytest.raises(ValueError, match="destination"):
        safe_extract(archive, destination)


@pytest.mark.parametrize("name", ["/absolute", "../escape", "package/../../escape", "package\\escape"])
def test_path_escape_is_rejected(tmp_path: Path, name: str) -> None:
    archive = _archive(tmp_path, [(name, b"bad")])
    with pytest.raises(ValueError, match="path"):
        safe_extract(archive, tmp_path / "target")


def test_symlink_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "link.tar.gz"
    with tarfile.open(archive, "w:gz") as bundle:
        info = tarfile.TarInfo("package/link")
        info.type = tarfile.SYMTYPE
        info.linkname = "/etc/passwd"
        bundle.addfile(info)
    with pytest.raises(ValueError, match="link"):
        safe_extract(archive, tmp_path / "target")


def test_duplicate_member_is_rejected(tmp_path: Path) -> None:
    archive = _archive(tmp_path, [("package/file", b"one"), ("package/file", b"two")])
    with pytest.raises(ValueError, match="duplicate"):
        safe_extract(archive, tmp_path / "target")


def test_quota_is_checked_before_materializing(tmp_path: Path) -> None:
    archive = _archive(tmp_path, [("package/large", b"x" * 1024)])
    with pytest.raises(ValueError, match="quota"):
        safe_extract(archive, tmp_path / "target", max_total_bytes=1023)
