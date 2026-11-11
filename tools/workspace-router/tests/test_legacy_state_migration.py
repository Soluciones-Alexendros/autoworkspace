"""D3/H2: ``.machineroom`` state with legacy ``.autoworkspace`` fallback."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
ROUTER = ROOT / "tools" / "workspace-router" / "run.py"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "workspace-router"))

from state_paths import (  # noqa: E402
    PROJECT_DIRNAME,
    StateDirError,
    excluded_prefixes,
    migrate_state,
    state_dir,
    state_file,
)


def test_constants_and_paths(tmp_path: Path) -> None:
    assert PROJECT_DIRNAME == ".machineroom"
    assert state_dir(tmp_path) == tmp_path / ".machineroom"
    assert state_file(tmp_path, "status.yaml") == tmp_path / ".machineroom" / "status.yaml"


def test_legacy_fallback_warns_once(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / ".autoworkspace").mkdir()
    first = state_dir(tmp_path)
    assert first == tmp_path / ".autoworkspace"
    captured = capsys.readouterr()
    assert "deprecation" in captured.err
    assert "9.0.0" in captured.err
    state_dir(tmp_path)
    assert capsys.readouterr().err == ""


def test_current_dir_wins_over_legacy(tmp_path: Path) -> None:
    (tmp_path / ".machineroom").mkdir()
    (tmp_path / ".autoworkspace").mkdir()
    assert state_dir(tmp_path) == tmp_path / ".machineroom"


def test_migrate_moves_state(tmp_path: Path) -> None:
    legacy = tmp_path / ".autoworkspace"
    (legacy / "evidence").mkdir(parents=True)
    (legacy / "status.yaml").write_text("phase: DEFINE\n", encoding="utf-8")

    result = migrate_state(tmp_path)

    assert result["migrated"] is True
    assert not legacy.exists()
    assert (tmp_path / ".machineroom" / "status.yaml").read_text(encoding="utf-8") == "phase: DEFINE\n"


def test_migrate_dry_run_writes_nothing(tmp_path: Path) -> None:
    legacy = tmp_path / ".autoworkspace"
    legacy.mkdir()
    result = migrate_state(tmp_path, dry_run=True)
    assert result["migrated"] is False
    assert legacy.is_dir()
    assert not (tmp_path / ".machineroom").exists()


def test_migrate_refuses_two_dirs(tmp_path: Path) -> None:
    (tmp_path / ".autoworkspace").mkdir()
    (tmp_path / ".machineroom").mkdir()
    with pytest.raises(StateDirError) as caught:
        migrate_state(tmp_path)
    assert caught.value.component == "state"
    assert "two state directories" in caught.value.detail


def test_excluded_prefixes_cover_both_names() -> None:
    prefixes = excluded_prefixes()
    assert ".machineroom/evidence/" in prefixes
    assert ".autoworkspace/evidence/" in prefixes
    assert len(prefixes) == 7 * 2


def test_router_reads_current_state(tmp_path: Path) -> None:
    state = tmp_path / ".machineroom"
    state.mkdir()
    (state / "project.yaml").write_text(
        "schema_version: 1\nname: demo\nprofile: P1\nphases: [DEFINE]\n", encoding="utf-8"
    )
    proc = subprocess.run(
        [sys.executable, str(ROUTER), "--repo", str(tmp_path), "--list", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(proc.stdout)["allowed_skills"]
    assert "deprecation" not in proc.stderr


def test_router_accepts_legacy_state_with_warning(tmp_path: Path) -> None:
    state = tmp_path / ".autoworkspace"
    state.mkdir()
    (state / "project.yaml").write_text(
        "schema_version: 1\nname: demo\nprofile: P1\nphases: [DEFINE]\n", encoding="utf-8"
    )
    proc = subprocess.run(
        [sys.executable, str(ROUTER), "--repo", str(tmp_path), "--list", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(proc.stdout)["allowed_skills"]
    assert "deprecation" in proc.stderr
