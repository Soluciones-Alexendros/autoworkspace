#!/bin/bash
# Canonical validation gate — wraps tools/validate/* (no duplicated rules).
#
# Usage: bash run-validation.sh [--pytest-only] [--smoke-only] [--check-index]
#   default: full gate. --pytest-only: tests only. --smoke-only: router smoke.
#   --check-index: compare skill-index.json without rewriting it.
set -euo pipefail

ONLY_PYTEST=0
ONLY_SMOKE=0
CHECK_INDEX=0
for arg in "$@"; do
  case "$arg" in
    --pytest-only) ONLY_PYTEST=1 ;;
    --smoke-only) ONLY_SMOKE=1 ;;
    --check-index) CHECK_INDEX=1 ;;
    --help|-h)
      echo "Usage: bash run-validation.sh [--pytest-only] [--smoke-only] [--check-index]"
      exit 0
      ;;
    *)
      echo "ERROR: invalid flag: $arg" >&2
      exit 2
      ;;
  esac
done
FULL=1
if [ "$ONLY_PYTEST" = 1 ] || [ "$ONLY_SMOKE" = 1 ]; then FULL=0; fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

echo "=== Autoworkspace validation (canonical) ==="

if [ "$FULL" = 1 ]; then
  echo "[1] skill_spec.py (catalog + frontmatter + domain)"
  python3 tools/validate/skill_spec.py --root "$ROOT"

  echo "[2] skill_links.py"
  python3 tools/validate/skill_links.py --root "$ROOT"

  echo "[3] release_coherence.py"
  python3 tools/validate/release_coherence.py --root "$ROOT"

  echo "[4] hygiene.py"
  python3 tools/validate/hygiene.py --root "$ROOT"

  echo "[4b] execution registry (required)"
  PYTHONPATH="$ROOT/tools${PYTHONPATH:+:$PYTHONPATH}" \
    python3 -m execution.registry --check --root "$ROOT"
  python3 tools/contracts/validate_contracts.py --root "$ROOT"

  echo "[5] skill-index.json generate + marker check"
  python3 tools/skill-index/generate.py --check --root "$ROOT"

  echo "[5b] frozen catalog snapshot"
  python3 tools/skill-index/generate.py --json | diff -q - docs/architecture/skill-index-7.0.0.json
fi

if [ "$CHECK_INDEX" = 1 ] && [ "$FULL" = 0 ]; then
  python3 tools/skill-index/generate.py --check --root "$ROOT"
fi

if [ "$FULL" = 1 ] || [ "$ONLY_SMOKE" = 1 ]; then
  echo "[6] Router smoke (selection only — not behavior proof)"
  python3 tools/skill-router/route.py "por donde empiezo con este repo" --top 2
  python3 tools/skill-router/route.py "limpia mi sistema" --top 2
  python3 tools/skill-router/route.py "refactoriza este código aplicando clean code" --top 2
fi

if [ "$FULL" = 1 ] || [ "$ONLY_PYTEST" = 1 ]; then
  echo "[7] Pytest tools/ + skills (install + Proton included)"
  python3 -m pytest tools/ \
    skills/local-maintenance/scripts/tests/ \
    skills/web-compliance/tests/ \
    skills/local-security/scripts/tests/ \
    tools/email/drivers/proton/ \
    -q
fi

if [ "$FULL" = 1 ]; then
  echo "[8] Install scripts matrix"
  bash scripts/tests/test_install.sh

  echo "[8b] Execution E2E mínimo"
  bash scripts/tests/test_execution_e2e.sh

  echo "[9] Bash syntax (scripts/ + root wrappers)"
  while IFS= read -r -d '' f; do
    bash -n "$f"
  done < <(find scripts skills tools -name '*.sh' -print0 2>/dev/null; printf '%s\0' run-validation.sh)
fi

echo "=== All checks passed ==="
