---
version: "2.0.0"
date: "2026-10-25"
status: "Accepted"
adr_id: "ADR-0013"
priority: "P0"
---

# ADR-0013: Check único `ci-gate`

**Fecha:** 2026-10-25
**Estado:** Accepted
**Prioridad:** P0
**Sustituye:** [ADR-0003](./ADR-0003-job-build-y-required-checks.md) en lo relativo a required checks

### Propósito de este documento

- **Objetivos:** Un solo check obligatorio en toda la flota (`ci-gate`), fijado a GitHub Actions (`integration_id` 15368), sin checks fantasma por nombres de fase.
- **Estructura:** Frontmatter → H1 → esta meta-sección → Contexto, Decisión, Consecuencias, Prioridad, Checklist, Alternativas, Relacionados.
- **Contenido a integrar según contexto:** No copies este ADR. En producto: el caller declara `pipeline` + `ci-gate`; el ruleset exige solo `ci-gate`. Las fases viven dentro del reusable.

## Contexto

[ADR-0003](./ADR-0003-job-build-y-required-checks.md) listaba `quality` + `test` + `smoke` (+ `build`/`e2e` si existían) como required. Eso obliga a rulesets por perfil, crea checks fantasma cuando falta un job y bloquea el auto-merge de [ADR-0012](./ADR-0012-solo-dev-automerge-sin-revision.md) si un nombre no coincide.

## Decisión

1. El **orden lógico** de fases sigue siendo `quality` → `test` → `build` → `smoke` (`e2e` opcional en webs). `build` solo se declara si hay artefacto.
2. El **único** context required en branch protection / ruleset de la flota es **`ci-gate`**, con `integration_id` **15368** (GitHub Actions).
3. `ci-gate` vive en el **caller** (`.github/workflows/ci.yml` del producto), con `needs: [pipeline]` e `if: always()`. Lee `toJSON(needs)` por variable de entorno y falla si algún resultado no es `success` (lista opcional de skips permitidos). También falla si el PR tiene la etiqueta `hold`.
4. `ci-gate` **no** va dentro del reusable: así el check se llama exactamente `ci-gate` y no `pipeline / ci-gate`.
5. El job `pipeline` llama al reusable del stack (`workflow_call`) pineado por SHA completo.

## Consecuencias

- Un ruleset de org/repo puede exigir el mismo nombre en toda la flota.
- Renombrar o eliminar `ci-gate` es **breaking** ([ADR-0010](./ADR-0010-semver-contrato-estandar.md)).
- Los nombres de fase dejan de ser required; siguen siendo contratos internos del reusable.

## Prioridad

**P0.** Sin el check único no hay auto-merge homogéneo ni ruleset compartible.

## Checklist de implementación

- [x] Marcar ADR-0003 como Superseded (required checks).
- [x] Workflows reutilizables + callers con `ci-gate`.
- [x] Actualizar README, AGENTS, REUTILIZACION, testing, ARCHITECTURE.
- [ ] Protection/ruleset de este repo: solo `ci-gate` (app 15368).
- [ ] CHANGELOG `[Unreleased]` BREAKING.

## Alternativas

- **Required `quality`+`test`+`smoke` (status quo):** se descartó; multiplica contexts y fantasma `build`.
- **`ci-gate` dentro del reusable:** se descartó; GitHub reporta el check como `pipeline / ci-gate`.
- **Matrix de required por perfil:** se descartó; el objetivo es un solo nombre de flota.

## Relacionados

- [ADR-0003](./ADR-0003-job-build-y-required-checks.md) (superseded en required checks)
- [ADR-0012](./ADR-0012-solo-dev-automerge-sin-revision.md)
- [ADR-0014](./ADR-0014-release-please-y-packaging-por-stack.md)
- [docs/guides/testing.md](../../guides/testing.md)
