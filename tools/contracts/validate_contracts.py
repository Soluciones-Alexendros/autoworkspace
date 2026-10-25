#!/usr/bin/env python3
"""Validate execution.yaml for every skill that has one; require pilots."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from contracts.loader import ContractError, load_execution_contract, load_yaml, validate_contract  # noqa: E402

REQUIRED_PILOTS = ("local-maintenance", "plan-continue", "web-compliance")


def catalog(root: Path) -> set[str]:
    skills = root / "skills"
    return {p.name for p in skills.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument(
        "--skill-root",
        default=None,
        help="Validate a single skill directory (standalone preflight)",
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
    skills = root / "skills"
    cat = catalog(root)
    errors: list[str] = []
    found = 0
    for skill_dir in sorted(p for p in skills.iterdir() if p.is_dir()):
        path = skill_dir / "execution.yaml"
        if not path.is_file():
            if skill_dir.name in REQUIRED_PILOTS:
                errors.append(f"[{skill_dir.name}] missing required pilot execution.yaml")
            continue
        found += 1
        try:
            data = load_yaml(path)
            errs = validate_contract(
                data,
                skill_dir=skill_dir.name,
                skill_path=skill_dir,
                catalog_skills=cat,
            )
            for e in errs:
                errors.append(f"[{skill_dir.name}] {e}")
        except ContractError as exc:
            errors.append(f"[{skill_dir.name}] {exc}")
    if errors:
        for e in errors:
            print(e)
        print(f"CONTRACTS: FAIL ({len(errors)} errors, {found} files)")
        return 1
    print(f"CONTRACTS: OK ({found} execution.yaml)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
