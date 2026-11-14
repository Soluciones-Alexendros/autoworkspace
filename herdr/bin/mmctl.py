#!/usr/bin/env python3
"""Machineroom bridge for Herdr.

`open` runs from a plugin action and asks Herdr for a plugin pane; `pane` runs
inside that pane and renders Machineroom state for the repo of the current
workspace. Everything is stdlib-only: the router scripts are the tooling, this
file only drives them.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

PLUGIN_ID = os.environ.get("HERDR_PLUGIN_ID", "machineroom")
HERDR = os.environ.get("HERDR_BIN_PATH") or shutil.which("herdr") or "herdr"
PHASES = ("DEFINE", "SCHEMAS", "IMPLEMENT", "VALIDATE", "INTEGRATE", "STATUS")
BOLD, DIM, RESET = "\033[1m", "\033[2m", "\033[0m"

PANE_KEYS = {
    "dashboard": ("overlay", None),
    "skills": ("overlay", None),
    "route": ("overlay", None),
    "status": ("overlay", None),
    "phase": ("overlay", None),
    "doctor": ("overlay", None),
    "validate": ("split", "down"),
}


def paint(text: str, code: str) -> str:
    return f"{code}{text}{RESET}" if sys.stdout.isatty() else text


def mm_root() -> Path:
    """Locate the Machineroom checkout that hosts this plugin."""
    candidates: list[Path] = []
    plugin_root = os.environ.get("HERDR_PLUGIN_ROOT")
    if plugin_root:
        candidates.append(Path(plugin_root).resolve().parent)
    here = Path(__file__).resolve()
    candidates.extend([here.parents[1], here.parents[2], Path.cwd()])
    for candidate in candidates:
        if (candidate / "skill-index.json").is_file() and (candidate / "skills").is_dir():
            return candidate
    raise SystemExit("machineroom: no encuentro el checkout (skill-index.json + skills/)")


def context() -> dict[str, Any]:
    raw = os.environ.get("HERDR_PLUGIN_CONTEXT_JSON") or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def scoped(start: Path) -> Path:
    """Nearest ancestor with a `.machineroom/` directory, else `start`."""
    for path in (start, *start.parents):
        if (path / ".machineroom").is_dir():
            return path
    return start


def target_repo() -> Path:
    """Pane cwd first (actions pass `--cwd`), then the workspace context."""
    ctx = context()
    worktree = ctx.get("worktree") or {}
    here = Path.cwd()
    if here != mm_root() and (here / ".machineroom").is_dir():
        return here
    for value in (worktree.get("path"), ctx.get("workspace_cwd"), ctx.get("focused_pane_cwd"), str(here)):
        if value and Path(value).is_dir():
            return scoped(Path(value))
    return scoped(here)


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def has_uv() -> bool:
    return shutil.which("uv") is not None


def pause(prompt: str = "Enter para cerrar") -> None:
    with contextlib.suppress(EOFError):
        input(f"\n{paint(prompt, DIM)} ")


# --- panes -----------------------------------------------------------------


def skills_catalog(root: Path) -> list[dict[str, Any]]:
    index = json.loads((root / "skill-index.json").read_text(encoding="utf-8"))
    return list(index.get("skills", []))


def first_sentence(text: str, limit: int = 150) -> str:
    cut = text.split(". ", maxsplit=1)[0].strip()
    if len(cut) > limit:
        cut = cut[: limit - 1].rstrip() + "…"
    return cut


def pane_skills(repo: Path) -> None:
    root = mm_root()
    skills = skills_catalog(root)
    domains: dict[str, list[dict[str, Any]]] = {}
    for skill in skills:
        domains.setdefault(str(skill.get("domain", "otras")), []).append(skill)
    print(paint(f"Machineroom · {len(skills)} skills en {len(domains)} dominios", BOLD))
    print(paint(f"catalogo: {root / 'skills'}", DIM))
    for domain in sorted(domains):
        print(f"\n{paint(domain, BOLD)}")
        for skill in sorted(domains[domain], key=lambda item: str(item.get("name"))):
            kind = skill.get("type", "-")
            print(f"  {skill.get('name', '?'):<20} {kind:<13} {first_sentence(str(skill.get('description', '')))}")
    print(paint(f"\nproyecto activo: {repo}", DIM))
    pause()


def route_skills(repo: Path, text: str) -> None:
    root = mm_root()
    if not text.strip():
        print("Selecciona texto en un panel y lanza la acción, o escribe la petición aquí:")
        try:
            text = input("> ")
        except EOFError:
            return
    if not text.strip():
        return
    code, output = run([sys.executable, str(root / "tools/skill-router/route.py"), text, "--top", "3"], cwd=root)
    print()
    print(output.strip() or f"route.py terminó con código {code} sin salida")
    top = output.split("->", 1)[0].strip().split(" ")[-1] if "->" in output else ""
    if top:
        print(f"\n{paint('siguiente paso', BOLD)}: pedir al agente que cargue {paint(top, BOLD)}")
    print(paint(f"proyecto activo: {repo}", DIM))
    pause()


def git_line(repo: Path) -> str:
    branch = run(["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"])[1].strip()
    status = run(["git", "-C", str(repo), "status", "--porcelain"])[1].strip()
    dirty = len(status.splitlines()) if status else 0
    if not branch:
        return "no es un repositorio git"
    return f"rama {branch} · {dirty} ficheros sin commitear"


def declared_phase(repo: Path) -> str:
    for name in ("project.yaml", "status.yaml"):
        path = repo / ".machineroom" / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if stripped.startswith(("phase:", "current_phase:", "fase:")):
                return stripped.split(":", 1)[1].strip().strip("'\"") or "?"
    return "sin declarar"


def pane_status(repo: Path) -> None:
    print(paint(f"Machineroom · {repo.name}", BOLD))
    print(f"  {paint('ruta', DIM)}     {repo}")
    print(f"  {paint('git', DIM)}      {git_line(repo)}")
    print(f"  {paint('fase', DIM)}     {declared_phase(repo)}")
    state = repo / ".machineroom"
    if not state.is_dir():
        print(paint("\n  sin .machineroom/: plan-continue lo crea al arrancar el pipeline", DIM))
    else:
        print(f"\n{paint('.machineroom/', BOLD)}")
        for item in sorted(state.iterdir()):
            print(f"  {item.name}")
        for name in ("project.yaml", "status.yaml"):
            path = state / name
            if path.is_file():
                body = path.read_text(encoding="utf-8", errors="replace").splitlines()[:24]
                print(f"\n{paint(f'.machineroom/{name}', BOLD)}")
                for line in body:
                    print(f"  {line}")
    pause()


def pane_phase(repo: Path) -> None:
    print(paint("Enrutar fase del pipeline", BOLD))
    for index, phase in enumerate(PHASES, 1):
        print(f"  {index}. {phase}")
    try:
        choice = input("\nfase (1-6, Enter cancela) > ").strip()
    except EOFError:
        return
    if not choice.isdigit() or not 1 <= int(choice) <= len(PHASES):
        return
    phase = PHASES[int(choice) - 1]
    root = mm_root()
    script = ["tools/workspace-router/run.py", "--phase", phase, "--repo", str(repo), "--json"]
    runner = ["uv", "run", "--project", str(root / "tools"), "python3"] if has_uv() else [sys.executable]
    code, output = run([*runner, *script], cwd=root)
    print()
    if code != 0:
        print(output.strip())
    else:
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            print(output.strip())
        else:
            print(paint(f"fase {data.get('phase')} → skill {data.get('skill')}", BOLD))
            print(f"  repo: {data.get('repo')}")
            allowed = data.get("allowed_skills") or []
            if allowed:
                print(f"  skills permitidas: {', '.join(allowed)}")
            next_phase = data.get("next") or data.get("next_phase")
            if next_phase:
                print(f"  siguiente: {next_phase}")
    pause()


def pane_validate(repo: Path) -> None:
    root = mm_root()
    print(paint(f"Machineroom · validate en {repo}", BOLD))
    if (repo / "Makefile").is_file():
        cmd = ["make", "validate"]
    elif (repo / "run-validation.sh").is_file():
        cmd = ["bash", "run-validation.sh"]
    else:
        print(f"\n{paint('nada que validar:', BOLD)} no hay Makefile ni run-validation.sh en {repo}")
        pause()
        return
    print(paint(f"$ {' '.join(cmd)}", DIM))
    proc = subprocess.run(cmd, cwd=str(repo), check=False)
    verdict = "OK" if proc.returncode == 0 else f"FALLO (código {proc.returncode})"
    print(f"\n{paint('resultado', BOLD)}: {verdict}")
    if proc.returncode != 0:
        print(paint(f"guía del gate: {root / 'docs/harness-integration.md'}", DIM))
    pause()


def pane_doctor(repo: Path) -> None:
    root = mm_root()
    print(paint("Machineroom · doctores de harness", BOLD))
    code, output = run([sys.executable, str(root / "tools/harness/doctor.py")], cwd=root)
    print(f"\n{paint('tools/harness/doctor.py', BOLD)}")
    for line in output.strip().splitlines() or ["(sin salida)"]:
        print(f"  {line}")
    home = Path.home()
    for label, path in (("pi", home / ".pi/agent/skills"), ("cursor", home / ".cursor/skills")):
        links = sorted(item.name for item in path.iterdir() if item.is_symlink()) if path.is_dir() else []
        print(f"\n{paint(label, BOLD)}: {path} → {len(links)} enlaces")
        if links:
            print("  " + ", ".join(links))
    if code != 0:
        print(paint(f"\ndoctor terminó con código {code}", DIM))
    pause()


def dashboard(repo: Path) -> None:
    root = mm_root()
    skills = skills_catalog(root)
    print(paint(f"Machineroom · {repo.name}", BOLD))
    print(f"  {paint('repo', DIM)}    {repo}")
    print(f"  {paint('git', DIM)}     {git_line(repo)}")
    print(f"  {paint('fase', DIM)}    {declared_phase(repo)}")
    print(f"  {paint('skills', DIM)}  {len(skills)} en el catálogo de {root.name}")
    print(
        f"\n  {paint('teclas', DIM)}   prefix+m panel · prefix+shift+m skills · prefix+g enrutar"
        f" · prefix+shift+v validar · prefix+o doctores"
    )
    try:
        choice = input("\n[r]efrescar [s]kills [e]nrutar [f]ases [v]alidar [d]octor [q]uitar > ").strip().lower()
    except EOFError:
        return
    if choice == "r":
        dashboard(repo)
    elif choice == "s":
        pane_skills(repo)
    elif choice == "e":
        route_skills(repo, os.environ.get("MM_SELECTION", ""))
    elif choice == "f":
        pane_phase(repo)
    elif choice == "v":
        open_pane("validate-pane", repo)
    elif choice == "d":
        pane_doctor(repo)


PANE_DISPATCH = {
    "dashboard": dashboard,
    "skills": pane_skills,
    "status": pane_status,
    "phase": pane_phase,
    "doctor": pane_doctor,
    "validate": pane_validate,
}


# --- actions ---------------------------------------------------------------


def open_pane(entrypoint: str, repo: Path | None = None, extra_env: dict[str, str] | None = None) -> int:
    placement, direction = PANE_KEYS.get(entrypoint.replace("-pane", ""), ("overlay", None))
    args = [
        HERDR,
        "plugin",
        "pane",
        "open",
        "--plugin",
        PLUGIN_ID,
        "--entrypoint",
        entrypoint,
        "--cwd",
        str(repo or target_repo()),
        "--placement",
        placement,
        "--focus",
    ]
    if direction:
        args.extend(["--direction", direction])
    for key, value in (extra_env or {}).items():
        args.extend(["--env", f"{key}={value}"])
    proc = subprocess.run(args, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or proc.stdout)
    return proc.returncode


USAGE_ARGC = 2
TARGET_ARGC = 3


def main(argv: list[str]) -> int:
    if len(argv) < USAGE_ARGC:
        print(__doc__)
        return 2
    command = argv[1]
    repo = target_repo()
    default_target = "dashboard"
    if command == "open":
        target = argv[2] if len(argv) >= TARGET_ARGC else default_target
        env = {}
        selection = context().get("selected_text") or ""
        if selection.strip():
            env["MM_SELECTION"] = selection
        return open_pane(f"{target}-pane", repo, env)
    if command == "pane":
        target = argv[2] if len(argv) >= TARGET_ARGC else default_target
        if target == "route":
            route_skills(repo, os.environ.get("MM_SELECTION", ""))
            return 0
        handler = PANE_DISPATCH.get(target)
        if handler is None:
            print(f"machineroom: entrada de panel desconocida: {target}")
            return 2
        handler(repo)
        return 0
    print(f"machineroom: comando desconocido: {command}")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
