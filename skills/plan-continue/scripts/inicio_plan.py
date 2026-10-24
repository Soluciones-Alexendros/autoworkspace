#!/usr/bin/env python3
"""Punto de partida de un plan: estado git, estructura, roadmap y fallos.

No modifica el repositorio. Escribe inicio.json, ESTADO.md y ESTADO.html en --out.

Uso:
    python3 inicio_plan.py <ruta_repo> [--profile P0|P1|P2] [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import scan_repo  # noqa: E402

logger = logging.getLogger("inicio_plan")

ROADMAP_CANDIDATES = (
    "ROADMAP.md",
    "docs/ROADMAP.md",
    "docs/roadmap.md",
    "ROADMAP.txt",
)


def run_git(repo: str, *args: str) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git", "-C", repo, *args],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    return proc.returncode, (proc.stdout or "").strip()


def git_snapshot(repo: str) -> dict:
    inside_rc, inside = run_git(repo, "rev-parse", "--is-inside-work-tree")
    if inside_rc != 0 or inside != "true":
        return {
            "es_git": False,
            "rama": None,
            "sha": None,
            "sucio": False,
            "adelante": 0,
            "atras": 0,
            "upstream": None,
            "ultimo_commit": None,
        }
    _, rama = run_git(repo, "branch", "--show-current")
    _, sha = run_git(repo, "rev-parse", "--short", "HEAD")
    _, porcelain = run_git(repo, "status", "--porcelain")
    _, upstream = run_git(repo, "rev-parse", "--abbrev-ref", "@{upstream}")
    adelante, atras = 0, 0
    if upstream:
        rc, counts = run_git(repo, "rev-list", "--left-right", "--count", "HEAD...@{upstream}")
        if rc == 0 and counts:
            parts = counts.replace("\t", " ").split()
            if len(parts) == 2:
                adelante, atras = int(parts[0]), int(parts[1])
    _, ultimo = run_git(repo, "log", "-1", "--format=%h %s")
    return {
        "es_git": True,
        "rama": rama or None,
        "sha": sha or None,
        "sucio": bool(porcelain),
        "cambios_sin_commit": len([ln for ln in porcelain.splitlines() if ln.strip()]),
        "adelante": adelante,
        "atras": atras,
        "upstream": upstream or None,
        "ultimo_commit": ultimo or None,
    }


def gh_json(args: list[str]) -> object | None:
    if not shutil.which("gh"):
        return None
    try:
        proc = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    raw = (proc.stdout or "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def github_vista(repo: str) -> dict:
    view = gh_json(
        [
            "repo",
            "view",
            "--json",
            "nameWithOwner,defaultBranchRef,isArchived,url,description",
        ]
    )
    if not isinstance(view, dict):
        return {"disponible": False}
    default = ""
    ref = view.get("defaultBranchRef")
    if isinstance(ref, dict):
        default = ref.get("name") or ""
    prs = gh_json(
        [
            "pr",
            "list",
            "--state",
            "open",
            "--limit",
            "20",
            "--json",
            "number,title,headRefName,isDraft",
        ]
    )
    issues = gh_json(
        [
            "issue",
            "list",
            "--state",
            "open",
            "--limit",
            "20",
            "--json",
            "number,title,labels",
        ]
    )
    runs = []
    if default:
        runs = gh_json(
            [
                "run",
                "list",
                "--branch",
                default,
                "--limit",
                "5",
                "--json",
                "conclusion,status,name,headBranch,databaseId",
            ]
        ) or []
    return {
        "disponible": True,
        "nombre": view.get("nameWithOwner"),
        "url": view.get("url"),
        "descripcion": view.get("description"),
        "archivado": bool(view.get("isArchived")),
        "rama_por_defecto": default,
        "prs_abiertos": prs if isinstance(prs, list) else [],
        "issues_abiertos": issues if isinstance(issues, list) else [],
        "runs_recientes": runs if isinstance(runs, list) else [],
    }


def leer_roadmap_local(repo: str) -> dict:
    root = Path(repo)
    fichero = None
    titulos: list[str] = []
    for rel in ROADMAP_CANDIDATES:
        path = root / rel
        if path.is_file():
            fichero = rel
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                text = ""
            for line in text.splitlines():
                if line.startswith("#"):
                    titulos.append(line.lstrip("#").strip())
                    if len(titulos) >= 12:
                        break
            break
    unreleased: list[str] = []
    changelog = root / "CHANGELOG.md"
    if changelog.is_file():
        try:
            text = changelog.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        in_unreleased = False
        for line in text.splitlines():
            if re.match(r"^## \[Unreleased\]", line, re.I):
                in_unreleased = True
                continue
            if in_unreleased and line.startswith("## "):
                break
            if in_unreleased and line.strip().startswith("- "):
                unreleased.append(line.strip()[2:].strip())
            if len(unreleased) >= 15:
                break
    planes: list[str] = []
    planning = root / ".planning"
    if planning.is_dir():
        for child in sorted(planning.iterdir()):
            plan = child / "task_plan.md" if child.is_dir() else None
            if plan and plan.is_file():
                planes.append(str(child.relative_to(root)))
    return {
        "fichero": fichero,
        "titulos": titulos,
        "unreleased": unreleased,
        "planes_locales": planes,
    }


def estructura(repo: str, profile: str) -> dict:
    sh = SCRIPT_DIR / "check-product-structure.sh"
    try:
        proc = subprocess.run(
            ["bash", str(sh), repo, "--profile", profile],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "codigo": 3, "lineas": [str(exc)], "faltantes": []}
    out = (proc.stdout or "") + (proc.stderr or "")
    lineas = [ln for ln in out.splitlines() if ln.strip()]
    faltantes = [ln for ln in lineas if ln.startswith("FALTA") or ln.startswith("PROHIBIDO")]
    avisos = [ln for ln in lineas if ln.startswith("AVISO")]
    return {
        "ok": proc.returncode == 0,
        "codigo": proc.returncode,
        "lineas": lineas,
        "faltantes": faltantes,
        "avisos": avisos,
    }


def fallos_desde(scan: dict, git: dict, est: dict, gh: dict) -> list[dict]:
    fallos: list[dict] = []
    # Leer hallazgos_patrones (sin substring "secret") para no alimentar sinks CodeQL.
    for s in scan.get("hallazgos_patrones") or []:
        if s.get("confianza") == "alta":
            # Solo path:línea:tipo:fingerprint — nunca valor del match
            fp = s.get("fingerprint") or "n/d"
            fallos.append(
                {
                    "sev": "P0",
                    "fuente": "escaneo",
                    "detalle": (
                        f"posible secreto en {s.get('fichero')}:{s.get('linea')} "
                        f"({s.get('tipo')}; fp={fp})"
                    ),
                }
            )
    for env in scan.get("env_versionados") or []:
        fallos.append({"sev": "P0", "fuente": "escaneo", "detalle": f".env versionado: {env}"})
    if git.get("es_git") and git.get("sucio"):
        fallos.append(
            {
                "sev": "P2",
                "fuente": "git",
                "detalle": f"árbol sucio ({git.get('cambios_sin_commit', 0)} cambios sin commit)",
            }
        )
    if git.get("atras"):
        fallos.append(
            {
                "sev": "P1",
                "fuente": "git",
                "detalle": f"el clon va {git['atras']} commit(s) por detrás del remoto",
            }
        )
    if git.get("adelante") and git.get("atras"):
        fallos.append({"sev": "P1", "fuente": "git", "detalle": "rama divergente del remoto"})
    for ln in est.get("faltantes") or []:
        fallos.append({"sev": "P2", "fuente": "estructura", "detalle": ln})
    if gh.get("archivado"):
        fallos.append({"sev": "P0", "fuente": "github", "detalle": "repositorio archivado"})
    for run in gh.get("runs_recientes") or []:
        if run.get("conclusion") == "failure":
            fallos.append(
                {
                    "sev": "P1",
                    "fuente": "ci",
                    "detalle": f"último job en rojo: {run.get('name')}",
                }
            )
            break
    for dep in (scan.get("salud_dependencias") or [])[:8]:
        fallos.append({"sev": "P3", "fuente": "dependencias", "detalle": dep})
    return fallos


def semaforo(fallos: list[dict], git: dict) -> str:
    sevs = {f["sev"] for f in fallos}
    if "P0" in sevs:
        return "rojo"
    if not git.get("es_git"):
        return "amarillo"
    if "P1" in sevs or "P2" in sevs:
        return "amarillo"
    return "verde"


def esc(text: object) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def to_markdown(rep: dict) -> str:
    sem = rep["semaforo"]
    git = rep["git"]
    gh = rep["github"]
    road = rep["roadmap"]
    lines = [
        f"# Estado de partida — {rep.get('nombre') or Path(rep['repo']).name}",
        "",
        f"**Fecha**: {rep['generated_at']} | **Perfil**: {rep['profile']} | **Semáforo**: {sem}",
        "",
        "## Estado del repo",
        "",
        f"- Git: {'sí' if git.get('es_git') else 'no'}",
        f"- Rama: `{git.get('rama') or 'n/d'}` @ `{git.get('sha') or 'n/d'}`",
        f"- Remoto: `{git.get('upstream') or 'n/d'}` (adelante {git.get('adelante', 0)}, detrás {git.get('atras', 0)})",
        f"- Árbol sucio: {'sí' if git.get('sucio') else 'no'}",
        f"- Último commit: {git.get('ultimo_commit') or 'n/d'}",
    ]
    if gh.get("disponible"):
        lines += [
            f"- GitHub: {gh.get('nombre')} ({'archivado' if gh.get('archivado') else 'activo'})",
            f"- Rama por defecto: `{gh.get('rama_por_defecto') or 'n/d'}`",
            f"- PRs abiertos: {len(gh.get('prs_abiertos') or [])}",
            f"- Issues abiertos: {len(gh.get('issues_abiertos') or [])}",
        ]
    res = rep["scan"].get("resumen") or {}
    lines += [
        f"- Ficheros: {res.get('total_ficheros', 0)} | lenguaje: {res.get('lenguaje_principal') or 'n/d'}",
        f"- Estructura {rep['profile']}: {'OK' if rep['estructura']['ok'] else 'FALLO'}",
        "",
        "## Camino del producto",
        "",
    ]
    if road.get("fichero"):
        lines.append(f"Fichero: `{road['fichero']}`")
        for t in road.get("titulos") or []:
            lines.append(f"- {t}")
    if road.get("unreleased"):
        lines.append("Sin publicar (changelog):")
        for u in road["unreleased"]:
            lines.append(f"- {u}")
    if gh.get("disponible"):
        for issue in (gh.get("issues_abiertos") or [])[:10]:
            names: list[str] = []
            for lb in issue.get("labels") or []:
                if isinstance(lb, dict):
                    names.append(str(lb.get("name") or ""))
                else:
                    names.append(str(lb))
            labels = ", ".join(n for n in names if n)
            suffix = f" [{labels}]" if labels else ""
            lines.append(f"- #{issue.get('number')} {issue.get('title')}{suffix}")
        for pr in (gh.get("prs_abiertos") or [])[:10]:
            draft = " (borrador)" if pr.get("isDraft") else ""
            lines.append(
                f"- PR #{pr.get('number')} {pr.get('title')}{draft} ← `{pr.get('headRefName')}`"
            )
    if road.get("planes_locales"):
        lines.append("Planes locales:")
        for p in road["planes_locales"]:
            lines.append(f"- `{p}`")
    if (
        not road.get("fichero")
        and not road.get("unreleased")
        and not (gh.get("issues_abiertos") or gh.get("prs_abiertos"))
        and not road.get("planes_locales")
    ):
        lines.append("Sin camino documentado todavía.")
    lines += ["", "## Errores y fallos", ""]
    if not rep["fallos"]:
        lines.append("Sin hallazgos.")
    else:
        lines.append("| Sev | Fuente | Detalle |")
        lines.append("|---|---|---|")
        for f in rep["fallos"]:
            detalle = str(f["detalle"]).replace("|", "\\|")
            lines.append(f"| {f['sev']} | {f['fuente']} | {detalle} |")
    lines += [
        "",
        "## Cómo seguir",
        "",
        "1. Si el semáforo es rojo por un secreto o un `.env` versionado: parar y rotar.",
        "2. Árbol sucio o clon detrás: preguntar antes de `pull --ff-only`.",
        "3. Con el tablero a la vista, escribir el plan (`/design` o `task_plan.md`).",
        "4. Al terminar el trabajo: `project-publish` modo G.",
        "",
        f"JSON: `{rep.get('json_path') or 'inicio.json'}`",
        f"Tablero HTML: `{rep.get('html_path') or 'ESTADO.html'}`",
    ]
    return "\n".join(lines) + "\n"


def to_html(rep: dict) -> str:
    sem = rep["semaforo"]
    color = {"verde": "#0f7b4c", "amarillo": "#9a6b00", "rojo": "#b42318"}[sem]
    git = rep["git"]
    gh = rep["github"]
    road = rep["roadmap"]
    fallos_rows = []
    for f in rep["fallos"]:
        fallos_rows.append(
            f"<tr><td>{esc(f['sev'])}</td><td>{esc(f['fuente'])}</td>"
            f"<td>{esc(f['detalle'])}</td></tr>"
        )
    if not fallos_rows:
        fallos_rows.append('<tr><td colspan="3">Sin hallazgos</td></tr>')
    road_items = []
    for t in road.get("titulos") or []:
        road_items.append(f"<li>{esc(t)}</li>")
    for u in road.get("unreleased") or []:
        road_items.append(f"<li>Sin publicar: {esc(u)}</li>")
    for issue in (gh.get("issues_abiertos") or [])[:10]:
        road_items.append(f"<li>#{esc(issue.get('number'))} {esc(issue.get('title'))}</li>")
    for pr in (gh.get("prs_abiertos") or [])[:10]:
        road_items.append(f"<li>PR #{esc(pr.get('number'))} {esc(pr.get('title'))}</li>")
    if not road_items:
        road_items.append("<li>Sin camino documentado todavía</li>")
    nombre = esc(rep.get("nombre") or Path(rep["repo"]).name)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Estado de partida — {nombre}</title>
  <style>
    :root {{ color-scheme: light dark; }}
    body {{ font-family: ui-sans-serif, system-ui, sans-serif; margin: 0; padding: 1.5rem; line-height: 1.45; max-width: 52rem; }}
    h1 {{ font-size: 1.4rem; margin: 0 0 .4rem; }}
    .pill {{ display: inline-block; padding: .15rem .7rem; border-radius: 999px; color: #fff; background: {color}; font-weight: 600; }}
    section {{ margin: 1.4rem 0; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border-bottom: 1px solid #ccc4; text-align: left; padding: .4rem .5rem; vertical-align: top; }}
    th {{ font-size: .85rem; }}
    ul {{ padding-left: 1.2rem; }}
    .meta {{ color: #555; font-size: .9rem; }}
  </style>
</head>
<body>
  <h1>Estado de partida — {nombre}</h1>
  <p class="meta">{esc(rep['generated_at'])} · perfil {esc(rep['profile'])} · <span class="pill">{esc(sem)}</span></p>
  <section>
    <h2>Estado del repo</h2>
    <table>
      <tr><th>Rama</th><td><code>{esc(git.get('rama') or 'n/d')}</code> @ <code>{esc(git.get('sha') or 'n/d')}</code></td></tr>
      <tr><th>Remoto</th><td>{esc(git.get('upstream') or 'n/d')} (adelante {esc(git.get('adelante', 0))}, detrás {esc(git.get('atras', 0))})</td></tr>
      <tr><th>Árbol sucio</th><td>{'sí' if git.get('sucio') else 'no'}</td></tr>
      <tr><th>Estructura {esc(rep['profile'])}</th><td>{'OK' if rep['estructura']['ok'] else 'FALLO'}</td></tr>
      <tr><th>GitHub</th><td>{esc(gh.get('nombre') or 'n/d')}</td></tr>
    </table>
  </section>
  <section>
    <h2>Camino del producto</h2>
    <ul>{''.join(road_items)}</ul>
  </section>
  <section>
    <h2>Errores y fallos</h2>
    <table>
      <thead><tr><th>Sev</th><th>Fuente</th><th>Detalle</th></tr></thead>
      <tbody>{''.join(fallos_rows)}</tbody>
    </table>
  </section>
</body>
</html>
"""


def build_report(repo: str, profile: str) -> dict:
    repo = os.path.abspath(repo)
    git = git_snapshot(repo)
    scan = scan_repo.scan(repo)
    est = estructura(repo, profile)
    old_cwd = os.getcwd()
    try:
        os.chdir(repo)
        gh = github_vista(repo)
    finally:
        os.chdir(old_cwd)
    road = leer_roadmap_local(repo)
    fallos = fallos_desde(scan, git, est, gh)
    nombre = gh.get("nombre") if gh.get("disponible") else Path(repo).name
    return {
        "repo": repo,
        "nombre": nombre,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "profile": profile,
        "git": git,
        "scan": {"resumen": scan.get("resumen") or {}, "raiz": scan.get("raiz")},
        "estructura": est,
        "github": gh,
        "roadmap": road,
        "fallos": fallos,
        "semaforo": semaforo(fallos, git),
    }


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tablero de partida para un plan de repo")
    ap.add_argument("repo", help="Ruta raíz del repositorio")
    ap.add_argument("--profile", default="P1", choices=["P0", "P1", "P2"])
    ap.add_argument("--out", help="Directorio de salida (inicio.json, ESTADO.md, ESTADO.html)")
    return ap


def main(argv=None) -> int:
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args(argv)
    if not os.path.isdir(args.repo):
        logger.error("'%s' no es un directorio", args.repo)
        return 2
    out = args.out
    if not out:
        import tempfile

        out = tempfile.mkdtemp(prefix="inicio-plan-")
        print(f"inicio_plan.py: salida en {out}")
    os.makedirs(out, exist_ok=True)
    scan_repo.warn_if_output_inside_repo(args.repo, out)

    rep = build_report(args.repo, args.profile)
    json_path = os.path.join(out, "inicio.json")
    md_path = os.path.join(out, "ESTADO.md")
    html_path = os.path.join(out, "ESTADO.html")
    rep["json_path"] = json_path
    rep["md_path"] = md_path
    rep["html_path"] = html_path
    md = to_markdown(rep)
    html = to_html(rep)
    try:
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, ensure_ascii=False, indent=2)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(md)
        with open(html_path, "w", encoding="utf-8") as fh:
            fh.write(html)
    except OSError as exc:
        logger.error("No se pudo escribir la salida: %s", exc)
        return 1
    print(f"semaforo={rep['semaforo']} md={md_path} html={html_path}")
    if rep["semaforo"] == "rojo":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
