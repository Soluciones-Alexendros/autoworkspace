"""Native loading of the packaged Pi extension without invoking a model."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness.pi import rpc_commands  # noqa: E402


def test_packaged_extension_registers_native_command(tmp_path: Path) -> None:
    if shutil.which("pi") is None:
        pytest.skip("Pi binary not on PATH; native extension gate is not_run in this environment")
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()
    env = dict(os.environ, HOME=str(home))
    subprocess.run(["pi", "install", str(ROOT)], env=env, check=True, capture_output=True)
    commands = rpc_commands(project, env=env)
    status = [command for command in commands if command.get("name") == "aw-status"]
    assert len(status) == 1
    assert status[0]["source"] == "extension"
