"""Product closure V01–V12: strict evidence, phase semantics, content confinement."""

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from execution.evidence import (  # noqa: E402
    content_manifest,
    load_evidence,
    store_result,
    work_digest,
)
from execution.ops import OpResult  # noqa: E402

DIG = "b" * 64


def _ok(op="local_gates", **kw):
    return OpResult(
        operation_id=op,
        outcome="succeeded",
        returncode=0,
        duration_ms=1,
        detail="",
        effect="write-workspace",
        run_id=kw.pop("run_id", str(uuid.uuid4())),
        plan_digest=kw.pop("plan_digest", DIG),
    )


def _write_art(tmp: Path, name="artifact.txt", body="ok") -> Path:
    p = tmp / name
    p.write_text(body)
    return p


# --- V01–V04 ---


def test_v01_succeeded_only_rejected(tmp_path):
    (tmp_path / ".autoworkspace").mkdir()
    rid = str(uuid.uuid4())
    ed = tmp_path / ".autoworkspace" / "evidence"
    ed.mkdir()
    # Hand-craft minimal JSON (succeeded + uuid filename, no bindings)
    (ed / f"{rid}.json").write_text(json.dumps({"outcome": "succeeded", "run_id": rid, "schema_version": 1}))
    with pytest.raises(ValueError, match="missing required|schema|plan_digest|phase"):
        load_evidence(tmp_path, rid, revalidate_content=False)


def test_v02_omit_each_binding(tmp_path):
    (tmp_path / ".autoworkspace").mkdir()
    art = _write_art(tmp_path)
    base = dict(
        artifacts=[str(art)],
        phase="VALIDATE",
        skill="project-publish",
        target="/t",
        verifications=[{"kind": "gate_result", "ok": True}],
    )
    # Missing plan_digest on result
    with pytest.raises(ValueError, match="plan_digest"):
        store_result(
            tmp_path,
            OpResult("local_gates", "succeeded", 0, 1, "", "read", plan_digest=""),
            **base,
        )
    for drop in ("phase", "skill", "target"):
        kw = dict(base)
        kw[drop] = ""
        with pytest.raises(ValueError, match=drop):
            store_result(tmp_path, _ok(), **kw)


def test_v03_bad_types_and_legacy(tmp_path):
    (tmp_path / ".autoworkspace").mkdir()
    rid = str(uuid.uuid4())
    ed = tmp_path / ".autoworkspace" / "evidence"
    ed.mkdir()
    payload = {
        "schema_version": 1,
        "run_id": rid,
        "operation_id": "local_gates",
        "outcome": "succeeded",
        "plan_digest": DIG,
        "input_digest": DIG,
        "output_digest": DIG,
        "phase": "VALIDATE",
        "skill": "project-publish",
        "target": "/t",
        "verifications": [{"kind": "gate_result", "ok": True}],
        "artifacts": [{"path": "a.txt", "sha256": DIG}],
    }
    # Wrong schema version
    bad = dict(payload, schema_version=99)
    (ed / f"{rid}.json").write_text(json.dumps(bad))
    with pytest.raises(ValueError, match="schema_version"):
        load_evidence(tmp_path, rid, revalidate_content=False, for_complete=True)
    # Empty digests do not fail-open
    rid2 = str(uuid.uuid4())
    bad2 = dict(payload, run_id=rid2, output_digest="")
    (ed / f"{rid2}.json").write_text(json.dumps(bad2))
    with pytest.raises(ValueError, match="output_digest|missing"):
        load_evidence(tmp_path, rid2, revalidate_content=False, for_complete=True)


def test_v04_valid_accepted(tmp_path):
    (tmp_path / "code.py").write_text("x")
    (tmp_path / ".autoworkspace").mkdir()
    art = _write_art(tmp_path)
    digest = work_digest(tmp_path)
    rid = store_result(
        tmp_path,
        _ok(),
        artifacts=[str(art)],
        phase="VALIDATE",
        skill="project-publish",
        target="/t",
        input_digest=digest,
        output_digest=digest,
        verifications=[{"kind": "gate_result", "ok": True}],
        require_complete_fields=True,
    )
    data = load_evidence(
        tmp_path, rid, expected_phase="VALIDATE", expected_skill="project-publish", expected_target="/t"
    )
    assert data["run_id"] == rid


# --- V05–V07 ---


def test_v05_local_gates_cannot_complete_define(tmp_path):
    (tmp_path / "x").write_text("1")
    (tmp_path / ".autoworkspace").mkdir()
    art = _write_art(tmp_path)
    rid = store_result(
        tmp_path,
        _ok("local_gates"),
        artifacts=[str(art)],
        phase="DEFINE",
        skill="plan-specification",
        target="/t",
        verifications=[{"kind": "spec_deliverable", "ok": True}],
    )
    with pytest.raises(ValueError, match="cannot complete phase"):
        load_evidence(tmp_path, rid, expected_phase="DEFINE", for_complete=True)


def test_v06_prefix_and_wrong_phase_rejected(tmp_path):
    (tmp_path / "x").write_text("1")
    (tmp_path / ".autoworkspace").mkdir()
    art = _write_art(tmp_path)
    rid = store_result(
        tmp_path,
        _ok("local_gates_extra"),
        artifacts=[str(art)],
        phase="VALIDATE",
        skill="project-publish",
        target="/t",
        verifications=[{"kind": "gate_result", "ok": True}],
    )
    with pytest.raises(ValueError, match="cannot complete phase"):
        load_evidence(tmp_path, rid, expected_phase="VALIDATE")


def test_v07_missing_verification_rejected(tmp_path):
    (tmp_path / "x").write_text("1")
    (tmp_path / ".autoworkspace").mkdir()
    art = _write_art(tmp_path)
    rid = store_result(
        tmp_path,
        _ok(),
        artifacts=[str(art)],
        phase="VALIDATE",
        skill="project-publish",
        target="/t",
        verifications=[],  # store allows; complete rejects
    )
    with pytest.raises(ValueError, match="verifications"):
        load_evidence(tmp_path, rid, expected_phase="VALIDATE", for_complete=True)


# --- V08–V12 ---


def test_v08_bytes_change_digest_touch_stable(tmp_path):
    f = tmp_path / "a.bin"
    f.write_bytes(b"AAAA")
    d1 = work_digest(tmp_path)
    f.write_bytes(b"BBBB")  # same size
    d2 = work_digest(tmp_path)
    assert d1 != d2
    f.write_bytes(b"BBBB")
    d3 = work_digest(tmp_path)
    os.utime(f, None)  # touch
    d4 = work_digest(tmp_path)
    assert d3 == d4


def test_v09_dir_symlink_recorded(tmp_path):
    real = tmp_path / "realdir"
    real.mkdir()
    (real / "f").write_text("z")
    link = tmp_path / "linkdir"
    link.symlink_to(real)
    m = content_manifest(tmp_path)
    assert "linkdir" in m["entries"]
    assert m["entries"]["linkdir"].startswith("symlink:")


def test_v10_artifact_symlink_rejected(tmp_path):
    (tmp_path / ".autoworkspace").mkdir()
    real = tmp_path / "real.txt"
    real.write_text("p")
    link = tmp_path / "art_link"
    link.symlink_to(real)
    with pytest.raises(ValueError, match="symlink"):
        store_result(
            tmp_path,
            _ok(),
            artifacts=[str(link)],
            phase="VALIDATE",
            skill="project-publish",
            target="/t",
            verifications=[{"kind": "gate_result", "ok": True}],
        )


def test_v11_unreadable_file_errors(tmp_path):
    f = tmp_path / "secret.bin"
    f.write_bytes(b"x")
    f.chmod(0o000)
    try:
        with pytest.raises(ValueError, match="unreadable"):
            content_manifest(tmp_path)
    finally:
        f.chmod(0o600)


def test_v12_admin_change_stable_new_file_changes(tmp_path):
    (tmp_path / "code.py").write_text("stable")
    aw = tmp_path / ".autoworkspace"
    aw.mkdir()
    d1 = work_digest(tmp_path)
    (aw / "status.yaml").write_text("phase: DEFINE\n")
    d2 = work_digest(tmp_path)
    assert d1 == d2
    (tmp_path / "new.py").write_text("added")
    d3 = work_digest(tmp_path)
    assert d3 != d1
