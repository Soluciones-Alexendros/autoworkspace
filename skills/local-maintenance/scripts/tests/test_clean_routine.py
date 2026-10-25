"""Tests for clean_routine single-path dispatch."""

from __future__ import annotations

from unittest.mock import patch

import clean_routine


def test_dry_run_simulates(monkeypatch):
    monkeypatch.setattr(clean_routine, "which", lambda c: "/bin/true" if c == "apt" else None)
    monkeypatch.setattr(clean_routine, "run_capture", lambda *a, **k: (0, ""))
    monkeypatch.setattr(clean_routine, "run", lambda *a, **k: "")
    rc = clean_routine.main(["--dry-run", "--json"])
    assert rc == 0
    assert all(a["status"] in ("simulated", "skipped") for a in clean_routine.ACTION_RESULTS)


def test_execute_blocked_without_approval(monkeypatch, tmp_path):
    monkeypatch.setattr(clean_routine, "which", lambda c: "/bin/true" if c == "apt" else None)
    monkeypatch.delenv("AUTOWORKSPACE_APPROVAL_PROVIDER", raising=False)
    snap = tmp_path / "snap-ok"
    snap.mkdir()
    (snap / "metadata.json").write_text('{"backend_status":"ok"}', encoding="utf-8")
    monkeypatch.setenv("SNAPSHOT_DIR", str(tmp_path))
    invoked = []

    def spy_capture(cmd, timeout=10):
        invoked.append(cmd)
        return 0, ""

    monkeypatch.setattr(clean_routine, "run_capture", spy_capture)
    monkeypatch.setattr(clean_routine, "run", lambda *a, **k: "")
    rc = clean_routine.main(["--execute", "--snapshot-id", "snap-ok"])
    assert rc != 0
    assert not any("journalctl --vacuum" in c or "apt-get" in c for c in invoked)


def test_dispatch_policy_deny_skips_handler(monkeypatch):
    monkeypatch.setattr(clean_routine, "DRY_RUN", False)
    monkeypatch.setattr(clean_routine, "EXECUTE", True)
    monkeypatch.setattr(clean_routine, "SNAPSHOT_ID", "snap")
    monkeypatch.setattr(clean_routine, "PKG_MGR", "apt")
    clean_routine.ACTION_RESULTS.clear()

    class Deny:
        outcome = "blocked"
        detail = "denied"
        returncode = 3
        run_id = ""

    monkeypatch.setattr(
        "execution.ops.run_registered",
        lambda *a, **k: Deny(),
    )
    called = []
    monkeypatch.setattr(clean_routine, "clean_journal", lambda: called.append(1))
    # dispatch goes through run_registered, not direct handler when registered via ops
    rc = clean_routine.dispatch_operation("clean_journal")
    assert rc == 3
    assert called == []


def test_generate_json_dry_run(monkeypatch, tmp_path):
    monkeypatch.setattr(clean_routine, "DRY_RUN", True)
    monkeypatch.setattr(clean_routine, "EXECUTE", False)
    monkeypatch.setattr(clean_routine, "PKG_MGR", "apt")
    monkeypatch.setattr(clean_routine, "JSON_MODE", True)
    out = tmp_path / "out.json"
    monkeypatch.setattr(clean_routine, "JSON_OUTPUT", str(out))
    monkeypatch.setattr(clean_routine, "WITH_FIRMWARE", False)
    clean_routine.ACTION_RESULTS.clear()
    clean_routine.ACTION_RESULTS.append({"action": "clean_journal", "status": "simulated", "rc": 0, "detail": ""})
    clean_routine.generate_json_output()
    assert out.is_file()
