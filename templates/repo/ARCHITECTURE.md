# Arquitectura — repo-standard

### Propósito de este documento

- **Objetivos:** Resumen de 1–2 páginas del sistema (canon o producto) y puntero al detalle en `docs/architecture/`.
- **Estructura:** Esta meta-sección → qué hay aquí → perfiles / cajas → gates → qué no unifica → enlace a reutilización.
- **Contenido a integrar según contexto:** En producto, **reescribe** el cuerpo: límites del *producto*, cajas reales, gates del stack. No dejes el texto «esto es el canon». Enlaza overview + ADRs propios.

Este repositorio es el **canon de plataforma** de Soluciones-Alexendros: un contrato reutilizable, no un runtime.

Detalle: [`docs/architecture/overview.md`](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/architecture/overview.md). Decisiones: [`docs/architecture/decisions/`](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/architecture/decisions/).

## Qué hay aquí

```
contrato de flota (docs + AGENTS + CI names)
        │
        ├── stacks/     callers ci.yml por runtime (pin SHA)
        ├── scripts/    smoke + validador de estructura de este canon
        └── .github/    reusable-*, ci.yml (ci-gate), Renovate, plantillas
```

Tres perfiles, un esqueleto:

| Perfil | Para quién | Extra sobre el anterior |
|--------|------------|-------------------------|
| **P0 Base** | Todo repo activo | README, LICENSE, SECURITY, CONTRIBUTING, CHANGELOG, CI `pipeline`+`ci-gate`, CODEOWNERS, metadatos |
| **P1 Producto** | Webs, SaaS, apps, CLIs | `docs/`, AGENTS, ARCHITECTURE, `.env.example`, `smoke`, Renovate, issue/PR templates |
| **P2 Público** | Contribución externa | CoC, SUPPORT, topics ricos, `security.yml` / audit, coverage publicado |

## Gates

Orden de fases en la flota:

`quality` → `test` (unit/function + coverage) → `build` → `smoke` → (`e2e` opcional)

`build` solo existe si hay artefacto. El único check **required** es `ci-gate` ([ADR-0013](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/architecture/decisions/ADR-0013-check-unico-ci-gate.md)). Auto-merge squash sin revisión ([ADR-0012](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/architecture/decisions/ADR-0012-solo-dev-automerge-sin-revision.md)).

En **este** repo no hay artefacto de aplicación: `reusable-static` corre actionlint + `check-structure`, el hook `test` y `smoke`; el caller emite `ci-gate`.

## Qué no unifica este canon

- El framework de aplicación (Next vs Astro vs Rust).
- El historial ni los nombres de repos existentes.
- Archivados ni forks externos.

Para aplicar el contrato a un repo que ya existe: [`docs/REUTILIZACION.md`](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/REUTILIZACION.md).
