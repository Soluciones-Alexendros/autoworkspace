#!/usr/bin/env python3
"""Scoring de compliance: % por pilar, semáforo y dictamen POSITIVO/PARCIAL/NEGATIVO.

Entrada: JSON de resultados con la forma:
{
  "target": "https://ejemplo.com",
  "checks": [
    {"id": "ACC-01", "resultado": "PASS|FAIL|WARN|NA|PENDING",
     "evidencia": "...", "accion": "..."}
  ]
}
(Si un check no lleva "id", se resuelve por script_key contra configs/checks.json;
resultados de scripts/audit_page.py se aceptan directamente.)

Uso:
    python3 score.py resultados.json [--config DIR_CONFIGS] [--json salida.json]
"""

import argparse
import json
import logging
import os
import sys
from typing import Any

logger = logging.getLogger("auditoria360.score")

RESULTADOS_VALIDOS = {"PASS", "FAIL", "WARN", "NA", "PENDING"}
# WARN cuenta como FAIL a efectos de dictamen (evidencia de incumplimiento parcial)


def _load_json(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except OSError as e:
        raise RuntimeError(f"no se pudo leer {path}: {type(e).__name__}: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"JSON inválido en {path}: {e}") from e


def load_configs(config_dir: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    base = config_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configs")
    checks = _load_json(os.path.join(base, "checks.json"))
    thresholds = _load_json(os.path.join(base, "thresholds.json"))
    return checks, thresholds


def normalizar(resultados: list[dict[str, Any]], registry: dict[str, Any]) -> dict[str, Any]:
    """Devuelve {check_id: resultado} fusionando entradas por id o script_key."""
    by_key = {c["script_key"]: c["id"] for c in registry["checks"] if c.get("script_key")}
    mapa: dict[str, Any] = {}
    for item in resultados:
        cid = item.get("id") or by_key.get(item.get("script_key"))
        if not cid:
            continue
        estado = (item.get("resultado") or item.get("status") or "PENDING").upper()
        if estado not in RESULTADOS_VALIDOS:
            estado = "PENDING"
        # Prioridad: un FAIL/WARN nunca es pisado por un PASS posterior
        prev = mapa.get(cid)
        if prev and prev["resultado"] in ("FAIL", "WARN") and estado == "PASS":
            continue
        mapa[cid] = {
            "id": cid,
            "resultado": estado,
            "evidencia": item.get("evidencia", ""),
            "accion": item.get("accion") or item.get("detalle", ""),
        }
    return mapa


def score(resultados: list[dict[str, Any]], config_dir: str | None = None) -> dict[str, Any]:
    registry, thresholds = load_configs(config_dir)
    mapa = normalizar(resultados, registry)
    reg_by_id = {c["id"]: c for c in registry["checks"]}

    pilares: dict[str, Any] = {}
    hallazgos: list[dict[str, Any]] = []
    deuda_horas = 0
    for cid, c in reg_by_id.items():
        r = mapa.get(cid, {"resultado": "PENDING", "evidencia": "", "accion": ""})
        p = pilares.setdefault(c["pilar"], {"pass": 0, "fail": 0, "pending": 0, "na": 0})
        estado = r["resultado"]
        if estado == "PASS":
            p["pass"] += 1
        elif estado == "NA":
            p["na"] += 1
        elif estado == "PENDING":
            p["pending"] += 1
        else:  # FAIL o WARN
            p["fail"] += 1
            horas = c.get("esfuerzo_h") or thresholds["severidad_horas_defecto"].get(c["severidad"], 4)
            deuda_horas += horas
            hallazgos.append(
                {
                    "id": cid,
                    "pilar": c["pilar"],
                    "criterio": c["criterio"],
                    "estandar": c["estandar"],
                    "severidad": c["severidad"],
                    "resultado": estado,
                    "evidencia": r.get("evidencia", ""),
                    "accion": r.get("accion", ""),
                    "esfuerzo_h": horas,
                }
            )

    por_pilar = {}
    global_pass = global_eval = 0
    for pid, p in pilares.items():
        evaluables = p["pass"] + p["fail"]
        pct = round(100 * p["pass"] / evaluables) if evaluables else None
        meta = registry["pilares"][pid]
        por_pilar[pid] = {
            "nombre": meta["nombre"],
            "peso": meta["peso"],
            "pass": p["pass"],
            "fail": p["fail"],
            "na": p["na"],
            "pending": p["pending"],
            "pct": pct,
            "semaforo": (
                "SIN DATOS"
                if pct is None
                else "VERDE"
                if pct >= thresholds["semaforo"]["verde"]
                else "AMBAR"
                if pct >= thresholds["semaforo"]["ambar"]
                else "ROJO"
            ),
        }
        global_pass += p["pass"]
        global_eval += evaluables

    pct_global = round(100 * global_pass / global_eval) if global_eval else None

    # Dictamen
    reglas = thresholds["dictamen"]["positivo"]
    fails_criticos = [h for h in hallazgos if h["severidad"] == "Crítico" and h["resultado"] == "FAIL"]
    if fails_criticos:
        dictamen = "NEGATIVO"
        motivo = f"{len(fails_criticos)} FAIL crítico(s): " + ", ".join(h["id"] for h in fails_criticos)
    elif pct_global is None:
        dictamen = "SIN DATOS"
        motivo = "No hay checks evaluables"
    else:
        incumple_pilar = [
            pid
            for pid, umbral in reglas["min_pct_pilar"].items()
            if por_pilar.get(pid, {}).get("pct") is not None and por_pilar[pid]["pct"] < umbral
        ]
        if pct_global >= reglas["min_pct_global"] and not incumple_pilar:
            dictamen = "POSITIVO"
            motivo = "0 FAIL críticos y umbrales por pilar superados"
        elif pct_global >= thresholds["dictamen"]["parcial"]["min_pct_global"]:
            dictamen = "PARCIAL"
            motivo = f"Global {pct_global}% bajo umbral {reglas['min_pct_global']}%" + (
                f"; pilares bajo umbral: {', '.join(incumple_pilar)}" if incumple_pilar else ""
            )
        else:
            dictamen = "NEGATIVO"
            motivo = f"Cumplimiento global {pct_global}% bajo mínimo"

    sev_orden = {"Crítico": 0, "Alto": 1, "Medio": 2, "Bajo": 3}
    hallazgos.sort(key=lambda h: (sev_orden.get(h["severidad"], 9), h["id"]))

    return {
        "target": None,
        "dictamen": dictamen,
        "motivo_dictamen": motivo,
        "pct_global": pct_global,
        "pilares": por_pilar,
        "fails_criticos": len(fails_criticos),
        "total_hallazgos": len(hallazgos),
        "deuda_horas_estimada": deuda_horas,
        "pendientes": sum(p["pending"] for p in pilares.values()),
        "hallazgos": hallazgos,
    }


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(description="Scoring de compliance Auditoría 360°")
    ap.add_argument("resultados", help="JSON con checks evaluados")
    ap.add_argument("--config", help="Directorio de configs (por defecto ../configs)")
    ap.add_argument("--json", help="Guardar scoring en JSON")
    args = ap.parse_args(argv)

    try:
        data = _load_json(args.resultados)
    except RuntimeError as e:
        logger.error("%s", e)
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        return 2
    if not isinstance(data, dict):
        logger.error("formato inválido en %s: se esperaba objeto con 'checks'", args.resultados)
        print(
            json.dumps(
                {"error": f"Formato inválido en {args.resultados}: se esperaba objeto con 'checks'"}, ensure_ascii=False
            )
        )
        return 2
    try:
        out = score(data.get("checks", []), config_dir=args.config)
    except RuntimeError as e:
        logger.error("%s", e)
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        return 2
    except (KeyError, TypeError, AttributeError) as e:
        logger.error("configs o resultados inválidos: %s: %s", type(e).__name__, e)
        print(json.dumps({"error": f"Datos inválidos: {type(e).__name__}: {e}"}, ensure_ascii=False))
        return 2
    out["target"] = data.get("target")
    txt = json.dumps(out, ensure_ascii=False, indent=2)
    if args.json:
        try:
            with open(args.json, "w", encoding="utf-8") as fh:
                fh.write(txt)
        except OSError as e:
            logger.error("no se pudo escribir %s: %s: %s", args.json, type(e).__name__, e)
            print(txt)
            return 2
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
