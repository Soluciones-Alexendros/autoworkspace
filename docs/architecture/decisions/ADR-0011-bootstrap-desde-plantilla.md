---
version: "1.0.0"
date: "2026-09-24"
status: "Proposed"
adr_id: "ADR-0011"
priority: "P1"
---

# ADR-0011: Bootstrap al usar la plantilla

**Fecha:** 2026-09-24  
**Estado:** Proposed  
**Prioridad:** P1

### Propósito de este documento

- **Objetivos:** Evitar que un repo nacido de esta plantilla se quede con hooks placeholder eternos: o se sustituyen, o un script de bootstrap **falla** hasta declarar los comandos reales del producto.
- **Estructura:** Frontmatter → H1 → esta meta-sección → Contexto, Decisión, Consecuencias, Prioridad, Checklist, Alternativas, Relacionados.
- **Contenido a integrar según contexto:** No copies este ADR. Si naciste de la plantilla, ejecuta el bootstrap o sustituye `make test`/`lint`/`smoke` y el `ci.yml` por snippets de `stacks/`. Este canon (meta-estándar) **no** corre el bootstrap contra sí mismo.

## Contexto

«Use this template» copia stubs que **salen 0** (`make test` echo, `scripts/smoke.sh` demo, job `test` placeholder). Un producto puede llegar a `main` en verde sin haber enganchado tests reales. Eso viola el espíritu de P1 y entrena a agentes a dejar el placeholder.

## Decisión

1. Los repos **de producto** creados desde la plantilla deben, en el primer PR:
   - sustituir los hooks placeholder (`Makefile` lint/test, `scripts/smoke.sh`, job `test` del CI) por comandos reales del stack, **o**
   - ejecutar `scripts/bootstrap-from-template.sh` (nombre canónico) que **falla** (exit ≠ 0) hasta que existan declaraciones explícitas.
2. El script exige un manifiesto local (p. ej. `product.toml` / `.repo-standard-product.yml`) con:
   - `stack` (`typescript` | `astro` | `rust` | `python-skills` | `infra` | …)
   - `lint`, `test`, `smoke` (comandos no vacíos y distintos de los stubs del canon)
   - `has_artifact: true|false` (decide si existe job `build`, ADR-0003)
3. Mientras el manifiesto falte o apunte a stubs (`echo`, «placeholder», `exit 0` vacío), `bootstrap-from-template.sh` sale 1 y el job `quality` del **producto** puede invocarlo.
4. **Este repo** (`repo-standard`) no usa el bootstrap como gate: es el origen de los stubs. `check-structure.sh` sigue siendo su `quality`.
5. Documentar en Quickstart A: «el placeholder no es el estado final».

## Consecuencias

- Nacer de la plantilla ya no equivale a «CI verde eterno sin tests».
- Hay que mantener la lista de stubs conocidos (fácil de evadir si alguien pone `true`; el review humano sigue siendo necesario).
- Skills/Python y Astro se benefician cuando existan snippets (ADR-0008).

## Prioridad

**P1.** Primero el contrato y los ADRs; el script se implementa antes de promover el repo a GitHub Template de uso masivo.

## Checklist de implementación

- [ ] Escribir `scripts/bootstrap-from-template.sh` (fail-closed) + ejemplo de manifiesto.
- [ ] Documentar en README Quickstart A y en `docs/guides/local-setup.md`.
- [ ] Decidir si el producto añade `bash scripts/bootstrap-from-template.sh` a `quality` (recomendado P1).
- [ ] Lista de stubs prohibidos (`placeholder`, `este canon no tiene`, `@true` solo).
- [ ] No activar el script como required en **este** canon.
- [ ] CHANGELOG al añadir el script.

## Alternativas

- **Confiar en el review:** se queda como red de seguridad; no basta (agentes y humanos pegan el árbol y cierran).
- **Borrar los stubs de la plantilla:** rompe `make test` del propio canon.
- **Cookiecutter / copier:** reserva P2; un script fail-closed cubre P1.

## Relacionados

- [ADR-0003](./ADR-0003-job-build-y-required-checks.md)
- [ADR-0008](./ADR-0008-snippets-reales-post-oleada.md)
- [README.md](../../../README.md)
