#!/usr/bin/env python3
"""Genera el informe de cierre en Markdown a partir del JSON de scoring.

Uso:
    python3 report.py scoring.json --md informe.md
    python3 report.py resultados.json --from-checks   # calcula scoring internamente
"""

import argparse
import contextlib
import datetime
import importlib.util
import json
import logging
import os
import sys
from typing import Any

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

ICONO = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "NA": "\u2796", "PENDING": "🔎"}
SEMAFORO = {"VERDE": "🟢", "AMBAR": "🟠", "ROJO": "🔴", "SIN DATOS": "⚪"}
SPRINT = {
    "Crítico": "Sprint 1 (<72h)",
    "Alto": "Sprint 2 (<2-6 semanas)",
    "Medio": "Sprint 3 (<7-12 semanas)",
    "Bajo": "Backlog",
}


def render(sc: dict[str, Any]) -> str:
    fecha = datetime.date.today().isoformat()
    lines: list[str] = []
    lines.append("# INFORME DE CIERRE — AUDITORÍA 360°")
    lines.append(f"**Objetivo:** {sc.get('target') or '(sin especificar)'}  ")
    lines.append(f"**Fecha:** {fecha}  ")
    lines.append("**Estándares:** WCAG 2.2 AA · EN 301 549 · Google Search Essentials · Consent Mode v2 · RGPD\n")

    lines.append("## 1. Resumen ejecutivo\n")
    pct = sc["pct_global"]
    lines.append(f"- **Dictamen: {sc['dictamen']}** — {sc['motivo_dictamen']}")
    lines.append(f"- Cumplimiento global: **{pct}%**" if pct is not None else "- Cumplimiento global: SIN DATOS")
    lines.append(
        f"- FAIL críticos: **{sc['fails_criticos']}** · Hallazgos totales: {sc['total_hallazgos']}"
        f" · Pendientes de verificación: {sc['pendientes']}"
    )
    lines.append(f"- Deuda técnica estimada: **~{sc['deuda_horas_estimada']} h**\n")

    lines.append("## 2. Semáforo por pilar\n")
    lines.append("| Pilar | PASS | FAIL | N/A | Pend. | % | Semáforo |")
    lines.append("|---|---|---|---|---|---|---|")
    for pid, p in sc["pilares"].items():
        pct_txt = f"{p['pct']}%" if p["pct"] is not None else "—"
        lines.append(
            f"| {pid} — {p['nombre']} | {p['pass']} | {p['fail']} | {p['na']} "
            f"| {p['pending']} | {pct_txt} | {SEMAFORO[p['semaforo']]} {p['semaforo']} |"
        )
    lines.append("")

    lines.append("## 3. Hallazgos y acciones correctivas (priorización por severidad)\n")
    if not sc["hallazgos"]:
        lines.append("Sin hallazgos FAIL/WARN. ✅\n")
    for h in sc["hallazgos"]:
        lines.append(f"### {ICONO[h['resultado']]} {h['id']} — {h['criterio']}")
        sev = h["severidad"]
        pilar = h["pilar"]
        sprint = SPRINT.get(sev, "Backlog")
        lines.append(f"- **Severidad:** {sev} · **Pilar:** {pilar} · **Sprint:** {sprint}")
        lines.append(f"- **Estándar:** {h['estandar']}")
        if h["evidencia"]:
            lines.append(f"- **Evidencia:** {h['evidencia']}")
        if h["accion"]:
            lines.append(f"- **Acción correctiva:** {h['accion']}")
        lines.append(f"- **Esfuerzo estimado:** ~{h['esfuerzo_h']} h")
        lines.append("")

    lines.append("## 4. Check de verificación de cumplimiento — cierre\n")
    ok = sc["fails_criticos"] == 0 and sc["dictamen"] == "POSITIVO"
    lines.append("| Verificación | Resultado |")
    lines.append("|---|---|")
    lines.append(f"| 0 FAIL críticos en Accesibilidad y Técnico | {'✅' if sc['fails_criticos'] == 0 else '❌'} |")
    for _pid, p in sc["pilares"].items():
        if p["pct"] is None:
            lines.append(f"| {p['nombre']} evaluado | \u2796 sin datos |")
        else:
            lines.append(f"| {p['nombre']}: {p['pct']}% PASS | {'✅' if p['semaforo'] == 'VERDE' else '❌'} |")
    lines.append(f"| **Dictamen global** | **{'✅ POSITIVO' if ok else '❌ ' + sc['dictamen']}** |")
    lines.append("")
    lines.append("## 5. Próximos pasos\n")
    lines.append("1. Ejecutar Sprint 1 (FAIL críticos) y re-auditar de forma parcial.")
    lines.append("2. Completar checks 🔎 PENDING con los protocolos manuales de references/.")
    lines.append("3. Aplicar roadmap RICE completo y mejoras proactivas (references/remediation.md).")
    lines.append("4. Fijar re-auditoría trimestral y declaración de accesibilidad (EN 301 549).")
    return "\n".join(lines) + "\n"


def _load_input(path: str) -> tuple[Any, int | None]:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh), None
    except OSError as e:
        logger.error("no se pudo leer %s: %s: %s", path, type(e).__name__, e)
        return None, 2
    except json.JSONDecodeError as e:
        logger.error("JSON inválido en %s: %s", path, e)
        return None, 2


def _build_scoring(data: Any, args: argparse.Namespace) -> dict[str, Any]:
    if args.from_checks:
        if not isinstance(data, dict):
            raise ValueError("con --from-checks la entrada debe ser objeto con 'checks'")
        sc: dict[str, Any] = score(data.get("checks", []), config_dir=args.config)
        sc["target"] = data.get("target")
        return sc
    if not isinstance(data, dict):
        raise ValueError("el JSON de scoring debe ser un objeto")
    for clave in ("dictamen", "pilares", "hallazgos"):
        if clave not in data:
            raise ValueError(f"el JSON de scoring no trae '{clave}' (¿olvidaste --from-checks?)")
    return data


def _write_report(path: str, md: str) -> int | None:
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(md)
    except OSError as e:
        logger.error("no se pudo escribir %s: %s: %s", path, type(e).__name__, e)
        print(md)
        return 2
    return None


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(description="Informe de cierre Auditoría 360°")
    ap.add_argument("entrada", help="JSON de scoring (o de checks con --from-checks)")
    ap.add_argument("--from-checks", action="store_true", help="La entrada es JSON de checks; calcula el scoring")
    ap.add_argument("--config", help="Directorio de configs")
    ap.add_argument("--md", help="Guardar informe Markdown")
    args = ap.parse_args(argv)

    data, rc = _load_input(args.entrada)
    if rc is not None:
        return rc
    try:
        md = render(_build_scoring(data, args))
    except (ValueError, KeyError, TypeError, AttributeError) as e:
        logger.error("no se pudo generar el informe: %s: %s", type(e).__name__, e)
        return 1
    except RuntimeError as e:
        logger.error("%s", e)
        return 2
    if args.md:
        write_rc = _write_report(args.md, md)
        if write_rc is not None:
            return write_rc
    with contextlib.suppress(BrokenPipeError):
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
