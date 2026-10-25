---
version: "1.0.0"
date: "2026-09-24"
status: "Proposed"
adr_id: "ADR-0007"
priority: "P1"
---

# ADR-0007: Coverage ≥70% como gate opcional en `test`

**Fecha:** 2026-09-24  
**Estado:** Proposed  
**Prioridad:** P1

### Propósito de este documento

- **Objetivos:** Precisar que el umbral ≥70% (80% en críticos) es un **gate en el job `test`** cuando la suite es estable, no un check fantasma ni un requisito el día 1 de un repo sin tests.
- **Estructura:** Frontmatter → H1 → esta meta-sección → Contexto, Decisión, Consecuencias, Prioridad, Checklist, Alternativas, Relacionados.
- **Contenido a integrar según contexto:** No copies este ADR. En producto: engancha `--coverage` / `cargo llvm-cov` en `test` cuando la baseline sea estable; documenta 80% en módulos críticos (auth, pagos, parsers, crypto).

## Contexto

[ADR-0001](./ADR-0001-canon-repo-standard.md) fijó coverage por defecto ≥70% y 80% aspiracional en críticos. Aplicarlo como required check el primer día de alineación rompe repos con suite incompleta o sin runner de coverage, y empuja a umbrales de mentira (`passWithNoTests`).

Este canon no tiene runtime: el job `test` es un hook. El gate vive en el **producto**, dentro de `test`, no como job extra `coverage`.

## Decisión

1. El umbral de flota sigue siendo **≥70% de líneas** cuando el gate está activo. Los módulos críticos documentan **80%** en `docs/guides/testing.md` o README del producto (no un segundo job).
2. El gate es **opcional hasta que la suite sea estable**: hay tests en CI, el reporte es determinista y el umbral no se «compra» excluyendo todo el árbol.
3. Cuando se activa, vive **dentro del job `test`** (mismo job, mismo required check). No se crea un check `coverage` aparte.
4. Repos sin suite (docs-only, este canon, infra sin código): no hay gate; el placeholder de `test` permanece.
5. Bajar el umbral o apagar el gate en un producto que ya lo tenía es cambio de contrato: se documenta en el CHANGELOG del producto.

## Consecuencias

- La oleada P1 no se bloquea por coverage el día 0; el scorecard puede marcar «gate off (suite inestable)» en ámbar.
- 80% críticos queda escrito (auth, billing, parsers, crypto, pipelines); no es un número decorativo.
- Un único required check (`test`) evita el fantasma `coverage`.

## Prioridad

**P1.** El hook `test` ya existe; el umbral se enciende por repo cuando toque.

## Checklist de implementación

- [ ] Actualizar `docs/guides/testing.md` y stacks: «gate opcional hasta suite estable».
- [ ] Plantilla de snippet `test` con flag de coverage comentado o `COVERAGE_GATE=off`.
- [ ] Lista de «críticos» a documentar (80%) en la guía de testing del producto.
- [ ] Scorecard (ADR-0009): verde = gate on ≥70%; ámbar = suite inestable / gate off; rojo = gate on y fallando.
- [ ] CHANGELOG cuando la guía deje el gate como contrato P1.

## Alternativas

- **70% required en toda la flota el día 0:** se descartó (rompe alineación y fomenta exclusiones masivas).
- **Job `coverage` separado y required:** se descartó (check fantasma en repos sin reporter).
- **Solo cobertura 80% global (zedazo):** se mantiene como techo de críticos, no como default.

## Relacionados

- [ADR-0001](./ADR-0001-canon-repo-standard.md)
- [ADR-0003](./ADR-0003-job-build-y-required-checks.md)
- [docs/guides/testing.md](../../guides/testing.md)
