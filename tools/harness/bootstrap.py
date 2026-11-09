"""Safe extraction of a previously authenticated autoworkspace release archive."""

from __future__ import annotations

import argparse
import shutil
import tarfile
from pathlib import Path, PurePosixPath

MAX_FILES = 10_000
MAX_TOTAL_BYTES = 100 * 1024 * 1024


def _member_path(name: str) -> PurePosixPath:
    if not name or "\\" in name:
        raise ValueError(f"invalid archive path: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"archive path escape rejected: {name!r}")
    return path


def safe_extract(  # noqa: C901, PLR0912  # zip slip + size gates need explicit branches
    archive_path: Path,
    destination: Path,
    *,
    max_files: int = MAX_FILES,
    max_total_bytes: int = MAX_TOTAL_BYTES,
) -> None:
    """Inspect all members before creating a new private extraction directory."""
    archive_path = archive_path.resolve()
    destination = destination.resolve()
    if destination.exists():
        raise ValueError(f"extraction destination must be new: {destination}")
    if not destination.parent.is_dir():
        raise ValueError(f"extraction parent missing: {destination.parent}")
    created = False
    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            members = archive.getmembers()
            if len(members) > max_files:
                raise ValueError("archive file quota exceeded")
            total = sum(member.size for member in members if member.isfile())
            if total > max_total_bytes:
                raise ValueError("archive total byte quota exceeded")
            seen: set[str] = set()
            for member in members:
                member_path = _member_path(member.name)
                if str(member_path) in seen:
                    raise ValueError(f"duplicate archive member: {member_path}")
                seen.add(str(member_path))
                if member.issym() or member.islnk():
                    raise ValueError(f"archive link rejected: {member.name}")
                if not (member.isfile() or member.isdir()):
                    raise ValueError(f"special archive member rejected: {member.name}")
            destination.mkdir(mode=0o700)
            created = True
            for member in members:
                output_path = destination / str(_member_path(member.name))
                if member.isdir():
                    output_path.mkdir(parents=True, exist_ok=True)
                    continue
                output_path.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise ValueError(f"unreadable archive member: {member.name}")
                with source, output_path.open("xb") as output:
                    shutil.copyfileobj(source, output)
                output_path.chmod(member.mode & 0o777)
    except Exception:
        if created:
            shutil.rmtree(destination)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely extract a verified autoworkspace archive")
    parser.add_argument("archive", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        safe_extract(args.archive, args.destination)
    except (ValueError, OSError, tarfile.TarError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print(str(args.destination.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
