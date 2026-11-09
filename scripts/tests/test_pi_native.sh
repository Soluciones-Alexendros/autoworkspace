#!/usr/bin/env bash
# Native Pi package discovery and lifecycle in isolated HOME directories.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
if ! command -v pi >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "not_run: Pi or npm binary not found" >&2
  exit 3
fi
TMP=$(mktemp -d /tmp/autoworkspace-pi-native-XXXXXX)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/home" "$TMP/project" "$TMP/home/.pi/agent/skills/foreign-skill"
cat >"$TMP/home/.pi/agent/skills/foreign-skill/SKILL.md" <<'EOF'
---
name: foreign-skill
description: Foreign fixture skill preserved during uninstall.
---
# Foreign fixture
EOF

# Pi installs Git packages with production dependencies. The development hook
# must be inert when husky is omitted (regression: v7.0.2 prepare failure).
mkdir -p "$TMP/production-package/scripts"
cp "$ROOT/package.json" "$TMP/production-package/package.json"
cp "$ROOT/scripts/prepare.mjs" "$TMP/production-package/scripts/prepare.mjs"
(
  cd "$TMP/production-package"
  npm install --omit=dev --legacy-peer-deps --no-audit --no-fund
)

export HOME="$TMP/home"
pi install "$ROOT"
pi install "$ROOT"
pi list >"$TMP/packages.txt"
uv run --project "$ROOT/tools" --frozen python "$ROOT/tools/harness/pi.py" --cwd "$TMP/project" --catalog "$ROOT" --json >"$TMP/report.json"
python3 - "$TMP/report.json" <<'PY'
import json, sys
report = json.load(open(sys.argv[1]))
assert report["outcome"] == "pass", report
assert report["harness_version"]
assert report["capabilities"]["B"] == "pass"
print("Pi native package discovery:", report["checks"][0]["detail"])
PY
uv run --project "$ROOT/tools" --frozen python - "$TMP/project" "$ROOT" <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, "tools")
from harness.pi import rpc_commands
root = Path(sys.argv[2])
manifest = json.loads((root / "package.json").read_text())
commands = rpc_commands(Path(sys.argv[1]))
if manifest.get("pi", {}).get("extensions"):
    status = [c for c in commands if c.get("name") == "aw-status" and c.get("source") == "extension"]
    assert len(status) == 1, status
    print("Pi packaged extension loaded: aw-status")
PY

pi remove "$ROOT"
uv run --project "$ROOT/tools" --frozen python - "$TMP/project" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, "tools")
from harness.pi import rpc_commands
commands = rpc_commands(Path(sys.argv[1]))
names = {c.get("name") for c in commands}
assert "skill:foreign-skill" in names, names
assert "skill:plan-continue" not in names, names
print("Pi uninstall preserved foreign skill and removed package skills")
PY

if [[ "${AW_PI_GIT_SMOKE:-0}" == "1" ]]; then
  FROM_TAG="${AW_PI_GIT_FROM_TAG:-v7.0.3}"
  TO_TAG="${AW_PI_GIT_TO_TAG:?set AW_PI_GIT_TO_TAG to the newly published release}"
  export HOME="$TMP/git-home"
  mkdir -p "$HOME" "$TMP/git-project"
  pi install "git:github.com/Soluciones-Alexendros/autoworkspace@${FROM_TAG}"
  uv run --project "$ROOT/tools" --frozen python "$ROOT/tools/harness/pi.py" --cwd "$TMP/git-project" --catalog "$ROOT" --json >"$TMP/from-tag.json"
  pi install "git:github.com/Soluciones-Alexendros/autoworkspace@${TO_TAG}"
  uv run --project "$ROOT/tools" --frozen python "$ROOT/tools/harness/pi.py" --cwd "$TMP/git-project" --catalog "$ROOT" --json >"$TMP/to-tag.json"
  python3 - "$TMP/from-tag.json" "$TMP/to-tag.json" <<'PY'
import json, sys
for path in sys.argv[1:]:
    report = json.load(open(path))
    assert report["outcome"] == "pass", report
print("Pi Git from/to tags discovered the full package catalog")
PY
  pi remove "git:github.com/Soluciones-Alexendros/autoworkspace@${TO_TAG}"
fi

echo "Pi native lifecycle OK"
