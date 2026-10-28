"""Dorados (valores congelados del código actual) + errores controlados sin red.

Exit codes: 0 OK · 1 error de datos/render · 2 error de uso/IO/red.
Degradación documentada: HTML corrupto no aborta (checks parciales, error None).
"""

import importlib.util
import json
import os
import sys
import urllib.error
from pathlib import Path
from typing import Any

import pytest

# Cargar módulos desde scripts/ explícitamente para evitar colisiones con web-compliance
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")


def _load_module(name: str) -> Any:
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

# Constantes con nombre (P12 T6e): sustituyen literales magicos.
AA_UI_MIN_RATIO = 3.0
PCT_FULL = 100
EXPECTED_PENDING = 31
EXIT_USAGE = 2

# ---------------------------------------------------------------- contrast

CONTRAST_GOLDEN = [
    # (fg, bg, ratio, aa, aaa, veredicto)
    ("#000000", "#FFFFFF", 21.0, True, True, "AAA"),
    ("#767676", "#FFFFFF", 4.54, True, False, "AA"),
    ("#767676", "#FFFF00", 4.23, False, False, "FAIL"),
    ("#777777", "#FFFFFF", 4.48, False, False, "FAIL"),
    ("#1a1a1a", "#ffffff", 17.4, True, True, "AAA"),
]


@pytest.mark.parametrize("caso", CONTRAST_GOLDEN)
def test_contrast_dorado(caso: tuple[Any, Any, float, bool, bool, str]) -> None:
    fg, bg, ratio, aa, aaa, veredicto = caso
    r = contrast.check(fg, bg)
    assert r["ratio"] == pytest.approx(ratio, abs=0.02)
    assert r["aa"] is aa
    assert r["aaa"] is aaa
    assert r["veredicto"] == veredicto
    assert r["aa_ui_components"] == (ratio >= AA_UI_MIN_RATIO)


def test_contrast_selftest_interno_pasa() -> None:
    assert contrast.selftest() == []


# ---------------------------------------------------------------- score


def test_score_page_pass_dorado() -> None:
    res = audit_page.audit(file=os.path.join(FIX, "page_pass.html"))
    assert res["error"] is None
    sc = score_mod.score(res["checks"])
    assert sc["pct_global"] == PCT_FULL
    assert sc["dictamen"] == "POSITIVO"
    assert sc["fails_criticos"] == 0
    assert sc["total_hallazgos"] == 0
    assert sc["pendientes"] == EXPECTED_PENDING
    assert sc["deuda_horas_estimada"] == 0
    assert sc["pilares"]["ACC"]["pct"] == PCT_FULL
    assert sc["pilares"]["TEC"]["pct"] == PCT_FULL
    assert sc["pilares"]["ONP"]["pct"] == PCT_FULL
    assert sc["pilares"]["OFF"]["pct"] is None
    assert sc["pilares"]["LEG"]["pct"] == PCT_FULL


def test_score_fail_critico_dorado() -> None:
    reg, _ = score_mod.load_configs()
    crit = next(c for c in reg["checks"] if c["severidad"] == "Crítico")
    checks = [{"id": c["id"], "resultado": "FAIL" if c["id"] == crit["id"] else "PASS"} for c in reg["checks"]]
    sc = score_mod.score(checks)
    assert sc["dictamen"] == "NEGATIVO"
    assert sc["fails_criticos"] == 1


# ---------------------------------------------------------------- errores


def test_audit_html_corrupto_degrada_sin_abortar() -> None:
    res = audit_page.audit(file=os.path.join(FIX, "page_corrupt.html"))
    assert res["error"] is None  # degradación: parse parcial, no error fatal
    assert len(res["checks"]) > 0


def test_audit_timeout_simulado_exit_2(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def _boom(url: str, timeout: int = 20) -> tuple[str, int, dict[str, str], bytes, float]:
        raise TimeoutError("timed out (simulado)")

    monkeypatch.setattr(audit_page, "fetch", _boom)
    res = audit_page.audit(url="https://ejemplo.test/")
    assert res["error"] is not None and "TimeoutError" in res["error"]
    assert res["checks"] == []
    assert audit_page.main(["https://ejemplo.test/"]) == EXIT_USAGE


def test_audit_dns_simulado_exit_2(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(url: str, timeout: int = 20) -> tuple[str, int, dict[str, str], bytes, float]:
        raise urllib.error.URLError("Name or service not known (simulado)")

    monkeypatch.setattr(audit_page, "fetch", _boom)
    res = audit_page.audit(url="https://ejemplo.test/")
    assert "URLError" in res["error"]
    assert audit_page.main(["https://ejemplo.test/"]) == EXIT_USAGE


def test_score_json_invalido_exit_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert score_mod.main([os.path.join(FIX, "invalid.json")]) == EXIT_USAGE


def test_score_no_dict_exit_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    p = tmp_path / "lista.json"
    p.write_text("[1, 2]", encoding="utf-8")
    assert score_mod.main([str(p)]) == EXIT_USAGE


def test_report_json_invalido_exit_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert report_mod.main([os.path.join(FIX, "invalid.json")]) == EXIT_USAGE


def test_report_scoring_incompleto_exit_1(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    p = tmp_path / "casi.json"
    p.write_text(json.dumps({"target": "x"}), encoding="utf-8")
    assert report_mod.main([str(p)]) == 1  # falta dictamen/pilares/hallazgos


def test_report_pipeline_dorado(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    res = audit_page.audit(file=os.path.join(FIX, "page_pass.html"))
    checks_path = tmp_path / "checks.json"
    checks_path.write_text(json.dumps(res), encoding="utf-8")
    md_path = tmp_path / "informe.md"
    assert report_mod.main([str(checks_path), "--from-checks", "--md", str(md_path)]) == 0
    md = md_path.read_text(encoding="utf-8")
    assert "POSITIVO" in md and "Cumplimiento global: **100%**" in md
