#!/bin/bash
# Package shared tools/execution into a skill's vendor/ for true standalone use.
# Usage: bash scripts/package-standalone-skill.sh --skill local-maintenance [--dry-run]
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
SKILL=""
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --skill) SKILL="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --help|-h)
      echo "Usage: bash scripts/package-standalone-skill.sh --skill NAME [--dry-run]"
      exit 0
      ;;
    *) echo "ERROR: unknown arg $1" >&2; exit 2 ;;
  esac
done

if [ -z "$SKILL" ]; then
  echo "ERROR: --skill required" >&2
  exit 2
fi

SRC="$ROOT/tools/execution"
DEST="$ROOT/skills/$SKILL/vendor/execution"
if [ ! -d "$SRC" ]; then
  echo "ERROR: missing $SRC" >&2
  exit 1
fi
if [ ! -f "$ROOT/skills/$SKILL/SKILL.md" ]; then
  echo "ERROR: skill not found: $SKILL" >&2
  exit 1
fi

echo "PACKAGE standalone: $SRC → $DEST (dry_run=$DRY_RUN)"
if [ "$DRY_RUN" = 1 ]; then
  echo "[dry-run] would mkdir -p $DEST and copy Python modules"
  exit 0
fi

mkdir -p "$DEST"
# Copy modules only (no tests/caches)
rsync -a --delete \
  --exclude '__pycache__' \
  --exclude 'tests' \
  --exclude '*.pyc' \
  "$SRC/" "$DEST/"
# Ensure importable as execution when vendor parent is on PYTHONPATH
if [ ! -f "$DEST/../__init__.py" ]; then
  : > "$ROOT/skills/$SKILL/vendor/__init__.py" || true
fi
echo "Packaged. Standalone consumers: PYTHONPATH=\$SKILL/vendor"
echo "Preflight resolves vendor/execution for shared_dependencies: tools/execution"
