#!/usr/bin/env bash
# Native Pi orchestration with a real model on a disposable worktree.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT"
if [[ "${AW_NATIVE_OPT_IN:-}" != "1" ]]; then
  echo "not_run: set AW_NATIVE_OPT_IN=1 to authorize Pi model orchestration" >&2
  exit 3
fi
if ! command -v pi >/dev/null 2>&1; then
  echo "not_run: pi binary missing" >&2
  exit 3
fi
AW_PI_MODEL="${AW_PI_MODEL:-opencode-go/beam-free}"
export AW_PI_MODEL
if ! pi auth check --model "$AW_PI_MODEL" --json >/tmp/aw-pi-auth.json 2>&1; then
  echo "not_run: pi model auth not ready for $AW_PI_MODEL" >&2
  exit 3
fi
python3 - <<'PY'
import json
data = json.load(open("/tmp/aw-pi-auth.json", encoding="utf-8"))
assert data.get("status") == "ready", data
print("pi auth ready:", data)
PY

TMP=$(mktemp -d /tmp/autoworkspace-pi-orch-XXXXXX)
trap 'git worktree prune; rm -rf "$TMP"' EXIT
REPO="$TMP/repo"
git worktree add --detach "$REPO" HEAD >/dev/null
git -C "$REPO" config commit.gpgsign false

export AW_PI_MODEL="${AW_PI_MODEL:-kimi-coding/k3.1-pro}"
uv run --project tools --frozen python - "$REPO" "$ROOT" <<'PY'
import hashlib
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(sys.argv[2])
repo = Path(sys.argv[1])
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "workspace-router"))

from execution.evidence import load_evidence
from execution.ops import OpResult
from harness.pi import PiSubagentAdapter
from orchestrator.runner import WorktreeAdapter
from orchestrator.scheduler import Scheduler
from status_bump import activate_plan, load_status

revision = subprocess.run(
    ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
).stdout.strip()
plan = {
    "schema_version": 1,
    "plan_id": "pi-native-orchestration",
    "base_revision": revision,
    "tasks": [
        {
            "id": "write-sentinel",
            "phase": "IMPLEMENT",
            "operation": "implement_api",
            "roles": ["role-back"],
            "depends_on": [],
            "read_scope": ["README.md"],
            "write_scope": ["orchestration-sentinel.txt"],
            "artifacts": ["write-sentinel-patch"],
            "acceptance": ["sentinel-content"],
            "verification": ["independent-content-check"],
            "on_failure": "stop",
        }
    ],
}
path = repo / "plan.md"
path.write_text("# Fixture\n\n```yaml aw-plan\n" + yaml.safe_dump(plan, sort_keys=False) + "```\n")
activate_plan(repo, path)

def verifier_for(task):
    def verify(result: OpResult, staging: Path):
        path = staging / task["write_scope"][0]
        raw = path.read_text(encoding="utf-8") if path.is_file() else ""
        ok = path.is_file() and raw.strip() == task["id"] and result.outcome == "succeeded"
        return [{"kind": "implementation_deliverable", "ok": ok, "detail": repr(raw) if path.is_file() else "missing"}]
    return verify

adapter = WorktreeAdapter(
    repo,
    PiSubagentAdapter(model=__import__("os").environ.get("AW_PI_MODEL", "kimi-coding/k3.1-pro"), timeout=180),
    verifier_for,
)
summary = Scheduler(repo, adapter=adapter, max_parallel=1).run()
assert summary.outcome == "pass", summary
status = load_status(repo)
task = status["tasks"]["write-sentinel"]
assert task["state"] == "succeeded", task
evidence = load_evidence(
    repo,
    task["run_id"],
    expected_phase="IMPLEMENT",
    expected_skill="role-back",
    expected_target=str(repo),
    for_complete=True,
)
assert evidence["plan_id"] == "pi-native-orchestration"
assert not (repo / "orchestration-sentinel.txt").exists(), "must not mutate fixture checkout"
patches = list((repo / ".autoworkspace" / "runs").glob("*/*.patch"))
assert patches, "expected staged patch artifact"
verify = repo / ".autoworkspace" / "verify-tree"
subprocess.run(["git", "worktree", "add", "--detach", str(verify), "HEAD"], cwd=repo, check=True, capture_output=True)
subprocess.run(["git", "apply", str(patches[0])], cwd=verify, check=True, capture_output=True)
content = (verify / "orchestration-sentinel.txt").read_text(encoding="utf-8")
assert content.strip() == "write-sentinel", repr(content)
print("Pi orchestration PASS", "model=", __import__("os").environ.get("AW_PI_MODEL"), "digest=", hashlib.sha256(content.encode()).hexdigest()[:12])
PY

echo "Pi native orchestration OK"
