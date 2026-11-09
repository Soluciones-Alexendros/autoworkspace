"""Active-plan state migration and identity tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "workspace-router"))

from status_bump import (  # noqa: E402
    activate_plan,
    load_active_plan,
    load_status,
    migrate_status,
    status_path,
)

FIXTURE = ROOT / "scripts" / "tests" / "fixtures" / "plans" / "minimal.md"


def _legacy(root: Path) -> None:
    (root / ".autoworkspace").mkdir()
    status_path(root).write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "version": "0.1.0",
                "phase": "DEFINE",
                "history": [{"phase": "DEFINE", "note": "historical"}],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_legacy_load_is_pure_and_has_no_active_plan(tmp_path: Path) -> None:
    _legacy(tmp_path)
    before = status_path(tmp_path).read_bytes()
    data = load_status(tmp_path)
    assert data["schema_version"] == 2
    assert data["active_plan"] is None
    assert data["tasks"] == {}
    assert status_path(tmp_path).read_bytes() == before


def test_explicit_migration_preserves_history_and_is_idempotent(tmp_path: Path) -> None:
    _legacy(tmp_path)
    migrated = migrate_status(tmp_path)
    assert migrated["schema_version"] == 2
    assert migrated["history"][0]["note"] == "historical"
    first = status_path(tmp_path).read_bytes()
    again = migrate_status(tmp_path)
    assert again["active_plan"] is None
    assert status_path(tmp_path).read_bytes() == first


def test_unknown_status_schema_is_rejected(tmp_path: Path) -> None:
    _legacy(tmp_path)
    status_path(tmp_path).write_text("schema_version: 99\n", encoding="utf-8")
    with pytest.raises(ValueError, match="schema_version"):
        load_status(tmp_path)


def test_activate_plan_tracks_path_digest_and_pending_tasks(tmp_path: Path) -> None:
    _legacy(tmp_path)
    migrate_status(tmp_path)
    plan = tmp_path / "fixture.md"
    plan.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    state = activate_plan(tmp_path, plan)
    assert state["active_plan"]["plan_id"] == "fixture-plan-v1"
    assert state["active_plan"]["path"] == "fixture.md"
    assert state["plan_digest"] == state["active_plan"]["digest"]
    assert state["tasks"]["fixture-read"]["state"] == "pending"
    assert load_active_plan(tmp_path).plan_id == "fixture-plan-v1"

    plan.write_text(plan.read_text(encoding="utf-8").replace("fixture-read-observed", "changed"), encoding="utf-8")
    with pytest.raises(ValueError, match="digest"):
        load_active_plan(tmp_path)


def test_existing_plan_file_is_not_inferred_as_active(tmp_path: Path) -> None:
    _legacy(tmp_path)
    migrate_status(tmp_path)
    (tmp_path / "tasks").mkdir()
    (tmp_path / "tasks" / "plan.md").write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError, match="no active plan"):
        load_active_plan(tmp_path)
