#!/usr/bin/env bash
# Materialize the machine runtime at $HOME/.autoworkspace (real directory, not a symlink).
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CMD="${1:-}"
shift || true
FROM="$ROOT"
VERSION=""
DRY_RUN=false
JSON_OUT=false
HOME_DIR="${HOME}"
REPOSITORY="${AW_BOOTSTRAP_REPOSITORY:-Soluciones-Alexendros/autoworkspace}"

usage() {
  cat <<EOF
Usage:
  bash scripts/runtime-sync.sh sync [--from CHECKOUT] [--dry-run] [--json]
  bash scripts/runtime-sync.sh install --version X.Y.Z [--dry-run] [--json]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from) FROM="${2:-}"; shift 2 ;;
    --version) VERSION="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    --json) JSON_OUT=true; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "ERROR: unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

RUNTIME="${HOME_DIR}/.autoworkspace"

if [[ "$CMD" != "sync" && "$CMD" != "install" ]]; then
  usage
  exit 2
fi

if [[ -L "$RUNTIME" ]]; then
  echo "ERROR: runtime must be a real directory, not a symlink: $RUNTIME" >&2
  exit 1
fi

if [[ "$CMD" == "sync" ]]; then
  FROM=$(cd "$FROM" && pwd)
  if [[ "$DRY_RUN" == true ]]; then
    if [[ "$JSON_OUT" == true ]]; then
      printf '{"status":"simulated","action":"sync","from":"%s","runtime":"%s"}\n' "$FROM" "$RUNTIME"
    else
      echo "dry-run: would sync payload from $FROM into $RUNTIME"
    fi
    exit 0
  fi
  export AW_SYNC_FROM="$FROM"
  export AW_SYNC_RUNTIME="$RUNTIME"
  set +e
  RESULT=$(PYTHONPATH="$ROOT/tools" JSON_OUT="$JSON_OUT" python3 - <<'PY'
import json
import os
import sys
from pathlib import Path
from harness.runtime import InstallFailure, format_failure, sync_payload

from_path = Path(os.environ["AW_SYNC_FROM"])
runtime = Path(os.environ["AW_SYNC_RUNTIME"])
json_out = os.environ.get("JSON_OUT") == "true"
try:
    manifest = sync_payload(from_path, runtime, origin="sync")
except InstallFailure as exc:
    print(format_failure(exc.component, exc.function, exc.detail), file=sys.stderr)
    if json_out:
        print(json.dumps({"status": "failed", "action": "sync", "runtime": str(runtime), "failures": [exc.to_dict()]}))
    raise SystemExit(1) from exc
print(json.dumps({"status": "ok", "action": "sync", "runtime": str(runtime), **manifest}))
PY
)
  RC=$?
  set -e
  if [[ "$RC" -ne 0 ]]; then
    if [[ "$JSON_OUT" == true && -n "$RESULT" ]]; then
      echo "$RESULT"
    fi
    exit "$RC"
  fi
  if [[ "$JSON_OUT" == true ]]; then
    echo "$RESULT"
  else
    echo "Synced runtime at $RUNTIME"
    printf '%s\n' "$RESULT" | python3 -c 'import json,sys; d=json.load(sys.stdin); print("version=%s digest=%s…" % (d["version"], d["digest"][:12]))'
  fi
  exit 0
fi

if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$ ]]; then
  echo "ERROR: --version must be an exact SemVer release" >&2
  exit 2
fi
if [[ "$DRY_RUN" == true ]]; then
  if [[ "$JSON_OUT" == true ]]; then
    printf '{"status":"simulated","action":"install","version":"%s","runtime":"%s"}\n' "$VERSION" "$RUNTIME"
  else
    echo "dry-run: would download and install v$VERSION into $RUNTIME"
  fi
  exit 0
fi

for dependency in gh python3; do
  if ! command -v "$dependency" >/dev/null 2>&1; then
    echo "not_run: required dependency not found: $dependency" >&2
    exit 3
  fi
done

WORK=$(mktemp -d /tmp/autoworkspace-runtime-XXXXXX)
chmod 700 "$WORK"
trap 'rm -rf "$WORK"' EXIT
ARCHIVE="$WORK/autoworkspace-${VERSION}.tar.gz"
gh release download "v${VERSION}" --repo "$REPOSITORY" \
  --pattern "autoworkspace-${VERSION}.tar.gz" --pattern "SHA256SUMS" --dir "$WORK"
(
  cd "$WORK"
  sha256sum -c SHA256SUMS
)
gh attestation verify "$ARCHIVE" -R "$REPOSITORY"
PYTHONPATH="$ROOT/tools" python3 -m harness.bootstrap "$ARCHIVE" "$WORK/extracted"
PACKAGE="$WORK/extracted/autoworkspace-${VERSION}"
[[ -d "$PACKAGE" && ! -L "$PACKAGE" ]]
RESULT=$(PYTHONPATH="$ROOT/tools" python3 - <<PY
from pathlib import Path
from harness.runtime import sync_payload
import json
manifest = sync_payload(Path("$PACKAGE"), Path("$RUNTIME"), origin="release:$VERSION")
print(json.dumps({"status": "ok", "action": "install", "runtime": "$RUNTIME", **manifest}))
PY
)
if [[ "$JSON_OUT" == true ]]; then
  echo "$RESULT"
else
  echo "Installed runtime $VERSION at $RUNTIME"
fi
