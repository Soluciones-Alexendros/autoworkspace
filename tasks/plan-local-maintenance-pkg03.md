# Plan: fix PKG-03 (local-maintenance)

Spec: `tasks/SPEC-local-maintenance-pkg03.md`

## Diseño

Rama `pacman` de `check_pkg_03`:

1. **Primario (genérico):** `pacman -Qo /usr/lib/modules/<running>/vmlinuz`
   → parsea `... is owned by <pkg> <version>`. Funciona con cualquier nombre
   de paquete de kernel.
2. **Fallback:** la lista hardcodeada actual ampliada con `linux-omarchy` y
   `linux-cachyos` (cubre kernels cuyo directorio de módulos ya fue eliminado
   tras actualizar → ahí el mismatch es el FAIL legítimo de reboot pendiente).
3. Comparación por base (`split("-")[0]`) sin cambios.

## Riesgos

- Bajo: cambio acotado a una rama de una función; runner inyectable preservado.
- Formato localizado de `pacman -Qo` ("is owned by" es estable en pacman).

## Tasks

- [x] T1 (RED): 4 tests en `tests/test_common.py` para `check_pkg_03` pacman
  - Acceptance: fallan los 2 de omarchy contra el código actual; pasan los 2 de linux estándar
  - Roles: role-clean-code · Test surfaces: `check_pkg_03` vía runner falso
  - Verify: `pytest tests/test_common.py -q` (2 fallos esperados)
  - Files: `skills/local-maintenance/scripts/tests/test_common.py`
- [x] T2 (GREEN): fix en `common.py`
  - Acceptance: los 4 tests pasan
  - Roles: role-clean-code · Verify: `pytest tests/test_common.py -q`
  - Files: `skills/local-maintenance/scripts/common.py`
- [x] T3 (VALIDATE): suite completa del skill + `make validate`
  - Acceptance: 0 fallos
  - Verify: `cd skills/local-maintenance/scripts && python3 -m pytest tests/ -q`; `make validate`
- [x] T4 (VERIFY real): re-auditoría quick en el host → PKG-03 PASS
  - Verify: `python3 ~/.pi/agent/skills/local-maintenance/scripts/audit_quick.py` (tras reinstalar skill)

## Checkpoints

Tras T2: suite del skill completa. Tras T3: gate del repo.
