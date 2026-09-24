---
version: "1.0.0"
date: "2026-09-24"
status: "Proposed"
adr_id: "ADR-0010"
priority: "P1"
---

# ADR-0010: SemVer y CHANGELOG del contrato del estándar

**Fecha:** 2026-09-24  
**Estado:** Proposed  
**Prioridad:** P1

### Propósito de este documento

- **Objetivos:** Versionar el *contrato* de `repo-standard` (no un runtime) y exigir que los repos declaren `repo-standard ≥x.y`.
- **Estructura:** Frontmatter → H1 → esta meta-sección → Contexto, Decisión, Consecuencias, Prioridad, Checklist, Alternativas, Relacionados.
- **Contenido a integrar según contexto:** No copies este ADR. En producto: una línea en README o `docs/REUTILIZACION.md` («cumple repo-standard ≥x.y»). No inventes versiones; usa el tag publicado de este canon.

## Contexto

El CHANGELOG ya cita Keep a Changelog y SemVer, pero no hay tag ni regla de *qué* es breaking. Renombrar el job `quality` a `lint`, o exigir un job nuevo como required, rompe protection y CI de toda la flota sin que nadie sepa qué versión del canon siguen.

## Decisión

1. Este repo publica **SemVer del contrato** (tags `vX.Y.Z`). El CHANGELOG de raíz es la fuente (Keep a Changelog). El esqueleto inicial ([#1](https://github.com/Iniciativas-Alexendros/repo-standard/pull/1)) es la línea base **1.0.0** cuando se etiquete.
2. **Breaking (MAJOR):**
   - Renombrar o eliminar un job **required** (`quality`, `test`, `smoke`; `build`/`e2e` cuando aplican)
   - Quitar un archivo P0 del árbol contractual o cambiar su nombre canónico
   - Cambiar el bot de deps (p. ej. volver a Dependabot version-updates)
   - Cambiar el idioma contractual o el label `automerge`
3. **MINOR:** nuevas piezas opt-in (snippets, scorecard, runbook de settings, meta-sección, ADRs de ampliación, gate de coverage opcional).
4. **PATCH:** correcciones de redacción, typos, pins de actions, stubs que no cambian nombres.
5. Cada repo de producto **declara** en README (o badge/texto) `repo-standard ≥x.y` de la versión con la que se alineó. Alinear a un major nuevo = PR propio.
6. Estos ADRs (0002–0011) son **MINOR** sobre 1.0.0: no retiran jobs ni archivos P0.

## Consecuencias

- Un rename de job required exige major + nota de migración en REUTILIZACION.
- Los consumidores pueden decir «estamos en ≥1.1» y el scorecard puede contrastarlo.
- Hay que etiquetar 1.0.0 (humano) cuando el contrato base se considere cerrado.

## Prioridad

**P1.** El CHANGELOG ya existe; faltan reglas de bump, tag y la línea `≥x.y` en productos.

## Checklist de implementación

- [ ] Publicar `VERSION` o leer la versión solo de tags + CHANGELOG (una fuente).
- [ ] Sección en README: «Versión del contrato» + cómo se bumpea.
- [ ] Plantilla de alineación: línea `Cumple repo-standard ≥x.y`.
- [ ] Tag `v1.0.0` del esqueleto (humano, tras revisar Unreleased).
- [ ] Guía breve «qué es breaking» enlazada desde CONTRIBUTING.
- [ ] Scorecard opcional: leer la declaración `≥x.y` (ámbar si falta).

## Alternativas

- **CalVer:** se descartó; el contrato es API de plataforma, SemVer comunica breaking mejor.
- **Versionar solo por hash de commit:** poco legible para humanos en READMEs de producto.
- **No versionar (status quo):** se descartó; la flota no puede decir a qué contrato obedece.

## Relacionados

- [ADR-0001](./ADR-0001-canon-repo-standard.md)
- [ADR-0003](./ADR-0003-job-build-y-required-checks.md)
- [CHANGELOG.md](../../../CHANGELOG.md)
