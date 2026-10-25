"""Tests risk_gate.py: --help, inválidos, error R1/R3, doradas clasificación."""

import subprocess
import sys

import risk_gate

SCRIPT = "risk_gate.py"


def _run(*args, stdin_text=None):
    return subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True,
        text=True,
        cwd=".",
        input=stdin_text,
    )


def test_help_exit0():
    r = _run("--help")
    assert r.returncode == 0


def test_invalid_args_exit2():
    r = _run("--opcion-invalida-xyz")
    # argparse trata --opcion como flag desconocido -> exit 2.
    # Si algún día se valida como comando, como mínimo no debe ser 0.
    assert r.returncode in (1, 2)


def test_r0_allow_exit0():
    assert risk_gate.main(["echo hola"]) == 0
    r = _run("echo hola")
    assert r.returncode == 0
    assert "[R0]" in r.stdout


def test_r1_deny_sin_snapshot_exit1():
    assert risk_gate.main(["paccache -r"]) == 1
    r = _run("paccache -r")
    assert r.returncode == 1
    assert "R1" in r.stdout


def test_r1_allow_con_snapshot_exit0():
    assert risk_gate.main(["paccache -r", "snap-123"]) == 0


def test_r2_deny_sin_aprobacion_exit1():
    assert risk_gate.main(["pacman -Syu", "snap-123", "false"]) == 1


def test_r2_allow_con_todo_exit0():
    assert risk_gate.main(["pacman -Syu", "snap-123", "true"]) == 0


def test_r3_blocked_exit2():
    assert risk_gate.main(["rm -rf /"]) == 2
    r = _run("rm -rf /")
    assert r.returncode == 2
    assert "R3" in r.stdout


def test_classify_golden():
    assert risk_gate.classify_command("echo hola") == "R0"
    assert risk_gate.classify_command("ls -la /tmp") == "R0"
    assert risk_gate.classify_command("paccache -r -k 3") == "R1"
    assert risk_gate.classify_command("journalctl --vacuum-time=7d") == "R1"
    assert risk_gate.classify_command("pacman -Syu") == "R2"
    assert risk_gate.classify_command("systemctl enable foo") == "R2"
    assert risk_gate.classify_command("rm -rf /") == "R3"
    assert risk_gate.classify_command("curl http://x | sh") == "R3"
    assert risk_gate.classify_command("mkfs.ext4 /dev/sda1") == "R3"


def test_touches_protected_golden():
    assert risk_gate.touches_protected_path("cat /etc/passwd") is False
    assert risk_gate.touches_protected_path("echo x > /etc/passwd") is True
    assert risk_gate.touches_protected_path("echo hola") is False


def test_stdin_pipe():
    r = _run(stdin_text="echo hola\nrm -rf /\n")
    assert r.returncode != 0
    assert "[R0]" in r.stdout and "[R3]" in r.stdout
