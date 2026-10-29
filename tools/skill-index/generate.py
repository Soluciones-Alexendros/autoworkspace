#!/usr/bin/env python3
"""Generate skill-index.json and the marked catalog tables.

skills/ is the only source. skill-index.json is a gitignored artifact.
README.md and docs/TAXONOMY.md carry the same table between:

    <!-- SKILL-INDEX:START -->
    <!-- SKILL-INDEX:END -->
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

import yaml

START = "<!-- SKILL-INDEX:START -->"
END = "<!-- SKILL-INDEX:END -->"
INDEX_VERSION = "7.0.0-alpha.1"
DOC_PATHS = ("README.md", "docs/TAXONOMY.md")


def build_index(root: pathlib.Path | None = None) -> dict:
    root = root or pathlib.Path(".")
    skills_root = root / "skills"
    triggers_by_skill: dict[str, list[str]] = {}
    intent_map = root / "tools" / "skill-router" / "intent-map.yaml"
    if intent_map.exists():
        intents = (yaml.safe_load(intent_map.read_text(encoding="utf-8")) or {}).get("intents", {})
        for intent in intents.values():
            for skill in intent.get("skills", []):
                triggers_by_skill.setdefault(skill, []).extend(intent.get("patterns", []))

    skills = []
    if skills_root.is_dir():
        for md in sorted(skills_root.glob("*/SKILL.md")):
            text = md.read_text(encoding="utf-8")
            try:
                fm = yaml.safe_load(text.split("---", 2)[1])
            except Exception as exc:
                print(f"skip {md}: {exc}", file=sys.stderr)
                continue
            if not isinstance(fm, dict):
                print(f"skip {md}: frontmatter is not a mapping", file=sys.stderr)
                continue
            meta = fm.get("metadata") or {}
            if not isinstance(meta, dict):
                meta = {}
            name = fm.get("name", md.parent.name)
            keywords = meta.get("keywords", "")
            if not isinstance(keywords, str):
                keywords = str(keywords)
            skills.append(
                {
                    "name": name,
                    "description": str(fm.get("description", ""))[:1000],
                    "domain": meta.get("domain", ""),
                    "type": meta.get("type", "atomic"),
                    "language": meta.get("language", "en"),
                    "keywords": [k.strip() for k in keywords.split(",") if k.strip()],
                    "triggers": sorted(set(triggers_by_skill.get(name, []))),
                    "entry": f"skills/{md.parent.name}/SKILL.md",
                    "compatibility": fm.get("compatibility", "cursor, pi"),
                }
            )
    return {"version": INDEX_VERSION, "skills": skills}


def catalog_markdown(root: pathlib.Path) -> str:
    lines = [
        "| Skill | Domain | Description |",
        "| --- | --- | --- |",
    ]
    for skill in build_index(root)["skills"]:
        desc = " ".join(str(skill["description"]).split()).replace("|", "\\|")
        lines.append(f"| `{skill['name']}` | {skill['domain']} | {desc} |")
    return "\n".join(lines) + "\n"


def normalize_catalog(text: str) -> str:
    """Compare tables ignoring Prettier cell padding, dash width and blank lines."""
    lines: list[str] = []
    for raw in text.strip().splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if cells and all(set(cell) <= {"-", ":"} and cell for cell in cells):
                cells = ["---" for _ in cells]
            lines.append("| " + " | ".join(cells) + " |")
        else:
            lines.append(line)
    return "\n".join(lines) + "\n"


def marked_block(root: pathlib.Path) -> str:
    return f"{START}\n{catalog_markdown(root)}{END}\n"


def extract_region(text: str) -> str | None:
    if START not in text or END not in text:
        return None
    inner = text.split(START, 1)[1].split(END, 1)[0]
    return inner.strip() + "\n"


def replace_region(text: str, block: str) -> str:
    if START not in text or END not in text:
        raise ValueError("missing SKILL-INDEX markers")
    pre, rest = text.split(START, 1)
    _, post = rest.split(END, 1)
    return f"{pre}{START}\n{block}{END}{post}"


def region_errors(root: pathlib.Path) -> list[str]:
    expected = normalize_catalog(catalog_markdown(root))
    errors: list[str] = []
    for rel in DOC_PATHS:
        path = root / rel
        if not path.is_file():
            errors.append(f"[catalog] falta {rel}")
            continue
        region = extract_region(path.read_text(encoding="utf-8"))
        if region is None:
            errors.append(f"[catalog] {rel} sin {START} / {END}")
            continue
        if normalize_catalog(region) != expected:
            errors.append(f"[catalog] {rel} bloque distinto del generador")
    return errors


def write_index(root: pathlib.Path) -> pathlib.Path:
    index = build_index(root)
    again = build_index(root)
    if index != again:
        raise RuntimeError("skill index generator is not deterministic")
    path = root / "skill-index.json"
    path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def sync_docs(root: pathlib.Path) -> None:
    block = catalog_markdown(root)
    for rel in DOC_PATHS:
        path = root / rel
        text = path.read_text(encoding="utf-8")
        path.write_text(replace_region(text, block), encoding="utf-8")


def ensure_index(root: pathlib.Path) -> dict:
    path = root / "skill-index.json"
    if not path.is_file():
        write_index(root)
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate skill-index.json and catalog markers")
    ap.add_argument("--root", default=".", help="Repository root")
    ap.add_argument("--check", action="store_true", help="Write the index and fail if doc markers drift")
    ap.add_argument("--sync-docs", action="store_true", help="Rewrite marker regions from skills/")
    args = ap.parse_args(argv)
    root = pathlib.Path(args.root)
    write_index(root)
    if args.sync_docs:
        sync_docs(root)
    errors = region_errors(root)
    if args.check and errors:
        for item in errors:
            print("FAIL", item, file=sys.stderr)
        return 1
    if errors and not args.sync_docs and not args.check:
        for item in errors:
            print("WARN", item, file=sys.stderr)
    count = len(build_index(root)["skills"])
    print(f"Index OK: {count} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
