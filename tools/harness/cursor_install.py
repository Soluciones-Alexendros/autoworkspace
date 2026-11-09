"""Transactional installation of the complete Cursor harness component set."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

MANIFEST_NAME = ".autoworkspace-full-manifest.json"
JOURNAL_NAME = ".autoworkspace-full-journal.json"


class ConflictError(ValueError):
    pass


def _config_dir(target: Path) -> Path:
    return target if target.name == ".cursor" else target / ".cursor"


def _resources(source_root: Path) -> list[tuple[Path, str]]:
    source_root = source_root.resolve()
    resources: list[tuple[Path, str]] = []
    for source in sorted((source_root / "skills").iterdir()):
        if source.is_dir() and (source / "SKILL.md").is_file():
            resources.append((source, f"skills/{source.name}"))
    resources.append((source_root / ".cursor" / "rules" / "autoworkspace.mdc", "rules/autoworkspace.mdc"))
    for source in sorted((source_root / ".cursor" / "agents").glob("*.md")):
        resources.append((source, f"agents/{source.name}"))
    resources.append((source_root / ".cursor" / "hooks.json", "hooks.json"))
    for source in sorted((source_root / ".cursor" / "hooks").glob("*.py")):
        resources.append((source, f"hooks/{source.name}"))
    missing = [str(source) for source, _relative in resources if not source.exists()]
    if missing:
        raise ValueError(f"Cursor source resources missing: {missing}")
    return resources


def _owned_by(source: Path, source_root: Path) -> bool:
    try:
        source.resolve().relative_to(source_root.resolve())
        return True
    except ValueError:
        return False


def _preflight(resources: list[tuple[Path, str]], config: Path, source_root: Path) -> tuple[int, int]:
    changed = skipped = 0
    for source, relative in resources:
        destination = config / relative
        if not destination.exists() and not destination.is_symlink():
            changed += 1
            continue
        if not destination.is_symlink():
            raise ConflictError(f"real file/dir conflict: {destination}")
        if not destination.exists():
            raise ConflictError(f"broken symlink conflict: {destination}")
        if destination.resolve() == source.resolve():
            skipped += 1
        elif _owned_by(destination, source_root):
            changed += 1
        else:
            raise ConflictError(f"foreign symlink conflict: {destination}")
    return changed, skipped


def _write_json(path: Path, data: dict[str, Any]) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _rollback(journal_path: Path) -> None:
    if not journal_path.is_file():
        return
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    for entry in reversed(journal["entries"]):
        if not entry.get("applied"):
            continue
        destination = Path(entry["destination"])
        if destination.is_symlink() or destination.is_file():
            destination.unlink()
        previous = entry.get("previous")
        if previous:
            os.symlink(previous, destination)
    journal_path.unlink(missing_ok=True)


def install_full(source_root: Path, target: Path, *, dry_run: bool = False) -> dict[str, Any]:
    source_root = source_root.resolve()
    target = target.resolve()
    if target in {Path("/"), Path("/etc"), Path("/usr"), Path("/var"), Path("/root")}:
        raise ValueError(f"privileged target rejected: {target}")
    resources = _resources(source_root)
    config = _config_dir(target)
    changed, skipped = _preflight(resources, config, source_root)
    result: dict[str, Any] = {
        "harness": "cursor",
        "components": "full",
        "target": str(target),
        "installed": len(resources),
        "changed": changed,
        "skipped": skipped,
        "conflicts": 0,
        "dry_run": dry_run,
        "status": "ok",
        "version": _json_version(source_root),
    }
    if dry_run:
        return result

    config.mkdir(parents=True, exist_ok=True)
    journal_path = config / JOURNAL_NAME
    journal: dict[str, Any] = {"schema_version": 1, "entries": []}
    try:
        for source, relative in resources:
            destination = config / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            previous = os.readlink(destination) if destination.is_symlink() else None
            action = (
                "unchanged"
                if destination.is_symlink() and destination.resolve() == source.resolve()
                else ("replaced" if destination.is_symlink() else "created")
            )
            entry = {
                "destination": str(destination),
                "previous": previous,
                "action": action,
                "applied": False,
            }
            journal["entries"].append(entry)
            _write_json(journal_path, journal)
            if action != "unchanged":
                if destination.is_symlink():
                    destination.unlink()
                os.symlink(str(source.resolve()), destination)
            entry["applied"] = True
            _write_json(journal_path, journal)
        manifest = {
            "schema_version": 1,
            "source_root": str(source_root),
            "components": "full",
            "resources": [relative for _source, relative in resources],
            "version": _json_version(source_root),
        }
        _write_json(config / MANIFEST_NAME, manifest)
        journal_path.unlink(missing_ok=True)
    except Exception:
        _rollback(journal_path)
        raise
    return result


def _validated_manifest(source_root: Path, target: Path) -> tuple[Path, dict[str, Any]]:
    config = _config_dir(target.resolve())
    path = config / MANIFEST_NAME
    if not path.is_file() or path.is_symlink():
        raise ValueError("full Cursor manifest missing or invalid")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("source_root") != str(source_root.resolve()):
        raise ValueError("manifest belongs to another source checkout")
    for relative in data.get("resources", []):
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError(f"manifest path escape: {relative}")
    return config, data


def uninstall_full(source_root: Path, target: Path, *, dry_run: bool = False) -> dict[str, Any]:
    config, manifest = _validated_manifest(source_root, target)
    removed = 0
    retained: list[str] = []
    for relative in manifest["resources"]:
        destination = config / relative
        if not destination.exists() and not destination.is_symlink():
            continue
        if not destination.is_symlink() or not _owned_by(destination, source_root):
            retained.append(relative)
            continue
        if not dry_run:
            destination.unlink()
        removed += 1
    if not dry_run:
        (config / MANIFEST_NAME).unlink(missing_ok=True)
    return {
        "harness": "cursor",
        "components": "full",
        "target": str(target.resolve()),
        "removed": removed,
        "retained": retained,
        "dry_run": dry_run,
        "status": "ok",
    }


def _json_version(source_root: Path) -> str:
    data = json.loads((source_root / "package.json").read_text(encoding="utf-8"))
    return str(data["version"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install the complete Cursor harness")
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = (
            uninstall_full(args.source, args.target, dry_run=args.dry_run)
            if args.uninstall
            else install_full(args.source, args.target, dry_run=args.dry_run)
        )
    except (ConflictError, ValueError, OSError) as exc:
        if args.json:
            print(
                json.dumps({"status": "conflict" if isinstance(exc, ConflictError) else "failed", "detail": str(exc)})
            )
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(result, ensure_ascii=False) if args.json else f"Cursor full {result['status']}: {result['target']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
