#!/usr/bin/env bash
# Print the full machineroom Cursor rule (frontmatter + Markdown body) for
# Customize -> Rules. Cursor keeps user rules in Settings and syncs them with the
# account, so this cannot be written as a file: paste it, or pipe it with --copy.
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
RULE="$ROOT/.cursor/rules/machineroom.mdc"
COPY=false

while [ $# -gt 0 ]; do
  case "$1" in
    --copy) COPY=true; shift ;;
    --help|-h)
      echo "Usage: bash scripts/cursor-user-rule.sh [--copy]"
      echo "Prints the whole rule (frontmatter included) for Cursor Customize -> Rules."
      exit 0
      ;;
    *) echo "ERROR: unknown arg $1" >&2; exit 2 ;;
  esac
done

if [ ! -f "$RULE" ]; then
  echo "ERROR: missing $RULE" >&2
  exit 1
fi

# The rule must keep YAML frontmatter (description + alwaysApply) when pasted.
if [ "$(head -1 "$RULE")" != "---" ]; then
  echo "ERROR: $RULE has no frontmatter block" >&2
  exit 1
fi

if [ "$COPY" = true ]; then
  if ! command -v wl-copy >/dev/null 2>&1; then
    echo "ERROR: --copy needs wl-copy (Wayland clipboard)" >&2
    exit 3
  fi
  wl-copy < "$RULE"
  echo "Copied the whole rule (frontmatter included) to the clipboard." >&2
  echo "Paste it into Cursor: Customize -> Rules." >&2
  exit 0
fi

cat "$RULE"
