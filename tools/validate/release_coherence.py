#!/usr/bin/env python3
"""Coherencia de versión de repo, changelog, README y workflows.

Uso:
  python3 tools/validate/release_coherence.py [--root DIR] [--release-gate]
Exit 0 si cumple; 1 si hay fallos.
--release-gate exige sección de changelog para package.json (job de publicación).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(sys.argv[sys.argv.index("--root") + 1]) if "--root" in sys.argv else Path(__file__).resolve().parents[2]
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
README_VERSION_RE = re.compile(r"Versión \*\*(\d+\.\d+\.\d+)\*\*")
CHANGELOG_H2 = re.compile(r"^## \[([0-9]+\.[0-9]+\.[0-9]+)\] - (\d{4}-\d{2}-\d{2})(.*)$")
USES_RE = re.compile(r"^\s+uses:\s+(\S+)", re.M)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ERRORS: list[str] = []


def err(msg: str) -> None:
    ERRORS.append(msg)


def package_version(root: Path) -> str | None:
    path = root / "package.json"
    if not path.is_file():
        err("falta package.json")
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    ver = str(data.get("version", ""))
    if not SEMVER_RE.match(ver):
        err(f"package.json version no semver: {ver!r}")
        return None
    return ver


def check_readme_version(root: Path, version: str | None) -> None:
    path = root / "README.md"
    if not path.is_file():
        err("falta README.md")
        return
    found = README_VERSION_RE.findall(path.read_text(encoding="utf-8"))
    if not found:
        err("README.md sin línea 'Versión **X.Y.Z**'")
        return
    if version is None:
        return
    for value in found:
        if value != version:
            err(f"README.md declara Versión **{value}** y package.json.version es {version}")


def changelog_sections(text: str) -> dict[str, dict[str, object]]:
    sections: dict[str, dict[str, object]] = {}
    current = None
    buf: list[str] = []
    yanked = False
    for line in text.splitlines():
        found = CHANGELOG_H2.match(line)
        if line.startswith("## [") and not found and not line.startswith("## [Unreleased]"):
            err(f"encabezado de changelog inválido: {line}")
            continue
        if found or line.startswith("## [Unreleased]"):
            if current is not None:
                sections[current] = {
                    "yanked": yanked,
                    "body": "\n".join(buf).strip(),
                }
            buf = []
            if found:
                current = found.group(1)
                yanked = "YANKED" in found.group(3)
            else:
                current = "Unreleased"
                yanked = False
            continue
        if current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = {"yanked": yanked, "body": "\n".join(buf).strip()}
    return sections


def check_changelog(root: Path, version: str | None, release_gate: bool) -> None:
    path = root / "CHANGELOG.md"
    if not path.is_file():
        err("falta CHANGELOG.md")
        return
    sections = changelog_sections(path.read_text(encoding="utf-8"))
    if version is None:
        return
    if version in sections:
        info = sections[version]
        if info["yanked"]:
            err(f"{version} está YANKED")
        if not info["body"]:
            err(f"notas vacías para {version}")
        return
    if release_gate:
        err(f"CHANGELOG.md no tiene sección [{version}]")
        return
    if "Unreleased" not in sections:
        err("CHANGELOG.md sin [Unreleased] ni sección de la versión del manifiesto")


def _load_workflow(path: Path, rel: str, yaml: Any) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        err(f"{rel}: YAML inválido: {e}")
        return None
    if not isinstance(data, dict):
        err(f"{rel}: workflow no es un mapping")
        return None
    if "permissions" not in data:
        err(f"{rel}: falta permissions de workflow")
    return data


def _check_job_timeouts(rel: str, data: dict[str, Any]) -> None:
    jobs = data.get("jobs") or {}
    if not isinstance(jobs, dict):
        err(f"{rel}: jobs inválidos")
        return
    for name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        # P11 T0: jobs llamadores de reusable (jobs.<id>.uses) no admiten
        # timeout-minutes en Actions (solo name/uses/with/secrets/needs/if/
        # permissions/concurrency/strategy). Los jobs con steps: y los de
        # reusable-*.yml siguen exigiendo timeout-minutes.
        if "uses" in job and "steps" not in job:
            continue
        if "timeout-minutes" not in job:
            err(f"{rel}: job '{name}' sin timeout-minutes")


def _check_action_pins(rel: str, text: str) -> None:
    for match in USES_RE.findall(text):
        action = match.strip().strip("'\"")
        if action.startswith("./") or action.startswith("docker://"):
            continue
        if "@" not in action:
            err(f"{rel}: uses sin ref: {action}")
            continue
        _repo, ref = action.rsplit("@", 1)
        if not SHA_RE.match(ref):
            err(f"{rel}: uses sin SHA de 40 hex: {action}")


def check_workflows(root: Path) -> None:
    wf_dir = root / ".github" / "workflows"
    if not wf_dir.is_dir():
        err("falta .github/workflows")
        return
    try:
        import yaml  # noqa: PLC0415  # import opcional: PyYAML puede faltar
    except ImportError:
        err("PyYAML requerido para inspeccionar workflows")
        return
    for path in sorted(wf_dir.glob("*.yml")) + sorted(wf_dir.glob("*.yaml")):
        rel = str(path.relative_to(root))
        data = _load_workflow(path, rel, yaml)
        if data is None:
            continue
        _check_job_timeouts(rel, data)
        _check_action_pins(rel, path.read_text(encoding="utf-8"))


def main() -> int:
    release_gate = "--release-gate" in sys.argv
    root = ROOT
    version = package_version(root)
    check_readme_version(root, version)
    check_changelog(root, version, release_gate)
    check_workflows(root)
    print(f"errores: {len(ERRORS)}")
    for e in ERRORS:
        print("FAIL", e)
    print("RELEASE:", "OK" if not ERRORS else "CON-FALLOS")
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
