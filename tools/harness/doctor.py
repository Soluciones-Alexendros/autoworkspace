#!/usr/bin/env python3
"""Read-only installation and capability diagnostics for Pi and Cursor."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from harness.base import Check, build_report, report_exit_code  # noqa: E402

_VERSION_ASSIGN_RE = re.compile(r"^VERSION=(.+)$", re.MULTILINE)
_LITERAL_VERSION_RE = re.compile(r'^"([0-9][^"$`]*)"$')
_PACKAGE_JSON_REF = "package.json"


def _json_version(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = data.get("version")
    return str(value) if value is not None else None


def _version_assignment(text: str) -> str | None:
    match = _VERSION_ASSIGN_RE.search(text)
    return match.group(1).strip() if match else None


def installer_version_check(root: Path, expected: str | None) -> Check:
    """Drift guard: the skills installer may derive the version, never lag behind it."""
    try:
        text = (root / "scripts" / "lib" / "link-skills.sh").read_text(encoding="utf-8")
    except OSError:
        return Check("installer-version", "contract", "fail", "installer missing")
    assignment = _version_assignment(text)
    if assignment is None:
        return Check("installer-version", "contract", "fail", "installer VERSION assignment missing")
    literal = _LITERAL_VERSION_RE.match(assignment)
    if literal is not None:
        value = literal.group(1)
        matches = bool(expected) and value == expected
        return Check(
            "installer-version",
            "contract",
            "pass" if matches else "fail",
            f"installer={value} expected={expected or 'unknown'}",
        )
    if _PACKAGE_JSON_REF in assignment:
        # Derived form keeps package.json as the only source of truth, so it cannot drift.
        return Check(
            "installer-version",
            "contract",
            "pass" if expected else "fail",
            f"installer=derived from package.json expected={expected or 'unknown'}",
        )
    return Check(
        "installer-version",
        "contract",
        "fail",
        f"installer VERSION is neither literal nor package.json-derived: {assignment}",
    )


def version_coherence_checks(root: Path, expected_version: str | None = None) -> list[Check]:
    root = root.resolve()
    package = _json_version(root / "package.json")
    expected = expected_version or package
    checks = [
        Check(
            "package-version",
            "contract",
            "pass" if package and (expected_version is None or package == expected_version) else "fail",
            f"package={package or 'missing'} expected={expected or 'unknown'}",
        )
    ]
    plugin = _json_version(root / ".cursor-plugin" / "plugin.json")
    checks.append(
        Check(
            "cursor-plugin-version",
            "contract",
            "pass" if plugin and expected and plugin == expected else "fail",
            f"cursor-plugin={plugin or 'missing'} expected={expected or 'unknown'}",
        )
    )
    checks.append(installer_version_check(root, expected))
    return checks


def skill_link_check(root: Path, harness: str, *, source_root: Path | None = None) -> Check:
    root = root.resolve()
    source = (source_root or root).resolve() / "skills"
    destination = root / (".pi/skills" if harness == "pi" else ".cursor/skills")
    expected = (
        sorted(path for path in source.iterdir() if path.is_dir() and (path / "SKILL.md").is_file())
        if source.is_dir()
        else []
    )
    if not expected or not destination.is_dir():
        return Check(f"{harness}-skill-links", "A", "fail", "catalog or destination missing")
    relative_count = 0
    for skill in expected:
        link = destination / skill.name
        if not link.is_symlink():
            return Check(f"{harness}-skill-links", "A", "fail", f"not a symlink: {link}")
        if not Path(link.readlink()).is_absolute():
            relative_count += 1
        if not link.exists() or link.resolve() != skill.resolve():
            return Check(f"{harness}-skill-links", "A", "fail", f"wrong or broken target: {link}")
    detail = f"{len(expected)} links resolve to catalog"
    if relative_count:
        detail += f" ({relative_count} relative)"
    return Check(f"{harness}-skill-links", "A", "pass", detail)


def cursor_full_check(root: Path) -> Check:  # noqa: C901, PLR0911  # v1/v2 + user/project link checks
    manifest = root.resolve() / ".cursor" / ".machineroom-full-manifest.json"
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        entries = _full_manifest_entries(data)
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        return Check("cursor-full-components", "A", "fail", "full component manifest missing or invalid")
    user_scope = data.get("scope") == "user"
    source_root = Path(str(data.get("source_root", "")))
    for relative, kind in entries:
        path = manifest.parent / relative
        if kind == "generated":
            # Legacy user-scope hooks.json written as a real file.
            if path.is_symlink() or not path.is_file():
                return Check("cursor-full-components", "A", "fail", f"invalid generated component: {relative}")
            continue
        if not path.is_symlink() or not path.exists():
            return Check("cursor-full-components", "A", "fail", f"invalid full component: {relative}")
        link_text = Path(path.readlink())
        if user_scope:
            if link_text.is_absolute():
                return Check("cursor-full-components", "A", "fail", f"user link must be relative: {relative}")
            if source_root.parts and not _resolves_under(path, source_root):
                return Check("cursor-full-components", "A", "fail", f"user link escapes runtime: {relative}")
        elif not link_text.is_absolute():
            return Check("cursor-full-components", "A", "fail", f"project link must be absolute: {relative}")
    required = {"agents/mr-verifier.md", "hooks.json", "hooks/shell_gate.py"}
    if not user_scope:
        # User rules live in Cursor Settings, so the project rule is project-scope only.
        required.add("rules/machineroom.mdc")
    if not required <= {relative for relative, _kind in entries}:
        return Check("cursor-full-components", "A", "fail", "full component manifest is incomplete")
    scope = "user" if user_scope else "project"
    return Check("cursor-full-components", "A", "pass", f"{len(entries)} full components verified ({scope} scope)")


def _resolves_under(link: Path, root: Path) -> bool:
    try:
        link.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _full_manifest_entries(data: dict[str, Any]) -> list[tuple[str, str]]:
    """Accept schema v1 (paths) and v2 ({path, kind}); generated files are owned, not linked."""
    raw = data["resources"]
    if not isinstance(raw, list):
        raise TypeError("resources must be a list")
    entries: list[tuple[str, str]] = []
    for item in raw:
        if isinstance(item, str):
            entries.append((item, "symlink"))
        elif isinstance(item, dict):
            entries.append((str(item["path"]), str(item.get("kind", "symlink"))))
        else:
            raise TypeError(f"invalid manifest resource: {item!r}")
    return entries


def collect_checks(  # noqa: PLR0913  # doctor entry: keyword-only harness/native/full options
    root: Path,
    harness: str,
    expected_version: str | None,
    *,
    native: bool = False,
    source_root: Path | None = None,
    full: bool = False,
) -> list[Check]:
    source = (source_root or root).resolve()
    if (source / ".runtime-manifest.json").is_file():
        # Machine runtime payload: package.json only (no plugin / installer scripts).
        package = _json_version(source / "package.json")
        checks = [
            Check(
                "package-version",
                "contract",
                "pass" if package and (expected_version is None or package == expected_version) else "fail",
                f"package={package or 'missing'} expected={expected_version or package or 'unknown'} (runtime)",
            )
        ]
    else:
        checks = version_coherence_checks(source, expected_version)
    expected_skills = {
        path.name for path in (source / "skills").iterdir() if path.is_dir() and (path / "SKILL.md").is_file()
    }
    if harness in {"pi", "all"}:
        if not native:
            checks.append(skill_link_check(root, "pi", source_root=source))
        else:
            from harness.pi import pi_discovery_check  # noqa: PLC0415

            checks.append(pi_discovery_check(root, expected_skills))
    if harness in {"cursor", "all"}:
        checks.append(skill_link_check(root, "cursor", source_root=source))
        if full:
            checks.append(cursor_full_check(root))
        if native:
            from harness.cursor import capability_checks  # noqa: PLC0415

            checks.extend(capability_checks(root, expected_skills, require_auth=False))
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Machineroom harness doctor")
    parser.add_argument("--harness", choices=("pi", "cursor", "all"), default="all")
    parser.add_argument("--target", type=Path, default=Path("."))
    parser.add_argument("--source", type=Path, help="Package/catalog source when it differs from target")
    parser.add_argument("--full", action="store_true", help="Require the complete Cursor component manifest")
    parser.add_argument("--expected-version")
    parser.add_argument("--native", action="store_true", help="Run native discovery checks when available")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = args.target.resolve()
    source = (args.source or root).resolve()
    if not root.is_dir() or not source.is_dir():
        print(f"ERROR: target/source is not a directory: {root} / {source}", file=sys.stderr)
        return 2
    checks = collect_checks(
        root,
        args.harness,
        args.expected_version,
        native=args.native,
        source_root=source,
        full=args.full,
    )
    package = _json_version(source / "package.json")
    report = build_report(
        args.harness,
        checks,
        package_version=package,
        source=str(source),
        target=str(root),
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{args.harness}: {report['outcome']}")
        for reason in report["reasons"]:
            print(reason)
    return report_exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
