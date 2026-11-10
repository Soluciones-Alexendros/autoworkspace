#!/bin/bash
# Link skills/<name> into an explicit directory. Journal, dry-run, conflicts, uninstall.
# Public entrypoints: scripts/install-cursor.sh and scripts/install-pi.sh.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
SRC="$ROOT/skills"
TARGET=""
DRY_RUN=0
UNINSTALL=0
SCOPE="skills"
USER_INSTALL=0
INSTALLER="scripts/lib/link-skills.sh"
DEFAULT_TARGET=""
USER_TARGET=""
MANIFEST_NAME=".autoworkspace-install-manifest.json"
YES=0
JSON_OUT=0
HARNESS="cursor"
RUNTIME_HOME="${HOME}/.autoworkspace"
# Single source of truth for the release version (avoids drift with package.json).
VERSION="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["version"])' "$ROOT/package.json")"
INSTALLED=0
CHANGED=0
SKIPPED=0
CONFLICTS=0

usage() {
  cat <<EOF
Usage: bash $INSTALLER [--target DIR] [--user] [--dry-run] [--uninstall] [--yes] [--json]
  --target DIR   Destination skills directory. '.' is this script's checkout (\$ROOT), not the cwd.
                 A path ending in .cursor/skills, .pi/skills, or .pi/agent/skills is used as-is.
  --user         Destination is the harness user directory. Overrides --target.
                 Reads the catalog from \$HOME/.autoworkspace (relative symlinks).
  --dry-run      Preflight only — no mkdir, no links, no manifest.
  --uninstall    Remove only resources listed in the manifest under the destination.
  --yes          Non-interactive; does not overwrite foreign/real-dir conflicts.
  --json         Machine-readable JSON on stdout (human logs on stderr).
Does not overwrite global AGENTS.md. Does not prune foreign skills.
EOF
}

log() {
  if [ "$JSON_OUT" = 1 ]; then
    echo "$@" >&2
  else
    echo "$@"
  fi
}

emit_json() {
  local status="$1"
  local dry_bool=false
  [ "$DRY_RUN" = 1 ] && dry_bool=true
  python3 - "$HARNESS" "$TARGET" "$INSTALLED" "$CHANGED" "$SKIPPED" "$CONFLICTS" "$dry_bool" "$status" "$VERSION" "${FAILURE_JSON:-}" <<'PY'
import json, sys
harness, target, installed, changed, skipped, conflicts, dry, status, version = sys.argv[1:10]
payload = {
    "harness": harness,
    "target": target,
    "installed": int(installed),
    "changed": int(changed),
    "skipped": int(skipped),
    "conflicts": int(conflicts),
    "dry_run": dry == "true",
    "status": status,
    "version": version,
}
raw = sys.argv[10] if len(sys.argv) > 10 else ""
if raw:
    payload["failures"] = json.loads(raw)
print(json.dumps(payload))
PY
}

emit_failure() {
  local component="$1"
  local function_name="$2"
  local detail="$3"
  local status="${4:-failed}"
  echo "FAIL ${component} ${function_name}: ${detail}" >&2
  FAILURE_JSON=$(python3 -c 'import json,sys; print(json.dumps([{"component":sys.argv[1],"function":sys.argv[2],"detail":sys.argv[3]}]))' "$component" "$function_name" "$detail")
  if [ "$JSON_OUT" = 1 ]; then
    emit_json "$status"
  fi
}

finish_ok() {
  if [ "$JSON_OUT" = 1 ]; then
    emit_json "ok"
  else
    log "Done. AGENTS.md was not copied to any global home."
  fi
  exit 0
}

while [ $# -gt 0 ]; do
  case "$1" in
    --target) TARGET="${2:-}"; shift 2 ;;
    --user) USER_INSTALL=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --uninstall) UNINSTALL=1; shift ;;
    --yes) YES=1; shift ;;
    --json) JSON_OUT=1; shift ;;
    --harness)
      HARNESS="${2:-}"
      if [ "$HARNESS" != "cursor" ] && [ "$HARNESS" != "pi" ]; then
        echo "ERROR: --harness must be cursor|pi" >&2
        exit 2
      fi
      shift 2
      ;;
    --scope) SCOPE="${2:-}"; shift 2 ;;
    --installer) INSTALLER="${2:-}"; shift 2 ;;
    --default-target) DEFAULT_TARGET="${2:-}"; shift 2 ;;
    --user-target) USER_TARGET="${2:-}"; shift 2 ;;
    --prune)
      echo "ERROR: --prune removed; refusing to archive foreign skills by catalog absence" >&2
      exit 2
      ;;
    --help|-h) usage; exit 0 ;;
    *) echo "ERROR: unknown arg $1" >&2; usage; exit 2 ;;
  esac
done

# --yes is accepted for AI/CI non-interactive mode; foreign/real-dir still refused.
: "${YES}"

FAILURE_JSON=""
if [ "$USER_INSTALL" = 1 ]; then
  if [ -L "$RUNTIME_HOME" ]; then
    TARGET="${USER_TARGET:-$RUNTIME_HOME}"
    emit_failure "runtime" "link-skills" "runtime must be a real directory, not a symlink: $RUNTIME_HOME"
    exit 1
  fi
  if [ ! -d "$RUNTIME_HOME/skills" ]; then
    if [ "$UNINSTALL" != 1 ]; then
      TARGET="${USER_TARGET:-${HOME}/.pi/agent/skills}"
      if [ "$HARNESS" = "cursor" ]; then
        TARGET="${USER_TARGET:-${HOME}/.cursor/skills}"
      fi
      emit_failure "runtime" "link-skills" "runtime missing: $RUNTIME_HOME (run scripts/runtime-sync.sh sync first)"
      exit 1
    fi
  else
    SRC="$RUNTIME_HOME/skills"
    VERSION="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["version"])' "$RUNTIME_HOME/package.json")"
    ROOT="$RUNTIME_HOME"
  fi
fi

if [ "$USER_INSTALL" = 1 ] && [ -n "$TARGET" ]; then
  echo "WARN: --user overrides --target; ignoring --target $TARGET" >&2
  if [ -z "$USER_TARGET" ]; then
    echo "ERROR: --user without a user destination" >&2
    exit 2
  fi
  TARGET="$USER_TARGET"
elif [ -n "$TARGET" ]; then
  :
elif [ "$USER_INSTALL" = 1 ]; then
  if [ -z "$USER_TARGET" ]; then
    echo "ERROR: --user without a user destination" >&2
    exit 2
  fi
  TARGET="$USER_TARGET"
else
  if [ -z "$DEFAULT_TARGET" ]; then
    echo "ERROR: --target is required" >&2
    exit 2
  fi
  TARGET="$DEFAULT_TARGET"
fi

# Fix Ojo: --target . or repo root → DEFAULT_TARGET (not links in repo root).
# Skipped after --user wins, so a discarded --target . cannot replace the user dir.
if [ "$USER_INSTALL" != 1 ] && [ -n "$DEFAULT_TARGET" ]; then
  if [ "$TARGET" = "." ]; then
    TARGET="$DEFAULT_TARGET"
  elif [ -d "$TARGET" ]; then
    _abs=$(cd "$TARGET" && pwd)
    if [ "$_abs" = "$ROOT" ]; then
      TARGET="$DEFAULT_TARGET"
    fi
    unset _abs
  fi
fi

is_privileged() {
  case "$1" in
    /|/etc|/usr|/var|/bin|/sbin|/boot|/root) return 0 ;;
    *) return 1 ;;
  esac
}

# Read-only: the nearest existing ancestor must be writable. Does not mkdir.
assert_user_ancestor_writable() {
  local dest="$1"
  local cur="$dest"
  while [ ! -e "$cur" ]; do
    if [ "$cur" = "/" ] || [ -z "$cur" ] || [ "$cur" = "." ]; then
      echo "ERROR: no existing ancestor for user target: $dest" >&2
      exit 3
    fi
    cur=$(dirname -- "$cur")
  done
  if [ ! -w "$cur" ]; then
    echo "ERROR: user target ancestor not writable: $cur" >&2
    exit 3
  fi
}

assert_planned_symlinks() {
  local name dest link
  for name in "${RESOURCES[@]}"; do
    dest="$TARGET/$name"
    if [ ! -L "$dest" ]; then
      emit_failure "$name" "assert_planned_symlinks" "expected symlink at $dest"
      exit 1
    fi
    link=$(readlink -- "$dest")
    if [ "$USER_INSTALL" = 1 ]; then
      case "$link" in
        /*)
          emit_failure "$name" "assert_planned_symlinks" "user symlink must be relative: $dest -> $link"
          exit 1
          ;;
      esac
    else
      case "$link" in
        /*) ;;
        *)
          emit_failure "$name" "assert_planned_symlinks" "symlink is not absolute: $dest -> $link"
          exit 1
          ;;
      esac
    fi
    if [ "$(readlink -f -- "$dest")" != "$(readlink -f -- "$SRC/$name")" ]; then
      emit_failure "$name" "assert_planned_symlinks" "symlink resolves outside catalog: $dest"
      exit 1
    fi
  done
}

resolve_existing_or_parent() {
  local t="$1"
  if [ -d "$t" ]; then
    (cd "$t" && pwd)
    return
  fi
  # Allow nested missing dirs (e.g. /tmp/ai-cursor/.cursor/skills): resolve via
  # deepest existing ancestor; mkdir -p happens later (not on dry-run).
  local cur="$t"
  local suffix=""
  local base
  while [ ! -d "$cur" ]; do
    if [ "$cur" = "/" ] || [ -z "$cur" ] || [ "$cur" = "." ]; then
      echo "ERROR: no existing ancestor for target: $t" >&2
      return 1
    fi
    base=$(basename -- "$cur")
    suffix="/$base$suffix"
    cur=$(dirname -- "$cur")
  done
  cur=$(cd "$cur" && pwd)
  echo "${cur}${suffix}"
}

preflight_conflicts() {
  local dest name s cur prev_root
  prev_root=""
  if [ -f "$TARGET/$MANIFEST_NAME" ]; then
    prev_root=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8")).get("source_root",""))' "$TARGET/$MANIFEST_NAME")
  fi
  for s in "$SRC"/*; do
    [ -d "$s" ] || continue
    [ -f "$s/SKILL.md" ] || continue
    name=$(basename "$s")
    dest="$TARGET/$name"
    if [ -e "$dest" ] || [ -L "$dest" ]; then
      if [ -e "$dest" ] && [ ! -L "$dest" ]; then
        echo "ERROR: conflict — real file/dir at $dest (foreign resource preserved)" >&2
        CONFLICTS=$((CONFLICTS + 1))
        return 1
      fi
      if [ -L "$dest" ]; then
        cur=$(readlink -f "$dest" 2>/dev/null || true)
        if [ -z "$cur" ]; then
          echo "ERROR: conflict — broken symlink at $dest (foreign/broken; retained)" >&2
          CONFLICTS=$((CONFLICTS + 1))
          return 1
        fi
        if [ "$cur" != "$(readlink -f "$s")" ]; then
          case "$cur" in
            "$SRC"/*) ;;
            *)
              if [ -n "$prev_root" ] && [[ "$cur" == "$prev_root"/* ]]; then
                :
              else
                echo "ERROR: conflict — symlink $dest → $cur not owned by this install" >&2
                CONFLICTS=$((CONFLICTS + 1))
                return 1
              fi
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
print("manifest paths OK", file=sys.stderr)
PY
}

plan_counts() {
  # Compute planned installed/changed/skipped without writing (for dry-run JSON/human).
  python3 - "$SRC" "$TARGET" <<'PY'
import os, sys
from pathlib import Path
src, target = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
installed = changed = skipped = 0
for s in sorted(src.iterdir()):
    if not s.is_dir() or not (s / "SKILL.md").is_file():
        continue
    dest = target / s.name
    installed += 1
    if dest.is_symlink() and os.path.realpath(dest) == os.path.realpath(s):
        skipped += 1
    else:
        changed += 1
print(f"{installed} {changed} {skipped}")
PY
}

TARGET=$(resolve_existing_or_parent "$TARGET") || exit 1
if is_privileged "$TARGET"; then
  echo "ERROR: target too privileged: $TARGET" >&2
  exit 3
fi
if [ "$USER_INSTALL" = 1 ]; then
  assert_user_ancestor_writable "$TARGET"
fi

MANIFEST="$TARGET/$MANIFEST_NAME"

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

log "PREFLIGHT: $SRC → $TARGET (scope=$SCOPE dry_run=$DRY_RUN)"
if ! preflight_conflicts; then
  if [ "$JSON_OUT" = 1 ]; then
    emit_json "conflict"
  fi
  exit 1
fi
RESOURCES=()
for s in "$SRC"/*; do
  [ -d "$s" ] || continue
  [ -f "$s/SKILL.md" ] || continue
  RESOURCES+=("$(basename "$s")")
done
log "PREFLIGHT OK: ${#RESOURCES[@]} skills planned"

if [ "$DRY_RUN" = 1 ]; then
  for name in "${RESOURCES[@]}"; do
    log "[dry-run] ln -sfn $SRC/$name $TARGET/$name"
  done
  log "[dry-run] would write manifest $MANIFEST (not created)"
  read -r INSTALLED CHANGED SKIPPED <<<"$(plan_counts)"
  log "Done (dry-run: zero filesystem writes)."
  finish_ok
fi

JOURNAL="$TARGET/.autoworkspace-install-journal.json"
rollback() {
  echo "ROLLBACK: restoring prior link state from journal" >&2
  if ! python3 - "$JOURNAL" <<'PY'
import json, os, sys
from pathlib import Path
jp = Path(sys.argv[1])
if not jp.is_file():
    print("rollback: no journal; nothing to restore", file=sys.stderr)
    sys.exit(0)
doc = json.loads(jp.read_text(encoding="utf-8"))
for entry in reversed(doc.get("entries", [])):
    if not entry.get("applied"):
        continue
    dest = Path(entry["dest"])
    action = entry.get("action")
    prev = entry.get("previous") or {}
    if action == "created":
        if dest.is_symlink() or (dest.exists() and not dest.is_dir()):
            dest.unlink()
    elif action == "replaced":
        if dest.is_symlink() or (dest.exists() and not dest.is_dir()):
            dest.unlink()
        if prev.get("type") == "symlink":
            os.symlink(prev["target"], dest)
jp.unlink(missing_ok=True)
print("rollback restored prior state")
PY
  then
    echo "ROLLBACK FAILED" >&2
    exit 1
  fi
  exit 1
}
trap rollback ERR

if [ ! -d "$TARGET" ]; then
  mkdir -p "$TARGET"
fi

COUNTS_LINE=$(python3 - "$JOURNAL" "$SRC" "$TARGET" "$USER_INSTALL" "${RESOURCES[@]}" <<'PY'
"""Write-ahead journal: persist prior state BEFORE each filesystem effect."""
import json, os, sys
from pathlib import Path

journal_path = Path(sys.argv[1])
src = Path(sys.argv[2]).resolve()
target = Path(sys.argv[3]).resolve()
relative = sys.argv[4] == "1"
names = sys.argv[5:]


def persist(doc: dict) -> None:
    tmp = journal_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, journal_path)
    try:
        fd = os.open(journal_path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


def link_text(source: Path, dest: Path) -> str:
    if relative:
        return os.path.relpath(str(source), start=str(dest.parent))
    return str(source)


doc = {"schema_version": 1, "run_id": os.environ.get("AW_INSTALL_RUN", ""), "entries": []}
persist(doc)
changed = skipped = 0

for name in names:
    dest = target / name
    s = (src / name).resolve()
    previous = None
    if dest.is_symlink():
        previous = {"type": "symlink", "target": os.readlink(dest)}
        action = "unchanged" if os.path.realpath(dest) == os.path.realpath(s) else "replaced"
    elif dest.exists():
        raise SystemExit(f"conflict real path {dest}")
    else:
        action = "created"
        previous = {"type": "absent"}

    if action == "unchanged":
        skipped += 1
    else:
        changed += 1

    entry = {
        "name": name,
        "dest": str(dest),
        "action": action,
        "previous": previous,
        "applied": False,
        "source": str(s),
    }
    doc["entries"].append(entry)
    persist(doc)

    if action != "unchanged":
        if dest.is_symlink() or (dest.exists() and not dest.is_dir()):
            dest.unlink()
        os.symlink(link_text(s, dest), dest)
    entry["applied"] = True
    persist(doc)

installed = changed + skipped
print(f"journal → {journal_path} ({len(doc['entries'])} resources)", file=sys.stderr)
print(f"{installed} {changed} {skipped}")
PY
)
read -r INSTALLED CHANGED SKIPPED <<<"$COUNTS_LINE"

python3 - "$MANIFEST" "$ROOT" "$INSTALLER" "${RESOURCES[@]}" <<'PY'
import json, sys
from pathlib import Path
mf = Path(sys.argv[1])
root = sys.argv[2]
installer = sys.argv[3]
resources = list(sys.argv[4:])
doc = {
    "schema_version": 1,
    "source_root": root,
    "resources": resources,
    "installer": installer,
}
mf.parent.mkdir(parents=True, exist_ok=True)
tmp = mf.with_suffix(".tmp")
tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
tmp.replace(mf)
print(f"manifest → {mf}", file=sys.stderr)
PY
validate_manifest_paths "$MANIFEST"
assert_planned_symlinks
rm -f "$JOURNAL"
trap - ERR

finish_ok
