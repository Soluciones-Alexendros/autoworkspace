"""Naming gate: the pre-8.0 name may survive only where it is load-bearing.

Scans live files for the pre-8.0 brand and prefix and fails when
the match is not in an allowlisted file. History (plans, archives, ADRs,
changelog, frozen snapshots) is excluded by path, and generated/caches are
ignored, so the gate is about code and living docs.

Allowlisted files carry the legacy name on purpose: the naming SSOT, the state
fallback, the glossary, the migration tests and the scripts that must recognise
the old paths. Adding a new file to ``ALLOWED_FILES`` is a reviewed decision.

Exit codes: 0 clean, 1 findings, 2 usage.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SCAN_ROOTS = (
    "skills",
    ".cursor",
    ".cursor-plugin",
    "extensions",
    "scripts",
    "tools",
    "templates",
    "stacks",
    "docs",
)
ROOT_FILES = (
    "README.md",
    "ARCHITECTURE.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    "package.json",
    "Makefile",
    ".env.example",
    "run-validation.sh",
)
EXCLUDED_DIR_NAMES = frozenset(
    {
        "plans",
        "archives",
        "decisions",
        ".venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".git",
        "rendered",
    }
)
EXCLUDED_FILES = frozenset({"CHANGELOG.md", "skill-index-7.0.0.json"})
# Local install artifacts (gitignored): symlink manifests carry absolute paths.
EXCLUDED_PREFIXES = (".cursor/skills/", ".pi/skills/")
SUFFIXES = frozenset({".py", ".sh", ".md", ".json", ".yaml", ".yml", ".ts", ".toml", ".mdc", ".example", ""})

ALLOWED_FILES = {
    # Naming SSOT and state fallback: they must spell the old name.
    "tools/harness/naming.py",
    "tools/state_paths.py",
    # Glossary documents what is legacy.
    "docs/GLOSARIO.md",
    # Migration and fallback must be tested against the old name.
    "tools/harness/tests/test_naming.py",
    "tools/harness/tests/test_runtime_migration.py",
    "tools/workspace-router/tests/test_legacy_state_migration.py",
    # The gate itself and its tests must spell the legacy name to define/detect it.
    "tools/validate/naming_gate.py",
    "tools/validate/tests/test_naming_gate.py",
    "tools/execution/tests/test_deny_list.py",
    "tools/execution/tests/test_pi_gate_parity.py",
    "tools/execution/tests/test_env_legacy.py",
    "tools/harness/tests/test_pi_catalog_discovery.py",
    # Installers and gates must recognise the pre-8.0 runtime and prefixes.
    "scripts/runtime-sync.sh",
    "scripts/install-pi.sh",
    "scripts/install-cursor.sh",
    "scripts/tests/test_bootstrap.sh",
    "scripts/tests/test_install.sh",
    "scripts/tests/test_install_journal_wa.sh",
    "scripts/tests/test_standalone_package.sh",
    "scripts/tests/fixtures/release/release.json",
    "extensions/machineroom/gates.ts",
    "extensions/machineroom/path-guard.ts",
    # Contract loader accepts the pre-8.0 dialect.
    "tools/contracts/loader.py",
    "tools/contracts/schemas/execution.schema.json",
    "tools/execution/schemas/registry.schema.json",
    "tools/execution/approval.py",
    "tools/harness/policy.py",
    # Plan of this increment names both sides by design.
    "docs/harness-integration.md",
    "docs/harness-setup.md",
    # Runtime docstrings document the pre-8.0 path.
    "tools/harness/runtime.py",
    # The embedded plan-block keyword of historical plans: renaming it would
    # invalidate every committed plan, so the parser keeps accepting it.
    "tools/contracts/plan.py",
    "tools/contracts/tests/test_plan.py",
    "tools/skill-router/tests/test_catalog_17.py",
    "templates/harness/plan.md",
    "tools/orchestrator/run.py",
    "tools/orchestrator/tests/test_full_flow.py",
    "tools/orchestrator/tests/test_orchestration_red.py",
    "tools/orchestrator/tests/test_scheduler.py",
    "scripts/tests/test_cursor_orchestration.sh",
    "scripts/tests/test_pi_orchestration.sh",
    "scripts/tests/test_orchestration_core.sh",
    "tools/workspace-router/tests/test_task_lifecycle.py",
    # Bootstrap keeps a documented fallback to the pre-8.0 repository variable.
    "scripts/bootstrap.sh",
}

# The ADR-0016 filename is immutable history: links to it may keep the old name.
ADR_FILENAME = "ADR-0016-autoworkspace-host-del-canon.md"

PATTERN = re.compile(r"autoworkspace|\baw[-_](?!fixture)", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    """One offending line: path, line number and the matched text."""

    path: str
    line: int
    text: str

    def render(self) -> str:
        return f"{self.path}:{self.line}: {self.text.strip()[:120]}"


def candidate_files(root: Path) -> list[Path]:
    """Live files subject to the gate, history and caches excluded."""
    files: list[Path] = []
    for name in ROOT_FILES:
        path = root / name
        if path.is_file():
            files.append(path)
    for name in SCAN_ROOTS:
        base = root / name
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix not in SUFFIXES:
                continue
            if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
                continue
            if path.relative_to(root).as_posix().startswith(EXCLUDED_PREFIXES):
                continue
            if path.name in EXCLUDED_FILES:
                continue
            files.append(path)
    return files


def scan(root: Path = ROOT, allowed: set[str] | None = None) -> list[Finding]:
    """Return every unexpected legacy literal."""
    allowed = ALLOWED_FILES if allowed is None else allowed
    findings: list[Finding] = []
    for path in candidate_files(root):
        relative = path.relative_to(root).as_posix()
        if relative in allowed:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if PATTERN.search(line.replace(ADR_FILENAME, "")):
                findings.append(Finding(relative, number, line))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail when the pre-8.0 name leaks into live files")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    findings = scan(args.root.resolve())
    if findings:
        for finding in findings:
            print(finding.render(), file=sys.stderr)
        print(f"FAIL naming naming_gate: {len(findings)} line(s) outside the allowlist", file=sys.stderr)
        return 1
    print(f"naming gate OK ({len(candidate_files(args.root.resolve()))} live files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
