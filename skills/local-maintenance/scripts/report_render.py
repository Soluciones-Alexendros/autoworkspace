#!/usr/bin/env python3
"""report_render.py - Genera informe MD/HTML con puntuación, hallazgos y diff temporal."""

import html as _html
import json
import logging
import os
import sys
from datetime import datetime, timezone

from common import SKILL_VERSION

logger = logging.getLogger("mantenimiento.report")


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s", stream=sys.stderr)
    else:
        logging.getLogger().setLevel(level)


def load_json(path):
    """Carga archivo JSON (None si falta o es inválido; con contexto en stderr)."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("fichero no encontrado: %r", path)
        return None
    except json.JSONDecodeError as exc:
        logger.error("JSON inválido en %r: %s", path, exc)
        return None
    except OSError as exc:
        logger.error("no se pudo leer %r: %s", path, exc)
        return None
    except (UnicodeDecodeError, ValueError) as exc:
        logger.error("contenido inválido en %r: %s", path, exc)
        return None


def load_history(history_dir):
    """Carga historial de auditorías (lista vacía si falta o es inválido)."""
    try:
        index_path = os.path.join(history_dir, "index.json")
    except (TypeError, ValueError) as exc:
        logger.error("history_dir inválido %r: %s", history_dir, exc)
        return []
    if not os.path.exists(index_path):
        return []
    data = load_json(index_path)
    if not data:
        return []
    try:
        return data.get("runs", [])
    except AttributeError as exc:
        logger.error("formato de historial inválido en %r: %s", index_path, exc)
        return []


def calculate_trend(current_score, previous_score):
    """Calcula tendencia del health score."""
    if previous_score is None:
        return "first_run"
    delta = current_score - previous_score
    if delta > 5:
        return "improving"
    elif delta < -5:
        return "degrading"
    else:
        return "stable"


def severity_emoji(severity):
    """Devuelve emoji para severidad."""
    return {"P0": "🔴", "P1": "🟠", "P2": "🟡", "P3": "🔵", "P4": "⚪"}.get(severity, "❓")


def severity_color(severity):
    """Devuelve color HTML para severidad."""
    return {
        "P0": "#dc3545",
        "P1": "#fd7e14",
        "P2": "#ffc107",
        "P3": "#0d6efd",
        "P4": "#6c757d",
    }.get(severity, "#000")


def _is_bad(finding) -> bool:
    return isinstance(finding, dict) and finding.get("status") in ("FAIL", "WARN")


def _finding_label(finding) -> str:
    if not isinstance(finding, dict):
        return "?"
    return f"{finding.get('id', '?')} — {finding.get('title', 'sin titulo')}"


def diff_findings(prev_findings, curr_findings) -> dict:
    """Diff temporal entre dos listas de hallazgos.

    nuevos: FAIL/WARN ahora, antes PASS/ausente. resueltos: FAIL/WARN antes,
    ahora PASS/ausente. persistentes: FAIL/WARN en ambos. regresados: PASS
    antes y FAIL/WARN ahora (subconjunto de nuevos que existian como PASS).
    """
    prev = prev_findings if isinstance(prev_findings, list) else []
    curr = curr_findings if isinstance(curr_findings, list) else []
    prev_by_id = {f.get("id"): f for f in prev if isinstance(f, dict) and f.get("id")}
    curr_by_id = {f.get("id"): f for f in curr if isinstance(f, dict) and f.get("id")}
    nuevos, resueltos, persistentes, regresados = [], [], [], []
    for fid, f in curr_by_id.items():
        if not _is_bad(f):
            continue
        prev_f = prev_by_id.get(fid)
        if prev_f is None or not _is_bad(prev_f):
            nuevos.append(_finding_label(f))
            if prev_f is not None:
                regresados.append(_finding_label(f))
        else:
            persistentes.append(_finding_label(f))
    for fid, f in prev_by_id.items():
        if _is_bad(f) and not _is_bad(curr_by_id.get(fid)):
            resueltos.append(_finding_label(f))
    return {
        "nuevos": sorted(nuevos),
        "resueltos": sorted(resueltos),
        "persistentes": sorted(persistentes),
        "regresados": sorted(regresados),
    }


def _extract_prev_findings(history, prev_data) -> list | None:
    if isinstance(prev_data, dict) and isinstance(prev_data.get("findings"), list):
        return prev_data["findings"]
    if isinstance(history, list):
        for run in reversed(history):
            if isinstance(run, dict) and isinstance(run.get("findings"), list):
                return run["findings"]
    return None


def render_markdown(data, history=None, prev_data=None):
    """Genera informe en Markdown."""
    meta = data.get("metadata", {})
    hs = data.get("health_score", {})
    findings = data.get("findings", [])
    summary = data.get("summary", {})

    lines = []
    lines.append("# Informe de Auditoría - mantenimiento-linux")
    lines.append("")
    lines.append(f"**Fecha:** {meta.get('timestamp', 'N/A')}")
    lines.append(f"**Host:** {meta.get('hostname', 'N/A')}")
    lines.append(f"**Modo:** {meta.get('mode', 'N/A')}")
    lines.append(f"**Distro:** {meta.get('distro', 'N/A')} ({meta.get('family', 'N/A')})")
    lines.append(f"**Kernel:** {meta.get('kernel', 'N/A')}")
    lines.append(f"**Duración:** {meta.get('duration_seconds', 'N/A')}s")
    lines.append("")

    # Health Score
    lines.append("## Health Score")
    lines.append("")
    overall = hs.get("overall", 0)
    bar = "█" * (overall // 5) + "░" * (20 - overall // 5)
    lines.append(f"**Overall: {overall}/100**")
    lines.append(f"`{bar}`")
    lines.append("")
    lines.append("| Componente | Puntuación | Peso |")
    lines.append("|------------|-----------|------|")
    lines.append(f"| Seguridad | {hs.get('security', 0)}/100 | 35% |")
    lines.append(f"| Actualización | {hs.get('updates', 0)}/100 | 25% |")
    lines.append(f"| Higiene | {hs.get('hygiene', 0)}/100 | 20% |")
    lines.append(f"| Recursos | {hs.get('resources', 0)}/100 | 10% |")
    lines.append(f"| Estabilidad | {hs.get('stability', 0)}/100 | 10% |")
    lines.append("")

    # Tendencia
    if history and len(history) >= 2:
        prev = history[-2]
        prev_score = (
            prev.get("health_score", {}).get("overall", 0) if isinstance(prev, dict) else prev.get("health_score", 0)
        )
        trend = calculate_trend(overall, prev_score)
        trend_labels = {
            "improving": "📈 Mejorando",
            "degrading": "📉 Degradando",
            "stable": "➡️ Estable",
            "first_run": "🆕 Primera ejecución",
        }
        lines.append(f"**Tendencia:** {trend_labels.get(trend, trend)} (anterior: {prev_score})")
        lines.append("")

    # Resumen
    lines.append("## Resumen")
    lines.append("")
    lines.append(f"- **Total checks:** {summary.get('total_checks', 0)}")
    lines.append(f"- **Passed:** {summary.get('passed', 0)}")
    lines.append(f"- **Failed:** {summary.get('failed', 0)}")
    lines.append(f"- **Warned:** {summary.get('warned', 0)}")
    lines.append(f"- **Skipped:** {summary.get('skipped', 0)}")
    lines.append(f"- **Errors:** {summary.get('errors', 0)}")
    lines.append("")

    # Hallazgos por severidad
    by_sev = summary.get("by_severity", {})
    lines.append("### Por severidad")
    lines.append("")
    for sev in ["P0", "P1", "P2", "P3", "P4"]:
        count = by_sev.get(sev, 0)
        lines.append(f"- {severity_emoji(sev)} **{sev}:** {count}")
    lines.append("")

    # Diff temporal contra auditoria previa (--prev o historial con findings)
    prev_findings = _extract_prev_findings(history, prev_data)
    if prev_findings is not None:
        diff = diff_findings(prev_findings, findings)
        lines.append("## Diff temporal (vs auditoria previa)")
        lines.append("")
        for key, label in (
            ("nuevos", "🆕 Nuevos"),
            ("resueltos", "✅ Resueltos"),
            ("persistentes", "🔁 Persistentes"),
            ("regresados", "⚠️ Regresados"),
        ):
            items = diff[key]
            lines.append(f"### {label} ({len(items)})")
            lines.append("")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")

    # Hallazgos detallados
    if findings:
        lines.append("## Hallazgos")
        lines.append("")
        for sev in ["P0", "P1", "P2", "P3", "P4"]:
            sev_findings = [f for f in findings if f.get("severity") == sev]
            if not sev_findings:
                continue
            lines.append(f"### {severity_emoji(sev)} {sev} ({len(sev_findings)})")
            lines.append("")
            for f in sev_findings:
                lines.append(f"**{f.get('title', 'Sin título')}**")
                lines.append(f"- ID: `{f.get('id', 'N/A')}`")
                lines.append(f"- Categoría: {f.get('category', 'N/A')}")
                lines.append(f"- Estado: {f.get('status', 'N/A')}")
                if f.get("description"):
                    lines.append(f"- Descripción: {_html.escape(f.get('description'))}")
                if f.get("evidence"):
                    lines.append(f"- Evidencia: `{_html.escape(f.get('evidence'))}`")
                if f.get("remediation"):
                    lines.append(f"- Remediación: {_html.escape(f.get('remediation'))}")
                lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"*Generado por mantenimiento-linux v{SKILL_VERSION}*")

    return "\n".join(lines)


def render_html(data, history=None, prev_data=None):
    """Genera informe HTML."""
    meta = data.get("metadata", {})
    hs = data.get("health_score", {})
    findings = data.get("findings", [])
    summary = data.get("summary", {})
    overall = hs.get("overall", 0)

    score_color = "#28a745" if overall >= 85 else "#ffc107" if overall >= 70 else "#dc3545"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Informe mantenimiento-linux - {meta.get("hostname", "N/A")}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; line-height: 1.6; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #fff; border-radius: 8px; padding: 24px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header .meta {{ color: #666; font-size: 14px; }}
        .score-card {{ background: #fff; border-radius: 8px; padding: 24px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
        .score-circle {{ width: 120px; height: 120px; border-radius: 50%; background: {score_color}; color: #fff; display: inline-flex; align-items: center; justify-content: center; font-size: 36px; font-weight: bold; }}
        .score-breakdown {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 16px; }}
        .score-item {{ background: #f8f9fa; padding: 12px; border-radius: 6px; text-align: center; }}
        .score-item .label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
        .score-item .value {{ font-size: 24px; font-weight: bold; }}
        .section {{ background: #fff; border-radius: 8px; padding: 24px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .section h2 {{ font-size: 18px; margin-bottom: 16px; border-bottom: 2px solid #eee; padding-bottom: 8px; }}
        .finding {{ border-left: 4px solid #ddd; padding: 12px 16px; margin-bottom: 12px; background: #fafafa; border-radius: 0 4px 4px 0; }}
        .finding.P0 {{ border-left-color: #dc3545; }}
        .finding.P1 {{ border-left-color: #fd7e14; }}
        .finding.P2 {{ border-left-color: #ffc107; }}
        .finding.P3 {{ border-left-color: #0d6efd; }}
        .finding.P4 {{ border-left-color: #6c757d; }}
        .finding h3 {{ font-size: 14px; margin-bottom: 4px; }}
        .finding .detail {{ font-size: 13px; color: #666; }}
        .finding .remediation {{ font-size: 13px; color: #0d6efd; margin-top: 4px; }}
        .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; color: #fff; }}
        .badge.P0 {{ background: #dc3545; }}
        .badge.P1 {{ background: #fd7e14; }}
        .badge.P2 {{ background: #ffc107; color: #333; }}
        .badge.P3 {{ background: #0d6efd; }}
        .badge.P4 {{ background: #6c757d; }}
        .badge.PASS {{ background: #28a745; }}
        .badge.FAIL {{ background: #dc3545; }}
        .badge.WARN {{ background: #ffc107; color: #333; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }}
        .summary-item {{ text-align: center; padding: 8px; background: #f8f9fa; border-radius: 4px; }}
        .summary-item .count {{ font-size: 20px; font-weight: bold; }}
        .summary-item .label {{ font-size: 11px; color: #666; }}
        footer {{ text-align: center; color: #999; font-size: 12px; padding: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Informe de Mantenimiento Linux</h1>
            <div class="meta">
                <strong>Host:</strong> {meta.get("hostname", "N/A")} ·
                <strong>Modo:</strong> {meta.get("mode", "N/A")} ·
                <strong>Distro:</strong> {meta.get("distro", "N/A")} ·
                <strong>Kernel:</strong> {meta.get("kernel", "N/A")} ·
                <strong>Fecha:</strong> {meta.get("timestamp", "N/A")} ·
                <strong>Duración:</strong> {meta.get("duration_seconds", "N/A")}s
            </div>
        </div>

        <div class="score-card">
            <div class="score-circle">{overall}</div>
            <p style="margin-top: 8px; color: #666;">Health Score</p>
            <div class="score-breakdown">
                <div class="score-item">
                    <div class="label">Seguridad</div>
                    <div class="value">{hs.get("security", 0)}</div>
                </div>
                <div class="score-item">
                    <div class="label">Actualización</div>
                    <div class="value">{hs.get("updates", 0)}</div>
                </div>
                <div class="score-item">
                    <div class="label">Higiene</div>
                    <div class="value">{hs.get("hygiene", 0)}</div>
                </div>
                <div class="score-item">
                    <div class="label">Recursos</div>
                    <div class="value">{hs.get("resources", 0)}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Resumen</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="count">{summary.get("total_checks", 0)}</div>
                    <div class="label">Total</div>
                </div>
                <div class="summary-item">
                    <div class="count" style="color: #28a745;">{summary.get("passed", 0)}</div>
                    <div class="label">Passed</div>
                </div>
                <div class="summary-item">
                    <div class="count" style="color: #dc3545;">{summary.get("failed", 0)}</div>
                    <div class="label">Failed</div>
                </div>
                <div class="summary-item">
                    <div class="count" style="color: #ffc107;">{summary.get("warned", 0)}</div>
                    <div class="label">Warned</div>
                </div>
                <div class="summary-item">
                    <div class="count" style="color: #6c757d;">{summary.get("skipped", 0)}</div>
                    <div class="label">Skipped</div>
                </div>
            </div>
            <div style="margin-top: 16px;">
"""

    by_sev = summary.get("by_severity", {})
    for sev in ["P0", "P1", "P2", "P3", "P4"]:
        count = by_sev.get(sev, 0)
        html += f'<span class="badge {sev}">{sev}: {count}</span> '

    html += """
            </div>
        </div>
"""

    if findings:
        html += """        <div class="section">
            <h2>Hallazgos</h2>
"""
        for sev in ["P0", "P1", "P2", "P3", "P4"]:
            sev_findings = [f for f in findings if f.get("severity") == sev]
            if not sev_findings:
                continue
            for f in sev_findings:
                status = f.get("status", "N/A")
                title_text = _html.escape(f.get("title", "Sin título"))
                html += f"""            <div class="finding {sev}">
                <h4><span class="badge {sev}">{sev}</span> <span class="badge {status}">{status}</span> {title_text}</h4>
                <div class="detail"><strong>ID:</strong> {_html.escape(f.get("id", "N/A"))} · <strong>Categoría:</strong> {_html.escape(f.get("category", "N/A"))}</div>
"""
                if f.get("description"):
                    html += f'                <div class="detail">{_html.escape(str(f.get("description", "")))}</div>\n'
                if f.get("evidence"):
                    html += f'                <div class="detail"><strong>Evidencia:</strong> <code>{_html.escape(str(f.get("evidence")))}</code></div>\n'
                if f.get("remediation"):
                    html += f'                <div class="remediation"><strong>Remediación:</strong> {_html.escape(str(f.get("remediation", "")))}</div>\n'
                html += "            </div>\n"
        html += "        </div>\n"

    prev_findings = _extract_prev_findings(history, prev_data)
    if prev_findings is not None:
        diff = diff_findings(prev_findings, findings)
        html += """        <div class="section">
            <h2>Diff temporal (vs auditoria previa)</h2>
"""
        for key, label in (
            ("nuevos", "Nuevos"),
            ("resueltos", "Resueltos"),
            ("persistentes", "Persistentes"),
            ("regresados", "Regresados"),
        ):
            items = diff[key]
            html += f"            <h3>{label} ({len(items)})</h3>\n"
            for item in items:
                html += f"            <div class='detail'>- {_html.escape(item)}</div>\n"
        html += "        </div>\n"

    html += f"""        <footer>
            Generado por mantenimiento-linux v{SKILL_VERSION} · {meta.get("timestamp", "")}
        </footer>
    </div>
</body>
</html>"""

    return html


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Genera informe de mantenimiento-linux")
    parser.add_argument("--input", "-i", required=True, help="Archivo JSON de auditoría")
    parser.add_argument("--output", "-o", default="report.md", help="Archivo de salida")
    parser.add_argument("--format", "-f", choices=["md", "html"], default="md", help="Formato de salida")
    parser.add_argument("--history", help="Directorio de historial")
    parser.add_argument("--prev", default="", help="Auditoria previa JSON para diff temporal")
    parser.add_argument(
        "--mode",
        choices=["report", "optimize"],
        default="report",
        help="Modo de generación",
    )
    parser.add_argument("--verbose", action="store_true", help="Logging verboso a stderr")

    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    data = load_json(args.input)
    if not data:
        logger.error("No se pudo cargar %s", args.input)
        print(f"Error: No se pudo cargar {args.input}", file=sys.stderr)
        return 1

    history = None
    if args.history:
        history = load_history(args.history)

    prev_data = load_json(args.prev) if args.prev else None

    if args.mode == "optimize":
        # Generar plan de optimización basado en hallazgos
        findings = data.get("findings", [])
        lines = []
        lines.append("# Plan de Optimización - mantenimiento-linux")
        lines.append("")
        lines.append(f"**Generado:** {datetime.now(timezone.utc).isoformat()}")
        lines.append("")

        for sev in ["P0", "P1", "P2", "P3"]:
            sev_findings = [f for f in findings if f.get("severity") == sev]
            if not sev_findings:
                continue
            lines.append(f"## {sev} - {len(sev_findings)} acciones")
            lines.append("")
            for f in sev_findings:
                lines.append(f"### {f.get('title', 'Sin título')}")
                lines.append(f"- **ID:** {f.get('id', 'N/A')}")
                lines.append(f"- **Riesgo:** {f.get('risk_level', 'N/A')}")
                lines.append(f"- **Remediación:** {f.get('remediation', 'N/A')}")
                lines.append("")

        output = "\n".join(lines)
        ext = ".md"
    else:
        if args.format == "html":
            output = render_html(data, history, prev_data)
            ext = ".html"
        else:
            output = render_markdown(data, history, prev_data)
            ext = ".md"

    # Asegurar extensión correcta
    out_path = args.output
    if not out_path.endswith(ext):
        out_path = out_path.rsplit(".", 1)[0] + ext

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(output)
    except (OSError, TypeError, ValueError) as exc:
        logger.error("no se pudo escribir %r: %s", out_path, exc)
        print(f"Error: no se pudo escribir {out_path}: {exc}", file=sys.stderr)
        return 1

    print(f"Informe generado: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
