"""Pi shell gate (TypeScript) must decide exactly like the Cursor hook engine.

The gate is TypeScript, so a pytest cannot import it. This test runs the module
through Node's type stripping when the runtime supports it and compares the whole
decision matrix against ``execution.deny_list.decide_command``. When Node or the
flag is unavailable the test skips: the gate is then ``not_run`` here, never a
silent PASS.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from execution.deny_list import decide_command, load_policy  # noqa: E402

GATES = ROOT / "extensions" / "machineroom" / "gates.ts"
COMMANDS = [
    "sudo pacman -Syu",
    "systemctl restart nginx",
    "rm -rf /etc",
    "rm -rf /tmp/machineroom-x",
    "curl --version",
    "curl https://example.com",
    "git status",
    "npm test",
]


def _node() -> str:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node not on PATH: Pi shell gate parity is not_run here")
    probe = subprocess.run(
        [node, "--experimental-strip-types", "-e", "process.exit(0)"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        pytest.skip("node without --experimental-strip-types: Pi shell gate parity is not_run here")
    return node


def test_pi_gate_matches_the_shared_policy(tmp_path: Path) -> None:
    node = _node()
    assert GATES.is_file(), "the Pi gate module must be versioned"
    script = tmp_path / "parity.mjs"
    script.write_text(
        "import { decideWithFallback } from "
        f'"{GATES.as_posix()}";\n'
        f"const root = {json.dumps(str(ROOT))};\n"
        f"const commands = {json.dumps(COMMANDS)};\n"
        "console.log(JSON.stringify(commands.map((c) => decideWithFallback(c, root).permission)));\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [node, "--experimental-strip-types", str(script)],
        capture_output=True,
        text=True,
        check=True,
    )
    observed = json.loads(proc.stdout.strip().splitlines()[-1])
    policy = load_policy(ROOT)
    expected = [decide_command(command, policy)["permission"] for command in COMMANDS]
    assert observed == expected
    assert "deny" in observed and "allow" in observed and "ask" in observed


def test_pi_gate_fails_closed_without_policy(tmp_path: Path) -> None:
    node = _node()
    script = tmp_path / "missing.mjs"
    script.write_text(
        "import { decideWithFallback } from "
        f'"{GATES.as_posix()}";\n'
        f"const decision = decideWithFallback('git status', {json.dumps(str(tmp_path))});\n"
        "console.log(JSON.stringify(decision));\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [node, "--experimental-strip-types", str(script)],
        capture_output=True,
        text=True,
        check=True,
    )
    decision = json.loads(proc.stdout.strip().splitlines()[-1])
    assert decision["permission"] == "deny"
    assert "policy error" in decision["agent_message"]
