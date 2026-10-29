---
version: "1.0.0"
date: "2026-10-29"
status: "Accepted"
adr_id: "ADR-0017"
priority: "P1"
---

# ADR-0017: Centralización de execution y mínimo privilegio por tipo

**Fecha:** 2026-10-29
**Estado:** Accepted
**Prioridad:** P1

### Propósito de este documento

- **Objetivos:** Dejar de empaquetar `execution.yaml` dentro de cada skill (extensión no estándar para Cursor/Pi) y aplicar mínimo privilegio en `allowed-tools` según `metadata.type`.
- **Estructura:** Frontmatter → H1 → Contexto, Decisión, Consecuencias, Relacionados.
- **Contenido a integrar según contexto:** No copies este ADR a un producto consumidor; aplica el registry del host autoworkspace.

## Contexto

Tras el pivot `7.0.0-alpha.0` (`compatibility: cursor, pi`), cada skill seguía declarando `skills/<name>/execution.yaml` como extensión local. Cursor y Pi no interpretan ese archivo; rompe la promesa de compatibilidad del frontmatter estándar. Además `allowed-tools: Read, Grep, Glob, Bash, Write` era genérico: skills de tipo audit (solo informe) declaraban Write y Bash.

## Decisión

1. **Registry central:** `tools/execution/registry.yaml` (+ schema JSON) es la SSOT de tools/ops mutadores. `run_registered` y la capa `tools/execution/` leen ese registry. Las skills enlazan con `metadata.execution: <tool_id>` sin añadir claves top-level al frontmatter (siguen siendo 6).
2. **Sin `execution.yaml` bajo `skills/`:** el gate (`skill_spec`, `registry --check`, contracts) falla si aparece.
3. **Audits fuera del registry:** `web-compliance`, `web-owasp`, `web-performance`, `project-architecture`, `project-libraries` son `type: audit`, `allowed-tools: Read, Grep, Glob`, sin entrada en registry.
4. **Matriz mínima por tipo** (máximos):

| type         | allowed-tools máximo                                                    |
| ------------ | ----------------------------------------------------------------------- |
| audit        | Read, Grep, Glob                                                        |
| atomic       | Read, Write, Grep, Glob (+ Bash solo si la skill muta vía tools/suites) |
| orchestrator | Read, Grep, Glob, Bash, Write (justificado en description)              |
| router       | Read, Glob                                                              |

5. Versión de este hardening: **`7.0.0-alpha.1`** (misma línea que el pivot `alpha.0`, no minor nueva).

## Consecuencias

- Cursor/Pi solo cargan `SKILL.md` (+ references/scripts); la ejecución mutadora sigue pasando por `run_registered` + aprobación.
- Los tests de closure y contracts apuntan al registry (25 ops / 11 tools tras retirar 7 ops audit).
- `allowed-tools` sigue sin autorizar en Cursor; es contrato de catálogo enforceable por `skill_spec`.

## Relacionados

- [ADR-0016](./ADR-0016-autoworkspace-host-del-canon.md) (host del canon)
- Plan: `docs/plans/2026-10-29-execution-registry-min-priv/`
