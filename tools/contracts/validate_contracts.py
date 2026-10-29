#!/usr/bin/env python3
"""Validate the central execution registry (no skills/*/execution.yaml)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from contracts.loader import ContractError, load_execution_contract  # noqa: E402
from execution.registry import check_registry, load_tools  # noqa: E402

# Skills that must appear in the central registry (mutators / orchestrators).
REQUIRED_REGISTRY_TOOLS = ("local-maintenance", "plan-continue", "project-publish")


def catalog(root: Path) -> set[str]:
    skills = root / "skills"
    return {p.name for p in skills.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument(
        "--skill-root",
        default=None,
        help="Validate a single skill via central registry (standalone preflight)",
    )
    args = ap.parse_args(argv)
    if args.skill_root:
        skill_path = Path(args.skill_root).resolve()
        try:
            load_execution_contract(skill_path)
        except ContractError as exc:
            print(f"CONTRACTS: FAIL [{skill_path.name}] {exc}")
            return 1
        print(f"CONTRACTS: OK (standalone {skill_path.name})")
        return 0

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    errors = check_registry(root=root)
    cat = catalog(root)
    try:
        tools = load_tools(force=True)
    except ValueError as exc:
        errors.append(str(exc))
        tools = {}

    for tool_id in REQUIRED_REGISTRY_TOOLS:
        if tool_id not in tools:
            errors.append(f"missing required registry tool: {tool_id}")
        elif tools[tool_id].skill not in cat:
            errors.append(f"registry tool {tool_id}: skill missing from catalog")

    for skill_dir in sorted(p for p in (root / "skills").iterdir() if p.is_dir()):
        exe = skill_dir / "execution.yaml"
        if exe.is_file():
            errors.append(f"[{skill_dir.name}] forbidden execution.yaml under skills/")

    if errors:
        for e in errors:
            print(e)
        print(f"CONTRACTS: FAIL ({len(errors)} errors)")
        return 1
    n_ops = sum(len(t.operations) for t in tools.values())
    print(f"CONTRACTS: OK (registry {len(tools)} tools, {n_ops} ops)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
