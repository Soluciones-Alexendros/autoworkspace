#!/bin/bash
# Symlink skills/ into Pi's project (.pi/skills) or user (~/.pi/agent/skills) directory.
# User installs also link extensions/autoworkspace.ts from $HOME/.autoworkspace.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/.." && pwd)

USER_MODE=0
ARGS=()
for arg in "$@"; do
  if [ "$arg" = "--user" ]; then
    USER_MODE=1
  fi
  ARGS+=("$arg")
done

bash "$HERE/lib/link-skills.sh" \
  --installer "scripts/install-pi.sh" \
  --default-target "$ROOT/.pi/skills" \
  --user-target "${HOME}/.pi/agent/skills" \
  --harness pi \
  "${ARGS[@]}"

if [ "$USER_MODE" != 1 ]; then
  exit 0
fi

# Extension file link (skills installer already succeeded).
DRY=0
JSON=0
for arg in "${ARGS[@]}"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --json) JSON=1 ;;
    --uninstall)
      PYTHONPATH="$ROOT/tools" python3 - <<'PY'
import os
from pathlib import Path
from harness.runtime import require_runtime

home = Path(os.environ["HOME"])
dest = home / ".pi" / "agent" / "extensions" / "autoworkspace.ts"
if not dest.is_symlink():
    raise SystemExit(0)
runtime = require_runtime(home)
source = (runtime / "extensions" / "autoworkspace" / "index.ts").resolve()
if dest.resolve() == source:
    dest.unlink()
    print(f"removed {dest}", flush=True)
PY
      exit 0
      ;;
  esac
done

if [ "$DRY" = 1 ]; then
  if [ "$JSON" != 1 ]; then
    echo "[dry-run] would link ${HOME}/.pi/agent/extensions/autoworkspace.ts"
  fi
  exit 0
fi

PYTHONPATH="$ROOT/tools" JSON_OUT="$JSON" python3 - <<'PY'
import json
import os
import sys
from pathlib import Path

from harness.runtime import InstallFailure, format_failure, make_relative_symlink, require_runtime

COMPONENT = "extensions/autoworkspace.ts"
FUNCTION = "install-pi-extension"
JSON_OUT = os.environ.get("JSON_OUT") == "1"


def fail(detail: str) -> None:
    exc = InstallFailure(COMPONENT, FUNCTION, detail)
    print(format_failure(exc.component, exc.function, exc.detail), file=sys.stderr)
    if JSON_OUT:
        print(json.dumps({"status": "failed", "detail": detail, "failures": [exc.to_dict()]}))
    raise SystemExit(1)


def log(message: str) -> None:
    print(message, flush=True, file=sys.stderr)


home = Path(os.environ["HOME"])
try:
    runtime = require_runtime(home)
except InstallFailure as exc:
    print(format_failure(exc.component, exc.function, exc.detail), file=sys.stderr)
    if JSON_OUT:
        print(json.dumps({"status": "failed", "detail": exc.detail, "failures": [exc.to_dict()]}))
    raise SystemExit(1) from exc

source = runtime / "extensions" / "autoworkspace" / "index.ts"
if not source.is_file():
    fail(f"runtime extension missing: {source}")
dest = home / ".pi" / "agent" / "extensions" / "autoworkspace.ts"
dest.parent.mkdir(parents=True, exist_ok=True)

if dest.is_symlink() and dest.resolve() == source.resolve():
    link_text = Path(os.readlink(dest))
    if link_text.is_absolute():
        fail(f"user extension link must be relative: {dest} -> {link_text}")
    log(f"skip extension {dest}")
elif dest.exists() and not dest.is_symlink():
    fail(f"foreign extension conflict: {dest}")
elif dest.is_symlink():
    cur = dest.resolve()
    try:
        cur.relative_to(runtime)
        owned = True
    except ValueError:
        owned = False
    if not owned:
        fail(f"foreign extension symlink conflict: {dest} -> {cur}")
    make_relative_symlink(source, dest)
    if dest.resolve() != source.resolve() or Path(os.readlink(dest)).is_absolute():
        fail(f"extension link invalid after install: {dest}")
    log(f"replaced extension {dest}")
else:
    make_relative_symlink(source, dest)
    if dest.resolve() != source.resolve() or Path(os.readlink(dest)).is_absolute():
        fail(f"extension link invalid after install: {dest}")
    log(f"linked extension {dest}")
PY
