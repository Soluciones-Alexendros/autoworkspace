#!/usr/bin/env bash
# Smoke para scripts de data-linkml: --help (exit 0) + py_compile de cada .py,
# y dry-run del bootstrap (sin sudo, sin red, sin efectos secundarios).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

fail=0
ok() { echo "OK: $1"; }
bad() { echo "FALLO: $1" >&2; fail=1; }

shopt -s nullglob
count=0
for py in "$SCRIPT_DIR"/*.py; do
  count=$((count + 1))
  base="$(basename "$py")"
  if python3 "$py" --help >/dev/null 2>&1; then
    ok "--help $base exit 0"
  else
    bad "--help $base exit $?"
  fi
  if python3 -m py_compile "$py"; then
    ok "py_compile $base"
  else
    bad "py_compile $base"
  fi
done
shopt -u nullglob

if [[ $count -eq 0 ]]; then
  bad "sin scripts .py en $SCRIPT_DIR"
fi

if [[ -f "$SCRIPT_DIR/bootstrap_arch.sh" ]]; then
  if bash "$SCRIPT_DIR/bootstrap_arch.sh" --dry-run >/dev/null 2>&1; then
    ok "bootstrap_arch.sh --dry-run exit 0"
  else
    bad "bootstrap_arch.sh --dry-run exit $?"
  fi
else
  bad "falta bootstrap_arch.sh"
fi

if [[ $fail -eq 0 ]]; then
  echo "smoke data-linkml: VERDE"
else
  echo "smoke data-linkml: ROJO" >&2
fi
exit "$fail"
