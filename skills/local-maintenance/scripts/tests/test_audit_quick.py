"""Tests audit_quick.py: --help, inválidos, error perfil -> 1, doradas."""

import subprocess
import sys
from pathlib import Path
from typing import Any

import audit_quick
import pytest

EXIT_USAGE = 2

SCRIPT = "audit_quick.py"


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


def test_invalid_args_exit2() -> None:
    r = _run("--opcion-invalida-xyz")
    assert r.returncode == EXIT_USAGE


def test_error_perfil_exit1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(_p: Any) -> None:
        raise OSError("perfil simulado")

    monkeypatch.setattr(audit_quick, "load_profile_family", _boom)
    assert audit_quick.main([str(tmp_path / "o.json")]) == 1


def test_error_escritura_exit1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(audit_quick, "load_profile_family", lambda _p: ("unknown", "unknown", "x", "", ""))
    # Acelerar: sin subprocesos reales (run mockeado), solo para llegar al write.
    monkeypatch.setattr(audit_quick, "run", lambda *a, **k: "")
    monkeypatch.setattr(audit_quick, "run_check", lambda *a, **k: "")
    # Directorio inexistente -> open falla -> exit 1.
    assert audit_quick.main([str(tmp_path / "nodir" / "o.json"), str(tmp_path / "p.json")]) == 1


def test_run_check_golden() -> None:
    assert audit_quick.run_check("echo hi").strip() == "hi"
    assert isinstance(audit_quick.run_check("exit 3"), str)


def test_sshd_value_golden() -> None:
    v = audit_quick.sshd_value("PermitRootLogin")
    assert isinstance(v, str)
