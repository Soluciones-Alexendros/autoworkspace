#!/usr/bin/env bash
# Unified AI entrypoint: resolve harness project root → skills dir, then exec installer.
# Public flat --target semantics stay on install-cursor.sh / install-pi.sh.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

HARNESS=""
TARGET=""
USER_MODE=false
YES=false
JSON_OUT=false
DRY_RUN=false

resolve_harness_root() {
  local t="$1"
  local h="$2"
  case "$t" in
    *.cursor/skills|*/.cursor/skills|.cursor/skills) echo "$t"; return ;;
    *.pi/skills|*/.pi/skills|.pi/skills) echo "$t"; return ;;
    *.pi/agent/skills|*/.pi/agent/skills|.pi/agent/skills) echo "$t"; return ;;
  esac
  if [[ "$h" == "cursor" ]]; then
    echo "$t/.cursor/skills"
  else
    echo "$t/.pi/skills"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --harness)
      if [[ $# -lt 2 ]]; then echo "ERROR: --harness requires cursor|pi" >&2; exit 2; fi
      HARNESS="$2"
      shift 2
      ;;
    --target)
      if [[ $# -lt 2 ]]; then echo "ERROR: --target requires DIR" >&2; exit 2; fi
      TARGET="$2"
      shift 2
      ;;
    --user) USER_MODE=true; shift ;;
    --yes|-y) YES=true; shift ;;
    --json) JSON_OUT=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    --help|-h)
      cat <<'HELP'
Usage: bash scripts/install.sh --harness cursor|pi [--target DIR] [--user] [--yes] [--dry-run] [--json]

  --harness cursor|pi   Required. Which harness installer to run.
  --target DIR          Project/root directory (default without --user: /tmp/ai-<harness>).
                        Nested to DIR/.cursor/skills or DIR/.pi/skills unless already a skills path.
  --user                Install into the harness user skills directory ($HOME/...).
  --yes                 Non-interactive (forwarded).
  --dry-run             No filesystem writes (forwarded).
  --json                JSON on stdout (forwarded).
HELP
      exit 0
      ;;
    --*) echo "ERROR: unknown flag $1" >&2; exit 2 ;;
    *) echo "ERROR: positional args not supported; use --target DIR" >&2; exit 2 ;;
  esac
done

if [[ "$HARNESS" != "cursor" && "$HARNESS" != "pi" ]]; then
  echo "ERROR: --harness cursor|pi required" >&2
  exit 2
fi

if [[ "$USER_MODE" == true ]]; then
  if [[ "$HARNESS" == "cursor" ]]; then
    TARGET="${HOME}/.cursor/skills"
  else
    TARGET="${HOME}/.pi/agent/skills"
  fi
elif [[ -z "$TARGET" ]]; then
  TARGET="/tmp/ai-${HARNESS}"
fi

RESOLVED="$(resolve_harness_root "$TARGET" "$HARNESS")"

ARGS=("--target" "$RESOLVED" "--harness" "$HARNESS")
if [[ "$YES" == true ]]; then ARGS+=("--yes"); fi
if [[ "$JSON_OUT" == true ]]; then ARGS+=("--json"); fi
if [[ "$DRY_RUN" == true ]]; then ARGS+=("--dry-run"); fi

if [[ "$HARNESS" == "cursor" ]]; then
  exec bash "$ROOT/scripts/install-cursor.sh" "${ARGS[@]}"
else
  exec bash "$ROOT/scripts/install-pi.sh" "${ARGS[@]}"
fi
