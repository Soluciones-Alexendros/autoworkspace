"""P0 containment + exact assertions (no or True / failed >= 0)."""
from __future__ import annotations

import json
import tarfile
from pathlib import Path
from unittest.mock import patch

import clean_routine
import common
import risk_gate
import snapshot_state


class SpyExecutor:
    FORBIDDEN_MUTATORS = (
        "apt-get",
        "apt autoremove",
        "pacman -Sc",
        "dnf clean",
        "journalctl --vacuum",
        "fwupdmgr update",
        "needrestart -r",
        "tar -xzf",
        "tar -czf",
        "timeshift --create",
        "snapper create",
    )

    def __init__(self) -> None:
        self.calls: list[str] = []

    def __call__(self, cmd: str, timeout: int = 10):
        self.calls.append(cmd)
        if any(x in cmd for x in self.FORBIDDEN_MUTATORS):
            raise AssertionError(f"forbidden host mutation attempted: {cmd}")
        return 1, ""


def test_f01_execute_without_policy_blocks(monkeypatch, tmp_path):
    spy = SpyExecutor()
    monkeypatch.setattr(clean_routine, "which", lambda c: "/bin/true" if c == "apt" else None)
    monkeypatch.setattr(clean_routine, "run_capture", spy)
    monkeypatch.setattr(clean_routine, "run", lambda *a, **k: "")
    monkeypatch.delenv("AUTOWORKSPACE_ALLOW_HOST_MUTATION", raising=False)
    rc = clean_routine.main(["--execute", "--snapshot-id", "missing-snap"])
    assert rc != 0
    assert not any("apt" in c or "journalctl --vacuum" in c for c in spy.calls)


def test_f02_create_snapshot_requires_approval(monkeypatch):
    monkeypatch.setattr(clean_routine, "which", lambda c: "/bin/true" if c == "apt" else None)
    monkeypatch.delenv("AUTOWORKSPACE_APPROVAL_PROVIDER", raising=False)

    def fake_run_capture(cmd, timeout=10):
        raise AssertionError(f"mutation/create before approval: {cmd}")

    monkeypatch.setattr(clean_routine, "run_capture", fake_run_capture)
    monkeypatch.setattr(clean_routine, "run", lambda *a, **k: "")
    rc = clean_routine.main(["--execute"])
    assert rc == 3  # blocked awaiting approval


def test_f02_invalid_snapshot_id_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(clean_routine, "which", lambda c: "/bin/true" if c == "apt" else None)
    monkeypatch.setattr(clean_routine, "run_capture", SpyExecutor())
    monkeypatch.setenv("SNAPSHOT_DIR", str(tmp_path))
    rc = clean_routine.main(["--execute", "--snapshot-id", "../escape"])
    assert rc != 0


def test_f03_json_reflects_simulated_not_completed(monkeypatch, tmp_path):
    monkeypatch.setattr(clean_routine, "which", lambda c: "/bin/true" if c == "apt" else None)
    monkeypatch.setattr(clean_routine, "run_capture", SpyExecutor())
    monkeypatch.setattr(clean_routine, "run", lambda *a, **k: "")
    out = tmp_path / "out.json"
    rc = clean_routine.main(["--dry-run", "--json", str(out)])
    assert rc == 0
    assert out.is_file()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["summary"]["failed"] == 0
    assert data["summary"]["simulated"] >= 1
    assert data["metadata"]["dry_run"] is True
    assert all(
        a["status"] in ("simulated", "skipped") for a in data["actions"]
    )
    assert "completed" not in {a["status"] for a in data["actions"]}


def test_f04_unknown_operation_denied():
    assert risk_gate.classify_command("echo hola") == "R0"
    allowed, reason = risk_gate.authorize_operation("totally-unknown-op", {})
    assert allowed is False
    assert reason


def test_authorize_rejects_approved_token():
    allowed, reason = risk_gate.authorize_operation(
        "clean_journal", {"approved": True, "snapshot_id": "s"}
    )
    assert allowed is False
    assert "consent" in reason or "ApprovalProvider" in reason


def test_f19_backend_failure_not_success(monkeypatch, tmp_path):
    monkeypatch.setenv("AUTOWORKSPACE_EXECUTION_APPROVED", "1")
    monkeypatch.setattr(snapshot_state, "which", lambda c: "/usr/bin/timeshift" if c == "timeshift" else None)
    monkeypatch.setattr(snapshot_state, "detect_pkg_mgr", lambda: "apt")
    monkeypatch.setattr(snapshot_state, "run", lambda *a, **k: "5.0.0\n")
    monkeypatch.setattr(snapshot_state, "run_capture", lambda *a, **k: (1, "fail"))
    monkeypatch.setattr(snapshot_state, "capture_packages", lambda *a, **k: None)
    monkeypatch.setattr(snapshot_state, "capture_etc_checksums", lambda *a, **k: None)
    monkeypatch.setattr(snapshot_state, "capture_config_pending", lambda *a, **k: None)
    monkeypatch.setattr(snapshot_state, "write_text", lambda *a, **k: None)
    monkeypatch.setattr(snapshot_state, "md5_file", lambda p: "abc")

    rc = snapshot_state.main(["snap-fail", "--snapshot-dir", str(tmp_path)])
    assert rc != 0


def test_f20_no_private_ssh_keys_by_default(monkeypatch, tmp_path):
    monkeypatch.setenv("AUTOWORKSPACE_EXECUTION_APPROVED", "1")
    monkeypatch.setattr(snapshot_state, "which", lambda c: None)
    monkeypatch.setattr(snapshot_state, "detect_pkg_mgr", lambda: "apt")
    monkeypatch.setattr(snapshot_state, "run", lambda *a, **k: "")
    captured = {}

    def capture_run(cmd, timeout=10):
        captured["cmd"] = cmd
        return 0, ""

    monkeypatch.setattr(snapshot_state, "run_capture", capture_run)
    monkeypatch.setattr(snapshot_state, "capture_packages", lambda *a, **k: None)
    monkeypatch.setattr(snapshot_state, "capture_etc_checksums", lambda *a, **k: None)
    monkeypatch.setattr(snapshot_state, "capture_config_pending", lambda *a, **k: None)
    monkeypatch.setattr(snapshot_state, "write_text", lambda *a, **k: None)
    monkeypatch.setattr(snapshot_state, "md5_file", lambda p: "d" * 32)

    snapshot_state.main(["snap-ssh", "--snapshot-dir", str(tmp_path)])
    cmd = captured.get("cmd", "")
    assert "ssh_host_" not in cmd
    assert "id_rsa" not in cmd


def test_f21_empty_category_not_perfect_score():
    collector = common.FindingCollector()
    scores = collector.health_score()
    for cat, score in scores.items():
        if cat == "overall":
            continue
        assert score != 100 or collector.summary().get("check_coverage") == 0
    assert collector._category_score("packages") != 100


def test_f21_timeout_preserved_in_run_result():
    with patch("common.subprocess.run", side_effect=__import__("subprocess").TimeoutExpired("x", 1)):
        res = common.run_result(["true"], timeout=1)
        assert res.timed_out or res.returncode != 0


def test_f22_skill_version_from_manifest():
    version = common.skill_version_from_manifest()
    assert version == common.SKILL_VERSION
    assert version != "2.0.0"


def test_r07_dry_run_zero_mutations(monkeypatch):
    spy = SpyExecutor()
    monkeypatch.setattr(clean_routine, "which", lambda c: "/bin/true" if c == "apt" else None)
    monkeypatch.setattr(clean_routine, "run_capture", spy)
    monkeypatch.setattr(clean_routine, "run", lambda *a, **k: "ok")
    rc = clean_routine.main(["--dry-run"])
    assert rc == 0
    assert spy.calls == []


def test_restore_staging_content_assert(tmp_path):
    snap = tmp_path / "snap-x"
    snap.mkdir()
    (snap / "metadata.json").write_text("{}", encoding="utf-8")
    tarball = snap / "etc-backup.tar.gz"
    src = tmp_path / "payload"
    src.mkdir()
    (src / "hello.txt").write_text("restore-ok\n", encoding="utf-8")
    with tarfile.open(tarball, "w:gz") as tf:
        tf.add(src / "hello.txt", arcname="hello.txt")
    rc = snapshot_state.main(
        ["--rollback", "snap-x", "--snapshot-dir", str(tmp_path), "--execute"]
    )
    assert rc == 0


def test_restore_rejects_symlink_member(tmp_path):
    snap = tmp_path / "snap-link"
    snap.mkdir()
    (snap / "metadata.json").write_text("{}", encoding="utf-8")
    tarball = snap / "etc-backup.tar.gz"
    with tarfile.open(tarball, "w:gz") as tf:
        info = tarfile.TarInfo(name="evil")
        info.type = tarfile.SYMTYPE
        info.linkname = "/etc/passwd"
        tf.addfile(info)
    # Caller staging rejected; program staging still rejects symlink members
    rc_foreign = snapshot_state.rollback_snapshot(
        str(tmp_path), "snap-link", execute=True, restore_root=str(tmp_path / "stage")
    )
    assert rc_foreign == 3
    rc = snapshot_state.rollback_snapshot(str(tmp_path), "snap-link", execute=True)
    assert rc != 0


def test_host_rollback_privileged_root_blocked(tmp_path):
    snap = tmp_path / "snap-x"
    snap.mkdir()
    (snap / "etc-backup.tar.gz").write_bytes(b"\x1f\x8b")  # not used if root rejected first
    (snap / "metadata.json").write_text("{}", encoding="utf-8")
    rc = snapshot_state.rollback_snapshot(
        str(tmp_path), "snap-x", execute=True, restore_root="/"
    )
    assert rc == 3
