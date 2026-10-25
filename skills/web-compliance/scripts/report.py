#!/usr/bin/env python3
"""Genera el informe de cierre en Markdown a partir del JSON de scoring.

Uso:
    python3 report.py scoring.json --md informe.md
    python3 report.py resultados.json --from-checks   # calcula scoring internamente
"""

import argparse
import datetime
import importlib.util
import json
import logging
import os
import sys

# Cargar score desde el mismo directorio para evitar conflictos de imports
_SCRIPTS_DIR = os.path.dirname(__file__)
_score_path = os.path.join(_SCRIPTS_DIR, "score.py")
_score_spec = importlib.util.spec_from_file_location("web_compliance_score", _score_path)
if _score_spec is None or _score_spec.loader is None:
    raise ImportError(f"Could not load score module from {_score_path}")
_score_module = importlib.util.module_from_spec(_score_spec)
_score_spec.loader.exec_module(_score_module)
score = _score_module.score

logger = logging.getLogger("auditoria360.report")

ICONO = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "NA": "➖", "PENDING": "🔎"}
SEMAFORO = {"VERDE": "🟢", "AMBAR": "🟠", "ROJO": "🔴", "SIN DATOS": "⚪"}
SPRINT = {
    "Crítico": "Sprint 1 (<72h)",
    "Alto": "Sprint 2 (<2-6 semanas)",
    "Medio": "Sprint 3 (<7-12 semanas)",
    "Bajo": "Backlog",
}


def render(sc):
    fecha = datetime.date.today().isoformat()
    L = []
    L.append(f"# INFORME DE CIERRE — AUDITORÍA 360°")
    L.append(f"**Objetivo:** {sc.get('target') or '(sin especificar)'}  ")
    L.append(f"**Fecha:** {fecha}  ")
    L.append(f"**Estándares:** WCAG 2.2 AA · EN 301 549 · Google Search Essentials · Consent Mode v2 · RGPD\n")

    L.append("## 1. Resumen ejecutivo\n")
    pct = sc["pct_global"]
    L.append(f"- **Dictamen: {sc['dictamen']}** — {sc['motivo_dictamen']}")
    L.append(f"- Cumplimiento global: **{pct}%**" if pct is not None else "- Cumplimiento global: SIN DATOS")
    L.append(
        f"- FAIL críticos: **{sc['fails_criticos']}** · Hallazgos totales: {sc['total_hallazgos']}"
        f" · Pendientes de verificación: {sc['pendientes']}"
    )
    L.append(f"- Deuda técnica estimada: **~{sc['deuda_horas_estimada']} h**\n")

    L.append("## 2. Semáforo por pilar\n")
    L.append("| Pilar | PASS | FAIL | N/A | Pend. | % | Semáforo |")
    L.append("|---|---|---|---|---|---|---|")
    for pid, p in sc["pilares"].items():
        pct_txt = f"{p['pct']}%" if p["pct"] is not None else "—"
        L.append(
            f"| {pid} — {p['nombre']} | {p['pass']} | {p['fail']} | {p['na']} "
            f"| {p['pending']} | {pct_txt} | {SEMAFORO[p['semaforo']]} {p['semaforo']} |"
        )
    L.append("")

    L.append("## 3. Hallazgos y acciones correctivas (priorización por severidad)\n")
    if not sc["hallazgos"]:
        L.append("Sin hallazgos FAIL/WARN. ✅\n")
    for h in sc["hallazgos"]:
        L.append(f"### {ICONO[h['resultado']]} {h['id']} — {h['criterio']}")
        L.append(
            f"- **Severidad:** {h['severidad']} · **Pilar:** {h['pilar']} · **Sprint:** {SPRINT.get(h['severidad'], 'Backlog')}"
        )
        L.append(f"- **Estándar:** {h['estandar']}")
        if h["evidencia"]:
            L.append(f"- **Evidencia:** {h['evidencia']}")
        if h["accion"]:
            L.append(f"- **Acción correctiva:** {h['accion']}")
        L.append(f"- **Esfuerzo estimado:** ~{h['esfuerzo_h']} h")
        L.append("")

    L.append("## 4. Check de verificación de cumplimiento — cierre\n")
    ok = sc["fails_criticos"] == 0 and sc["dictamen"] == "POSITIVO"
    L.append("| Verificación | Resultado |")
    L.append("|---|---|")
    L.append(f"| 0 FAIL críticos en Accesibilidad y Técnico | {'✅' if sc['fails_criticos'] == 0 else '❌'} |")
    for pid, p in sc["pilares"].items():
        if p["pct"] is None:
            L.append(f"| {p['nombre']} evaluado | ➖ sin datos |")
        else:
            L.append(f"| {p['nombre']}: {p['pct']}% PASS | {'✅' if p['semaforo'] == 'VERDE' else '❌'} |")
    L.append(f"| **Dictamen global** | **{'✅ POSITIVO' if ok else '❌ ' + sc['dictamen']}** |")
    L.append("")
    L.append("## 5. Próximos pasos\n")
    L.append("1. Ejecutar Sprint 1 (FAIL críticos) y re-auditar de forma parcial.")
    L.append("2. Completar checks 🔎 PENDING con los protocolos manuales de references/.")
    L.append("3. Aplicar roadmap RICE completo y mejoras proactivas (references/remediation.md).")
    L.append("4. Fijar re-auditoría trimestral y declaración de accesibilidad (EN 301 549).")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(description="Informe de cierre Auditoría 360°")
    ap.add_argument("entrada", help="JSON de scoring (o de checks con --from-checks)")
    ap.add_argument("--from-checks", action="store_true", help="La entrada es JSON de checks; calcula el scoring")
    ap.add_argument("--config", help="Directorio de configs")
    ap.add_argument("--md", help="Guardar informe Markdown")
    args = ap.parse_args(argv)

    try:
        with open(args.entrada, encoding="utf-8") as fh:
            data = json.load(fh)
    except OSError as e:
        logger.error("no se pudo leer %s: %s: %s", args.entrada, type(e).__name__, e)
        return 2
    except json.JSONDecodeError as e:
        logger.error("JSON inválido en %s: %s", args.entrada, e)
        return 2
    try:
        if args.from_checks:
            if not isinstance(data, dict):
                raise ValueError("con --from-checks la entrada debe ser objeto con 'checks'")
            sc = score(data.get("checks", []), config_dir=args.config)
            sc["target"] = data.get("target")
        else:
            if not isinstance(data, dict):
                raise ValueError("el JSON de scoring debe ser un objeto")
            sc = data
            for clave in ("dictamen", "pilares", "hallazgos"):
                if clave not in sc:
                    raise ValueError(f"el JSON de scoring no trae '{clave}' (¿olvidaste --from-checks?)")
        md = render(sc)
    except (ValueError, KeyError, TypeError, AttributeError) as e:
        logger.error("no se pudo generar el informe: %s: %s", type(e).__name__, e)
        return 1
    except RuntimeError as e:
        logger.error("%s", e)
        return 2
    if args.md:
        try:
            with open(args.md, "w", encoding="utf-8") as fh:
                fh.write(md)
        except OSError as e:
            logger.error("no se pudo escribir %s: %s: %s", args.md, type(e).__name__, e)
            print(md)
            return 2
    try:
        print(md)
    except BrokenPipeError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
