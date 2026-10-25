"""Tests audit_full.py: --help, inválidos, error perfil/escritura -> 1, doradas."""

import subprocess
import sys

import audit_full

SCRIPT = "audit_full.py"


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


def test_invalid_args_exit2():
    r = _run("--opcion-invalida-xyz")
    assert r.returncode == 2


def test_error_perfil_exit1(tmp_path, monkeypatch):
    def _boom(_p):
        raise OSError("perfil simulado")

    monkeypatch.setattr(audit_full, "load_profile_family", _boom)
    assert audit_full.main([str(tmp_path / "o.json")]) == 1


def test_error_escritura_exit1(tmp_path, monkeypatch):
    import audit_full as af

    monkeypatch.setattr(af, "load_profile_family", lambda _p: ("unknown", "unknown", "x", "", ""))
    monkeypatch.setattr(af, "run", lambda *a, **k: "")
    monkeypatch.setattr(af, "run_check", lambda *a, **k: "")
    assert af.main([str(tmp_path / "nodir" / "o.json"), str(tmp_path / "p.json")]) == 1


def test_run_check_golden():
    assert audit_full.run_check("echo hi").strip() == "hi"


def test_sshd_eff_get_golden(monkeypatch):
    monkeypatch.setattr(audit_full, "sshd_effective", lambda: "permitrootlogin no\npasswordauthentication no\n")
    assert audit_full.sshd_eff_get("permitrootlogin") == "no"
    assert audit_full.sshd_eff_get("inexistente-xyz") == ""
