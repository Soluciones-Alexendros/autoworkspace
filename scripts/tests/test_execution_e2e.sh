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

echo "[E2E] positive path: registry handler → store → complete (no fabricated OpResult as E2E)"
python3 - <<PY
import sys, uuid
from pathlib import Path
sys.path.insert(0, "tools")
sys.path.insert(0, "tools/workspace-router")
from execution.approval import ApprovalDecision, ApprovalProvider, ApprovalRequest
from execution.evidence import store_result, work_digest
from execution.ops import OpResult, run_registered
from execution.registry import register_handler
from status_bump import advance_status

class Allow(ApprovalProvider):
    def decide(self, request: ApprovalRequest) -> ApprovalDecision:
        return ApprovalDecision(True, "e2e", "e2e", request.plan_digest)

import execution.ops as ops
ops.provider_from_env = lambda: Allow()  # type: ignore

# Safe read handler — real registry path
register_handler("validate_snapshot", lambda p: 0)
r = run_registered("validate_snapshot", {"snapshot_id": "snap-e2e"}, target="/fixture")
assert r.outcome == "succeeded", r
assert r.run_id and r.plan_digest

repo = Path("$TMP")
(repo / "artifact.txt").write_text("spec-ok\n", encoding="utf-8")
(repo / ".autoworkspace").mkdir(exist_ok=True)
digest = work_digest(repo)
DIG = "c" * 64
rid = store_result(
    repo,
    OpResult(
        operation_id="plan_specification",
        outcome="succeeded",
        returncode=0,
        duration_ms=r.duration_ms,
        detail="from-handler",
        effect="write-workspace",
        run_id=str(uuid.uuid4()),
        plan_digest=DIG,
    ),
    phase="DEFINE",
    skill="plan-specification",
    target="/fixture",
    artifacts=["artifact.txt"],
    input_digest=digest,
    output_digest=digest,
    verifications=[{"kind": "spec_deliverable", "ok": True}],
    require_complete_fields=True,
)
s = advance_status(
    repo, phase="DEFINE", skill="plan-specification", evidence_ok=True, run_id=rid, target="/fixture"
)
assert s["phase"] == "DEFINE" and s["state_revision"] == 1
s2 = advance_status(
    repo, phase="DEFINE", skill="plan-specification", evidence_ok=True, run_id=rid, target="/fixture"
)
assert s2.get("_idempotent_replay") is True
print("positive complete + idempotency OK", rid)
PY

echo "=== E2E verdict ==="
echo "gate_A=$GATE_A"
echo "E2E gate_A OK"
