#!/usr/bin/env bash
# Native Cursor discovery B and policy C on a temporary project.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
export PATH="${HOME}/.local/bin:${PATH}"

if ! command -v agent >/dev/null 2>&1; then
  echo "blocked: agent binary not on PATH" >&2
  exit 3
fi

VERSION=$(agent --version)
echo "agent --version → ${VERSION}"

TMP=$(mktemp -d /tmp/autoworkspace-cursor-native-XXXXXX)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/project" "$TMP/policy"

bash "$ROOT/scripts/install.sh" --harness cursor --components full \
  --target "$TMP/project" --yes --json >"$TMP/install.json"

uv run --project "$ROOT/tools" --frozen python "$ROOT/tools/harness/cursor.py" \
  --target "$TMP/project" --catalog "$ROOT" --work-dir "$TMP/policy" --json \
  >"$TMP/report.json"

python3 - "$TMP/report.json" "$VERSION" <<'PY'
import json, sys
report = json.load(open(sys.argv[1]))
version = sys.argv[2]
assert report["outcome"] == "pass", report
assert report["harness_version"] == version or version in (report.get("harness_version") or "")
caps = report.get("capabilities") or {}
assert caps.get("B") == "pass", report
assert caps.get("C") == "pass", report
by_id = {c["id"]: c for c in report["checks"]}
assert by_id["cursor-native-discovery"]["outcome"] == "pass", by_id
assert by_id["cursor-native-policy"]["outcome"] == "pass", by_id
print("Cursor native B/C:", by_id["cursor-native-discovery"]["detail"])
print("Cursor native policy:", by_id["cursor-native-policy"]["detail"])
PY

# Explicit planner/worker/verifier presence after full install
python3 - "$TMP/project" <<'PY'
from pathlib import Path
import sys
agents = {p.name for p in (Path(sys.argv[1]) / ".cursor" / "agents").glob("*.md")}
for name in ("aw-planner.md", "aw-worker.md", "aw-verifier.md"):
    assert name in agents, agents
print("Cursor agents delegated:", sorted(agents))
PY

echo "Cursor native lifecycle OK"
