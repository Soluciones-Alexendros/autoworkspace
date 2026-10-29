#!/bin/bash
# Symlink skills/ into Cursor's project or user skills directory.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/.." && pwd)
exec bash "$HERE/lib/link-skills.sh" \
  --installer "scripts/install-cursor.sh" \
  --default-target "$ROOT/.cursor/skills" \
  --user-target "${HOME}/.cursor/skills" \
  "$@"
