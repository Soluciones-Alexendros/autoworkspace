#!/usr/bin/env python3
"""Generate frozen quality-debt baseline in pyproject.toml (P11 T5 / P12).

Never hand-edit the generated block. Re-run this script to refresh:

  uv run python3 tools/validate/freeze_quality_debt.py

Produces:
  - [tool.ruff.lint.per-file-ignores] for every existing file that still
    violates the reusable-python ruff --select set (exact codes today).
  - [tool.mypy] excludes for paths mypy cannot load (hyphenated packages,
    duplicate conftest module names).
  - one [[tool.mypy.overrides]] with ignore_errors=true for modules that
    currently fail under mypy --strict (using mypy's own module ids).

New files outside this freeze keep full rigor. Debt retires in P12.

Note: a root .ruff.toml would shadow [tool.ruff] in pyproject.toml; this
script refuses to run while .ruff.toml exists (migrate settings first).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"
RUFF_TOML = ROOT / ".ruff.toml"

RUFF_SELECT = "E,F,W,I,B,UP,SIM,C90,N,PL,RUF"
RUFF_CONFIG = "lint.mccabe.max-complexity = 10"

BEGIN = "# BEGIN GENERATED: quality-debt (tools/validate/freeze_quality_debt.py — do not edit by hand)"
END = "# END GENERATED: quality-debt"

HYPHEN_EXCLUDES = (
    "tools/workspace-router/",
    "tools/skill-router/",
)

FOUND_SOURCE_RE = re.compile(r"BuildSource\(path='(?P<path>[^']+)', module='(?P<module>[^']+)'")
ERROR_RE = re.compile(r"^(?P<path>[^:]+):\d+:\s+error:(?:.*?\[(?P<code>[a-z0-9-]+)\])?\s*$")


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)


def collect_ruff() -> dict[str, list[str]]:
    proc = _run(
        [
            "uv",
            "run",
            "ruff",
            "check",
            ".",
            f"--select={RUFF_SELECT}",
            f"--config={RUFF_CONFIG}",
            "--output-format=json",
        ]
    )
    if not proc.stdout.strip():
        return {}
    data = json.loads(proc.stdout)
    by_file: dict[str, set[str]] = defaultdict(set)
    for item in data:
        path = item["filename"]
        try:
            rel = str(Path(path).resolve().relative_to(ROOT))
        except ValueError:
            rel = path
        by_file[rel].add(item["code"])
    return {k: sorted(v) for k, v in sorted(by_file.items())}


def rule_counts_from_ruff(ruff_map: dict[str, list[str]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    proc = _run(
        [
            "uv",
            "run",
            "ruff",
            "check",
            ".",
            f"--select={RUFF_SELECT}",
            f"--config={RUFF_CONFIG}",
            "--output-format=json",
        ]
    )
    if proc.stdout.strip():
        for item in json.loads(proc.stdout):
            counts[item["code"]] += 1
    return dict(sorted(counts.items(), key=lambda x: (-x[1], x[0])))


def _rel(path: str) -> str:
    raw = path[2:] if path.startswith("./") else path
    try:
        return str(Path(raw).resolve().relative_to(ROOT))
    except ValueError:
        return raw


def collect_mypy_failing_modules() -> tuple[list[str], list[str], dict[str, int]]:
    """Return (modules_for_ignore, exclude_globs, rule_counts)."""
    exclude_globs = [*list(HYPHEN_EXCLUDES), r".*/tests/conftest\.py$"]
    cmd = [
        "uv",
        "run",
        "mypy",
        "--strict",
        "--explicit-package-bases",
        "-v",
        ".",
    ]
    for ex in exclude_globs:
        cmd.extend(["--exclude", ex])
    proc = _run(cmd)
    text = (proc.stdout or "") + (proc.stderr or "")

    path_to_module: dict[str, str] = {}
    for m in FOUND_SOURCE_RE.finditer(text):
        path_to_module[_rel(m.group("path"))] = m.group("module")

    modules: set[str] = set()
    rule_counts: dict[str, int] = defaultdict(int)
    for line in text.splitlines():
        err_match = ERROR_RE.match(line)
        if not err_match:
            continue
        code = err_match.group("code") or "uncategorized"
        rule_counts[code] += 1
        rel = _rel(err_match.group("path"))
        mod = path_to_module.get(rel)
        if mod is None and rel.endswith(".py"):
            # Fallback: basename without suffix (mypy default for script dirs).
            mod = Path(rel).stem
        if mod:
            modules.add(mod)
    return (
        sorted(modules),
        exclude_globs,
        dict(sorted(rule_counts.items(), key=lambda x: (-x[1], x[0]))),
    )


def render_block(
    ruff_map: dict[str, list[str]],
    mypy_modules: list[str],
    mypy_excludes: list[str],
    ruff_counts: dict[str, int],
    mypy_counts: dict[str, int],
) -> str:
    lines: list[str] = [BEGIN, "# Generated baseline — retire in P12. Do not edit by hand."]
    lines.append("# ruff remaining by rule: " + ", ".join(f"{k}={v}" for k, v in ruff_counts.items()))
    lines.append("# mypy remaining by code: " + ", ".join(f"{k}={v}" for k, v in mypy_counts.items()))
    lines.append("")
    select_items = ", ".join(f'"{s.strip()}"' for s in RUFF_SELECT.split(","))
    lines.append("[tool.ruff.lint]")
    lines.append(f"select = [{select_items}]")
    lines.append("")
    lines.append("[tool.ruff.lint.mccabe]")
    lines.append("max-complexity = 10")
    lines.append("")
    lines.append("[tool.ruff.lint.per-file-ignores]")
    for path, codes in ruff_map.items():
        codes_toml = ", ".join(f'"{c}"' for c in codes)
        lines.append(f'"{path}" = [{codes_toml}]')
    lines.append("")
    lines.append("[tool.mypy]")
    lines.append('python_version = "3.12"')
    lines.append("strict = true")
    lines.append("explicit_package_bases = true")
    lines.append("exclude = [")
    for ex in mypy_excludes:
        if "'" in ex:
            raise ValueError(f"exclude pattern contains single quote: {ex!r}")
        lines.append(f"  '{ex}',")
    lines.append("]")
    lines.append("")
    lines.append("[[tool.mypy.overrides]]")
    lines.append("module = [")
    for mod in mypy_modules:
        lines.append(f'  "{mod}",')
    lines.append("]")
    lines.append("ignore_errors = true")
    lines.append(END)
    return "\n".join(lines) + "\n"


_GENERATED_RE = re.compile(
    re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?",
    re.S,
)


def strip_generated(text: str) -> str:
    return _GENERATED_RE.sub("", text).rstrip() + "\n"


def upsert_pyproject(block: str) -> None:
    text = strip_generated(PYPROJECT.read_text(encoding="utf-8"))
    if not text.endswith("\n"):
        text += "\n"
    PYPROJECT.write_text(text + "\n" + block, encoding="utf-8")


def main() -> int:
    if RUFF_TOML.exists():
        print(
            "ERROR: .ruff.toml shadows [tool.ruff] in pyproject.toml. "
            "Move its settings into pyproject and remove .ruff.toml, then re-run.",
            file=sys.stderr,
        )
        return 2
    original = PYPROJECT.read_text(encoding="utf-8")
    PYPROJECT.write_text(strip_generated(original), encoding="utf-8")
    try:
        ruff_map = collect_ruff()
        ruff_counts = rule_counts_from_ruff(ruff_map)
        mypy_modules, mypy_excludes, mypy_counts = collect_mypy_failing_modules()
    except Exception:
        PYPROJECT.write_text(original, encoding="utf-8")
        raise
    block = render_block(ruff_map, mypy_modules, mypy_excludes, ruff_counts, mypy_counts)
    upsert_pyproject(block)
    print(
        json.dumps(
            {
                "ruff_files": len(ruff_map),
                "ruff_diagnostics": sum(ruff_counts.values()),
                "ruff_by_rule": ruff_counts,
                "mypy_modules": len(mypy_modules),
                "mypy_modules_list": mypy_modules,
                "mypy_by_code": mypy_counts,
                "mypy_excludes": mypy_excludes,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
