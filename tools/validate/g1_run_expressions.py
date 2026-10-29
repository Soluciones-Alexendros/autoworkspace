#!/usr/bin/env python3
"""G1: detecta expresiones GitHub ${{ ... }} incrustadas en scalars `run`.

No inspecciona env/if/with/comentarios como hallazgos. Fallo si YAML inválido
o si aparece una expresión en un campo run de un workflow versionado.

Uso: python3 tools/validate/g1_run_expressions.py [--root DIR]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml as _yaml_mod
except ImportError:  # pragma: no cover - entorno sin PyYAML
    _yaml_mod = None

yaml = _yaml_mod

ROOT = Path(sys.argv[sys.argv.index("--root") + 1]) if "--root" in sys.argv else Path(__file__).resolve().parents[2]
EXPR_RE = re.compile(r"\$\{\{")
ERRORS: list[str] = []


def err(msg: str) -> None:
    ERRORS.append(msg)


def _walk_steps(rel: str, job_name: str, steps: Any) -> None:
    if not isinstance(steps, list):
        return
    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        run = step.get("run")
        if isinstance(run, str) and EXPR_RE.search(run):
            err(f"{rel}: job '{job_name}' step[{idx}] run incrusta expresión ${{{{ ... }}}}")


def check_workflow(path: Path, root: Path) -> None:
    rel = str(path.relative_to(root))
    if yaml is None:
        err("PyYAML requerido para G1")
        return
    text = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        err(f"{rel}: YAML inválido: {type(exc).__name__}")
        return
    if not isinstance(data, dict):
        err(f"{rel}: workflow no es un mapping")
        return
    jobs = data.get("jobs") or {}
    if not isinstance(jobs, dict):
        err(f"{rel}: jobs inválidos")
        return
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        _walk_steps(rel, str(job_name), job.get("steps"))


def run_g1(root: Path) -> int:
    ERRORS.clear()
    wf_dir = root / ".github" / "workflows"
    if not wf_dir.is_dir():
        err("falta .github/workflows")
    else:
        for path in sorted(wf_dir.glob("*.yml")) + sorted(wf_dir.glob("*.yaml")):
            check_workflow(path, root)
    print(f"errores: {len(ERRORS)}")
    for e in ERRORS:
        print("FAIL", e)
    print("G1:", "OK" if not ERRORS else "CON-FALLOS")
    return 1 if ERRORS else 0


def main() -> int:
    return run_g1(ROOT)


if __name__ == "__main__":
    sys.exit(main())
