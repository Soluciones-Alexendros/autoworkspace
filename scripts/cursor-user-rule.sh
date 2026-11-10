#!/usr/bin/env bash
# Print the autoworkspace Cursor rule body for Customize -> Rules (user scope).
# Cursor keeps user rules in Settings and syncs them with the account, so this
# cannot be written as a file: paste the body, or pipe it with --copy.
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
RULE="$ROOT/.cursor/rules/autoworkspace.mdc"
COPY=false

while [ $# -gt 0 ]; do
  case "$1" in
    --copy) COPY=true; shift ;;
    --help|-h)
      echo "Usage: bash scripts/cursor-user-rule.sh [--copy]"
      echo "Prints the rule body (frontmatter stripped) for Customize -> Rules."
      exit 0
      ;;
    *) echo "ERROR: unknown arg $1" >&2; exit 2 ;;
  esac
done

if [ ! -f "$RULE" ]; then
  echo "ERROR: missing $RULE" >&2
  exit 1
fi

BODY=$(python3 - "$RULE" <<'PY'
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
lines = text.splitlines()
if lines and lines[0].strip() == "---":
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            lines = lines[index + 1 :]
            break
print("\n".join(lines).strip())
PY
)

if [ -z "$BODY" ]; then
  echo "ERROR: empty rule body" >&2
  exit 1
fi

if [ "$COPY" = true ]; then
  if ! command -v wl-copy >/dev/null 2>&1; then
    echo "ERROR: --copy needs wl-copy (Wayland clipboard)" >&2
    exit 3
  fi
  printf '%s\n' "$BODY" | wl-copy
  echo "Copied the rule body to the clipboard. Paste it into Cursor: Customize -> Rules." >&2
  exit 0
fi

printf '%s\n' "$BODY"
