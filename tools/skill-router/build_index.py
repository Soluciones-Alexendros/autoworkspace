#!/usr/bin/env python3
"""Shim. The generator lives in tools/skill-index/generate.py."""

from __future__ import annotations

import importlib.util
import pathlib

_PATH = pathlib.Path(__file__).resolve().parents[1] / "skill-index" / "generate.py"
_spec = importlib.util.spec_from_file_location("skill_index_generate", _PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load {_PATH}")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

build_index = _mod.build_index


def main(argv: list[str] | None = None) -> int:
    return _mod.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
