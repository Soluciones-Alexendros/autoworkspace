"""Tests check_deps.py: --help, inválidos, falta requerida -> 1, dorada check_cmd."""

import subprocess
import sys

import check_deps
import pytest

EXIT_USAGE = 2

SCRIPT = "check_deps.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=".",
    )


def test_help_exit0() -> None:
    r = _run("--help")
    assert r.returncode == 0
    assert "dependencias" in (r.stdout + r.stderr).lower()


def test_invalid_args_exit2() -> None:
    r = _run("--opcion-invalida-xyz")
    assert r.returncode == EXIT_USAGE


def test_error_falta_requerida_exit1(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(check_deps, "which", lambda cmd: None)
    assert check_deps.main([]) == 1


def test_ok_cuando_todo_presente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(check_deps, "which", lambda cmd: "/usr/bin/" + cmd)
    assert check_deps.main([]) == 0


def test_check_cmd_golden(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(check_deps, "which", lambda cmd: "/usr/bin/" + cmd if cmd == "jq" else None)
    required = {"required": True, "verbose": False, "install_hint": False}
    optional = {**required, "required": False}
    assert check_deps.check_cmd(("jq", "jq", "hint"), **required) == 1
    assert check_deps.check_cmd(("ausente-xyz", "pkg", "hint"), **required) == 0
    assert check_deps.check_cmd(("ausente-opt", "pkg", "hint"), **optional) == 0
