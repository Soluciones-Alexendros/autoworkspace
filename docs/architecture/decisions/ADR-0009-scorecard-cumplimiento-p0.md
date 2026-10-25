---
version: "1.0.0"
date: "2026-09-24"
status: "Proposed"
adr_id: "ADR-0009"
priority: "P1"
---

# ADR-0009: Scorecard de cumplimiento P0 de flota

**Fecha:** 2026-09-24
**Estado:** Proposed
**Prioridad:** P1

### Propósito de este documento

- **Objetivos:** Definir un escáner/scorecard rojo-ámbar-verde del P0 de flota, para que la oleada no se mida a ojo.
- **Estructura:** Frontmatter → H1 → esta meta-sección → Contexto, Decisión, Consecuencias, Prioridad, Checklist, Alternativas, Relacionados.
- **Contenido a integrar según contexto:** No copies este ADR a un producto. El scorecard corre **contra** la flota desde este canon (o un workflow del Mantenedor), no dentro de cada app.

## Contexto

La alineación es un PR por repo y un checklist §8 manual. Tras 10+ repos, nadie sabe qué quedó en rojo (sin SECURITY, Dependabot duplicado, `build` required fantasma, Renovate App ausente). Hace falta una lectura objetiva y repetible.

Restricción: el escáner no cambia settings de org ni de otros repos; solo **lee** (API GitHub / árbol público o token read-only del Mantenedor).

## Decisión

1. Este canon publica un **scorecard P0** (script o workflow `workflow_dispatch`) que, para cada repo activo de la org, pinta **rojo / ámbar / verde**.
2. Señales P0 (mínimo):
   - Archivos: README, LICENSE, CHANGELOG, SECURITY, CONTRIBUTING, CODEOWNERS, `ci.yml` con jobs `quality` + `test`
   - CI: existe el check required `ci-gate` ([ADR-0013](./ADR-0013-check-unico-ci-gate.md)); las fases viven en el reusable
   - Deps: hay `renovate.json` y **no** hay `dependabot.yml` de version-updates
   - Metadatos: description no vacía, ≥4 topics
   - Protección: `main` exige PR; checks required ⊆ jobs que existen
   - Seguridad: secret scanning / push protection heredados (ADR-0005)
   - Renovate App: el repo está en la instalación (ADR-0004) — si no se puede leer, ámbar
3. Escala:
   - **Rojo:** falta un archivo P0, o CI sin `quality`/`test`, o `dependabot.yml` de bumps, o protection ausente, o secreto escaneable apagado
   - **Ámbar:** JSON de Renovate sin App; topics incompletos; `build` required pero el job no existe; suite/coverage inestable
   - **Verde:** P0 cubierto y sin fantasmas
4. Salida: tabla Markdown en `docs/` o artefacto de workflow (sin tokens, sin datos de security advisories).
5. P1/P2 del checklist §8 son columnas extra, no bloquean el color P0.

## Consecuencias

- La oleada tiene un «definition of done» medible.
- Un token `read:org` + `repo` (humano) es necesario para protection/App; el script documenta scopes y no los commitea.
- Falsos ámbar si la API no expone un setting: se documentan, no se «adivinan verdes».

## Prioridad

**P1.** Útil cuando haya ≥2 repos alineados; no bloquea los ADRs P0.

## Checklist de implementación

- [ ] `scripts/fleet-scorecard.sh` (o `python`) + README de uso (dry-run sobre un repo).
- [ ] Workflow `workflow_dispatch` opcional en este canon (token por secret de org, no en el árbol).
- [ ] Matriz de señales P0 publicada en `docs/guides/` o en el runbook de settings.
- [ ] Excluir archivados y forks externos (misma regla que REUTILIZACION).
- [ ] CHANGELOG al añadir el escáner.

## Alternativas

- **Solo checklist §8 en cada PR:** se queda como complemento; no escala.
- **OSSF Scorecard genérico:** útil en P2 público; no mide nuestros nombres de jobs ni Renovate.
- **Agente que «arregla» en caliente todos los rojos:** fuera de alcance (un PR por repo, sin mutar org).

## Relacionados

- [ADR-0002](./ADR-0002-proteccion-metadatos-como-codigo.md)
- [ADR-0003](./ADR-0003-job-build-y-required-checks.md)
- [ADR-0004](./ADR-0004-renovate-org-y-dependabot.md)
- [ADR-0005](./ADR-0005-secret-scanning-org.md)
- [REUTILIZACION.md](../../REUTILIZACION.md)
