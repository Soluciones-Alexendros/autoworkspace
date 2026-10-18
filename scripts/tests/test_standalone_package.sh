#!/bin/bash
# V34–V35: standalone package runs without source PYTHONPATH
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

DEST="$TMP/pkg"
mkdir -p "$DEST"

# Reject relative dest
if bash "$ROOT/scripts/package-standalone-skill.sh" --skill local-maintenance --dest relative 2>/dev/null; then
  echo "FAIL: relative dest should be rejected"; exit 1
fi

# Reject escape skill name
if bash "$ROOT/scripts/package-standalone-skill.sh" --skill '../evil' --dest "$DEST/x" 2>/dev/null; then
  echo "FAIL: escape skill should be rejected"; exit 1
fi

bash "$ROOT/scripts/package-standalone-skill.sh" --skill local-maintenance --dest "$DEST"
test -f "$DEST/local-maintenance/SKILL.md"
test -f "$DEST/local-maintenance/vendor/execution/ops.py"

# Move package and run with clean env (no ROOT/tools on PYTHONPATH)
MOVED="$TMP/moved"
mv "$DEST" "$MOVED"
# Make source tools unreadable via empty PYTHONPATH and cwd outside repo
cd "$MOVED"
python3 - <<'PY'
import sys, os
from pathlib import Path
# Only vendor on path — prove autonomy
vendor = Path("local-maintenance/vendor").resolve()
sys.path.insert(0, str(vendor))
# Ensure repo tools not accidentally present
sys.path = [p for p in sys.path if "autoworkspace/tools" not in p.replace("\\", "/")]
from execution.ops import run_registered
from execution.approval import DenyProvider
import execution.ops as ops
ops.provider_from_env = lambda: DenyProvider()
r = run_registered("clean_journal", {"snapshot_id": "s"}, target="/")
assert r.outcome == "blocked", r
print("standalone deny OK", r.detail[:40])
PY

echo "standalone package tests PASS"
