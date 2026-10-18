"""Tests for status_bump."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TOOLS))

from execution.evidence import store_result  # noqa: E402
from execution.ops import OpResult  # noqa: E402
from status_bump import advance_status, load_status  # noqa: E402


def _ok_run(repo: Path, op: str = "validate_snapshot") -> str:
    return store_result(
        repo,
        OpResult(
            operation_id=op,
            outcome="succeeded",
            returncode=0,
            duration_ms=1,
            detail="",
            effect="read",
            run_id=f"{op}:test:{id(repo)}",
            plan_digest="abc",
        ),
    )


class TestStatusBump(unittest.TestCase):
    def test_refuse_without_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".autoworkspace").mkdir()
            with self.assertRaises(ValueError):
                advance_status(root, phase="DEFINE", skill="plan-specification")

    def test_refuse_evidence_ok_without_run_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".autoworkspace").mkdir()
            with self.assertRaises(ValueError):
                advance_status(
                    root, phase="DEFINE", skill="plan-specification", evidence_ok=True
                )

    def test_define_to_integrate_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".autoworkspace").mkdir()
            rid = _ok_run(root)
            advance_status(
                root, phase="DEFINE", skill="plan-specification", evidence_ok=True, run_id=rid
            )
            rid2 = _ok_run(root, "op2")
            with self.assertRaises(ValueError) as ctx:
                advance_status(
                    root,
                    phase="INTEGRATE",
                    skill="project-publish",
                    evidence_ok=True,
                    run_id=rid2,
                )
            self.assertIn("invalid phase jump", str(ctx.exception))

    def test_advance_state_revision_without_product_semver(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".autoworkspace").mkdir()
            rid = _ok_run(root)
            s1 = advance_status(
                root,
                phase="DEFINE",
                skill="plan-specification",
                evidence_ok=True,
                run_id=rid,
            )
            self.assertEqual(s1["advance"], 1)
            self.assertEqual(s1["state_revision"], 1)
            self.assertEqual(s1["version"], "0.1.0")
            rid2 = _ok_run(root, "op2")
            s2 = advance_status(
                root,
                phase="SCHEMAS",
                skill="plan-specification",
                evidence_ok=True,
                run_id=rid2,
                bump_product_version=True,
            )
            self.assertEqual(s2["version"], "0.1.1")
            loaded = load_status(root)
            self.assertEqual(loaded["advance"], 2)
            self.assertEqual(len(loaded["history"]), 2)

    def test_awaiting_agent_without_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".autoworkspace").mkdir()
            data = advance_status(
                root, phase="IMPLEMENT", evidence_ok=False, allow_awaiting=True
            )
            self.assertTrue(data.get("awaiting_agent"))
            self.assertEqual(data.get("phase", "DEFINE"), "DEFINE")  # not completed


if __name__ == "__main__":
    unittest.main()
