"""Dorados (valores congelados del código actual) + errores controlados sin red.

Exit codes: 0 OK · 1 error de datos/render · 2 error de uso/IO/red.
Degradación documentada: HTML corrupto no aborta (checks parciales, error None).
"""

import importlib.util
import json
import os
import sys
import urllib.error

import pytest

# Cargar módulos desde scripts/ explícitamente para evitar colisiones con web-compliance
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")


def _load_module(name):
    path = os.path.join(SCRIPTS_DIR, f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"web_compliance_{name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"web_compliance_{name}"] = module
    spec.loader.exec_module(module)
    return module


audit_page = _load_module("audit_page")
contrast = _load_module("contrast")
score_mod = _load_module("score")
report_mod = _load_module("report")

FIX = os.path.join(os.path.dirname(__file__), "fixtures")

# ---------------------------------------------------------------- contrast

CONTRAST_GOLDEN = [
    # (fg, bg, ratio, aa, aaa, veredicto)
    ("#000000", "#FFFFFF", 21.0, True, True, "AAA"),
    ("#767676", "#FFFFFF", 4.54, True, False, "AA"),
    ("#767676", "#FFFF00", 4.23, False, False, "FAIL"),
    ("#777777", "#FFFFFF", 4.48, False, False, "FAIL"),
    ("#1a1a1a", "#ffffff", 17.4, True, True, "AAA"),
]


@pytest.mark.parametrize("fg,bg,ratio,aa,aaa,veredicto", CONTRAST_GOLDEN)
def test_contrast_dorado(fg, bg, ratio, aa, aaa, veredicto):
    r = contrast.check(fg, bg)
    assert r["ratio"] == pytest.approx(ratio, abs=0.02)
    assert r["aa"] is aa
    assert r["aaa"] is aaa
    assert r["veredicto"] == veredicto
    assert r["aa_ui_components"] == (ratio >= 3.0)


def test_contrast_selftest_interno_pasa():
    assert contrast.selftest() == []


# ---------------------------------------------------------------- score


def test_score_page_pass_dorado():
    res = audit_page.audit(file=os.path.join(FIX, "page_pass.html"))
    assert res["error"] is None
    sc = score_mod.score(res["checks"])
    assert sc["pct_global"] == 100
    assert sc["dictamen"] == "POSITIVO"
    assert sc["fails_criticos"] == 0
    assert sc["total_hallazgos"] == 0
    assert sc["pendientes"] == 31
    assert sc["deuda_horas_estimada"] == 0
    assert sc["pilares"]["ACC"]["pct"] == 100
    assert sc["pilares"]["TEC"]["pct"] == 100
    assert sc["pilares"]["ONP"]["pct"] == 100
    assert sc["pilares"]["OFF"]["pct"] is None
    assert sc["pilares"]["LEG"]["pct"] == 100


def test_score_fail_critico_dorado():
    reg, _ = score_mod.load_configs()
    crit = next(c for c in reg["checks"] if c["severidad"] == "Crítico")
    checks = [{"id": c["id"], "resultado": "FAIL" if c["id"] == crit["id"] else "PASS"} for c in reg["checks"]]
    sc = score_mod.score(checks)
    assert sc["dictamen"] == "NEGATIVO"
    assert sc["fails_criticos"] == 1


# ---------------------------------------------------------------- errores


def test_audit_html_corrupto_degrada_sin_abortar():
    res = audit_page.audit(file=os.path.join(FIX, "page_corrupt.html"))
    assert res["error"] is None  # degradación: parse parcial, no error fatal
    assert len(res["checks"]) > 0


def test_audit_timeout_simulado_exit_2(monkeypatch, capsys):
    def _boom(url, timeout=20):
        raise TimeoutError("timed out (simulado)")

    monkeypatch.setattr(audit_page, "fetch", _boom)
    res = audit_page.audit(url="https://ejemplo.test/")
    assert res["error"] is not None and "TimeoutError" in res["error"]
    assert res["checks"] == []
    assert audit_page.main(["https://ejemplo.test/"]) == 2


def test_audit_dns_simulado_exit_2(monkeypatch):
    def _boom(url, timeout=20):
        raise urllib.error.URLError("Name or service not known (simulado)")

    monkeypatch.setattr(audit_page, "fetch", _boom)
    res = audit_page.audit(url="https://ejemplo.test/")
    assert "URLError" in res["error"]
    assert audit_page.main(["https://ejemplo.test/"]) == 2


def test_score_json_invalido_exit_2(capsys):
    assert score_mod.main([os.path.join(FIX, "invalid.json")]) == 2


def test_score_no_dict_exit_2(tmp_path, capsys):
    p = tmp_path / "lista.json"
    p.write_text("[1, 2]", encoding="utf-8")
    assert score_mod.main([str(p)]) == 2


def test_report_json_invalido_exit_2(capsys):
    assert report_mod.main([os.path.join(FIX, "invalid.json")]) == 2


def test_report_scoring_incompleto_exit_1(tmp_path, capsys):
    p = tmp_path / "casi.json"
    p.write_text(json.dumps({"target": "x"}), encoding="utf-8")
    assert report_mod.main([str(p)]) == 1  # falta dictamen/pilares/hallazgos


def test_report_pipeline_dorado(tmp_path, capsys):
    res = audit_page.audit(file=os.path.join(FIX, "page_pass.html"))
    checks_path = tmp_path / "checks.json"
    checks_path.write_text(json.dumps(res), encoding="utf-8")
    md_path = tmp_path / "informe.md"
    assert report_mod.main([str(checks_path), "--from-checks", "--md", str(md_path)]) == 0
    md = md_path.read_text(encoding="utf-8")
    assert "POSITIVO" in md and "Cumplimiento global: **100%**" in md
