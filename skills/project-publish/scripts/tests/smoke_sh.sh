#!/usr/bin/env bash
# smoke_sh.sh — Smoke test de project-publish/scripts.
# Verifica review-vs-plan.py: (a) bloquea diff vacio, (b) OK con cambios,
# (c) bloquea posibles secretos en el diff; finalmente ejecuta el smoke Husky.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
D="$(mktemp -d -t smoke-release-XXXXXX 2>/dev/null)" || D="$(mktemp -d 2>/dev/null)"
if ! (printf '#!/bin/sh\nexit 0\n' > "$D/.probe.sh" && chmod +x "$D/.probe.sh" && "$D/.probe.sh" 2>/dev/null); then
  rm -rf "$D"
  mkdir -p "$HOME/.cache/harness-tmp"
  D="$(mktemp -d -p "$HOME/.cache/harness-tmp" smoke-release-XXXXXX)"
fi
rm -f "$D/.probe.sh"
TMP="$D"
trap 'rm -rf "$TMP"' EXIT

cd "$TMP"
git init -q
git config user.email "smoke@example.com"
git config user.name "Smoke"
git checkout -qb main
echo "base" > src.txt
mkdir -p .planning/active
printf '# Plan\n\n- [x] status: completed\n- crear `src.txt`\n' > .planning/active/task_plan.md
git add -A && git commit -qm "chore: base"

# (a) diff vacio debe bloquear (exit 1)
git checkout -qb feat/vacia
if python3 "$ROOT/scripts/review-vs-plan.py" .planning/active/task_plan.md feat/vacia main; then
  echo "FAIL: diff vacio no bloqueo" >&2; exit 1
fi

# (b) diff con cambios debe pasar
echo "cambio" >> src.txt
git add -A && git commit -qm "feat: cambio"
python3 "$ROOT/scripts/review-vs-plan.py" .planning/active/task_plan.md feat/vacia main

# (c) secreto en diff debe bloquear
echo "api_key = SUPERSECRETO123" > secreto.txt
git add -A && git commit -qm "feat: secreto (test)"
if python3 "$ROOT/scripts/review-vs-plan.py" .planning/active/task_plan.md feat/vacia main; then
  echo "FAIL: secreto no bloqueo" >&2; exit 1
fi

bash "$ROOT/scripts/tests/smoke_hooks.sh"

echo "smoke project-publish: OK"
