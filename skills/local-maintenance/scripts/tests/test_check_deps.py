"""Tests check_deps.py: --help, inválidos, falta requerida -> 1, dorada check_cmd."""

import subprocess
import sys

import check_deps

SCRIPT = "check_deps.py"


def _run(*args):
    return subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True,
        text=True,
        cwd=".",
    )


def test_help_exit0():
    r = _run("--help")
    assert r.returncode == 0
    assert "dependencias" in (r.stdout + r.stderr).lower()


def test_invalid_args_exit2():
    r = _run("--opcion-invalida-xyz")
    assert r.returncode == 2


def test_error_falta_requerida_exit1(monkeypatch):
    monkeypatch.setattr(check_deps, "which", lambda cmd: None)
    assert check_deps.main([]) == 1


def test_ok_cuando_todo_presente(monkeypatch):
    monkeypatch.setattr(check_deps, "which", lambda cmd: "/usr/bin/" + cmd)
    assert check_deps.main([]) == 0


def test_check_cmd_golden(monkeypatch):
    monkeypatch.setattr(check_deps, "which", lambda cmd: "/usr/bin/" + cmd if cmd == "jq" else None)
    assert check_deps.check_cmd("jq", True, "jq", "hint", False, False) == 1
    assert check_deps.check_cmd("ausente-xyz", True, "pkg", "hint", False, False) == 0
    assert check_deps.check_cmd("ausente-opt", False, "pkg", "hint", False, False) == 0
