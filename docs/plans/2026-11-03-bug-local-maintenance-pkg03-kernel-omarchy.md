# Bug: PKG-03 falso positivo en kernels no estándar (Omarchy)

**Fecha:** 2026-11-03
**Skill:** `local-maintenance` (scripts/common.py)
**Severidad:** baja (falso positivo; degrada el Health Score ~10-14 puntos en categoría `updates`)
**Detectado en:** auditoría completa en Omarchy 4.0.6 (ID_LIKE=arch, pacman)

## Síntoma

```
[FAIL] PKG-03 — Kernel running (7.2.8-9-omarchy) != installed (unknown)
   evidencia: uname -r: 7.2.8-9-omarchy, instalado: unknown
   remediación: "Reiniciar sistema"   ← incorrecta; no hay reinicio pendiente
```

## Causa raíz

`check_pkg_03()` (`scripts/common.py:776`), rama pacman, lista hardcodeada:

```python
for kernel_pkg in ("linux", "linux-lts", "linux-zen", "linux-hardened"):
```

Omarchy usa el paquete `linux-omarchy` (y cualquier derivado puede usar otro
nombre: `linux-cachyos`, `linux-lqx`, etc.). Al no encontrarse, cae a
`installed_kernel = "unknown"` → mismatch → FAIL espurio.

La comparación posterior sí es correcta: con el paquete detectado,
`running "7.2.8-9-omarchy".split("-")[0] == installed "7.2.8-9".split("-")[0]`
→ PASS.

## Fix propuesto (mínimo)

Añadir detección genérica en la rama pacman antes de la lista hardcodeada,
p. ej. resolver el paquete dueño de `/usr/lib/modules/$(uname -r)/vmlinuz`:

```bash
pacman -Qo "/usr/lib/modules/$(uname -r)/vmlinuz" 2>/dev/null
```

o, más simple, ampliar la tupla con `"linux-omarchy"` y derivados conocidos.
La primera opción es robusta para cualquier kernel empaquetado y además
detecta correctamente el caso real de "reboot pendiente" (el módulo del kernel
en ejecución ya no existe tras actualizar).

## Reproducir

En cualquier Omarchy actualizado:

```bash
python3 ~/.pi/agent/skills/local-maintenance/scripts/audit_quick.py
```

## Contexto adicional

- Verificado que `pacman -Qo /usr/lib/modules/7.2.8-9-omarchy/vmlinuz` →
  `linux-omarchy 7.2.8-9` (coincide con `uname -r`).
- Mientras no se corrija, toda auditoría en Omarchy reporta FAIL en PKG-03 y
  arrastra `updates` (71/100) y el score global (~10 puntos).
