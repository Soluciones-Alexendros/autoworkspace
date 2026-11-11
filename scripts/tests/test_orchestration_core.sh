#!/usr/bin/env bash
# Complete controlled orchestration path on disposable Git worktrees.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT"
export PYTHONPATH="$ROOT/tools${PYTHONPATH:+:$PYTHONPATH}"

uv run --project tools --frozen pytest \
  tools/orchestrator/tests/test_full_flow.py \
  tools/orchestrator/tests/test_orchestration_red.py \
  tools/orchestrator/tests/test_worktrees.py \
  tools/orchestrator/tests/test_scheduler.py \
  -q

# --plan dry-run must validate the aw-plan block without writing status or bytes.
STATUS_BEFORE=$(sha256sum .machineroom/status.yaml | awk '{print $1}')
uv run --project tools --frozen python tools/orchestrator/run.py \
  --repo "$ROOT" \
  --plan tasks/plan-autoworkspace-remediation.md \
  --adapter pi \
  --dry-run \
  --json >/tmp/mr-orch-dry-run.json
STATUS_AFTER=$(sha256sum .machineroom/status.yaml | awk '{print $1}')
test "$STATUS_BEFORE" = "$STATUS_AFTER"
python3 - <<'PY'
import json
payload = json.load(open("/tmp/mr-orch-dry-run.json", encoding="utf-8"))
assert payload["outcome"] == "simulated"
assert payload["plan_id"] == "auto" "workspace-remediation-v1"
assert payload["digest"]
assert payload["waves"]
print("dry-run --plan OK:", payload["digest"][:12], "waves", len(payload["waves"]))
PY

echo "orchestration core OK"
