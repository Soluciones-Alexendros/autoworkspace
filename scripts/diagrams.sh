#!/usr/bin/env bash
# Regenera los diagramas de docs/architecture/diagrams/ con Archify (P12 T5).
# El HTML resultante vive en rendered/ y no se versiona: es artefacto de CI.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CATALOG="docs/architecture/diagrams/catalog.json"
DIAGRAMS_DIR="docs/architecture/diagrams"
ARCHIFY_DIR="${ARCHIFY_DIR:-.cache/archify}"

export ARCHIFY_UPDATE_CHECK_DISABLED=1

if [ ! -f "$CATALOG" ]; then
  echo "diagrams: falta $CATALOG" >&2
  exit 1
fi

read -r REPO SHA <<<"$(python3 -c '
import json
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    renderer = json.load(fh)["renderer"]
print(renderer["repo"], renderer["sha"])
' "$CATALOG")"

if [ ! -d "$ARCHIFY_DIR/.git" ] || [ "$(git -C "$ARCHIFY_DIR" rev-parse HEAD)" != "$SHA" ]; then
  rm -rf "$ARCHIFY_DIR"
  git clone --quiet "https://github.com/${REPO}.git" "$ARCHIFY_DIR"
  git -C "$ARCHIFY_DIR" checkout --quiet "$SHA"
fi

CLI="$ARCHIFY_DIR/archify/bin/archify.mjs"
if [ ! -f "$CLI" ]; then
  echo "diagrams: falta el CLI de Archify en $CLI" >&2
  exit 1
fi

mkdir -p "$DIAGRAMS_DIR/rendered"

ENTRIES="$(mktemp)"
trap 'rm -f "$ENTRIES"' EXIT

python3 -c '
import json
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    diagrams = json.load(fh)["diagrams"]
for entry in diagrams:
    print(entry["id"], entry["type"], entry["source"])
' "$CATALOG" > "$ENTRIES"

while read -r ID TYPE SOURCE; do
  if [ ! -f "$SOURCE" ]; then
    echo "diagrams: la entrada $ID apunta a $SOURCE, que no existe" >&2
    exit 1
  fi
  node "$CLI" validate "$TYPE" "$SOURCE" --json >/dev/null
  node "$CLI" deliver "$TYPE" "$SOURCE" "$DIAGRAMS_DIR/rendered/${ID}.html" --json >/dev/null
  echo "diagrams: $ID ok"
done < "$ENTRIES"

python3 -c '
import json
import sys
from pathlib import Path

catalog = Path(sys.argv[1])
sources = Path(sys.argv[2])
with catalog.open(encoding="utf-8") as fh:
    listed = {Path(entry["source"]).as_posix() for entry in json.load(fh)["diagrams"]}
present = {path.as_posix() for path in sources.glob("*.json")}
orphans = sorted(present - listed)
if orphans:
    print("diagrams: fuentes fuera del catálogo: " + ", ".join(orphans), file=sys.stderr)
    sys.exit(1)
' "$CATALOG" "$DIAGRAMS_DIR/sources"
