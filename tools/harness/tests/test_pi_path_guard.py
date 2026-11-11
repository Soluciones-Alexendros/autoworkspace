"""Pi path-guard (TypeScript): the fail-closed decision must be provable.

``path-guard.ts`` protects writes outside ``~/Work``: hard lists block, config
files confirm, and any unlisted path is fail-closed. The decision lives inside
the extension, so this test drives the module through Node's type stripping and
asserts the full matrix. It skips (``not_run``) when Node cannot run it.

RED target: ``decidePath`` does not exist yet, so the first run must fail.
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

PATH_GUARD = ROOT / "extensions" / "machineroom" / "path-guard.ts"


def _node() -> str:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node not on PATH: path-guard decision is not_run here")
    probe = subprocess.run(
        [node, "--experimental-strip-types", "-e", "process.exit(0)"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        pytest.skip("node without --experimental-strip-types: path-guard decision is not_run here")
    return node


def _decisions(tmp_path: Path, home: Path, has_ui: bool) -> list[str]:
    node = _node()
    work = home / "Work"
    matrix = [
        str(work / "notes.txt"),
        "/tmp/machineroom-x/foo",
        str(home),
        str(home / ".ssh" / "id_rsa"),
        str(home / ".machineroom" / "runtime"),
        str(home / ".pi" / "agent" / "auth.json"),
        str(home / "proj" / ".env"),
        str(home / ".pi" / "agent" / "settings.json"),
        str(home / "random" / "file.txt"),
    ]
    script = tmp_path / "matrix.mjs"
    script.write_text(
        "import { decidePath } from "
        f'"{PATH_GUARD.as_posix()}";\n'
        f"const home = {json.dumps(str(home))};\n"
        f"const work = {json.dumps(str(work))};\n"
        f"const hasUI = {'true' if has_ui else 'false'};\n"
        f"const paths = {json.dumps(matrix)};\n"
        "console.log(JSON.stringify(paths.map((p) => decidePath(p, { home, work, hasUI }).verdict)));\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [node, "--experimental-strip-types", str(script)],
        capture_output=True,
        text=True,
        check=True,
    )
    verdicts: list[str] = json.loads(proc.stdout.strip().splitlines()[-1])
    return verdicts


def test_path_guard_matrix_is_fail_closed_without_ui(tmp_path: Path) -> None:
    home = tmp_path / "home"
    verdicts = _decisions(tmp_path, home, has_ui=False)
    assert verdicts == [
        "allow",  # inside ~/Work
        "allow",  # explicit /tmp allowlist prefix
        "block",  # home root
        "block",  # hard dir
        "block",  # machineroom runtime
        "block",  # hard file
        "block",  # hard segment (.env)
        "block",  # config file without UI -> fail-closed
        "block",  # unlisted path without UI -> fail-closed
    ]


def test_path_guard_confirm_files_with_ui(tmp_path: Path) -> None:
    home = tmp_path / "home"
    verdicts = _decisions(tmp_path, home, has_ui=True)
    assert verdicts[7] == "confirm"  # settings.json
    assert verdicts[8] == "confirm"  # unlisted path, UI available


def test_path_guard_missing_export_is_not_silently_accepted() -> None:
    # Guard against the extension losing its pure decision entry point.
    text = PATH_GUARD.read_text(encoding="utf-8")
    assert "export function decidePath" in text
