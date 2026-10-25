#!/usr/bin/env python3
"""Suite de tests integrada de la skill auditoria-360-web.

Valida configs, fixtures, cada script y el pipeline completo (audit → score → report).
Ejecutar tras cualquier cambio:  python3 scripts/selftest.py

Código de salida: 0 = todos los tests PASS; 1 = algún FAIL (detalle en stdout).
Los fallos conocidos y su resolución están documentados en references/troubleshooting.md.

NOTA DE DISEÑO (hardening 2026): se mantiene como *smoke ejecutable* con exit
codes 0/1 y logging a stderr, sin dependencia de pytest, porque corre en
entornos mínimos y aúna pipeline end-to-end. Los tests pytest reales
(asserts granulares, fixtures dorados, errores simulados sin red) viven en
tests/test_*.py. No importar este módulo desde pytest: los decoradores @test
se ejecutan en tiempo de importación por diseño.
"""

import argparse
import logging
import os
import sys

logger = logging.getLogger("auditoria360.selftest")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")
sys.path.insert(0, HERE)

import audit_page  # noqa: E402
import contrast  # noqa: E402
import report as report_mod  # noqa: E402
import score as score_mod  # noqa: E402

RESULTADOS = []


def test(nombre):
    def deco(fn):
        try:
            fn()
            RESULTADOS.append((nombre, "PASS", ""))
        except AssertionError as e:
            logger.warning("FAIL %s: %s", nombre, e)
            RESULTADOS.append((nombre, "FAIL", str(e)))
        except Exception as e:  # un test nunca debe interrumpir la suite
            logger.warning("ERROR %s: %s: %s", nombre, type(e).__name__, e)
            RESULTADOS.append((nombre, "ERROR", f"{type(e).__name__}: {e}"))

    return deco


def _by_key(res):
    return {c["script_key"]: c for c in res["checks"]}


# ---------------------------------------------------------------- configs


@test("configs/checks.json y thresholds.json válidos y coherentes")
def _():
    reg, th = score_mod.load_configs()
    ids = [c["id"] for c in reg["checks"]]
    assert len(ids) == len(set(ids)), "IDs duplicados en el registry"
    assert len(ids) >= 40, f"Registry con {len(ids)} checks (<40)"
    for c in reg["checks"]:
        assert c["pilar"] in reg["pilares"], f"{c['id']} con pilar desconocido {c['pilar']}"
        assert c["severidad"] in ("Crítico", "Alto", "Medio", "Bajo"), f"{c['id']} severidad inválida"
    peso = sum(p["peso"] for p in reg["pilares"].values())
    assert abs(peso - 1.0) < 0.001, f"Pesos de pilares suman {peso} (debe ser 1.0)"


@test("todos los script_key del registry tienen check implementado en audit_page")
def _():
    reg, _ = score_mod.load_configs()
    keys_registry = {c["script_key"] for c in reg["checks"] if c.get("script_key")}
    res = audit_page.audit(file=os.path.join(FIXTURES, "page_pass.html"))
    keys_impl = {c["script_key"] for c in res["checks"]}
    falta = keys_registry - keys_impl
    assert not falta, f"script_key sin implementación: {falta}"


# ---------------------------------------------------------------- audit_page


@test("audit_page: fixture PASS supera checks clave")
def _():
    res = audit_page.audit(file=os.path.join(FIXTURES, "page_pass.html"))
    assert res["error"] is None, f"error inesperado: {res['error']}"
    c = _by_key(res)
    for k in (
        "title",
        "meta_description",
        "canonical",
        "headings",
        "img_alt_coverage",
        "html_lang",
        "viewport",
        "skip_link",
        "form_labels",
        "jsonld",
        "content_parity",
        "charset",
    ):
        assert c[k]["status"] == "PASS", f"{k} = {c[k]['status']} ({c[k]['evidencia']})"


@test("audit_page: fixture FAIL detecta violaciones clave")
def _():
    res = audit_page.audit(file=os.path.join(FIXTURES, "page_fail.html"))
    c = _by_key(res)
    esperado_fail = ["html_lang", "viewport", "skip_link", "jsonld", "headings", "title"]
    for k in esperado_fail:
        assert c[k]["status"] in ("FAIL", "WARN"), f"{k} debería fallar: {c[k]}"
    assert c["form_labels"]["status"] in ("FAIL", "WARN"), "labels deberían fallar"
    assert c["img_alt_coverage"]["status"] in ("FAIL", "WARN"), "alt debería fallar"


@test("audit_page: URL inalcanzable produce error controlado y exit 2")
def _():
    res = audit_page.audit(url="https://dominio-que-no-existe-xyz.invalid/")
    assert res["error"] is not None, "debería registrar error de red"
    assert res["checks"] == [], "no debe inventar checks ante fallo de obtención"


@test("audit_page: hreflang válido con x-default y detección de inválido")
def _():
    p = audit_page.PageParser()
    p.feed(
        '<html lang="es"><head>'
        '<link rel="alternate" hreflang="es" href="https://x.com/es/">'
        '<link rel="alternate" hreflang="en" href="https://x.com/en/">'
        '<link rel="alternate" hreflang="x-default" href="https://x.com/">'
        "</head><body></body></html>"
    )
    assert audit_page.check_hreflang(p)["status"] == "PASS"
    p2 = audit_page.PageParser()
    p2.feed('<html><head><link rel="alternate" hreflang="ESPAÑOL!" href="x"></head><body></body></html>')
    assert audit_page.check_hreflang(p2)["status"] == "FAIL"


# ---------------------------------------------------------------- contrast


@test("contrast: ratios WCAG de referencia")
def _():
    failures = contrast.selftest()
    assert not failures, "; ".join(failures)


@test("contrast: color inválido devuelve exit 2 sin romper")
def _():
    assert contrast.main(["#zzz", "#fff"]) == 2
    assert contrast.main(["#000", "#fff"]) == 0


# ---------------------------------------------------------------- score


@test("score: todo PASS => dictamen POSITIVO")
def _():
    reg, _ = score_mod.load_configs()
    checks = [{"id": c["id"], "resultado": "PASS"} for c in reg["checks"]]
    sc = score_mod.score(checks)
    assert sc["dictamen"] == "POSITIVO", sc["motivo_dictamen"]
    assert sc["pct_global"] == 100


@test("score: 1 FAIL crítico => NEGATIVO aunque el resto pase")
def _():
    reg, _ = score_mod.load_configs()
    checks = [{"id": c["id"], "resultado": "PASS"} for c in reg["checks"]]
    crit = next(c for c in reg["checks"] if c["severidad"] == "Crítico")
    checks = [{"id": crit["id"], "resultado": "FAIL" if c["id"] == crit["id"] else "PASS"} for c in reg["checks"]]
    sc = score_mod.score(checks)
    assert sc["dictamen"] == "NEGATIVO"
    assert sc["fails_criticos"] == 1


@test("score: N/A se excluye del denominador; WARN cuenta como fallo")
def _():
    reg, _ = score_mod.load_configs()
    checks = [{"id": c["id"], "resultado": "NA"} for c in reg["checks"]]
    checks[0]["resultado"] = "PASS"
    checks[1]["resultado"] = "WARN"
    sc = score_mod.score(checks)
    assert sc["pct_global"] == 50, sc["pct_global"]
    assert sc["dictamen"] in ("PARCIAL", "NEGATIVO")


@test("score: acepta salida directa de audit_page (script_key)")
def _():
    res = audit_page.audit(file=os.path.join(FIXTURES, "page_pass.html"))
    sc = score_mod.score(res["checks"])
    assert sc["pct_global"] is not None
    assert sc["total_hallazgos"] >= 0


@test("score: un FAIL no es pisado por un PASS posterior del mismo check")
def _():
    checks = [{"id": "ACC-04", "resultado": "FAIL"}, {"id": "ACC-04", "resultado": "PASS"}]
    sc = score_mod.score(checks)
    acc04 = [h for h in sc["hallazgos"] if h["id"] == "ACC-04"]
    assert acc04, "ACC-04 debería seguir siendo hallazgo FAIL"


# ---------------------------------------------------------------- report


@test("report: genera Markdown con dictamen, matriz y verificación de cierre")
def _():
    reg, _ = score_mod.load_configs()
    checks = [{"id": c["id"], "resultado": "PASS", "evidencia": "test"} for c in reg["checks"]]
    checks[0]["resultado"] = "FAIL"
    sc = score_mod.score(checks)
    sc["target"] = "https://fixture.test"
    md = report_mod.render(sc)
    for fragmento in ("DICTAMEN", "Dictamen", "Semáforo", "Hallazgos", "verificación"):
        assert fragmento.lower() in md.lower(), f"falta sección '{fragmento}'"
    assert "❌" in md, "el informe debe reflejar el FAIL"


# ---------------------------------------------------------------- main


def main(argv=None) -> int:
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(description="Smoke test integrado de auditoria-360-web (exit 0/1)")
    ap.parse_args(argv)
    print("=" * 60)
    print("SELFTEST auditoria-360-web")
    print("=" * 60)
    fallos = 0
    for nombre, estado, detalle in RESULTADOS:
        icono = {"PASS": "✅", "FAIL": "❌", "ERROR": "💥"}[estado]
        print(f"{icono} {estado:5} {nombre}" + (f" — {detalle}" if detalle else ""))
        if estado != "PASS":
            fallos += 1
    print("=" * 60)
    print(f"{len(RESULTADOS) - fallos}/{len(RESULTADOS)} tests superados")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
