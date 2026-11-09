#!/usr/bin/env bash
# End-to-end bootstrap tests with a local release fixture; no network or real release.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
VERSION=$(python3 -c 'import json; print(json.load(open("package.json"))["version"])' "$ROOT")
TMP=$(mktemp -d /tmp/autoworkspace-bootstrap-test-XXXXXX)
trap 'rm -rf "$TMP"' EXIT
RELEASE="$TMP/release"
PACKAGE="$TMP/package/autoworkspace-${VERSION}"
mkdir -p "$PACKAGE" "$RELEASE" "$TMP/bin"
cp -a "$ROOT/package.json" "$ROOT/README.md" "$PACKAGE/"
cp -a "$ROOT/scripts" "$ROOT/skills" "$ROOT/extensions" "$ROOT/.cursor" "$ROOT/.cursor-plugin" "$PACKAGE/"
# Installation artifacts are not source files and must not enter a release fixture.
rm -rf "$PACKAGE/.cursor/skills"
mkdir -p "$PACKAGE/tools"
cp -a "$ROOT/tools/pyproject.toml" "$ROOT/tools/uv.lock" "$PACKAGE/tools/"
for component in harness execution contracts workspace-router orchestrator; do
  cp -a "$ROOT/tools/$component" "$PACKAGE/tools/"
done
tar -czf "$RELEASE/autoworkspace-${VERSION}.tar.gz" -C "$TMP/package" "autoworkspace-${VERSION}"
(
  cd "$RELEASE"
  sha256sum "autoworkspace-${VERSION}.tar.gz" > SHA256SUMS
)

cat >"$TMP/bin/gh" <<'PY'
#!/usr/bin/env python3
import os, shutil, sys
from pathlib import Path
args = sys.argv[1:]
if args[0] == "release" and args[1] == "download":
    destination = Path(args[args.index("--dir") + 1])
    for name in os.environ["AW_BOOTSTRAP_RELEASE_DIR"].split(os.pathsep):
        source = Path(name)
        for item in source.iterdir():
            if item.is_file():
                shutil.copyfile(item, destination / item.name)
    raise SystemExit(0)
if args[0] == "attestation" and args[1] == "verify":
    raise SystemExit(1 if os.environ.get("AW_FIXTURE_ATTESTATION_FAIL") == "1" else 0)
raise SystemExit(2)
PY
chmod +x "$TMP/bin/gh"
export PATH="$TMP/bin:$PATH"
export AW_BOOTSTRAP_REPOSITORY="fixture/autoworkspace"
export AW_BOOTSTRAP_RELEASE_DIR="$RELEASE"

DRY_TARGET="$TMP/dry-target"
DRY=$(bash "$ROOT/scripts/bootstrap.sh" --version "$VERSION" --harness cursor --target "$DRY_TARGET" --dry-run --json)
echo "$DRY" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="simulated" and d["dry_run"] is True'
test ! -e "$DRY_TARGET"

HOME="$TMP/home-pi" bash "$ROOT/scripts/bootstrap.sh" --version "$VERSION" --harness pi \
  --target "$TMP/project-pi" --json >"$TMP/pi.json"
python3 - "$TMP/pi.json" <<'PY'
import json,sys
result=json.load(open(sys.argv[1]))
assert result["status"]=="installed" and result["doctor"]=="pass", result
print("bootstrap Pi + native doctor: PASS")
PY

bash "$ROOT/scripts/bootstrap.sh" --version "$VERSION" --harness cursor \
  --target "$TMP/project-cursor" --json >"$TMP/cursor.json"
python3 - "$TMP/cursor.json" <<'PY'
import json,sys
result=json.load(open(sys.argv[1]))
assert result["status"]=="installed" and result["doctor"]=="pass", result
print("bootstrap Cursor full + doctor: PASS")
PY

# Checksum mismatch must stop before target installation.
BAD_SUM="$TMP/bad-sum"
cp -a "$RELEASE" "$BAD_SUM"
printf 'tampered' >> "$BAD_SUM/autoworkspace-${VERSION}.tar.gz"
if AW_BOOTSTRAP_RELEASE_DIR="$BAD_SUM" bash "$ROOT/scripts/bootstrap.sh" --version "$VERSION" --harness cursor \
  --target "$TMP/bad-sum-target" --json >/dev/null 2>&1; then
  echo "FAIL: checksum mismatch accepted"; exit 1
fi
test ! -e "$TMP/bad-sum-target/.cursor"

# Attestation denial must stop before target installation.
if AW_FIXTURE_ATTESTATION_FAIL=1 bash "$ROOT/scripts/bootstrap.sh" --version "$VERSION" --harness cursor \
  --target "$TMP/denied-target" --json >/dev/null 2>&1; then
  echo "FAIL: attestation denial accepted"; exit 1
fi
test ! -e "$TMP/denied-target/.cursor"

# Hostile archive with valid checksum must be rejected by the confined extractor.
HOSTILE="$TMP/hostile"
cp -a "$RELEASE" "$HOSTILE"
python3 - "$HOSTILE/autoworkspace-${VERSION}.tar.gz" <<'PY'
import io, sys, tarfile
path=sys.argv[1]
with tarfile.open(path, "w:gz") as archive:
    info=tarfile.TarInfo("../escape.txt")
    payload=b"escape"
    info.size=len(payload)
    archive.addfile(info, io.BytesIO(payload))
PY
(
  cd "$HOSTILE"
  sha256sum "autoworkspace-${VERSION}.tar.gz" > SHA256SUMS
)
if AW_BOOTSTRAP_RELEASE_DIR="$HOSTILE" bash "$ROOT/scripts/bootstrap.sh" --version "$VERSION" --harness cursor \
  --target "$TMP/hostile-target" --json >/dev/null 2>&1; then
  echo "FAIL: hostile archive accepted"; exit 1
fi
test ! -e "$TMP/hostile-target/.cursor"

echo "bootstrap tests OK"
