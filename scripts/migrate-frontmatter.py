#!/usr/bin/env python3
"""Migrate frontmatter to v3.0 spec with vendor-neutral phrasing.

Stdlib + pyyaml only (no python-frontmatter dependency).
Idempotent: safe to re-run.
"""

import pathlib
import shutil
import subprocess
import sys
from typing import Any

import yaml

FRONTMATTER_PARTS = 3


def split_frontmatter(text: str, path: pathlib.Path) -> tuple[dict[str, Any] | None, str]:
    if not text.startswith("---"):
        print(f"SKIP (no frontmatter): {path}")
        return None, text
    parts = text.split("---", 2)
    if len(parts) < FRONTMATTER_PARTS:
        print(f"SKIP (malformed frontmatter): {path}")
        return None, text
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        print(f"SKIP (yaml error): {path}: {exc}")
        return None, text
    if not isinstance(fm, dict):
        print(f"SKIP (frontmatter not a mapping): {path}")
        return None, text
    return fm, parts[2]


def dump_frontmatter(fm: dict[str, Any]) -> str:
    body = yaml.safe_dump(
        fm,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=1024,
    )
    return f"---\n{body}---"


def main() -> int:
    changed = 0
    for md in sorted(pathlib.Path("skills").glob("*/SKILL.md")):
        text = md.read_text(encoding="utf-8")
        fm, rest = split_frontmatter(text, md)
        if fm is None:
            continue
        meta = fm.get("metadata", {}) or {}
        # ES -> EN keys (legacy)
        if "dominio" in meta:
            meta["domain"] = meta.pop("dominio")
        if "tipo" in meta:
            meta["type"] = meta.pop("tipo")
        if "idioma" in meta:
            meta["language"] = meta.pop("idioma")
        # normalize (D3: keep existing language, e.g. en; only fill if missing)
        meta.setdefault(
            "domain",
            md.parent.name.split("-")[0] if "-" in md.parent.name else "operate",
        )
        meta.setdefault("type", "atomic")
        meta.setdefault("language", "es")
        meta.setdefault("author", "Soluciones-Alexendros")
        meta["version"] = "3.0.0"  # D2: force v3.0.0 on all skills
        if "keywords" not in meta:
            meta["keywords"] = fm.get("name", "")
        fm["metadata"] = meta
        fm["name"] = md.parent.name  # enforce name==dir
        fm["compatibility"] = "opencode, codex, cursor, copilot"
        if "allowed-tools" not in fm and "allowed_tools" not in fm:
            fm["allowed-tools"] = "Read, Grep, Glob, Bash, Write"
        # legacy single-vendor cleanup already completed; nothing to normalize here
        md.write_text(dump_frontmatter(fm) + rest, encoding="utf-8")
        print(f"migrated {md}")
        changed += 1
    print(f"Done: {changed} skills migrated")
    # Normalize formatting so migrated files stay Prettier-clean (yaml.safe_dump
    # does not match Prettier's YAML/Markdown style). Best-effort, non-fatal.
    if shutil.which("npx"):
        try:
            subprocess.run(
                ["npx", "--no-install", "prettier", "--write", "skills/*/SKILL.md"],
                check=False,
                capture_output=True,
            )
            print("Formatted with Prettier")
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
