#!/usr/bin/env bash
# Native Cursor discovery B and policy C on a temporary project.
# Level A is static install; B requires real Cursor sessionStart; C requires
# beforeShellExecution allow/deny/ask observed via Cursor without --force/--yolo.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
export PATH="${HOME}/.local/bin:${PATH}"

if ! command -v agent >/dev/null 2>&1; then
  echo "blocked: agent binary not on PATH" >&2
  exit 3
fi

VERSION=$(agent --version)
echo "agent --version → ${VERSION}"

TMP=$(mktemp -d /tmp/machineroom-cursor-native-XXXXXX)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/project" "$TMP/policy"

bash "$ROOT/scripts/install.sh" --harness cursor --components full \
  --target "$TMP/project" --yes --json >"$TMP/install.json"

# cursor.py exits 0 when A/B/C pass; 3 when required capability blocked/not_run.
set +e
uv run --project "$ROOT/tools" --frozen python "$ROOT/tools/harness/cursor.py" \
  --target "$TMP/project" --catalog "$ROOT" --work-dir "$TMP/policy" --json \
  >"$TMP/report.json"
report_rc=$?
set -e
echo "cursor.py exit=${report_rc}"

python3 - "$TMP/report.json" "$VERSION" "$TMP/policy" <<'PY'
import json, sys
from pathlib import Path

report = json.load(open(sys.argv[1]))
version = sys.argv[2]
policy_dir = Path(sys.argv[3])
caps = report.get("capabilities") or {}
by_id = {c["id"]: c for c in report["checks"]}
assert by_id["cursor-static-install"]["outcome"] == "pass", by_id
assert by_id["cursor-cli-version"]["outcome"] == "pass", by_id
# B must come from Cursor sessionStart, not filesystem alone.
assert caps.get("B") == "pass", report
assert by_id["cursor-native-discovery"]["outcome"] == "pass", by_id
# C: allow/deny/ask via Cursor-invoked beforeShellExecution, never --force/--yolo.
assert by_id["cursor-native-policy"]["outcome"] == "pass", by_id
assert caps.get("C") == "pass", report
assert report["outcome"] == "pass", report
detail = by_id["cursor-native-policy"]["detail"]
assert "without --force/--yolo" in detail, detail
receipt = policy_dir / "policy-receipt.json"
assert receipt.is_file(), receipt
data = json.loads(receipt.read_text(encoding="utf-8"))
assert data.get("force_flags") is False, data
assert data.get("decisions") == {"allow": "allow", "deny": "deny", "ask": "ask"}, data
print("Cursor native A/B:", by_id["cursor-native-discovery"]["detail"])
print("Cursor native C pass:", detail)
PY

# Negative: corrupt hooks.json — B must fail even if skill paths still exist.
rm -f "$TMP/project/.cursor/hooks.json"
uv run --project "$ROOT/tools" --frozen python "$ROOT/tools/harness/cursor.py" \
  --target "$TMP/project" --catalog "$ROOT" --work-dir "$TMP/policy-corrupt" --json \
  >"$TMP/report-corrupt.json" || true
python3 - "$TMP/report-corrupt.json" <<'PY'
import json, sys
report = json.load(open(sys.argv[1]))
by_id = {c["id"]: c for c in report["checks"]}
# Static A or native B must fail when hooks.json is gone.
assert by_id["cursor-static-install"]["outcome"] == "fail" or by_id["cursor-native-discovery"]["outcome"] == "fail", by_id
print("seeded hooks.json absence breaks discovery as required")
PY

# Explicit planner/worker/verifier presence after full install (reinstall for agents check)
bash "$ROOT/scripts/install.sh" --harness cursor --components full \
  --target "$TMP/project" --yes >/dev/null
python3 - "$TMP/project" <<'PY'
from pathlib import Path
import sys
agents = {p.name for p in (Path(sys.argv[1]) / ".cursor" / "agents").glob("*.md")}
for name in ("mr-planner.md", "mr-worker.md", "mr-verifier.md"):
    assert name in agents, agents
print("Cursor agents delegated:", sorted(agents))
PY

echo "Cursor native lifecycle OK (A/B/C pass without --force/--yolo)"
exit 0
