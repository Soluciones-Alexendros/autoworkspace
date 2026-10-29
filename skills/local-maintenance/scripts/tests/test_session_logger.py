"""Tests session_logger.py: --help, inválidos, error I/O -> 1, dorada log_event."""

import os
import subprocess
import sys
from contextlib import suppress
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import session_logger

EXIT_USAGE = 2

SCRIPT = "session_logger.py"


def _run(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=".",
        env=e,
    )


def test_help_exit0() -> None:
    r = _run("--help")
    assert r.returncode == 0


def test_invalid_args_exit2() -> None:
    r = _run("--opcion-invalida-xyz")
    assert r.returncode == EXIT_USAGE


def test_main_crea_log_en_tmp(tmp_path: Path) -> None:
    logdir = str(tmp_path / "logs")
    r = _run("--log-dir", logdir, "--session-id", "test-sess-1")
    assert r.returncode == 0
    logf = os.path.join(logdir, "test-sess-1.log")
    assert os.path.isfile(logf)
    content = Path(logf).read_text(encoding="utf-8")
    assert "mantenimiento-linux session log" in content
    assert "SESSION_ID: test-sess-1" in content


def test_error_io_exit1(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*a: str, **k: Any) -> None:
        raise OSError("disco simulado")

    monkeypatch.setattr(os, "makedirs", _boom)
    assert session_logger.main(["--log-dir", "/tmp/irrelevante-xyz", "--session-id", "s"]) == 1


def test_log_event_golden(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    logdir = str(tmp_path / "logs2")
    monkeypatch.setattr(session_logger._STATE, "log_dir", logdir)
    monkeypatch.setattr(session_logger._STATE, "session_id", "gold-1")
    session_logger.log_event("GATE", "R0", "echo hola", "ALLOW", "detalle-x")
    content = Path(logdir, "gold-1.log").read_text(encoding="utf-8")
    assert "[GATE]" in content and "echo hola" in content and "detalle-x" in content
    assert session_logger.get_log_file().endswith("gold-1.log")
    assert session_logger.get_session_id() == "gold-1"


# --- session_logger additional tests for coverage ---


def test_session_logger_init_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    logdir = str(tmp_path / "logs3")
    monkeypatch.setattr(session_logger._STATE, "log_dir", logdir)
    monkeypatch.setattr(session_logger._STATE, "session_id", "init-test")
    with (
        patch("session_logger.run", return_value="6.1.0"),
        patch("session_logger.socket.gethostname", return_value="test-host"),
        patch("session_logger.getpass.getuser", return_value="testuser"),
    ):
        session_logger.init_log()
    logf = os.path.join(logdir, "init-test.log")
    assert os.path.isfile(logf)
    content = Path(logf).read_text(encoding="utf-8")
    assert "SESSION_ID: init-test" in content
    assert "HOSTNAME: test-host" in content
    assert "USER: testuser" in content


def test_session_logger_ensure_log_dir_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*a: str, **k: Any) -> None:
        raise OSError("disco simulado")

    monkeypatch.setattr(session_logger._STATE, "log_dir", "/invalid/path")
    monkeypatch.setattr(os, "makedirs", _boom)
    # Should fallback to /tmp/mantenimiento-linux/logs
    with suppress(OSError):  # el fallback también falla en el entorno de test
        session_logger._ensure_log_dir()


def test_session_logger_log_event_multiple(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    logdir = str(tmp_path / "logs4")
    monkeypatch.setattr(session_logger._STATE, "log_dir", logdir)
    monkeypatch.setattr(session_logger._STATE, "session_id", "multi-test")
    session_logger.log_event("GATE", "R1", "cmd1", "ALLOW", "detalle1")
    session_logger.log_event("EXEC", "R2", "cmd2", "DENY", "detalle2")
    content = Path(logdir, "multi-test.log").read_text(encoding="utf-8")
    assert content.count("[GATE]") == 1
    assert content.count("[EXEC]") == 1
    assert "cmd1" in content and "cmd2" in content
    assert "detalle1" in content and "detalle2" in content


def test_session_logger_getters(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    logdir = str(tmp_path / "logs5")
    monkeypatch.setattr(session_logger._STATE, "log_dir", logdir)
    monkeypatch.setattr(session_logger._STATE, "session_id", "getter-test")
    assert session_logger.get_log_file().endswith("getter-test.log")
    assert session_logger.get_session_id() == "getter-test"
