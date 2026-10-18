"""Adversarial regression suite for verifiable closure (A01–A48 subset)."""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from execution.approval import (  # noqa: E402
    ApprovalDecision,
    ApprovalProvider,
    ApprovalRequest,
    DenyProvider,
    plan_digest,
)
from execution.evidence import (  # noqa: E402
    content_manifest,
    load_evidence,
    store_result,
    work_digest,
)
from execution.ops import OpResult, run_operation, run_registered  # noqa: E402
from execution.preflight import preflight_contract  # noqa: E402
from execution.registry import register_handler  # noqa: E402

sys.path.insert(0, str(ROOT / "tools" / "workspace-router"))
from status_bump import advance_status  # noqa: E402


class AllowProvider(ApprovalProvider):
    def decide(self, request: ApprovalRequest) -> ApprovalDecision:
        return ApprovalDecision(True, "test allow", "test", request.plan_digest)


# --- A01–A03: free-form / reserved ---


def test_a01_free_form_read_argv_rejected(tmp_path):
    sentinel = tmp_path / "sentinel.txt"
    r = run_operation(
        operation_id="evil_read",
        argv=[sys.executable, "-c", f"open({str(sentinel)!r},'w').write('x')"],
        effect="read",
        require_approval=False,
    )
    assert r.outcome == "blocked"
    assert "free-form" in r.detail
    assert not sentinel.exists()


def test_a02_reserved_params_rejected(monkeypatch):
    monkeypatch.setattr("execution.ops.provider_from_env", lambda: AllowProvider())
    register_handler("clean_temp", lambda p: 0)
    r = run_registered(
        "clean_temp",
        {"snapshot_id": "s", "effect": "read", "argv": ["true"]},
        target="/t",
    )
    assert r.outcome == "blocked"
    assert "reserved" in r.detail


def test_a03_registered_read_ok(monkeypatch):
    monkeypatch.setattr("execution.ops.provider_from_env", lambda: AllowProvider())
    register_handler("validate_snapshot", lambda p: 0)
    r = run_registered("validate_snapshot", {"snapshot_id": "s"}, target="/t")
    assert r.outcome == "succeeded"
    assert r.run_id  # UUID


# --- A04–A07: plan binding ---


def test_a04_param_change_invalidates(monkeypatch):
    fixed = {"d": ""}

    class P(ApprovalProvider):
        def decide(self, request: ApprovalRequest) -> ApprovalDecision:
            if not fixed["d"]:
                fixed["d"] = request.plan_digest
                return ApprovalDecision(True, "ok", "t", request.plan_digest)
            return ApprovalDecision(True, "stale", "t", fixed["d"])

    monkeypatch.setattr("execution.ops.provider_from_env", lambda: P())
    register_handler("clean_temp", lambda p: 0)
    assert run_registered("clean_temp", {"snapshot_id": "a"}, target="/t").outcome == "succeeded"
    assert run_registered("clean_temp", {"snapshot_id": "b"}, target="/t").outcome == "blocked"


def test_a06_deny_default(monkeypatch):
    monkeypatch.setattr("execution.ops.provider_from_env", lambda: DenyProvider())
    invoked = []
    register_handler("clean_journal", lambda p: invoked.append(1) or 0)
    r = run_registered("clean_journal", {"snapshot_id": "s"}, target="/")
    assert r.outcome == "blocked"
    assert invoked == []


def test_a07_handler_receives_plan_params(monkeypatch):
    monkeypatch.setattr("execution.ops.provider_from_env", lambda: AllowProvider())
    seen = []

    def handler(params):
        seen.append(dict(params))
        return 0

    register_handler("clean_temp", handler)
    r = run_registered("clean_temp", {"snapshot_id": "snap-x", "keep_versions": 3}, target="/host")
    assert r.outcome == "succeeded"
    assert seen[0]["snapshot_id"] == "snap-x"
    assert seen[0]["keep_versions"] == 3


def test_none_handler_not_success(monkeypatch):
    monkeypatch.setattr("execution.ops.provider_from_env", lambda: AllowProvider())
    register_handler("clean_temp", lambda p: None)
    r = run_registered("clean_temp", {"snapshot_id": "s"}, target="/t")
    assert r.outcome == "blocked"
    assert "None" in r.detail


# --- A16–A19: content digest ---


def test_a16_bytes_change_same_size_mtime(tmp_path):
    f = tmp_path / "a.txt"
    f.write_bytes(b"AAAA")
    d1 = work_digest(tmp_path)
    # Same size, force same mtime
    os.utime(f, (1_000_000, 1_000_000))
    f.write_bytes(b"BBBB")
    os.utime(f, (1_000_000, 1_000_000))
    d2 = work_digest(tmp_path)
    assert d1 != d2


def test_a17_touch_stable(tmp_path):
    f = tmp_path / "a.txt"
    f.write_bytes(b"same")
    d1 = work_digest(tmp_path)
    time.sleep(0.01)
    os.utime(f, None)
    d2 = work_digest(tmp_path)
    assert d1 == d2


def test_a18_new_file_changes(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    d1 = work_digest(tmp_path)
    (tmp_path / "b.txt").write_text("y")
    d2 = work_digest(tmp_path)
    assert d1 != d2


def test_a19_evidence_excluded(tmp_path):
    (tmp_path / "code.py").write_text("print(1)")
    d1 = work_digest(tmp_path)
    ed = tmp_path / ".autoworkspace" / "evidence"
    ed.mkdir(parents=True)
    (ed / "x.json").write_text("{}")
    (tmp_path / ".autoworkspace" / "status.yaml").write_text("phase: DEFINE\n")
    d2 = work_digest(tmp_path)
    assert d1 == d2


# --- A20–A27: evidence store / stale / phase ---


def _ok_result(op="local_gates", run_id=None):
    import uuid

    return OpResult(
        operation_id=op,
        outcome="succeeded",
        returncode=0,
        duration_ms=1,
        detail="",
        effect="write-workspace",
        run_id=run_id or str(uuid.uuid4()),
        plan_digest="pd",
    )


def test_a20_run_id_traversal_rejected(tmp_path):
    (tmp_path / ".autoworkspace").mkdir()
    with pytest.raises(ValueError, match="UUID|traversal|run_id"):
        store_result(
            tmp_path,
            OpResult("local_gates", "succeeded", 0, 1, "", "read", run_id="../escape"),
        )


def test_a21_uuid_unique(tmp_path):
    (tmp_path / "f.txt").write_text("x")
    (tmp_path / ".autoworkspace").mkdir()
    r1 = store_result(tmp_path, _ok_result(), phase="VALIDATE")
    r2 = store_result(tmp_path, _ok_result(), phase="VALIDATE")
    assert r1 != r2


def test_a22_failed_action_not_succeeded(tmp_path):
    (tmp_path / ".autoworkspace").mkdir()
    with pytest.raises(ValueError):
        store_result(
            tmp_path,
            OpResult(
                "local_gates",
                "succeeded",
                1,
                1,
                "ACTION_FAILED:x",
                "read",
                run_id=__import__("uuid").uuid4().hex
                if False
                else str(__import__("uuid").uuid4()),
            ),
        )


def test_a23_artifact_content_mismatch(tmp_path):
    art = tmp_path / "out.bin"
    art.write_bytes(b"payload")
    (tmp_path / ".autoworkspace").mkdir()
    with pytest.raises(ValueError, match="mismatch|artifact"):
        store_result(
            tmp_path,
            _ok_result(),
            artifacts=[{"path": "out.bin", "sha256": "0" * 64}],
            phase="VALIDATE",
        )


def test_a24_stale_content_blocks_complete(tmp_path):
    code = tmp_path / "app.py"
    code.write_text("v1")
    (tmp_path / ".autoworkspace").mkdir()
    rid = store_result(tmp_path, _ok_result("local_gates"), phase="VALIDATE", skill="plan-validators")
    code.write_text("v2")
    with pytest.raises(ValueError, match="stale"):
        advance_status(
            tmp_path,
            phase="VALIDATE",
            skill="plan-validators",
            evidence_ok=True,
            run_id=rid,
        )


def test_a25_admin_only_ok(tmp_path):
    code = tmp_path / "app.py"
    code.write_text("stable")
    (tmp_path / ".autoworkspace").mkdir()
    rid = store_result(tmp_path, _ok_result("local_gates"), phase="VALIDATE")
    (tmp_path / ".autoworkspace" / "status.yaml").write_text("phase: DEFINE\n")
    data = load_evidence(tmp_path, rid, revalidate_content=True, expected_phase="VALIDATE")
    assert data["outcome"] == "succeeded"


def test_a26_validate_snapshot_cannot_complete_define(tmp_path):
    (tmp_path / "x").write_text("1")
    (tmp_path / ".autoworkspace").mkdir()
    rid = store_result(
        tmp_path,
        _ok_result("validate_snapshot"),
        phase="DEFINE",
        skill="plan-specification",
    )
    with pytest.raises(ValueError, match="operation|phase"):
        advance_status(
            tmp_path,
            phase="DEFINE",
            skill="plan-specification",
            evidence_ok=True,
            run_id=rid,
        )


def test_a27_wrong_target_rejected(tmp_path):
    (tmp_path / "x").write_text("1")
    (tmp_path / ".autoworkspace").mkdir()
    rid = store_result(
        tmp_path,
        _ok_result("local_gates"),
        phase="VALIDATE",
        target="/a",
    )
    with pytest.raises(ValueError, match="target"):
        load_evidence(tmp_path, rid, expected_target="/b", revalidate_content=True)


# --- A28–A32: state transaction / transitions / idempotency ---


def test_a28_concurrent_writers(tmp_path):
    (tmp_path / "c").write_text("z")
    (tmp_path / ".autoworkspace").mkdir()
    errors = []
    results = []

    def worker(i):
        try:
            rid = store_result(tmp_path, _ok_result("local_gates"), phase="DEFINE")
            # First writer advances DEFINE; second may be idempotent same phase or conflict
            s = advance_status(
                tmp_path,
                phase="DEFINE",
                skill="plan-specification",
                evidence_ok=True,
                run_id=rid,
            )
            results.append(s.get("state_revision"))
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))

    # Sequential unique run_ids under lock — both should serialize without lost update
    rids = [
        store_result(tmp_path, _ok_result("plan_specification"), phase="DEFINE")
        for _ in range(2)
    ]
    barrier = threading.Barrier(2)

    def w(rid):
        barrier.wait()
        try:
            s = advance_status(
                tmp_path, phase="DEFINE", skill="", evidence_ok=True, run_id=rid
            )
            results.append(int(s.get("state_revision") or 0))
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))

    t1 = threading.Thread(target=w, args=(rids[0],))
    t2 = threading.Thread(target=w, args=(rids[1],))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert not errors, errors
    assert sorted(results) == [1, 2]


def test_a30_status_to_define_rejected(tmp_path):
    (tmp_path / "c").write_text("z")
    aw = tmp_path / ".autoworkspace"
    aw.mkdir()
    # Seed STATUS phase
    import yaml

    (aw / "status.yaml").write_text(
        yaml.safe_dump(
            {
                "phase": "STATUS",
                "state_revision": 5,
                "advance": 5,
                "version": "0.1.0",
                "history": [],
                "completed_run_ids": [],
            }
        )
    )
    rid = store_result(tmp_path, _ok_result("plan_specification"), phase="DEFINE")
    with pytest.raises(ValueError, match="regress|restart|invalid"):
        advance_status(tmp_path, phase="DEFINE", evidence_ok=True, run_id=rid)


def test_a32_idempotent_complete(tmp_path):
    (tmp_path / "c").write_text("z")
    (tmp_path / ".autoworkspace").mkdir()
    rid = store_result(tmp_path, _ok_result("plan_specification"), phase="DEFINE")
    s1 = advance_status(tmp_path, phase="DEFINE", evidence_ok=True, run_id=rid)
    s2 = advance_status(tmp_path, phase="DEFINE", evidence_ok=True, run_id=rid)
    assert s1["state_revision"] == 1
    assert s2["state_revision"] == 1
    assert s2.get("_idempotent_replay") is True


# --- A39–A40: preflight ---


def test_a40_network_hard_blocks():
    r = preflight_contract(
        {
            "skill": "local-proton",
            "distribution": "workspace-required",
            "system_requirements": {"binaries": [], "network": True},
        },
        cwd=ROOT,
        allow_network=False,
    )
    assert r.ok is False
    assert any("network" in x for x in r.blocked_reasons)


def test_digest_plan_includes_handler():
    a = plan_digest("op", "t", {}, ["read"], handler_id="h1")
    b = plan_digest("op", "t", {}, ["read"], handler_id="h2")
    assert a != b


def test_content_manifest_schema(tmp_path):
    (tmp_path / "f").write_bytes(b"hi")
    m = content_manifest(tmp_path)
    assert m["schema_version"] == 1
    assert "f" in m["entries"]
    assert len(m["digest"]) == 64


# --- V02 / D2: effective plan params (not globals alone) ---


def test_v02_dispatch_plan_includes_effective_params(monkeypatch):
    """Approved plan must include keep_versions/journal/pkg_mgr used by cleaners."""
    sys.path.insert(0, str(ROOT / "skills" / "local-maintenance" / "scripts"))
    import clean_routine as cr  # noqa: WPS433

    monkeypatch.setattr(cr, "SNAPSHOT_ID", "snap-v02")
    monkeypatch.setattr(cr, "PKG_MGR", "apt")
    monkeypatch.setattr(cr, "KEEP_VERSIONS", 5)
    monkeypatch.setattr(cr, "JOURNAL_VACUUM_TIME", "3d")
    monkeypatch.setattr(cr, "JOURNAL_VACUUM_SIZE", "100M")
    monkeypatch.setattr(cr, "DRY_RUN", False)
    monkeypatch.setattr(cr, "WITH_FIRMWARE", False)

    captured = {}

    def fake_registered(op, params, target="."):
        captured["params"] = dict(params)
        from execution.ops import OpResult

        return OpResult(op, "succeeded", 0, 1, "", "mutate-host", run_id="x", plan_digest="d")

    monkeypatch.setattr("execution.ops.run_registered", fake_registered)
    # ensure import path for dispatch
    monkeypatch.setattr(cr, "hostname", lambda: "testhost")
    rc = cr.dispatch_operation("clean_journal")
    assert rc == 0
    p = captured["params"]
    assert p.get("snapshot_id") == "snap-v02"
    assert p.get("pkg_mgr") == "apt"
    assert p.get("keep_versions") == 5
    assert p.get("journal_time") == "3d"
    assert p.get("journal_size") == "100M"


def test_v02_handler_uses_plan_params_not_stale_globals(monkeypatch):
    """After approval, handler must apply keep_versions from params even if global differs."""
    sys.path.insert(0, str(ROOT / "skills" / "local-maintenance" / "scripts"))
    import clean_routine as cr  # noqa: WPS433

    monkeypatch.setattr(cr, "KEEP_VERSIONS", 99)  # stale global
    monkeypatch.setattr(cr, "PKG_MGR", "wrong")
    seen = {}

    def spy_run_capture(cmd, timeout=10):
        seen["cmd"] = cmd
        return 0, ""

    monkeypatch.setattr(cr, "run_capture", spy_run_capture)
    monkeypatch.setattr(cr, "run", lambda *a, **k: "1M")
    monkeypatch.setattr(cr, "log_info", lambda *a, **k: None)
    monkeypatch.setattr(cr, "log_warn", lambda *a, **k: None)
    monkeypatch.setattr(cr, "log_success", lambda *a, **k: None)

    cr._register_handlers()
    from execution.registry import get_handler

    handler = get_handler("clean_package_cache")
    assert handler is not None
    rc = handler(
        {
            "snapshot_id": "s",
            "pkg_mgr": "pacman",
            "keep_versions": 2,
            "journal_time": "7d",
            "journal_size": "500M",
        }
    )
    assert rc == 0
    assert "-k 2" in seen.get("cmd", "")
    assert "-k 99" not in seen.get("cmd", "")


def test_a39_standalone_missing_shared_deps(tmp_path):
    skill = tmp_path / "local-maintenance"
    skill.mkdir()
    (skill / "SKILL.md").write_text("---\nname: local-maintenance\n---\n# x\n")
    r = preflight_contract(
        {
            "skill": "local-maintenance",
            "distribution": "standalone",
            "shared_dependencies": ["tools/execution"],
            "system_requirements": {"binaries": [], "network": False},
        },
        cwd=tmp_path,
        skill_root=skill,
    )
    assert r.ok is False
    assert any("shared_dependencies" in x for x in r.blocked_reasons)


def test_a39_standalone_with_vendor_ok(tmp_path):
    skill = tmp_path / "local-maintenance"
    skill.mkdir()
    (skill / "SKILL.md").write_text("---\nname: local-maintenance\n---\n# x\n")
    vendor = skill / "vendor" / "execution"
    vendor.mkdir(parents=True)
    (vendor / "__init__.py").write_text("# packaged\n")
    r = preflight_contract(
        {
            "skill": "local-maintenance",
            "distribution": "standalone",
            "shared_dependencies": ["tools/execution"],
            "system_requirements": {"binaries": [], "network": False},
        },
        cwd=tmp_path,
        skill_root=skill,
    )
    assert r.ok is True
