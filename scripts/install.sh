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
UNINSTALL=false
COMPONENTS="skills"

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

resolve_project_root() {
  local t="$1"
  reject_parent_segments "$t" || return $?
  if [[ "$t" != "/" && "$t" == */ ]]; then t="${t%/}"; fi
  if [[ "$t" == "." ]]; then
    echo "$ROOT"
  elif [[ "$t" != /* ]]; then
    echo "$ROOT/${t#./}"
  else
    echo "$t"
  fi
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
    --components)
      if [[ $# -lt 2 ]]; then echo "ERROR: --components requires skills|full" >&2; exit 2; fi
      COMPONENTS="$2"
      shift 2
      ;;
    --yes|-y) YES=true; shift ;;
    --json) JSON_OUT=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    --uninstall) UNINSTALL=true; shift ;;
    --help|-h)
      cat <<'HELP'
Usage: bash scripts/install.sh --harness cursor|pi [--components skills|full] [--target DIR] [--user] [--yes] [--dry-run] [--uninstall] [--json]

  --harness cursor|pi   Required. Which harness installer to run.
  --target DIR          Destination project directory. '.' is this script's checkout
                        ($ROOT), not the cwd. Relative paths anchor to $ROOT.
                        A path ending in .cursor/skills, .pi/skills, or .pi/agent/skills
                        is used as-is. Default without --user: /tmp/ai-<harness>, then nested.
  --components skills|full  Cursor full installs skills, rules, agents and hooks.
  --user                Install into the harness user directory. Overrides --target.
  --uninstall           Remove only owned resources recorded in the manifest.
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
if [[ "$COMPONENTS" != "skills" && "$COMPONENTS" != "full" ]]; then
  echo "ERROR: --components must be skills|full" >&2
  exit 2
fi

if [[ "$COMPONENTS" == "full" ]]; then
  if [[ "$HARNESS" != "cursor" ]]; then
    echo "ERROR: --components full is only supported for cursor" >&2
    exit 2
  fi
  if [[ "$USER_MODE" == true ]]; then
    if [[ -n "$TARGET" ]]; then echo "WARN: --user overrides --target; ignoring --target $TARGET" >&2; fi
    FULL_TARGET="${HOME}/.cursor"
  else
    if [[ -z "$TARGET" ]]; then TARGET="/tmp/ai-cursor"; fi
    if is_skills_dir "$TARGET"; then
      echo "ERROR: full Cursor install expects a project root, not a skills directory" >&2
      exit 2
    fi
    FULL_TARGET="$(resolve_project_root "$TARGET")" || exit $?
  fi
  if [[ "$USER_MODE" == true ]]; then
    RUNTIME_SOURCE="${HOME}/.machineroom"
    if [[ ! -d "$RUNTIME_SOURCE/skills" ]]; then
      echo "ERROR: runtime missing: $RUNTIME_SOURCE (run scripts/runtime-sync.sh sync first)" >&2
      exit 1
    fi
    FULL_ARGS=(--source "$RUNTIME_SOURCE" --target "$FULL_TARGET" --user)
  else
    FULL_ARGS=(--source "$ROOT" --target "$FULL_TARGET")
  fi
  if [[ "$YES" == true ]]; then FULL_ARGS+=(--yes); fi
  if [[ "$JSON_OUT" == true ]]; then FULL_ARGS+=(--json); fi
  if [[ "$DRY_RUN" == true ]]; then FULL_ARGS+=(--dry-run); fi
  if [[ "$UNINSTALL" == true ]]; then FULL_ARGS+=(--uninstall); fi
  exec python3 "$ROOT/tools/harness/cursor_install.py" "${FULL_ARGS[@]}"
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
if [[ "$UNINSTALL" == true ]]; then ARGS+=("--uninstall"); fi

if [[ "$HARNESS" == "cursor" ]]; then
  exec bash "$ROOT/scripts/install-cursor.sh" "${ARGS[@]}"
else
  exec bash "$ROOT/scripts/install-pi.sh" "${ARGS[@]}"
fi
