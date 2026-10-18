"""Tests for status_bump."""
from __future__ import annotations

import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TOOLS))

from execution.evidence import store_result, work_digest  # noqa: E402
from execution.ops import OpResult  # noqa: E402
from status_bump import advance_status, load_status  # noqa: E402

DIG = "e" * 64


def _ok_run(repo: Path, op: str = "plan_specification", phase: str = "DEFINE") -> str:
    (repo / "keepalive.txt").write_text("x", encoding="utf-8")
    art = repo / "artifact.txt"
    art.write_text("ok")
    kind = {
        "DEFINE": "spec_deliverable",
        "SCHEMAS": "schema_deliverable",
        "IMPLEMENT": "implementation_deliverable",
        "VALIDATE": "gate_result",
        "INTEGRATE": "integrate_result",
        "STATUS": "status_result",
    }[phase]
    digest = work_digest(repo)
    return store_result(
        repo,
        OpResult(
            operation_id=op,
            outcome="succeeded",
            returncode=0,
            duration_ms=1,
            detail="",
            effect="write-workspace",
            run_id=str(uuid.uuid4()),
            plan_digest=DIG,
        ),
        phase=phase,
        skill="plan-specification",
        target="/fixture",
        artifacts=[str(art)],
        verifications=[{"kind": kind, "ok": True}],
        input_digest=digest,
        output_digest=digest,
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
                root,
                phase="DEFINE",
                skill="plan-specification",
                evidence_ok=True,
                run_id=rid,
                target="/fixture",
            )
            # Evidence claims INTEGRATE but current phase is DEFINE → jump rejected
            art = root / "artifact.txt"
            digest = work_digest(root)
            rid2 = store_result(
                root,
                OpResult(
                    operation_id="local_gates",
                    outcome="succeeded",
                    returncode=0,
                    duration_ms=1,
                    detail="",
                    effect="write-workspace",
                    run_id=str(uuid.uuid4()),
                    plan_digest=DIG,
                ),
                phase="INTEGRATE",
                skill="project-publish",
                target="/fixture",
                artifacts=[str(art)],
                verifications=[{"kind": "integrate_result", "ok": True}],
                input_digest=digest,
                output_digest=digest,
            )
            with self.assertRaises(ValueError) as ctx:
                advance_status(
                    root,
                    phase="INTEGRATE",
                    skill="project-publish",
                    evidence_ok=True,
                    run_id=rid2,
                    target="/fixture",
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
                target="/fixture",
            )
            self.assertEqual(s1["advance"], 1)
            self.assertEqual(s1["state_revision"], 1)
            self.assertEqual(s1["version"], "0.1.0")
            rid2 = _ok_run(root, "plan_specification", phase="SCHEMAS")
            s2 = advance_status(
                root,
                phase="SCHEMAS",
                skill="plan-specification",
                evidence_ok=True,
                run_id=rid2,
                bump_product_version=True,
                target="/fixture",
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

    def test_validate_snapshot_cannot_define(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".autoworkspace").mkdir()
            rid = _ok_run(root, op="validate_snapshot", phase="DEFINE")
            with self.assertRaises(ValueError):
                advance_status(
                    root,
                    phase="DEFINE",
                    skill="plan-specification",
                    evidence_ok=True,
                    run_id=rid,
                    target="/fixture",
                )


if __name__ == "__main__":
    unittest.main()
