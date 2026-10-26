#!/usr/bin/env python3
"""review-vs-plan.py — Revision critica automatizada del diff contra el plan.

Compara el resultado esperado del plan (task_plan.md) con el diff
<base>...<branch> de cada rama del plan:
  1. Bloquea si el diff contiene posibles secretos.
  2. Bloquea si el diff esta vacio (nada que mergear).
  3. Informa cobertura plan->diff (heuristica por nombres de fichero).

Uso: python3 review-vs-plan.py <plan_file> <branch> [base=main]
Exit: 0 OK, 1 bloqueo/desviacion.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SECRET_PATTERNS = [
    # Asignaciones tipo password = "valor", secret: xyz (con frontera de palabra).
    re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|private[_-]?key)\b\s*[:=]\s*\S+"),
    # Tokens/bearers con valor sustancial.
    re.compile(r"(?i)\b(token|bearer)\b\s*[:=]\s*['\"]?[A-Za-z0-9_\-./+]{8,}"),
    # Exportaciones de entorno: export GITHUB_TOKEN=... / SECRET_FOO=bar.
    re.compile(r"(?i)^\+?\s*(?:export\s+)?[A-Z_]*(PASSWORD|SECRET|TOKEN|PRIVATE_KEY|API_KEY)[A-Z_]*\s*=\s*\S+"),
]
FILE_RE = re.compile(r"[\w\-./]+\.(?:ts|tsx|js|jsx|py|sh|md|json|yaml|yml|toml)")

# Constantes con nombre (P12 T6e): sustituyen literales mágicos.
MIN_ARGV = 3
MIN_COVERAGE = 0.5


def run(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, check=False)


def main() -> int:
    if len(sys.argv) < MIN_ARGV:
        print("Uso: review-vs-plan.py <plan_file> <branch> [base=main]")
        return 1
    plan_file = Path(sys.argv[1])
    branch = sys.argv[2]
    base = sys.argv[3] if len(sys.argv) > MIN_ARGV else "main"

    if not plan_file.is_file():
        print(f"BLOQUEO: plan no encontrado: {plan_file}")
        return 1
    plan_content = plan_file.read_text(encoding="utf-8")

    ref = branch if branch == "HEAD" else f"{base}...{branch}"
    diff = run(["git", "diff", ref, "--name-only"]).stdout.strip()
    files = [f for f in diff.splitlines() if f.strip()]
    print(f"Archivos en diff {ref}: {len(files)}")
    if not files:
        print("BLOQUEO: diff vacio; no hay cambios que mergear.")
        return 1

    full_diff = run(["git", "diff", ref]).stdout
    added = [ln for ln in full_diff.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
    leaks = [ln for ln in added if any(p.search(ln) for p in SECRET_PATTERNS)][:5]
    if leaks:
        print("BLOQUEO: posibles secretos en el diff:")
        for ln in leaks:
            print(f"  {ln[:160]}")
        return 1

    planned = set(FILE_RE.findall(plan_content))
    if planned:
        changed = set(files)
        hit = {p for p in planned if any(p == c or c.endswith("/" + p) for c in changed)}
        cov = len(hit) / len(planned)
        print(f"Cobertura plan->diff: {cov:.0%} ({len(hit)}/{len(planned)})")
        if cov < MIN_COVERAGE:
            print("AVISO: cobertura baja; verifica que el resultado del plan este en el diff.")
    else:
        print("Sin ficheros mencionables en el plan; se acepta el diff tal cual.")

    print("OK: revision vs plan superada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
