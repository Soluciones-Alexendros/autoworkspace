---
version: "1.0.0"
date: "2026-09-24"
status: "Accepted"
adr_id: "ADR-0001"
---

# ADR-0001: Canon de flota en `repo-standard`

**Fecha:** 2026-09-24  
**Estado:** Accepted

### Propósito de este documento

- **Objetivos:** Dejar sentado que `repo-standard` (no la landing) es el canon de flota y cerrar las decisiones fundacionales (Renovate, idioma, coverage, automerge, gates).
- **Estructura:** Frontmatter → H1 → esta meta-sección → Contexto, Decisión, Consecuencias, Alternativas, Relacionados.
- **Contenido a integrar según contexto:** No copies este ADR a un producto. En producto, escribe ADRs del sistema real y enlaza este si adoptas el canon. Las ampliaciones P0/P1 viven en ADR-0002…0011.

## Contexto

La flota Iniciativas-Alexendros tiene estándares desiguales (inventario 2026-09-24): hay gold (`website-landingpage-template`, `zedazo`, `saas-afiladocs`) y repos sin CI, sin SECURITY, sin CODEOWNERS o con Dependabot y Renovate a la vez.

Hacía falta un **único contrato** (perfiles P0/P1/P2) que no aplastara el stack. Las decisiones abiertas de la plantilla (repo canónico, coverage, automerge humano, idioma) se cerraron al crear este repositorio.

## Decisión

1. El repo canónico es **`Iniciativas-Alexendros/repo-standard`** (nuevo), no una extensión de `website-landingpage-template`. La landing sigue siendo plantilla de producto web.
2. **Renovate** es el único bot de version-updates. No se añade `dependabot.yml` de bumps. Dependabot Alerts (seguridad) pueden permanecer ON.
3. Documentación del estándar en **español**.
4. Coverage por defecto **≥70%** de líneas; los módulos críticos documentan **80%** (techo aspiracional tipo zedazo).
5. Automerge de PRs humanos/agentes **solo** con label `automerge` (más CI verde y review). Renovate sí automergea `patch` y `minor`.
6. Gates: `quality` → `test` → `build` → `smoke`; `e2e` opcional en webs.
7. Este repo es **producto de plataforma**: esqueleto + docs + snippets. No incluye una app de referencia ejecutable.

## Consecuencias

- Los repos nuevos pueden nacer desde GitHub Template o copiar el árbol.
- Los existentes se alinean con [REUTILIZACION.md](../../REUTILIZACION.md), un PR por repo.
- `website-landingpage-template` no se degrada; se le pedirá (oleada 3) cerrar gaps (Renovate vs Dependabot, SECURITY unificado).
- Quien abra un major de deps o un cambio de workflow no tiene automerge.

## Alternativas

- **Extender `website-landingpage-template`:** se descartó para no mezclar el meta-estándar con un starter Astro/Next.
- **Dependabot como bot de la flota:** se descartó; varios gold ya usan Renovate y la decisión de 2026-09-24 lo fija.
- **Automerge humano tras 1 approval sin label:** se descartó para evitar merges accidentales de agentes.
- **Docs bilingües por defecto:** se reserva a P2 si un producto lo necesita.

## Relacionados

- [overview.md](../overview.md)
- [REUTILIZACION.md](../../REUTILIZACION.md)
- Inventario `repo-std-inventory.md` (2026-09-24)
- Ampliaciones: [ADR-0002](./ADR-0002-proteccion-metadatos-como-codigo.md) … [ADR-0011](./ADR-0011-bootstrap-desde-plantilla.md)
