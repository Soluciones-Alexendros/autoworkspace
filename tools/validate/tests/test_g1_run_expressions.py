"""G01-G05: detector G1 de expresiones en run."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

G1 = Path(__file__).resolve().parents[1] / "g1_run_expressions.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("g1_mod", G1)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["g1_mod"] = mod
    spec.loader.exec_module(mod)
    return mod


def _wf(root: Path, name: str, body: str) -> None:
    d = root / ".github" / "workflows"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(body, encoding="utf-8")


def test_g01_unsafe_run_fails(tmp_path: Path) -> None:
    mod = _load()
    _wf(
        tmp_path,
        "bad.yml",
        """
name: bad
on: push
permissions: {}
jobs:
  j:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - run: echo ${{ github.event.issue.title }}
""",
    )
    assert mod.run_g1(tmp_path) != 0


def test_g02_env_quoted_passes(tmp_path: Path) -> None:
    mod = _load()
    _wf(
        tmp_path,
        "good.yml",
        """
name: good
on: push
permissions: {}
jobs:
  j:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - env:
          TITLE: ${{ github.event.issue.title }}
        run: echo "$TITLE"
""",
    )
    assert mod.run_g1(tmp_path) == 0


def test_g03_invalid_yaml_fails(tmp_path: Path) -> None:
    mod = _load()
    _wf(tmp_path, "broken.yml", "jobs: [\n  invalid: {\n")
    assert mod.run_g1(tmp_path) != 0


def test_g04_comment_and_fixture_no_false_positive(tmp_path: Path) -> None:
    mod = _load()
    _wf(
        tmp_path,
        "comment.yml",
        """
name: c
on: push
permissions: {}
jobs:
  j:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      # ${{ github.event.issue.title }} en comentario no cuenta
      - run: echo safe
""",
    )
    # Fixture outside workflows must not be scanned
    fix = tmp_path / "tools" / "validate" / "tests" / "fixtures"
    fix.mkdir(parents=True)
    (fix / "evil.yml").write_text("run: echo ${{ github.event }}\n", encoding="utf-8")
    assert mod.run_g1(tmp_path) == 0


def test_g05_reusable_workflow_inspected(tmp_path: Path) -> None:
    mod = _load()
    _wf(
        tmp_path,
        "reusable-python.yml",
        """
name: reusable
on:
  workflow_call:
permissions: {}
jobs:
  quality:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - run: echo ${{ inputs.x }}
""",
    )
    assert mod.run_g1(tmp_path) != 0
