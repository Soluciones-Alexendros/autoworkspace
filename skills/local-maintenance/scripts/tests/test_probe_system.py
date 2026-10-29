"""Tests probe_system.py: --help, inválidos, error distro -> 1, doradas."""

import builtins
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import probe_system
import pytest

EXIT_USAGE = 2

SCRIPT = "probe_system.py"


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


def test_error_detect_distro_exit1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom() -> None:
        raise OSError("os-release simulado")

    monkeypatch.setattr(probe_system, "detect_distro", _boom)
    assert probe_system.main([str(tmp_path / "out.json")]) == 1


def test_error_write_exit1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Fuerza fallo de escritura sin tocar el sistema: open siempre falla.
    real_open = builtins.open

    def _boom_open(*a: str, **k: Any) -> None:
        raise OSError("solo-lectura simulada")

    monkeypatch.setattr("builtins.open", _boom_open)
    try:
        assert probe_system.main([str(tmp_path / "out.json")]) == 1
    finally:
        monkeypatch.setattr("builtins.open", real_open)


def test_kernel_info_keys_golden() -> None:
    info = probe_system.get_kernel_info()
    assert set(info) >= {"release", "version", "arch", "cmdline"}


def test_journal_info_keys_golden() -> None:
    info = probe_system.get_journal_info()
    assert set(info) >= {"disk_usage", "errors_24h", "coredumps"}


def test_probe_tmp_output_golden(tmp_path: Path) -> None:
    out = tmp_path / "profile.json"
    rc = probe_system.main([str(out)])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert set(data) >= {"metadata", "distro", "kernel", "hardware"}
