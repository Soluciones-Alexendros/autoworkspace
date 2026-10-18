#!/bin/bash
# Populate project-local OpenCode/agent skill links. Always operates on --target repo root.
# Phases: preflight (no writes on dry-run) → apply → finalize.
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

# Resolve without forcing mkdir of missing nested paths beyond repo root
if [ ! -d "$TARGET" ]; then
  echo "ERROR: target repo root does not exist: $TARGET" >&2
  exit 1
fi
TARGET=$(cd "$TARGET" && pwd)
ROOT="$TARGET"
SRC="$ROOT/skills"

if [ ! -d "$SRC" ]; then
  echo "ERROR: $SRC missing — target is not an autoworkspace checkout" >&2
  exit 1
fi

echo "PREFLIGHT OpenCode setup — project-local (target=$TARGET dry_run=$DRY_RUN)"

# Conflict scan
for dest_rel in .opencode/skills .agents/skills; do
  dest="$TARGET/$dest_rel"
  [ -d "$dest" ] || continue
  for link in "$dest"/*; do
    [ -e "$link" ] || [ -L "$link" ] || continue
    name=$(basename "$link")
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
          echo "ERROR: conflict — foreign symlink $link → $tgt" >&2
          exit 1
          ;;
      esac
    fi
  done
done
echo "PREFLIGHT OK"

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

# apply
for dest_rel in .opencode/skills .agents/skills; do
  dest="$TARGET/$dest_rel"
  mkdir -p "$dest"
  for link in "$dest"/*; do
    [ -L "$link" ] || continue
    tgt=$(readlink -f "$link" 2>/dev/null || true)
    case "$tgt" in
      "$SRC"/*)
        rm -f "$link"
        ;;
      *)
        echo "keep foreign/broken link: $link → ${tgt:-broken}"
        ;;
    esac
  done
  for s in "$SRC"/*; do
    [ -d "$s" ] || continue
    [ -f "$s/SKILL.md" ] || continue
    name=$(basename "$s")
    ln -sfn "../../skills/$name" "$dest/$name"
  done
done

# finalize
if [ -f "$TARGET/opencode.json" ]; then
  echo "Check $TARGET/opencode.json"
  cat "$TARGET/opencode.json"
else
  echo "WARN: opencode.json missing in target"
fi

echo "OpenCode links ready under .opencode/skills and .agents/skills"
