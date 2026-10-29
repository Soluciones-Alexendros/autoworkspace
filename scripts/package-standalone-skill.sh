#!/bin/bash
# Package a skill + shared tools/execution into an explicit destination (C14).
# Usage:
#   bash scripts/package-standalone-skill.sh --skill NAME --dest DIR [--dry-run]
# Without --dest, packages into skills/NAME/vendor/execution (in-tree).
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
SKILL=""
DEST_ROOT=""
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --skill) SKILL="${2:-}"; shift 2 ;;
    --dest) DEST_ROOT="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --help|-h)
      echo "Usage: bash scripts/package-standalone-skill.sh --skill NAME [--dest DIR] [--dry-run]"
      exit 0
      ;;
    *) echo "ERROR: unknown arg $1" >&2; exit 2 ;;
  esac
done

if [ -z "$SKILL" ]; then
  echo "ERROR: --skill required" >&2
  exit 2
fi
# Reject path escape in skill name
case "$SKILL" in
  *..*|/*|*\\*|*" "*) echo "ERROR: invalid skill name: $SKILL" >&2; exit 2 ;;
esac

SRC_EXEC="$ROOT/tools/execution"
SKILL_SRC="$ROOT/skills/$SKILL"
if [ ! -d "$SRC_EXEC" ]; then
  echo "ERROR: missing $SRC_EXEC" >&2
  exit 1
fi
if [ ! -f "$SKILL_SRC/SKILL.md" ]; then
  echo "ERROR: skill not found: $SKILL" >&2
  exit 1
fi

if [ -n "$DEST_ROOT" ]; then
  # External package: new destination only; never rsync --delete onto unvalidated dest
  case "$DEST_ROOT" in
    /*) ;;
    *) echo "ERROR: --dest must be an absolute path" >&2; exit 2 ;;
  esac
  if [ -e "$DEST_ROOT" ] && [ ! -d "$DEST_ROOT" ]; then
    echo "ERROR: --dest exists and is not a directory" >&2
    exit 1
  fi
  if [ -d "$DEST_ROOT" ] && [ "$(ls -A "$DEST_ROOT" 2>/dev/null)" ]; then
    echo "ERROR: --dest must be empty or new (refusing rsync --delete on populated dest)" >&2
    exit 1
  fi
  DEST_SKILL="$DEST_ROOT/$SKILL"
  DEST_EXEC="$DEST_SKILL/vendor/execution"
else
  DEST_SKILL="$SKILL_SRC"
  DEST_EXEC="$SKILL_SRC/vendor/execution"
fi

echo "PACKAGE standalone: skill=$SKILL dest=$DEST_SKILL (dry_run=$DRY_RUN)"
if [ "$DRY_RUN" = 1 ]; then
  echo "[dry-run] would copy skill + tools/execution into $DEST_EXEC"
  exit 0
fi

mkdir -p "$DEST_EXEC"
if [ -n "$DEST_ROOT" ]; then
  # Copy skill tree (no vendor yet) then execution modules
  rsync -a \
    --exclude 'vendor' \
    --exclude '__pycache__' \
    --exclude 'tests/__pycache__' \
    --exclude '*.pyc' \
    "$SKILL_SRC/" "$DEST_SKILL/"
fi
rsync -a --delete \
  --exclude '__pycache__' \
  --exclude 'tests' \
  --exclude '*.pyc' \
  "$SRC_EXEC/" "$DEST_EXEC/"
# Ensure importable as execution when vendor parent is on PYTHONPATH
: > "$DEST_SKILL/vendor/__init__.py"

# P11 T3: include canon files the skill cites (relative links into docs/ or templates/product/)
CANON_VENDOR="$DEST_SKILL/vendor/canon"
mkdir -p "$CANON_VENDOR"
while IFS= read -r -d '' md; do
  rel_md="${md#"$SKILL_SRC"/}"
  dir_md=$(dirname "$rel_md")
  while IFS= read -r target; do
    [ -z "$target" ] && continue
    case "$target" in
      http://*|https://*|mailto:*|\#*) continue ;;
    esac
    target="${target%%\#*}"
    resolved=$(python3 -c "from pathlib import Path; print((Path('$SKILL_SRC')/'$dir_md'/'$target').resolve())" 2>/dev/null || true)
    [ -z "$resolved" ] && continue
    case "$resolved" in
      "$ROOT"/docs/*|"$ROOT"/templates/product/*) ;;
      *) continue ;;
    esac
    [ -f "$resolved" ] || continue
    rel_canon="${resolved#"$ROOT"/}"
    dest_file="$CANON_VENDOR/$rel_canon"
    mkdir -p "$(dirname "$dest_file")"
    cp -a "$resolved" "$dest_file"
  done < <(grep -oE '\[[^]]+\]\([^)]+\)' "$md" | sed -E 's/^\[[^]]+\]\(([^)]+)\)$/\1/' || true)
done < <(find "$SKILL_SRC" -name '*.md' -print0)

echo "Packaged. Standalone: PYTHONPATH=$DEST_SKILL/vendor (no repo tools/ required)"
echo "Preflight resolves vendor/execution for shared_dependencies: tools/execution"
if [ -d "$CANON_VENDOR" ] && [ "$(find "$CANON_VENDOR" -type f | wc -l)" -gt 0 ]; then
  echo "Canon files vendored under $CANON_VENDOR"
fi
