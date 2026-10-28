"""Tests audit_full.py: --help, inválidos, error perfil/escritura -> 1, doradas."""

import subprocess
import sys
from pathlib import Path
from typing import Any

import audit_full
import pytest

EXIT_USAGE = 2

SCRIPT = "audit_full.py"


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

    monkeypatch.setattr(audit_full, "load_profile_family", _boom)
    assert audit_full.main([str(tmp_path / "o.json")]) == 1


def test_error_escritura_exit1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(audit_full, "load_profile_family", lambda _p: ("unknown", "unknown", "x", "", ""))
    monkeypatch.setattr(audit_full, "run", lambda *a, **k: "")
    monkeypatch.setattr(audit_full, "run_check", lambda *a, **k: "")
    assert audit_full.main([str(tmp_path / "nodir" / "o.json"), str(tmp_path / "p.json")]) == 1


def test_run_check_golden() -> None:
    assert audit_full.run_check("echo hi").strip() == "hi"


def test_sshd_eff_get_golden(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(audit_full, "sshd_effective", lambda: "permitrootlogin no\npasswordauthentication no\n")
    assert audit_full.sshd_eff_get("permitrootlogin") == "no"
    assert audit_full.sshd_eff_get("inexistente-xyz") == ""
