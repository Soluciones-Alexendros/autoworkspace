#!/usr/bin/env bash
# Smoke para scripts .py: --help (exit 0) + py_compile de cada script.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

fail=0
ok() { echo "OK: $1"; }
bad() { echo "FALLO: $1" >&2; fail=1; }

shopt -s nullglob
found=0
for py in "$SCRIPT_DIR"/*.py; do
  found=1
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

if [[ $found -eq 0 ]]; then
  bad "sin scripts .py en $SCRIPT_DIR"
fi

if [[ $fail -eq 0 ]]; then echo "smoke scripts py: VERDE"; else echo "smoke scripts py: ROJO" >&2; fi
exit "$fail"
