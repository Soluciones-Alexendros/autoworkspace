#!/usr/bin/env python3
"""Read-only installation and capability diagnostics for Pi and Cursor."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from harness.base import Check, build_report, report_exit_code  # noqa: E402

_INSTALLER_VERSION_RE = re.compile(r'^VERSION="([^"]+)"', re.MULTILINE)


def _json_version(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = data.get("version")
    return str(value) if value is not None else None


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
    installer_path = root / "scripts" / "lib" / "link-skills.sh"
    try:
        match = _INSTALLER_VERSION_RE.search(installer_path.read_text(encoding="utf-8"))
        installer = match.group(1) if match else None
    except OSError:
        installer = None
    checks.append(
        Check(
            "installer-version",
            "contract",
            "pass" if installer and expected and installer == expected else "fail",
            f"installer={installer or 'missing'} expected={expected or 'unknown'}",
        )
    )
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
    for skill in expected:
        link = destination / skill.name
        if not link.is_symlink():
            return Check(f"{harness}-skill-links", "A", "fail", f"not a symlink: {link}")
        target = Path(link.readlink())
        if not target.is_absolute():
            return Check(f"{harness}-skill-links", "A", "fail", f"relative symlink: {link}")
        if not link.exists() or link.resolve() != skill.resolve():
            return Check(f"{harness}-skill-links", "A", "fail", f"wrong or broken target: {link}")
    return Check(f"{harness}-skill-links", "A", "pass", f"{len(expected)} absolute links resolve to catalog")


def cursor_full_check(root: Path) -> Check:
    manifest = root.resolve() / ".cursor" / ".autoworkspace-full-manifest.json"
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        resources = data["resources"]
        assert isinstance(resources, list)
    except (OSError, json.JSONDecodeError, KeyError, AssertionError):
        return Check("cursor-full-components", "A", "fail", "full component manifest missing or invalid")
    for relative in resources:
        path = manifest.parent / relative
        if not path.is_symlink() or not path.exists() or not Path(path.readlink()).is_absolute():
            return Check("cursor-full-components", "A", "fail", f"invalid full component: {relative}")
    required = {"rules/autoworkspace.mdc", "agents/aw-verifier.md", "hooks.json", "hooks/shell_gate.py"}
    if not required <= set(resources):
        return Check("cursor-full-components", "A", "fail", "full component manifest is incomplete")
    return Check("cursor-full-components", "A", "pass", f"{len(resources)} full components verified")


def collect_checks(
    root: Path,
    harness: str,
    expected_version: str | None,
    *,
    native: bool = False,
    source_root: Path | None = None,
    full: bool = False,
) -> list[Check]:
    source = (source_root or root).resolve()
    checks = version_coherence_checks(source, expected_version)
    expected_skills = {
        path.name for path in (source / "skills").iterdir() if path.is_dir() and (path / "SKILL.md").is_file()
    }
    if harness in {"pi", "all"}:
        if not native:
            checks.append(skill_link_check(root, "pi", source_root=source))
        else:
            from harness.pi import discovery_check  # noqa: PLC0415

            checks.append(discovery_check(root, expected_skills))
    if harness in {"cursor", "all"}:
        checks.append(skill_link_check(root, "cursor", source_root=source))
        if full:
            checks.append(cursor_full_check(root))
        if native:
            from harness.cursor import capability_checks  # noqa: PLC0415

            checks.extend(capability_checks(root, expected_skills, require_auth=False))
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Autoworkspace harness doctor")
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
