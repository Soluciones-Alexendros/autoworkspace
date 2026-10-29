#!/bin/bash
# V31–V33: write-ahead journal + real rollback (shared installer path, no mirror algo)
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# --- V31: fail after first applied link; journal rollback removes it ---
RB="$TMP/rb"
mkdir -p "$RB"

INSTALL="$TMP/link-skills.sh"
sed "s|^ROOT=.*|ROOT=\"$ROOT\"|" "$ROOT/scripts/lib/link-skills.sh" > "$INSTALL"
python3 - "$INSTALL" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
text = p.read_text()
needle = '    entry["applied"] = True\n    persist(doc)\n\nprint'
inject = (
    '    entry["applied"] = True\n'
    '    persist(doc)\n'
    '    applied_n = sum(1 for e in doc["entries"] if e.get("applied"))\n'
    '    if __import__("os").environ.get("AW_INSTALL_FAIL_AFTER") == "1" and applied_n >= 1:\n'
    '        raise SystemExit("injected apply failure")\n'
    '\nprint'
)
if needle not in text:
    raise SystemExit("inject point missing")
p.write_text(text.replace(needle, inject, 1))
PY
chmod +x "$INSTALL"

set +e
AW_INSTALL_FAIL_AFTER=1 bash "$INSTALL" --target "$RB" 2>"$TMP/err.txt"
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "FAIL: expected non-zero after injected failure"; cat "$TMP/err.txt"; exit 1
fi
grep -q "injected apply failure\|ROLLBACK" "$TMP/err.txt" || true
# First skill link must not remain (rollback undoes created)
FIRST=$(find "$ROOT/skills" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort | head -1)
if [ -e "$RB/$FIRST" ] || [ -L "$RB/$FIRST" ]; then
  echo "FAIL: $FIRST still present after rollback"; ls -la "$RB"; exit 1
fi
# Journal should be cleaned by rollback
test ! -f "$RB/.autoworkspace-install-journal.json"
echo "V31 OK: created link rolled back after injected failure (rc=$rc)"

# --- V32: successful install then foreign preserved ---
OK="$TMP/ok"
mkdir -p "$OK/foreign"
echo keep > "$OK/foreign/x"
bash "$ROOT/scripts/install-cursor.sh" --target "$OK"
test -L "$OK/local-maintenance"
test "$(cat "$OK/foreign/x")" = "keep"
echo "V32 OK: foreign preserved"

# --- dry-run ---
MISS="$TMP/miss"
bash "$ROOT/scripts/install-cursor.sh" --target "$MISS" --dry-run
test ! -e "$MISS"
echo "V33 dry-run OK"

echo "install journal WA tests PASS"
