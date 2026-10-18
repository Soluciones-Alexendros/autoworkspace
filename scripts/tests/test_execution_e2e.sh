#!/bin/bash
# Minimal E2E: install dry-run → registry deny → restore reject → complete refuse
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
cd "$ROOT"
export PYTHONPATH="$ROOT/tools${PYTHONPATH:+:$PYTHONPATH}"

echo "[E2E] install dry-run no writes"
MISS="$TMP/missing-target"
bash scripts/install.sh --target "$MISS" --dry-run
test ! -e "$MISS"

echo "[E2E] mutator blocked without ApprovalProvider"
python3 - <<'PY'
import sys
sys.path.insert(0, "tools")
from execution.ops import run_registered
r = run_registered("clean_journal", {"snapshot_id": "s"}, target="/")
assert r.outcome == "blocked", r
print("blocked OK:", r.detail[:60])
PY

echo "[E2E] free-form run_operation rejected"
python3 - <<'PY'
import sys
sys.path.insert(0, "tools")
from execution.ops import run_operation
r = run_operation(operation_id="x", argv=["true"], effect="mutate-host", target="/")
assert r.outcome == "blocked" and "free-form" in r.detail
print("free-form reject OK")
PY

echo "[E2E] complete without evidence fails"
python3 tools/workspace-router/run.py --repo "$TMP" --init >/dev/null
if python3 tools/workspace-router/run.py --repo "$TMP" --phase DEFINE --complete 2>/dev/null; then
  echo "FAIL: complete without run-id"; exit 1
fi

echo "[E2E] OpenCode version declared"
V=$(opencode --version 2>/dev/null || true)
test "$V" = "1.18.34" || { echo "FAIL: expected OpenCode 1.18.34 got '$V'"; exit 1; }

echo "E2E OK"
