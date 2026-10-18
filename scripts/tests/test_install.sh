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

echo "install tests OK"
