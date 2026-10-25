"""Tests audit_quick.py: --help, inválidos, error perfil -> 1, doradas."""

import subprocess
import sys

import audit_quick

SCRIPT = "audit_quick.py"


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

    monkeypatch.setattr(audit_quick, "load_profile_family", _boom)
    assert audit_quick.main([str(tmp_path / "o.json")]) == 1


def test_error_escritura_exit1(tmp_path, monkeypatch):
    import audit_quick as aq

    monkeypatch.setattr(aq, "load_profile_family", lambda _p: ("unknown", "unknown", "x", "", ""))
    # Acelerar: sin subprocesos reales (run mockeado), solo para llegar al write.
    monkeypatch.setattr(aq, "run", lambda *a, **k: "")
    monkeypatch.setattr(aq, "run_check", lambda *a, **k: "")
    # Directorio inexistente -> open falla -> exit 1.
    assert aq.main([str(tmp_path / "nodir" / "o.json"), str(tmp_path / "p.json")]) == 1


def test_run_check_golden():
    assert audit_quick.run_check("echo hi").strip() == "hi"
    assert isinstance(audit_quick.run_check("exit 3"), str)


def test_sshd_value_golden():
    v = audit_quick.sshd_value("PermitRootLogin")
    assert isinstance(v, str)
