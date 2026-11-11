---
version: "1.0.0"
date: "2026-11-10"
status: "Accepted"
adr_id: "ADR-0018"
priority: "P1"
---

# ADR-0018: Rename a machineroom y capa de compatibilidad legacy

**Fecha:** 2026-11-10
**Estado:** Accepted
**Prioridad:** P1

### Propósito de este documento

- **Objetivos:** Fijar el rename `autoworkspace` → `machineroom` (marca, repo, runtime y estado por proyecto) y la ventana de compatibilidad de los nombres viejos.
- **Estructura:** Frontmatter → H1 → Contexto, Decisión, Consecuencias, Relacionados.
- **Contenido a integrar según contexto:** No copies este ADR a un producto consumidor; el fallback se retira en 9.0.0.

## Contexto

El nombre `autoworkspace` se había fragmentado en cuatro superficies con vidas
distintas: la marca (`Autoworkspace`), el prefijo corto (`aw-`), el runtime de
máquina (`~/.autoworkspace`) y el estado por proyecto (`.autoworkspace/`). Cada
una arrastraba literales en skills, hooks, instaladores, tests y docs, y el
recuento de skills ya divergía entre ficheros (16 frente a 17). La auditoría de
harness de 2026-11-10 dejó además dos asimetrías: Cursor tenía gate de shell y Pi
no, y el contrato de ejecución estaba copiado en tres sitios.

## Decisión

1. **Marca:** `machineroom` en minúsculas para identificadores, rutas, repo y
   paquetes; título humano `Machineroom`. Prefijo corto `mr-` sustituye a `aw-`.
2. **SSOT de nombres:** `tools/harness/naming.py` (marca, prefijo, repo, dirs) y
   `tools/state_paths.py` (directorio de estado y prefijos excluidos). Ningún
   literal repetido en el código vivo.
3. **Runtime:** `~/.machineroom`. La migración desde `~/.autoworkspace` la hace
   `scripts/runtime-sync.sh` (o `migrate_legacy_runtime`); si existen las dos,
   falla en cerrado y pide intervención. Nunca hay dos runtimes.
4. **Estado por proyecto:** `.machineroom/`, con fallback de lectura a
   `.autoworkspace/` durante toda la línea **8.x** y eliminación en **9.0.0**.
   El fallback avisa por stderr una vez y `--migrate` mueve el directorio.
5. **Historia inmutable:** `CHANGELOG.md`, `docs/plans/`, `docs/archives/`, los
   ADR previos (incluido el nombre de fichero
   `ADR-0016-autoworkspace-host-del-canon.md`) y los planes históricos conservan
   el nombre viejo. Un ADR nuevo documenta el cambio en vez de reescribirlo.
6. **Versión:** `8.0.0` (BREAKING) con release `v8.0.0`.

## Consecuencias

- Cualquier repo de producto que aún tenga `.autoworkspace/` sigue funcionando
  con aviso; la migración es explícita y reversible.
- Los clones y paquetes Pi pineados a `v7.x` siguen apuntando al nombre viejo;
  GitHub redirige la URL del repo y los tags previos no se reescriben.
- Los literales `autoworkspace`/`aw-` quedan confinados a `LEGACY_*`, a las
  rutas de fallback y a los tests que los verifican; un gate de naming lo
  comprueba en CI.
- El contrato de ejecución pasa a una sola fuente (la rule) con puntero y
  digest, y el gate de shell es único para Cursor y Pi.

## Relacionados

- [ADR-0016](ADR-0016-autoworkspace-host-del-canon.md): host del canon de flota.
- [ADR-0017](ADR-0017-centralizacion-execution-min-priv.md): execution central y
  mínimo privilegio.
- Plan canónico del incremento: `tasks/plan-machineroom-rename-harness.md`.
