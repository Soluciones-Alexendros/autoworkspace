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

reject_parent_segments() {
  local rest="${1%/}"
  local seg
  while [[ -n "$rest" ]]; do
    seg="${rest%%/*}"
    if [[ "$seg" == ".." ]]; then
      echo "ERROR: --target must not contain .." >&2
      return 2
    fi
    if [[ "$rest" == */* ]]; then
      rest="${rest#*/}"
    else
      break
    fi
  done
}

is_skills_dir() {
  case "$1" in
    *.cursor/skills|.cursor/skills) return 0 ;;
    *.pi/skills|.pi/skills) return 0 ;;
    *.pi/agent/skills|.pi/agent/skills) return 0 ;;
    *) return 1 ;;
  esac
}

# Anchor relative paths to this checkout. $ROOT is already a physical pwd.
resolve_harness_root() {
  local t="$1"
  local h="$2"
  local nested
  if [[ "$h" == "cursor" ]]; then
    nested=".cursor/skills"
  else
    nested=".pi/skills"
  fi

  reject_parent_segments "$t" || return $?

  if [[ "$t" != "/" && "$t" == */ ]]; then
    t="${t%/}"
  fi

  if is_skills_dir "$t"; then
    if [[ "$t" == /* ]]; then
      echo "$t"
      return 0
    fi
    t="${t#./}"
    echo "$ROOT/$t"
    return 0
  fi

  if [[ "$t" == "." || "$t" == "$ROOT" ]]; then
    echo "$ROOT/$nested"
    return 0
  fi

  if [[ "$t" != /* ]]; then
    t="${t#./}"
    echo "$ROOT/$t/$nested"
    return 0
  fi

  echo "$t/$nested"
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
  --target DIR          Destination project directory. '.' is this script's checkout
                        ($ROOT), not the cwd. Relative paths anchor to $ROOT.
                        A path ending in .cursor/skills, .pi/skills, or .pi/agent/skills
                        is used as-is. Default without --user: /tmp/ai-<harness>, then nested.
  --user                Install into the harness user skills directory. Overrides --target.
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
  if [[ -n "$TARGET" ]]; then
    echo "WARN: --user overrides --target; ignoring --target $TARGET" >&2
  fi
  ARGS=(--user --harness "$HARNESS")
else
  if [[ -z "$TARGET" ]]; then
    TARGET="/tmp/ai-${HARNESS}"
  fi
  RESOLVED="$(resolve_harness_root "$TARGET" "$HARNESS")" || exit $?
  ARGS=(--target "$RESOLVED" --harness "$HARNESS")
fi

if [[ "$YES" == true ]]; then ARGS+=("--yes"); fi
if [[ "$JSON_OUT" == true ]]; then ARGS+=("--json"); fi
if [[ "$DRY_RUN" == true ]]; then ARGS+=("--dry-run"); fi

if [[ "$HARNESS" == "cursor" ]]; then
  exec bash "$ROOT/scripts/install-cursor.sh" "${ARGS[@]}"
else
  exec bash "$ROOT/scripts/install-pi.sh" "${ARGS[@]}"
fi
