"""Tests sintéticos del control privado de denylist (D01-D14)."""

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
import time as time_mod
from pathlib import Path
from typing import Any

import pytest

CLI = Path(__file__).resolve().parents[1] / "private_denylist.py"
SYNTH_PATTERN = r"CI_BACKLOG_01_SYNTH_TOKEN_[A-Z]+"
SYNTH_MATCH_VALUE = "CI_BACKLOG_01_SYNTH_TOKEN_ALPHA"
ENV_KEY = "AUTOWORKSPACE_PRIVATE_PATTERNS"


def _run(
    root: Path,
    env: dict[str, str] | None = None,
    *,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    base = {k: v for k, v in os.environ.items() if k not in {ENV_KEY, "HYGIENE_DENYLIST"}}
    if env is not None:
        base.update(env)
    if extra_env:
        base.update(extra_env)
    return subprocess.run(
        [sys.executable, str(CLI), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
        env=base,
    )


def _init(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)


def _add_file(tmp_path: Path, rel: str, content: str) -> None:
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", "-f", "--", rel], cwd=tmp_path, check=True, capture_output=True)


def test_d01_missing_env(tmp_path: Path) -> None:
    _init(tmp_path)
    r = _run(tmp_path, env={})
    assert r.returncode != 0
    assert "CONFIG_MISSING" in r.stdout or "CONFIG_MISSING" in r.stderr
    assert SYNTH_PATTERN not in r.stdout + r.stderr


def test_d02_empty_env(tmp_path: Path) -> None:
    _init(tmp_path)
    r = _run(tmp_path, env={ENV_KEY: ""})
    assert r.returncode != 0
    assert "CONFIG_EMPTY" in r.stdout or "CONFIG_EMPTY" in r.stderr


def test_d03_whitespace_only(tmp_path: Path) -> None:
    _init(tmp_path)
    r = _run(tmp_path, env={ENV_KEY: "   \n\t\n  "})
    assert r.returncode != 0
    assert "CONFIG_EMPTY" in r.stdout or "CONFIG_EMPTY" in r.stderr


def test_d04_valid_no_match(tmp_path: Path) -> None:
    _init(tmp_path)
    _add_file(tmp_path, "readme.txt", "nothing here\n")
    r = _run(tmp_path, env={ENV_KEY: SYNTH_PATTERN})
    assert r.returncode == 0, r.stdout + r.stderr
    assert "DENYLIST: CLEAR" in r.stdout
    assert SYNTH_PATTERN not in r.stdout + r.stderr


def test_d05_match(tmp_path: Path) -> None:
    _init(tmp_path)
    _add_file(tmp_path, "leak.txt", f"found {SYNTH_MATCH_VALUE} here\n")
    r = _run(tmp_path, env={ENV_KEY: SYNTH_PATTERN})
    assert r.returncode != 0
    assert "DENYLIST_MATCH" in r.stdout or "DENYLIST_MATCH" in r.stderr
    combined = r.stdout + r.stderr
    assert SYNTH_PATTERN not in combined
    assert SYNTH_MATCH_VALUE not in combined
    assert "leak.txt" not in combined


def test_d06_invalid_regex(tmp_path: Path) -> None:
    _init(tmp_path)
    r = _run(tmp_path, env={ENV_KEY: "("})
    assert r.returncode != 0
    assert "REGEX_INVALID" in r.stdout or "REGEX_INVALID" in r.stderr
    assert "(" not in (r.stdout + r.stderr).replace("REGEX_INVALID", "")


def test_d07_multiline_with_blanks(tmp_path: Path) -> None:
    _init(tmp_path)
    _add_file(tmp_path, "ok.txt", "clean\n")
    r = _run(tmp_path, env={ENV_KEY: f"\n{SYNTH_PATTERN}\n\n"})
    assert r.returncode == 0, r.stdout + r.stderr


def test_d08_utf8_pattern(tmp_path: Path) -> None:
    _init(tmp_path)
    _add_file(tmp_path, "ok.txt", "clean\n")
    r = _run(tmp_path, env={ENV_KEY: r"CI_BACKLOG_01_ñ_TOKEN"})
    assert r.returncode == 0, r.stdout + r.stderr


def test_d09_tool_error_distinct(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _init(tmp_path)
    spec = importlib.util.spec_from_file_location("private_denylist_d09", CLI)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["private_denylist_d09"] = mod
    spec.loader.exec_module(mod)

    class BadEnum:
        status = "error"
        reason = "boom"

        def __init__(self) -> None:
            self.files: list[str] = []

    monkeypatch.setattr(mod, "enumerate_tracked", lambda _root: BadEnum())
    monkeypatch.setenv(ENV_KEY, SYNTH_PATTERN)
    assert mod.main_with_root(tmp_path) != 0


def test_d10_read_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _init(tmp_path)
    _add_file(tmp_path, "skills/x/a.txt", "clean\n")
    spec = importlib.util.spec_from_file_location("private_denylist_d10", CLI)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["private_denylist_d10"] = mod
    spec.loader.exec_module(mod)
    real_open = Path.open

    def flaky(self: Path, *a: Any, **k: Any) -> Any:
        if self.name == "a.txt":
            raise OSError("injected")
        return real_open(self, *a, **k)

    monkeypatch.setattr(Path, "open", flaky)
    monkeypatch.setenv(ENV_KEY, SYNTH_PATTERN)
    assert mod.main_with_root(tmp_path) != 0


def test_d11_timeout_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _init(tmp_path)
    _add_file(tmp_path, "skills/x/a.txt", "clean\n")
    spec = importlib.util.spec_from_file_location("private_denylist_d11", CLI)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["private_denylist_d11"] = mod
    spec.loader.exec_module(mod)
    monkeypatch.setenv(ENV_KEY, SYNTH_PATTERN)
    monkeypatch.setattr(mod, "SCAN_TIMEOUT_SEC", 0.0)
    # Force time.monotonic to jump past deadline immediately after start
    real_mono = time_mod.monotonic
    state = {"n": 0}

    def fake_mono() -> float:
        state["n"] += 1
        return 0.0 if state["n"] == 1 else 10.0

    monkeypatch.setattr(mod.time, "monotonic", fake_mono)
    assert mod.main_with_root(tmp_path) != 0
    _ = real_mono


def test_d12_shell_metachar_not_executed(tmp_path: Path) -> None:
    _init(tmp_path)
    marker = tmp_path / "SHOULD_NOT_EXIST"
    # Pattern that looks like shell; must be treated as regex only.
    pat = re.escape("$(touch SHOULD_NOT_EXIST)")
    _add_file(tmp_path, "ok.txt", "clean\n")
    r = _run(tmp_path, env={ENV_KEY: pat})
    assert r.returncode == 0, r.stdout + r.stderr
    assert not marker.exists()


def test_d13_pattern_starting_with_dash(tmp_path: Path) -> None:
    _init(tmp_path)
    _add_file(tmp_path, "ok.txt", "clean\n")
    r = _run(tmp_path, env={ENV_KEY: r"-CI_BACKLOG_01_DASH"})
    assert r.returncode == 0, r.stdout + r.stderr
    assert "-CI_BACKLOG_01_DASH" not in r.stdout + r.stderr


def test_d14_no_leak_on_traceback_paths(tmp_path: Path) -> None:
    _init(tmp_path)
    _add_file(tmp_path, "skills/x/hit.txt", f"{SYNTH_MATCH_VALUE}\n")
    r = _run(tmp_path, env={ENV_KEY: SYNTH_PATTERN})
    assert r.returncode != 0
    blob = r.stdout + r.stderr
    assert SYNTH_PATTERN not in blob
    assert SYNTH_MATCH_VALUE not in blob
    assert "hit.txt" not in blob
