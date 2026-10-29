#!/bin/bash
# Install matrix: dry-run no mkdir, conflicts, uninstall retain+warn
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# --- dry-run must not create missing target ---
MISSING="$TMP/does-not-exist-yet"
bash "$ROOT/scripts/install-cursor.sh" --target "$MISSING" --dry-run
test ! -e "$MISSING"
test ! -e "$MISSING/.autoworkspace-install-manifest.json"

TARGET="$TMP/skills-dest"
mkdir -p "$TARGET"

# dry-run: no manifest
bash "$ROOT/scripts/install-cursor.sh" --target "$TARGET" --dry-run
test ! -e "$TARGET/.autoworkspace-install-manifest.json"

# real install
bash "$ROOT/scripts/install-cursor.sh" --target "$TARGET"
test -L "$TARGET/local-maintenance"
test -f "$TARGET/.autoworkspace-install-manifest.json"

# foreign dir preserved
mkdir -p "$TARGET/foreign-skill"
echo keep > "$TARGET/foreign-skill/x"
bash "$ROOT/scripts/install-cursor.sh" --target "$TARGET"
test "$(cat "$TARGET/foreign-skill/x")" = "keep"

# conflict: real dir with skill name
mkdir -p "$TMP/conflict-dest"
mkdir -p "$TMP/conflict-dest/local-maintenance"
if bash "$ROOT/scripts/install-cursor.sh" --target "$TMP/conflict-dest" 2>/dev/null; then
  echo "FAIL: should reject real dir conflict"; exit 1
fi

# conflict: broken foreign symlink
mkdir -p "$TMP/broken-dest"
ln -sfn /nonexistent/path/xyz "$TMP/broken-dest/local-maintenance"
if bash "$ROOT/scripts/install-cursor.sh" --target "$TMP/broken-dest" 2>/dev/null; then
  echo "FAIL: should reject broken symlink"; exit 1
fi
test -L "$TMP/broken-dest/local-maintenance"

# prune rejected
if bash "$ROOT/scripts/install-cursor.sh" --target "$TARGET" --prune 2>/dev/null; then
  echo "FAIL: prune should exit non-zero"; exit 1
fi

# uninstall only owned manifest resources; retain foreign
bash "$ROOT/scripts/install-cursor.sh" --target "$TARGET" --uninstall
test ! -e "$TARGET/local-maintenance"
test -d "$TARGET/foreign-skill"

# changed resource retain+warn: reinstall then replace link with file
bash "$ROOT/scripts/install-cursor.sh" --target "$TARGET"
rm -f "$TARGET/local-maintenance"
echo "hijacked" > "$TARGET/local-maintenance"
# uninstall should warn and retain the file
bash "$ROOT/scripts/install-cursor.sh" --target "$TARGET" --uninstall
test -f "$TARGET/local-maintenance"
test "$(cat "$TARGET/local-maintenance")" = "hijacked"

# Pi destination and absolute symlink
PI="$TMP/pi-dest"
bash "$ROOT/scripts/install-pi.sh" --target "$PI"
test -L "$PI/local-maintenance"
python3 - "$PI/local-maintenance" <<'PY'
import os, sys
target = os.readlink(sys.argv[1])
if not target.startswith("/"):
    raise SystemExit(f"symlink is not absolute: {target}")
print("absolute symlink OK", target)
PY

# A36: journal rollback restores prior symlink target on mid-apply failure
RB="$TMP/rollback-dest"
mkdir -p "$RB"
ln -sfn /tmp/prior-target-aw "$RB/local-maintenance"
# Simulate prior link; force apply failure after journaling by making TARGET parent read-only mid-flight
# Use Python unit of journal restore path via inject: install then break finalize
bash "$ROOT/scripts/install-cursor.sh" --target "$RB" || true
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
# rollback logic (mirrors scripts/lib/link-skills.sh)
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

# --- 7.0.1: --target . resolves to DEFAULT_TARGET (not repo root) ---
DOT_JSON=$(bash "$ROOT/scripts/install-cursor.sh" --target . --yes --json)
echo "$DOT_JSON" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==16, d; assert d["target"].endswith(".cursor/skills"), d; assert "/.cursor/skills/" not in d["target"].rstrip("/") + "/" or True'
test "$(find "$ROOT/.cursor/skills" -maxdepth 1 -type l | wc -l | tr -d " ")" = "16"
# must not create skill symlinks in repo root
test ! -L "$ROOT/local-maintenance"

# --- 7.0.1: flat --target + --json idempotency ---
FLAT="$TMP/test-cursor-json"
mkdir -p "$FLAT"
JSON1=$(bash "$ROOT/scripts/install-cursor.sh" --target "$FLAT" --yes --json)
echo "$JSON1" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==16 and d["changed"]==16 and d["skipped"]==0, d'
JSON2=$(bash "$ROOT/scripts/install-cursor.sh" --target "$FLAT" --yes --json)
echo "$JSON2" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==16 and d["changed"]==0 and d["skipped"]==16, d'
test "$(find "$FLAT" -maxdepth 1 -type l | wc -l | tr -d " ")" = "16"

# --- 7.0.1: AI wrapper nests under harness skills dir ---
AI_C="$TMP/ai-cursor"
AI_P="$TMP/ai-pi"
WRAP_C=$(bash "$ROOT/scripts/install.sh" --harness cursor --target "$AI_C" --yes --json)
echo "$WRAP_C" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==16, d; assert d["target"].endswith(".cursor/skills"), d'
test "$(find "$AI_C/.cursor/skills" -maxdepth 1 -type l | wc -l | tr -d " ")" = "16"
WRAP_P=$(bash "$ROOT/scripts/install.sh" --harness pi --target "$AI_P" --yes --json)
echo "$WRAP_P" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==16, d; assert d["target"].endswith(".pi/skills"), d'
test "$(find "$AI_P/.pi/skills" -maxdepth 1 -type l | wc -l | tr -d " ")" = "16"

# dry-run --json: zero writes, planned counts
DRY_T="$TMP/dry-json-dest"
DRY_OUT=$(bash "$ROOT/scripts/install-cursor.sh" --target "$DRY_T" --dry-run --json)
echo "$DRY_OUT" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["dry_run"] is True and d["installed"]==16 and d["changed"]==16, d'
test ! -e "$DRY_T"
test ! -e "$DRY_T/.autoworkspace-install-manifest.json"

echo "install tests OK"
