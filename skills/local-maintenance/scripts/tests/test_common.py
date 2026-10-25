"""Tests common.py: --help, args inválidos, self-check, doradas puras."""

import json
import subprocess
import sys

import common

SCRIPT = "common.py"


def _run(*args):
    return subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True,
        text=True,
        cwd=".",
    )


def test_help_exit0():
    r = _run("--help")
    assert r.returncode == 0
    assert "usage" in (r.stdout + r.stderr).lower()


def test_invalid_args_exit2():
    r = _run("--opcion-invalida-xyz")
    assert r.returncode == 2


def test_self_check_exit0():
    r = _run("--self-check")
    assert r.returncode == 0
    assert "self-check OK" in r.stdout


def test_self_check_failure_exit1(monkeypatch):
    monkeypatch.setattr(common, "to_int", lambda *a, **k: 9999)
    assert common.main(["--self-check"]) == 1


def test_count_nonempty_golden():
    assert common.count_nonempty("a\n\nb\n  \nc\n") == 3
    assert common.count_nonempty("") == 0
    assert common.count_nonempty("\n\n") == 0


def test_to_int_golden():
    assert common.to_int("42") == 42
    assert common.to_int("  7  ") == 7
    assert common.to_int("x") == 0
    assert common.to_int("x", default=7) == 7
    assert common.to_int("") == 0
    assert common.to_int(None) == 0  # type: ignore[arg-type]


def test_finding_collector_health_score_golden():
    c = common.FindingCollector()
    c.add("S1", "security", "P0", "t", "d", "c", "PASS", "e", "", "R0")
    c.add("S2", "security", "P0", "t", "d", "c", "FAIL", "e", "", "R2")
    c.add("U1", "updates", "P1", "t", "d", "c", "PASS", "e", "", "R0")
    hs = c.health_score()
    assert hs["security"] == 50
    assert hs["updates"] == 100
    # Unchecked categories are None (not silent 100)
    assert hs["hygiene"] is None
    assert hs["resources"] is None
    assert hs["stability"] is None
    covered = 50 * common.CATEGORY_WEIGHTS["security"] + 100 * common.CATEGORY_WEIGHTS["updates"]
    weight = common.CATEGORY_WEIGHTS["security"] + common.CATEGORY_WEIGHTS["updates"]
    assert hs["overall"] == covered // weight
    s = c.summary()
    assert s["total_checks"] == 3
    assert s["passed"] == 2
    assert s["failed"] == 1
    assert s["check_coverage"] == 3


def test_health_score_skip_no_penaliza():
    c = common.FindingCollector()
    c.add("A1", "updates", "P1", "t", "d", "c", "PASS", "e", "", "R0")
    c.add("A2", "updates", "P4", "t", "d", "c", "SKIP", "no aplica", "", "R0")
    assert c.health_score()["updates"] == 100


def test_health_score_pondera_por_severidad():
    c = common.FindingCollector()
    c.add("S1", "security", "P0", "t", "d", "c", "FAIL", "e", "", "R2")
    c.add("P1", "security", "P4", "t", "d", "c", "FAIL", "e", "", "R2")
    c.add("W1", "stability", "P2", "t", "d", "c", "WARN", "e", "", "R0")
    hs = c.health_score()
    # security: solo puntua el fallo P0 -> 0; stability: WARN P2 -> 40
    assert hs["security"] == 0
    assert hs["stability"] == 40


def test_health_score_error_no_penaliza():
    c = common.FindingCollector()
    c.add("S1", "security", "P0", "t", "d", "c", "PASS", "e", "", "R0")
    c.add("S2", "security", "P0", "t", "d", "c", "ERROR", "e", "", "R0")
    assert c.health_score()["security"] == 100


def test_category_weights_sum_100():
    assert sum(common.CATEGORY_WEIGHTS.values()) == 100
    assert set(common.CATEGORY_WEIGHTS) == set(common.CATEGORIES)
    assert common.SEVERITY_WEIGHTS["P0"] > common.SEVERITY_WEIGHTS["P4"]


def test_check_pkg_06_apt_cuenta_solo_fuera_de_repo():
    c = common.FindingCollector()
    installed = ["pkg-repo", "libfoo:amd64", "installed-local"]

    def runner(cmd, timeout=10):
        if cmd.startswith("apt-cache dumpavail"):
            return "pkg-repo\nlibfoo\notro\n"
        if cmd.startswith("dpkg-query"):
            return "\n".join(installed) + "\n"
        return ""

    common.check_pkg_06(c, "apt", runner=runner)
    finding = c.findings[0]
    assert finding["status"] == "PASS"
    assert finding["title"] == "1 paquetes foraneos"
    assert "installed-local" in finding["evidence"]


def test_check_pkg_06_apt_muchos_manuales_no_son_foraneos():
    c = common.FindingCollector()
    installed = [f"pkg-{i}" for i in range(60)]

    def runner(cmd, timeout=10):
        if cmd.startswith("apt-cache dumpavail"):
            return "".join(f"pkg-{i}\n" for i in range(60))
        if cmd.startswith("dpkg-query"):
            return "\n".join(installed) + "\n"
        return ""

    common.check_pkg_06(c, "apt", runner=runner)
    assert c.findings[0]["status"] == "PASS"
    assert c.findings[0]["title"] == "0 paquetes foraneos"


def test_check_pkg_06_apt_warn_si_supera_umbral():
    c = common.FindingCollector()

    def runner(cmd, timeout=10):
        if cmd.startswith("apt-cache dumpavail"):
            return "conocido\n"
        if cmd.startswith("dpkg-query"):
            return "conocible\n" + "".join(f"local-{i}\n" for i in range(51))
        return ""

    common.check_pkg_06(c, "apt", runner=runner)
    assert c.findings[0]["status"] == "WARN"


def test_check_pkg_06_si_gestor_desconocido_skip():
    c = common.FindingCollector()
    common.check_pkg_06(c, "zypper", runner=lambda cmd, timeout=10: "")
    assert c.findings[0]["status"] == "SKIP"
    # SKIP-only category is not_checked — never silent 100
    assert c.health_score()["hygiene"] is None


def test_load_profile_family_tmp(tmp_path):
    prof = {
        "distro": {
            "family": "debian",
            "package_manager": "apt",
            "distro_id": "ubuntu",
            "version_id": "22.04",
            "version_codename": "jammy",
        }
    }
    p = tmp_path / "profile.json"
    p.write_text(json.dumps(prof), encoding="utf-8")
    fam, mgr, did, vid, cod = common.load_profile_family(str(p))
    assert (fam, mgr, did, vid, cod) == ("debian", "apt", "ubuntu", "22.04", "jammy")


def test_load_profile_family_corrupt_fallback(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{no-json", encoding="utf-8")
    fam, mgr, did, vid, cod = common.load_profile_family(str(p))
    assert isinstance(fam, str) and isinstance(mgr, str)
