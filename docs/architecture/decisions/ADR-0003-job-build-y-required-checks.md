---
version: "1.0.0"
date: "2026-09-24"
status: "Superseded"
adr_id: "ADR-0003"
priority: "P0"
---

# ADR-0003: Cuándo el job `build` es required

> **Histórico (Superseded by ADR-0013).** No aplicar; la decisión vigente está en [ADR-0013](./ADR-0013-check-unico-ci-gate.md).

**Fecha:** 2026-09-24
**Estado:** Superseded by [ADR-0013](./ADR-0013-check-unico-ci-gate.md) (required checks). La regla «`build` solo si hay artefacto» y el orden de fases siguen vigentes allí.
**Prioridad:** P0 (hacer pronto)

### Propósito de este documento

- **Objetivos:** Evitar checks fantasma: `build` solo existe si hay artefacto; los required checks del producto son `quality` + `test` + `smoke` (+ `build`/`e2e` si aplican).
- **Estructura:** Frontmatter → H1 → esta meta-sección → Contexto, Decisión, Consecuencias, Prioridad, Checklist, Alternativas, Relacionados.
- **Contenido a integrar según contexto:** No copies este ADR. En el `ci.yml` del producto, crea o omite el job `build` según haya artefacto. Actualiza branch protection / ruleset a los jobs que **existen**.

## Contexto

[ADR-0001](./ADR-0001-canon-repo-standard.md) fijó el orden `quality` → `test` → `build` → `smoke`. Varios docs y la sección de Settings de [REUTILIZACION.md](../../REUTILIZACION.md) se leen como si `build` fuera siempre required. En repos sin artefacto (este canon, infra-only, skills) el job no existe: exigirlo en protection deja un check gris eterno y bloquea el merge.

## Decisión

1. El **orden lógico** de la flota sigue siendo `quality` → `test` → `build` → `smoke` (`e2e` opcional en webs). Es un orden de dependencias, no una lista fija de jobs.
2. El job **`build` solo se declara si hay artefacto** (sitio estático, imagen, binario, bundle). Si no hay artefacto, **el job no existe** (no se declara un no-op para «cumplir el nombre»).
3. `smoke` depende de `build` cuando `build` existe; si no, depende de `quality` + `test` (como en este canon).
4. **Required checks del producto** (branch protection / ruleset):
   - Siempre: `quality`, `test`, `smoke`
   - Además: `build` **solo** si el workflow lo define
   - Además: `e2e` **solo** si el producto es web P1 y el job está cableado
5. Este canon (`repo-standard`) **no** tiene job `build`. Sus required checks son `quality`, `test`, `smoke`.

## Consecuencias

- Un ruleset de org que exija `build` en todos los repos viola este ADR; el ruleset debe ser por perfil o por repo.
- Renombrar un job required es **breaking** del contrato ([ADR-0010](./ADR-0010-semver-contrato-estandar.md)).
- Los PRs dejan de quedarse «esperando» un check que nunca corre.

## Prioridad

**P0.** Los checks fantasma bloquean merges y falsean el cumplimiento de la oleada.

## Checklist de implementación

- [ ] Alinear README, AGENTS, ARCHITECTURE, REUTILIZACION y `docs/guides/testing.md` con esta regla (frase explícita: «`build` no existe si no hay artefacto»).
- [ ] Revisar el runbook/script de [ADR-0002](./ADR-0002-proteccion-metadatos-como-codigo.md) para no marcar `build` required por defecto.
- [ ] En oleada: cada repo de producto declara o no `build` y actualiza protection a los jobs reales.
- [ ] `scripts/check-structure.sh` de este canon **no** exige el job `build`.
- [ ] CHANGELOG `[Unreleased]` cuando el contrato de checks quede publicado en docs de flota.

## Alternativas

- **Job `build` no-op en todos los repos:** se descartó; crea ruido y un required check vacío.
- **`smoke` absorbe el build:** se descartó; mezcla «compila» con «responde» y alarga el job.
- **Required solo `quality`:** se descartó; deja test/smoke opcionales y degrada el P0.

## Relacionados

- [ADR-0001](./ADR-0001-canon-repo-standard.md)
- [ADR-0002](./ADR-0002-proteccion-metadatos-como-codigo.md)
- [ADR-0010](./ADR-0010-semver-contrato-estandar.md)
- [docs/guides/testing.md](../../guides/testing.md)
