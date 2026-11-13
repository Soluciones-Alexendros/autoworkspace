#!/usr/bin/env bash
# Bootstrap de LinkML para Arch Linux (skill data-linkml).
#
# Un solo script: pacman (python + python-pip) → venv aislado → pip con pin
# linkml==1.12.1 → verificación opcional. Pip SOLO dentro del venv (Arch marca
# el Python del sistema como externally-managed / PEP 668).
#
# Por defecto DRY-RUN: imprime el plan y no toca nada. --apply ejecuta.
# Exit codes canónicos: 0 OK, 1 error/veredicto negativo, 2 input inválido,
# 3 dependencia ausente, 4 permiso.
#
# Uso:
#   bootstrap_arch.sh                    # dry-run: muestra el plan
#   bootstrap_arch.sh --apply            # instala (sudo para pacman)
#   bootstrap_arch.sh --apply --verify --venv-dir /tmp/linkml-venv
#   bootstrap_arch.sh --apply --skip-pacman
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REQ_FILE="$SKILL_DIR/assets/requirements-linkml.txt"

APPLY=0
# LinkML project directory: the venvs live under ~/Projects/linkml/venvs/.
LINKML_PROJECT_DIR="${LINKML_PROJECT_DIR:-$HOME/Projects/linkml}"
VENV_DIR="${LINKML_VENV_DIR:-$LINKML_PROJECT_DIR/venvs/linkml}"
SKIP_PACMAN=0
VERIFY=0
DRY_RUN=1

usage() {
  cat <<EOF
Uso: bootstrap_arch.sh [--apply] [--venv-dir DIR] [--skip-pacman] [--verify]

Prepara el entorno LinkML en Arch Linux:
  1. pacman: python + python-pip (solo si faltan; sudo + confirmación)
  2. venv:   python3 -m venv <venv-dir>
  3. pip:    install -r assets/requirements-linkml.txt (pin linkml==1.12.1)
  4. verify: linkml --version + laboratorio (validate_cycle.py)

Flags:
  --apply        ejecuta (sin esta flag: dry-run, imprime el plan y no toca nada)
  --venv-dir DIR ubicación del venv (default: ~/Projects/linkml/venvs/linkml)
  --skip-pacman  no toca pacman (requiere Python >= 3.10 ya presente)
  --verify       tras instalar, ejecuta la verificación completa
  --help         esta ayuda
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1; DRY_RUN=0 ;;
    --venv-dir) VENV_DIR="${2:?--venv-dir requiere DIR}"; shift ;;
    --skip-pacman) SKIP_PACMAN=1 ;;
    --verify) VERIFY=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "ERROR: flag desconocida: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

ok() { echo "OK: $1"; }
bad() { echo "FALLO: $1" >&2; exit 1; }
step() { echo "==> $1"; }

# ---------- Preflight ----------
step "Preflight"
OS_ID="$(grep -E '^ID=' /etc/os-release | cut -d= -f2 | tr -d '"' || true)"
OS_LIKE="$(grep -E '^ID_LIKE=' /etc/os-release | cut -d= -f2 | tr -d '"' || true)"
IS_ARCH=0
for cand in "$OS_ID" $OS_LIKE; do
  [[ "$cand" == "arch" || "$cand" == "archlinux" ]] && IS_ARCH=1
done
if [[ "$IS_ARCH" -eq 0 ]]; then
  echo "ERROR: este bootstrap solo soporta Arch Linux y derivadas (ID=$OS_ID, ID_LIKE=$OS_LIKE)." >&2
  echo "  Alternativa: imagen OCI oficial 'docker.io/linkml/linkml'." >&2
  exit 2
fi
echo "  OS: $OS_ID (Arch-compatible: ID_LIKE=$OS_LIKE)"

command -v pacman >/dev/null 2>&1 || { echo "ERROR: pacman no encontrado" >&2; exit 3; }
command -v sudo >/dev/null 2>&1 || echo "  aviso: sudo no encontrado (--skip-pacman será obligatorio)"

PY_BIN="$(command -v python3 || true)"
[[ -n "$PY_BIN" ]] || { echo "ERROR: python3 no encontrado" >&2; exit 3; }
PY_VER="$("$PY_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
[[ "$(printf '%s\n' "$PY_VER" "3.10" | sort -V | head -1)" == "3.10" ]] \
  || { echo "ERROR: python3 $PY_VER < 3.10" >&2; exit 2; }
echo "  Python del sistema: $PY_VER"

if [[ "$DRY_RUN" -eq 0 ]]; then
  "$PY_BIN" -c '
import urllib.request, sys
try:
    urllib.request.urlopen("https://pypi.org/simple/linkml/", timeout=10)
except Exception:
    sys.exit(1)
' || { echo "ERROR: sin acceso a PyPI (o red caída)" >&2; exit 3; }
  echo "  Red hacia PyPI: OK"
else
  echo "  Red hacia PyPI: no comprobada (dry-run)"
fi

# ---------- Plan ----------
step "Plan"
MISSING_PKGS=()
if [[ "$SKIP_PACMAN" -eq 0 ]]; then
  pacman -Q python >/dev/null 2>&1 || MISSING_PKGS+=(python)
  pacman -Q python-pip >/dev/null 2>&1 || MISSING_PKGS+=(python-pip)
  if [[ ${#MISSING_PKGS[@]} -eq 0 ]]; then
    echo "  pacman: python y python-pip ya instalados (nada que hacer)"
  else
    echo "  pacman: instalar ${MISSING_PKGS[*]} (sudo pacman -S --needed)"
  fi
else
  echo "  pacman: omitido (--skip-pacman)"
fi

if [[ -d "$VENV_DIR" ]]; then
  echo "  venv: $VENV_DIR ya existe (se reutiliza)"
else
  echo "  venv: crear $VENV_DIR (python3 -m venv)"
fi
echo "  pip:   $VENV_DIR/bin/pip install -r $REQ_FILE"
[[ "$VERIFY" -eq 1 ]] && echo "  verify: linkml --version + laboratorio validate_cycle.py" || echo "  verify: omitido"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo ""
  echo "Dry-run: nada ejecutado. Repite con --apply para instalar."
  exit 0
fi

# ---------- 1. pacman ----------
if [[ "$SKIP_PACMAN" -eq 0 && ${#MISSING_PKGS[@]} -gt 0 ]]; then
  step "pacman: instalar ${MISSING_PKGS[*]}"
  if [[ -t 0 ]]; then
    read -r -p "¿Continúo? (y/N) " confirm
    [[ "$confirm" == "y" || "$confirm" == "Y" ]] || bad "cancelado por el usuario"
  else
    bad "sin TTY: no puedo pedir confirmación para sudo pacman. Usa --skip-pacman o una terminal interactiva."
  fi
  sudo pacman -S --needed --noconfirm "${MISSING_PKGS[@]}" || bad "pacman falló (exit $?)"
else
  step "pacman: nada que instalar"
fi

# ---------- 2. venv ----------
step "venv"
if [[ ! -d "$VENV_DIR" ]]; then
  mkdir -p "$(dirname "$VENV_DIR")" || bad "no se pudo crear el directorio del venv"
  "$PY_BIN" -m venv "$VENV_DIR" || bad "no se pudo crear el venv en $VENV_DIR"
fi
"$VENV_DIR/bin/python" -m pip install --upgrade pip >/dev/null || bad "pip upgrade falló"

# ---------- 3. pip (dentro del venv) ----------
step "pip install (dentro del venv)"
"$VENV_DIR/bin/pip" install -r "$REQ_FILE" || bad "pip install falló"

# ---------- 4. verify ----------
if [[ "$VERIFY" -eq 1 ]]; then
  step "verify"
  VER="$("$VENV_DIR/bin/linkml" --version || true)"
  echo "  linkml --version: ${VER:-DESCONOCIDA}"
  python3 "$SCRIPT_DIR/validate_cycle.py" \
    --linkml "$VENV_DIR/bin/linkml" \
    --schema "$SKILL_DIR/assets/schema-template.yaml" \
    --target-class Catalog \
    --data "$SKILL_DIR/assets/instance-valid.yaml" "$SKILL_DIR/assets/instance-invalid.yaml" \
    || bad "laboratorio con veredicto negativo"
fi

step "Resumen"
echo "  venv:   $VENV_DIR"
echo "  activar: source $VENV_DIR/bin/activate"
echo "  usar:   linkml --help · linkml validate · linkml lint · linkml generate"
echo "Bootstrap completado."
