#!/bin/bash
# Symlink skills/ into Pi's project (.pi/skills) or user (~/.pi/agent/skills) directory.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/.." && pwd)
exec bash "$HERE/lib/link-skills.sh" \
  --installer "scripts/install-pi.sh" \
  --default-target "$ROOT/.pi/skills" \
  --user-target "${HOME}/.pi/agent/skills" \
  "$@"
