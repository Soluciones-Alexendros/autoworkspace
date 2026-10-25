---
version: "2.0.0"
date: "2026-10-25"
status: "Accepted"
adr_id: "ADR-0012"
priority: "P0"
---

# ADR-0012: Solo-dev con IA: auto-merge sin revisión

**Fecha:** 2026-10-25  
**Estado:** Accepted  
**Prioridad:** P0  
**Sustituye:** [ADR-0006](./ADR-0006-reviews-por-perfil.md)

### Propósito de este documento

- **Objetivos:** Fijar el modelo de merge de la flota para un único desarrollador que trabaja con agentes: PR → checks verdes → squash-merge automático sin revisión humana.
- **Estructura:** Frontmatter → H1 → esta meta-sección → Contexto, Decisión, Consecuencias, Prioridad, Checklist, Alternativas, Relacionados.
- **Contenido a integrar según contexto:** No copies este ADR. En producto: 0 approvals + auto-merge squash cuando `ci-gate` esté verde. La etiqueta `hold` es la única vía documentada para excluir un PR del auto-merge.

## Contexto

[ADR-0006](./ADR-0006-reviews-por-perfil.md) exigía el label `automerge` como interruptor de merge automático humano/agente y contemplaba ≥1 approval en productos con equipo. En la flota actual (un solo owner, Alejandro, más agentes) esa etiqueta y las reviews teatrales solo añaden fricción: el DoD ya vive en CI ([ADR-0013](./ADR-0013-check-unico-ci-gate.md)).

## Decisión

1. **Perfil de flota:** solo-dev con agentes. PR obligatorio a `main`. **0 aprobaciones** mínimas en ruleset / branch protection. CODEOWNERS informa, no bloquea.
2. **Auto-merge:** squash-merge automático en cuanto el check required `ci-gate` está en `success`. El agente (o el humano) activa `gh pr merge --auto --squash` al abrir el PR.
3. **Se elimina** la etiqueta `automerge` como requisito de merge humano/agente. Renovate sigue usando su propio `automerge` de configuración para `patch`/`minor` (no esa etiqueta).
4. **Etiqueta opcional `hold`:** si el PR la lleva, el job `ci-gate` del caller falla con mensaje claro y el PR queda fuera del auto-merge hasta quitarla.
5. **Sin bypass:** ni siquiera el admin (`enforce_admins` / ruleset sin bypass actors). Force-push a `main` prohibido.
6. **Break-glass:** desactivar el ruleset del repo (queda en el audit log de GitHub), mergear, reactivarlo. No hay excepción silenciosa.

## Consecuencias

- Un PR verde se fusiona sin revisión humana; la calidad se mide solo en CI.
- Un fallo de `ci-gate` (o la etiqueta `hold`) bloquea el merge sin necesidad de quitar permisos de auto-merge del repo.
- Cambiar a ≥1 approval o reintroducir `automerge` como requisito es breaking del contrato ([ADR-0010](./ADR-0010-semver-contrato-estandar.md)).

## Prioridad

**P0.** Sin esto el objetivo de flota (PR → verde → squash automático) no cierra.

## Checklist de implementación

- [x] Marcar ADR-0006 como Superseded.
- [x] Actualizar AGENTS, CONTRIBUTING, REUTILIZACION, plantilla de PR e issue.
- [ ] Ruleset de este repo: 0 approvals, sin bypass, check `ci-gate`, historial lineal.
- [ ] Crear etiqueta `hold` en el repo (y documentarla en CONTRIBUTING).
- [ ] CHANGELOG `[Unreleased]` BREAKING.

## Alternativas

- **Mantener label `automerge`:** se descartó; añade un paso manual sin ganar seguridad frente a CI.
- **≥1 approval en toda la flota:** se descartó para solo-owner (auto-review inútil).
- **Bypass de admin para break-glass:** se descartó; el audit log del ruleset es más auditable.

## Relacionados

- [ADR-0006](./ADR-0006-reviews-por-perfil.md) (superseded)
- [ADR-0013](./ADR-0013-check-unico-ci-gate.md)
- [ADR-0002](./ADR-0002-proteccion-metadatos-como-codigo.md)
- [CONTRIBUTING.md](../../../CONTRIBUTING.md)
