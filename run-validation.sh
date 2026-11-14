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

echo "=== Machineroom validation (canonical) ==="

if [ "$FULL" = 1 ]; then
  echo "[1] skill_spec.py (catalog + frontmatter + domain)"
  python3 tools/validate/skill_spec.py --root "$ROOT"

  echo "[2] skill_links.py"
  python3 tools/validate/skill_links.py --root "$ROOT"

  echo "[3] release_coherence.py"
  python3 tools/validate/release_coherence.py --root "$ROOT"

  echo "[3a] naming_gate.py (pre-8.0 name only where it is load-bearing)"
  python3 tools/validate/naming_gate.py

  echo "[3b] contract_parity.py (rule SSOT vs sessionStart pointer)"
  python3 tools/validate/contract_parity.py

  echo "[4] hygiene.py"
  python3 tools/validate/hygiene.py --root "$ROOT"

  echo "[4b] execution registry (required)"
  PYTHONPATH="$ROOT/tools${PYTHONPATH:+:$PYTHONPATH}" \
    python3 -m execution.registry --check --root "$ROOT"
  python3 tools/contracts/validate_contracts.py --root "$ROOT"

  echo "[5] skill-index.json generate + marker check"
  python3 tools/skill-index/generate.py --check --root "$ROOT"

  echo "[5b] frozen catalog snapshot"
  python3 tools/skill-index/generate.py --json | diff -q - docs/architecture/skill-index-8.0.0.json
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
  echo "HARNESS_MATRIX: cursor,pi"
  bash scripts/tests/test_install.sh

  echo "[8b] Execution E2E mínimo"
  bash scripts/tests/test_execution_e2e.sh

  echo "[9] Bash syntax (scripts/ + root wrappers)"
  while IFS= read -r -d '' f; do
    bash -n "$f"
  done < <(find scripts skills tools -name '*.sh' -print0 2>/dev/null; printf '%s\0' run-validation.sh)

  echo "[10] Herdr plugin (manifest + paneles)"
  python3 - <<'PY'
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

root = Path.cwd()
plugin = root / "herdr"
manifest = tomllib.loads((plugin / "herdr-plugin.toml").read_text(encoding="utf-8"))
for key in ("id", "name", "version", "min_herdr_version"):
    assert manifest.get(key), f"manifest sin {key}"
panes = {pane["id"] for pane in manifest.get("panes", [])}
actions = manifest.get("actions", [])
assert actions, "manifest sin acciones"
for action in actions:
    command = action["command"]
    assert command[:3] == ["python3", "bin/mmctl.py", "open"], command
    entrypoint = f"{command[3]}-pane"
    assert entrypoint in panes, f"accion {action['id']} apunta a un panel inexistente: {entrypoint}"

env = dict(os.environ, HERDR_PLUGIN_ROOT=str(plugin), HERDR_PLUGIN_ID=manifest["id"])
rendered = subprocess.run(
    ["python3", "bin/mmctl.py", "pane", "skills"],
    cwd=plugin,
    env=env,
    stdin=subprocess.DEVNULL,
    capture_output=True,
    text=True,
    timeout=120,
)
assert rendered.returncode == 0, rendered.stderr
expected = [skill["name"] for skill in json.loads((root / "skill-index.json").read_text(encoding="utf-8"))["skills"]]
missing = [name for name in expected if name not in rendered.stdout]
assert not missing, f"el panel no lista: {missing}"
print(f"herdr plugin: {len(actions)} acciones, {len(panes)} paneles, {len(expected)} skills")
PY
fi

echo "=== All checks passed ==="
