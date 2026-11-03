# Spec: fix PKG-03 falso positivo kernel (local-maintenance)

Origen: `docs/plans/2026-11-03-bug-local-maintenance-pkg03-kernel-omarchy.md`

## Objective

`check_pkg_03` (skills/local-maintenance/scripts/common.py) marca FAIL espurio
en sistemas Arch cuyo kernel no se llama `linux`/`linux-lts`/`linux-zen`/
`linux-hardened` (p. ej. Omarchy con `linux-omarchy`): reporta
"installed: unknown" y recomienda reiniciar sin necesidad. Debe detectar el
kernel instalado de forma genérica y seguir detectando el reinicio pendiente
real (kernel actualizado sin reiniciar).

Criterios de aceptación:

1. En Omarchy con kernel al día → PKG-03 PASS (era FAIL).
2. Tras actualizar kernel sin reiniciar → PKG-03 FAIL (reboot pendiente real).
3. Distros con kernel `linux` estándar → comportamiento idéntico al actual.
4. Sin regresiones: suite del skill y `make validate` en verde.

## Tech Stack

Python 3 stdlib, pytest. Sin dependencias nuevas.

## Commands

```bash
cd skills/local-maintenance/scripts && python3 -m pytest tests/ -q
make validate   # gate canónico del repo
```

## Project Structure

- `skills/local-maintenance/scripts/common.py` → checks compartidos (aquí vive `check_pkg_03`)
- `skills/local-maintenance/scripts/tests/test_common.py` → tests unitarios (runner inyectado)

## Code Style

Ruff (`ruff.toml`), español en mensajes de usuario, helpers `_run_with(runner, cmd, timeout)`
para toda ejecución de comandos (permite inyección de runner falso en tests).

## Testing Strategy

Red-green con runner falso (patrón existente en test_common.py): un `runner(cmd, timeout)`
que devuelve salidas simuladas de `uname -r`, `pacman -Qo` y `pacman -Q`.

## Boundaries

- Always: tests antes de cerrar; mantener la firma pública de `check_pkg_03`.
- Ask first: cambios en el contrato de salida JSON de auditorías.
- Never: tocar los JSON de clean-routine ni `__pycache__` versionados; editar
  la copia instalada en `~/.pi/agent/skills/` (es symlink gestionado por install-pi.sh).

## Success Criteria

- PKG-03 pasa en Omarchy real (re-auditoría en el host).
- 4 tests nuevos cubren: omarchy OK, omarchy reboot pendiente, linux estándar OK, linux estándar mismatch.
- `make validate` verde.

## Open Questions

Ninguna. (Reinstalación del skill vía `scripts/install-pi.sh` queda como paso
posterior, fuera del código.)
