"""Transactional installation of the complete Cursor harness component set.

Cursor scopes differ, so the component set is scope-aware:

* Project scope (``<project>/.cursor``): hooks, rules and agents are read from the
  repository, so every component is a symlink into the catalog.
* User scope (``~/.cursor``): Cursor reads ``~/.cursor/skills`` and
  ``~/.cursor/agents`` but keeps user rules in Settings, and runs ``hooks.json``
  from ``~/.cursor`` itself. The rule is therefore omitted (reported as such) and
  ``hooks.json`` is generated as an owned file with ``hooks/...`` commands.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MANIFEST_NAME = ".autoworkspace-full-manifest.json"
JOURNAL_NAME = ".autoworkspace-full-journal.json"
SCHEMA_VERSION = 2
RULE_RELATIVE = "rules/autoworkspace.mdc"
USER_RULE_NOTE = (
    "Cursor reads project rules only from <project>/.cursor/rules and keeps user rules in "
    "Customize -> Rules, so rules/autoworkspace.mdc is omitted at user scope. "
    "Paste it into Customize -> Rules if you want the contract globally."
)


class ConflictError(ValueError):
    pass


@dataclass(frozen=True)
class Resource:
    """One owned component: a symlink to the catalog, or a generated file."""

    relative: str
    kind: str
    source: Path | None = None
    content: str | None = None


def _config_dir(target: Path) -> Path:
    return target if target.name == ".cursor" else target / ".cursor"


def _hooks_config(source_root: Path, *, user_scope: bool) -> str:
    raw = (source_root / ".cursor" / "hooks.json").read_text(encoding="utf-8")
    data: dict[str, Any] = json.loads(raw)
    if user_scope:
        # User hooks run from ~/.cursor, so commands drop the project-relative prefix.
        for entries in data.get("hooks", {}).values():
            for entry in entries:
                command = str(entry.get("command", ""))
                entry["command"] = command.replace("python3 .cursor/", "python3 ", 1)
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _resources(source_root: Path, *, user_scope: bool) -> list[Resource]:
    source_root = source_root.resolve()
    resources = [
        Resource(f"skills/{source.name}", "symlink", source)
        for source in sorted((source_root / "skills").iterdir())
        if source.is_dir() and (source / "SKILL.md").is_file()
    ]
    resources.extend(
        Resource(f"agents/{source.name}", "symlink", source)
        for source in sorted((source_root / ".cursor" / "agents").glob("*.md"))
    )
    if not user_scope:
        resources.append(Resource(RULE_RELATIVE, "symlink", source_root / ".cursor" / RULE_RELATIVE))
    if user_scope:
        resources.append(Resource("hooks.json", "generated", content=_hooks_config(source_root, user_scope=True)))
    else:
        resources.append(Resource("hooks.json", "symlink", source_root / ".cursor" / "hooks.json"))
    resources.extend(
        Resource(f"hooks/{source.name}", "symlink", source)
        for source in sorted((source_root / ".cursor" / "hooks").glob("*.py"))
    )
    missing = [
        str(resource.source)
        for resource in resources
        if resource.kind == "symlink" and (resource.source is None or not resource.source.exists())
    ]
    if missing:
        raise ValueError(f"Cursor source resources missing: {missing}")
    return resources


def _owned_by(path: Path, source_root: Path) -> bool:
    try:
        path.resolve().relative_to(source_root.resolve())
        return True
    except ValueError:
        return False


def _state(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if path.is_file():
        return "file"
    if path.exists():
        return "other"
    return "absent"


def _source_of(resource: Resource) -> Path:
    if resource.source is None:
        raise ValueError(f"symlink resource without source: {resource.relative}")
    return resource.source


def _manifest_entries(manifest: dict[str, Any]) -> list[dict[str, str]]:
    """Normalize schema v1 (list of paths) and v2 (list of {path, kind})."""
    entries: list[dict[str, str]] = []
    for item in manifest.get("resources", []):
        if isinstance(item, str):
            entries.append({"path": item, "kind": "symlink"})
        else:
            entries.append({"path": str(item["path"]), "kind": str(item.get("kind", "symlink"))})
    return entries


def _owned_generated(relative: str, manifest: dict[str, Any] | None) -> bool:
    if manifest is None:
        return False
    return any(entry["path"] == relative and entry["kind"] == "generated" for entry in _manifest_entries(manifest))


def _preflight_symlink(resource: Resource, destination: Path, state: str, source_root: Path) -> str:
    if state == "absent":
        return "changed"
    if state != "symlink":
        raise ConflictError(f"real file/dir conflict: {destination}")
    if not destination.exists():
        raise ConflictError(f"broken symlink conflict: {destination}")
    if destination.resolve() == _source_of(resource).resolve():
        return "skipped"
    if _owned_by(destination, source_root):
        return "changed"
    raise ConflictError(f"foreign symlink conflict: {destination}")


def _preflight_generated(
    resource: Resource,
    destination: Path,
    state: str,
    source_root: Path,
    manifest: dict[str, Any] | None,
) -> str:
    if state == "absent":
        return "changed"
    if state == "other":
        raise ConflictError(f"real file/dir conflict: {destination}")
    if state == "symlink":
        if not _owned_by(destination, source_root):
            raise ConflictError(f"foreign symlink conflict: {destination}")
        return "changed"
    if not _owned_generated(resource.relative, manifest):
        raise ConflictError(f"foreign file conflict: {destination} (move it away, then reinstall)")
    return "skipped" if destination.read_text(encoding="utf-8") == resource.content else "changed"


def _preflight(
    resources: list[Resource],
    config: Path,
    source_root: Path,
    manifest: dict[str, Any] | None,
) -> tuple[int, int]:
    changed = skipped = 0
    for resource in resources:
        destination = config / resource.relative
        state = _state(destination)
        outcome = (
            _preflight_generated(resource, destination, state, source_root, manifest)
            if resource.kind == "generated"
            else _preflight_symlink(resource, destination, state, source_root)
        )
        if outcome == "changed":
            changed += 1
        else:
            skipped += 1
    return changed, skipped


def _write_json(path: Path, data: dict[str, Any]) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _rollback(journal_path: Path) -> None:
    if not journal_path.is_file():
        return
    journal: dict[str, Any] = json.loads(journal_path.read_text(encoding="utf-8"))
    for entry in reversed(journal["entries"]):
        if not entry.get("applied"):
            continue
        destination = Path(entry["destination"])
        if destination.is_symlink() or destination.is_file():
            destination.unlink()
        previous = entry.get("previous") or {}
        if previous.get("kind") == "symlink":
            os.symlink(previous["target"], destination)
        elif previous.get("kind") == "file":
            destination.write_text(previous["content"], encoding="utf-8")
    journal_path.unlink(missing_ok=True)


def _action(resource: Resource, destination: Path) -> str:
    state = _state(destination)
    if state == "absent":
        return "created"
    if resource.kind == "symlink":
        unchanged = destination.exists() and destination.resolve() == _source_of(resource).resolve()
        return "unchanged" if unchanged else "replaced"
    if state == "file" and destination.read_text(encoding="utf-8") == resource.content:
        return "unchanged"
    return "replaced"


def _snapshot(resource: Resource, destination: Path, *, owned_generated: bool) -> dict[str, str]:
    state = _state(destination)
    if state == "symlink":
        return {"kind": "symlink", "target": os.readlink(destination)}
    if state == "file" and owned_generated:
        return {"kind": "file", "content": destination.read_text(encoding="utf-8")}
    return {"kind": "absent"}


def _apply(resource: Resource, destination: Path, action: str) -> None:
    if action == "unchanged":
        return
    if destination.is_symlink() or destination.is_file():
        destination.unlink()
    if resource.kind == "symlink":
        os.symlink(str(_source_of(resource).resolve()), destination)
    else:
        destination.write_text(str(resource.content), encoding="utf-8")


def _prune(
    previous: list[dict[str, str]],
    config: Path,
    source_root: Path,
    journal: dict[str, Any],
    journal_path: Path,
) -> list[str]:
    """Drop owned links that the current scope no longer installs (e.g. the rule at user scope)."""
    pruned: list[str] = []
    for entry in previous:
        destination = config / entry["path"]
        if not destination.is_symlink() or not _owned_by(destination, source_root):
            continue
        record = {
            "destination": str(destination),
            "kind": "pruned",
            "action": "removed",
            "previous": {"kind": "symlink", "target": os.readlink(destination)},
            "applied": False,
        }
        journal["entries"].append(record)
        _write_json(journal_path, journal)
        destination.unlink()
        record["applied"] = True
        _write_json(journal_path, journal)
        pruned.append(entry["path"])
        parent = destination.parent
        if parent != config and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
    return pruned


def install_full(
    source_root: Path,
    target: Path,
    *,
    dry_run: bool = False,
    user_scope: bool = False,
) -> dict[str, Any]:
    source_root = source_root.resolve()
    target = target.resolve()
    if target in {Path("/"), Path("/etc"), Path("/usr"), Path("/var"), Path("/root")}:
        raise ValueError(f"privileged target rejected: {target}")
    resources = _resources(source_root, user_scope=user_scope)
    config = _config_dir(target)
    manifest_path = config / MANIFEST_NAME
    existing: dict[str, Any] | None = None
    if manifest_path.is_file() and not manifest_path.is_symlink():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
    changed, skipped = _preflight(resources, config, source_root, existing)
    omitted = [RULE_RELATIVE] if user_scope else []
    result: dict[str, Any] = {
        "harness": "cursor",
        "components": "full",
        "scope": "user" if user_scope else "project",
        "target": str(target),
        "installed": len(resources),
        "changed": changed,
        "skipped": skipped,
        "conflicts": 0,
        "omitted": omitted,
        "dry_run": dry_run,
        "status": "ok",
        "version": _json_version(source_root),
    }
    if user_scope:
        result["notes"] = [USER_RULE_NOTE]
    if dry_run:
        return result

    config.mkdir(parents=True, exist_ok=True)
    journal_path = config / JOURNAL_NAME
    journal: dict[str, Any] = {"schema_version": SCHEMA_VERSION, "entries": []}
    try:
        for resource in resources:
            destination = config / resource.relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            owned = _owned_generated(resource.relative, existing)
            entry = {
                "destination": str(destination),
                "kind": resource.kind,
                "action": _action(resource, destination),
                "previous": _snapshot(resource, destination, owned_generated=owned),
                "applied": False,
            }
            journal["entries"].append(entry)
            _write_json(journal_path, journal)
            _apply(resource, destination, str(entry["action"]))
            entry["applied"] = True
            _write_json(journal_path, journal)
        previous_entries = _manifest_entries(existing) if existing else []
        current = {resource.relative for resource in resources}
        stale = [entry for entry in previous_entries if entry["path"] not in current]
        pruned = _prune(stale, config, source_root, journal, journal_path)
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "source_root": str(source_root),
            "components": "full",
            "scope": "user" if user_scope else "project",
            "resources": [{"path": resource.relative, "kind": resource.kind} for resource in resources],
            "omitted": omitted,
            "version": _json_version(source_root),
        }
        _write_json(config / MANIFEST_NAME, manifest)
        journal_path.unlink(missing_ok=True)
    except Exception:
        _rollback(journal_path)
        raise
    if pruned:
        result["pruned"] = pruned
    return result


def _validated_manifest(source_root: Path, target: Path) -> tuple[Path, dict[str, Any]]:
    config = _config_dir(target.resolve())
    path = config / MANIFEST_NAME
    if not path.is_file() or path.is_symlink():
        raise ValueError("full Cursor manifest missing or invalid")
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if data.get("source_root") != str(source_root.resolve()):
        raise ValueError("manifest belongs to another source checkout")
    for relative in (entry["path"] for entry in _manifest_entries(data)):
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError(f"manifest path escape: {relative}")
    return config, data


def uninstall_full(source_root: Path, target: Path, *, dry_run: bool = False) -> dict[str, Any]:
    config, manifest = _validated_manifest(source_root, target)
    user_scope = manifest.get("scope") == "user"
    removed = 0
    retained: list[str] = []
    for entry in _manifest_entries(manifest):
        relative = entry["path"]
        destination = config / relative
        if not destination.exists() and not destination.is_symlink():
            continue
        if entry["kind"] == "generated":
            if destination.is_symlink() or not destination.is_file():
                retained.append(relative)
                continue
            if destination.read_text(encoding="utf-8") != _hooks_config(source_root.resolve(), user_scope=user_scope):
                retained.append(relative)
                continue
        elif not destination.is_symlink() or not _owned_by(destination, source_root):
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
        "scope": manifest.get("scope", "project"),
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
    parser.add_argument(
        "--user", action="store_true", help="User scope (~/.cursor): omit the rule, generate hooks.json"
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = (
            uninstall_full(args.source, args.target, dry_run=args.dry_run)
            if args.uninstall
            else install_full(args.source, args.target, dry_run=args.dry_run, user_scope=args.user)
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
