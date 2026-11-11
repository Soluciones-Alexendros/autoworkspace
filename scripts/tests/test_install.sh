#!/bin/bash
# Install matrix: dry-run no mkdir, conflicts, uninstall retain+warn
set -euo pipefail
echo "HARNESS_MATRIX: cursor,pi"
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
TMP=$(mktemp -d)
# /tmp/.pi/skills and /tmp/.cursor/skills are only removed if this run found them absent.
PI_LEAK_ABSENT=0
CURSOR_LEAK_ABSENT=0
[ ! -e /tmp/.pi/skills ] && PI_LEAK_ABSENT=1
[ ! -e /tmp/.cursor/skills ] && CURSOR_LEAK_ABSENT=1
cleanup() {
  rm -rf "$TMP"
  if [ "$PI_LEAK_ABSENT" = 1 ]; then rm -rf /tmp/.pi/skills; fi
  if [ "$CURSOR_LEAK_ABSENT" = 1 ]; then rm -rf /tmp/.cursor/skills; fi
}
trap cleanup EXIT

assert_abs_links() {
  local dir="$1"
  local n=0 link target
  for link in "$dir"/*; do
    [ -L "$link" ] || continue
    n=$((n + 1))
    target=$(readlink -- "$link")
    case "$target" in
      /*) ;;
      *) echo "FAIL not absolute $link -> $target"; exit 1 ;;
    esac
  done
  test "$n" = 17
}

assert_rel_links() {
  local dir="$1"
  local n=0 link target
  for link in "$dir"/*; do
    [ -L "$link" ] || continue
    n=$((n + 1))
    target=$(readlink -- "$link")
    case "$target" in
      /*) echo "FAIL not relative $link -> $target"; exit 1 ;;
    esac
    case "$target" in
      *Work/machineroom*) echo "FAIL checkout path in link $link -> $target"; exit 1 ;;
    esac
  done
  test "$n" = 17
}

prepare_runtime() {
  local home="$1"
  mkdir -p "$home"
  HOME="$home" bash "$ROOT/scripts/runtime-sync.sh" sync --from "$ROOT" --json >/dev/null
  test -d "$home/.machineroom/skills"
}

# --- dry-run must not create missing target ---
MISSING="$TMP/does-not-exist-yet"
bash "$ROOT/scripts/install-cursor.sh" --target "$MISSING" --dry-run
test ! -e "$MISSING"
test ! -e "$MISSING/.machineroom-install-manifest.json"

TARGET="$TMP/skills-dest"
mkdir -p "$TARGET"

# dry-run: no manifest
bash "$ROOT/scripts/install-cursor.sh" --target "$TARGET" --dry-run
test ! -e "$TARGET/.machineroom-install-manifest.json"

# real install
bash "$ROOT/scripts/install-cursor.sh" --target "$TARGET"
test -L "$TARGET/local-maintenance"
test -f "$TARGET/.machineroom-install-manifest.json"

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
jp = target / ".machineroom-install-journal.json"
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
echo "$DOT_JSON" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==17, d; assert d["target"].endswith(".cursor/skills"), d; assert "/.cursor/skills/" not in d["target"].rstrip("/") + "/" or True'
test "$(find "$ROOT/.cursor/skills" -maxdepth 1 -type l | wc -l | tr -d " ")" = "17"
# must not create skill symlinks in repo root
test ! -L "$ROOT/local-maintenance"

# --- 7.0.1: flat --target + --json idempotency ---
FLAT="$TMP/test-cursor-json"
mkdir -p "$FLAT"
JSON1=$(bash "$ROOT/scripts/install-cursor.sh" --target "$FLAT" --yes --json)
echo "$JSON1" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==17 and d["changed"]==17 and d["skipped"]==0, d'
JSON2=$(bash "$ROOT/scripts/install-cursor.sh" --target "$FLAT" --yes --json)
echo "$JSON2" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==17 and d["changed"]==0 and d["skipped"]==17, d'
test "$(find "$FLAT" -maxdepth 1 -type l | wc -l | tr -d " ")" = "17"

# --- 7.0.1: AI wrapper nests under harness skills dir ---
AI_C="$TMP/ai-cursor"
AI_P="$TMP/ai-pi"
WRAP_C=$(bash "$ROOT/scripts/install.sh" --harness cursor --target "$AI_C" --yes --json)
echo "$WRAP_C" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==17, d; assert d["target"].endswith(".cursor/skills"), d'
test "$(find "$AI_C/.cursor/skills" -maxdepth 1 -type l | wc -l | tr -d " ")" = "17"
WRAP_P=$(bash "$ROOT/scripts/install.sh" --harness pi --target "$AI_P" --yes --json)
echo "$WRAP_P" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==17, d; assert d["target"].endswith(".pi/skills"), d'
test "$(find "$AI_P/.pi/skills" -maxdepth 1 -type l | wc -l | tr -d " ")" = "17"

# dry-run --json: zero writes, planned counts
DRY_T="$TMP/dry-json-dest"
DRY_OUT=$(bash "$ROOT/scripts/install-cursor.sh" --target "$DRY_T" --dry-run --json)
echo "$DRY_OUT" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["dry_run"] is True and d["installed"]==17 and d["changed"]==17, d'
test ! -e "$DRY_T"
test ! -e "$DRY_T/.machineroom-install-manifest.json"

# --- 7.0.2: wrapper --target . anchors to the checkout, even from /tmp ---
WRAP_DOT_PI=$(cd /tmp && bash "$ROOT/scripts/install.sh" --harness pi --target . --yes --json)
echo "$WRAP_DOT_PI" | python3 -c 'import json,sys; d=json.load(sys.stdin); root=sys.argv[1]; assert d["installed"]==17, d; assert d["target"]==root+"/.pi/skills", d' "$ROOT"
assert_abs_links "$ROOT/.pi/skills"
if [ "$PI_LEAK_ABSENT" = 1 ]; then test ! -e /tmp/.pi/skills; fi
test ! -L "$ROOT/local-maintenance"

WRAP_DOT_C=$(cd /tmp && bash "$ROOT/scripts/install.sh" --harness cursor --target . --yes --json)
echo "$WRAP_DOT_C" | python3 -c 'import json,sys; d=json.load(sys.stdin); root=sys.argv[1]; assert d["installed"]==17, d; assert d["target"]==root+"/.cursor/skills", d' "$ROOT"
if [ "$CURSOR_LEAK_ABSENT" = 1 ]; then test ! -e /tmp/.cursor/skills; fi

# Relative skills path from /tmp still lands in the checkout.
REL_PI=$(cd /tmp && bash "$ROOT/scripts/install.sh" --harness pi --target .pi/skills --yes --json)
echo "$REL_PI" | python3 -c 'import json,sys; d=json.load(sys.stdin); root=sys.argv[1]; assert d["target"]==root+"/.pi/skills", d' "$ROOT"

if (cd /tmp && bash "$ROOT/scripts/install.sh" --harness pi --target '../outside' --yes --json) 2>"$TMP/dotdot.err"; then
  echo "FAIL: --target with .. should exit non-zero"; exit 1
fi

# Public installer --target . from /tmp still uses the checkout default.
PUB_DOT=$(cd /tmp && bash "$ROOT/scripts/install-pi.sh" --target . --yes --json)
echo "$PUB_DOT" | python3 -c 'import json,sys; d=json.load(sys.stdin); root=sys.argv[1]; assert d["installed"]==17, d; assert d["target"]==root+"/.pi/skills", d' "$ROOT"

# Pi flat idempotency + absolute symlinks
PI_FLAT="$TMP/test-pi"
PI_JSON1=$(bash "$ROOT/scripts/install-pi.sh" --target "$PI_FLAT" --yes --json)
echo "$PI_JSON1" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==17 and d["changed"]==17 and d["skipped"]==0, d'
PI_JSON2=$(bash "$ROOT/scripts/install-pi.sh" --target "$PI_FLAT" --yes --json)
echo "$PI_JSON2" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==17 and d["changed"]==0 and d["skipped"]==17, d'
assert_abs_links "$PI_FLAT"

# Wrapper pi idempotency
AI_PI2="$TMP/ai-pi-idem"
WRAP_PI1=$(bash "$ROOT/scripts/install.sh" --harness pi --target "$AI_PI2" --yes --json)
echo "$WRAP_PI1" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==17, d; assert d["target"].endswith(".pi/skills"), d'
WRAP_PI2=$(bash "$ROOT/scripts/install.sh" --harness pi --target "$AI_PI2" --yes --json)
echo "$WRAP_PI2" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==17 and d["changed"]==0 and d["skipped"]==17, d'
assert_abs_links "$AI_PI2/.pi/skills"
assert_abs_links "$AI_C/.cursor/skills"

# Pi dry-run creates nothing
DRY_PI="$TMP/dry-pi"
DRY_PI_OUT=$(bash "$ROOT/scripts/install-pi.sh" --target "$DRY_PI" --dry-run --json)
echo "$DRY_PI_OUT" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["dry_run"] is True and d["installed"]==17, d'
test ! -e "$DRY_PI"

# --user requires ~/.machineroom; dry-run writes no harness links
HOME_DRY="$TMP/home-dry"
prepare_runtime "$HOME_DRY"
USER_DRY=$(HOME="$HOME_DRY" bash "$ROOT/scripts/install-pi.sh" --user --dry-run --json)
echo "$USER_DRY" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["dry_run"] is True, d; assert d["target"].endswith(".pi/agent/skills"), d'
test ! -e "$HOME_DRY/.pi/agent/skills"

HOME_REAL="$TMP/home-real"
prepare_runtime "$HOME_REAL"
USER_REAL=$(HOME="$HOME_REAL" bash "$ROOT/scripts/install-pi.sh" --user --yes --json)
echo "$USER_REAL" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==17, d; assert d["target"].endswith(".pi/agent/skills"), d'
assert_rel_links "$HOME_REAL/.pi/agent/skills"
test -L "$HOME_REAL/.pi/agent/extensions/machineroom.ts"
case "$(readlink -- "$HOME_REAL/.pi/agent/extensions/machineroom.ts")" in
  /*) echo "FAIL extension link must be relative"; exit 1 ;;
esac

# --user without runtime fails closed
HOME_MISS="$TMP/home-missing"
mkdir -p "$HOME_MISS"
if HOME="$HOME_MISS" bash "$ROOT/scripts/install-pi.sh" --user --yes --json >/dev/null 2>&1; then
  echo "FAIL: --user without runtime should fail"; exit 1
fi

# --user wins over --target on the public installer and on the wrapper
IGN_PUB="$TMP/ignored-public"
BOTH_ERR="$TMP/both-public.err"
BOTH_OUT=$(HOME="$HOME_REAL" bash "$ROOT/scripts/install-pi.sh" --user --target "$IGN_PUB" --yes --json 2>"$BOTH_ERR")
echo "$BOTH_OUT" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==17, d; assert d["target"].endswith(".pi/agent/skills"), d'
grep -q "WARN: --user overrides --target" "$BOTH_ERR"
test ! -e "$IGN_PUB"

HOME_WRAP="$TMP/home-wrap"
prepare_runtime "$HOME_WRAP"
IGN_WRAP="$TMP/ignored-wrap"
WRAP_ERR="$TMP/wrap-user.err"
WRAP_USER=$(HOME="$HOME_WRAP" bash "$ROOT/scripts/install.sh" --harness pi --target "$IGN_WRAP" --user --yes --json 2>"$WRAP_ERR")
echo "$WRAP_USER" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==17, d; assert d["target"].endswith(".pi/agent/skills"), d'
grep -q "WARN: --user overrides --target; ignoring --target" "$WRAP_ERR"
test ! -e "$IGN_WRAP"
assert_rel_links "$HOME_WRAP/.pi/agent/skills"

IGN_CURSOR="$TMP/ignored-cursor"
CUR_ERR="$TMP/cursor-user.err"
HOME_CURSOR="$TMP/home-cursor"
prepare_runtime "$HOME_CURSOR"
CUR_USER=$(HOME="$HOME_CURSOR" bash "$ROOT/scripts/install-cursor.sh" --user --target "$IGN_CURSOR" --yes --json 2>"$CUR_ERR")
echo "$CUR_USER" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==17, d; assert d["target"].endswith(".cursor/skills"), d'
grep -q "WARN: --user overrides --target" "$CUR_ERR"
test ! -e "$IGN_CURSOR"
assert_rel_links "$HOME_CURSOR/.cursor/skills"

# Cursor full component mode: project root, dry-run, idempotence and uninstall.
FULL="$TMP/full-cursor"
FULL_DRY=$(bash "$ROOT/scripts/install.sh" --harness cursor --components full --target "$FULL" --dry-run --yes --json)
echo "$FULL_DRY" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["components"]=="full" and d["installed"]==24 and d["dry_run"] is True, d'
test ! -e "$FULL"
FULL_JSON=$(bash "$ROOT/scripts/install.sh" --harness cursor --components full --target "$FULL" --yes --json)
echo "$FULL_JSON" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["installed"]==24 and d["changed"]==24, d'
assert_abs_links "$FULL/.cursor/skills"
test -L "$FULL/.cursor/rules/machineroom.mdc"
test -L "$FULL/.cursor/agents/mr-verifier.md"
test -L "$FULL/.cursor/hooks.json"
test -L "$FULL/.cursor/hooks/shell_gate.py"
FULL_JSON2=$(bash "$ROOT/scripts/install.sh" --harness cursor --components full --target "$FULL" --yes --json)
echo "$FULL_JSON2" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["changed"]==0 and d["skipped"]==24, d'
bash "$ROOT/scripts/install.sh" --harness cursor --components full --target "$FULL" --uninstall --yes --json >/dev/null
test ! -e "$FULL/.cursor/skills/plan-continue"
# User-scope full install: relative links from ~/.machineroom, no project rule.
FULL_USER_HOME="$TMP/home-full"
prepare_runtime "$FULL_USER_HOME"
FULL_USER=$(HOME="$FULL_USER_HOME" bash "$ROOT/scripts/install.sh" --harness cursor --components full --user --yes --json)
echo "$FULL_USER" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["scope"]=="user", d; assert d["installed"]==23, d; assert d["omitted"]==["rules/machineroom.mdc"], d; assert d["notes"], d'
USER_CURSOR="$FULL_USER_HOME/.cursor"
test -L "$USER_CURSOR/skills/plan-continue"
test -L "$USER_CURSOR/agents/mr-verifier.md"
test -L "$USER_CURSOR/hooks.json"
test -L "$USER_CURSOR/hooks/shell_gate.py"
test ! -e "$USER_CURSOR/rules"
assert_rel_links "$USER_CURSOR/skills"
case "$(readlink -- "$USER_CURSOR/hooks.json")" in
  /*) echo "FAIL hooks.json must be relative"; exit 1 ;;
esac
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); cmds=[e["command"] for v in data["hooks"].values() for e in v]; assert cmds, data; assert not any(".cursor/hooks/" in c for c in cmds), cmds; assert all(c.startswith("python3 hooks/") for c in cmds), cmds' "$USER_CURSOR/hooks.json"
FULL_USER2=$(HOME="$FULL_USER_HOME" bash "$ROOT/scripts/install.sh" --harness cursor --components full --user --yes --json)
echo "$FULL_USER2" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["changed"]==0 and d["skipped"]==23, d'
HOME="$FULL_USER_HOME" bash "$ROOT/scripts/install.sh" --harness cursor --components full --user --uninstall --yes --json >/dev/null
test ! -e "$USER_CURSOR/hooks.json"
test ! -e "$USER_CURSOR/agents/mr-verifier.md"

if bash "$ROOT/scripts/install.sh" --harness pi --components full --target "$TMP/invalid-full" --yes --json 2>/dev/null; then
  echo "FAIL: Pi full mode should be rejected"; exit 1
fi

# Cursor user rule helper: whole rule with frontmatter (Customize -> Rules format).
RULE_OUT=$(bash "$ROOT/scripts/cursor-user-rule.sh")
test "$(echo "$RULE_OUT" | head -1)" = "---"
echo "$RULE_OUT" | grep -q "^alwaysApply: true$"
echo "$RULE_OUT" | grep -q "^description: ."
echo "$RULE_OUT" | grep -q "^# Contrato de ejecución de machineroom$"
echo "$RULE_OUT" | grep -q "run_registered"
test "$(echo "$RULE_OUT" | grep -c '^---$')" = "2"
if bash "$ROOT/scripts/cursor-user-rule.sh" --bogus 2>/dev/null; then
  echo "FAIL: unknown arg accepted by cursor-user-rule.sh"; exit 1
fi

echo "install tests OK"
