#!/bin/bash
# E2E: install dry-run → registry deny → restore reject → complete refuse → OpenCode levels
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
cd "$ROOT"
export PYTHONPATH="$ROOT/tools${PYTHONPATH:+:$PYTHONPATH}"

GATE_A=pass
OPENCODE_B=not_run
OPENCODE_C=not_run

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

echo "[E2E] free-form run_operation rejected (incl. self-declared read)"
python3 - <<'PY'
import sys
sys.path.insert(0, "tools")
from execution.ops import run_operation
r = run_operation(operation_id="x", argv=["true"], effect="mutate-host", target="/")
assert r.outcome == "blocked" and "free-form" in r.detail
r2 = run_operation(operation_id="y", argv=["true"], effect="read", require_approval=False)
assert r2.outcome == "blocked" and "free-form" in r2.detail
print("free-form reject OK")
PY

echo "[E2E] complete without evidence fails"
python3 tools/workspace-router/run.py --repo "$TMP" --init >/dev/null
if python3 tools/workspace-router/run.py --repo "$TMP" --phase DEFINE --complete 2>/dev/null; then
  echo "FAIL: complete without run-id"; exit 1
fi

echo "[E2E] positive complete with bound evidence"
python3 - <<PY
import sys, uuid
from pathlib import Path
sys.path.insert(0, "tools")
sys.path.insert(0, "tools/workspace-router")
from execution.evidence import store_result
from execution.ops import OpResult
from status_bump import advance_status
repo = Path("$TMP")
(repo / "artifact.txt").write_text("ok\n", encoding="utf-8")
rid = store_result(
    repo,
    OpResult(
        operation_id="plan_specification",
        outcome="succeeded",
        returncode=0,
        duration_ms=1,
        detail="",
        effect="write-workspace",
        run_id=str(uuid.uuid4()),
        plan_digest="e2e",
    ),
    phase="DEFINE",
    skill="plan-specification",
    artifacts=["artifact.txt"],
)
s = advance_status(repo, phase="DEFINE", skill="plan-specification", evidence_ok=True, run_id=rid)
assert s["phase"] == "DEFINE" and s["state_revision"] == 1
s2 = advance_status(repo, phase="DEFINE", skill="plan-specification", evidence_ok=True, run_id=rid)
assert s2.get("_idempotent_replay") is True
print("positive complete + idempotency OK", rid)
PY

echo "[E2E] OpenCode levels B/C (target 1.18.34)"
TARGET_OC="1.18.34"
if ! command -v opencode >/dev/null 2>&1; then
  OPENCODE_B=not_run
  OPENCODE_C=not_run
  echo "not_run: opencode binary absent; harness B/C pending (declared target $TARGET_OC)"
else
  V=$(opencode --version 2>/dev/null || true)
  if [ "$V" != "$TARGET_OC" ]; then
    echo "FAIL: expected OpenCode $TARGET_OC got '$V'"
    exit 1
  fi
  OPENCODE_B=version_ok
  echo "OpenCode $V version OK (B partial: version only)"
  # Permissions (C): probe help without --auto; do not claim ask/deny without real skill load
  if opencode --help 2>&1 | grep -qi permission; then
    OPENCODE_C=help_mentions_permissions
    echo "OpenCode help mentions permissions (C partial; not full ask/deny proof)"
  else
    OPENCODE_C=not_run
    echo "not_run: could not confirm permissions surface via --help"
  fi
fi

echo "=== E2E verdict ==="
echo "gate_A=$GATE_A"
echo "opencode_B=$OPENCODE_B"
echo "opencode_C=$OPENCODE_C"
if [ "$OPENCODE_B" = "not_run" ] || [ "$OPENCODE_C" = "not_run" ]; then
  echo "E2E gate_A OK; harness B/C pending — NOT an integral E2E OK"
  exit 0
fi
echo "E2E OK (A+B+C surfaces exercised within declared limits)"
