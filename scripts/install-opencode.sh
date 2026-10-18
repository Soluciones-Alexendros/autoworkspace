#!/bin/bash
# Populate project-local OpenCode/agent skill links. Always operates on --target repo root.
# Phases: preflight (no writes on dry-run) → write-ahead journal apply → finalize.
set -euo pipefail
SCRIPT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
TARGET=""
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --target) TARGET="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --help|-h)
      echo "Usage: bash scripts/install-opencode.sh --target REPO_ROOT [--dry-run]"
      exit 0
      ;;
    *) echo "ERROR: unknown arg $1" >&2; exit 2 ;;
  esac
done

if [ -z "$TARGET" ]; then
  TARGET="$SCRIPT_ROOT"
fi

if [ ! -d "$TARGET" ]; then
  echo "ERROR: target repo root does not exist: $TARGET" >&2
  exit 1
fi
TARGET=$(cd "$TARGET" && pwd)
ROOT="$TARGET"
SRC="$ROOT/skills"
JOURNAL="$TARGET/.autoworkspace-opencode-install-journal.json"
MANIFEST="$TARGET/.autoworkspace-opencode-install-manifest.json"

if [ ! -d "$SRC" ]; then
  echo "ERROR: $SRC missing — target is not an autoworkspace checkout" >&2
  exit 1
fi

echo "PREFLIGHT OpenCode setup — project-local (target=$TARGET dry_run=$DRY_RUN)"

PLANNED=()
for s in "$SRC"/*; do
  [ -d "$s" ] || continue
  [ -f "$s/SKILL.md" ] || continue
  PLANNED+=("$(basename "$s")")
done

for dest_rel in .opencode/skills .agents/skills; do
  dest="$TARGET/$dest_rel"
  [ -d "$dest" ] || continue
  for name in "${PLANNED[@]}"; do
    link="$dest/$name"
    [ -e "$link" ] || [ -L "$link" ] || continue
    if [ -e "$link" ] && [ ! -L "$link" ]; then
      echo "ERROR: conflict — real file/dir at $link" >&2
      exit 1
    fi
    if [ -L "$link" ]; then
      tgt=$(readlink -f "$link" 2>/dev/null || true)
      if [ -z "$tgt" ]; then
        echo "ERROR: conflict — broken symlink $link (retained)" >&2
        exit 1
      fi
      case "$tgt" in
        "$SRC"/*) ;;
        *)
          echo "ERROR: conflict — foreign symlink $link → $tgt (name collides with planned install)" >&2
          exit 1
          ;;
      esac
    fi
  done
done
echo "PREFLIGHT OK (foreign non-colliding resources preserved)"

if [ "$DRY_RUN" = 1 ]; then
  for dest_rel in .opencode/skills .agents/skills; do
    echo "[dry-run] mkdir -p $TARGET/$dest_rel"
    for s in "$SRC"/*; do
      [ -d "$s" ] || continue
      [ -f "$s/SKILL.md" ] || continue
      name=$(basename "$s")
      echo "[dry-run] ln -sfn ../../skills/$name $TARGET/$dest_rel/$name"
    done
  done
  echo "Done (dry-run: zero filesystem writes)."
  exit 0
fi

rollback() {
  echo "ROLLBACK OpenCode install from journal" >&2
  if ! python3 - "$JOURNAL" <<'PY'
import json, os, sys
from pathlib import Path
jp = Path(sys.argv[1])
if not jp.is_file():
    sys.exit(0)
doc = json.loads(jp.read_text(encoding="utf-8"))
for entry in reversed(doc.get("entries", [])):
    if not entry.get("applied"):
        continue
    dest = Path(entry["dest"])
    prev = entry.get("previous") or {}
    action = entry.get("action")
    if action == "created":
        if dest.is_symlink() or (dest.exists() and not dest.is_dir()):
            dest.unlink()
    elif action == "replaced":
        if dest.is_symlink() or (dest.exists() and not dest.is_dir()):
            dest.unlink()
        if prev.get("type") == "symlink":
            os.symlink(prev["target"], dest)
jp.unlink(missing_ok=True)
print("opencode rollback restored prior state")
PY
  then
    echo "ROLLBACK FAILED" >&2
    exit 1
  fi
  exit 1
}
trap rollback ERR

python3 - "$JOURNAL" "$TARGET" "$SRC" "${PLANNED[@]}" <<'PY'
"""Write-ahead journal for OpenCode skill links — planned names only (H10)."""
import json, os, sys
from pathlib import Path

journal_path = Path(sys.argv[1])
target = Path(sys.argv[2]).resolve()
src = Path(sys.argv[3]).resolve()
names = sys.argv[4:]


def persist(doc):
    tmp = journal_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, journal_path)


doc = {"schema_version": 1, "entries": []}
persist(doc)

for dest_rel in (".opencode/skills", ".agents/skills"):
    dest_dir = target / dest_rel
    dest_dir.mkdir(parents=True, exist_ok=True)
    # Remove only previously owned links pointing into SRC (planned set)
    for link in list(dest_dir.iterdir()) if dest_dir.is_dir() else []:
        if not link.is_symlink():
            continue
        try:
            tgt = link.resolve()
        except OSError:
            continue
        try:
            tgt.relative_to(src)
        except ValueError:
            continue  # foreign — leave alone
        name = link.name
        if name not in names:
            continue
        previous = {"type": "symlink", "target": os.readlink(link)}
        entry = {
            "name": name,
            "dest": str(link),
            "action": "replaced",
            "previous": previous,
            "applied": False,
            "dest_rel": dest_rel,
        }
        doc["entries"].append(entry)
        persist(doc)
        link.unlink()
        entry["applied"] = True
        persist(doc)

    for name in names:
        link = dest_dir / name
        rel_target = f"../../skills/{name}"
        previous = None
        if link.is_symlink():
            previous = {"type": "symlink", "target": os.readlink(link)}
            action = "unchanged" if os.readlink(link) == rel_target else "replaced"
        elif link.exists():
            raise SystemExit(f"conflict real path {link}")
        else:
            action = "created"
            previous = {"type": "absent"}
        entry = {
            "name": name,
            "dest": str(link),
            "action": action,
            "previous": previous,
            "applied": False,
            "dest_rel": dest_rel,
            "link_target": rel_target,
        }
        doc["entries"].append(entry)
        persist(doc)
        if action != "unchanged":
            if link.is_symlink() or (link.exists() and not link.is_dir()):
                link.unlink()
            os.symlink(rel_target, link)
        entry["applied"] = True
        persist(doc)

print(f"opencode journal → {journal_path}")
PY

# finalize manifest
python3 - "$MANIFEST" "$TARGET" "${PLANNED[@]}" <<'PY'
import json, sys
from pathlib import Path
mf = Path(sys.argv[1])
target = sys.argv[2]
names = list(sys.argv[3:])
doc = {
    "schema_version": 1,
    "target": target,
    "resources": names,
    "destinations": [".opencode/skills", ".agents/skills"],
    "installer": "scripts/install-opencode.sh",
}
tmp = mf.with_suffix(".tmp")
tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
tmp.replace(mf)
print(f"manifest → {mf}")
PY

rm -f "$JOURNAL"
trap - ERR

if [ -f "$TARGET/opencode.json" ]; then
  echo "Check $TARGET/opencode.json"
  cat "$TARGET/opencode.json"
else
  echo "WARN: opencode.json missing in target"
fi

echo "OpenCode links ready under .opencode/skills and .agents/skills"
