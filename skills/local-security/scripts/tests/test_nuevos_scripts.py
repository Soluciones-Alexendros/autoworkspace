"""Tests de los scripts nuevos de local-security (esqueletos funcionales)."""

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS)

import apparmor_lifecycle  # noqa: E402
import forense_collector  # noqa: E402
import harden_plan  # noqa: E402
import scan_orchestrator  # noqa: E402
import vulns_check  # noqa: E402

EXIT_USAGE = 2
EXPECTED_INDETERMINADOS = 3
MIN_HARDEN_IDS = 50
EXPECTED_UPGRADABLE = 2
EXPECTED_PENDING = 2
EXPECTED_SECURITY_SIGNALS = 6
EXPECTED_SSH_IDS = 3
ISO_TS_LEN = 20


def _run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, script), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def test_all_help_exit0() -> None:
    for s in (
        "scan_orchestrator.py",
        "vulns_check.py",
        "harden_plan.py",
        "apparmor_lifecycle.py",
        "forense_collector.py",
    ):
        r = _run(s, "--help")
        assert r.returncode == 0, s


def test_all_invalid_args_exit2() -> None:
    for s in ("scan_orchestrator.py", "vulns_check.py", "harden_plan.py", "apparmor_lifecycle.py"):
        r = _run(s, "--opcion-inexistente-xyz")
        assert r.returncode == EXIT_USAGE, s
    r = _run("forense_collector.py", "receta-inexistente-xyz")
    assert r.returncode == EXIT_USAGE


def test_scan_check_exit0(tmp_path: Path) -> None:
    out = tmp_path / "scan.json"
    r = _run("scan_orchestrator.py", "--json", str(out))
    assert r.returncode == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert set(data) >= {"availability", "scans", "cross_validation"}


def test_cross_validate_golden() -> None:
    res = {"rkhunter": {"warnings": 2}, "debsums": {"mismatches": 1}, "aide": {"changed_entries": True}}
    cv = scan_orchestrator.cross_validate(res)
    assert len(cv["indeterminados"]) == EXPECTED_INDETERMINADOS and cv["validados"] == []
    cv2 = scan_orchestrator.cross_validate({"rkhunter": {}, "debsums": {}, "aide": {}})
    assert cv2["descartados"] != []


def test_vulns_exit0(tmp_path: Path) -> None:
    out = tmp_path / "vulns.json"
    r = _run("vulns_check.py", "--json", str(out))
    assert r.returncode == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert set(data["sources"]) == {"apt", "snap", "flatpak"}


def test_harden_plan_baseline_ids() -> None:
    base = os.path.join(SCRIPTS, "..", "references", "hardening-baseline.md")
    ids = harden_plan.parse_control_ids(base)
    assert "SSH-01" in ids and "KR-22" in ids and len(ids) > MIN_HARDEN_IDS


def test_harden_plan_exit0(tmp_path: Path) -> None:
    out = tmp_path / "plan.json"
    r = _run("harden_plan.py", "--level", "1", "--json", str(out))
    assert r.returncode == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "plan" in data and isinstance(data["plan"], list)


def test_harden_plan_baseline_ilegible() -> None:
    assert harden_plan.parse_control_ids("/no/existe/baseline.md") == []
    assert _run("harden_plan.py", "--baseline", "/no/existe.md").returncode == 1


def test_apparmor_status_y_soak(tmp_path: Path) -> None:
    st = str(tmp_path / "aa.json")
    assert apparmor_lifecycle.main(["status", "--state", st]) == 0
    assert apparmor_lifecycle.main(["soak", "--profile", "test-prof", "--days", "3", "--state", st]) == 0
    data = json.loads(Path(st).read_text(encoding="utf-8"))
    assert data["profiles"]["test-prof"]["stage"] == "soak"
    # enforce bloqueado si aa-logprof no parsea
    rc = apparmor_lifecycle.main(["enforce", "--profile", "test-prof", "--state", st])
    assert rc in (0, 1)


def test_apparmor_retroceso_bloqueado(tmp_path: Path) -> None:
    st = str(tmp_path / "aa2.json")
    apparmor_lifecycle.main(["soak", "--profile", "p", "--days", "1", "--state", st])
    assert apparmor_lifecycle.main(["genprof", "--profile", "p", "--state", st]) == 1


def test_forense_sin_pid_requiere_pid() -> None:
    assert forense_collector.main(["pid"]) == EXIT_USAGE


def test_forense_timeline_exit0(tmp_path: Path) -> None:
    out = tmp_path / "for.json"
    r = _run("forense_collector.py", "timeline", "--json", str(out))
    assert r.returncode == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "events" in data and "system_clock" in data


def test_postura_json(tmp_path: Path) -> None:
    sh = os.path.join(SCRIPTS, "postura_seguridad.sh")
    p = subprocess.run(["bash", sh, "--json"], capture_output=True, text=True, timeout=60, check=False)
    assert p.returncode == 0
    data = json.loads(p.stdout)
    assert "apparmor_kernel" in data and "lockdown" in data and "tpm2" in data
    assert "syft" in data and "canon_terminal" in data


def test_postura_sin_hardcodeo_visible() -> None:
    sh = os.path.join(SCRIPTS, "postura_seguridad.sh")
    text = Path(sh).read_text(encoding="utf-8")
    assert "Aplicaciones/Terminal" not in text


# --- vulns_check unit tests for coverage ---


def test_vulns_which_returns_none() -> None:
    with patch("vulns_check.shutil.which", return_value=None):
        assert vulns_check.which("nonexistent") is None


def test_vulns_run_cmd_timeout() -> None:
    with patch("vulns_check.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 10)):
        rc, out = vulns_check.run_cmd("sleep 100", timeout=1)
        assert rc == 1
        assert out == ""


def test_vulns_run_cmd_oserror() -> None:
    with patch("vulns_check.subprocess.run", side_effect=OSError("fail")):
        rc, out = vulns_check.run_cmd("badcmd", timeout=1)
        assert rc == 1
        assert out == ""


def test_vulns_has_network_true() -> None:
    with patch("vulns_check.run_cmd", return_value=(0, "1.2.3.4")):
        assert vulns_check.has_network() is True


def test_vulns_has_network_false() -> None:
    with patch("vulns_check.run_cmd", return_value=(0, "")):
        assert vulns_check.has_network() is False


def test_vulns_check_apt_skip() -> None:
    with patch("vulns_check.which", return_value=None):
        result = vulns_check.check_apt()
        assert result["status"] == "skip"
        assert result["reason"] == "apt no disponible"


def test_vulns_check_apt_ok() -> None:
    with (
        patch("vulns_check.which", return_value="/usr/bin/apt"),
        patch("vulns_check.run_cmd", return_value=(0, "pkg1/security\npkg2\n")),
    ):
        result = vulns_check.check_apt()
        assert result["status"] == "ok"
        assert result["upgradable"] == EXPECTED_UPGRADABLE
        assert result["security"] == 1


def test_vulns_check_snap_skip() -> None:
    with patch("vulns_check.which", return_value=None):
        result = vulns_check.check_snap()
        assert result["status"] == "skip"


def test_vulns_check_snap_ok() -> None:
    with (
        patch("vulns_check.which", return_value="/usr/bin/snap"),
        patch("vulns_check.run_cmd", return_value=(0, "pkg1\npkg2\n")),
    ):
        result = vulns_check.check_snap()
        assert result["status"] == "ok"
        assert result["pending"] == 1


def test_vulns_check_flatpak_skip() -> None:
    with patch("vulns_check.which", return_value=None):
        result = vulns_check.check_flatpak()
        assert result["status"] == "skip"


def test_vulns_check_flatpak_ok() -> None:
    with (
        patch("vulns_check.which", return_value="/usr/bin/flatpak"),
        patch("vulns_check.run_cmd", return_value=(0, "pkg1\npkg2\n")),
    ):
        result = vulns_check.check_flatpak()
        assert result["status"] == "ok"
        assert result["pending"] == EXPECTED_PENDING


def test_vulns_main_no_network_json(tmp_path: Path) -> None:
    out = tmp_path / "vulns.json"
    with patch("vulns_check.has_network", return_value=False):
        rc = vulns_check.main(["--json", str(out)])
        assert rc == 0
        data = json.loads(out.read_text())
        assert data["network"] is False
        assert "sources" in data
        assert "summary" in data


def test_vulns_main_with_network_json(tmp_path: Path) -> None:
    out = tmp_path / "vulns.json"
    with (
        patch("vulns_check.has_network", return_value=True),
        patch("vulns_check.check_apt", return_value={"status": "ok", "upgradable": 5, "security": 2}),
        patch("vulns_check.check_snap", return_value={"status": "ok", "pending": 1}),
        patch("vulns_check.check_flatpak", return_value={"status": "ok", "pending": 3}),
    ):
        rc = vulns_check.main(["--json", str(out)])
        assert rc == 0
        data = json.loads(out.read_text())
        assert data["network"] is True
        assert data["summary"]["pending_security_signals"] == EXPECTED_SECURITY_SIGNALS


# --- scan_orchestrator unit tests for coverage ---


def test_scan_which_found() -> None:
    with patch("scan_orchestrator.shutil.which", return_value="/usr/bin/clamscan"):
        assert scan_orchestrator.which("clamscan") == "/usr/bin/clamscan"


def test_scan_which_not_found() -> None:
    with patch("scan_orchestrator.shutil.which", return_value=None):
        assert scan_orchestrator.which("nonexistent") is None


def test_scan_run_cmd_success() -> None:
    with patch("scan_orchestrator.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
        rc, out = scan_orchestrator.run_cmd("echo test", timeout=10)
        assert rc == 0
        assert out == "output"


def test_scan_run_cmd_timeout() -> None:
    with patch("scan_orchestrator.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 10)):
        rc, out = scan_orchestrator.run_cmd("sleep 100", timeout=1)
        assert rc == 1
        assert out == ""


def test_scan_run_cmd_oserror() -> None:
    with patch("scan_orchestrator.subprocess.run", side_effect=OSError("fail")):
        rc, out = scan_orchestrator.run_cmd("badcmd", timeout=1)
        assert rc == 1
        assert out == ""


def test_scan_check_availability_all_skip() -> None:
    with patch("scan_orchestrator.which", return_value=None):
        avail = scan_orchestrator.check_availability()
        assert avail["clamav"]["daemon"] is False
        assert avail["rkhunter"]["present"] is False
        assert avail["aide"]["present"] is False
        assert avail["debsums"]["present"] is False
        assert avail["lynis"]["present"] is False


def test_scan_check_availability_some_present() -> None:
    def mock_which(cmd: str) -> str | None:
        if cmd in ("clamscan", "rkhunter"):
            return f"/usr/bin/{cmd}"
        return None

    with patch("scan_orchestrator.which", side_effect=mock_which):
        avail = scan_orchestrator.check_availability()
        assert avail["clamav"]["daemon"] is True
        assert avail["rkhunter"]["present"] is True
        assert avail["aide"]["present"] is False


def test_scan_clamav_skip() -> None:
    with patch("scan_orchestrator.which", return_value=None):
        result = scan_orchestrator.scan_clamav()
        assert result["status"] == "skip"


def test_scan_rkhunter_skip() -> None:
    with patch("scan_orchestrator.which", return_value=None):
        result = scan_orchestrator.scan_rkhunter()
        assert result["status"] == "skip"


def test_scan_aide_skip() -> None:
    with patch("scan_orchestrator.which", return_value=None):
        result = scan_orchestrator.scan_aide()
        assert result["status"] == "skip"


def test_scan_debsums_skip() -> None:
    with patch("scan_orchestrator.which", return_value=None):
        result = scan_orchestrator.scan_debsums()
        assert result["status"] == "skip"


def test_scan_lynis_skip() -> None:
    with patch("scan_orchestrator.which", return_value=None):
        result = scan_orchestrator.scan_lynis()
        assert result["status"] == "skip"


def test_scan_cross_validate_no_undetermined() -> None:
    cv = scan_orchestrator.cross_validate({})
    assert cv["descartados"] != []


def test_scan_cross_validate_rkhunter_warnings() -> None:
    cv = scan_orchestrator.cross_validate({"rkhunter": {"warnings": 5}})
    assert len(cv["indeterminados"]) >= 1
    assert any("rkhunter" in item for item in cv["indeterminados"])


def test_scan_cross_validate_debsums_mismatches() -> None:
    cv = scan_orchestrator.cross_validate({"debsums": {"mismatches": 3}})
    assert len(cv["indeterminados"]) >= 1
    assert any("debsums" in item for item in cv["indeterminados"])


def test_scan_cross_validate_aide_changed() -> None:
    cv = scan_orchestrator.cross_validate({"aide": {"changed_entries": True}})
    assert len(cv["indeterminados"]) >= 1
    assert any("aide" in item for item in cv["indeterminados"])


def test_scan_main_check_only() -> None:
    rc = scan_orchestrator.main(["--check"])
    assert rc == 0


def test_scan_main_run_only(tmp_path: Path) -> None:
    out = tmp_path / "scan.json"
    with (
        patch("scan_orchestrator.check_availability", return_value={}),
        patch("scan_orchestrator.scan_clamav", return_value={"status": "skip"}),
        patch("scan_orchestrator.scan_rkhunter", return_value={"status": "skip"}),
        patch("scan_orchestrator.scan_aide", return_value={"status": "skip"}),
        patch("scan_orchestrator.scan_debsums", return_value={"status": "skip"}),
        patch("scan_orchestrator.scan_lynis", return_value={"status": "skip"}),
    ):
        rc = scan_orchestrator.main(["--run", "--json", str(out)])
        assert rc == 0
        data = json.loads(out.read_text())
        assert "availability" in data
        assert "scans" in data
        assert "cross_validation" in data


# --- harden_plan unit tests for coverage ---


def test_harden_parse_control_ids_invalid_file() -> None:
    assert harden_plan.parse_control_ids("/no/existe/baseline.md") == []


def test_harden_parse_control_ids_empty_file(tmp_path: Path) -> None:
    f = tmp_path / "empty.md"
    f.write_text("", encoding="utf-8")
    assert harden_plan.parse_control_ids(str(f)) == []


def test_harden_parse_control_ids_with_ids(tmp_path: Path) -> None:
    f = tmp_path / "baseline.md"
    f.write_text("SSH-01 some text\nFW-02 more\nSSH-01 duplicate\nKR-22 end", encoding="utf-8")
    ids = harden_plan.parse_control_ids(str(f))
    assert "SSH-01" in ids
    assert "FW-02" in ids
    assert "KR-22" in ids
    assert len(ids) == EXPECTED_SSH_IDS  # SSH-01 only once


def test_harden_run_cmd_success() -> None:
    with patch("harden_plan.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="output", stderr="")
        out = harden_plan.run_cmd("echo test", timeout=10)
        assert out == "output"


def test_harden_run_cmd_timeout() -> None:
    with patch("harden_plan.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 10)):
        out = harden_plan.run_cmd("sleep 100", timeout=1)
        assert out == ""


def test_harden_run_cmd_oserror() -> None:
    with patch("harden_plan.subprocess.run", side_effect=OSError("fail")):
        out = harden_plan.run_cmd("badcmd", timeout=1)
        assert out == ""


def test_harden_probe_current(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        harden_plan, "run_cmd", lambda cmd, timeout=10: "permitrootlogin no\npasswordauthentication yes\n"
    )
    state = harden_plan.probe_current()
    assert state["SSH-01"] == "no"
    assert state["SSH-02"] == "yes"


def test_harden_main_level1_json(tmp_path: Path) -> None:
    out = tmp_path / "plan.json"
    # Create a dummy baseline file
    baseline = tmp_path / "baseline.md"
    baseline.write_text("SSH-01\nFW-02\nKR-22", encoding="utf-8")
    with patch("harden_plan.DEFAULT_BASELINE", str(baseline)):
        rc = harden_plan.main(["--level", "1", "--json", str(out)])
        assert rc == 0
        data = json.loads(out.read_text())
        assert "plan" in data
        assert isinstance(data["plan"], list)


# --- forense_collector unit tests for coverage ---


def test_forense_which_found() -> None:
    with patch("forense_collector.shutil.which", return_value="/usr/bin/journalctl"):
        assert forense_collector.which("journalctl") == "/usr/bin/journalctl"


def test_forense_which_not_found() -> None:
    with patch("forense_collector.shutil.which", return_value=None):
        assert forense_collector.which("nonexistent") is None


def test_forense_run_cmd_success() -> None:
    with patch("forense_collector.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="output", stderr="")
        out = forense_collector.run_cmd("echo test", timeout=10)
        assert out == "output"


def test_forense_run_cmd_timeout() -> None:
    with patch("forense_collector.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 10)):
        out = forense_collector.run_cmd("sleep 100", timeout=1)
        assert out == ""


def test_forense_run_cmd_oserror() -> None:
    with patch("forense_collector.subprocess.run", side_effect=OSError("fail")):
        out = forense_collector.run_cmd("badcmd", timeout=1)
        assert out == ""


def test_forense_utcnow_format() -> None:
    ts = forense_collector.utcnow()
    assert len(ts) == ISO_TS_LEN  # YYYY-MM-DDTHH:MM:SSZ
    assert ts[4] == "-" and ts[7] == "-" and ts[10] == "T" and ts[13] == ":" and ts[16] == ":" and ts.endswith("Z")


def test_forense_collect_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(forense_collector, "run_cmd", lambda cmd, timeout=120: "")
    events = forense_collector.collect_auth("1 hour ago")
    assert isinstance(events, list)


def test_forense_collect_sudo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(forense_collector, "run_cmd", lambda cmd, timeout=120: "")
    events = forense_collector.collect_sudo("1 hour ago")
    assert isinstance(events, list)


def test_forense_collect_apparmor_no_ausearch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(forense_collector, "which", lambda cmd: None)
    events = forense_collector.collect_apparmor("1 hour ago")
    assert len(events) == 1
    assert events[0]["source"] == "ausearch"


def test_forense_main_auth_json(tmp_path: Path) -> None:
    out = tmp_path / "for.json"
    with (
        patch("forense_collector.collect_auth", return_value=[]),
        patch("forense_collector.collect_sudo", return_value=[]),
        patch("forense_collector.collect_apparmor", return_value=[]),
        patch("forense_collector.collect_watch_key", return_value=[]),
        patch("forense_collector.collect_pid", return_value=[]),
    ):
        rc = forense_collector.main(["auth", "--json", str(out)])
        assert rc == 0


def test_forense_main_timeline_json(tmp_path: Path) -> None:
    out = tmp_path / "for.json"
    with (
        patch("forense_collector.collect_auth", return_value=[]),
        patch("forense_collector.collect_sudo", return_value=[]),
        patch("forense_collector.collect_apparmor", return_value=[]),
        patch("forense_collector.collect_watch_key", return_value=[]),
        patch("forense_collector.collect_pid", return_value=[]),
    ):
        rc = forense_collector.main(["timeline", "--json", str(out)])
        assert rc == 0
        data = json.loads(out.read_text())
        assert "events" in data
        assert "system_clock" in data


def test_forense_main_pid_requires_arg() -> None:
    assert forense_collector.main(["pid"]) == EXIT_USAGE


# --- apparmor_lifecycle unit tests for coverage ---


def test_apparmor_which_found() -> None:
    with patch("apparmor_lifecycle.shutil.which", return_value="/usr/bin/apparmor_parser"):
        assert apparmor_lifecycle.which("apparmor_parser") == "/usr/bin/apparmor_parser"


def test_apparmor_which_not_found() -> None:
    with patch("apparmor_lifecycle.shutil.which", return_value=None):
        assert apparmor_lifecycle.which("nonexistent") is None


def test_apparmor_utcnow_format() -> None:
    ts = apparmor_lifecycle.utcnow()
    assert len(ts) == ISO_TS_LEN
    assert ts[4] == "-" and ts[7] == "-" and ts[10] == "T" and ts[13] == ":" and ts[16] == ":" and ts.endswith("Z")


def test_apparmor_load_state(tmp_path: Path) -> None:
    state_file = tmp_path / "aa.json"
    state_file.write_text('{"profiles": {"test-prof": {"stage": "soak"}}}', encoding="utf-8")
    state = apparmor_lifecycle.load_state(str(state_file))
    assert state["profiles"]["test-prof"]["stage"] == "soak"


def test_apparmor_load_state_missing() -> None:
    state = apparmor_lifecycle.load_state("/no/existe.json")
    assert state == {}


def test_apparmor_save_state(tmp_path: Path) -> None:
    state_file = tmp_path / "aa.json"
    apparmor_lifecycle.save_state(str(state_file), {"profiles": {"p": {"stage": "enforce"}}})
    data = json.loads(state_file.read_text())
    assert data["profiles"]["p"]["stage"] == "enforce"


def test_apparmor_validate_logprof_parseable_no_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(apparmor_lifecycle, "which", lambda cmd: None)
    assert apparmor_lifecycle.validate_logprof_parseable("test-prof") is False
