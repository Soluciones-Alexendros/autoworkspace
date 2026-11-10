"""Harness report aggregation and static installation checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness.base import Check, build_report, report_exit_code  # noqa: E402
from harness.cursor_install import install_full  # noqa: E402
from harness.doctor import (  # noqa: E402
    cursor_full_check,
    installer_version_check,
    skill_link_check,
    version_coherence_checks,
)


def _schema() -> dict[str, Any]:
    data = json.loads(
        (ROOT / "tools" / "contracts" / "schemas" / "harness-report.schema.json").read_text(encoding="utf-8")
    )
    assert isinstance(data, dict)
    return data


def test_valid_report_matches_schema() -> None:
    report = build_report("pi", [Check("native", "B", "pass", "loaded")], package_version="1.2.3")
    jsonschema.validate(report, _schema())
    assert report["outcome"] == "pass"
    assert report_exit_code(report) == 0


def test_failed_required_check_blocks_pass() -> None:
    report = build_report("cursor", [Check("plugin", "A", "fail", "missing")])
    assert report["outcome"] == "fail"
    assert report_exit_code(report) == 1


def test_required_not_run_is_never_pass() -> None:
    report = build_report("cursor", [Check("native", "C", "not_run", "agent unavailable")])
    assert report["outcome"] == "not_run"
    assert report_exit_code(report) == 3  # noqa: PLR2004  # not_run exit code


def test_optional_not_run_does_not_hide_required_pass() -> None:
    report = build_report(
        "pi",
        [
            Check("native", "B", "pass", "loaded"),
            Check("optional-ui", "C", "not_run", "not applicable", required=False),
        ],
    )
    assert report["outcome"] == "pass"


def _versioned_repo(root: Path, version: str = "1.2.3") -> None:
    (root / "skills" / "fixture-skill").mkdir(parents=True)
    (root / "skills" / "fixture-skill" / "SKILL.md").write_text("---\nname: fixture-skill\n---\n")
    (root / ".cursor-plugin").mkdir()
    (root / ".cursor-plugin" / "plugin.json").write_text(json.dumps({"version": version}))
    (root / "package.json").write_text(json.dumps({"version": version}))
    (root / "scripts" / "lib").mkdir(parents=True)
    (root / "scripts" / "lib" / "link-skills.sh").write_text(f'VERSION="{version}"\n')


def test_version_drift_is_detected(tmp_path: Path) -> None:
    _versioned_repo(tmp_path)
    checks = version_coherence_checks(tmp_path, "1.2.3")
    assert all(check.outcome == "pass" for check in checks)
    (tmp_path / ".cursor-plugin" / "plugin.json").write_text(json.dumps({"version": "1.2.2"}))
    checks = version_coherence_checks(tmp_path, "1.2.3")
    assert any(check.outcome == "fail" and "cursor-plugin" in check.check_id for check in checks)


def _installer(tmp_path: Path, assignment: str) -> None:
    path = tmp_path / "scripts" / "lib" / "link-skills.sh"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(assignment + "\n", encoding="utf-8")


def test_installer_version_accepts_package_json_derivation(tmp_path: Path) -> None:
    derived = 'VERSION="$(python3 -c \'import json; print(json.load(open("$ROOT/package.json"))["version"])\'")'
    _installer(tmp_path, derived)
    check = installer_version_check(tmp_path, "1.2.3")
    assert check.outcome == "pass", check.detail
    assert "derived" in check.detail


def test_installer_version_flags_stale_literal(tmp_path: Path) -> None:
    _installer(tmp_path, 'VERSION="1.2.2"')
    check = installer_version_check(tmp_path, "1.2.3")
    assert check.outcome == "fail"
    assert "1.2.2" in check.detail


def test_installer_version_flags_unrecognized_assignment(tmp_path: Path) -> None:
    _installer(tmp_path, 'VERSION="$(cat VERSION.txt)"')
    check = installer_version_check(tmp_path, "1.2.3")
    assert check.outcome == "fail"
    assert "neither literal" in check.detail


def test_cursor_full_check_accepts_project_and_user_scope(tmp_path: Path) -> None:
    project = tmp_path / "project"
    install_full(ROOT, project)
    assert cursor_full_check(project).outcome == "pass"
    user_home = tmp_path / "home"
    install_full(ROOT, user_home / ".cursor", user_scope=True)
    check = cursor_full_check(user_home)
    assert check.outcome == "pass", check.detail
    assert "user scope" in check.detail


def test_cursor_full_check_rejects_missing_generated_hooks(tmp_path: Path) -> None:
    user_home = tmp_path / "home"
    install_full(ROOT, user_home / ".cursor", user_scope=True)
    (user_home / ".cursor" / "hooks.json").unlink()
    assert cursor_full_check(user_home).outcome == "fail"


def test_real_checkout_version_coherence_passes() -> None:
    """Regression: the shipped installer must satisfy the doctor that verifies it."""
    checks = version_coherence_checks(ROOT, None)
    assert [check.outcome for check in checks] == ["pass"] * 3, [check.detail for check in checks]


def test_skill_links_must_be_absolute_and_resolve_to_catalog(tmp_path: Path) -> None:
    _versioned_repo(tmp_path)
    destination = tmp_path / ".pi" / "skills"
    destination.mkdir(parents=True)
    (destination / "fixture-skill").symlink_to(tmp_path / "skills" / "fixture-skill")
    check = skill_link_check(tmp_path, "pi")
    assert check.outcome == "pass"
    (destination / "fixture-skill").unlink()
    (destination / "fixture-skill").symlink_to("relative-target")
    check = skill_link_check(tmp_path, "pi")
    assert check.outcome == "fail"
