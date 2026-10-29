"""Tests for project_load."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from project_load import (  # noqa: E402
    ProjectConfigError,
    filter_skills,
    handoff_for_phase,
    load_project,
    validate_project,
)


class TestProjectLoad(unittest.TestCase):
    def test_validate_ok(self):
        validate_project({"profile": "P1", "phases": ["DEFINE", "STATUS"], "skills": {}})

    def test_validate_bad_profile(self):
        with self.assertRaises(ProjectConfigError):
            validate_project({"profile": "PX"})

    def test_filter_skills(self):
        catalog = ["plan-continue", "role-back", "web-owasp"]
        self.assertEqual(
            filter_skills(catalog, {"skills": {"disabled": ["web-owasp"]}}),
            ["plan-continue", "role-back"],
        )
        self.assertEqual(
            filter_skills(catalog, {"skills": {"enabled": ["role-back"]}}),
            ["role-back"],
        )
        self.assertEqual(
            filter_skills(catalog, {"skills": {"enabled": []}}),
            [],
        )
        self.assertEqual(
            filter_skills(catalog, {"skills": {}}),
            catalog,
        )
        self.assertEqual(
            filter_skills(catalog, {"skills": {"enabled": None}}),
            catalog,
        )

    def test_handoff(self):
        p = {"handoffs": {"define": "plan-specification"}}
        self.assertEqual(handoff_for_phase(p, "DEFINE"), "plan-specification")

    def test_default_handoffs(self):
        self.assertEqual(handoff_for_phase({}, "VALIDATE"), "plan-validators")
        self.assertEqual(handoff_for_phase({}, "INTEGRATE"), "project-publish")

    def test_integrate_handoffs(self):
        self.assertEqual(
            handoff_for_phase({"handoffs": {"integrate_publish": "project-publish"}}, "INTEGRATE"),
            "project-publish",
        )
        self.assertEqual(
            handoff_for_phase({"handoffs": {"integrate_hooks": "project-publish"}}, "INTEGRATE"),
            "project-publish",
        )

    def test_load_from_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            aw = Path(tmp) / ".autoworkspace"
            aw.mkdir()
            (aw / "project.yaml").write_text(
                "schema_version: 1\nname: t\nprofile: P0\n",
                encoding="utf-8",
            )
            data = load_project(tmp)
            self.assertEqual(data["profile"], "P0")


if __name__ == "__main__":
    unittest.main()
