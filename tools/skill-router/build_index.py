#!/usr/bin/env python3
"""Build skill-index.json from skills/*/SKILL.md frontmatter.

Triggers are sourced from tools/skill-router/intent-map.yaml so the
deterministic router (route.py) can boost on Spanish/English intent
patterns. Output is sorted by skill name for stable diffs.

Usage:
  python3 tools/skill-router/build_index.py           # write index
  python3 tools/skill-router/build_index.py --check   # compare in memory, no write
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import yaml


def build_index(root: pathlib.Path | None = None) -> dict:
    root = root or pathlib.Path(".")
    skills_root = root / "skills"
    triggers_by_skill: dict[str, list[str]] = {}
    intent_map = root / "tools" / "skill-router" / "intent-map.yaml"
    if intent_map.exists():
        intents = (yaml.safe_load(intent_map.read_text(encoding="utf-8")) or {}).get(
            "intents", {}
        )
        for intent in intents.values():
            for skill in intent.get("skills", []):
                triggers_by_skill.setdefault(skill, []).extend(intent.get("patterns", []))

    skills = []
    for md in sorted(skills_root.glob("*/SKILL.md")):
        text = md.read_text(encoding="utf-8")
        try:
            fm = yaml.safe_load(text.split("---")[1])
        except Exception as e:
            print(f"skip {md}: {e}", file=sys.stderr)
            continue
        if not isinstance(fm, dict):
            print(f"skip {md}: frontmatter is not a mapping", file=sys.stderr)
            continue
        meta = fm.get("metadata", {})
        name = fm.get("name", md.parent.name)
        skills.append(
            {
                "name": name,
                "description": fm.get("description", "")[:1000],
                "domain": meta.get("domain", ""),
                "type": meta.get("type", "atomic"),
                "language": meta.get("language", "es"),
                "keywords": [
                    k.strip() for k in meta.get("keywords", "").split(",") if k.strip()
                ],
                "triggers": sorted(set(triggers_by_skill.get(name, []))),
                "entry": f"skills/{md.parent.name}/SKILL.md",
                "compatibility": fm.get("compatibility", "opencode, codex, cursor"),
            }
        )
    return {"version": "3.0.0", "skills": skills}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build or check skill-index.json")
    ap.add_argument(
        "--check",
        action="store_true",
        help="Compare built index to skill-index.json in memory; do not write",
    )
    ap.add_argument("--root", default=".", help="Repository root")
    args = ap.parse_args(argv)
    root = pathlib.Path(args.root)
    built = build_index(root)
    index_path = root / "skill-index.json"

    if args.check:
        if not index_path.is_file():
            print("FAIL: skill-index.json missing", file=sys.stderr)
            return 1
        on_disk = json.loads(index_path.read_text(encoding="utf-8"))
        # Compare skill names and full document for drift
        built_names = [s["name"] for s in built["skills"]]
        disk_names = [s["name"] for s in on_disk.get("skills", [])]
        if built_names != disk_names or built != on_disk:
            print("FAIL: skill-index.json drifts from skills/*/SKILL.md", file=sys.stderr)
            print(f"  built={len(built_names)} disk={len(disk_names)}", file=sys.stderr)
            print("Hint: python3 tools/skill-router/build_index.py  # explicit rebuild")
            return 1
        print(f"Index OK (check-only, no write): {len(built_names)} skills")
        return 0

    index_path.write_text(
        json.dumps(built, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Built index with {len(built['skills'])} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
