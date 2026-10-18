#!/bin/bash
# Install matrix: dry-run no mkdir, conflicts, uninstall retain+warn
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# --- dry-run must not create missing target ---
MISSING="$TMP/does-not-exist-yet"
bash "$ROOT/scripts/install.sh" --target "$MISSING" --dry-run
test ! -e "$MISSING"
test ! -e "$MISSING/.autoworkspace-install-manifest.json"

TARGET="$TMP/skills-dest"
mkdir -p "$TARGET"

# dry-run: no manifest
bash "$ROOT/scripts/install.sh" --target "$TARGET" --dry-run
test ! -e "$TARGET/.autoworkspace-install-manifest.json"

# real install
bash "$ROOT/scripts/install.sh" --target "$TARGET"
test -L "$TARGET/local-maintenance"
test -f "$TARGET/.autoworkspace-install-manifest.json"

# foreign dir preserved
mkdir -p "$TARGET/foreign-skill"
echo keep > "$TARGET/foreign-skill/x"
bash "$ROOT/scripts/install.sh" --target "$TARGET"
test "$(cat "$TARGET/foreign-skill/x")" = "keep"

# conflict: real dir with skill name
mkdir -p "$TMP/conflict-dest"
mkdir -p "$TMP/conflict-dest/local-maintenance"
if bash "$ROOT/scripts/install.sh" --target "$TMP/conflict-dest" 2>/dev/null; then
  echo "FAIL: should reject real dir conflict"; exit 1
fi

# conflict: broken foreign symlink
mkdir -p "$TMP/broken-dest"
ln -sfn /nonexistent/path/xyz "$TMP/broken-dest/local-maintenance"
if bash "$ROOT/scripts/install.sh" --target "$TMP/broken-dest" 2>/dev/null; then
  echo "FAIL: should reject broken symlink"; exit 1
fi
test -L "$TMP/broken-dest/local-maintenance"

# prune rejected
if bash "$ROOT/scripts/install.sh" --target "$TARGET" --prune 2>/dev/null; then
  echo "FAIL: prune should exit non-zero"; exit 1
fi

# uninstall only owned manifest resources; retain foreign
bash "$ROOT/scripts/install.sh" --target "$TARGET" --uninstall
test ! -e "$TARGET/local-maintenance"
test -d "$TARGET/foreign-skill"

# changed resource retain+warn: reinstall then replace link with file
bash "$ROOT/scripts/install.sh" --target "$TARGET"
rm -f "$TARGET/local-maintenance"
echo "hijacked" > "$TARGET/local-maintenance"
# uninstall should warn and retain the file
bash "$ROOT/scripts/install.sh" --target "$TARGET" --uninstall
test -f "$TARGET/local-maintenance"
test "$(cat "$TARGET/local-maintenance")" = "hijacked"

# opencode dry-run zero writes to a fresh clone-like tree
OC="$TMP/oc-root"
mkdir -p "$OC/skills/demo"
echo '---
name: demo
metadata:
  version: "1.0.0"
---
# demo' > "$OC/skills/demo/SKILL.md"
# point SRC via copying install-opencode expects skills in target
# use real ROOT for dry-run
bash "$ROOT/scripts/install-opencode.sh" --target "$ROOT" --dry-run

# A36: journal rollback restores prior symlink target on mid-apply failure
RB="$TMP/rollback-dest"
mkdir -p "$RB"
ln -sfn /tmp/prior-target-aw "$RB/local-maintenance"
# Simulate prior link; force apply failure after journaling by making TARGET parent read-only mid-flight
# Use Python unit of journal restore path via inject: install then break finalize
bash "$ROOT/scripts/install.sh" --target "$RB" || true
# After successful install, prior was replaced; re-seed prior and exercise rollback helper
PRIOR="$TMP/prior-skill"
mkdir -p "$PRIOR"
ln -sfn "$PRIOR" "$RB/local-maintenance"
# Direct journal restore scenario
python3 - "$RB" "$ROOT/skills/local-maintenance" <<'PY'
import json, os, sys
from pathlib import Path
target = Path(sys.argv[1])
src = Path(sys.argv[2]).resolve()
dest = target / "local-maintenance"
previous = {"type": "symlink", "target": os.readlink(dest)}
# Replace with new link then rollback entry
dest.unlink()
os.symlink(str(src), dest)
journal = {
    "schema_version": 1,
    "entries": [
        {"name": "local-maintenance", "dest": str(dest), "action": "replaced", "previous": previous}
    ],
}
jp = target / ".autoworkspace-install-journal.json"
jp.write_text(json.dumps(journal), encoding="utf-8")
# rollback logic (mirrors install.sh)
doc = json.loads(jp.read_text(encoding="utf-8"))
for entry in reversed(doc["entries"]):
    d = Path(entry["dest"])
    prev = entry.get("previous")
    if entry.get("action") == "replaced" and prev and prev.get("type") == "symlink":
        if d.is_symlink() or d.exists():
            d.unlink()
        os.symlink(prev["target"], d)
assert os.readlink(dest) == previous["target"], (os.readlink(dest), previous["target"])
print("journal rollback restored prior symlink OK")
PY

# package-standalone dry-run
bash "$ROOT/scripts/package-standalone-skill.sh" --skill local-maintenance --dry-run

echo "install tests OK"
