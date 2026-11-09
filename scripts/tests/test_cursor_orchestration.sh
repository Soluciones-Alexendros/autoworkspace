#!/usr/bin/env bash
# Native Cursor orchestration with a real headless agent on a disposable worktree.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT"
export PATH="${HOME}/.local/bin:${PATH}"

if ! command -v agent >/dev/null 2>&1; then
  echo "blocked: agent binary not on PATH" >&2
  exit 3
fi
VERSION=$(agent --version)
echo "agent --version → ${VERSION}"
if ! agent --list-models >/tmp/aw-cursor-models.txt 2>&1; then
  echo "not_run: agent authentication required for headless model run" >&2
  exit 3
fi

TMP=$(mktemp -d /tmp/autoworkspace-cursor-orch-XXXXXX)
trap 'git -C "$ROOT" worktree prune >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
REPO="$TMP/repo"
git worktree add --detach "$REPO" HEAD >/dev/null
git -C "$REPO" config commit.gpgsign false

# Replace committed .cursor tree with a transactional full install from the
# live catalog (includes planner/worker/verifier agents not yet on HEAD).
rm -rf "$REPO/.cursor"
bash "$ROOT/scripts/install.sh" --harness cursor --components full --target "$REPO" --yes >/dev/null

export AW_CURSOR_FORCE=1
uv run --project tools --frozen python - "$REPO" "$ROOT" "$VERSION" <<'PY'
import hashlib
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(sys.argv[2])
repo = Path(sys.argv[1])
version = sys.argv[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "workspace-router"))

from execution.evidence import load_evidence
from execution.ops import OpResult
from harness.cursor import CursorSubagentAdapter
from orchestrator.runner import WorktreeAdapter
from orchestrator.scheduler import Scheduler
from status_bump import activate_plan, load_status

revision = subprocess.run(
    ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
).stdout.strip()
plan = {
    "schema_version": 1,
    "plan_id": "cursor-native-orchestration",
    "base_revision": revision,
    "tasks": [
        {
            "id": "write-sentinel",
            "phase": "IMPLEMENT",
            "operation": "implement_api",
            "roles": ["role-back"],
            "depends_on": [],
            "read_scope": ["README.md"],
            "write_scope": ["cursor-orchestration-sentinel.txt"],
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
    CursorSubagentAdapter(force=True, timeout=240),
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
assert evidence["plan_id"] == "cursor-native-orchestration"
assert not (repo / "cursor-orchestration-sentinel.txt").exists()
patches = list((repo / ".autoworkspace" / "runs").glob("*/*.patch"))
assert patches
verify = repo / ".autoworkspace" / "verify-tree"
subprocess.run(["git", "worktree", "add", "--detach", str(verify), "HEAD"], cwd=repo, check=True, capture_output=True)
subprocess.run(["git", "apply", str(patches[0])], cwd=verify, check=True, capture_output=True)
content = (verify / "cursor-orchestration-sentinel.txt").read_text(encoding="utf-8")
assert content.strip() == "write-sentinel", repr(content)
print(
    "Cursor orchestration PASS",
    "agent=",
    version,
    "digest=",
    hashlib.sha256(content.encode()).hexdigest()[:12],
)
PY

echo "Cursor native orchestration OK"
