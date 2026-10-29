"""Adversarial regression suite for verifiable closure (A01-A48 subset)."""

from __future__ import annotations

import os
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import pytest
import yaml

DEFAULT_KEEP_VERSIONS = 3
CUSTOM_KEEP_VERSIONS = 5
SHA256_HEX_LEN = 64

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
from execution.registry import get_handler, register_handler  # noqa: E402

sys.path.insert(0, str(ROOT / "tools" / "workspace-router"))

sys.path.insert(0, str(ROOT / "skills" / "local-maintenance" / "scripts"))

import clean_routine as cr  # noqa: E402  # requiere el sys.path de skills/local-maintenance/scripts
from status_bump import advance_status  # noqa: E402


class AllowProvider(ApprovalProvider):
    def decide(self, request: ApprovalRequest) -> ApprovalDecision:
        return ApprovalDecision(True, "test allow", "test", request.plan_digest)


# --- A01-A03: free-form / reserved ---


def test_a01_free_form_read_argv_rejected(tmp_path: Path) -> None:
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


def test_a02_reserved_params_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("execution.ops.provider_from_env", AllowProvider)
    register_handler("clean_temp", lambda p: 0)
    r = run_registered(
        "clean_temp",
        {"snapshot_id": "s", "effect": "read", "argv": ["true"]},
        target="/t",
    )
    assert r.outcome == "blocked"
    assert "reserved" in r.detail


def test_a03_registered_read_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("execution.ops.provider_from_env", AllowProvider)
    register_handler("validate_snapshot", lambda p: 0)
    r = run_registered("validate_snapshot", {"snapshot_id": "s"}, target="/t")
    assert r.outcome == "succeeded"
    assert r.run_id  # UUID


# --- A04-A07: plan binding ---


def test_a04_param_change_invalidates(monkeypatch: pytest.MonkeyPatch) -> None:
    fixed = {"d": ""}

    class P(ApprovalProvider):
        def decide(self, request: ApprovalRequest) -> ApprovalDecision:
            if not fixed["d"]:
                fixed["d"] = request.plan_digest
                return ApprovalDecision(True, "ok", "t", request.plan_digest)
            return ApprovalDecision(True, "stale", "t", fixed["d"])

    monkeypatch.setattr("execution.ops.provider_from_env", P)
    register_handler("clean_temp", lambda p: 0)
    assert run_registered("clean_temp", {"snapshot_id": "a"}, target="/t").outcome == "succeeded"
    assert run_registered("clean_temp", {"snapshot_id": "b"}, target="/t").outcome == "blocked"


def test_a06_deny_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("execution.ops.provider_from_env", DenyProvider)
    invoked: list[int] = []

    def _denied(_params: dict[str, Any]) -> int:
        invoked.append(1)
        return 0

    register_handler("clean_journal", _denied)
    r = run_registered("clean_journal", {"snapshot_id": "s"}, target="/")
    assert r.outcome == "blocked"
    assert invoked == []


def test_a07_handler_receives_plan_params(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("execution.ops.provider_from_env", AllowProvider)
    seen = []

    def handler(params: dict[str, Any]) -> int:
        seen.append(dict(params))
        return 0

    register_handler("clean_temp", handler)
    r = run_registered("clean_temp", {"snapshot_id": "snap-x", "keep_versions": 3}, target="/host")
    assert r.outcome == "succeeded"
    assert seen[0]["snapshot_id"] == "snap-x"
    assert seen[0]["keep_versions"] == DEFAULT_KEEP_VERSIONS


def test_none_handler_not_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("execution.ops.provider_from_env", AllowProvider)
    register_handler("clean_temp", lambda p: None)
    r = run_registered("clean_temp", {"snapshot_id": "s"}, target="/t")
    assert r.outcome == "blocked"
    assert "None" in r.detail


# --- A16-A19: content digest ---


def test_a16_bytes_change_same_size_mtime(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_bytes(b"AAAA")
    d1 = work_digest(tmp_path)
    # Same size, force same mtime
    os.utime(f, (1_000_000, 1_000_000))
    f.write_bytes(b"BBBB")
    os.utime(f, (1_000_000, 1_000_000))
    d2 = work_digest(tmp_path)
    assert d1 != d2


def test_a17_touch_stable(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_bytes(b"same")
    d1 = work_digest(tmp_path)
    time.sleep(0.01)
    os.utime(f, None)
    d2 = work_digest(tmp_path)
    assert d1 == d2


def test_a18_new_file_changes(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x")
    d1 = work_digest(tmp_path)
    (tmp_path / "b.txt").write_text("y")
    d2 = work_digest(tmp_path)
    assert d1 != d2


def test_a19_evidence_excluded(tmp_path: Path) -> None:
    (tmp_path / "code.py").write_text("print(1)")
    d1 = work_digest(tmp_path)
    ed = tmp_path / ".autoworkspace" / "evidence"
    ed.mkdir(parents=True)
    (ed / "x.json").write_text("{}")
    (tmp_path / ".autoworkspace" / "status.yaml").write_text("phase: DEFINE\n")
    d2 = work_digest(tmp_path)
    assert d1 == d2


# --- A20-A27: evidence store / stale / phase ---


_DIG = "a" * 64


def _ok_result(op: str = "local_gates", run_id: str | None = None) -> OpResult:
    return OpResult(
        operation_id=op,
        outcome="succeeded",
        returncode=0,
        duration_ms=1,
        detail="",
        effect="write-workspace",
        run_id=run_id or str(uuid.uuid4()),
        plan_digest=_DIG,
    )


def _phase_meta(phase: str, op: str = "local_gates") -> dict[str, Any]:
    """Bindings + verifications required for phase completion."""
    kind = {
        "DEFINE": "spec_deliverable",
        "SCHEMAS": "schema_deliverable",
        "IMPLEMENT": "implementation_deliverable",
        "VALIDATE": "gate_result",
        "INTEGRATE": "integrate_result",
        "STATUS": "status_result",
    }[phase]
    skill = {
        "DEFINE": "plan-specification",
        "SCHEMAS": "plan-specification",
        "IMPLEMENT": "role-back",
        "VALIDATE": "project-publish",
        "INTEGRATE": "project-publish",
        "STATUS": "plan-continue",
    }[phase]
    return {
        "phase": phase,
        "skill": skill,
        "target": "/fixture",
        "verifications": [{"kind": kind, "ok": True}],
    }


def _store_ok(tmp_path: Path, op: str = "local_gates", phase: str = "VALIDATE", **kwargs: Any) -> str:
    meta = _phase_meta(phase, op)
    meta.update(kwargs)
    art = tmp_path / "artifact.txt"
    if not art.exists():
        art.write_text("ok")
    return store_result(
        tmp_path,
        _ok_result(op),
        artifacts=[str(art)],
        **meta,
    )


def test_a20_run_id_traversal_rejected(tmp_path: Path) -> None:
    (tmp_path / ".autoworkspace").mkdir()
    with pytest.raises(ValueError, match=r"UUID|traversal|run_id"):
        store_result(
            tmp_path,
            OpResult(
                "local_gates",
                "succeeded",
                0,
                1,
                "",
                "read",
                run_id="../escape",
                plan_digest=_DIG,
            ),
            phase="VALIDATE",
            skill="project-publish",
            target="/t",
        )


def test_a21_uuid_unique(tmp_path: Path) -> None:
    (tmp_path / "f.txt").write_text("x")
    (tmp_path / ".autoworkspace").mkdir()
    r1 = _store_ok(tmp_path, phase="VALIDATE")
    r2 = _store_ok(tmp_path, phase="VALIDATE")
    assert r1 != r2


def test_a22_failed_action_not_succeeded(tmp_path: Path) -> None:
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
                run_id=str(__import__("uuid").uuid4()),
                plan_digest=_DIG,
            ),
            phase="VALIDATE",
            skill="project-publish",
            target="/t",
        )


def test_a23_artifact_content_mismatch(tmp_path: Path) -> None:
    art = tmp_path / "out.bin"
    art.write_bytes(b"payload")
    (tmp_path / ".autoworkspace").mkdir()
    with pytest.raises(ValueError, match=r"mismatch|artifact"):
        store_result(
            tmp_path,
            _ok_result(),
            artifacts=[{"path": "out.bin", "sha256": "0" * 64}],
            phase="VALIDATE",
            skill="project-publish",
            target="/t",
            verifications=[{"kind": "gate_result", "ok": True}],
        )


def test_a24_stale_content_blocks_complete(tmp_path: Path) -> None:
    code = tmp_path / "app.py"
    code.write_text("v1")
    (tmp_path / ".autoworkspace").mkdir()
    rid = _store_ok(tmp_path, op="local_gates", phase="VALIDATE", skill="project-publish")
    code.write_text("v2")
    with pytest.raises(ValueError, match="stale"):
        advance_status(
            tmp_path,
            phase="VALIDATE",
            skill="project-publish",
            evidence_ok=True,
            run_id=rid,
        )


def test_a25_admin_only_ok(tmp_path: Path) -> None:
    code = tmp_path / "app.py"
    code.write_text("stable")
    (tmp_path / ".autoworkspace").mkdir()
    rid = _store_ok(tmp_path, op="local_gates", phase="VALIDATE")
    (tmp_path / ".autoworkspace" / "status.yaml").write_text("phase: DEFINE\n")
    data = load_evidence(tmp_path, rid, revalidate_content=True, expected_phase="VALIDATE")
    assert data["outcome"] == "succeeded"


def test_a26_validate_snapshot_cannot_complete_define(tmp_path: Path) -> None:
    (tmp_path / "x").write_text("1")
    (tmp_path / ".autoworkspace").mkdir()
    # Store with DEFINE bindings but wrong op — load/complete must reject
    art = tmp_path / "artifact.txt"
    art.write_text("ok")
    rid = store_result(
        tmp_path,
        _ok_result("validate_snapshot"),
        phase="DEFINE",
        skill="plan-specification",
        target="/fixture",
        artifacts=[str(art)],
        verifications=[{"kind": "spec_deliverable", "ok": True}],
    )
    with pytest.raises(ValueError, match=r"operation|phase"):
        advance_status(
            tmp_path,
            phase="DEFINE",
            skill="plan-specification",
            evidence_ok=True,
            run_id=rid,
        )


def test_a27_wrong_target_rejected(tmp_path: Path) -> None:
    (tmp_path / "x").write_text("1")
    (tmp_path / ".autoworkspace").mkdir()
    rid = _store_ok(tmp_path, op="local_gates", phase="VALIDATE", target="/a")
    with pytest.raises(ValueError, match="target"):
        load_evidence(tmp_path, rid, expected_target="/b", revalidate_content=True)


# --- A28-A32: state transaction / transitions / idempotency ---


def test_a28_concurrent_writers(tmp_path: Path) -> None:
    (tmp_path / "c").write_text("z")
    (tmp_path / ".autoworkspace").mkdir()
    errors = []
    results = []

    def worker(i: int) -> None:
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
        except Exception as exc:
            errors.append(str(exc))

    # Sequential unique run_ids under lock — both should serialize without lost update
    rids = [_store_ok(tmp_path, op="plan_specification", phase="DEFINE") for _ in range(2)]
    barrier = threading.Barrier(2)

    def w(rid: str) -> None:
        barrier.wait()
        try:
            s = advance_status(
                tmp_path,
                phase="DEFINE",
                skill="plan-specification",
                evidence_ok=True,
                run_id=rid,
            )
            results.append(int(s.get("state_revision") or 0))
        except Exception as exc:
            errors.append(str(exc))

    t1 = threading.Thread(target=w, args=(rids[0],))
    t2 = threading.Thread(target=w, args=(rids[1],))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert not errors, errors
    assert sorted(results) == [1, 2]


def test_a30_status_to_define_rejected(tmp_path: Path) -> None:
    (tmp_path / "c").write_text("z")
    aw = tmp_path / ".autoworkspace"
    aw.mkdir()
    # Seed STATUS phase
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
    rid = _store_ok(tmp_path, op="plan_specification", phase="DEFINE")
    with pytest.raises(ValueError, match=r"regress|restart|invalid"):
        advance_status(
            tmp_path,
            phase="DEFINE",
            skill="plan-specification",
            evidence_ok=True,
            run_id=rid,
        )


def test_a32_idempotent_complete(tmp_path: Path) -> None:
    (tmp_path / "c").write_text("z")
    (tmp_path / ".autoworkspace").mkdir()
    rid = _store_ok(tmp_path, op="plan_specification", phase="DEFINE")
    s1 = advance_status(tmp_path, phase="DEFINE", skill="plan-specification", evidence_ok=True, run_id=rid)
    s2 = advance_status(tmp_path, phase="DEFINE", skill="plan-specification", evidence_ok=True, run_id=rid)
    assert s1["state_revision"] == 1
    assert s2["state_revision"] == 1
    assert s2.get("_idempotent_replay") is True


# --- A39-A40: preflight ---


def test_a40_network_hard_blocks() -> None:
    r = preflight_contract(
        {
            "skill": "local-email",
            "distribution": "workspace-required",
            "system_requirements": {"binaries": [], "network": True},
        },
        cwd=ROOT,
        allow_network=False,
    )
    assert r.ok is False
    assert any("network" in x for x in r.blocked_reasons)


def test_digest_plan_includes_handler() -> None:
    a = plan_digest("op", "t", {}, ["read"], handler_id="h1")
    b = plan_digest("op", "t", {}, ["read"], handler_id="h2")
    assert a != b


def test_content_manifest_schema(tmp_path: Path) -> None:
    (tmp_path / "f").write_bytes(b"hi")
    m = content_manifest(tmp_path)
    assert m["schema_version"] == 1
    assert "f" in m["entries"]
    assert len(m["digest"]) == SHA256_HEX_LEN


# --- V02 / D2: effective plan params (not globals alone) ---


def test_v02_dispatch_plan_includes_effective_params(monkeypatch: pytest.MonkeyPatch) -> None:
    """Approved plan must include keep_versions/journal/pkg_mgr used by cleaners."""

    monkeypatch.setattr(cr._STATE, "snapshot_id", "snap-v02")
    monkeypatch.setattr(cr._STATE, "pkg_mgr", "apt")
    monkeypatch.setattr(cr._STATE, "keep_versions", 5)
    monkeypatch.setattr(cr._STATE, "journal_vacuum_time", "3d")
    monkeypatch.setattr(cr._STATE, "journal_vacuum_size", "100M")
    monkeypatch.setattr(cr._STATE, "dry_run", False)
    monkeypatch.setattr(cr._STATE, "with_firmware", False)

    captured = {}

    def fake_registered(op: str, params: dict[str, Any], target: str = ".") -> OpResult:
        captured["params"] = dict(params)
        return OpResult(op, "succeeded", 0, 1, "", "mutate-host", run_id="x", plan_digest="d")

    monkeypatch.setattr(cr, "run_registered", fake_registered)
    # ensure import path for dispatch
    monkeypatch.setattr(cr, "hostname", lambda: "testhost")
    rc = cr.dispatch_operation("clean_journal")
    assert rc == 0
    p = captured["params"]
    assert p.get("snapshot_id") == "snap-v02"
    assert p.get("pkg_mgr") == "apt"
    assert p.get("keep_versions") == CUSTOM_KEEP_VERSIONS
    assert p.get("journal_time") == "3d"
    assert p.get("journal_size") == "100M"


def test_v02_handler_uses_plan_params_not_stale_globals(monkeypatch: pytest.MonkeyPatch) -> None:
    """After approval, handler must apply keep_versions from params even if global differs."""

    monkeypatch.setattr(cr._STATE, "keep_versions", 99)  # stale state
    monkeypatch.setattr(cr._STATE, "pkg_mgr", "wrong")
    seen = {}

    def spy_run_capture(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
        seen["cmd"] = cmd
        return 0, ""

    monkeypatch.setattr(cr, "run_capture", spy_run_capture)
    monkeypatch.setattr(cr, "run", lambda *a, **k: "1M")
    monkeypatch.setattr(cr, "log_info", lambda *a, **k: None)
    monkeypatch.setattr(cr, "log_warn", lambda *a, **k: None)
    monkeypatch.setattr(cr, "log_success", lambda *a, **k: None)

    cr._register_handlers()
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


def test_a39_standalone_missing_shared_deps(tmp_path: Path) -> None:
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


def test_a39_standalone_with_vendor_ok(tmp_path: Path) -> None:
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
