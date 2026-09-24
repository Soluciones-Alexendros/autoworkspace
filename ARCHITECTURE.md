# Arquitectura — repo-standard

### Propósito de este documento

- **Objetivos:** Resumen de 1–2 páginas del sistema (canon o producto) y puntero al detalle en `docs/architecture/`.
- **Estructura:** Esta meta-sección → qué hay aquí → perfiles / cajas → gates → qué no unifica → enlace a reutilización.
- **Contenido a integrar según contexto:** En producto, **reescribe** el cuerpo: límites del *producto*, cajas reales, gates del stack. No dejes el texto «esto es el canon». Enlaza overview + ADRs propios.

Este repositorio es el **canon de plataforma** de Iniciativas-Alexendros: un contrato reutilizable, no un runtime.

Detalle: [`docs/architecture/overview.md`](docs/architecture/overview.md). Decisiones: [`docs/architecture/decisions/`](docs/architecture/decisions/).

## Qué hay aquí

```
contrato de flota (docs + AGENTS + CI names)
        │
        ├── stacks/     fragmentos de quality/smoke por runtime
        ├── scripts/    smoke + validador de estructura de este canon
        └── .github/    workflows, Renovate, plantillas, CODEOWNERS
```

Tres perfiles, un esqueleto:

| Perfil | Para quién | Extra sobre el anterior |
|--------|------------|-------------------------|
| **P0 Base** | Todo repo activo | README, LICENSE, SECURITY, CONTRIBUTING, CHANGELOG, CI `quality`+`test`, CODEOWNERS, metadatos |
| **P1 Producto** | Webs, SaaS, apps, CLIs | `docs/`, AGENTS, ARCHITECTURE, `.env.example`, `smoke`, Renovate, issue/PR templates |
| **P2 Público** | Contribución externa | CoC, SUPPORT, topics ricos, `security.yml` / audit, coverage publicado |

## Gates

Orden fijo en la flota:

`quality` → `test` (unit/function + coverage) → `build` → `smoke` → (`e2e` opcional)

`build` solo existe si hay artefacto; si no, el job no se declara ([ADR-0003](docs/architecture/decisions/ADR-0003-job-build-y-required-checks.md)). Required checks = `quality` + `test` + `smoke` (+ `build`/`e2e` si aplican).

En **este** repo no hay artefacto de aplicación: `quality` valida el árbol canónico, `test` documenta el hook, `smoke` demuestra el contrato del script.

## Qué no unifica este canon

- El framework de aplicación (Next vs Astro vs Rust).
- El historial ni los nombres de repos existentes.
- Archivados ni forks externos.

Para aplicar el contrato a un repo que ya existe: [`docs/REUTILIZACION.md`](docs/REUTILIZACION.md).
