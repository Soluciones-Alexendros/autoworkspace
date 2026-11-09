#!/usr/bin/env bash
# Download, authenticate, install and verify an immutable autoworkspace release.
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
VERSION=""
HARNESS=""
TARGET_INPUT=""
DRY_RUN=false
JSON_OUT=false
REPOSITORY="${AW_BOOTSTRAP_REPOSITORY:-Soluciones-Alexendros/autoworkspace}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) VERSION="${2:-}"; shift 2 ;;
    --harness) HARNESS="${2:-}"; shift 2 ;;
    --target) TARGET_INPUT="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    --json) JSON_OUT=true; shift ;;
    --help|-h)
      echo "Usage: bash scripts/bootstrap.sh --version X.Y.Z --harness pi|cursor --target DIR [--dry-run] [--json]"
      exit 0
      ;;
    *) echo "ERROR: unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$ ]]; then
  echo "ERROR: --version must be an exact SemVer release" >&2
  exit 2
fi
if [[ "$HARNESS" != "pi" && "$HARNESS" != "cursor" ]]; then
  echo "ERROR: --harness pi|cursor required" >&2
  exit 2
fi
if [[ -z "$TARGET_INPUT" ]]; then
  echo "ERROR: --target DIR required" >&2
  exit 2
fi
if [[ "$TARGET_INPUT" == *..* ]]; then
  echo "ERROR: --target must not contain .." >&2
  exit 2
fi
TARGET=$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve())' "$TARGET_INPUT")
case "$TARGET" in
  /|/etc|/usr|/var|/root) echo "ERROR: privileged target rejected: $TARGET" >&2; exit 3 ;;
esac

if [[ "$DRY_RUN" == true ]]; then
  if [[ "$JSON_OUT" == true ]]; then
    printf '{"status":"simulated","dry_run":true,"version":"%s","harness":"%s","target":"%s"}\n' "$VERSION" "$HARNESS" "$TARGET"
  else
    echo "dry-run: would download, verify and install autoworkspace $VERSION into $TARGET for $HARNESS"
  fi
  exit 0
fi

for dependency in gh python3 uv; do
  if ! command -v "$dependency" >/dev/null 2>&1; then
    echo "not_run: required dependency not found: $dependency" >&2
    exit 3
  fi
done
if [[ "$HARNESS" == "pi" ]] && ! command -v pi >/dev/null 2>&1; then
  echo "not_run: Pi binary not found" >&2
  exit 3
fi

WORK=$(mktemp -d /tmp/autoworkspace-bootstrap-XXXXXX)
chmod 700 "$WORK"
INSTALLED=""
on_exit() {
  local rc=$?
  trap - EXIT
  if [[ "$rc" -ne 0 ]]; then
    set +e
    if [[ "$INSTALLED" == "pi" ]]; then
      pi remove "$PACKAGE" >>"$WORK/rollback.log" 2>&1
    elif [[ "$INSTALLED" == "cursor" ]]; then
      bash "$PACKAGE/scripts/install.sh" --harness cursor --components full --target "$TARGET" --uninstall --yes >>"$WORK/rollback.log" 2>&1
    fi
    if [[ "$JSON_OUT" == true ]]; then
      printf '{"status":"failed","version":"%s","harness":"%s","target":"%s"}\n' "$VERSION" "$HARNESS" "$TARGET"
    else
      echo "ERROR: bootstrap failed; owned installation rollback attempted when applicable" >&2
    fi
  else
    if [[ "$JSON_OUT" == true ]]; then
      printf '{"status":"installed","doctor":"pass","version":"%s","harness":"%s","target":"%s"}\n' "$VERSION" "$HARNESS" "$TARGET"
    else
      echo "Installed and verified autoworkspace $VERSION ($HARNESS) at $TARGET"
    fi
  fi
  rm -rf "$WORK"
  exit "$rc"
}
trap 'on_exit $?' EXIT

ARCHIVE="$WORK/autoworkspace-${VERSION}.tar.gz"
gh release download "v${VERSION}" --repo "$REPOSITORY" \
  --pattern "autoworkspace-${VERSION}.tar.gz" --pattern "SHA256SUMS" --dir "$WORK" \
  >"$WORK/download.log" 2>&1
[[ -f "$ARCHIVE" && -f "$WORK/SHA256SUMS" ]]
(
  cd "$WORK"
  sha256sum -c SHA256SUMS
) >"$WORK/checksum.log" 2>&1
gh attestation verify "$ARCHIVE" -R "$REPOSITORY" >"$WORK/attestation.log" 2>&1
PYTHONPATH="$ROOT/tools" python3 -m harness.bootstrap "$ARCHIVE" "$WORK/extracted" >"$WORK/extract.log" 2>&1
PACKAGE="$WORK/extracted/autoworkspace-${VERSION}"
[[ -d "$PACKAGE" && ! -L "$PACKAGE" ]]
mkdir -p "$TARGET"

case "$HARNESS" in
  pi)
    pi install "$PACKAGE" >"$WORK/install.log" 2>&1
    INSTALLED="pi"
    uv run --project "$PACKAGE/tools" --frozen python "$PACKAGE/tools/harness/doctor.py" --harness pi --native \
      --source "$PACKAGE" --target "$TARGET" --expected-version "$VERSION" --json >"$WORK/doctor.json"
    ;;
  cursor)
    bash "$PACKAGE/scripts/install.sh" --harness cursor --components full \
      --target "$TARGET" --yes --json >"$WORK/install.log"
    INSTALLED="cursor"
    uv run --project "$PACKAGE/tools" --frozen python "$PACKAGE/tools/harness/doctor.py" --harness cursor --full \
      --source "$PACKAGE" --target "$TARGET" --expected-version "$VERSION" --json >"$WORK/doctor.json"
    ;;
esac
python3 - "$WORK/doctor.json" <<'PY'
import json, sys
report = json.load(open(sys.argv[1]))
if report.get("outcome") != "pass":
    print(f"doctor failed: {report.get('reasons')}", file=sys.stderr)
    raise SystemExit(1)
PY
