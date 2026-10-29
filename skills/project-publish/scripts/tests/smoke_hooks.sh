#!/usr/bin/env bash
# smoke_hooks.sh — Smoke del gate Husky integrado en project-publish.
# Crea un repo temporal minimo con package.json y verifica que gate-husky.sh
# instala hooks y pasa el gate en verde.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
D="$(mktemp -d -t smoke-hooks-XXXXXX 2>/dev/null)" || D="$(mktemp -d 2>/dev/null)"
if ! (printf '#!/bin/sh\nexit 0\n' > "$D/.probe.sh" && chmod +x "$D/.probe.sh" && "$D/.probe.sh" 2>/dev/null); then
  rm -rf "$D"
  mkdir -p "$HOME/.cache/harness-tmp"
  D="$(mktemp -d -p "$HOME/.cache/harness-tmp" smoke-hooks-XXXXXX)"
fi
rm -f "$D/.probe.sh"
TMP="$D"
trap 'rm -rf "$TMP"' EXIT

cd "$TMP"
git init -q 2>/dev/null || true
git config user.email "smoke@example.com" 2>/dev/null || true
git config user.name "Smoke" 2>/dev/null || true
cat > package.json <<'EOF'
{
  "name": "smoke-hooks",
  "version": "0.0.0",
  "private": true,
  "scripts": {
    "typecheck": "echo typecheck-ok",
    "test": "echo test-ok"
  }
}
EOF
echo "hola" > hola.md
git add -A 2>/dev/null || true

bash "$ROOT/scripts/gate-husky.sh" "$TMP"
test -f "$TMP/.husky/pre-commit"
test -f "$TMP/.lintstagedrc"
echo "smoke project-publish hooks: OK"
