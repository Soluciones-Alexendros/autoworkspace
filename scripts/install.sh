#!/bin/bash
# Install autoworkspace skills into an explicit target. Never touches HOME by default.
# Phases: preflight (no writes) → apply (journal) → finalize (manifest) / rollback.
# Usage:
#   bash scripts/install.sh --target DIR [--dry-run] [--scope skills]
#   bash scripts/install.sh --uninstall --target DIR
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
SRC="$ROOT/skills"
TARGET=""
DRY_RUN=0
UNINSTALL=0
SCOPE="skills"
MANIFEST_NAME=".autoworkspace-install-manifest.json"
PHASE="all"

usage() {
  cat <<EOF
Usage: bash scripts/install.sh --target DIR [--dry-run] [--uninstall]
  --target DIR   Required. Destination skills directory.
  --dry-run      Preflight only — no mkdir, no links, no manifest.
  --uninstall    Remove only resources listed in the manifest under --target.
Does not overwrite global AGENTS.md. Does not prune foreign skills.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --target) TARGET="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --uninstall) UNINSTALL=1; shift ;;
    --scope) SCOPE="${2:-}"; shift 2 ;;
    --prune)
      echo "ERROR: --prune removed; refusing to archive foreign skills by catalog absence" >&2
      exit 2
      ;;
    --help|-h) usage; exit 0 ;;
    *) echo "ERROR: unknown arg $1" >&2; usage; exit 2 ;;
  esac
done

if [ -z "$TARGET" ]; then
  echo "ERROR: --target is required (refusing implicit \$HOME installs)" >&2
  exit 2
fi

# --- helpers ---
is_privileged() {
  case "$1" in
    /|/etc|/usr|/var|/bin|/sbin|/boot|/root) return 0 ;;
    *) return 1 ;;
  esac
}

resolve_existing_or_parent() {
  # Resolve target without creating it. If missing, resolve parent + basename.
  local t="$1"
  if [ -d "$t" ]; then
    (cd "$t" && pwd)
    return
  fi
  local parent base
  parent=$(dirname -- "$t")
  base=$(basename -- "$t")
  if [ ! -d "$parent" ]; then
    echo "ERROR: parent of target does not exist: $parent" >&2
    return 1
  fi
  parent=$(cd "$parent" && pwd)
  echo "$parent/$base"
}

preflight_conflicts() {
  local dest name s cur
  for s in "$SRC"/*; do
    [ -d "$s" ] || continue
    [ -f "$s/SKILL.md" ] || continue
    name=$(basename "$s")
    dest="$TARGET/$name"
    if [ -e "$dest" ] || [ -L "$dest" ]; then
      if [ -e "$dest" ] && [ ! -L "$dest" ]; then
        echo "ERROR: conflict — real file/dir at $dest (foreign resource preserved)" >&2
        return 1
      fi
      if [ -L "$dest" ]; then
        cur=$(readlink -f "$dest" 2>/dev/null || true)
        if [ -z "$cur" ]; then
          echo "ERROR: conflict — broken symlink at $dest (foreign/broken; retained)" >&2
          return 1
        fi
        if [ "$cur" != "$(readlink -f "$s")" ]; then
          case "$cur" in
            "$SRC"/*) ;;
            *)
              echo "ERROR: conflict — symlink $dest → $cur not owned by this install" >&2
              return 1
              ;;
          esac
        fi
      fi
    fi
  done
  return 0
}

validate_manifest_paths() {
  local mf="$1"
  [ -f "$mf" ] || return 0
  python3 - "$mf" "$TARGET" <<'PY'
import json, os, sys
from pathlib import Path
mf, target = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
data = json.loads(mf.read_text(encoding="utf-8"))
for rel in data.get("resources", []):
    if ".." in Path(rel).parts or Path(rel).is_absolute():
        print(f"FAIL: traversal/absolute in manifest: {rel}", file=sys.stderr)
        sys.exit(1)
    joined = Path(os.path.normpath(str(target / rel)))
    try:
        joined.relative_to(target)
    except ValueError:
        print(f"FAIL: manifest path escapes target: {rel}", file=sys.stderr)
        sys.exit(1)
print("manifest paths OK")
PY
}

# Resolve without mkdir (preflight must not write)
TARGET=$(resolve_existing_or_parent "$TARGET") || exit 1
if is_privileged "$TARGET"; then
  echo "ERROR: target too privileged: $TARGET" >&2
  exit 3
fi

MANIFEST="$TARGET/$MANIFEST_NAME"

# ---------- uninstall ----------
if [ "$UNINSTALL" = 1 ]; then
  if [ ! -d "$TARGET" ]; then
    echo "ERROR: target missing for uninstall: $TARGET" >&2
    exit 1
  fi
  validate_manifest_paths "$MANIFEST"
  if [ ! -f "$MANIFEST" ]; then
    echo "ERROR: no manifest at $MANIFEST; refusing blind uninstall" >&2
    exit 1
  fi
  python3 - "$MANIFEST" "$TARGET" "$DRY_RUN" "$SRC" <<'PY'
import json, os, sys
from pathlib import Path
mf, target, dry = Path(sys.argv[1]), Path(sys.argv[2]).resolve(), sys.argv[3] == "1"
src = Path(sys.argv[4]).resolve()
data = json.loads(mf.read_text(encoding="utf-8"))
for rel in data.get("resources", []):
    if ".." in Path(rel).parts or Path(rel).is_absolute():
        print("escape", rel); sys.exit(1)
    p = Path(os.path.normpath(str(target / rel)))
    try:
        p.relative_to(target)
    except ValueError:
        print("escape", rel); sys.exit(1)
    if not p.exists() and not p.is_symlink():
        print(f"warn: missing {p}; skip")
        continue
    # Verify still owned (symlink → SRC) or retain+warn
    if p.is_symlink():
        cur = Path(os.path.realpath(p))
        try:
            cur.relative_to(src)
            owned = True
        except ValueError:
            owned = False
        if not owned:
            print(f"WARN: retain changed resource {p} → {cur} (not owned); skip remove")
            continue
    elif p.is_dir() or p.is_file():
        print(f"WARN: retain non-symlink resource {p} (type changed); skip remove")
        continue
    print(("dry-run " if dry else "") + f"remove {p}")
    if not dry:
        p.unlink()
if not dry:
    mf.unlink(missing_ok=True)
print("uninstall done")
PY
  exit 0
fi

# ---------- preflight (always; never writes) ----------
echo "PREFLIGHT: $SRC → $TARGET (scope=$SCOPE dry_run=$DRY_RUN)"
preflight_conflicts || exit 1
RESOURCES=()
for s in "$SRC"/*; do
  [ -d "$s" ] || continue
  [ -f "$s/SKILL.md" ] || continue
  RESOURCES+=("$(basename "$s")")
done
echo "PREFLIGHT OK: ${#RESOURCES[@]} skills planned"

if [ "$DRY_RUN" = 1 ]; then
  for name in "${RESOURCES[@]}"; do
    echo "[dry-run] ln -sfn $SRC/$name $TARGET/$name"
  done
  echo "[dry-run] would write manifest $MANIFEST (not created)"
  echo "Done (dry-run: zero filesystem writes)."
  exit 0
fi

# ---------- apply (journal per resource: absent|created|unchanged|replaced) ----------
JOURNAL="$TARGET/.autoworkspace-install-journal.json"
rollback() {
  echo "ROLLBACK: restoring prior link state from journal" >&2
  python3 - "$JOURNAL" <<'PY' || true
import json, os, sys
from pathlib import Path
jp = Path(sys.argv[1])
if not jp.is_file():
    sys.exit(0)
doc = json.loads(jp.read_text(encoding="utf-8"))
for entry in reversed(doc.get("entries", [])):
    dest = Path(entry["dest"])
    action = entry.get("action")
    prev = entry.get("previous")
    if action == "created":
        if dest.is_symlink() or dest.exists():
            dest.unlink()
    elif action == "replaced" and prev is not None:
        if dest.is_symlink() or (dest.exists() and not dest.is_dir()):
            try:
                dest.unlink()
            except OSError:
                pass
        if prev.get("type") == "symlink":
            os.symlink(prev["target"], dest)
        # absent previous → leave removed
    # unchanged: nothing
jp.unlink(missing_ok=True)
print("rollback restored prior state")
PY
  exit 1
}
trap rollback ERR

if [ ! -d "$TARGET" ]; then
  mkdir -p "$TARGET"
fi

python3 - "$JOURNAL" "$SRC" "$TARGET" "${RESOURCES[@]}" <<'PY'
import json, os, sys
from pathlib import Path
journal_path = Path(sys.argv[1])
src = Path(sys.argv[2]).resolve()
target = Path(sys.argv[3]).resolve()
names = sys.argv[4:]
entries = []
for name in names:
    dest = target / name
    s = src / name
    previous = None
    if dest.is_symlink():
        previous = {"type": "symlink", "target": os.readlink(dest)}
        action = "unchanged" if os.path.realpath(dest) == os.path.realpath(s) else "replaced"
    elif dest.exists():
        raise SystemExit(f"conflict real path {dest}")
    else:
        action = "created"
    if action != "unchanged":
        if dest.is_symlink() or dest.exists():
            dest.unlink()
        os.symlink(str(s), dest)
    entries.append({"name": name, "dest": str(dest), "action": action, "previous": previous})
doc = {"schema_version": 1, "entries": entries}
journal_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
print(f"journal → {journal_path} ({len(entries)} resources)")
PY

# ---------- finalize ----------
python3 - "$MANIFEST" "$ROOT" "${RESOURCES[@]}" <<'PY'
import json, sys
from pathlib import Path
mf = Path(sys.argv[1])
root = sys.argv[2]
resources = list(sys.argv[3:])
doc = {
    "schema_version": 1,
    "source_root": root,
    "resources": resources,
    "installer": "scripts/install.sh",
}
mf.parent.mkdir(parents=True, exist_ok=True)
tmp = mf.with_suffix(".tmp")
tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
tmp.replace(mf)
print(f"manifest → {mf}")
PY
validate_manifest_paths "$MANIFEST"
# Manifest written successfully — drop journal (no longer needed)
rm -f "$JOURNAL"
trap - ERR

echo "Done. AGENTS.md was not copied to any global home."
echo "OpenCode project links: use scripts/install-opencode.sh --target <repo>"
