#!/bin/bash
# E2E público: dry-run → deny → handler real → evidencia → complete.
# Nivel A es la puerta de symlinks. No se exige binario de Cursor ni de Pi.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
cd "$ROOT"
export PYTHONPATH="$ROOT/tools${PYTHONPATH:+:$PYTHONPATH}"

GATE_A=pass

echo "[E2E] install dry-run no writes"
MISS="$TMP/missing-target"
bash scripts/install-cursor.sh --target "$MISS" --dry-run
test ! -e "$MISS"

echo "[E2E] mutator blocked without ApprovalProvider (deny path)"
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
r2 = run_operation(operation_id="y", argv=["true"], effect="read", require_approval=False)
assert r2.outcome == "blocked" and "free-form" in r2.detail
print("free-form reject OK")
PY

echo "[E2E] complete without evidence fails"
python3 tools/workspace-router/run.py --repo "$TMP" --init >/dev/null
if python3 tools/workspace-router/run.py --repo "$TMP" --phase DEFINE --complete 2>/dev/null; then
  echo "FAIL: complete without run-id"; exit 1
fi

echo "[E2E] positive path: registry handler → verify → evidence → complete"
python3 - <<PY
from pathlib import Path
import sys
sys.path.insert(0, "tools")
sys.path.insert(0, "tools/workspace-router")
from execution.ops import run_verified
from execution.registry import register_handler
from status_bump import advance_status

repo = Path("$TMP")

def specify(params):
    (repo / "artifact.txt").write_text(params["content"], encoding="utf-8")
    return 0

def verify_spec(result, root):
    content = (root / "artifact.txt").read_text(encoding="utf-8")
    return [{"kind": "spec_deliverable", "ok": content == "spec-ok\n", "detail": "fixture content"}]

register_handler("specify", specify)
executed = run_verified(
    "specify",
    {"content": "spec-ok\n"},
    repo=repo,
    phase="DEFINE",
    skill="plan-specification",
    target="/fixture",
    plan_id="execution-e2e",
    task_id="define-spec",
    artifacts=["artifact.txt"],
    verifier=verify_spec,
)
assert executed.outcome == "succeeded", executed
assert executed.input_digest != executed.output_digest
rid = executed.run_id
s = advance_status(
    repo, phase="DEFINE", skill="plan-specification", evidence_ok=True, run_id=rid, target="/fixture"
)
assert s["phase"] == "DEFINE" and s["state_revision"] == 1
s2 = advance_status(
    repo, phase="DEFINE", skill="plan-specification", evidence_ok=True, run_id=rid, target="/fixture"
)
assert s2.get("_idempotent_replay") is True
print("positive complete + idempotency OK", rid)

(repo / "artifact.txt").write_text("stale\n", encoding="utf-8")
try:
    advance_status(repo, phase="DEFINE", skill="plan-specification", evidence_ok=True, run_id=rid, target="/fixture")
except ValueError as exc:
    assert "stale" in str(exc) or "mismatch" in str(exc), exc
else:
    raise AssertionError("stale evidence unexpectedly completed")
print("stale evidence rejected OK")

failed = run_verified(
    "specify",
    {"content": "wrong\n"},
    repo=repo,
    phase="DEFINE",
    skill="plan-specification",
    target="/fixture",
    plan_id="execution-e2e",
    task_id="failed-spec",
    artifacts=["artifact.txt"],
    verifier=verify_spec,
)
assert failed.outcome == "failed", failed
try:
    advance_status(
        repo, phase="DEFINE", skill="plan-specification", evidence_ok=True, run_id=failed.run_id, target="/fixture"
    )
except ValueError as exc:
    assert "outcome" in str(exc), exc
else:
    raise AssertionError("failed verification unexpectedly completed")
print("failed verification rejected OK")
PY

echo "=== E2E verdict ==="
echo "gate_A=$GATE_A"
echo "E2E gate_A OK"
