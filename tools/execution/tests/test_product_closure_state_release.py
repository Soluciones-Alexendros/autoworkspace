"""Product closure: state/idempotency (V26–V30) and release readiness (V44–V45)."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import uuid
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "workspace-router"))

from execution.evidence import store_result, work_digest  # noqa: E402
from execution.ops import OpResult  # noqa: E402
from status_bump import advance_status, resolve_awaiting_agent  # noqa: E402

DIG = "d" * 64
CUT = ROOT / "tools" / "version" / "cut_tag.py"


def _store(repo: Path, phase="DEFINE", op="plan_specification", **kw):
    art = repo / "artifact.txt"
    if not art.exists():
        art.write_text("ok")
    kind = {
        "DEFINE": "spec_deliverable",
        "VALIDATE": "gate_result",
    }.get(phase, "spec_deliverable")
    skill = kw.pop("skill", "plan-specification")
    target = kw.pop("target", "/fixture")
    digest = work_digest(repo)
    return store_result(
        repo,
        OpResult(op, "succeeded", 0, 1, "", "write-workspace", run_id=str(uuid.uuid4()), plan_digest=DIG),
        phase=phase,
        skill=skill,
        target=target,
        artifacts=[str(art)],
        verifications=[{"kind": kind, "ok": True}],
        input_digest=digest,
        output_digest=digest,
        **kw,
    )


def test_v26_concurrent_no_lost_update(tmp_path):
    (tmp_path / ".autoworkspace").mkdir()
    (tmp_path / "c").write_text("z")
    rids = [_store(tmp_path) for _ in range(2)]
    results, errors = [], []
    barrier = threading.Barrier(2)

    def w(rid):
        barrier.wait()
        try:
            s = advance_status(
                tmp_path,
                phase="DEFINE",
                skill="plan-specification",
                evidence_ok=True,
                run_id=rid,
                target="/fixture",
            )
            results.append(int(s["state_revision"]))
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))

    ts = [threading.Thread(target=w, args=(r,)) for r in rids]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert not errors, errors
    assert sorted(results) == [1, 2]


def test_v28_resolve_awaiting_public(tmp_path):
    (tmp_path / ".autoworkspace").mkdir()
    (tmp_path / "c").write_text("z")
    advance_status(tmp_path, phase="DEFINE", allow_awaiting=True, evidence_ok=False)
    st = yaml.safe_load((tmp_path / ".autoworkspace" / "status.yaml").read_text())
    assert st.get("awaiting_agent") is True
    rid = _store(tmp_path)
    resolved = resolve_awaiting_agent(
        tmp_path, run_id=rid, phase="DEFINE", skill="plan-specification", target="/fixture"
    )
    assert resolved.get("awaiting_agent") is False
    s = advance_status(
        tmp_path,
        phase="DEFINE",
        skill="plan-specification",
        evidence_ok=True,
        run_id=rid,
        target="/fixture",
    )
    assert s["state_revision"] == 1


def test_v29_receipt_survives_compaction(tmp_path):
    (tmp_path / ".autoworkspace").mkdir()
    (tmp_path / "c").write_text("z")
    # Seed >200 fake completions then replay original
    rid = _store(tmp_path)
    s = advance_status(
        tmp_path,
        phase="DEFINE",
        skill="plan-specification",
        evidence_ok=True,
        run_id=rid,
        target="/fixture",
    )
    assert s["state_revision"] == 1
    # Simulate compaction of completed_run_ids while receipt remains
    path = tmp_path / ".autoworkspace" / "status.yaml"
    data = yaml.safe_load(path.read_text())
    data["completed_run_ids"] = [str(uuid.uuid4()) for _ in range(200)]
    assert rid not in data["completed_run_ids"]
    assert f"DEFINE:{rid}" in (data.get("completion_receipts") or {})
    path.write_text(yaml.safe_dump(data))
    s2 = advance_status(
        tmp_path,
        phase="DEFINE",
        skill="plan-specification",
        evidence_ok=True,
        run_id=rid,
        target="/fixture",
    )
    assert s2.get("_idempotent_replay") is True
    assert s2["state_revision"] == 1


def _init_release_repo(tmp: Path, version: str, notes_section: str | None) -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=tmp, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp, check=True, capture_output=True)
    (tmp / "package.json").write_text(json.dumps({"version": version}))
    cl = "# Changelog\n\n"
    if notes_section is not None:
        cl += notes_section
    (tmp / "CHANGELOG.md").write_text(cl)
    subprocess.run(["git", "add", "."], cwd=tmp, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp, check=True, capture_output=True)
    return tmp


def test_v44_readiness_fails_missing_yanked(tmp_path):
    repo = _init_release_repo(tmp_path / "a", "9.9.9", None)
    r = subprocess.run(
        [sys.executable, str(CUT), "--root", str(repo), "--check-readiness"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 1
    assert "not_ready" in r.stdout or "fail" in r.stdout.lower()

    repo2 = _init_release_repo(
        tmp_path / "b",
        "9.9.8",
        "## [9.9.8] - 2026-01-01 [YANKED]\n\n- gone\n",
    )
    r2 = subprocess.run(
        [sys.executable, str(CUT), "--root", str(repo2), "--check-readiness"],
        capture_output=True,
        text=True,
    )
    assert r2.returncode == 1
    assert "yanked" in r2.stdout.lower() or "YANKED" in r2.stdout


def test_v45_readiness_ok_and_ordinary_skip(tmp_path):
    repo = _init_release_repo(
        tmp_path / "c",
        "9.9.7",
        "## [9.9.7] - 2026-01-02\n\n- ready notes\n",
    )
    r = subprocess.run(
        [sys.executable, str(CUT), "--root", str(repo), "--check-readiness"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    # Ordinary cut without notes → skip 0 (not published)
    empty = _init_release_repo(tmp_path / "d", "9.9.6", None)
    r2 = subprocess.run(
        [sys.executable, str(CUT), "--root", str(empty)],
        capture_output=True,
        text=True,
    )
    assert r2.returncode == 0
    assert "skip" in r2.stdout.lower()
    # Strict cut without notes → fail
    r3 = subprocess.run(
        [sys.executable, str(CUT), "--root", str(empty), "--strict-readiness"],
        capture_output=True,
        text=True,
    )
    assert r3.returncode == 1
